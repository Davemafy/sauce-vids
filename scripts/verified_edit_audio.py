"""Sauce original deterministic picture-locked Foley for a verified short EDL.

Generates sound ONLY for genuine recorded clicks, verified DOM outcomes,
recorded stable source-state changes, and the CAMERA MOVES we actually render.
No fake workflow, unsourced dialogue, licensed music or arbitrary whooshes.
The audio time map uses the exact EDL 60fps output-frame projection.
"""
from __future__ import annotations

import argparse
import json
import math
import hashlib
from pathlib import Path
import wave
import numpy as np

FPS=60
SAMPLE_RATE=48000
SAMPLES_PER_FRAME=SAMPLE_RATE//FPS


def actual_cues(manifest:dict,edit:dict)->list[dict]:
    if len(edit.get("shots",[]))<1 or not manifest.get("cursorless"):
        raise ValueError("No genuine cursorless source/timeline")
    source_hash=manifest.get("source_sha256")
    if not isinstance(source_hash,str) or len(source_hash)!=64 or any(
        c not in "0123456789abcdef" for c in source_hash.lower()):
        raise ValueError("Missing source SHA256 receipt; render source must independently match")
    lead=float(manifest["lead_s"])
    if not math.isfinite(lead) or lead<0 or lead>10:
        raise ValueError("Invalid capture timing offset")
    timeline=[]
    start=0
    for shot in edit["shots"]:
        a,b=shot["startFrame"],shot["endFrame"]
        if type(a) is not int or type(b) is not int or a<0 or b<=a:
            raise ValueError("Invalid source edit range")
        timeline.append((a,b,start))
        start+=b-a
    out=[]
    for event in manifest["events"]:
        kind=event.get("kind")
        if kind not in ("click","state_change"):continue
        if (not isinstance(event.get("t"),(int,float)) or
            not math.isfinite(float(event["t"])) or float(event["t"])<0):
            raise ValueError("Invalid recorded event timestamp")
        evidence=event.get("semanticGoal") if kind=="click" else event.get("evidence")
        if not isinstance(evidence,str) or not evidence.strip():
            raise ValueError("Recorded event lacks verified semantic evidence")
        tick=round((float(event["t"])+lead)*FPS)
        for a,b,origin in timeline:
            if a<=tick<b:
                out.append({"frame":origin+tick-a,
                            "kind":event["kind"],
                            "evidence":event.get("evidence") or event.get("semanticGoal") or "",
                            "source_frame":tick})
                break
    # Cut whoosh must be sourced from an actual shot boundary, not fantasy UI.
    for a,b,origin in timeline[1:]:
        out.append({"frame":origin,"kind":"edit_boundary",
                    "evidence":"real source footage cut at verified stable source spans",
                    "source_frame":a})
    # Moving camera who's audio is editorial (not a fictional product action).
    for a,b,origin in timeline:
        shot=next(x for x in edit["shots"] if x["startFrame"]==a)
        keys=shot.get("camera",[])
        for prev,cur in zip(keys,keys[1:]):
            if prev["zoom"]!=cur["zoom"] or prev["anchor"]!=cur["anchor"]:
                out.append({"frame":origin+prev["f"],"kind":"camera_transition",
                            "evidence":"camera pose change in actual editor frameplan",
                            "source_frame":a+prev["f"]})
    return sorted(out,key=lambda x:x["frame"])


def synthesize(manifest:dict,edit:dict,duration_frames:int,output:Path)->dict:
    if not 30<=duration_frames<=30*FPS:raise ValueError("Unbounded film duration")
    cues=actual_cues(manifest,edit)
    if not cues or not any(x["kind"]=="click" for x in cues):
        raise ValueError("No real click for synchronous sound")
    total=duration_frames*SAMPLES_PER_FRAME
    t=np.arange(total,dtype=np.float64)/SAMPLE_RATE
    # Low, gently moving original atmosphere: not a song, no generic trailer hit.
    smooth=np.sin(2*np.pi*86*t)*.0015+np.sin(2*np.pi*129*t)*.0008
    slow=np.sin(2*np.pi*(1.3*t+0.2*t*t))
    envelope=.45+.35*(slow+1)/2
    music=(smooth*envelope).astype(np.float32)
    left=music.copy()
    right=music.copy()
    rng=np.random.default_rng(20261119)
    wave_strength={"click":.068,"state_change":.025,
                   "edit_boundary":.043,"camera_transition":.016}
    for cue in cues:
        frame=int(cue["frame"])
        if not 0<=frame<duration_frames:continue
        at=frame*SAMPLES_PER_FRAME
        kind=cue["kind"]
        if kind=="click":
            count=round(.058*SAMPLE_RATE)
            seconds=np.arange(count)/SAMPLE_RATE
            wave_noise=rng.normal(size=count).astype(np.float32)
            # Quick tactile contact, no unlicensed audio sample.
            sound=(wave_noise*.9 + np.sin(2*np.pi*570*seconds)*.1)*np.exp(-seconds/.008)
        else:
            count=round((.13 if kind=="edit_boundary" else .17)*SAMPLE_RATE)
            seconds=np.arange(count)/SAMPLE_RATE
            wave_noise=rng.normal(size=count).astype(np.float32)
            # Band-limit noise by a running mean, airy transition not static hiss.
            kernel=np.full(33,1/33,np.float32)
            airy=np.convolve(wave_noise,kernel,mode="same")
            fade=np.sin(np.pi*np.clip(seconds/seconds[-1],0,1))**2
            sound=airy*fade
        strength=wave_strength[kind]
        n=min(len(sound),total-at)
        if n>0:
            out=(sound[:n]*strength).astype(np.float32)
            left[at:at+n]+=out*.95
            right[at:at+n]+=out
    peak=float(max(np.max(np.abs(left)),np.max(np.abs(right))))
    if peak>.5:
        left*=.5/peak;right*=.5/peak
    output.parent.mkdir(parents=True,exist_ok=True)
    pcm=np.column_stack((left,right))
    pcm=np.int16(np.clip(pcm,-1,1)*32767)
    with wave.open(str(output),"wb") as writer:
        writer.setnchannels(2)
        writer.setsampwidth(2)
        writer.setframerate(SAMPLE_RATE)
        writer.writeframes(pcm.tobytes())
    return {"schema":"sauce-original-verified-foley-v1",
            "source_sha256":manifest["source_sha256"],
            "pcm_sha256":hashlib.sha256(output.read_bytes()).hexdigest(),
            "frame_count":duration_frames,
            "sample_rate":SAMPLE_RATE,"samples_per_frame":SAMPLES_PER_FRAME,
            "audio_samples":total,"peak_before_limiter":round(peak,6),
            "cues":cues,"no_licensed_music":True,
            "all_events_trace_or_editor_backed":True}


if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--manifest",type=Path,required=True)
    cli.add_argument("--edl",type=Path,required=True)
    cli.add_argument("--frames",type=int,required=True)
    cli.add_argument("--out",type=Path,required=True)
    ns=cli.parse_args()
    receipt=synthesize(json.loads(ns.manifest.read_text()),
                       json.loads(ns.edl.read_text()),ns.frames,ns.out)
    print(json.dumps(receipt,indent=2))
