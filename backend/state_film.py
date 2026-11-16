"""Render a truthful Sauce film from SHA-verified captured browser states.

This path does not pretend a browser replay succeeded. It gives arbitrary
accessible public pages a dependable preview while replay QA remains strict.
"""
from __future__ import annotations
import hashlib,json,math,subprocess,sys
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageOps
from scripts.session_contract import verify_package
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
from produce_cinematic_demo import verify_mp4,build_web_player

FPS=30
CANVAS=(1280,720)
MASTER=(1920,1080)
DURATION=8.0

def select_states(session:dict,folder:Path)->list[dict]:
    selected=[]
    for item in session['states']:
        path=folder/'states'/item['file']
        if not path.is_file():raise RuntimeError('Captured state is missing')
        check=hashlib.sha256(path.read_bytes()).hexdigest()
        if check!=item['sha256']:raise RuntimeError('Captured browser pixels were modified')
        im=cv2.imread(str(path))
        if im is None:raise RuntimeError('Invalid capture screenshot')
        thumb=cv2.resize(im,(320,180),interpolation=cv2.INTER_AREA)
        if selected:
            difference=float(np.mean(np.abs(thumb.astype(np.int16)-selected[-1][1].astype(np.int16))))
            if difference<1.6:continue
        selected.append((item,thumb))
    if not selected:return [session['states'][0]]
    if len(selected)>4:
        idx=[0,round((len(selected)-1)/3),round(2*(len(selected)-1)/3),len(selected)-1]
        selected=[selected[i] for i in sorted(set(idx))]
    return [s for s,_ in selected]

def screen(path:Path)->np.ndarray:
    # Actual screenshot; no synthetic recreation of the website.
    with Image.open(path) as im:
        img=ImageOps.fit(im.convert('RGB'),CANVAS,method=Image.Resampling.LANCZOS)
        return cv2.cvtColor(np.asarray(img),cv2.COLOR_RGB2BGR)

def camera(image:np.ndarray,progress:float,rect:dict|None)->np.ndarray:
    h,w=image.shape[:2]
    # 1-4% camera push without cutting away large parts of the interface.
    amount=1.012+0.027*progress
    crop_w=round(w/amount);crop_h=round(h/amount)
    center_x=w*.50
    center_y=h*.50
    if rect and rect.get('width',0)>30 and rect.get('height',0)>20:
        fx=(rect['x']+rect['width']/2.)/1280.
        fy=(rect['y']+rect['height']/2.)/720.
        center_x+=max(-w*.095,min(w*.095,(fx-.5)*w*.16))
        center_y+=max(-h*.085,min(h*.085,(fy-.5)*h*.13))
    center_x=max(crop_w/2,min(w-crop_w/2,center_x))
    center_y=max(crop_h/2,min(h-crop_h/2,center_y))
    view=cv2.getRectSubPix(image,(crop_w,crop_h),(center_x,center_y))
    return cv2.resize(view,(w,h),interpolation=cv2.INTER_LINEAR)

def make_film(session_dir:Path,out:Path,*,title:str,story:str,
              mode:str='public_showcase',duration:float=DURATION)->dict:
    session_dir=Path(session_dir);out=Path(out)
    session=json.loads((session_dir/'session.json').read_text())
    verification=verify_package(session,session_dir)
    states=select_states(session,session_dir)
    if not 5<=duration<=15:raise ValueError('Unsupported film duration')
    out.mkdir(parents=True,exist_ok=True)
    frames=[screen(session_dir/'states'/s['file']) for s in states]
    count=int(round(duration*FPS))
    segment=count/len(frames)
    video=out/'preview.mp4'
    command=['ffmpeg','-hide_banner','-loglevel','error','-y','-nostdin',
         '-f','rawvideo','-pix_fmt','bgr24','-s','1280x720','-r',str(FPS),
         '-i','pipe:0','-an','-c:v','libx264','-preset','veryfast',
         '-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(video)]
    worker=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    if worker.stdin is None:raise RuntimeError('Encoder stdin unavailable')
    try:
        for index in range(count):
            shot=min(len(frames)-1,int(index/segment))
            start=round(shot*segment)
            span=max(1,round((shot+1)*segment)-start)
            progress=max(0,min(1,(index-start)/span))
            rendered=camera(frames[shot],progress,states[shot].get('focus_rect'))
            # Eight-frame honest cross-dissolve between observed states.
            if shot and index-start<9:
                old=camera(frames[shot-1],1,states[shot-1].get('focus_rect'))
                alpha=(index-start+1)/10.
                rendered=cv2.addWeighted(old,1-alpha,rendered,alpha,0)
            if index<8:rendered=cv2.convertScaleAbs(rendered,alpha=(index+1)/8.,beta=0)
            if index>count-8:rendered=cv2.convertScaleAbs(rendered,alpha=max(.05,(count-index)/8.),beta=0)
            worker.stdin.write(rendered.tobytes())
            if index%10==0 or index==count-1:
                print(f'REPLAY {index+1} of {count}',flush=True)
    except Exception:
        worker.kill()
        raise
    finally:
        try:worker.stdin.close()
        except (OSError,ValueError):pass
    stderr=(worker.stderr.read() if worker.stderr else b'').decode(errors='replace')
    if worker.wait(timeout=60)!=0:raise RuntimeError('Encoder failed: '+stderr[-450:])
    verify_mp4(video,*CANVAS,FPS)
    master=out/'master-1080p60.mp4'
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-nostdin',
         '-i',str(video),'-vf','scale=1920:1080:flags=lanczos,fps=60',
         '-c:v','libx264','-preset','veryfast','-crf','19',
         '-pix_fmt','yuv420p','-movflags','+faststart',str(master)],
         check=True,timeout=130)
    verify_mp4(master,*MASTER,60)
    poster=out/'poster.jpg'
    with Image.open(session_dir/'states'/states[min(1,len(states)-1)]['file']) as im:
        im=ImageOps.fit(im.convert('RGB'),CANVAS,method=Image.Resampling.LANCZOS)
        im.save(poster,quality=87)
    build_web_player(Path(__file__).parents[1]/'docs/sauce-premium-player-template.html',
                     out,title,story,duration)
    receipt={'render_mode':'sha-verified-source-states','source_url':session['source_url'],
       'title':title,'description':story,'plan_mode':mode,
       'source_states':len(session['states']),'selected_scenes':len(states),
       'screenshot_hashes_verified':len(session['states']),
       'replay_verified':False,'source_pixels_real':True,'ai_claims_unverified':False,
       'frames_preview':count,'preview_fps':FPS,'master_fps':60,
       'full_master_frames':count*2,'duration_seconds':duration,
       'limitations':['State montage uses real browser screenshots, not a continuous DOM replay.',
          'An interaction is not claimed to succeed without observed distinct states.']}
    (out/'release.json').write_text(json.dumps(receipt,indent=2))
    return receipt

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument('--session',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--title',default='Website walkthrough')
    ap.add_argument('--description',default='Recorded public website')
    ap.add_argument('--mode',default='public_showcase')
    args=ap.parse_args()
    print(json.dumps(make_film(args.session,args.out,title=args.title,
                    story=args.description,mode=args.mode)),flush=True)
