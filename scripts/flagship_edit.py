"""Single-source Sauce launch-film edit: evidence-first product scene and clean titles.

One exact timeline at 60fps. Editorial titles are clearly separate from the
verified Brimble capture; they do not invent application state or behavior.
No proprietary soundtrack: source Foley is decoded and sample-index aligned.
"""
from __future__ import annotations
import argparse,json,subprocess,wave,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

FPS=60
RATE=48000
W,H=1920,1080
INTRO_FRAMES=78  # 1.30 seconds
END_FRAMES=96  # 1.60 seconds
DARK='#161819'
SANS='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
SERIF='/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'


def run(cmd,timeout=120):
    subprocess.run(cmd,check=True,timeout=timeout)


def title_image(stage:str)->Image.Image:
    image=Image.new('RGB',(W,H),DARK)
    d=ImageDraw.Draw(image)
    sans=ImageFont.truetype(SANS,29)
    small=ImageFont.truetype(SANS,22)
    mono=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',22)
    if stage=='opening':
        d.text((155,157),'BRIMBLE   /   PRODUCT WORKFLOW 01',font=mono,fill='#a5a9a7')
        d.text((153,385),'Bring your agent.',font=ImageFont.truetype(SERIF,106),fill='#f4f4f0')
        d.text((158,565),'Real agent setup. In Brimble.',font=sans,fill='#c2c6c3')
        d.line([(156,685),(690,685)],fill='#484d4c',width=2)
        d.text((158,721),'Connect agent   ·   Choose Codex   ·   Copy command',font=small,fill='#959a98')
        d.text((158,951),'A FILM BY SAUCE',font=small,fill='#aeb2af')
    else:
        d.text((158,170),'PRODUCT FILMS   /   SAUCE',font=mono,fill='#a5aaa7')
        d.text((144,385),'SAUCE',font=ImageFont.truetype(BOLD,187),fill='#f3f4f0')
        d.text((156,670),'Real interactions. Directed.',font=ImageFont.truetype(SANS,37),fill='#bec2c0')
        d.line([(157,789),(650,789)],fill='#484d4c',width=2)
        d.text((158,821),'Brimble product footage · verified interaction',font=small,fill='#959a98')
    return image


def probe(video:Path)->tuple[int,int,int]:
    data=json.loads(subprocess.check_output(['ffprobe','-v','error','-of','json',
      '-show_entries','stream=codec_type,width,height,r_frame_rate,nb_frames',str(video)],text=True))
    stream=next(x for x in data['streams'] if x['codec_type']=='video')
    if (stream['width'],stream['height'],stream['r_frame_rate'])!=(W,H,'60/1'):
        raise ValueError('Source product film must be 1920x1080 at 60fps')
    return int(stream['nb_frames']),W,H


def encode_title(png:Path,path:Path,frames:int,stage:str):
    duration=frames/FPS
    # Text is deliberately locked to the composition grid; soft photographic
    # exposure fade instead of a template-like flying typography effect.
    # Actual inspection exposed an ugly black-flash at 1.28s/7.63s when
    # both cards faded *to/from* zero before a hard scene cut.
    # Keep title-to-product and product-to-end cuts exact on frame boundaries.
    treatment=('fade=t=in:st=0:d=0.22' if stage=='opening' else
               f'fade=t=out:st={duration-.32:.6f}:d=0.32')
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-loop','1',
        '-framerate','60','-i',str(png),'-frames:v',str(frames),
        '-vf',treatment,
        '-c:v','libx264','-preset','medium','-crf','15','-pix_fmt','yuv420p',
        '-r','60','-an',str(path)])


def original_ambient_bed(samples:int)->np.ndarray:
    """Original quiet, harmonically restrained pad; no licensed samples.

    Fixed phases and the 48k integer sample clock make rerenders identical.
    The mix deliberately leaves source click/modal Foley intact.
    """
    n=np.arange(samples,dtype=np.float64)
    t=n/RATE
    fade_in=np.clip(t/.48,0,1)
    fade_out=np.clip((samples/RATE-t)/.64,0,1)
    level=(fade_in*fade_in*(3-2*fade_in))*          (fade_out*fade_out*(3-2*fade_out))
    # Minor suspended tone with restrained stereo width; not a stock loop.
    tones=[(164.8138,.043),(220.0,.030),(246.9417,.018)]
    left=np.zeros(samples,dtype=np.float64)
    right=np.zeros(samples,dtype=np.float64)
    for frequency,amp in tones:
        left+=amp*np.sin(2*np.pi*frequency*t)
        right+=amp*np.sin(2*np.pi*(frequency+.07)*t+.11)
    # Low-level overtone avoids sub-heavy playback on phone speakers.
    left+=.008*np.sin(2*np.pi*329.6276*t)
    right+=.008*np.sin(2*np.pi*329.6976*t+.24)
    bed=np.stack((left,right),axis=1)*level[:,None]
    return np.asarray(bed,dtype=np.float32)


def assemble(source:Path,dest:Path)->dict:
    source=source.resolve();dest=dest.resolve()
    if not source.is_file():raise FileNotFoundError(source)
    if source.parent==dest or source.parent.is_relative_to(dest) or dest.is_relative_to(source.parent):
        raise ValueError('Keep finished media separate from raw source and capture')
    source_frames,*_=probe(source)
    if source_frames>3600:raise ValueError('This flagship edit is bounded to 60 s')
    dest.mkdir(parents=True,exist_ok=True)
    (dest/'title.png').write_bytes(b'') if False else None
    cards=[]
    for name,frames in [('opening',INTRO_FRAMES),('ending',END_FRAMES)]:
        png=dest/(name+'.png');title_image(name).save(png,optimize=True)
        part=dest/(name+'-video.mp4');encode_title(png,part,frames,name)
        cards.append(part)
    # Video is concatenated on the *fixed output frame* boundary, then
    # encoded once at 60fps. No wall-clock camera interpolation or VFR.
    concat=dest/'video-only.mp4'
    filter_graph=(
      '[0:v]setpts=PTS-STARTPTS,format=yuv420p[v0];'
      '[1:v]setpts=PTS-STARTPTS,format=yuv420p[v1];'
      '[2:v]setpts=PTS-STARTPTS,format=yuv420p[v2];'
      '[v0][v1][v2]concat=n=3:v=1:a=0[v]')
    run(['ffmpeg','-hide_banner','-loglevel','error','-y',
        '-i',str(cards[0]),'-i',str(source),'-i',str(cards[1]),
        '-filter_complex',filter_graph,'-map','[v]','-vsync','cfr',
        '-r','60','-frames:v',str(INTRO_FRAMES+source_frames+END_FRAMES),
        '-c:v','libx264','-preset','medium','-crf','15',
        '-pix_fmt','yuv420p','-an',str(concat)],timeout=210)
    # Use integer sample offsets for a strict soundtrack clock, rather than
    # AAC input packet timestamps and concat segment priming differences.
    actual=source_frames*RATE//FPS
    decoded=subprocess.run(['ffmpeg','-hide_banner','-loglevel','error',
        '-i',str(source),'-map','0:a:0','-f','f32le','-ac','2','-ar',str(RATE),'-'],
        capture_output=True,check=True,timeout=90)
    audio=np.frombuffer(decoded.stdout,dtype='<f4')
    if len(audio)%2:raise ValueError('Non-stereo source audio')
    audio=audio.reshape((-1,2))
    # Trim/pad by samples, not arbitrary seconds; this is audibly silent
    # during editorial title cards and exact with Foley on product contact.
    source_samples=np.zeros((actual,2),np.float32)
    source_samples[:min(len(audio),actual)]=audio[:min(len(audio),actual)]
    count=(INTRO_FRAMES+source_frames+END_FRAMES)*RATE//FPS
    pcm=np.zeros((count,2),np.float32)
    pcm[INTRO_FRAMES*RATE//FPS:(INTRO_FRAMES+source_frames)*RATE//FPS]=source_samples
    # One original 48-kHz bed, not a borrowed sample loop. Its envelope is
    # fixed to the exact film frame/sample grid and keeps real Foley audible.
    pcm+=original_ambient_bed(count)
    if float(np.max(np.abs(pcm)))>=.93:
        raise ValueError('Sound design exceeded headroom')
    wav=dest/'sound-clock-48k.wav'
    with wave.open(str(wav),'wb') as writer:
        writer.setnchannels(2);writer.setsampwidth(2);writer.setframerate(RATE)
        writer.writeframes((np.clip(pcm,-1,1)*32767).astype('<i2').tobytes())
    master=dest/'master-1080p60.mp4'
    run(['ffmpeg','-hide_banner','-loglevel','error','-y',
      '-i',str(concat),'-i',str(wav),'-map','0:v:0','-map','1:a:0',
      '-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000',
      '-t',f'{count/RATE:.8f}','-movflags','+faststart',str(master)])
    # External release keeps no raw SHA capture states, HAR or source code.
    preview=dest/'preview.mp4'
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(master),
      '-vf','fps=30,scale=1280:720:flags=lanczos',
      '-c:v','libx264','-preset','medium','-crf','17',
      '-pix_fmt','yuv420p','-c:a','aac','-b:a','160k',
      '-movflags','+faststart',str(preview)],timeout=150)
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss','4.0',
      '-i',str(master),'-frames:v','1','-vf','scale=1280:720:flags=lanczos',
      '-q:v','3',str(dest/'poster.jpg')])
    from produce_cinematic_demo import build_web_player,verify_mp4
    verify_mp4(master,W,H,FPS)
    build_web_player(Path(__file__).resolve().parents[1]/'docs/sauce-premium-player-template.html',
        dest,'Brimble · Connect your agent',
        'A verified Brimble agent selection and command copy, directed with Sauce.',count/RATE)
    report={'schema':'sauce-flagship-film-v1','source':str(source),'master':master.name,
        'video_frames':INTRO_FRAMES+source_frames+END_FRAMES,
        'source_frames':source_frames,'intro_frames':INTRO_FRAMES,
        'outro_frames':END_FRAMES,'fps':FPS,'sample_rate':RATE,
        'audio_samples':count,'duration_s':count/RATE}
    (dest/'release.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();print(json.dumps(assemble(a.source,a.out),indent=2))
