"""Flagship film V4: verified brand hero → real clicks → actual result macro.

No fake terminal sessions, capabilities, dialogs or cursor motions. The detail
shot is labelled as a held photographic insert from the verified session.
Source 60fps frame/time and 48k audio offsets remain integer sample exact.
"""
from __future__ import annotations
import argparse,json,wave,subprocess,hashlib
from pathlib import Path
import cv2,numpy as np
from flagship_stage import FlagshipStage
from flagship_story_v3 import hero_video,verify_hero,HERO_FRAMES
from flagship_edit import (run,probe,encode_title,title_image,
    original_ambient_bed,FPS,RATE,W,H,END_FRAMES)
from session_contract import verify_package

ACTION_FRAMES=261   # Recorded second-click success, then one-second hold
DETAIL_FRAMES=90   # Intentional photographic close-up, 1.5 sec


def verified_result_image(session_dir:Path)->np.ndarray:
    session_dir=session_dir.resolve()
    session=json.loads((session_dir/'session.json').read_text())
    verify_package(session,session_dir)
    # This state was observed AFTER a real browser assertion, not generated UI.
    workflow=session['workflow']
    if not any('Copied. Paste it into your terminal' in str(w.get('expect_text',''))
               for w in workflow if w.get('action')=='click'):
        raise ValueError('There is no verified successful copy action')
    state=session['states'][-1]
    file=session_dir/'states'/state['file'];raw=file.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=state['sha256']:
        raise ValueError('Result screenshot evidence hash differs')
    image=cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)
    if image is None or image.shape!=(1440,2560,3):
        raise ValueError('Wrong DPR source for outcome detail')
    if session.get('presentation_hide_selector')!='img[src*="bee-cutout-"]':
        raise ValueError('Original pointer contamination may be present')
    return image


def result_video(session_dir:Path,path:Path)->None:
    source=verified_result_image(session_dir)
    stage=FlagshipStage()
    w,h=stage.window[2:]
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y',
         '-f','rawvideo','-pix_fmt','bgr24','-video_size',f'{W}x{H}',
         '-framerate','60','-i','pipe:0','-frames:v',str(DETAIL_FRAMES),
         '-c:v','libx264','-preset','medium','-crf','14',
         '-pix_fmt','yuv420p','-an',str(path)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        for index in range(DETAIL_FRAMES):
            u=index/(DETAIL_FRAMES-1)
            smooth=u*u*(3-2*u)
            # 1600×900 high-DPI crop, real source pixels; source typography
            # is downsampled only once, not enlarged from a 1080p video.
            scale=1.+.026*smooth
            cw=1600/scale;ch=900/scale
            left=round(1280-cw/2);top=round(700-ch/2)
            crop=source[top:round(top+ch),left:round(left+cw)]
            if crop.shape[0]<400 or crop.shape[1]<400:
                raise ValueError('Unsafe closeup source crop')
            img=cv2.resize(crop,(w,h),interpolation=cv2.INTER_LANCZOS4)
            frame=stage.render(img)
            if proc.stdin is None:raise RuntimeError('Missing compositor stream')
            proc.stdin.write(frame.tobytes())
        proc.stdin.close()
        error=proc.stderr.read().decode(errors='replace') if proc.stderr else ''
        if proc.wait(timeout=90):raise RuntimeError('Closeup failed: '+error[-900:])
    finally:
        if proc.poll() is None:proc.kill()
    if probe(path)[0]!=DETAIL_FRAMES:raise ValueError('Detail frame mismatch')


def assemble(source:Path,manifest:Path,session_dir:Path,out:Path)->dict:
    source=source.resolve();manifest=manifest.resolve()
    session_dir=session_dir.resolve();out=out.resolve();out.mkdir(parents=True,exist_ok=True)
    raw_frames,*_=probe(source)
    if raw_frames<ACTION_FRAMES+40:raise ValueError('Short action source')
    hero_proof=hero_video(manifest,out/'hero-video.mp4')
    result_video(session_dir,out/'outcome-video.mp4')
    title_image('ending').save(out/'ending.png',optimize=True)
    encode_title(out/'ending.png',out/'ending-video.mp4',END_FRAMES,'ending')
    total=HERO_FRAMES+ACTION_FRAMES+DETAIL_FRAMES+END_FRAMES
    video=out/'video-only.mp4'
    graph=('[0:v]setpts=PTS-STARTPTS,format=yuv420p[a];'
           f'[1:v]trim=start_frame=0:end_frame={ACTION_FRAMES},setpts=PTS-STARTPTS,format=yuv420p[b];'
           '[2:v]setpts=PTS-STARTPTS,format=yuv420p[c];'
           '[3:v]setpts=PTS-STARTPTS,format=yuv420p[d];'
           '[a][b][c][d]concat=n=4:v=1:a=0[v]')
    run(['ffmpeg','-hide_banner','-loglevel','error','-y',
         '-i',str(out/'hero-video.mp4'),'-i',str(source),
         '-i',str(out/'outcome-video.mp4'),
         '-i',str(out/'ending-video.mp4'),
         '-filter_complex',graph,'-map','[v]',
         '-r',str(FPS),'-frames:v',str(total),
         '-c:v','libx264','-preset','medium','-crf','14',
         '-pix_fmt','yuv420p','-an',str(video)],timeout=240)
    if probe(video)[0]!=total:raise ValueError('Four-shot film frame mismatch')
    # Only source-clock Foley that actually occurred before the cut is mixed.
    audio=subprocess.run(['ffmpeg','-hide_banner','-loglevel','error',
         '-i',str(source),'-map','0:a:0','-f','f32le','-ar',str(RATE),
         '-ac','2','-'],capture_output=True,check=True,timeout=90)
    samples=np.frombuffer(audio.stdout,dtype='<f4')
    if len(samples)%2:raise ValueError('Invalid input PCM')
    samples=samples.reshape((-1,2))
    length=total*RATE//FPS
    pcm=original_ambient_bed(length)
    src_start=HERO_FRAMES*RATE//FPS
    src_length=ACTION_FRAMES*RATE//FPS
    available=min(len(samples),src_length)
    pcm[src_start:src_start+available]+=samples[:available]
    if np.max(np.abs(pcm))>=.93:raise ValueError('Clipping in original soundtrack')
    wav=out/'sound-clock-48k.wav'
    with wave.open(str(wav),'wb') as wf:
        wf.setnchannels(2);wf.setsampwidth(2);wf.setframerate(RATE)
        wf.writeframes((np.clip(pcm,-1,1)*32767).astype('<i2').tobytes())
    master=out/'master-1080p60.mp4'
    run(['ffmpeg','-hide_banner','-loglevel','error','-y',
         '-i',str(video),'-i',str(wav),'-map','0:v:0','-map','1:a:0',
         '-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000',
         '-movflags','+faststart','-t',f'{length/RATE:.8f}',str(master)])
    from produce_cinematic_demo import verify_mp4,build_web_player
    verify_mp4(master,W,H,FPS)
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(master),
        '-vf','fps=30,scale=1280:720:flags=lanczos',
        '-c:v','libx264','-preset','medium','-crf','17',
        '-pix_fmt','yuv420p','-c:a','aac','-b:a','160k',
        '-movflags','+faststart',str(out/'preview.mp4')],timeout=180)
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss','5.3',
         '-i',str(master),'-frames:v','1','-vf','scale=1280:720:flags=lanczos',
         '-q:v','3',str(out/'poster.jpg')])
    build_web_player(Path(__file__).resolve().parents[1]/'docs/sauce-premium-player-template.html',
          out,'Brimble · A product film by Sauce',
          'Real Brimble homepage, Codex selection, and a verified copied-command close-up.',
          length/RATE)
    receipt={'schema':'sauce-flagship-story-v4','master':str(master),
         'hero_source_sha256':hero_proof['source_sha256'],
         'session_dir':str(session_dir),'source':str(source),
         'hero_frames':HERO_FRAMES,'real_interaction_frames':ACTION_FRAMES,
         'verified_result_hold_frames':DETAIL_FRAMES,
         'ending_frames':END_FRAMES,'video_frames':total,'fps':FPS,
         'audio_samples':length,'sample_rate':RATE,'duration_s':length/RATE,
         'notes':'Result closeup uses SHA-backed captured UI; it is an editorial cut, not a live connection.'}
    (out/'release.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    p.add_argument('--hero-manifest',type=Path,required=True)
    p.add_argument('--session',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    print(json.dumps(assemble(a.source,a.hero_manifest,a.session,a.out),indent=2))
