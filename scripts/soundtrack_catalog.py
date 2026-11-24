"""Private CC0 music intake, measured excerpt suggestions and picture-locked audition.

The measured rhythm score is not creative approval. No track fetch or inference
is implicit, and no customer release approval survives a change to audio.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import wave
import numpy as np
from scipy.signal import stft, find_peaks, correlate

RATE=48000
HOP=256
ANALYSIS_RATE=16000

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def run(*args):
    return subprocess.check_output(args,stderr=subprocess.DEVNULL)

def decode(path,rate,channels,offset=0,duration=None):
    cmd=['ffmpeg','-v','error','-nostdin','-ss',str(offset),'-i',str(path)]
    if duration is not None:cmd+=['-t',str(duration)]
    cmd+=['-vn','-ar',str(rate),'-ac',str(channels),'-f','f32le','-']
    a=np.frombuffer(run(*cmd),dtype='<f4').reshape(-1,channels)
    if not len(a) or not np.isfinite(a).all():raise ValueError('Invalid audio')
    return a

def admit(root,row):
    root=Path(root).resolve()
    if row['license']!='CC0-1.0':raise ValueError('Unsupported license')
    def verified(rel,digest):
        p=(root/rel).resolve()
        if root not in p.parents or not p.is_file() or sha(p)!=digest:
            raise ValueError('Unpinned local asset')
        return p
    evidence=verified(row['license_evidence'],row['license_evidence_sha256'])
    html=evidence.read_text(errors='replace').replace('\\/','/')
    if 'CC0 1.0 Universal License' not in html or 'creativecommons.org/publicdomain/zero/1.0' not in html:
        raise ValueError('Missing CC0 source evidence')
    return verified(row['file'],row['sha256'])

def measure(path):
    x=decode(path,ANALYSIS_RATE,1)[:,0]
    f,t,z=stft(x,fs=ANALYSIS_RATE,nperseg=1024,noverlap=768)
    mag=np.log1p(np.abs(z)*100)
    flux=np.maximum(np.diff(mag,axis=1,prepend=mag[:,:1]),0).mean(axis=0)
    bass=np.mean(np.abs(z[f<150])**2,axis=0)
    power=np.mean(np.abs(z)**2,axis=0)
    flux=flux/(np.percentile(flux,95)+1e-8)
    power=power/(np.percentile(power,90)+1e-12)
    ac=correlate(flux-flux.mean(),flux-flux.mean(),mode='full')[len(flux)-1:]
    lo=int(60/180*ANALYSIS_RATE/HOP);hi=int(60/65*ANALYSIS_RATE/HOP)
    lag=lo+int(np.argmax(ac[lo:hi+1]))
    peaks,_=find_peaks(flux,distance=round(.15*ANALYSIS_RATE/HOP),prominence=.25)
    return {'duration':len(x)/ANALYSIS_RATE,'tempoEstimateBpm':round(60*ANALYSIS_RATE/(HOP*lag),1),
            'periodicity':round(float(ac[lag]/max(ac[0],1e-9)),3),
            'bassFraction':round(float(bass.mean()*len(f[f<150])/(np.mean(np.abs(z)**2)*len(f)+1e-12)),4),
            'onsets':[round(float(t[i]),3) for i in peaks],
            'rmsDb':round(float(20*np.log10(np.sqrt(np.mean(x*x))+1e-9)),2)},t,flux,power

def excerpts(t,flux,power,duration,seconds,accents=()):
    if seconds<=0 or seconds>duration:raise ValueError('Unusable duration')
    starts=np.arange(0,max(0,duration-seconds)+.001,.16)
    ranked=[]
    for start in starts:
        a=np.searchsorted(t,start);b=np.searchsorted(t,start+seconds)
        if b<=a:continue
        intro=power[a:np.searchsorted(t,start+min(1,seconds))]
        if not len(intro):continue
        energy=float(np.clip(np.mean(intro),0,1.5))
        continuity=float(np.clip(np.percentile(power[a:b],20),0,1))
        detail=float(np.clip(np.mean(flux[a:b]),0,1))
        align=[]
        for cue in accents:
            i=np.searchsorted(t,start+cue-.09);j=np.searchsorted(t,start+cue+.09)
            align.append(float(np.clip(np.max(flux[i:j],initial=0),0,2)))
        rank=.65*energy+.35*continuity+.30*detail+.30*(np.mean(align) if align else 0)
        ranked.append((float(rank),float(start)))
    ranked.sort(reverse=True)
    selected=[]
    for score,offset in ranked:
        if all(abs(offset-r['start'])>=seconds*.75 for r in selected):
            selected.append({'start':round(offset,3),'rhythmScore':round(score,4)})
        if len(selected)>=3:break
    return selected

def build(root,accents=(),seconds=10):
    root=Path(root)
    rows=json.loads((root/'intake.json').read_text())
    catalog=[]
    for r in rows:
        if r.get('status')!='candidate':continue
        p=admit(root,r);meta,t,flux,power=measure(p)
        meta['excerptCandidates']={str(n):excerpts(t,flux,power,meta['duration'],n) for n in (5,10,15)}
        meta['pictureAccents']=list(accents)
        meta['pictureExcerptCandidates']=excerpts(t,flux,power,meta['duration'],seconds,accents)
        catalog.append({**r,**meta,'approval':'unreviewed','usageCount':0})
    return {'schema':'sauce-soundtrack-catalog-v1','tracks':catalog,'scoreMeaning':'signal-based suggestions, not taste approval'}

def picture_hash(path):
    return run('ffmpeg','-v','error','-i',str(path),'-map','0:v:0','-c','copy','-f','hash','-hash','sha256','-').decode().strip()

def cue_times(proof,showcase_plan=None):
    if proof.get('verifiedSourceEvents'):
        if showcase_plan is not None:raise ValueError('Mixed source and showcase cue authority')
        pairs=proof['verifiedSourceEvents']
        return [e['visibleResultAt'] for e in pairs], [t for e in pairs for t in (e['pressAt'],e['visibleResultAt'])]
    if showcase_plan is None:raise ValueError('Missing genuine event or showcase Foley plan')
    plan=json.loads(Path(showcase_plan).read_text())
    if (plan.get('schema')!='sauce-foley-plan-v1' or plan.get('sampleRate')!=RATE
        or plan.get('muted') or plan.get('musicGain')!=0
        or abs(plan['durationMs']*48-proof['samples'])>.01
        or len(plan['cues'])!=proof['cue_count']):
        raise ValueError('Showcase Foley plan does not match receipt')
    times=[]
    for c in plan['cues']:
        if (c['sound']!='whoosh_soft' or type(c['outputSample']) is not int
            or not 0<=c['outputSample']<proof['samples']
            or abs(c['outputSample']/48-c['outputMs'])>.05):
            raise ValueError('Invalid showcase cue')
        times.append(c['outputSample']/RATE)
    return times,times

def audition(root,row,film,foley,receipt,out,showcase_plan=None):
    p=admit(root,row)
    info=json.loads(run('ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames,avg_frame_rate,width,height','-of','json',str(film)))['streams'][0]
    if info['avg_frame_rate']!='60/1' or (info['width'],info['height'])!=(1920,1080):raise ValueError('Expected landscape60 master')
    n=int(info['nb_frames'])*800;duration=n/RATE
    if not 3<=duration<=30:raise ValueError('Only bounded short auditions supported')
    foley_proof=json.loads(Path(receipt).read_text())
    if foley_proof['samples']!=n or foley_proof['sample_rate']!=RATE or foley_proof['muted']:
        raise ValueError('Foley receipt does not match output clock')
    with wave.open(str(foley),'rb') as f:
        if (f.getnchannels(),f.getframerate(),f.getsampwidth(),f.getnframes())!=(2,RATE,2,n):raise ValueError('Foley clock mismatch')
        fx=np.frombuffer(f.readframes(n),dtype='<i2').reshape(n,2).astype(np.float32)/32768
    _,times=cue_times(foley_proof,showcase_plan)
    offset=row['pictureExcerptCandidates'][0]['start']
    m=decode(p,RATE,2,offset,duration+.02)
    if len(m)<n:raise ValueError('Track ends before film')
    m=m[:n].copy()
    # RMS target for fair audition, NOT LUFS. Prevent loudness from winning.
    gain=min(4,10**(-18/20)/max(float(np.sqrt(np.mean(m*m))),1e-8))
    m*=gain
    from foley_mixer import _ducking_gain,_soft_knee
    ducks=[]
    for t in times:
        at=round(t*RATE)
        if 0<=at<n:
            ducks.append({'startSample':max(0,at-1920),'endSample':min(n,at+12000),'attackMs':40,'releaseMs':160,'attenuationDb':-3.5})
    m*=_ducking_gain(n,ducks)[:,None]
    # Very short attack avoids abrupt clip edges without a slow intro.
    m[:1440]*=np.linspace(0,1,1440)[:,None]
    m[-14400:]*=np.linspace(1,0,14400)[:,None]
    mix=_soft_knee(fx+m)
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists():raise ValueError('Refusing to overwrite existing audition')
    wav=out.with_suffix('.wav')
    with wave.open(str(wav),'wb') as f:
        f.setnchannels(2);f.setsampwidth(2);f.setframerate(RATE)
        f.writeframes((mix*32767).astype('<i2').tobytes())
    subprocess.run(['ffmpeg','-v','error','-nostdin','-i',str(film),'-i',str(wav),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','256k','-movflags','+faststart',str(out)],check=True)
    if picture_hash(out)!=picture_hash(film):raise ValueError('Picture stream changed')
    subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(out),'-f','null','-'],check=True)
    result={'track':row['id'],'trackSha256':row['sha256'],'start':offset,'duration':duration,'samples':n,'duckIntervals':ducks,'peak':float(np.max(np.abs(mix))),'musicGain':gain,'pictureHash':picture_hash(out),'filmSha256':sha(out),'inputFilmSha256':sha(film),'foleySha256':sha(foley),'foleyReceiptSha256':sha(receipt),'showcasePlanSha256':sha(showcase_plan) if showcase_plan else None,'ownerApproved':False}
    out.with_suffix('.json').write_text(json.dumps(result,indent=2))
    return result

def main():
    a=argparse.ArgumentParser();a.add_argument('--root',type=Path,required=True);a.add_argument('--film',type=Path,required=True);a.add_argument('--foley',type=Path,required=True);a.add_argument('--receipt',type=Path,required=True);a.add_argument('--tracks',nargs='+');a.add_argument('--role',choices=['interaction','showcase','transformation']);a.add_argument('--recent',nargs='*',default=[]);a.add_argument('--explore',action='store_true');a.add_argument('--showcase-plan',type=Path);a.add_argument('--out',type=Path,required=True)
    args=a.parse_args();ev=json.loads(args.receipt.read_text());seconds=ev['samples']/RATE
    accents,_=cue_times(ev,args.showcase_plan)
    if bool(args.tracks)==bool(args.role):raise ValueError('Choose exactly one explicit track list or editorial role')
    catalog=build(args.root,accents,seconds)
    if args.role:
        from soundtrack_taste import rank_candidates
        ranked=rank_candidates(catalog['tracks'],args.role,args.recent,args.explore)
        if not ranked:raise ValueError('No unused matching soundtrack candidate; abstaining')
        args.tracks=[ranked[0]['id']]
        catalog['selection']={'ranked':ranked,'chosen':args.tracks[0],'recent':args.recent}
    if not set(args.tracks)<=set(r['id'] for r in catalog['tracks']):raise ValueError('Unknown track requested')
    args.out.mkdir(parents=True,exist_ok=False)
    for row in catalog['tracks']:
        print(row['id'],row['tempoEstimateBpm'],row['pictureExcerptCandidates'][0],flush=True)
        if row['id'] in args.tracks:
            print(audition(args.root,row,args.film,args.foley,args.receipt,args.out/(row['id']+'.mp4'),args.showcase_plan),flush=True)
            row['auditionCount']=1
    (args.out/'catalog.json').write_text(json.dumps(catalog,indent=2))
if __name__=='__main__':main()
