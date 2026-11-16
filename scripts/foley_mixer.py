"""48 kHz sample-accurate Foley for Sauce's versioned FoleyPlan.

No remote assets or implicit soundtrack. Local WAV/OGG samples may replace the
three deliberately subtle, reproducible NumPy/SciPy synths. This module NEVER
reads screenshots, clipboard contents, input text or the user's raw session.
"""
from __future__ import annotations
import json,math,subprocess,wave
from pathlib import Path
from typing import Any
import numpy as np

try:
    from scipy.signal import butter,sosfilt
except ImportError:  # NumPy-only fallback remains functional offline.
    butter=sosfilt=None

RATE=48000
SOUNDS=('click_crisp','whoosh_soft','pop_glass')
SEEDS={'click_crisp':1837,'whoosh_soft':5543,'pop_glass':2309}


def _synthesis(sound:str)->np.ndarray:
    if sound not in SOUNDS:raise ValueError('Unsupported Foley sound')
    length={'click_crisp':.074,'whoosh_soft':.38,'pop_glass':.23}[sound]
    n=int(round(length*RATE))
    t=np.arange(n,dtype=np.float64)/RATE
    rng=np.random.default_rng(SEEDS[sound])
    noise=rng.standard_normal(n)
    if sound=='click_crisp':
        if butter is not None:
            noise=sosfilt(butter(2,1550,btype='highpass',fs=RATE,output='sos'),noise)
        else:
            noise=noise-np.convolve(noise,np.ones(17)/17,mode='same')
        env=np.exp(-t/0.007)
        wave_signal=(.37*noise+.58*np.sin(2*np.pi*(1950*t+200*t*t)))*env
        wave_signal*=np.minimum(1,t/.0012)
    elif sound=='whoosh_soft':
        if butter is not None:
            noise=sosfilt(butter(2,1600,btype='lowpass',fs=RATE,output='sos'),noise)
        else:
            noise=np.convolve(noise,np.ones(13)/13,mode='same')
        env=np.sin(np.pi*np.minimum(1.,t/length))**2
        low=np.sin(2*np.pi*(180*t+500*t*t))
        wave_signal=(.48*noise+.16*low)*env*.75
    else:
        env=np.exp(-t/0.071)*np.minimum(1,t/.0028)
        bell=(np.sin(2*np.pi*(1240*t+45*t*t))+
              .38*np.sin(2*np.pi*2050*t))*.42
        wave_signal=(bell+.07*noise)*env
    wave_signal=np.clip(wave_signal,-1,1).astype(np.float32)
    return np.column_stack((wave_signal*.96,wave_signal)).astype(np.float32)


def _sample_asset(sound:str,asset_dir:Path|None)->np.ndarray|None:
    if asset_dir is None:return None
    root=Path(asset_dir).resolve()
    if not root.is_dir():raise FileNotFoundError(root)
    # Fixed allowlist, never paths or filenames originating in the trace.
    candidate=next((root/(sound+ext) for ext in ('.wav','.ogg')
                    if (root/(sound+ext)).is_file()),None)
    if candidate is None:return None
    if candidate.resolve().parent!=root:raise ValueError('Unsafe Foley asset path')
    p=subprocess.run(['ffmpeg','-v','error','-nostdin','-i',str(candidate),
       '-f','f32le','-ac','2','-ar',str(RATE),'-'],capture_output=True,check=True,
       timeout=28)
    if not p.stdout or len(p.stdout)%8:raise RuntimeError('Invalid local Foley sample')
    sample=np.frombuffer(p.stdout,dtype='<f4').reshape(-1,2).copy()
    if sample.shape[0]>RATE*4 or not np.isfinite(sample).all():
        raise ValueError('Sample is too long or nonfinite')
    peak=float(np.max(np.abs(sample)))
    if peak>1:sample=sample/peak
    return sample


def _music_buffer(path:Path,n:int)->np.ndarray:
    p=Path(path).resolve()
    if not p.is_file() or p.suffix.lower() not in ('.wav','.ogg','.mp3','.flac'):
        raise ValueError('Music must be a local WAV/OGG/MP3/FLAC file')
    cmd=['ffmpeg','-v','error','-nostdin','-i',str(p),
         '-f','f32le','-ac','2','-ar',str(RATE),'-']
    res=subprocess.run(cmd,capture_output=True,check=True,timeout=55)
    result=np.frombuffer(res.stdout,dtype='<f4')
    if len(result)%2 or not np.isfinite(result).all():
        raise ValueError('Invalid music data')
    stereo=result.reshape(-1,2)
    output=np.zeros((n,2),dtype=np.float32)
    usable=min(n,len(stereo))
    output[:usable]=stereo[:usable]
    return output


def _ducking_gain(n:int,intervals:list[dict])->np.ndarray:
    envelope=np.ones(n,dtype=np.float32)
    for interval in intervals:
        start=int(interval['startSample']);end=int(interval['endSample'])
        attack=int(round(float(interval['attackMs'])*RATE/1000.))
        release=int(round(float(interval['releaseMs'])*RATE/1000.))
        attenuation=float(interval['attenuationDb'])
        if (not 0<=start<end<=n or not -24<=attenuation<=0
            or attack<0 or release<0):raise ValueError('Invalid ducking interval')
        low=10**(attenuation/20.)
        arrival=min(end,start+max(1,attack))
        exit_start=max(arrival,end-max(1,release))
        span=np.full(end-start,low,dtype=np.float32)
        if arrival>start:
            span[:arrival-start]=np.linspace(1,low,arrival-start,dtype=np.float32)
        if end>exit_start:
            span[exit_start-start:]=np.linspace(low,1,end-exit_start,dtype=np.float32)
        envelope[start:end]=np.minimum(envelope[start:end],span)
    return envelope


def _soft_knee(x:np.ndarray,knee:float=.72,headroom:float=.23)->np.ndarray:
    # Smoothly approaches +/-0.95 rather than hard clipping at 0dBFS.
    a=np.abs(x)
    limit=knee+headroom*np.tanh(np.maximum(a-knee,0)/headroom)
    return np.sign(x)*np.where(a<=knee,a,limit)


def render_foley_plan(plan:dict,output_wav:Path,
                      asset_dir:Path|None=None,music:Path|None=None,
                      target_duration_ms:float|None=None)->dict[str,Any]:
    if plan.get('schema')!='sauce-foley-plan-v1' or plan.get('sampleRate')!=RATE:
        raise ValueError('Unexpected FoleyPlan schema or sample rate')
    duration=float(plan['durationMs'])
    if not math.isfinite(duration) or not 0<duration<=600000:
        raise ValueError('Invalid FoleyPlan duration')
    target=float(target_duration_ms) if target_duration_ms is not None else duration
    if target+1e-5<duration or not math.isfinite(target) or target>600000:
        raise ValueError('Audio cannot end before video frame timeline')
    n=math.ceil(target*RATE/1000)
    enabled=not bool(plan.get('muted',False))
    master=float(plan['masterGain']);music_gain=float(plan['musicGain'])
    if not 0<=master<=1 or not 0<=music_gain<=1:
        raise ValueError('Audio volume outside 0..1')
    fx=np.zeros((n,2),dtype=np.float32)
    sources:dict[str,str]={}
    if enabled:
        for event in plan.get('cues',[]):
            sound=event.get('sound')
            if sound not in SOUNDS:raise ValueError('Unrecognized Foley cue')
            at=event.get('outputSample')
            gain=event.get('gain')
            if (not isinstance(at,int) or not 0<=at<n
                or not isinstance(gain,(int,float)) or not math.isfinite(gain)
                or not 0<=gain<=1):
                raise ValueError('Invalid Foley cue position/gain')
            # Require sample-accurate correspondence to the typed output plan.
            if abs(float(event.get('outputMs',-10000))-at/48.)>.05:
                raise ValueError('Foley cue timestamp disagrees with outputSample')
            asset=_sample_asset(sound,asset_dir)
            clip=asset if asset is not None else _synthesis(sound)
            sources[sound]='local' if asset is not None else 'procedural'
            end=min(n,at+clip.shape[0])
            fx[at:end]+=clip[:end-at]*float(gain)
    mixed=fx.copy()
    if enabled and music is not None and music_gain>0:
        backing=_music_buffer(music,n)
        duck=_ducking_gain(n,plan.get('duckIntervals',[]))
        mixed+=backing*(music_gain*duck[:,None])
    if not enabled:mixed[:]=0.
    mixed=np.asarray(_soft_knee(mixed*master),dtype=np.float32)
    if not np.isfinite(mixed).all():raise ValueError('Non-finite audio output')
    peak=float(np.max(np.abs(mixed))) if n else 0.
    if peak>.951:raise RuntimeError('Limiter exceeded maximum output peak')
    output_wav=Path(output_wav)
    output_wav.parent.mkdir(parents=True,exist_ok=True)
    pcm=(np.clip(mixed,-1,1)*32767).astype('<i2')
    with wave.open(str(output_wav),'wb') as writer:
        writer.setnchannels(2);writer.setsampwidth(2);writer.setframerate(RATE)
        writer.writeframes(pcm.tobytes(order='C'))
    return {'schema':'sauce-foley-render-v1',
       'sample_rate':RATE,'channels':2,'samples':n,
       'duration_s':n/RATE,'cue_count':len(plan.get('cues',[])) if enabled else 0,
       'muted':not enabled,'asset_sources':sources,'peak':round(peak,6),
       'music_ducking':bool(music is not None and plan.get('duckIntervals') and enabled)}


def foley_shader_envelopes(plan:dict,frames:int,
                           asset_dir:Path|None=None,fps:int=60)->dict[str,list[float]]:
    """Deterministic shader uniforms from the SAME Foley samples as the mix.

    At 60 fps each video frame corresponds to exactly 800 48-kHz samples;
    outputSample (not source time, wall time or ffmpeg PTS) drives pulses.
    """
    if plan.get('schema')!='sauce-foley-plan-v1' or plan.get('sampleRate')!=RATE:
        raise ValueError('Invalid shader FoleyPlan')
    if not isinstance(frames,int) or frames<1 or frames>36000 or fps!=60:
        raise ValueError('Shader envelope requires deterministic 60fps')
    names={'click_crisp':'click','pop_glass':'glass'}
    samples_per_frame=RATE//fps
    output={channel:np.zeros(frames*samples_per_frame,dtype=np.float32)
            for channel in names.values()}
    if bool(plan.get('muted')):return {key:[0.]*frames for key in output}
    for cue in plan.get('cues',[]):
        name=cue.get('sound')
        if name not in SOUNDS:raise ValueError('Invalid shader sound')
        if name not in names:continue
        index=cue.get('outputSample')
        gain=cue.get('gain')
        if not isinstance(index,int) or index<0 or index>=frames*samples_per_frame or not isinstance(gain,(float,int)) or not 0<=gain<=1:
            raise ValueError('Invalid shader cue clock')
        asset=_sample_asset(name,asset_dir)
        wave=(asset if asset is not None else _synthesis(name)).mean(axis=1)
        block=output[names[name]]
        end=min(len(block),index+len(wave))
        block[index:end]+=wave[:end-index]*gain*float(plan['masterGain'])
    result={}
    for name,arr in output.items():
        rms=np.sqrt(np.mean(arr.reshape(frames,samples_per_frame).astype(np.float64)**2,
                            axis=1))
        # Audio peak is bounded; protect perceived transients without creating
        # shader pulses where no actual audio waveform exists.
        level=np.clip(rms/.10,0.,1.)
        result[name]=[float(round(q,5)) for q in level]
    return result
