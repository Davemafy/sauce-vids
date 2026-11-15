#!/usr/bin/env python3
"""Four-second sound edit, using Sauce's OWN previously generated narration.

Two truthful lines only: Connect it to Brimble; Copy the setup command.
The quiet synth ambience/foley is original and tied to recorded actions.
No third-party tracks, invented actions or text-to-speech API charges.
"""
from __future__ import annotations
import json,wave,math,argparse
from pathlib import Path
import numpy as np

def load_mono(path:Path)->tuple[np.ndarray,int]:
    with wave.open(str(path),'rb') as reader:
        if reader.getnchannels()!=1 or reader.getsampwidth()!=2:
            raise ValueError('Expected mono PCM16 original voice source')
        sr=reader.getframerate()
        raw=reader.readframes(reader.getnframes())
    return np.frombuffer(raw,dtype='<i2').astype(np.float64)/32768,sr

def produce(voice_wav:Path,voice_json:Path,session_path:Path,out_wav:Path,
            duration:float=4.0)->dict:
    voice,sr=load_mono(voice_wav)
    manifest=json.loads(voice_json.read_text())
    session=json.loads(session_path.read_text())
    actual_clicks=[e for e in session['events'] if e.get('type')=='pointerdown']
    assert len(actual_clicks)>=2
    startms=session['states'][0]['at_ms']
    clicks=[(e['t']-startms)/1000. for e in actual_clicks[:2]]
    assert .5<clicks[0]<1.2 and 1.7<clicks[1]<2.5
    length=int(round(duration*sr))
    mix=np.zeros(length,dtype=np.float64)
    selected=[('connect',.16),('copy',2.08)]
    cues=[]
    for key,destination in selected:
        item=next(a for a in manifest['lines'] if a['id']==key)
        if key=='connect': assert item['text']=='Connect it to Brimble.'
        if key=='copy': assert item['text']=='Copy the setup command.'
        clip=voice[round(float(item['start'])*sr):round(float(item['end'])*sr)].copy()
        fade=min(round(.025*sr),len(clip)//5)
        env=np.ones(len(clip),dtype=np.float64)
        env[:fade]=np.linspace(0,1,fade,endpoint=False)
        env[-fade:]=np.linspace(1,0,fade,endpoint=True)
        off=round(destination*sr)
        assert off+len(clip)<=length-.17*sr
        mix[off:off+len(clip)]+=clip*env
        cues.append({'id':key,'start':round(destination,3),
                     'end':round(destination+len(clip)/sr,3),
                     'text':item['text']})
    # Original subtly evolving harmonic drone: enough tone to separate the
    # voice from digital silence without a generic stock-music motif.
    t=np.arange(length)/sr
    attack=np.minimum(1.,t/.48)
    release=np.minimum(1.,(duration-t)/.65)
    envelope=np.maximum(0.,np.minimum(attack,release))
    low=.006*np.sin(2*np.pi*110*t+.03*np.sin(2*np.pi*.23*t))
    fifth=.0027*np.sin(2*np.pi*164.814*t)
    upper=.0019*np.sin(2*np.pi*220.00*t)
    mix+=(low+fifth+upper)*envelope
    # Soft mechanical response to real mouse-down, no stock UI boing.
    rng=np.random.default_rng(240)
    for k,click in enumerate(clicks):
        offset=round(click*sr)
        count=min(round(.095*sr),length-offset)
        u=np.arange(count)/sr
        noise=rng.standard_normal(count)
        noise=np.convolve(noise,np.ones(13)/13,mode='same')
        tap=(.011*np.sin(2*np.pi*(790 if k==0 else 980)*u)
             +.008*noise)*np.exp(-44*u)
        mix[offset:offset+count]+=tap
    # Gentle confirmed-dialog whoosh after actual visible event.
    event=next(e for e in session['events'] if e['type']=='dialog-visible')
    onset=round((event['t']-startms)/1000.*sr)
    N=min(round(.22*sr),length-onset)
    u=np.arange(N)/sr
    noise=rng.standard_normal(N)
    filtered=np.convolve(noise,np.ones(101)/101,mode='same')
    mix[onset:onset+N]+=filtered*.010*np.sin(np.pi*u/(N/sr))**2
    peak=np.max(np.abs(mix))
    if peak>.84:mix*=.84/peak
    out_wav.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(out_wav),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr)
        w.writeframes((np.clip(mix,-1,1)*32767).astype('<i2').tobytes())
    result={'duration':duration,'sample_rate':sr,'voice':'Kokoro af_heart (existing Sauce-owned recording)',
            'lines':cues,'recorded_clicks':clicks,'music':'original quiet harmonic ambience',
            'recorded_dialog_time':(event['t']-startms)/1000.}
    out_wav.with_suffix('.json').write_text(json.dumps(result,indent=2))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--voice',type=Path,required=True)
    p.add_argument('--voice-json',type=Path,required=True)
    p.add_argument('--session',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(produce(args.voice,args.voice_json,args.session,args.out),indent=2))
