"""Source-true deterministic 48kHz soundtrack for Scripted v2.

Audio is opt-in. Voice and locally licensed music are decoded into the same
sample clock; music ducks beneath detected voice. The completed mix uses
two-pass EBU R128 loudness normalization, independent of render speed.
"""
from __future__ import annotations

import json
import re
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

RATE = 48000
TARGET_LUFS = -16.0
MUSIC_DUCK_GAIN = .22  # About -13 dB under voiced passages.
VOICE_THRESHOLD = .004  # Conservative noise-floor gate on 20 ms blocks.


def _decode(path: Path, length: int, loop: bool=False) -> np.ndarray:
    if not path.is_file() or path.suffix.lower() not in ('.mp3','.wav','.ogg','.flac','.m4a'):
        raise ValueError("Audio must be an existing local MP3/WAV/OGG/FLAC/M4A")
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-nostdin']
    if loop:cmd += ['-stream_loop','-1']
    cmd += ['-i',str(path),'-t',f'{length/RATE:.8f}',
            '-f','f32le','-ac','2','-ar',str(RATE),'-']
    raw=subprocess.run(cmd,capture_output=True,check=True,timeout=120).stdout
    decoded=np.frombuffer(raw,dtype='<f4')
    if len(decoded)%2:raise RuntimeError("Invalid decoded audio")
    out=np.zeros((length,2),np.float32)
    n=min(length,len(decoded)//2)
    if n:out[:n]=decoded[:n*2].reshape(-1,2)
    if not np.isfinite(out).all():raise ValueError("Non-finite audio sample")
    return out


def original_bed(length:int)->np.ndarray:
    """Subtle original synthesized ambient pulse, not licensed stock music."""
    t=np.arange(length,dtype=np.float64)/RATE
    # A three-note original sustained texture; the 7-second drift prevents
    # hard musical downbeats from competing with verified UI click timing.
    tones=(np.sin(2*np.pi*110*t) +
           .48*np.sin(2*np.pi*164.8*t+.35*np.sin(2*np.pi*t/7.)) +
           .19*np.sin(2*np.pi*220*t+.13*np.sin(2*np.pi*t/9.)))
    tremolo=.7+.3*np.sin(2*np.pi*t/8.)**2
    attack=np.minimum(1.,t/.9)
    release=np.minimum(1.,(length/RATE-t)/1.)
    envelope=attack*np.maximum(0.,release)*tremolo
    left=(tones*envelope*.055).astype(np.float32)
    right=(np.roll(left,240)*.985).astype(np.float32)
    return np.column_stack((left,right)).astype(np.float32)


def _duck_envelope(voice:np.ndarray)->np.ndarray:
    block=960  # 20ms voice activity windows avoid sample-to-sample pumping.
    count=(len(voice)+block-1)//block
    mono=np.max(np.abs(voice),axis=1)
    padded=np.pad(mono,(0,count*block-len(mono)))
    rms=np.sqrt(np.mean(padded.reshape(count,block).astype(np.float64)**2,
                        axis=1))
    active=(rms>VOICE_THRESHOLD).astype(np.float32)
    # 120ms look-ahead/release prevents a music jump on every syllable.
    smooth=np.convolve(active,np.ones(13,dtype=np.float32)/13,mode='same')
    return np.repeat(1-(1-MUSIC_DUCK_GAIN)*smooth,block)[:len(voice)]


def _write_wav(path:Path,samples:np.ndarray):
    pcm=(np.clip(samples,-1,1)*32767).astype('<i2')
    with wave.open(str(path),'wb') as wf:
        wf.setnchannels(2);wf.setsampwidth(2);wf.setframerate(RATE)
        wf.writeframes(pcm.tobytes())


def make_soundtrack(out_wav:Path,frames:int,voice:Path|None=None,
                    music:Path|None=None,bed:bool=False,silent:bool=False)->dict:
    n=frames*(RATE//60)
    if silent and (voice or music or bed):
        raise ValueError("--silent cannot mix with other audio sources")
    # No opted-in soundtrack also means genuinely silent output. This avoids
    # passing an all-zero waveform into EBU R128 normalization (-inf LUFS).
    silent = bool(silent or not (voice or music or bed))
    output=np.zeros((n,2),np.float32)
    if not silent:
        if music is not None:
            output+=.26*_decode(music,n,loop=True)
        elif bed:
            output+=original_bed(n)
        if voice is not None:
            speech=_decode(voice,n)
            output*= _duck_envelope(speech)[:,None]
            output+=speech
    if np.max(np.abs(output))>2:
        output/=np.max(np.abs(output))/1.5
    _write_wav(out_wav,output)
    return {'schema':'sauce-scripted-v2-audio','sampleRate':RATE,
            'samples':n,'voice':bool(voice),'music':bool(music or bed),
            'ducked':bool(voice and (music or bed)),'silent':bool(silent)}


def _r128_params(wav:Path)->dict:
    result=subprocess.run(['ffmpeg','-hide_banner','-nostdin','-i',str(wav),
        '-af','loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json',
        '-f','null','-'],capture_output=True,text=True,check=True,timeout=90)
    block=re.search(r'\{\s*"input_i".*?\}',result.stderr,re.S)
    if not block:raise RuntimeError("Missing EBU R128 analysis data")
    return json.loads(block.group())


def mux_sound(video:Path,wav:Path,out:Path,frames:int,silent:bool=False)->dict:
    duration=frames/60
    if silent:
        af='volume=0'
        analysis={'targetLUFS':None}
    else:
        p=_r128_params(wav)
        af=(
            'loudnorm=I=-16:TP=-1.5:LRA=7:linear=true:'
            f'measured_I={p["input_i"]}:measured_TP={p["input_tp"]}:'
            f'measured_LRA={p["input_lra"]}:measured_thresh={p["input_thresh"]}:'
            f'offset={p["target_offset"]}'
        )
        analysis={'targetLUFS':TARGET_LUFS,'preNormalization':p['input_i']}
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y',
         '-i',str(video),'-i',str(wav),'-map','0:v:0','-map','1:a:0',
         '-c:v','copy','-c:a','aac','-ar',str(RATE),'-b:a','192k',
         '-af',af,'-t',f'{duration:.8f}','-movflags','+faststart',str(out)]
    subprocess.run(cmd,check=True,timeout=120)
    return analysis


def measured_lufs(path:Path)->float|None:
    p=subprocess.run(['ffmpeg','-hide_banner','-nostdin','-i',str(path),
       '-filter_complex','ebur128=peak=true','-f','null','-'],
       stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True,timeout=90,
       check=True)
    rows=re.findall(r'I:\s*(-?inf|[-+]?\d+(?:\.\d+)?)\s*LUFS',p.stderr)
    if not rows:return None
    val=rows[-1]
    return None if val=='-inf' else float(val)
