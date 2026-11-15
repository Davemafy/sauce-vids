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
from studio_motion_blur import directional_blur
from studio_motion_callouts import KineticCalloutRenderer
from spatial_parallax import inertial_tilt_track
from code_semantics import (plan_focus_cues,semantic_camera_track,
                            active_code_focus,highlight_code_region)
from session_capture import MOCKUP_SCROLLBAR_STYLE
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
            'states':[(v['name'],v['at_ms'],v['sha256']) for v in session['states']],
            'events':session['events'],
            'workflow':workflow,
            'source_frame_times_ms':times,
            'hidden_decorative_selector':hide_selector,
            'capture_dpr':session['page'].get('dpr',2)}
    return hashlib.sha256(json.dumps(stable,sort_keys=True,
               ensure_ascii=True,separators=(',',':')).encode()).hexdigest()


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
           raster_cache_dir:Path|None=None) -> dict:
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
    preset_spotlight_frames=0
    film_mode=presentation_v12 or presentation_v13 or presentation_v14 or presentation_v15
    vector_mode=presentation_v13 or presentation_v14 or presentation_v15
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
    if studio_motion_plan and not presentation_v15:
        raise ValueError('StudioMotion requires root CinematicStage')
    root_stage=(CinematicStage(
        enable_studio_floor=bool(floor_config.get('enabled',False)),
        floor_reflection_intensity=float(floor_config.get('reflectionIntensity',.25))
    ) if presentation_v15 else None)
    callout_renderer=(KineticCalloutRenderer(
        studio_motion_plan.get('callouts',[]),fps=fps) if studio_motion_plan else None)
    root_cursor=(CinematicCursor(root_stage,session['events'],start_ms,
                  cursor_style,cursor_scale) if root_stage else None)
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
    tmp=output.with_suffix('.video-only.mp4')
    encoder=subprocess.Popen([
      'ffmpeg','-hide_banner','-loglevel','error','-y',
      '-f','rawvideo','-pix_fmt','bgr24','-video_size',f'{MASTER_W}x{MASTER_H}',
      '-framerate',str(fps),'-i','pipe:0','-an',
      '-c:v','libx264','-preset','medium' if film_mode else 'veryfast',
      '-crf','14' if film_mode else '16',
      '-pix_fmt','yuv420p','-g',str(fps*2),'-threads','7',
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
            # Hide grey native scrollbars in drawers without disabling scrolling.
            page.add_style_tag(content=MOCKUP_SCROLLBAR_STYLE)
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
                execute_action(page,actions[next_action])
                next_action+=1
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
            while next_check<len(actions) and stored[next_check]['end_ms']-start_ms<=wanted_ms:
                a=actions[next_check]
                if a.get('expect_selector'):
                    loc=page.locator(a['expect_selector']).first
                    ok=loc.count()>0 and bool(loc.evaluate(VISIBLE_PIXELS_JS))
                    if not ok:raise RuntimeError('Semantic replay divergence: expected '+a['expect_selector'])
                    checks.append({'frame':index,'action':next_check,'selector':a['expect_selector'],'passed':True})
                if a.get('expect_text'):
                    loc=page.get_by_text(a['expect_text'],exact=False).first
                    ok=loc.count()>0 and bool(loc.evaluate(VISIBLE_PIXELS_JS))
                    if not ok:raise RuntimeError('Semantic replay divergence: expected text '+a['expect_text'])
                    checks.append({'frame':index,'action':next_check,'text':a['expect_text'],'passed':True})
                if a.get('expect_selector') or a.get('expect_text'):
                    proof=compare_verified_region(session_dir,session['states'][next_check+1],page,info['dpr'])
                    if proof:visuals.append(proof)
                next_check+=1
            if cache_hit:
                raw=raster_cache_dir/f'{index:05d}.png'
                if not raw.is_file() or hashlib.sha256(raw.read_bytes()).hexdigest()!=cached_files[index]:
                    raise RuntimeError('Canonical source frame hash mismatch: '+str(raw))
                decoded=cv2.imread(str(raw),cv2.IMREAD_COLOR)
            else:
                png=page.screenshot(scale='device',animations='allow',caret='hide')
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
            if frame_map:
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
                def draw_overlays(final):
                    if callout_renderer is not None:
                        callout_renderer.draw(final,index,
                            info['dpr']*factor,dx,dy,frame_tilt,root_stage.window,
                            focal=perspective)
                    root_cursor.draw(final,
                        cursor[source_index] if cursor else None,wanted_ms/1000.,
                        info['dpr']*factor,dx,dy,tilt=frame_tilt,focal=perspective)
                output_image=root_stage.render(
                    source,cinematic_cursor=draw_overlays,tilt=frame_tilt,
                    glow=audio_levels[source_index] if audio_levels is not None else 0.,
                    perspective_px=perspective,spotlight=spotlight)
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
            encoder.stdin.write(output_image.tobytes())
            rendered+=1
            if index%screenshot_step==0 or index==total-1:
                save=session_dir/f'replay-frame-{index:04d}.jpg'
                cv2.imwrite(str(save),output_image,[cv2.IMWRITE_JPEG_QUALITY,84])
                checkpoints.append({'frame':index,'sha256':hashlib.sha256(save.read_bytes()).hexdigest(),
                                    'file':save.name})
            if index%60==0:print('REPLAY',index,'of',total,'elapsed',round(time.monotonic()-start_wall,1),flush=True)
        if expected_text:
            page.get_by_text(expected_text,exact=True).first.wait_for(state='visible',timeout=3000)
        context.close();browser.close()
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
            'spotlight_frames':preset_spotlight_frames,
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
    cli.add_argument('--presentation-hide-selector',
       help='Optional decorative selector to suppress only in presentation replay')
    cli.add_argument('--raw-replay',action='store_true',
       help='Opt out of the default cinematic presentation (debug/legacy mode)')
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
    if not args.raw_replay and not any(chosen):
        # The polished reference-shaped vector cursor is the new film
        # default. Older versions and unstyled source replay stay opt-in.
        args.presentation_v15=True
    result=replay(args.session,args.workflow,args.output,args.fps,args.seconds,
                  args.har,expected_text=args.expect_text,
                  click_effect=args.click_effect,backdrop_focus=args.backdrop_focus,
                  presentation_v12=args.presentation_v12,
                  presentation_hide_selector=args.presentation_hide_selector,
                  presentation_v13=args.presentation_v13,
                  presentation_v14=args.presentation_v14,cursor_style=args.cursor_style,
                  presentation_v15=args.presentation_v15,cursor_scale=args.cursor_scale)
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
