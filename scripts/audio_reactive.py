"""Frame-accurate RMS and transient envelope from a licensed input soundtrack.

An optional, operator-provided audio track drives ONLY outside-window glow.
Silent session replays remain silent and static. No invented soundtrack.
"""
from __future__ import annotations
from pathlib import Path
import math,subprocess
import numpy as np

SAMPLE_RATE=48000

def audio_envelope(path:Path,fps:int,frames:int)->list[float]:
    if not path.is_file():raise FileNotFoundError(path)
    if not 0<fps<=120 or frames<=0:raise ValueError('Invalid audio frame grid')
    duration=frames/fps
    cmd=['ffmpeg','-hide_banner','-loglevel','error',
         '-i',str(path),'-ac','1','-ar',str(SAMPLE_RATE),
         '-f','f32le','-acodec','pcm_f32le','-t',str(duration),'pipe:1']
    p=subprocess.run(cmd,check=True,capture_output=True,timeout=90)
    samples=np.frombuffer(p.stdout,dtype='<f4')
    if not samples.size:raise ValueError('Audio file decoded to silence or no samples')
    per_frame=SAMPLE_RATE/fps
    rms=np.zeros(frames,dtype=np.float32)
    for i in range(frames):
        left=round(i*per_frame);right=round((i+1)*per_frame)
        section=samples[left:min(right,len(samples))]
        if section.size:
            rms[i]=float(np.sqrt(np.mean(section.astype(np.float64)**2)))
    if float(rms.max())<1e-6:return [0.]*frames
    # Normalize by robust 95th percentile, suppress quiet ambient noise,
    # and emphasize rising transients without brutal strobing.
    ref=float(max(np.percentile(rms,95),1e-6))
    energy=np.clip((rms/ref-.07)/.93,0,1)
    rises=np.maximum(0,np.diff(rms,prepend=rms[0]))/ref
    target=np.clip(.60*energy+.40*np.minimum(1,rises*3.5),0,1)
    smooth=np.zeros(frames,dtype=np.float32)
    for i,v in enumerate(target):
        last=float(smooth[i-1]) if i else 0.
        a=.35 if v>last else .12
        smooth[i]=last+(float(v)-last)*a
    return [float(round(v,5)) for v in smooth]
