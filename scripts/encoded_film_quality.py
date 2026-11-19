"""Encoded-video QA for Sauce film preflight. Evidence, not taste scores.

Reads real frames AND audio; distinguishes a physically valid export from a
film worth reviewing. It produces source-bounded repair suggestions only.
Never authorizes synthetic state, autoplay, inference, or a premium approval.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import subprocess

import cv2
import numpy as np

SAMPLE_W = 320
SAMPLE_H = 180
OPENING_S = 2.4
FPS = 60


@dataclass(frozen=True)
class Finding:
    level: str
    code: str
    window: tuple[float,float]
    evidence: dict
    remedy: str


def _content_signature(image:np.ndarray)->tuple[np.ndarray,float]:
    small=cv2.resize(image,(SAMPLE_W,SAMPLE_H),interpolation=cv2.INTER_AREA)
    # Exclude outside 5% rim where shadows and floating-shell movement
    # could otherwise disguise an inert source application.
    center=small[10:-10,16:-16]
    bright=np.min(center,axis=2)>235
    return center.copy(),float(np.mean(bright))


def inspect_frames(frames:list[np.ndarray],fps:int=FPS,
                   event_frames:list[int]|None=None,
                   *,consider_opening=True)->list[Finding]:
    """Deterministic evidence measured from already-decoded video pixels."""
    if fps<1 or not frames:
        raise ValueError("Empty media or invalid frame clock")
    if len(frames)<min(15,fps//2):
        raise ValueError("Insufficient actual decoded picture evidence")
    if any(im.dtype!=np.uint8 or len(im.shape)!=3 or im.shape[2]!=3
           for im in frames):
        raise ValueError("Expected real 8-bit BGR decoded film frames")
    if len(set(im.shape for im in frames))!=1:
        raise ValueError("Source frames change geometry")
    pairs=[_content_signature(im) for im in frames]
    samples=np.asarray([p[0] for p in pairs],np.float32)
    brightness=np.array([p[1] for p in pairs])
    differences=np.asarray([np.mean(np.abs(samples[k+1].astype(np.float32)-samples[k].astype(np.float32))) for k in range(len(samples)-1)],np.float32)
    findings=[]
    def mark(level,code,a,b,metrics,repair):
        findings.append(Finding(level,code,(round(a/fps,3),round(b/fps,3)),metrics,repair))
    # Detect successive actual picture frames moving so little that the film
    # reads as frozen, rather than measuring 60fps container metadata alone.
    if consider_opening:
        n=min(len(frames),round(OPENING_S*fps))
        if n>=30:
            opening_diff=differences[:n-1]
            low=np.mean(opening_diff<.55)
            delta=np.mean(np.abs(samples[0]-samples[n-1]))
            actions=[i for i in (event_frames or []) if 0<=i<n]
            if low>.88 and delta<11 and not actions:
                mark('reject','INERT_OPENING',0,n-1,
                     {'fraction_nearly_static':round(float(low),4),
                      'source_image_change_MAE':round(float(delta),3),
                      'recorded_actions':0},
                     'Rebuild opening using a verified product action or observed result in the first 1–2s; do not fabricate one')
    # Single-frame jump is not necessarily bad; locate it and request an
    # inspection unless it was an intentional, declared editor cut.
    cuts=np.flatnonzero(differences>23)
    if len(cuts)>0:
        windows=[]
        for f in cuts:
            if windows and f<=windows[-1][-1]+3: windows[-1].append(int(f))
            else:windows.append([int(f)])
        for group in windows:
            f=group[np.argmax(differences[group])]
            if len(windows)>12:break
            mark('warn','ABRUPT_IMAGE_CHANGE',max(0,f-1),min(len(frames)-1,f+2),
                 {'delta_MAE':round(float(differences[f]),3)},
                 'Check this exact cut against verified shot boundaries; replace an unmotivated cut with an anchored match-cut or clean edit')
    # An anomalous full bright frame is legitimate on some products, so only
    # reject a sudden exposure spike RELATIVE to this video's own baseline.
    base=float(np.median(brightness))
    spikes=brightness>max(.28,base+.33)
    if np.any(spikes):
        idx=np.flatnonzero(spikes)
        groups=[]
        for f in idx:
            if groups and f<=groups[-1][-1]+2:groups[-1].append(int(f))
            else:groups.append([int(f)])
        for group in groups:
            if len(group)<max(2,round(.04*fps)):continue
            mark('reject','SOURCE_WASHOUT',group[0],group[-1],
                 {'bright_fraction_baseline':round(base,4),
                  'bright_fraction_max':round(float(max(brightness[group])),4)},
                 'Replace only affected frames with a verified stable source span; never synthesize missing UI')
    return findings


def audio_evidence(video:Path,sample_rate=48000)->dict:
    result=subprocess.run([
        'ffmpeg','-nostdin','-v','error','-i',str(video),
        '-vn','-f','f32le','-ac','1','-ar',str(sample_rate),'pipe:1'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=80)
    if result.returncode:
        if b'Output file does not contain any stream' in result.stderr:
            return {'present':False,'silence_ratio':1.0,'duration':0.0}
        raise RuntimeError('Audio decode failed: '+result.stderr.decode(errors='replace')[-240:])
    raw=result.stdout
    if not raw:
        return {'present':False,'silence_ratio':1.0,'duration':0.0}
    signal=np.frombuffer(raw,dtype='<f4')
    block=sample_rate//4
    rms_values=[]
    for i in range(0,len(signal),block):
        segment=signal[i:i+block]
        if len(segment)>block//2:
            rms_values.append(float(np.sqrt(np.mean(segment*segment))))
    rms=np.asarray(rms_values,dtype=np.float32)
    return {'present':True,
            'silence_ratio':round(float(np.mean(rms<.00045)),4),
            'duration':round(len(signal)/sample_rate,4),
            'peak':round(float(np.max(np.abs(signal))),6),
            'rms_quarters':len(rms)}


def assess_encoded_video(path:Path,*,events:list[dict]|None=None,
                         source_fps:float|None=None,
                         expected_frames:int|None=None,
                         max_scan_frames:int=1800)->dict:
    path=Path(path)
    probe=json.loads(subprocess.check_output([
        'ffprobe','-v','error','-show_entries',
        'stream=codec_name,width,height,r_frame_rate,nb_frames,sample_rate:format=duration',
        '-of','json',str(path)],text=True,timeout=20))
    streams=probe['streams']
    stream=next((s for s in streams if s.get('codec_name') in ('h264','hevc','vp9','av1')),None)
    if not stream:raise ValueError('No decodable video stream')
    num=int(stream.get('nb_frames') or 0)
    if num<1 or num>max_scan_frames:raise ValueError('Out-of-bounds decoded frame count')
    fpsnum,fpsden=[int(v) for v in stream['r_frame_rate'].split('/')]
    fps=fpsnum/fpsden
    if abs(fps-round(fps))>.001 or not 24<=fps<=120:
        raise ValueError('Unverified source/output video FPS')
    frames=[]
    cap=cv2.VideoCapture(str(path))
    if not cap.isOpened():raise ValueError('Could not decode video')
    try:
        for index in range(num):
            ok,frame=cap.read()
            if not ok:break
            frames.append(frame)
    finally:cap.release()
    if len(frames)!=num:raise RuntimeError('Video frame count not fully decodable')
    recorded=[int(e['output_frame']) for e in events or [] if 'output_frame' in e]
    findings=inspect_frames(frames,round(fps),recorded)
    if expected_frames is not None and num!=expected_frames:
        findings.append(Finding('reject','FRAME_COUNT_MISMATCH',
                 (0,round(num/fps,3)),
                 {'observed':num,'required':expected_frames},
                 'Bounded source-truth preserving end-pad/trim with frame map receipt; never conceal interior drop'))
    if source_fps is not None and source_fps+1 < fps:
        findings.append(Finding('warn','SOURCE_FPS_RESAMPLED',
                 (0,round(num/fps,3)),{'source_fps':source_fps,'output_fps':fps},
                 'Capture native high-resolution 60fps at origin; disclosure required'))
    if events is not None and not any(e.get('kind') in ('observed_state_change','state_change') for e in events):
        findings.append(Finding('reject','NO_VERIFIED_PRODUCT_PAYOFF',
                (0,round(num/fps,3)),
                {'real_source_actions':len(events),'verified_results':0},
                'Use public-site showcase classification or capture actual interaction and visible outcome'))
    audio=audio_evidence(path)
    if audio['silence_ratio']>.9:
        findings.append(Finding('warn','NEAR_SILENT_SOUNDTRACK',
                (0,round(num/fps,3)),
                {'silence_ratio':audio['silence_ratio']},
                'Direct restrained event-locked Foley and authentic sonic pacing; preserve mute preference'))
    return {'schema':'sauce-encoded-film-inspection-v1',
       'source_video':path.name,
       'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
       'output_fps':fps,'duration_seconds':float(probe['format']['duration']),
       'video_frames':num,'resolution':[stream['width'],stream['height']],
       'audio':audio,
       'findings':[asdict(x) for x in findings],
       'requires_repair':any(x.level=='reject' for x in findings),
       'human_premium_approval':False}


def bounded_review(preflight:list[dict],candidate:list[dict],*,used_attempts:int,
                   max_attempts:int=2)->dict:
    """Never claim premium success from only objective decoded-frame metrics."""
    if type(used_attempts) is not int or used_attempts<0 or max_attempts not in (1,2):
        raise ValueError('Invalid retry contract')
    if used_attempts>=max_attempts:
        return {'status':'stop_human_review','retries_remaining':0,'accepted':False}
    unresolved=[f for f in candidate if f.get('level')=='reject']
    if unresolved:
        if len([f for f in candidate if f.get('level')=='reject']) >= len(
            [f for f in preflight if f.get('level')=='reject']):
            return {'status':'reject_no_verified_improvement',
                    'retries_remaining':max_attempts-used_attempts-1,'accepted':False}
        return {'status':'repair_another_short_preflight',
                'retries_remaining':max_attempts-used_attempts-1,'accepted':False}
    return {'status':'request_human_visual_review','retries_remaining':max_attempts-used_attempts-1,
            'accepted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--video',type=Path,required=True)
    p.add_argument('--source-fps',type=float)
    p.add_argument('--expected-frames',type=int)
    p.add_argument('--out',type=Path)
    a=p.parse_args()
    result=assess_encoded_video(a.video,source_fps=a.source_fps,expected_frames=a.expected_frames)
    if a.out:a.out.write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
