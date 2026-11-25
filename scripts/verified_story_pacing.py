"""Compact a verified, already-rendered multi-action film without inventing frames.

The parent must preserve the original source clock. Cut only stationary
encoded holds, outside the recorded action/result windows. The receipt maps
each output interval back to its parent and original native frame indices.
"""
import argparse,hashlib,json,math,subprocess,wave
from pathlib import Path
import numpy as np
FPS=60
SAMPLES=800

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def probe(p):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,nb_frames','-of','json',str(p)]))['streams'][0]

def decode_small(p):
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-an','-vf','scale=320:180','-pix_fmt','rgb24','-f','rawvideo','-'])
    return np.frombuffer(raw,np.uint8).reshape(-1,180,320,3)

def stable_runs(frames,a,b,threshold=.30):
    """Every omitted frame must resemble the run's retained first frame."""
    if b<=a:return []
    runs=[];start=a;anchor=frames[a].astype(np.int16)
    for i in range(a+1,b):
        if np.abs(frames[i].astype(np.int16)-anchor).mean()>threshold:
            runs.append((start,i));start=i;anchor=frames[i].astype(np.int16)
    runs.append((start,b))
    return runs

def stationary_approach_gaps(frames,events,points,source_frames=None):
    """Shorten only recorded stationary pauses before the first real press.

    Both endpoints must have the exact same pointer coordinates. A recorded
    move interval (including sparse interpolation) is never considered idle.
    Keep at least .12s at either end and the first .35s of establishing context.
    """
    stop=math.floor((events[0]['start']-.12)*FPS)
    gaps=[]
    for p,q in zip(points,points[1:]):
        if p['x']!=q['x'] or p['y']!=q['y']:continue
        a=max(math.ceil((p['t']+.12)*FPS),math.ceil(.35*FPS))
        b=min(math.floor((q['t']-.12)*FPS),stop)
        if b-a<12:continue
        for l,r in stable_runs(frames,a,b):
            if r-l<12 or l<1 or r>=len(frames):continue
            if np.abs(frames[l-1].astype(np.int16)-frames[r].astype(np.int16)).mean()>.30:continue
            if source_frames is not None:
                if len(stable_runs(source_frames,l-1,r+1))!=1:continue
            gaps.append((l,r))
    return gaps


def plan_ranges(frames,events,points,ready_frame=None,source_frames=None):
    n=len(frames)
    if not 3<=len(events)<=4 or not points or n>1800:raise ValueError('Need bounded multi-action native film')
    for i,e in enumerate(events):
        if not e.get('evidence') or not 0<=e['start']<=e['end']<=e['t']<n/FPS:
            raise ValueError('Invalid verified action')
        if i and events[i-1]['t']>=e['start']:raise ValueError('Overlapping actions')
    # Preserve every sampled pointer movement. Sparse telemetry is not
    # filled with invented points; compare the rendered picture as well.
    if source_frames is not None and len(source_frames)!=n:raise ValueError("Source and parent sample clocks differ")
    if any(not 0<=p['t']<n/FPS or not all(math.isfinite(p[k]) for k in ('t','x','y')) for p in points):
        raise ValueError("Invalid pointer samples")
    if any(b['t']<=a['t'] for a,b in zip(points,points[1:])):raise ValueError("Pointer clock is not ordered")
    moving=[(a['t'],b['t']) for a,b in zip(points,points[1:]) if a['x']!=b['x'] or a['y']!=b['y']]
    movements=[b for a,b in moving]
    first=min((t for t in movements if t<events[0]['start']),default=0)
    lead=max(0,min(round((first-.35)*FPS),round(1.5*FPS)))
    if lead:
        # A genuine source state can change before the first pointer sample.
        # Preserve that change; shorten only the first verified stable run.
        lead=min(lead,stable_runs(frames,0,lead+1)[0][1]-15)
        lead=max(0,lead)
    if ready_frame is not None:
        # Explicit owner-review diagnostic for an observed loading/layout flash.
        # No action or recorded moving pointer can be skipped. The retained
        # starting frame must precede the first approach by at least .25s.
        if (type(ready_frame) is not int or not 0<=ready_frame<=min(round(2*FPS),math.floor((first-.25)*FPS))
            or ready_frame>=events[0]['start']*FPS or ready_frame+10>=n
            or len(stable_runs(frames,ready_frame,ready_frame+10,threshold=.75))!=1):
            raise ValueError('Ready frame would skip approach or is unstable')
        lead=max(lead,ready_frame)
    removals=[(a,b) for a,b in stationary_approach_gaps(frames,events,points,source_frames) if a>lead]
    for i,e in enumerate(events):
        a=math.ceil((e['t']+1.35)*FPS)
        if i+1<len(events):
            following=[t for t in movements if e['t']<t<=events[i+1]['start']]
            end=min(following,default=events[i+1]['start'])-.40
        else:
            # Preserve the final release move and final .4s of the film.
            end=n/FPS-.40
        b=min(n,math.floor(end*FPS))
        if b-a<FPS:continue
        for l,r in stable_runs(frames,a,b):
            # Keep .15s on either side of any cut; retain at least .8s.
            x,y=l+9,r-9
            if y-x>=48 and not any(a<y/FPS and b>x/FPS for a,b in moving):
                if np.abs(frames[x-1].astype(np.int16)-frames[y].astype(np.int16)).mean()<=.30:
                    if source_frames is None or len(stable_runs(source_frames,x-1,y+1))==1:
                        removals.append((x,y))
    ranges=[];start=lead
    for a,b in sorted(removals):
        if a<=start:continue
        ranges.append((start,a));start=b
    ranges.append((start,n))
    for e in events:
        if not any(a<=e['start']*FPS and e['t']*FPS<b for a,b in ranges):
            raise ValueError('Edit would remove action or result')
    return ranges

def remap(t,ranges):
    pos=0
    for a,b in ranges:
        if a<=t*FPS<b:return t-a/FPS+pos/FPS
        pos+=b-a
    raise ValueError('Verified event excluded from edit')

def run(parent,source,manifest,plan,foley,receipt,out,parent_sha256,ready_frame=None):
    parent,source,manifest,plan,foley,receipt,out=map(Path,(parent,source,manifest,plan,foley,receipt,out))
    if sha(parent)!=parent_sha256:raise ValueError("Parent film hash mismatch")
    d=json.loads(manifest.read_text());p=json.loads(plan.read_text());r=json.loads(receipt.read_text())
    if (p.get('sourceSha256')!=sha(source) or p.get('manifestSha256')!=sha(manifest) or
        d.get('provenance',{}).get('originalSourceSha256')!=sha(source) or not d.get('cursorless')):
        raise ValueError('Source and plan hash mismatch')
    parent_info=probe(parent);source_info=probe(source)
    n=int(parent_info['nb_frames'])
    if (parent_info['avg_frame_rate']!='60/1' or source_info['avg_frame_rate']!='60/1' or
        (parent_info['width'],parent_info['height'])!=(1920,1080) or
        n!=int(source_info['nb_frames']) or n!=round(d['duration']*FPS) or
        r['samples']!=n*SAMPLES or r['sample_rate']!=48000):
        raise ValueError('Parent and source clocks must match exactly')
    events=d['events']
    expected=[{'eventIndex':i,'pressAt':e['start'],'visibleResultAt':e['t']} for i,e in enumerate(events)]
    if r.get('verifiedSourceEvents')!=expected:raise ValueError('Foley proof mismatch')
    frames=decode_small(parent)
    if len(frames)!=n:raise ValueError('Parent decode count mismatch')
    source_frames=decode_small(source)
    ranges=plan_ranges(frames,events,d['pointer_samples'],ready_frame,source_frames)
    total=sum(b-a for a,b in ranges)
    if total>=n or total<8*FPS:raise ValueError('No useful safe pacing edit')
    # Confirm each internal splice at the original rendered resolution,
    # not only at the 320px planning scale. Compare exact native frames.
    cuts=[]
    for (_,left),(right,_) in zip(ranges,ranges[1:]):
        expr=f"eq(n,{left-1})+eq(n,{right})"
        raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(parent),'-an','-vf',f"select='{expr}'",'-fps_mode','passthrough','-pix_fmt','rgb24','-f','rawvideo','-'])
        pair=np.frombuffer(raw,np.uint8).reshape(-1,1080,1920,3)
        if len(pair)!=2:raise ValueError("Splice boundary decode failed")
        delta=float(np.abs(pair[0].astype(np.int16)-pair[1].astype(np.int16)).mean())
        if delta>.75:raise ValueError("Full-resolution splice not stationary")
        cuts.append({'leftFrame':left-1,'rightFrame':right,'fullResolutionMeanDelta':round(delta,5)})
    out.mkdir(mode=0o700,parents=True,exist_ok=False)
    filt='+'.join(f'between(n,{a},{b-1})' for a,b in ranges)
    picture=out/'picture.mp4'
    subprocess.run(['ffmpeg','-v','error','-nostdin','-i',str(parent),'-an','-vf',f"select='{filt}',setpts=N/60/TB",'-r','60','-c:v','libx264','-preset','fast','-crf','16','-pix_fmt','yuv420p','-movflags','+faststart',str(picture)],check=True)
    if int(probe(picture)['nb_frames'])!=total:raise ValueError('Edited frame count mismatch')
    # Sample-exact cut of the existing source-verified Foley, with the same
    # map as picture. Music is re-auditioned separately, never jump-cut.
    with wave.open(str(foley),'rb') as f:
        if (f.getnchannels(),f.getsampwidth(),f.getframerate(),f.getnframes())!=(2,2,48000,n*SAMPLES):raise ValueError('Foley mismatch')
        audio=f.readframes(n*SAMPLES)
    with wave.open(str(out/'foley.wav'),'wb') as f:
        f.setnchannels(2);f.setsampwidth(2);f.setframerate(48000)
        f.writeframes(b''.join(audio[a*SAMPLES*4:b*SAMPLES*4] for a,b in ranges))
    mapped=[{**e,'pressAt':remap(e['pressAt'],ranges),'visibleResultAt':remap(e['visibleResultAt'],ranges)} for e in expected]
    (out/'foley.json').write_text(json.dumps({**r,'samples':total*SAMPLES,'duration_s':total/FPS,'verifiedSourceEvents':mapped},indent=2))
    edl={'schema':'sauce-verified-story-pacing-v1','sourceSha256':sha(source),'manifestSha256':sha(manifest),'parentFilmSha256':sha(parent),'parentPlanSha256':sha(plan),'parentFoleySha256':sha(foley),'pictureSha256':sha(picture),'ranges':ranges,'operatorObservedReadyFrame':ready_frame,'spliceChecks':cuts,'outputFrames':total,'removedFrames':n-total,'events':mapped,'nativeFrameOrderPreserved':True,'continuousSourceTimeline':False,'creativeApproved':False}
    (out/'edit.json').write_text(json.dumps(edl,indent=2));return edl

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('parent','source','manifest','plan','foley','receipt','out'):p.add_argument('--'+k,required=True)
    p.add_argument('--parent-sha256',required=True)
    p.add_argument('--ready-frame',type=int,help='Optional operator-observed stable layout before first approach; research only')
    print(json.dumps(run(**vars(p.parse_args())),indent=2))
