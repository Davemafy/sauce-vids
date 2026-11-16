#!/usr/bin/env python3
"""One-command Sauce 16:9 cinematic capture -> verified replay -> web export.

Use --session to reuse a previously authorized browser capture or --url to
capture an explicitly provided workflow. Raw session states and HAR remain
private; only the mastered MP4, preview, poster and index.html are published.
"""
from __future__ import annotations
import argparse,html,json,subprocess,os,tempfile
from pathlib import Path

from cinematic_spec import (DEFAULT_DPR,DPR_CHOICES,CURSOR_FILM_SCALE,
    MASTER_SIZE,PREVIEW_SIZE,FPS,enforce_hidpi,ffmpeg_lanczos_preview)
from session_contract import verify_package


def video_info(path:Path)->dict:
    return json.loads(subprocess.check_output([
        'ffprobe','-v','error','-show_entries',
        'stream=codec_name,codec_type,width,height,r_frame_rate,nb_frames:format=duration',
        '-of','json',str(path)],text=True))


def verify_mp4(path:Path, width:int,height:int,fps:int)->None:
    if not path.is_file() or path.stat().st_size<1000:
        raise RuntimeError('Missing or empty video '+str(path))
    meta=video_info(path)
    stream=next((s for s in meta['streams'] if s['codec_type']=='video'),None)
    if not stream or (stream['width'],stream['height'])!=(width,height):
        raise RuntimeError('Incorrect export dimensions for '+str(path))
    if stream['codec_name']!='h264':
        raise RuntimeError('Export must be H.264')
    rate=stream['r_frame_rate'].split('/')
    if int(rate[0])/int(rate[1])!=fps:
        raise RuntimeError('Incorrect frame rate')
    subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(path),
                    '-f','null','-'],check=True,timeout=120)


def build_web_player(template:Path,dir:Path,title:str,description:str,
                     seconds:float)->Path:
    content=template.read_text()
    tokens={
        'FILM_TITLE':title,
        'FILM_DESCRIPTION':description,
        'PREVIEW_NAME':'preview.mp4',
        'MASTER_NAME':'master-1080p60.mp4',
        'POSTER_NAME':'poster.jpg',
        'DURATION':f'{seconds:.1f} seconds',
    }
    for name,value in tokens.items():
        marker='{{'+name+'}}'
        if marker not in content:raise ValueError('Missing template marker '+marker)
        content=content.replace(marker,html.escape(value,quote=True))
    if '{{' in content:raise ValueError('Unresolved template marker')
    player=dir/'index.html'
    player.write_text(content)
    return player


def ensure_private_capture_separate(session_dir:Path,out_dir:Path)->None:
    """Prevent a published directory from containing raw HAR, states or workflows."""
    raw=session_dir.resolve()
    public=out_dir.resolve()
    if raw==public or raw.is_relative_to(public) or public.is_relative_to(raw):
        raise ValueError('Capture and public export directories must be disjoint')


def produce(*,workflow:Path,session_dir:Path,out_dir:Path,
            url:str|None=None,dpr:int=DEFAULT_DPR,
            seconds:float|None=None,title:str='Product walkthrough',
            description:str='A recorded, verified product interaction.',
            cursor_style:str='ink',cursor_scale:float=CURSOR_FILM_SCALE,
            presentation_hide_selector:str|None=None,
            webgl_optics:bool=True,spatial_parallax:bool=True,
            audio_track:Path|None=None,code_root:Path|None=None,
            editorial_closeup:bool=False,
            editorial_geometry:Path|None=None,
            enable_time_warp:bool=False,max_warp_speed:float=4.,
            enable_studio_floor:bool=False,floor_reflection_intensity:float=.25,
            enable_callouts:bool=False,callout_cooldown_ms:int=2500,
            deterministic_frame_cache:Path|None=None,
            preset:str|None=None,foley_assets:Path|None=None,
            music_track:Path|None=None,mute_audio:bool=False,
            foley_volume:float|None=None)->dict:
    enforce_hidpi(dpr)
    if cursor_style not in ('ink','outline'):raise ValueError('Unsupported pointer style')
    if not .35<=cursor_scale<=1:raise ValueError('Invalid cursor scale')
    if not workflow.is_file():raise FileNotFoundError(workflow)
    if url:
        from session_capture import record
        actions=json.loads(workflow.read_text())
        record(url,actions,session_dir,width=1280,height=720,dpr=dpr,capture_har=True)
    else:
        if not (session_dir/'session.json').is_file():
            raise FileNotFoundError('Provide an existing verified session or --url')
    from session_replay import replay
    session=json.loads((session_dir/'session.json').read_text())
    verified=verify_package(session,session_dir)
    enforce_hidpi(verified['dpr'])
    if verified['viewport']!=[1280,720]:
        raise ValueError('This 16:9 preset requires 1280x720 CSS viewport')
    ensure_private_capture_separate(session_dir,out_dir)
    out_dir.mkdir(parents=True,exist_ok=True)
    master=out_dir/'master-1080p60.mp4'
    real_duration=(seconds if seconds is not None
        else (session['states'][-1]['at_ms']-session['states'][0]['at_ms'])/1000.+.35)
    studio_enabled=bool(preset) or enable_time_warp or enable_studio_floor or enable_callouts
    if preset is not None and preset not in ('clean-studio','3d-launch','hyper-cut'):
        raise ValueError('Select a supported Sauce flavor')
    if preset and audio_track:
        raise ValueError('Preset Foley cannot be combined with legacy --audio-track; use --music-track')
    if preset is None and (foley_assets or music_track or mute_audio or foley_volume is not None):
        raise ValueError('Foley and music controls require --preset')
    if foley_volume is not None and not 0<=foley_volume<=1:
        raise ValueError('Foley volume must be between 0 and 1')
    if deterministic_frame_cache is not None:
        if not studio_enabled:raise ValueError('Frame cache requires StudioMotion')
        ensure_private_capture_separate(deterministic_frame_cache,out_dir)
    if studio_enabled and audio_track is not None:
        raise ValueError('StudioMotion takes no legacy audio tracks; use --preset with --music-track')
    if not 1<=max_warp_speed<=4:raise ValueError('maxWarpSpeed must be between 1 and 4')
    if not 0<=floor_reflection_intensity<=.5:
        raise ValueError('floorReflectionIntensity must be between 0 and .5')
    if callout_cooldown_ms<0:raise ValueError('calloutCooldownMs must be nonnegative')
    studio_plan=None
    if studio_enabled:
        from studio_motion_bridge import plan_studio_motion
        studio_plan=plan_studio_motion(session,real_duration,FPS,{
            'enableTimeWarp':enable_time_warp,
            'maxWarpSpeed':max_warp_speed,
            'enableStudioFloor':enable_studio_floor,
            'floorReflectionIntensity':floor_reflection_intensity,
            'enableCallouts':enable_callouts,
            'calloutCooldownMs':callout_cooldown_ms,
            'maxCalloutLifetimeMs':1800},
            preset=preset,session_dir=session_dir,preset_overrides=(
              {'sound':dict({'muted':bool(mute_audio)},
                    **({'masterGain':foley_volume} if foley_volume is not None else {}))}
              if preset and (mute_audio or foley_volume is not None) else None))
    if audio_track is not None:
        # Keep importable contract and player utilities dependency-free in
        # standard Python CI. Scientific audio dependencies are only needed
        # when an audio track is explicitly supplied.
        from audio_reactive import audio_envelope
        rms=audio_envelope(audio_track,FPS,round(real_duration*FPS))
    else:
        rms=None
    # HDR/offscreen replay's own time-step clock is independent of export fps.
    report=replay(session_dir,workflow,master,fps=FPS,seconds=seconds,
        har=(session_dir/'network.har').is_file(),backdrop_focus=True,
        presentation_v15=True,cursor_style=cursor_style,
        cursor_scale=cursor_scale,
        presentation_hide_selector=presentation_hide_selector,
        spatial_parallax=spatial_parallax,audio_levels=rms,code_root=code_root,
        editorial_closeup=editorial_closeup,editorial_geometry=editorial_geometry,
        studio_motion_plan=studio_plan,raster_cache_dir=deterministic_frame_cache)
    if not report['verified_semantics'] or not report['visual_region_checks']:
        raise RuntimeError('Replay must pass semantic and visual-region checks')
    if (not report.get('cinematic_stage_root') or
        report.get('cinematic_stage_window') != [220,124,1480,832] or
        report.get('cinematic_stage_background') != '#090a0f' or
        report.get('cursor_component') != 'CinematicCursor'):
        raise RuntimeError('CinematicStage root compositor is mandatory for production')
    expected_material=(studio_plan['motionEngine']['preset']['stage']['backdropStyle']
                       if preset is not None else 'obsidian-grain')
    if report.get('procedural_backdrop_style') != expected_material:
        raise RuntimeError('Rendered stage material does not match selected preset')
    verify_mp4(master,*MASTER_SIZE,FPS)
    webgl_report=None
    if webgl_optics:
        from postprocess_webgl_video import apply_video
        webgl_master=out_dir/'webgl-master-1080p60.mp4'
        shader_uniforms=None
        stage_fx=preset in ('3d-launch','hyper-cut')
        if stage_fx:
            from foley_mixer import foley_shader_envelopes
            shader_uniforms=foley_shader_envelopes(
                studio_plan['motionEngine']['foleyPlan'],
                int(round(report['seconds']*FPS)),foley_assets)
        if stage_fx:
            webgl_report=apply_video(master,webgl_master,
                foley_uniforms=shader_uniforms,studio=True)
        else:
            webgl_report=apply_video(master,webgl_master)
        os.replace(webgl_master,master)
        verify_mp4(master,*MASTER_SIZE,FPS)
    preset_foley=None
    if preset is not None:
        from foley_mixer import render_foley_plan,RATE
        plan=studio_plan['motionEngine']['foleyPlan']
        # FoleyPlan is generated in the SAME bridge invocation as FramePlan.
        # Pad to the encoded video-frame boundary (ceil outputDuration*fps).
        with tempfile.TemporaryDirectory(prefix='.sauce-foley-',dir=out_dir.parent) as temp:
            wav=Path(temp)/'sound.wav'
            preset_foley=render_foley_plan(
                plan,wav,asset_dir=foley_assets,music=music_track,
                target_duration_ms=report['seconds']*1000.)
            muxed=out_dir/'preset-mux-tmp.mp4'
            subprocess.run([
                'ffmpeg','-hide_banner','-loglevel','error','-y','-nostdin',
                '-i',str(master),'-i',str(wav),
                '-map','0:v:0','-map','1:a:0','-c:v','copy',
                '-c:a','aac','-ar','48000','-b:a','192k',
                '-t',f"{report['seconds']:.8f}",'-movflags','+faststart',
                str(muxed)],check=True,timeout=120)
            meta=video_info(muxed)
            check=subprocess.check_output(['ffprobe','-v','error','-of','json',
                '-show_entries','stream=codec_type,codec_name,sample_rate',
                str(muxed)],text=True)
            audio_streams=[v for v in json.loads(check)['streams']
                if v.get('codec_type')=='audio']
            if len(audio_streams)!=1 or audio_streams[0].get('sample_rate')!='48000':
                raise RuntimeError('Preset audio must be one 48kHz AAC stream')
            os.replace(muxed,master)
            verify_mp4(master,*MASTER_SIZE,FPS)
    if audio_track is not None:
        muxed=out_dir/'audio-master-1080p60.mp4'
        subprocess.run([
            'ffmpeg','-hide_banner','-loglevel','error','-y',
            '-i',str(master),'-i',str(audio_track),'-map','0:v:0',
            '-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k',
            '-t',str(real_duration),'-shortest','-movflags','+faststart',
            str(muxed)],check=True,timeout=95)
        os.replace(muxed,master)
        verify_mp4(master,*MASTER_SIZE,FPS)
    preview=out_dir/'preview.mp4'
    subprocess.run([
        'ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(master),
        '-vf',ffmpeg_lanczos_preview(*MASTER_SIZE,*PREVIEW_SIZE),
        '-c:v','libx264','-preset','slow','-crf','17',
        '-c:a','aac','-b:a','160k',
        '-pix_fmt','yuv420p','-movflags','+faststart',str(preview),
    ],check=True,timeout=120)
    verify_mp4(preview,*PREVIEW_SIZE,30)
    poster=out_dir/'poster.jpg'
    subprocess.run([
        'ffmpeg','-hide_banner','-loglevel','error','-y',
        '-ss',str(min(2.15,max(.1,report['seconds']*.5))),
        '-i',str(master),'-frames:v','1',
        '-vf',f'scale={PREVIEW_SIZE[0]}:{PREVIEW_SIZE[1]}:flags=lanczos',
        '-q:v','3',str(poster)
    ],check=True,timeout=30)
    if not poster.is_file():raise RuntimeError('Poster extraction failed')
    template=Path(__file__).resolve().parents[1]/'docs'/'sauce-premium-player-template.html'
    page=build_web_player(template,out_dir,title,description,report['seconds'])
    receipt={
        'master':master.name,'preview':preview.name,'poster':poster.name,
        'player':page.name,'fps':FPS,'dimensions':list(MASTER_SIZE),
        'source_dpr':verified['dpr'],'pointer':cursor_style,
        'cursor_scale':cursor_scale,'clicks':sum(e['type']=='pointerdown' for e in session['events']),
        'source_verified_states':len(session['states']),
        'semantic_checks':len(report['semantic_checks']),
        'pixel_region_checks':len(report['visual_region_checks']),
        'preview_resampling':'lanczos',
        'master_resampling':'Lanczos4',
        'player_template':'sauce-premium-player-template.html',
        'root_component':'CinematicStage',
        'cursor_component':'CinematicCursor',
        'window':[220,124,1480,832],
        'editorial_closeup':bool(editorial_closeup),
        'stage_background':'#090a0f',
        'procedural_backdrop_style':report['procedural_backdrop_style'],
        'glow_blur_px':140,
        'window_backdrop_blur_px':24,
        'webgl_optics':webgl_report,
        'spatial_parallax':report.get('spatial_parallax',False),
        'max_tilt_degrees':report.get('max_abs_tilt_degrees',0),
        'semantic_ast_foci':report.get('semantic_ast_foci',[]),
        'audio_reactive':{'frames':len(rms),'max_intensity':max(rms,default=0)}
            if rms is not None else None,
        'studio_motion':report.get('studio_motion'),
        'studio_config':(studio_plan.get('config') if studio_plan else None),
        'preset':preset,
        'preset_camera_frames':report.get('preset_camera_frames',0),
        'spotlight_frames':report.get('spotlight_frames',0),
        'beat_cut_frames':report.get('beat_cut_frames',[]),
        'multi_plane_frames':report.get('multi_plane_frames',0),
        'concealed_terminal_frames':report.get('concealed_terminal_frames',0),
        'live_modal_hold_frames':report.get('live_modal_hold_frames',0),
        'single_plane_fallback_frames':report.get('single_plane_fallback_frames',0),
        'foley_audio':preset_foley,
        'studio_output_frames':report['frames'],
        'deterministic_raster_cache':report.get('raster_cache')
    }
    (out_dir/'release.json').write_text(json.dumps(receipt,indent=2))
    return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__)
    source=p.add_mutually_exclusive_group(required=True)
    source.add_argument('--url',help='Public/authorized website to capture')
    source.add_argument('--session',type=Path,help='Existing raw Sauce session directory')
    p.add_argument('--workflow',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True,
                   help='Separate public-safe export directory')
    p.add_argument('--dpr',type=int,choices=DPR_CHOICES,default=DEFAULT_DPR)
    p.add_argument('--seconds',type=float)
    p.add_argument('--title',default='Product walkthrough')
    p.add_argument('--description',default='A recorded, verified product interaction.')
    p.add_argument('--cursor-style',choices=('ink','outline'),default='ink')
    p.add_argument('--cursor-scale',type=float,default=CURSOR_FILM_SCALE)
    p.add_argument('--presentation-hide-selector')
    p.add_argument('--no-webgl-optics',action='store_true',
                   help='Opt out of the actual WebGL2 shader pass for debugging')
    p.add_argument('--no-parallax',action='store_true',
                   help='Opt out of cursor velocity-driven 3D tilt')
    p.add_argument('--editorial-geometry',type=Path,
                   help='Verified post-click dialog geometry for safe editorial framing')
    p.add_argument('--editorial-closeup',action='store_true',
                   help='Tight evidence-led shot framing for a 4s narrated test')
    p.add_argument('--enable-time-warp',action='store_true',
                   help='Monotonic 1–4x idle compression with protected action windows')
    p.add_argument('--max-warp-speed',type=float,default=4.,
                   help='Peak idle speed, 1–4 (default 4)')
    p.add_argument('--enable-studio-floor',action='store_true',
                   help='Perspective floor reflection, contact and ambient cast shadows')
    p.add_argument('--floor-reflection-intensity',type=float,default=.25,
                   help='Studio floor reflection, 0–0.5 (default .25)')
    p.add_argument('--enable-callouts',action='store_true',
                   help='Show trace-verified, cooldown-constrained kinetic pills')
    p.add_argument('--callout-cooldown-ms',type=int,default=2500,
                   help='Minimum output-time interval between callouts')
    p.add_argument('--deterministic-frame-cache',type=Path,
                   help='Private lossless source frames for bitwise-reproducible exports')
    p.add_argument('--preset',choices=('clean-studio','3d-launch','hyper-cut'),
                   help='Enable the versioned Sauce FramePlan + FoleyPlan compositor')
    p.add_argument('--foley-assets',type=Path,
                   help='Optional local WAV/OGG samples; procedural fallback otherwise')
    p.add_argument('--music-track',type=Path,
                   help='Optional licensed local music, ducked under Foley cues')
    p.add_argument('--mute-audio',action='store_true',
                   help='Render a silent audio track for a selected preset')
    p.add_argument('--foley-volume',type=float,
                   help='Override preset Foley master gain (0..1)')
    p.add_argument('--audio-track',type=Path,
                   help='Licensed source soundtrack; drives RMS glow and is muxed into MP4')
    p.add_argument('--code-root',type=Path,
                   help='Local workspace to resolve source files for code-focus trace events')
    args=p.parse_args()
    session=args.session or (args.out.parent/(args.out.name+'-private-capture'))
    print(json.dumps(produce(
        workflow=args.workflow,session_dir=session,out_dir=args.out,url=args.url,
        dpr=args.dpr,seconds=args.seconds,title=args.title,
        description=args.description,cursor_style=args.cursor_style,
        cursor_scale=args.cursor_scale,
        presentation_hide_selector=args.presentation_hide_selector,
        webgl_optics=not args.no_webgl_optics,
        spatial_parallax=not args.no_parallax,
        audio_track=args.audio_track,code_root=args.code_root,
        editorial_closeup=args.editorial_closeup,
        editorial_geometry=args.editorial_geometry,
        enable_time_warp=args.enable_time_warp,
        max_warp_speed=args.max_warp_speed,
        enable_studio_floor=args.enable_studio_floor,
        floor_reflection_intensity=args.floor_reflection_intensity,
        enable_callouts=args.enable_callouts,
        callout_cooldown_ms=args.callout_cooldown_ms,
        deterministic_frame_cache=args.deterministic_frame_cache,
        preset=args.preset,foley_assets=args.foley_assets,
        music_track=args.music_track,mute_audio=args.mute_audio,
        foley_volume=args.foley_volume),indent=2))


if __name__=='__main__':main()
