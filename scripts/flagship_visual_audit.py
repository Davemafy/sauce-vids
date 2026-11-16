"""Contact sheets from decoded MP4 pixels at identical source-frame indices."""
from __future__ import annotations
import argparse,json,hashlib
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
SRC=['clean-v1','cinematic-v2','experimental-v1']
LABEL=['A — CLEAN','B — CINEMATIC','C — EXPERIMENTAL']
TIMES=[.55,1.70,3.05,5.35]
# Six separate actual output moments on B's identical frame clock.
CURSOR_TIMES=[.00,.43,.97,1.10,1.48,5.35]
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

def source_frame(video:Path,t:float):
    cap=cv2.VideoCapture(str(video));cap.set(cv2.CAP_PROP_POS_FRAMES,round(t*60))
    okay,frame=cap.read();cap.release()
    if not okay or frame.shape[:2]!=(1080,1920):raise RuntimeError('Bad frame at '+str(t))
    return cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)

def make(out:Path,root:Path)->dict:
    out.mkdir(parents=True,exist_ok=True)
    f=ImageFont.truetype(FONT,22)
    # Each column is exactly the same source time for every treatment.
    canvas=Image.new('RGB',(1760,996),(19,21,22))
    d=ImageDraw.Draw(canvas)
    for i,t in enumerate(TIMES):
        d.text((i*440+14,9),f'SOURCE   {t:04.2f}s',font=f,fill=(190,195,195))
    for row,name in enumerate(SRC):
        clip=root/name/'master-1080p60.mp4'
        for col,t in enumerate(TIMES):
            frame=source_frame(clip,t)
            image=Image.fromarray(frame).resize((440,248),Image.Resampling.LANCZOS)
            canvas.paste(image,(col*440,42+row*316))
            d.text((col*440+14,296+row*316),LABEL[row],font=f,fill=(211,218,214))
    canvas.save(out/'ABC-frame-aligned.jpg',quality=89,optimize=True)
    # Native 1920x1080 sample frames are retained as real regression evidence.
    b=root/'cinematic-v2'/'master-1080p60.mp4'
    grid=Image.new('RGB',(1920,1250),(19,21,22));d=ImageDraw.Draw(grid)
    phase=['BEFORE APPROACH','CURSOR ACCELERATION','BADGE AREA / PRECLICK',
           'RECORDED CLICK','MODAL OPEN','AFTER SETTLING']
    for i,(t,label) in enumerate(zip(CURSOR_TIMES,phase)):
        image=Image.fromarray(source_frame(b,t))
        # Crop central interaction rectangle from the actual encoded master;
        # never reconstruct UI from screenshot or DOM for this audit.
        crop=image.crop((240,130,1680,1010)).resize((640,391),Image.Resampling.LANCZOS)
        x=(i%3)*640;y=(i//3)*620
        grid.paste(crop,(x,y+34))
        d.text((x+14,y+7),f'{t:.2f}s   {label}',font=f,fill=(220,229,226))
    grid.save(out/'cursor-six-phases.jpg',quality=89,optimize=True)
    paths=['ABC-frame-aligned.jpg','cursor-six-phases.jpg']
    result={'files':{k:hashlib.sha256((out/k).read_bytes()).hexdigest() for k in paths},
            'source_times_s':TIMES,'cursor_times_s':CURSOR_TIMES,
            'master':'cinematic-v2/master-1080p60.mp4'}
    (out/'audit.json').write_text(json.dumps(result,indent=2))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    p.add_argument('--root',type=Path,default=Path('studio/.tmp/flagship'))
    a=p.parse_args();print(json.dumps(make(a.out,a.root),indent=2))


def selected_contact(out:Path,root:Path)->dict:
    """Same source-clock interactions across A/B/C and the V4 editorial cut.

    A/B/C source videos have no establishing insert; V4 puts that very same
    verified interaction at +132 frames, then uses a distinct result macro.
    """
    out.mkdir(parents=True,exist_ok=True)
    font=ImageFont.truetype(FONT,18)
    variants=[('A / CLEAN','clean-v1',0.),('B / CINEMATIC','cinematic-v2',0.),
              ('C / OPTICS','experimental-v1',0.),('V4 / STORY','B-v4',2.2)]
    samples=[.35,1.10,2.60,4.05]
    canvas=Image.new('RGB',(1536,1268),'#161819')
    draw=ImageDraw.Draw(canvas)
    for j,(label,folder,offset) in enumerate(variants):
        video=root/folder/'master-1080p60.mp4'
        for i,t in enumerate(samples):
            frame=source_frame(video,t+offset)
            shot=Image.fromarray(frame).resize((384,216),Image.Resampling.LANCZOS)
            x=i*384;y=j*316
            canvas.paste(shot,(x,y+40))
            draw.text((x+9,y+8),f'{label}  •  source +{t:.2f}s',font=font,
                      fill='#e7eae9')
    path=out/'ABCV4-source-frame-aligned.jpg'
    canvas.save(path,quality=88,optimize=True)
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    return {'path':str(path),'sha256':digest,'source_times_s':samples,
            'source_start_offset_v4_s':2.2}


def selected_contact_v5(out:Path,root:Path)->dict:
    """Final candidate V5 vs the unchanged A/B/C source-clock evidence."""
    out.mkdir(parents=True,exist_ok=True)
    font=ImageFont.truetype(FONT,18)
    variants=[('A / CLEAN','clean-v1',0.),('B / CINEMATIC','cinematic-v2',0.),
              ('C / OPTICS','experimental-v1',0.),('V5 / FINAL CANDIDATE','B-v5',2.2)]
    samples=[.35,1.10,2.60,4.05]
    canvas=Image.new('RGB',(1536,1268),'#161819')
    draw=ImageDraw.Draw(canvas)
    for row,(label,folder,offset) in enumerate(variants):
        film=root/folder/'master-1080p60.mp4'
        for col,t in enumerate(samples):
            real=Image.fromarray(source_frame(film,t+offset)).resize(
                    (384,216),Image.Resampling.LANCZOS)
            x=col*384;y=row*316
            canvas.paste(real,(x,y+40))
            draw.text((x+8,y+8),f'{label} • SOURCE +{t:.2f}s',
                      font=font,fill='#ecf0ed')
    path=out/'ABCV5-source-frame-aligned.jpg'
    canvas.save(path,quality=87,optimize=True)
    final=root/'B-v5'/'master-1080p60.mp4'
    moments=[(.60,'VERIFIED HOMEPAGE'),(2.20,'BEFORE APPROACH'),
             (2.63,'CURSOR ACCELERATION'),(3.30,'REAL CLICK CONTACT'),
             (3.68,'MODAL OPEN'),(6.15,'SOURCE RESPONSE SETTLED'),
             (7.30,'VERIFIED OUTCOME DETAIL'),(8.45,'SAUCE ENDING')]
    contact=Image.new('RGB',(1280,1028),'#161819')
    p=ImageDraw.Draw(contact)
    for index,(time,label) in enumerate(moments):
        full=Image.fromarray(source_frame(final,time))
        sample=full.resize((640,360),Image.Resampling.LANCZOS)
        x=(index%2)*640;y=(index//2)*257
        # Show actual video pixels at 640×360 with a label in the upper band.
        sample=sample.crop((0,0,640,230))
        contact.paste(sample,(x,y+25))
        p.text((x+10,y+3),f'{time:.2f}s  {label}',font=font,fill='#edf1ef')
    path2=out/'V5-verified-sequence.jpg'
    contact.save(path2,quality=86,optimize=True)
    return {'comparison':str(path),'sequence':str(path2),
      'digests':{name:hashlib.sha256((out/name).read_bytes()).hexdigest()
                 for name in (path.name,path2.name)},
      'source_times_s':samples,'v5_source_offset_s':2.2}
