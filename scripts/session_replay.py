#!/usr/bin/env python3
"""Offscreen frame renderer for a Sauce session package.

Replays authorized Playwright actions on a real Chromium DOM, stepping a
controlled virtual clock at fixed fps and capturing native DPR screenshots.
No H.264 screen recording is used as source. Reproduction is only guaranteed
for controllable pages/assets. HAR replay can pin supported network resources.
"""
from __future__ import annotations
import argparse,hashlib,json,math,os,subprocess,time
from bisect import bisect_right
from datetime import datetime,timezone
from pathlib import Path
from typing import Sequence
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from playwright.sync_api import sync_playwright
from session_contract import validate_actions,verify_package
from spring_motion import cursor_track
from click_anchor import align_click_positions
from cinematic_tracks import cinematic_camera
from editorial_closeup_camera import closeup_camera
from cinematic_composite import background_focus
from cinematic_presentation_v13 import (make_dark_stage,paint_svg_pointer,paint_click_ripple)
from online_cursor_assets import render_cursor as render_tabler_cursor
from cinematic_stage import CinematicStage,CinematicCursor
from modal_depth_capture import (verified_modal_background,expected_modal_box,
                                 stabilized_verified_dialog_opening)
from multi_plane_depth import DEPTH_PX,MAX_BACKGROUND_BLUR
from semantic_effect_timeline import (
    SemanticEffectTimeline, VerifiedEffectEvidence)
from studio_motion_blur import directional_blur
from studio_motion_callouts import KineticCalloutRenderer
from spatial_parallax import inertial_tilt_track
from code_semantics import (plan_focus_cues,semantic_camera_track,
                            active_code_focus,highlight_code_region)
from session_capture import PRESENTATION_CLEANUP_STYLE, install_presentation_cleanup
from cinematic_spec import CURSOR_FILM_SCALE,enforce_hidpi,MASTER_SIZE
from cinematic_presentation_v12 import (draw_stage,compose_cursor,click_feedback,
    modal_spring_scale,WINDOW_X as PRESENT_X,WINDOW_Y as PRESENT_Y,
    WINDOW_W as PRESENT_W,WINDOW_H as PRESENT_H)
from system_cursors import extract_native_cursors,cursor_class

MASTER_W,MASTER_H,FPS_DEFAULT=1920,1080,60
WINDOW_X,WINDOW_Y,WINDOW_W,WINDOW_H=160,50,1600,900

def compare_verified_region(session_dir:Path, state:dict, page, dpr:int) -> dict|None:
    """Compare exact captured element pixels, rejecting visibly divergent replays.

    This check is deliberately scoped to the expected UI, not unstable page
    decoration, counters, or authenticated network content outside the target.
    """
    rect=state.get('focus_rect')
    if not rect:return None
    source=cv2.imread(str(session_dir/'states'/state['file']),cv2.IMREAD_COLOR)
    if source is None:raise RuntimeError('Could not decode verified source screenshot')
    live=cv2.imdecode(np.frombuffer(
        page.screenshot(scale='device',animations='allow',caret='hide'),dtype=np.uint8),
        cv2.IMREAD_COLOR)
    if live is None or live.shape!=source.shape:
        raise RuntimeError('Replay screenshot dimensions differ from source')
    left=max(0,int(round(rect['x']*dpr)))
    top=max(0,int(round(rect['y']*dpr)))
    right=min(source.shape[1],int(round((rect['x']+rect['width'])*dpr)))
    bottom=min(source.shape[0],int(round((rect['y']+rect['height'])*dpr)))
    if right-left<15 or bottom-top<15:raise RuntimeError('Verified ROI invalid')
    a=source[top:bottom,left:right]
    b=live[top:bottom,left:right]
    mae=float(np.mean(np.abs(a.astype(np.float32)-b.astype(np.float32))))
    # Intended to reject missing/invisible controls. It is not a universal
    # pixel-perfect comparison across GPU drivers or browser versions.
    if mae>27:
        raise RuntimeError(f'Visible region does not match source: MAE {mae:.1f} at {state["name"]}')
    return {'roi_mae':round(mae,3),
            'roi_css_rect':rect,
            'state_index':state['index']}

def cursor_motion(events:Sequence[dict],start_ms:float,duration:float,fps:int):
    picked=[]
    for e in events:
        if e['type'] in ('pointermove','pointerdown','pointerup','click') and e['x'] is not None:
            t=max(0.,(e['t']-start_ms)/1000.)
            if picked and t<=picked[-1][0]+.0005:
                picked[-1]=(picked[-1][0],float(e['x']),float(e['y']))
            else:picked.append((t,float(e['x']),float(e['y'])))
    if len(picked)<2:return None,picked
    return cursor_track(samples=picked,fps=fps,duration=duration,stiffness=900,damping=60),picked

def draw_frame_base():
    pic=Image.new('RGB',(MASTER_W,MASTER_H),(243,242,238))
    mask=Image.new('L',(MASTER_W,MASTER_H),0)
    d=ImageDraw.Draw(mask)
    d.rounded_rectangle((WINDOW_X,WINDOW_Y,WINDOW_X+WINDOW_W,WINDOW_Y+WINDOW_H),
                        radius=18,fill=180)
    shade=mask.filter(ImageFilter.GaussianBlur(25))
    pic.paste((102,104,99),(0,14),shade.point(lambda x:int(x*.18)))
    d=ImageDraw.Draw(pic)
    d.rounded_rectangle((WINDOW_X-1,WINDOW_Y-1,WINDOW_X+WINDOW_W,WINDOW_Y+WINDOW_H),
                        radius=18,outline=(191,193,187),width=2,fill=(249,248,245))
    clip=Image.new('L',(WINDOW_W,WINDOW_H),0)
    ImageDraw.Draw(clip).rounded_rectangle((0,0,WINDOW_W-1,WINDOW_H-1),radius=17,fill=255)
    return np.asarray(pic)[:,:,::-1].copy(),np.asarray(clip,dtype=np.float32)[:,:,None]/255

def overlay_native_cursor(output:np.ndarray,assets,position,css,source_factor,shift_x,shift_y):
    if position is None or cursor_class(css)=='none':return
    sprite=assets[cursor_class(css)]
    rgba=np.asarray(sprite.rgba,dtype=np.uint8)
    rgb=rgba[:,:,:3][:,:,[2,1,0]]
    alpha=rgba[:,:,3:4].astype(np.float32)/255
    x=int(round(WINDOW_X+shift_x+position[0]*source_factor))-sprite.hotspot_x
    y=int(round(WINDOW_Y+shift_y+position[1]*source_factor))-sprite.hotspot_y
    h,w=rgba.shape[:2]
    left=max(WINDOW_X,x);top=max(WINDOW_Y,y)
    right=min(WINDOW_X+WINDOW_W,x+w);bottom=min(WINDOW_Y+WINDOW_H,y+h)
    if left>=right or top>=bottom:return
    block=output[top:bottom,left:right]
    sprite_rgb=rgb[top-y:bottom-y,left-x:right-x]
    sprite_alpha=alpha[top-y:bottom-y,left-x:right-x]
    block[:]=np.uint8(block.astype(np.float32)*(1-sprite_alpha)+sprite_rgb*sprite_alpha)

def overlay_click(output,events,start_ms,t,source_factor,dx,dy):
    # Optional 180ms grayscale ring, only after an actual mousedown event.
    for e in events:
        if e['type']!='pointerdown' or e['x'] is None:continue
        age=t-(e['t']-start_ms)/1000
        if age<0 or age>.18:continue
        px=round(WINDOW_X+dx+source_factor*e['x'])
        py=round(WINDOW_Y+dy+source_factor*e['y'])
        radius=round(8+16*age/.18)
        strength=.20*(1-age/.18)
        layer=output.copy()
        cv2.circle(layer,(px,py),radius,(50,54,51),1,cv2.LINE_AA)
        cv2.addWeighted(layer,strength,output,1-strength,0,dst=output)

# Chromium CSS animations and Web Animations can retain a negative current
# time when mock-clock time jumps. A JS virtual clock does not by itself
# guarantee visible animations. Seek the site's OWN finite Web Animations on
# each output frame without reconstructing its interface.
ANIMATION_DRIVER=r"""
(() => {
 const known=new WeakMap();
 const previous=new WeakSet();
 const finite=a=>{
   const e=a.effect?.getComputedTiming();
   return !!e && Number.isFinite(e.endTime) && e.endTime>0 && e.endTime<=2000;
 };
 window.__sauceAnimationControls={
   settleInitial:()=>{
     for(const a of document.getAnimations()){
       if(!finite(a))continue;
       try{a.finish();previous.add(a)}catch{}
     }
   },
   step:ms=>{
     let animated=0;
     for(const a of document.getAnimations()){
       if(!finite(a))continue;
       if(previous.has(a))continue;
       if(!known.has(a))known.set(a,ms);
       try{
         a.pause();
         const end=a.effect.getComputedTiming().endTime;
         a.currentTime=Math.min(end,Math.max(0,ms-known.get(a)));
         animated++;
       }catch{}
     }
     return animated;
   }
 };
})();
"""

VISIBLE_PIXELS_JS=r"""element=>{
 let opacity=1, current=element;
 while(current && current instanceof Element){
   const cs=getComputedStyle(current);
   if(cs.visibility==='hidden'||cs.display==='none')return false;
   opacity*=Number(cs.opacity||'1');
   current=current.parentElement;
 }
 const box=element.getBoundingClientRect();
 return box.width>0&&box.height>0&&opacity>=.85;
}"""

def execute_action(page,action:dict):
    k=action['action']
    if k=='approach':
        # Recorded pointer samples are played one frame at a time below.
        # Do not execute the entire trajectory instantaneously.
        return
    if k in ('click','hover'):
        loc=page.locator(action['selector']).first
        loc.wait_for(state='visible',timeout=9000)
        if k=='hover':loc.hover(force=True,timeout=9000)
        else:loc.click(force=True,timeout=9000)
    elif k=='fill':
        page.locator(action['selector']).first.fill(str(action.get('value','')),timeout=9000)
    elif k=='move':
        page.mouse.move(float(action['x']),float(action['y']),
                        steps=max(1,int(action.get('steps',12))))
    elif k=='scroll':
        page.mouse.wheel(float(action.get('dx',0)),float(action.get('dy',0)))
    elif k=='wait':pass

def _raster_cache_identity(session:dict,workflow:list[dict],
                           times:list[float],hide_selector:str|None)->str:
    """Bind private canonical raster frames to recorded events and source time."""
    stable={'source_url':session['source_url'],
            **({'brand_tokens':session['brand_tokens']} if 'brand_tokens' in session else {}),
            'states':[(v['name'],v['at_ms'],v['sha256']) for v in session['states']],
            'events':session['events'],
            'workflow':workflow,
            'source_frame_times_ms':times,
            'presentation_opacity_stabilization_version':1,
            'hidden_decorative_selector':hide_selector,
            'capture_dpr':session['page'].get('dpr',2)}
    return hashlib.sha256(json.dumps(stable,sort_keys=True,
               ensure_ascii=True,separators=(',',':')).encode()).hexdigest()


def source_checks_before_action(stored, first_unchecked, next_action):
    """Return prior semantic checks due before a new captured action.

    Captured hover and click times can be less than one 60fps frame apart.
    The earlier hover-state assertion must run before the click changes
    the page, even when both actions map to the same encoded frame.
    """
    if next_action>=len(stored) or not 0<=first_unchecked<=next_action:
        return ()
    due=[]
    for i in range(first_unchecked,next_action):
        if stored[i]['end_ms']>stored[next_action]['at_ms']:
            break
        due.append(i)
    return tuple(due)


def replay(session_dir:Path,workflow_file:Path,output:Path,
           fps:int=60,seconds:float|None=None,har:bool=False,
           screenshot_step:int=45,expected_text:str|None=None,
           click_effect:bool=False,backdrop_focus:bool=False,
           presentation_v12:bool=False,
           presentation_hide_selector:str|None=None,
           presentation_v13:bool=False,
           presentation_v14:bool=False,cursor_style:str='ink',
           presentation_v15:bool=False,cursor_scale:float=CURSOR_FILM_SCALE,
           spatial_parallax:bool=False,audio_levels:list[float]|None=None,
           code_root:Path|None=None,editorial_closeup:bool=False,
           editorial_geometry:Path|None=None,
           studio_motion_plan:dict|None=None,
           raster_cache_dir:Path|None=None,
           experimental_orbit_optics:bool=False,
           optics_seed:int=20261116,
           result_aware_editorial:bool=False,
           result_payoff_push:bool=False,modal_lift:bool=False,
           click_water_ripple:bool=False,
           cursorless_source:bool=False) -> dict:
    if cursorless_source and (presentation_v12 or presentation_v13 or
                              presentation_v14 or presentation_v15 or
                              click_effect or click_water_ripple or backdrop_focus or
                              studio_motion_plan is not None):
        raise ValueError("Cursorless source must be original Chromium pixels, not a presentation")
    info_json=session_dir/'session.json'
    session=json.loads(info_json.read_text())
    info=verify_package(session,session_dir)
    actions=json.loads(workflow_file.read_text())
    validate_actions(actions)
    stored=session['workflow']
    if len(actions)!=len(stored) or any(
        a['action']!=b['action'] or a.get('selector')!=b.get('selector')
        for a,b in zip(actions,stored)):
        raise ValueError('Replay action sequence differs from verified capture')
    if fps not in (30,60):raise ValueError('Supported frame rates: 30,60')
    start_ms=session['states'][0]['at_ms']
    last_ms=session['states'][-1]['at_ms']
    length=seconds if seconds is not None else (last_ms-start_ms)/1000.+.35
    if not 0<length<=10:raise ValueError('Limit this proof renderer to <=10s')
    source_total=round(length*fps)
    if studio_motion_plan is not None:
        if studio_motion_plan.get('schema')!='sauce-studio-motion-v1':
            raise ValueError('Unrecognized studio motion schema')
        if studio_motion_plan['fps']!=fps or abs(studio_motion_plan['sourceDurationMs']/1000-length)>.01:
            raise ValueError('StudioMotion source time or fps mismatch')
        frame_map=studio_motion_plan['frameMap']
        total=len(frame_map)
        if not total:raise ValueError('StudioMotion mapping is empty')
        # Audio is mixed offline AFTER video replay; no audio clock is
        # fed into Chromium and it never changes source frame timing.
        if audio_levels is not None:raise ValueError('Do not drive preset visuals from audio RMS')
    else:
        frame_map=None
        total=source_total
    preset_engine=(studio_motion_plan.get('motionEngine')
                   if studio_motion_plan else None)
    preset_frames=(preset_engine['framePlan']['frames'] if preset_engine else None)
    if preset_frames is not None and len(preset_frames)!=total:
        raise ValueError('Preset FramePlan must cover every output video frame')
    modal_hints=[h for h in (preset_engine.get('framePlan',{}).get('heroMoments',[]) if preset_engine else [])
                 if h.get('kind')=='modal' and h.get('box')]
    beat_cut_frames={int(d['outputFrame']) for d in (
        preset_engine.get('framePlan',{}).get('editDecisions',[]) if preset_engine else [])
        if d.get('kind')=='cut' and isinstance(d.get('outputFrame'),int)}
    preset_spotlight_frames=0
    multi_plane_frames=0
    modal_lift_timeline=SemanticEffectTimeline(fps) if modal_lift else None
    modal_lift_frames=0
    single_plane_fallback_frames=0
    concealed_terminal_frames=0
    stabilized_opening_frames=0
    live_modal_hold_frames=0
    # Presentation-only exception: verified Brimble dark terminal shell.
    hide_brimble_terminal=(session['source_url'].rstrip('/')==
                           'https://www.brimble.io')
    diff_reveals={d['id']:d for d in (
        preset_engine.get('framePlan',{}).get('diffReveals',[]) if preset_engine else [])}
    film_mode=presentation_v12 or presentation_v13 or presentation_v14 or presentation_v15
    vector_mode=presentation_v13 or presentation_v14 or presentation_v15
    if click_water_ripple and not presentation_v15:
        raise ValueError('Water ripple requires the source-true CinematicStage renderer')
    if (presentation_v14 or presentation_v15) and cursor_style not in ('ink','outline'):
        raise ValueError('Select ink or outline cursor style')
    if vector_mode:
        enforce_hidpi(info['dpr'])
    if editorial_closeup and not presentation_v15:
        raise ValueError('Editorial closeup requires the root cinematic stage')
    expanded_rect=None
    if editorial_closeup:
        if editorial_geometry is None or not editorial_geometry.is_file():
            raise ValueError('Editorial closeup requires observed expanded dialog geometry')
        evidence=json.loads(editorial_geometry.read_text())
        if evidence.get('source_url')!=session['source_url']:
            raise ValueError('Expanded dialog evidence belongs to another website')
        if evidence.get('selector')!='[role=dialog]':
            raise ValueError('Expanded dialog selector must be verified')
        second_click=[e for e in session['events'] if e['type']=='pointerdown'][1]
        if abs(evidence['after_click_t']-(second_click['t']-start_ms)/1000.)>.15:
            raise ValueError('Expanded dialog evidence is not tied to second click')
        expanded_rect=evidence['observed_rect']
    camera,camera_cues=(closeup_camera(
        session['events'],start_ms,length,fps,tuple(info['viewport']),
        expanded_rect=expanded_rect)
        if editorial_closeup else cinematic_camera(
        session['events'],start_ms,length,fps,tuple(info['viewport'])))
    dialog_events=[event for event in session['events']
        if event['type']=='dialog-visible' and event.get('box')]
    first_dialog_ms=dialog_events[0]['t'] if dialog_events else None
    cursor,samples=cursor_motion(session['events'],start_ms,length,fps)
    if cursor:
        cursor=align_click_positions(cursor,session['events'],start_ms,fps)
    if any(e.get('type')=='code-focus' for e in session['events']) and code_root is None:
        raise ValueError('Code-focus events require --code-root for AST source verification')
    code_foci=plan_focus_cues(session['events'],code_root)
    if code_foci:
        camera=semantic_camera_track(camera,code_foci,start_ms,fps,tuple(info['viewport']))
    tilt_track=(inertial_tilt_track(cursor,fps=fps) if spatial_parallax and cursor
                else [(0.,0.)]*total)
    if audio_levels is not None:
        if len(audio_levels)!=source_total or any(not 0<=x<=1 for x in audio_levels):
            raise ValueError('Audio RMS envelope must match full frame count, values 0..1')
    if cursor:
        for action in (e for e in session['events'] if e['type']=='pointerdown'
                       and e.get('x') is not None):
            idx=round((action['t']-start_ms)*fps/1000)
            if 0<=idx<len(cursor):
                error=math.dist(cursor[idx],(action['x'],action['y']))
                if error>3.:
                    raise RuntimeError(f'Cursor would miss recorded click: {error:.2f}px')
    # Film frames are ALWAYS wrapped by the root compositor in production.
    # Older v12-v14 renderers are retained for deliberate A/B only.
    floor_config=(studio_motion_plan['stage'] if studio_motion_plan else {})
    backdrop_style=(preset_engine['preset']['stage']['backdropStyle']
                    if preset_engine else 'obsidian-grain')
    from brand_extractor import stage_brand_colors
    brand_primary,brand_accent=stage_brand_colors(session.get('brand_tokens'))
    if studio_motion_plan and not presentation_v15:
        raise ValueError('StudioMotion requires root CinematicStage')
    root_stage=(CinematicStage(
        backdrop_style=backdrop_style,
        brand_primary=brand_primary,brand_accent=brand_accent,
        enable_stage_optics=experimental_orbit_optics,
        optics_seed=optics_seed,
        enable_studio_floor=bool(floor_config.get('enabled',False)),
        floor_reflection_intensity=float(floor_config.get('reflectionIntensity',.25))
    ) if presentation_v15 else None)
    callout_renderer=(KineticCalloutRenderer(
        studio_motion_plan.get('callouts',[]),fps=fps) if studio_motion_plan else None)
    root_cursor=(CinematicCursor(root_stage,session['events'],start_ms,
                  cursor_style,cursor_scale,water_ripple=click_water_ripple)
                 if root_stage else None)
    if root_stage:
        wx,wy,ww,wh=root_stage.window
        base,clip=None,None
    else:
        wx,wy,ww,wh=WINDOW_X,WINDOW_Y,WINDOW_W,WINDOW_H
        base,clip=(make_dark_stage() if vector_mode else
                   draw_stage() if presentation_v12 else draw_frame_base())
        assert (WINDOW_X,WINDOW_Y,WINDOW_W,WINDOW_H)==(
            PRESENT_X,PRESENT_Y,PRESENT_W,PRESENT_H)
    # V13 deliberately never opens Xvfb or reads X11/native cursor glyphs.
    cursor_art=None if vector_mode else extract_native_cursors(display=':121',scale=2)
    source_w,source_h=info['viewport']
    source_px_w=source_w*info['dpr']
    source_px_h=source_h*info['dpr']
    actionable_boxes=[e['box'] for e in session['events']
        if e['type']=='pointerdown' and e.get('box')]
    if (source_w,source_h)!=(1280,720):
        raise ValueError('Current 16:9 proof compositor requires a 1280x720 CSS viewport')
    if output.parent:output.parent.mkdir(parents=True,exist_ok=True)
    cache_manifest=None
    cache_hit=False
    cache_key=None
    cached_files=[]
    if raster_cache_dir is not None:
        raw=raster_cache_dir.resolve();dst=output.parent.resolve()
        if raw==dst or raw.is_relative_to(dst) or dst.is_relative_to(raw):
            raise ValueError('Private raster cache cannot be inside published output')
        raster_cache_dir.mkdir(parents=True,exist_ok=True)
        times=[(float(row['sourceMs']) if frame_map else i*1000./fps)
               for i,row in enumerate(frame_map or [])] if frame_map else [
                   i*1000./fps for i in range(total)]
        cache_key=_raster_cache_identity(session,actions,times,presentation_hide_selector)
        cache_manifest=raster_cache_dir/'manifest.json'
        if cache_manifest.is_file():
            cached_manifest=json.loads(cache_manifest.read_text())
            if cached_manifest.get('identity')!=cache_key or cached_manifest.get('count')!=total:
                raise RuntimeError('Existing private raster cache does not match this trace')
            cached_files=cached_manifest.get('hashes',[])
            if len(cached_files)!=total:raise RuntimeError('Incomplete private raster manifest')
            cache_hit=True
    composition=None
    if experimental_orbit_optics:
        if raster_cache_dir is None or cache_key is None or preset_engine is None:
            raise ValueError('Experimental canonical export requires a private frame cache')
        from canonical_frame_cache import (CanonicalComposition,
                                           identity_for_composition)
        # A stable identity binds the *source* manifest, full camera plan,
        # explicit seed and renderer implementation. New edits/seed cannot
        # silently reuse an unrelated finished image.
        codefiles=[Path(__file__),Path(__file__).with_name('cinematic_stage.py'),
                   Path(__file__).with_name('stage_optics.py'),
                   Path(__file__).with_name('studio_motion_callouts.py')]
        identity=identity_for_composition(
            cache_key,preset_engine['framePlan'],optics_seed,codefiles)
        composition=CanonicalComposition(raster_cache_dir,identity,total)
    tmp=output.with_suffix('.video-only.mp4')
    encoder=subprocess.Popen([
      'ffmpeg','-hide_banner','-loglevel','error','-y',
      '-f','rawvideo','-pix_fmt','bgr24','-video_size',f'{MASTER_W}x{MASTER_H}',
      '-framerate',str(fps),'-i','pipe:0','-an',
      '-c:v','libx264','-preset','medium' if film_mode else 'veryfast',
      # CBR with filler keeps fine seeded grain above the 8 Mbps floor.
      # Default CRF=14 path remains byte-for-byte untouched.
      *(['-b:v','12M','-minrate','12M','-maxrate','12M',
         '-bufsize','24M','-x264-params','nal-hrd=cbr']
        if experimental_orbit_optics else
        ['-crf','14' if film_mode else '16']),
      '-pix_fmt','yuv420p','-g',str(fps*2),
      # x264's seven-thread rate control is not reproducible on this worker:
      # identical 75-frame inputs gave different decoded frame hashes.
      # The single-thread flagged encoder produced bit-identical MP4s.
      '-threads','1' if experimental_orbit_optics else '7',
      '-movflags','+faststart',str(tmp)
    ],stdin=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=10*1024*1024)
    timestamps=[float(e['t']) for e in session['events']]
    # Verified viewport scroll positions are a second directional motion
    # signal; a fast manual scroll receives a shutter even at 1x speed.
    initial_scroll=session['states'][0].get('visible',{})
    scroll_samples=[(0.,float(initial_scroll.get('x',0)),
                     float(initial_scroll.get('y',0)))]
    for event in session['events']:
        if event.get('type')!='scroll' or not isinstance(event.get('scroll'),dict):
            continue
        rel=float(event['t'])-start_ms
        if rel<0:continue
        scroll_samples.append((rel,float(event['scroll'].get('x',0)),
                               float(event['scroll'].get('y',0))))
    scroll_samples.sort(key=lambda q:q[0])
    scroll_times=[row[0] for row in scroll_samples]
    def scroll_at(ms:float)->tuple[float,float]:
        ix=max(0,bisect_right(scroll_times,ms)-1)
        return scroll_samples[ix][1:]
    clock_ms=0
    next_action=0
    next_check=0
    checks=[]
    visuals=[]
    checkpoints=[]
    rendered=0
    pending_result=None
    result_candidates=[]
    last_rendered_image=None
    added_hold={"holdFrames":0,"fadeFrames":0,"totalFrames":0}
    payoff_raw_source=None
    payoff_background_raw=None
    payoff_modal_box=None
    payoff_modal_radius=None
    payoff_pose=None
    payoff_tilt=None
    payoff_lift_factors=None
    payoff_perspective=None
    payoff_cursor=None
    if result_payoff_push and not result_aware_editorial:
        raise ValueError('Result payoff requires result-aware editorial')
    if result_payoff_push:
        from result_payoff import (
            FOCUS_ANCHOR_JS,create_payoff_plan,append_payoff)
    if result_aware_editorial:
        if fps!=60 or not preset_engine or preset_engine['preset']['id']!='3d-launch':
            raise ValueError('Result-aware editorial requires 3d-launch at 60fps')
        from result_reveal import RESULT_PROBE_JS,classify_result,append_result_hold
    def verify_completed_action(page, action_index, frame_index):
        """Assert source semantics before a later action can replace the UI.

        Two distinct source actions may land inside one output frame.
        Checks performed only after the frame's actions would see the wrong
        page, incorrectly rejecting a genuine action and result.
        """
        a=actions[action_index]
        if a.get('expect_selector'):
            loc=page.locator(a['expect_selector']).first
            ok=loc.count()>0 and bool(loc.evaluate(VISIBLE_PIXELS_JS))
            if not ok:raise RuntimeError('Semantic replay divergence: expected '+a['expect_selector'])
            checks.append({'frame':frame_index,'action':action_index,
                           'selector':a['expect_selector'],'passed':True})
        if a.get('expect_text'):
            loc=page.get_by_text(a['expect_text'],exact=False).first
            ok=loc.count()>0 and bool(loc.evaluate(VISIBLE_PIXELS_JS))
            if not ok:raise RuntimeError('Semantic replay divergence: expected text '+a['expect_text'])
            checks.append({'frame':frame_index,'action':action_index,
                           'text':a['expect_text'],'passed':True})
        if a.get('expect_selector') or a.get('expect_text'):
            proof=compare_verified_region(session_dir,session['states'][action_index+1],page,info['dpr'])
            if proof:visuals.append(proof)

    start_wall=time.monotonic()
    try:
      with sync_playwright() as pw:
        chromium=os.environ.get('SAUCE_CHROME_BIN') or '/opt/devmcp-browsers/chromium_headless_shell-1254/chrome-headless-shell-linux64/chrome-headless-shell'
        browser=pw.chromium.launch(headless=True,executable_path=chromium,
                                  args=['--no-sandbox','--disable-dev-shm-usage'])
        options={'viewport':{'width':source_w,'height':source_h},
           'device_scale_factor':info['dpr'],'service_workers':'block',
           'permissions':['clipboard-read','clipboard-write']}
        context=browser.new_context(**options)
        # Install before navigation, including frame zero. Identical rules
        # are used for first capture and deterministic browser replay.
        if film_mode:
            install_presentation_cleanup(context)
        if har:
            path=session_dir/'network.har'
            if not path.is_file():raise FileNotFoundError(path)
            context.route_from_har(str(path),not_found='abort',update=False)
        page=context.new_page()
        # Install before navigation, then pause at a later known timestamp.
        # Playwright can refuse pause_at() when called at or before a clock
        # that advanced during slow website initialization.
        page.clock.install(time=datetime(2026,1,1,0,0,tzinfo=timezone.utc))
        response=page.goto(session['source_url'],wait_until='domcontentloaded',timeout=30000)
        if response and response.status>=400:raise RuntimeError('Replay page unavailable')
        # Hydrate React/Vue/event listeners and load fonts before freezing time.
        page.wait_for_timeout(1200 if session['source_url'].startswith('https://') else 200)
        page.evaluate('document.fonts.ready')
        if actions and actions[0]['action']=='approach':
            page.locator(actions[0]['selector']).first.scroll_into_view_if_needed()
            page.wait_for_timeout(260)
        page.clock.pause_at(datetime(2026,1,1,1,0,tzinfo=timezone.utc))
        hidden_decoration_count=0
        if film_mode and presentation_hide_selector:
            # Strictly opt-in for specific decorative elements. Raw capture
            # evidence is unmodified; film-mode replay may hide the element
            # ONLY when the operator explicitly requests it.
            selector=presentation_hide_selector
            if len(selector)>180 or any(k in selector for k in ('{','}',';','<','>')):
                raise ValueError('Invalid presentation-only selector')
            hidden_decoration_count=page.locator(selector).count()
            if hidden_decoration_count:
                page.add_style_tag(content=selector+' { visibility: hidden !important; }')
                assert page.locator(selector).first.evaluate(
                    "e=>getComputedStyle(e).visibility")=='hidden'
            else:
                raise RuntimeError('Requested presentation element not found: '+selector)
        if film_mode:
            # Reinforce cleanup after hydration if the app replaced <head>.
            page.add_style_tag(content=PRESENTATION_CLEANUP_STYLE)
        if vector_mode:
            # Chromium only renders the REAL app; SVG cursor is composited
            # in the video layer. Hide every native/DOM CSS cursor state.
            page.add_style_tag(content='html,body,html *,html *::before,html *::after {cursor:none !important;}')
            if page.locator('button').count():
                actual=page.locator('button').first.evaluate(
                    '(e)=>getComputedStyle(e).cursor')
                if actual!='none':
                    raise RuntimeError('Native cursor suppression failed: '+actual)
        page.evaluate(ANIMATION_DRIVER)
        page.evaluate('window.__sauceAnimationControls.settleInitial()')
        animated_frames=0
        for index in range(total):
            wanted_ms=(round(float(frame_map[index]['sourceMs']))
                       if frame_map else round(index*1000/fps))
            source_index=min(source_total-1,max(0,round(wanted_ms*fps/1000)))
            last_source_index=(min(source_total-1,max(0,round(
                float(frame_map[index-1]['sourceMs'])*fps/1000)))
                if frame_map and index>0 else max(0,source_index-1))
            if wanted_ms<clock_ms:raise RuntimeError('Studio time mapping reversed')
            delta=wanted_ms-clock_ms
            if delta>0:page.clock.run_for(delta)
            clock_ms=wanted_ms
            # Real mouse movement is replayed at the output frame rate,
            # unlike Playwright's eager mouse.move(steps=N) loop. The DOM's
            # hover treatment and the visible cursor use the same spring path.
            if cursor and samples and wanted_ms/1000.>=samples[0][0]:
                mx,my=cursor[source_index]
                page.mouse.move(mx,my)
            while next_action<len(actions) and stored[next_action]['at_ms']-start_ms<=wanted_ms:
                # Verify an older state before the next click/navigation can
                # invalidate it within the SAME output frame.
                for prior in source_checks_before_action(stored,next_check,next_action):
                    verify_completed_action(page,prior,index)
                    next_check=prior+1
                a=actions[next_action]
                if result_aware_editorial and a['action']=='click':
                    # Comparison is local to Chromium and exports no text,
                    # keys, command content or hashes of product copy.
                    page.evaluate(RESULT_PROBE_JS,'before')
                    pending_result={'clickIndex':next_action,'sourceMs':wanted_ms,
                                    'deadlineMs':wanted_ms+600}
                execute_action(page,a)
                next_action+=1
            if result_aware_editorial and pending_result is not None:
                observed=page.evaluate(RESULT_PROBE_JS,'after')
                found=classify_result(observed,pending_result['sourceMs'])
                if found is not None:
                    found['clickIndex']=pending_result['clickIndex']
                    result_candidates.append(found)
                    pending_result=None
                elif wanted_ms>=pending_result['deadlineMs']:
                    pending_result=None
            animated_frames+=int(page.evaluate('(ms)=>window.__sauceAnimationControls.step(ms)',wanted_ms))
            if film_mode:
                # Independent CSS scale multiplies the site's native
                # Web Animations. A physically damped 0.95 -> 1.0 emphasis
                # only runs while the REAL modal has just opened.
                age=(wanted_ms-(first_dialog_ms-start_ms))/1000 if first_dialog_ms else -1.
                amount=modal_spring_scale(age) if 0<=age<=.35 else 1.
                page.evaluate("""s=>{
                  const d=document.querySelector('[role=dialog]');
                  if(d) {
                    d.style.scale=s.toFixed(6);
                    d.style.transformOrigin='center center';
                  }
                }""",amount)
            while (next_check<len(actions) and next_check<next_action and
                   stored[next_check]['end_ms']-start_ms<=wanted_ms):
                verify_completed_action(page,next_check,index)
                next_check+=1
            if cache_hit:
                raw=raster_cache_dir/f'{index:05d}.png'
                if not raw.is_file() or hashlib.sha256(raw.read_bytes()).hexdigest()!=cached_files[index]:
                    raise RuntimeError('Canonical source frame hash mismatch: '+str(raw))
                decoded=cv2.imread(str(raw),cv2.IMREAD_COLOR)
            else:
                # The original page briefly fades a real dialog across its
                # decorative terminal. For this opt-in Brimble presentation,
                # capture the genuinely mounted dialog at its final native
                # opacity only during those verified overlap frames. Restore
                # Chromium's original CSS before any further page action.
                opening_box=(modal_hints[-1]['box'] if
                             film_mode and hide_brimble_terminal and modal_hints
                             else None)
                with stabilized_verified_dialog_opening(page,opening_box) as stabilized:
                    png=page.screenshot(scale='device',animations='allow',caret='hide')
                stabilized_opening_frames+=int(stabilized)
                decoded=cv2.imdecode(np.frombuffer(png,dtype=np.uint8),cv2.IMREAD_COLOR)
            if decoded is None or decoded.shape[:2]!=(source_px_h,source_px_w):
                raise RuntimeError(f'Invalid Chromium frame {index}')
            if raster_cache_dir is not None and not cache_hit:
                raw=raster_cache_dir/f'{index:05d}.png'
                if not cv2.imwrite(str(raw),decoded,[cv2.IMWRITE_PNG_COMPRESSION,3]):
                    raise RuntimeError('Could not write private canonical source')
                cached_files.append(hashlib.sha256(raw.read_bytes()).hexdigest())
            preset_pose=(preset_frames[index]['camera'] if preset_frames else None)
            if preset_pose:
                z=float(preset_pose['scale'])
                fx=float(preset_pose['focusX'])
                fy=float(preset_pose['focusY'])
            else:
                z,fx,fy=camera[source_index]
            factor=(ww/source_px_w)*z
            dx=ww/2-fx*info['dpr']*factor
            dy=wh/2-fy*info['dpr']*factor
            dx=max(ww-source_px_w*factor,min(0.,dx))
            dy=max(wh-source_px_h*factor,min(0.,dy))
            matrix=np.array([[factor,0,dx],[0,factor,dy]],dtype=np.float32)
            source=cv2.warpAffine(decoded,matrix,(ww,wh),
                   flags=cv2.INTER_LANCZOS4 if film_mode else cv2.INTER_LINEAR,
                   borderMode=cv2.BORDER_REPLICATE)
            if backdrop_focus and not preset_pose and first_dialog_ms is not None:
                age_ms=wanted_ms-(first_dialog_ms-start_ms)
                if age_ms>0:
                    progress=min(1.,age_ms/280.)
                    smooth=progress*progress*(3-2*progress)
                    dialog=page.get_by_role('dialog').first
                    bounds=dialog.bounding_box() if dialog.count() else None
                    if bounds:
                        # Depth separation happens at the 1600x900 final
                        # browser size, preserving full-res source and speed.
                        projected={
                          'x':dx+bounds['x']*info['dpr']*factor,
                          'y':dy+bounds['y']*info['dpr']*factor,
                          'width':bounds['width']*info['dpr']*factor,
                          'height':bounds['height']*info['dpr']*factor,
                        }
                        source=background_focus(source,projected,1,mix=.37*smooth)
            if code_foci:
                current=active_code_focus(code_foci,start_ms+wanted_ms)
                if current:
                    source=highlight_code_region(source,current,z,dx,dy,
                                                 info['dpr'],factor)
            if frame_map and index not in beat_cut_frames:
                # An executed cut is a discontinuity, never motion blur.
                speed=float(frame_map[index]['speed'])
                if preset_frames:
                    prior=preset_frames[max(0,index-1)]['camera']
                    prev_z,prev_cx,prev_cy=(float(prior['scale']),
                       float(prior['focusX']),float(prior['focusY']))
                else:
                    prev_z,prev_cx,prev_cy=camera[last_source_index]
                # Blur only follows observed camera/scroll displacement.
                # Static UI remains sharp even when idle time is accelerated.
                vx=(prev_cx-fx)*z*(ww/source_w)
                vy=(prev_cy-fy)*z*(wh/source_h)
                last_ms=(float(frame_map[index-1]['sourceMs']) if index else 0.)
                sx0,sy0=scroll_at(last_ms)
                sx1,sy1=scroll_at(wanted_ms)
                vx+=(sx0-sx1)*factor*info['dpr']
                vy+=(sy0-sy1)*factor*info['dpr']
                if math.hypot((sx1-sx0),(sy1-sy0))>15:
                    speed=max(speed,2.2)
                source=directional_blur(source,vx,vy,speed)
            if root_stage:
                # One root export with perspective studio floor and overlays.
                frame_tilt=((float(preset_pose['rotateXDeg']),
                             float(preset_pose['rotateYDeg']))
                            if preset_pose else tilt_track[source_index])
                perspective=(float(preset_pose['perspectivePx'])
                             if preset_pose else 1820.)
                active_spotlight=(preset_pose is not None and
                     bool(preset_pose.get('spotlightActive')) and
                     bool(preset_pose.get('spotlightBox')))
                if active_spotlight:preset_spotlight_frames+=1
                spotlight=({'active':True,
                    'box':preset_pose['spotlightBox'],
                    'blurPx':min(6.,float(preset_pose['spotlightBlurPx'])),
                    'dimOpacity':float(preset_pose['spotlightDimOpacity']),
                    'factor':info['dpr']*factor,'dx':dx,'dy':dy}
                    if active_spotlight else None)
                foreground=None
                background_source=source
                live_modal_hold=False
                # A verified dialog can remain visible after the planner's
                # nominal 2400ms hero lifetime. Hide its terminal until the
                # actual DOM closes, rather than resurrecting it in the outro.
                if (hide_brimble_terminal and modal_hints
                    # A transient copied-command feature spotlight can
                    # outlive the planner's foregroundId, while Chromium's
                    # dialog stays open. Keep the real modal plane in front
                    # even across that feature highlight rather than briefly
                    # returning to the black terminal background.
                    and (spotlight is None or
                         not preset_frames[index].get('foregroundId'))
                    and not any(e.get('type') in
                        ('dialog-hidden','dialog-closed','modal-close','modal-closed')
                        and e['t']-start_ms<=wanted_ms
                        for e in session['events'])):
                    live=page.get_by_role('dialog').first
                    if live.count() and live.is_visible():
                        spotlight={'active':True,
                            'box':modal_hints[-1]['box'],
                            'blurPx':6.,'dimOpacity':.25,
                            'factor':info['dpr']*factor,'dx':dx,'dy':dy}
                        live_modal_hold=True
                # The live DOM may display the modal before the delayed trace
                # dialog-visible event. Hints only identify its expected real
                # bounds; a genuinely visible dialog is mandatory to lift.
                expected_box=(modal_hints[-1]['box'] if live_modal_hold else
                    expected_modal_box(modal_hints,
                        preset_frames[index].get('foregroundId'),wanted_ms))
                if spotlight is not None and expected_box is not None:
                    clean=verified_modal_background(
                        page,expected_box,(source_px_h,source_px_w),
                        hide_dark_panel=hide_brimble_terminal)
                    if clean is not None:
                        clean_pixels,live_box,radius_css,terminal_hidden=clean
                        concealed_terminal_frames+=int(terminal_hidden)
                        background_source=cv2.warpAffine(clean_pixels,matrix,(ww,wh),
                            flags=cv2.INTER_LANCZOS4 if film_mode else cv2.INTER_LINEAR,
                            borderMode=cv2.BORDER_REPLICATE)
                        spotlight['box']=live_box
                        foreground={'source':source,'box':live_box,
                                    'radiusCss':radius_css}
                        # Retain the *genuine* 2x Chromium modal and clean H0
                        # plate from the final verified frame for a native
                        # re-rendered 3D command close-up. No raster zoom.
                        if result_payoff_push and index==total-1:
                            payoff_raw_source=decoded.copy()
                            payoff_background_raw=clean_pixels.copy()
                            payoff_modal_box=dict(live_box)
                            payoff_modal_radius=float(radius_css)
                            payoff_pose=dict(preset_pose)
                            payoff_tilt=tuple(frame_tilt)
                            payoff_perspective=float(perspective)
                            payoff_cursor=(tuple(cursor[source_index])
                                           if cursor else None)
                        multi_plane_frames+=1
                        live_modal_hold_frames+=int(live_modal_hold)
                    else:
                        if live_modal_hold:
                            # No verified modal pixels; never invent a layer.
                            spotlight=None
                        else:
                            single_plane_fallback_frames+=1
                if modal_lift_timeline is not None:
                    # Evidence is satisfied only after replay verifies genuine
                    # modal pixels, live geometry and a clean H0 browser plate.
                    if foreground is None:
                        modal_lift_timeline.release('verified-dialog')
                    else:
                        effect=modal_lift_timeline.sample(
                            family='semantic-layer-separation',
                            target_id='verified-dialog',frame=index,
                            evidence=VerifiedEffectEvidence(
                                real_pixels=True,stable_geometry=True,
                                clean_background=True,single_projected_cursor=True))
                        foreground['depthPx']=DEPTH_PX*effect.depth_fraction
                        spotlight['blurPx']=MAX_BACKGROUND_BLUR*effect.background_focus_fraction
                        spotlight['dimOpacity']=.18*effect.background_focus_fraction
                        if result_payoff_push and index==total-1:
                            payoff_lift_factors=(foreground['depthPx'],
                                spotlight['blurPx'],spotlight['dimOpacity'])
                        modal_lift_frames+=int(effect.progress<1.)
                protected_text=None
                if foreground is not None and hide_brimble_terminal:
                    # Real DOM text range is narrower than the clickable span.
                    protected_text=page.evaluate("""() => {
                      const dialog=document.querySelector('[role=dialog]');
                      if(!dialog)return null;
                      const el=[...dialog.querySelectorAll('span')].find(
                        n=>n.textContent.trim()==='Codex');
                      if(!el)return null;
                      const range=document.createRange();
                      range.selectNodeContents(el);
                      const r=range.getBoundingClientRect();
                      return r.width>8&&r.height>8 ? {
                        x:r.x,y:r.y,width:r.width,height:r.height} : null;
                    }""")
                def draw_overlays(final):
                    if callout_renderer is not None:
                        callout_renderer.draw(final,index,
                            info['dpr']*factor,dx,dy,frame_tilt,root_stage.window,
                            focal=perspective)
                    root_cursor.draw(final,
                        cursor[source_index] if cursor else None,wanted_ms/1000.,
                        info['dpr']*factor,dx,dy,tilt=frame_tilt,focal=perspective,
                        foreground_box=foreground['box'] if foreground else None,
                        protected_text_box=protected_text,
                        foreground_depth=foreground.get('depthPx',DEPTH_PX)
                            if foreground else DEPTH_PX)
                output_image=root_stage.render(
                    background_source,cinematic_cursor=draw_overlays,tilt=frame_tilt,
                    glow=audio_levels[source_index] if audio_levels is not None else 0.,
                    perspective_px=perspective,spotlight=spotlight,
                    foreground=foreground,frame_index=index,
                    diff_reveal=({'commit':diff_reveals[preset_frames[index]['diffId']],
                                  'progress':preset_frames[index]['diffProgress']}
                       if preset_frames and preset_frames[index].get('diffId') in diff_reveals
                          # A separate 600px commit card peels out on the right and
                          # looks like an accidental cut-off terminal behind
                          # Brimble's genuine open dialog. The real command is
                          # already visible; never cover or shrink its source UI.
                          and not (hide_brimble_terminal and foreground is not None)
                       else None))
            else:
                output_image=base.copy()
                area=output_image[wy:wy+wh,wx:wx+ww]
                area[:]=np.uint8(area.astype(np.float32)*(1-clip)+source*clip)
            if root_stage:
                # CinematicStage has already drawn CinematicCursor above the
                # site. Do not fall through to any legacy native cursor.
                pass
            elif presentation_v14:
                # MIT Tabler SVG assets, black fill / outline variants.
                paint_click_ripple(output_image,session['events'],start_ms,
                                   wanted_ms/1000.,info['dpr']*factor,dx,dy)
                if cursor:
                    render_tabler_cursor(output_image,cursor[source_index],
                        session['events'],start_ms,wanted_ms/1000.,
                        info['dpr']*factor,dx,dy,cursor_style)
            elif presentation_v13:
                # Preserve previous SVG treatment for A/B.
                paint_click_ripple(output_image,session['events'],start_ms,
                                   wanted_ms/1000.,info['dpr']*factor,dx,dy)
                if cursor:
                    paint_svg_pointer(output_image,cursor[source_index],session['events'],
                                       start_ms,wanted_ms/1000.,info['dpr']*factor,dx,dy)
            elif presentation_v12:
                # Perceived click must remain visible. Draw feedback first,
                # pointer second; CSS cursor:none NEVER hides this overlay.
                click_feedback(output_image,session['events'],start_ms,index/fps,
                               info['dpr']*factor,dx,dy)
                if cursor:
                    t=start_ms+wanted_ms
                    k=max(0,bisect_right(timestamps,t)-1)
                    pointer_css=session['events'][k].get('cursor','default')
                    compose_cursor(output_image,cursor_art,pointer_css,cursor[source_index],
                                   info['dpr']*factor,dx,dy,actionable_boxes,
                                   wanted_ms/1000.,start_ms,session['events'])
            else:
                if cursor and samples and wanted_ms/1000.>=samples[0][0]:
                    t=start_ms+wanted_ms
                    k=max(0,bisect_right(timestamps,t)-1)
                    pointer_css=session['events'][k].get('cursor','default')
                    overlay_native_cursor(output_image,cursor_art,cursor[source_index],
                                pointer_css,info['dpr']*factor,dx,dy)
                if click_effect:
                    overlay_click(output_image,session['events'],start_ms,index/fps,
                                  info['dpr']*factor,dx,dy)
            if cursorless_source:
                # Bounded opt-in export for the existing source-verified film
                # plan. Chromium's genuine DPR2 pixels have NO raster cursor;
                # the separate compositor draws exactly one source-timed pointer.
                # This path intentionally bypasses every legacy stage/backdrop
                # and presentation overlay. The site's native aspect stays 16:9.
                if source_px_w*MASTER_H != source_px_h*MASTER_W:
                    raise ValueError("Cursorless export cannot distort source aspect ratio")
                output_image=cv2.resize(decoded,(MASTER_W,MASTER_H),
                                        interpolation=cv2.INTER_LANCZOS4)
            if composition is not None:
                # Real Chromium actions/semantic checks always execute.
                # Export only the versioned verified composited-frame proof.
                output_image=composition.use(index,output_image)
            encoder.stdin.write(output_image.tobytes())
            if result_aware_editorial:
                last_rendered_image=output_image.copy()
            rendered+=1
            if index%screenshot_step==0 or index==total-1:
                save=session_dir/f'replay-frame-{index:04d}.jpg'
                cv2.imwrite(str(save),output_image,[cv2.IMWRITE_JPEG_QUALITY,84])
                checkpoints.append({'frame':index,'sha256':hashlib.sha256(save.read_bytes()).hexdigest(),
                                    'file':save.name})
            if index%60==0:print('REPLAY',index,'of',total,'elapsed',round(time.monotonic()-start_wall,1),flush=True)
        if expected_text:
            page.get_by_text(expected_text,exact=True).first.wait_for(state='visible',timeout=3000)
        if result_aware_editorial and result_candidates:
            last_click=max((i for i,a in enumerate(actions) if a['action']=='click'),
                           default=-1)
            evidence=next((r for r in reversed(result_candidates)
                           if r['clickIndex']==last_click
                           and (frame_map[-1]['sourceMs'] if frame_map else length*1000)
                               -r['sourceMs']<=2600),None)
            if evidence:
                # An actual post-click <pre>/output is a source-backed
                # cinematic payoff. Otherwise keep the existing evidence
                # bounded reading hold (never manufacture a result).
                payoff_plan=None
                if result_payoff_push and payoff_raw_source is not None:
                    anchor=page.evaluate(FOCUS_ANCHOR_JS)
                    payoff_plan=create_payoff_plan(
                        evidence,anchor,payoff_pose)
                if payoff_plan is None:
                    added_hold=append_result_hold(
                        encoder,last_rendered_image,fps,evidence)
                else:
                    def render_payoff_pose(zoom,focus_x,focus_y,shot_frame):
                        # Use the exact same H0/H60 compositor from the last
                        # frame, but re-warp the original 2x browser pixels.
                        # Resampling the *finished* MP4 would soften code text.
                        scale=ww/source_px_w*zoom
                        shift_x=max(ww-source_px_w*scale,
                                    min(0.,ww/2-focus_x*info['dpr']*scale))
                        shift_y=max(wh-source_px_h*scale,
                                    min(0.,wh/2-focus_y*info['dpr']*scale))
                        affine=np.float32([[scale,0,shift_x],
                                           [0,scale,shift_y]])
                        foreground_source=cv2.warpAffine(
                            payoff_raw_source,affine,(ww,wh),
                            flags=cv2.INTER_LANCZOS4,
                            borderMode=cv2.BORDER_REPLICATE)
                        clean_source=cv2.warpAffine(
                            payoff_background_raw,affine,(ww,wh),
                            flags=cv2.INTER_LANCZOS4,
                            borderMode=cv2.BORDER_REPLICATE)
                        foreground={'source':foreground_source,
                                    'box':payoff_modal_box,
                                    'radiusCss':payoff_modal_radius}
                        spotlight={'active':True,'box':payoff_modal_box,
                                   'blurPx':6.,'dimOpacity':.25,
                                   'factor':info['dpr']*scale,
                                   'dx':shift_x,'dy':shift_y}
                        if payoff_lift_factors is not None:
                            depth,blur,dim=payoff_lift_factors
                            foreground['depthPx']=depth
                            spotlight.update(blurPx=blur,dimOpacity=dim)
                        frame=root_stage.render(
                            clean_source,tilt=payoff_tilt,glow=0.,
                            perspective_px=payoff_perspective,
                            spotlight=spotlight,foreground=foreground,
                            frame_index=total+shot_frame)
                        # The final shot is editorial camera motion; fade
                        # out the pointer rather than inventing a new click
                        # or letting the cursor cover the generated command.
                        if payoff_cursor is not None and shot_frame<12:
                            overlay=frame.copy()
                            root_cursor.draw(
                                overlay,payoff_cursor,
                                frame_map[-1]['sourceMs']/1000.,
                                info['dpr']*scale,shift_x,shift_y,
                                tilt=payoff_tilt,focal=payoff_perspective,
                                foreground_box=payoff_modal_box,
                                foreground_depth=foreground.get('depthPx',DEPTH_PX))
                            from result_payoff import ease
                            opacity=1-ease(shot_frame/12)
                            frame=np.uint8(np.rint(
                                frame.astype(np.float32)*(1-opacity)+
                                overlay.astype(np.float32)*opacity))
                        return frame
                    added_hold=append_payoff(
                        encoder,last_rendered_image,payoff_plan,
                        render_payoff_pose,fps)
                rendered+=added_hold['totalFrames']
        context.close();browser.close()
        if composition is not None:
            composition.finish()
        if raster_cache_dir is not None and not cache_hit:
            manifest={'schema':1,'identity':cache_key,'count':total,
                      'hashes':cached_files,'private':True}
            tmp_manifest=raster_cache_dir/'manifest.tmp.json'
            tmp_manifest.write_text(json.dumps(manifest,indent=2))
            tmp_manifest.replace(cache_manifest)
    finally:
        if encoder.stdin:
            try:encoder.stdin.close()
            except Exception:pass
        err=encoder.stderr.read().decode(errors='replace') if encoder.stderr else ''
        rc=encoder.wait(timeout=90)
        if rc!=0:raise RuntimeError('Frame encoder failed: '+err[-1400:])
    tmp.replace(output)
    subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(output),
                    '-f','null','-'],check=True,timeout=90)
    report={'mode':'replayed-real-dom','source':session['source_url'],
            'video':str(output),'width':MASTER_W,'height':MASTER_H,
            'fps':fps,'frames':rendered,
            'seconds':rendered/fps,
            'source_seconds':length,
            'raster_cache':({'private':True,'reused':cache_hit,'frames':total}
                             if raster_cache_dir is not None else None),
            'canonical_composition':({
                'private':True,'reused':composition.reused,
                'frames':total,'identity':composition.identity,
                'live_frame_divergences':composition.live_diff_frames
                } if composition is not None else None),
            'studio_motion':({'enabled':True,
                'output_duration_ms':studio_motion_plan['outputDurationMs'],
                'source_duration_ms':studio_motion_plan['sourceDurationMs'],
                'speed_peak':max(t['speed'] for t in frame_map),
                'dead_zones':len(studio_motion_plan['deadZones']),
                'protected_actions':len(studio_motion_plan['actionWindows']),
                'callouts':len(studio_motion_plan['callouts']),
                'studio_floor':root_stage.enable_studio_floor}
                if studio_motion_plan else None),
            'capture_state_hashes_checked':len(session['states']),
            'events':len(session['events']),
            'applied_actions':next_action,
            'camera_cues':camera_cues,
            'editorial_background_focus':bool(backdrop_focus),
            'presentation_v12':bool(presentation_v12),
            'presentation_v13':bool(presentation_v13),
            'presentation_v14':bool(presentation_v14),
            'presentation_v15':bool(presentation_v15),
            'editorial_closeup':bool(editorial_closeup),
            'cinematic_stage_root':bool(root_stage),
            'spatial_parallax':bool(spatial_parallax and root_stage),
            'preset':preset_engine['preset']['id'] if preset_engine else None,
            'preset_camera_frames':len(preset_frames) if preset_frames else 0,
            'result_aware_editorial':bool(result_aware_editorial),
            'result_payoff_push':bool(result_payoff_push),
            'result_evidence':(result_candidates[-1] if result_candidates else None),
            'result_hold':added_hold,
            'spotlight_frames':preset_spotlight_frames,
            'beat_cut_frames':sorted(beat_cut_frames),
            'multi_plane_frames':multi_plane_frames,
            'modal_lift_transition_frames':modal_lift_frames,
            'concealed_terminal_frames':concealed_terminal_frames,
            'stabilized_opening_frames':stabilized_opening_frames,
            'live_modal_hold_frames':live_modal_hold_frames,
            'single_plane_fallback_frames':single_plane_fallback_frames,
            'preset_perspective_px':preset_engine['preset']['camera']['perspectivePx']
                if preset_engine else None,
            'max_abs_tilt_degrees':round(max(
                max(abs(t[0]),abs(t[1])) for t in tilt_track),4),
            'semantic_ast_foci':[{'file':f.file,'symbol':f.name,
               'type':f.kind,'line_start':f.line_start,'line_end':f.line_end}
               for f in code_foci],
            'audio_reactive_frames':len(audio_levels) if audio_levels is not None else 0,
            'cinematic_stage_window':list(root_stage.window) if root_stage else None,
            'cinematic_stage_background':root_stage.background_hex if root_stage else None,
            'procedural_backdrop_style':root_stage.backdrop_style if root_stage else None,
            'brand_tokens':session.get('brand_tokens'),
            'studio_brand_primary':brand_primary if root_stage else None,
            'studio_brand_accent':brand_accent if root_stage else None,
            'cursorless_source':bool(cursorless_source),
            'experimental_orbit_optics':bool(experimental_orbit_optics),
            'optics_seed':root_stage.optics_seed if root_stage else None,
            'cinematic_stage_glow_blur':140 if root_stage else None,
            'cinematic_stage_backdrop_blur':24 if root_stage else None,
            'cursor_component':'CinematicCursor' if root_stage else None,
            'cursor_scale':cursor_scale if presentation_v15 else None,
            'cursor_style':cursor_style if (presentation_v14 or presentation_v15) else None,
            'cursor_asset':('assets/cursors/reference-v15/black-rounded.svg' if cursor_style=='ink' else 'assets/cursors/reference-v15/white-outline.svg') if presentation_v15 else (('assets/cursors/tabler/pointer-filled.svg' if cursor_style=='ink' else 'assets/cursors/tabler/pointer-outline.svg') if presentation_v14 else ('assets/cursors/sauce-pointer.svg' if presentation_v13 else 'native-x11')),
            'native_cursor_suppressed':bool(vector_mode),
            'stage':'dark-ambient-multilayer' if vector_mode else 'light',
            'cursor_visibility':'reference-svg-overlay-always-visible' if presentation_v15 else ('tabler-svg-overlay-always-visible' if presentation_v14 else ('svg-overlay-always-visible' if presentation_v13 else ('persistent' if presentation_v12 else 'respect-site-css'))),
            'click_feedback':'reference-pointer-contract-0.88+svg-ripple' if presentation_v15 else ('tabler-pointer-contract-0.85+svg-ripple' if presentation_v14 else ('svg-pointer-contract-0.85+svg-ripple' if presentation_v13 else ('physical press+ring' if presentation_v12 else ('ring' if click_effect else 'disabled')))),
            'presentation_only_hidden_selector':presentation_hide_selector if film_mode else None,
            'presentation_only_hidden_count':hidden_decoration_count,
            'pixel_resampling':'Lanczos4' if film_mode else 'linear',
            'source_dpr':info['dpr'],
            'encoder_profile':{'crf':14 if film_mode else 16,
                               'preset':'medium' if film_mode else 'veryfast'},
            'semantic_checks':checks,
            'animated_frame_effects':animated_frames,
            'visual_region_checks':visuals,
            'animation_mode':'original CSS/Web Animation keyframes, frame-clock seeking',
            'verified_semantics':bool(checks),
            'cursor_types':sorted({cursor_class(v.get('cursor')) for v in session['events']}),
            'snapshots':checkpoints,
            'elapsed_wall_sec':round(time.monotonic()-start_wall,1),
            'limitations':['Browser-clock control cannot guarantee reproducibility of arbitrary remote JS and networking.',
              'CSS/native animations may not render identically across platforms.',
              'Replay is permitted only for pages/actions the operator is authorized to automate.']}
    (session_dir/'replay-report.json').write_text(json.dumps(report,indent=2))
    return report

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument('--session',type=Path,required=True)
    cli.add_argument('--workflow',type=Path,required=True)
    cli.add_argument('--output',type=Path,required=True)
    cli.add_argument('--fps',type=int,default=60)
    cli.add_argument('--seconds',type=float)
    cli.add_argument('--har',action='store_true')
    cli.add_argument('--expect-text')
    cli.add_argument('--click-effect',action='store_true')
    cli.add_argument('--click-water-ripple',action='store_true',
        help='Refract genuine click positions in the composed video, opt-in')
    cli.add_argument('--presentation-hide-selector',
       help='Optional decorative selector to suppress only in presentation replay')
    cli.add_argument('--raw-replay',action='store_true',
       help='Opt out of the default cinematic presentation (debug/legacy mode)')
    cli.add_argument('--cursorless-source',action='store_true',
       help='Opt-in native Chromium pixels for a separate hash-pinned film plan; never paints a cursor or stage')
    cli.add_argument('--presentation-v15',action='store_true',
       help='Reference-shaped rounded pointer with deep drop shadow (default)')
    cli.add_argument('--presentation-v14',action='store_true',
       help='MIT Tabler SVG cursor, fixed hotspot, click ripple and dark stage')
    cli.add_argument('--cursor-scale',type=float,default=CURSOR_FILM_SCALE,
       help='Size of the reference cursor relative to its vector master; default 0.56 (about 32x39px)')
    cli.add_argument('--cursor-style',choices=('ink','outline'),default='ink',
       help='Black body with white rim, or white body with black outline')
    cli.add_argument('--presentation-v13',action='store_true',
       help='Dark cinematic SVG-only pointer film renderer')
    cli.add_argument('--presentation-v12',action='store_true',
        help='Persistent native cursor, press feedback, layered shadows, ambient glow, Lanczos source resampling, subtle native-modal spring emphasis')
    cli.add_argument('--backdrop-focus',action='store_true',
       help='Blur only real pixels behind the verified modal; never alters the modal itself')
    args=cli.parse_args()
    chosen=[args.presentation_v12,args.presentation_v13,args.presentation_v14,
            args.presentation_v15]
    if sum(map(bool,chosen))>1:
        cli.error('Choose one presentation version')
    if args.raw_replay and any(chosen):
        cli.error('--raw-replay is incompatible with a presentation version')
    if args.cursorless_source and (not args.raw_replay or args.click_effect or
                                   args.click_water_ripple or args.backdrop_focus):
        cli.error('--cursorless-source requires --raw-replay without compositor effects')
    if not args.raw_replay and not any(chosen):
        # The polished reference-shaped vector cursor is the new film
        # default. Older versions and unstyled source replay stay opt-in.
        args.presentation_v15=True
    result=replay(args.session,args.workflow,args.output,args.fps,args.seconds,
                  args.har,expected_text=args.expect_text,
                  click_effect=args.click_effect,backdrop_focus=args.backdrop_focus,
                  click_water_ripple=args.click_water_ripple,
                  presentation_v12=args.presentation_v12,
                  presentation_hide_selector=args.presentation_hide_selector,
                  presentation_v13=args.presentation_v13,
                  presentation_v14=args.presentation_v14,cursor_style=args.cursor_style,
                  presentation_v15=args.presentation_v15,cursor_scale=args.cursor_scale,
                  cursorless_source=args.cursorless_source)
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
