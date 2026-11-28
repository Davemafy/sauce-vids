"""Research-only native footage library, never production acceptance."""
from __future__ import annotations
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
import cv2,numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from backend.curious_showcase import Conversation
from backend.customer_story import media
from scripts.customer_editorial import validate
from scripts.source_event_director import direction

def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2)
    path.chmod(0o600)
def extract(directory):
    src=directory/'source-native.mp4';r=json.loads((directory/'capture-receipt.json').read_text())
    if r.get('operator')!='browser-use' or r.get('sha256')!=sha(src) or r.get('status')!='captured':raise ValueError('Capture mismatch')
    v=r['stream']['streams'][0];w,h=v['width'],v['height'];n=int(v['nb_frames'])
    if (w,h)!=(3840,2160) or v['avg_frame_rate']!='60/1' or not 60<=n<=9000:raise ValueError('Native source required')
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(src),'-vf','scale=480:270:flags=fast_bilinear','-f','rawvideo','-pix_fmt','bgr24','-'],timeout=120)
    a=np.frombuffer(raw,np.uint8).reshape(-1,270,480,3)
    if len(a)!=n:raise ValueError('Incomplete decode')
    opening=cv2.resize(cv2.imread(str(directory/'opening.png')),(480,270))
    cal=float(np.mean(np.abs(opening.astype(float)-a[20].astype(float))))
    if cal>5:raise ValueError('Opening viewport mismatch')
    library=directory/'footage';library.mkdir(mode=0o700)
    clips=[];events=r['events']
    for j,e in enumerate(events):
        if e['kind']!='pointerdown':continue
        up=next((z for z in events[j+1:] if z['kind'] in ('pointerup','pointerdown')),None)
        if not up or up['kind']!='pointerup' or not 0<up['t']-e['t']<750:continue
        t=(e['t']-r['captureStartEpochMs'])/1000;end=(up['t']-r['captureStartEpochMs'])/1000
        k=round(t*60);lo=k-90;hi=k+390
        if lo<0 or hi>n:continue
        box={q:e['rect'][q]*2 for q in ('x','y','width','height')}
        px,py=e.get('x',-1)*2,e.get('y',-1)*2
        ux,uy=up.get('x',-1)*2,up.get('y',-1)*2
        if not (0<=ux<w and 0<=uy<h and abs(ux-px)<=4 and abs(uy-py)<=4):continue
        if not(0<=box['x']<box['x']+box['width']<=w and 0<=box['y']<box['y']+box['height']<=h and box['x']<=px<=box['x']+box['width'] and box['y']<=py<=box['y']+box['height']):continue
        before=a[k-45];after=a[k+100];settled=a[k+145]
        diff=lambda b,c:np.max(cv2.absdiff(b,c),axis=2)>25
        if diff(before,a[k-15]).mean()>.003 or diff(after,settled).mean()>.003:continue
        mask=diff(before,after)
        x0,y0,x1,y1=round(box['x']/8),round(box['y']/8),round((box['x']+box['width'])/8),round((box['y']+box['height'])/8)
        mask[max(0,y0-3):y1+3,max(0,x0-3):x1+3]=False
        if mask.mean()<.003:continue
        ys,xs=np.where(mask)
        x0=max(0,int(np.quantile(xs,.01))-12);x1=min(480,int(np.quantile(xs,.99))+13)
        y0=max(0,int(np.quantile(ys,.01))-12);y1=min(270,int(np.quantile(ys,.99))+13)
        if diff(before,a[k-10]).mean()>.002 or max(diff(before,a[q]).mean() for q in range(k,k+25))<.001:continue
        clip={'id':f'clip-{len(clips)+1}','startFrame':lo,'endFrame':hi,'clickSeconds':t,'releaseSeconds':end,'resultSeconds':(k+100)/60,'targetRect':box,'resultRect':{'x':x0*8,'y':y0*8,'width':(x1-x0)*8,'height':(y1-y0)*8},'clickPoint':[px,py],'releasePoint':[ux,uy],'pixelChangeFraction':round(float(mask.mean()),6),'stableChangeVerified':True,'clockPrecision':'approximate; decoded onset consistent within 0.4s'}
        for name,frame in [('before',k-45),('after',k+100)]:
            subprocess.run(['ffmpeg','-v','error','-ss',str(frame/60),'-i',str(src),'-frames:v','1','-vf','scale=1920:1080',str(library/f"{clip['id']}-{name}.png")],check=True,timeout=20)
        clips.append(clip)
    save(library/'index.json',{'sourceSha256':r['sha256'],'openingMeanAbsoluteError':cal,'clips':clips,'creativeApproved':False})
    return clips

def make(directory):
    directory=Path(directory).resolve();library=directory/'footage';src=directory/'source-native.mp4'
    clips=extract(directory)
    if len(clips)<2:raise ValueError('Less than two independently observed visual moments')
    conv=Conversation(directory/'creative-model',call_budget=1)
    images=[media((library/f"{c['id']}-{name}.png").read_bytes()) for c in clips for name in ('before','after')]
    prompt=("Direct a source-true product demonstration. Identify real product value from the paired images. "
            "Select two chronological clips that form a coherent developer/customer story. Do not invent features or reject useful changes because of arbitrary values. "
            "Each clip is eight seconds of actual recorded footage. Choose wide, accent or detail for each beat and quick/readable/linger pacing. "
            "Screen Studio research shows decisive pushes around 1.62x, stable holds and return to context; avoid repetitive zooms and tiny controls. "
            "Choose a graphite, muted, paper or cobalt backdrop. Return JSON {ids:[...],hero:'id',story:'...',backdrop:'...',beats:[{action_id:'id',framing:'wide|accent|detail',pace:'quick|readable|linger',purpose:'...'}]}. "
            "Return ids:[] if no coherent useful story. Images are before/after in clip order. Evidence: "+json.dumps(clips))
    raw=conv.ask(prompt,media=tuple(images),json_mode=True,phase='public-footage-editorial',stop_on_rate_limit=True,max_attempts=1)
    if not raw:raise ValueError('Director unavailable; original preserved')
    plan=json.loads(raw);save(directory/'creative-direction.json',plan);ids=plan.get('ids')
    if not isinstance(ids,list) or len(ids)!=2 or len(set(ids))!=2:raise ValueError('Director declined two-moment film')
    chosen=[next(c for c in clips if c['id']==i) for i in ids]
    if chosen[0]['endFrame']>chosen[1]['startFrame']:raise ValueError('Clip order invalid')
    duration=16;hero=plan['hero']
    editorial={'backdrop':plan['backdrop'],'duration_seconds':duration,'beats':plan['beats']}
    validate(editorial,ids,hero,check_budget=False)
    parts=[];names=[]
    for i,c in enumerate(chosen):
        parts.append(f"[0:v]trim=start_frame={c['startFrame']}:end_frame={c['endFrame']},setpts=PTS-STARTPTS[v{i}]");names.append(f"[v{i}]")
    compact=directory/'compact-source.mp4'
    subprocess.run(['ffmpeg','-v','error','-i',str(src),'-filter_complex',';'.join(parts+[''.join(names)+'concat=n=2:v=1:a=0[v]']),'-map','[v]','-c:v','libx264','-preset','ultrafast','-crf','18','-threads','4','-pix_fmt','yuv420p','-movflags','+faststart',str(compact)],check=True,timeout=180)
    v=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,nb_frames,avg_frame_rate','-of','json',str(compact)]))['streams'][0]
    if int(v['nb_frames'])!=duration*60 or v['avg_frame_rate']!='60/1':raise ValueError('Edited source clock mismatch')
    events=[];points=[]
    for i,c in enumerate(chosen):
        offset=i*8-c['startFrame']/60;start=c['clickSeconds']+offset;end=c['releaseSeconds']+offset
        events.append({'kind':'click','start':start,'end':end,'t':c['resultSeconds']+offset,'targetRect':c['targetRect'],'resultRect':c['resultRect'],
            'evidence':'Decoded stable visual change outside clicked control; fraction '+str(c['pixelChangeFraction'])})
        for t,point in ((start,c['clickPoint']),(end,c['releasePoint'])):points.append({'t':t,'x':point[0],'y':point[1]})
    manifest={'source':json.loads((directory/'capture-receipt.json').read_text())['source'],'duration':duration,'cursorless':True,'capture_rect':{'width':v['width'],'height':v['height']},
       'events':events,'pointer_samples':points,'pointerMotionProvenance':'editorial-reconstructed-from-observed-clicks',
       'provenance':{'originalSourceSha256':sha(src),'originalReceiptSha256':sha(directory/'capture-receipt.json'),'originalFrameRanges':[[c['startFrame'],c['endFrame']] for c in chosen],'capture':'native source trim; research only','clockAlignmentVerified':False,'eventsAdvisoryOnly':True}}
    m=directory/'manifest.json';save(m,manifest)
    film=direction(compact,m,ids.index(hero),{'ids':ids,'hero':hero,'editorial':editorial})
    film['cursorMotion']='editorial-click-v1'
    fp=directory/'film-plan.json';save(fp,film)
    return compact,m,fp

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args()
    print(make(a.directory),flush=True)
