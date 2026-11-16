"""Film V3: a real Brimble homepage establishing shot before a real action.

Every pixel is captured from Brimble or is an explicitly editorial studio
background/title. All image, video and audio edits use a 60fps frame index.
The photographed bee is legitimate branding on the homepage insert; the
separate Connect Agent trace hides the mouse-following bee before capture.
"""
from __future__ import annotations
import argparse,hashlib,json,subprocess,wave
from pathlib import Path
import cv2,numpy as np
from flagship_stage import FlagshipStage
from flagship_edit import (run,probe,encode_title,title_image,
    original_ambient_bed,FPS,RATE,W,H,END_FRAMES)

HERO_FRAMES=132  # 2.2sec to comprehend the actual Brimble hero


def verify_hero(manifest_file:Path)->tuple[np.ndarray,dict]:
    report=json.loads(manifest_file.read_text())
    if (report.get('schema')!='sauce-public-homepage-insert-v1' or
        report.get('heading')!='The cloud for AI agents' or
        report.get('url')!='https://www.brimble.io/' or
        report.get('scroll_y_css')!=120 or
        report.get('viewport_css')!=[1280,720] or report.get('dpr')!=2):
        raise ValueError('Hero lacks verified public Brimble provenance')
    original=manifest_file.parent/'verified-hero.png'
    raw=original.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=report['source_sha256']:
        raise ValueError('Hero original bytes changed')
    image=cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)
    if image is None or image.shape!=(1440,2560,3):
        raise ValueError('Hero capture has wrong dimensions')
    return image,report


def hero_video(manifest:Path,path:Path)->dict:
    source,proof=verify_hero(manifest)
    stage=FlagshipStage()
    x,y,w,h=stage.window
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y',
        '-f','rawvideo','-pix_fmt','bgr24','-video_size',f'{W}x{H}',
        '-framerate',str(FPS),'-i','pipe:0','-c:v','libx264',
        '-preset','medium','-crf','14','-pix_fmt','yuv420p','-an',
        '-frames:v',str(HERO_FRAMES),str(path)]
    process=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        for index in range(HERO_FRAMES):
            progress=index/(HERO_FRAMES-1)
            smooth=progress*progress*(3-2*progress)
            # Lens eases gently outward to reveal Brimble's real headline.
            zoom=1.095-.095*smooth
            ww=2560/zoom;hh=1440/zoom
            # Keep the authenticated hero's bee and visible actual H1 within
            # the same crop; this is a camera crop, not rewritten interface.
            left=round((2560-ww)/2);top=round((1440-hh)*.42)
            right=round(left+ww);bottom=round(top+hh)
            crop=source[top:bottom,left:right]
            website=cv2.resize(crop,(w,h),interpolation=cv2.INTER_LANCZOS4)
            frame=stage.render(website)
            if process.stdin is None:raise RuntimeError('Encoder missing stdin')
            process.stdin.write(frame.tobytes())
        process.stdin.close()
        stderr=process.stderr.read().decode(errors='replace') if process.stderr else ''
        code=process.wait(timeout=60)
        if code:raise RuntimeError('Hero encoder error: '+stderr[-1500:])
    finally:
        if process.poll() is None:process.kill()
    frames,*_=probe(path)
    if frames!=HERO_FRAMES:raise ValueError('Hero export frame count differs')
    return proof


def assemble(source:Path,manifest:Path,out:Path)->dict:
    source=source.resolve();manifest=manifest.resolve();out=out.resolve()
    if not source.exists() or not manifest.exists():raise FileNotFoundError('Missing verified capture')
    out.mkdir(parents=True,exist_ok=True)
    source_frames,*_=probe(source)
    if source_frames<200 or source_frames>1200:raise ValueError('Invalid observed workflow')
    proof=hero_video(manifest,out/'hero-video.mp4')
    title_image('ending').save(out/'ending.png',optimize=True)
    encode_title(out/'ending.png',out/'ending-video.mp4',END_FRAMES,'ending')
    total=HERO_FRAMES+source_frames+END_FRAMES
    video=out/'video-only.mp4'
    graph=('[0:v]setpts=PTS-STARTPTS,format=yuv420p[a];'
           '[1:v]setpts=PTS-STARTPTS,format=yuv420p[b];'
           '[2:v]setpts=PTS-STARTPTS,format=yuv420p[c];'
           '[a][b][c]concat=n=3:v=1:a=0[v]')
    run(['ffmpeg','-hide_banner','-loglevel','error','-y',
        '-i',str(out/'hero-video.mp4'),'-i',str(source),
        '-i',str(out/'ending-video.mp4'),
        '-filter_complex',graph,'-map','[v]',
        '-r',str(FPS),'-frames:v',str(total),'-c:v','libx264',
        '-preset','medium','-crf','14','-pix_fmt','yuv420p',
        '-an',str(video)],timeout=250)
    if probe(video)[0]!=total:raise ValueError('Frame count drift after concat')
    # Source Foley and music are mixed at integer, frame-relative sample
    # offsets. AAC duration roundoff cannot accumulate visual audio drift.
    decoded=subprocess.run(['ffmpeg','-hide_banner','-loglevel','error',
        '-i',str(source),'-map','0:a:0','-f','f32le',
        '-ar',str(RATE),'-ac','2','-'],check=True,capture_output=True,
        timeout=100)
    wav_source=np.frombuffer(decoded.stdout,dtype='<f4')
    if len(wav_source)%2:raise ValueError('Stereo input invalid')
    wav_source=wav_source.reshape((-1,2))
    expected=source_frames*(RATE//FPS)
    pcm=original_ambient_bed(total*(RATE//FPS))
    anchor=HERO_FRAMES*(RATE//FPS)
    available=min(expected,len(wav_source))
    pcm[anchor:anchor+available]+=wav_source[:available]
    if np.max(np.abs(pcm))>=.93:raise ValueError('Audio headroom exceeded')
    wave_path=out/'sound-clock-48k.wav'
    with wave.open(str(wave_path),'wb') as wf:
        wf.setnchannels(2);wf.setsampwidth(2);wf.setframerate(RATE)
        wf.writeframes((np.clip(pcm,-1.,1.)*32767).astype('<i2').tobytes())
    master=out/'master-1080p60.mp4'
    run(['ffmpeg','-hide_banner','-loglevel','error','-y',
        '-i',str(video),'-i',str(wave_path),
        '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac',
        '-b:a','192k','-ar','48000','-movflags','+faststart',
        '-t',f'{total/FPS:.8f}',str(master)],timeout=130)
    from produce_cinematic_demo import verify_mp4,build_web_player
    verify_mp4(master,W,H,FPS)
    prev=out/'preview.mp4'
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(master),
         '-vf','fps=30,scale=1280:720:flags=lanczos',
         '-c:v','libx264','-preset','medium','-crf','17',
         '-pix_fmt','yuv420p','-c:a','aac','-b:a','160k',
         '-movflags','+faststart',str(prev)],timeout=180)
    run(['ffmpeg','-hide_banner','-loglevel','error','-y',
         '-ss','3.7','-i',str(master),'-frames:v','1',
         '-vf','scale=1280:720:flags=lanczos',
         '-q:v','3',str(out/'poster.jpg')])
    build_web_player(Path(__file__).resolve().parents[1]/'docs/sauce-premium-player-template.html',
        out,'Brimble · A product film by Sauce',
        'Real Brimble homepage and a verified Codex setup workflow.',total/FPS)
    receipt={'schema':'sauce-flagship-story-v3','master':str(master),
       'source':str(source),'verified_hero_sha256':proof['source_sha256'],
       'hero_frames':HERO_FRAMES,'workflow_frames':source_frames,
       'end_frames':END_FRAMES,'video_frames':total,'fps':FPS,
       'audio_samples':len(pcm),'sample_rate':RATE,
       'duration_s':total/FPS,'sound':'original ambient bed + source-clock Foley'}
    (out/'release.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    p.add_argument('--hero-manifest',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    print(json.dumps(assemble(a.source,a.hero_manifest,a.out),indent=2))
