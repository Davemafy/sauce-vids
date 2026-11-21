#!/usr/bin/env python3
"""Produce a shorter, source-traceable action reel from an immutable verified capture.

This is an EDIT of genuine source frames, not a new continuous browser capture.
Protects every genuine press/result interval and never synthesizes pointer samples,
UI, prices, successful states or scene content. No model required.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import subprocess


def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def verified_input(source, manifest, expected_source, expected_manifest):
    if digest(source)!=expected_source or digest(manifest)!=expected_manifest:
        raise ValueError("Immutable original source or event manifest hash mismatch")
    info=json.loads(subprocess.check_output(
        ["ffprobe","-v","error","-select_streams","v:0",
         "-show_entries","stream=width,height,avg_frame_rate,nb_frames:format=duration",
         "-of","json",str(source)],text=True))
    stream=info["streams"][0]
    fps=Fraction(stream["avg_frame_rate"])
    if fps not in (Fraction(24),Fraction(25),Fraction(30),Fraction(60)):
        raise ValueError("Unsupported original source frame clock")
    total=int(stream.get("nb_frames") or round(float(info["format"]["duration"])*float(fps)))
    raw=json.loads(Path(manifest).read_text())
    if raw.get("cursorless") is not True or abs(float(raw["duration"])-total/float(fps))>.06:
        raise ValueError("Source event clock mismatch")
    rect=raw["capture_rect"]
    if (rect["width"],rect["height"])!=(stream["width"],stream["height"]):
        raise ValueError("Source geometry mismatch")
    events=raw.get("events",[])
    if not (1<=len(events)<=6):
        raise ValueError("One to six verified genuine events needed")
    for i,e in enumerate(events):
        if not (isinstance(e,dict) and isinstance(e.get("evidence"),str)
            and e["evidence"].strip() and
            0<=float(e["start"])<=float(e["t"])<=total/float(fps) and
            float(e.get("end",e["t"]))<=total/float(fps)):
            raise ValueError("Unverified event")
        if i and float(e["start"])<=float(events[i-1]["t"]):
            raise ValueError("Overlapping or unordered verified events")
        for kind in ("targetRect","resultRect"):
            box=e[kind]
            if any(k not in box for k in ("x","y","width","height")):
                raise ValueError("Missing source-measured geometry")
            x,y,w,h=(float(box[k]) for k in ("x","y","width","height"))
            if not (0<=x<x+w<=stream["width"] and 0<=y<y+h<=stream["height"]):
                raise ValueError("Source-measured rectangle invalid")
    return raw,float(fps),total


def choose_windows(events, fps, total, *, lead=.74, tail=.88, final_hold=2.40):
    """Protect all actual interactions; drop only non-essential interstitial time."""
    def begin(t): return max(0,min(total,math.floor(t*fps+1e-8)))
    def finish(t): return max(0,min(total,math.ceil(t*fps-1e-8)))
    proposed=[]
    for i,e in enumerate(events):
        start=begin(float(e["start"])-lead)
        end=finish(max(float(e["t"]),float(e.get("end",e["t"])))+
                   (final_hold if i==len(events)-1 else tail))
        if not (start<finish(e["start"])<=end and
                start<=begin(e["t"])<end):
            raise ValueError("Action/source result would be clipped")
        proposed.append((start,end))
    merged=[]
    for a,b in proposed:
        if merged and a-merged[-1][1] <= round(.32*fps):
            merged[-1]=(merged[-1][0],max(b,merged[-1][1]))
        else:
            merged.append((a,b))
    if any(b<=a for a,b in merged):
        raise ValueError("Empty source clip")
    if sum(b-a for a,b in merged)>total:
        raise ValueError("Source edit illegally extends actual timeline")
    return merged


def remap_manifest(raw,windows,fps):
    new=deepcopy(raw)
    spans=[]
    destination=0
    for a,b in windows:
        spans.append({"sourceStartFrame":a,"sourceEndFrameExclusive":b,
            "outputStartFrame":destination,"frames":b-a})
        destination+=b-a
    def remap(t):
        for i,((a,b),span) in enumerate(zip(windows,spans)):
            n=t*fps
            if a-1e-5<=n<b-1e-5 or (i==len(windows)-1 and abs(n-b)<1e-5):
                return round(span["outputStartFrame"]/fps+t-a/fps,8)
        return None
    events=[]
    for e in raw["events"]:
        item=deepcopy(e)
        for k in ("start","t","end"):
            when=remap(float(item[k]))
            if when is None:raise ValueError("Protected original event was cut")
            item[k]=when
        if not (item["start"]<=item["t"]<=destination/fps):
            raise ValueError("Rebased event timeline broken")
        if isinstance(item.get("pointer_samples"),list):
            item["pointer_samples"]=[dict(p,t=m) for p in item["pointer_samples"]
                 if (m:=remap(float(p["t"]))) is not None]
        events.append(item)
    new["events"]=events
    pointers=raw.get("pointer_samples",[])
    if not isinstance(pointers,list) or len(pointers)<3:
        raise ValueError("No recorded real cursor trajectory")
    mapped=[dict(p,t=m) for p in pointers
             if (m:=remap(float(p["t"]))) is not None]
    if len(mapped)<8 or any(b["t"]<=a["t"] for a,b in zip(mapped,mapped[1:])):
        raise ValueError("Edited cursor lacks authentic monotonic samples")
    new["pointer_samples"]=mapped
    new["duration"]=destination/fps
    # Timestamped clean plates belong to the ORIGINAL clock. An edited clip
    # cannot claim those same-clock surfaces remain synchronized.
    new.pop("domPlanes",None)
    return new,spans


def produce(source,manifest,out,source_hash,manifest_hash):
    source=Path(source).resolve();manifest=Path(manifest).resolve()
    out=Path(out).resolve()
    if out.exists() and any(out.iterdir()):
        raise ValueError("Refuse overwriting previous experiments or media")
    raw,fps,total=verified_input(source,manifest,source_hash,manifest_hash)
    windows=choose_windows(raw["events"],fps,total)
    edited,spans=remap_manifest(raw,windows,fps)
    out.mkdir(parents=True,exist_ok=True,mode=0o700)
    film=out/"original-pixels-action-reel.mp4"
    tracks=[]
    for i,(a,b) in enumerate(windows):
        tracks.append(f"[0:v]trim=start_frame={a}:end_frame={b},setpts=PTS-STARTPTS[v{i}]")
    tracks.append("".join(f"[v{i}]" for i in range(len(windows)))+
                  f"concat=n={len(windows)}:v=1:a=0,format=yuv420p[outv]")
    cmd=["ffmpeg","-nostdin","-hide_banner","-v","error","-y","-i",str(source),
         "-filter_complex",";".join(tracks),"-map","[outv]",
         "-an","-c:v","libx264","-preset","veryfast","-crf","18",
         "-movflags","+faststart","-threads","2",str(film)]
    subprocess.run(cmd,check=True,timeout=210)
    output_info=json.loads(subprocess.check_output(["ffprobe","-v","error",
        "-select_streams","v:0","-show_entries","stream=avg_frame_rate,nb_frames",
        "-of","json",str(film)],text=True))
    actual=output_info["streams"][0]
    if Fraction(actual["avg_frame_rate"])!=Fraction(fps) or int(actual["nb_frames"])!=sum(
        b-a for a,b in windows):
        raise ValueError("Re-encoded film lost the native source frame clock")
    subprocess.run(["ffmpeg","-v","error","-xerror","-i",str(film),
                    "-f","null","-"],check=True,timeout=140)
    sidecar=out/"rebased-verified-events.json"
    sidecar.write_text(json.dumps(edited,indent=2)+"\n")
    receipt={
        "schema":"sauce-source-trim-receipt-v1",
        "sourceType":"EDITED_AUTHENTIC_FRAMES_NOT_CONTINUOUS_BROWSER_RECORDING",
        "originalSourceSha256":source_hash,
        "originalManifestSha256":manifest_hash,
        "trimmedSourceSha256":digest(film),
        "rebasedManifestSha256":digest(sidecar),
        "nativeFps":fps,
        "sourceFrameCount":total,
        "outputFrameCount":sum(b-a for a,b in windows),
        "originalDurationSeconds":total/fps,
        "editedDurationSeconds":edited["duration"],
        "protectedEvents":len(edited["events"]),
        "retainedOriginalPointerSamples":len(edited["pointer_samples"]),
        "originalFrames":spans,
        "noNewUIOrPointerPixels":True,
        "creativeApproved":False}
    (out/"trim-receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--source-sha256",required=True)
    p.add_argument("--manifest-sha256",required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(produce(args.source,args.manifest,args.out,
                              args.source_sha256,args.manifest_sha256),indent=2))


if __name__=="__main__": main()
