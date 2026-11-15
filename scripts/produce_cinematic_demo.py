#!/usr/bin/env python3
"""One-command Sauce 16:9 cinematic capture -> verified replay -> web export.

Use --session to reuse a previously authorized browser capture or --url to
capture an explicitly provided workflow. Raw session states and HAR remain
private; only the mastered MP4, preview, poster and index.html are published.
"""
from __future__ import annotations
import argparse,html,json,subprocess,os
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
            audio_track:Path|None=None,code_root:Path|None=None)->dict:
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
        spatial_parallax=spatial_parallax,audio_levels=rms,code_root=code_root)
    if not report['verified_semantics'] or not report['visual_region_checks']:
        raise RuntimeError('Replay must pass semantic and visual-region checks')
    if (not report.get('cinematic_stage_root') or
        report.get('cinematic_stage_window') != [220,124,1480,832] or
        report.get('cinematic_stage_background') != '#090a0f' or
        report.get('cursor_component') != 'CinematicCursor'):
        raise RuntimeError('CinematicStage root compositor is mandatory for production')
    verify_mp4(master,*MASTER_SIZE,FPS)
    webgl_report=None
    if webgl_optics:
        from postprocess_webgl_video import apply_video
        webgl_master=out_dir/'webgl-master-1080p60.mp4'
        webgl_report=apply_video(master,webgl_master)
        os.replace(webgl_master,master)
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
        'stage_background':'#090a0f',
        'glow_blur_px':140,
        'window_backdrop_blur_px':24,
        'webgl_optics':webgl_report,
        'spatial_parallax':report.get('spatial_parallax',False),
        'max_tilt_degrees':report.get('max_abs_tilt_degrees',0),
        'semantic_ast_foci':report.get('semantic_ast_foci',[]),
        'audio_reactive':{'frames':len(rms),'max_intensity':max(rms,default=0)}
            if rms is not None else None
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
        audio_track=args.audio_track,code_root=args.code_root),indent=2))


if __name__=='__main__':main()
