#!/usr/bin/env python3
"""Bridge unmodified Sauce anonymous-tab Chromium recordings to film EDL.

Never builds UI or invents states. Checks original source hash, original
discovery manifest, native 60fps frames, source-timed pointer path and
pixel differences around EACH actual browser-verified ARIA tab result.
"""
from __future__ import annotations
import argparse,hashlib,json,math,re,subprocess
from pathlib import Path

import cv2
import numpy as np

CAPTURE="Chromium X11 native DPR2 60fps"
SAFE_PUBLIC_LABEL=re.compile(r"^[A-Za-z][A-Za-z0-9 \-_]{0,41}$")

def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda:source.read(1<<20),b""):h.update(chunk)
    return h.hexdigest()

def _rect(raw,width,height):
    if not isinstance(raw,dict):
        raise ValueError("Original DOM rectangle missing")
    vals=[raw.get(k) for k in ("x","y","width","height")]
    if any(type(v) not in (int,float) or not math.isfinite(v) for v in vals):
        raise ValueError("Actual browser bounds must be finite")
    x,y,w,h=vals
    if x<0 or y<0 or w<25 or h<18 or x+w>width or y+h>height:
        raise ValueError("Actual browser rectangle outside recorded source")
    return {k:round(float(v),4) for k,v in zip(("x","y","width","height"),vals)}

def _frame_region(cap,at,fps,rect,*,max_t):
    frame=int(round(min(max(0.,at),max_t-1/fps)*fps))
    cap.set(cv2.CAP_PROP_POS_FRAMES,frame)
    ok,source=cap.read()
    if not ok:raise ValueError("Genuine result video frame missing")
    x,y,w,h=[int(round(rect[k])) for k in ("x","y","width","height")]
    return cv2.resize(source[y:y+h,x:x+w],(200,120),interpolation=cv2.INTER_AREA)

def normalize(source,original_receipt,discovery_file):
    source=Path(source)
    original_receipt=Path(original_receipt)
    discovery_file=Path(discovery_file)
    raw=json.loads(original_receipt.read_text())
    discovered=json.loads(discovery_file.read_text())
    if (raw.get("capture")!=CAPTURE or raw.get("cursorless") is not True
            or raw.get("source_sha256")!=digest(source)
            or raw.get("discoverySha256")!=digest(discovery_file)
            or raw.get("source")!=discovered.get("url")
            or not isinstance(discovered.get("actions"),list)):
        raise ValueError("Unchanged real source/discovery hashes required")
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error",
        "-show_entries","stream=width,height,avg_frame_rate,nb_frames:format=duration",
        "-of","json",str(source)],text=True))
    info=probe["streams"][0]
    width,height=int(info["width"]),int(info["height"])
    duration=float(probe["format"]["duration"])
    fps=60
    if (info["avg_frame_rate"]!="60/1"
        or (width,height)!=(2880,1800)
        or round(duration*60)!=int(info["nb_frames"])
        or int(info["nb_frames"])!=raw.get("frameCount")
        or not 10<=duration<=25
        or raw.get("fps")!=60
        or [raw.get("capture_rect",{}).get(k) for k in ("width","height")]!=[width,height]):
        raise ValueError("Native source dimensions/frame timing contradict original capture")
    expected=[a.get("name") for a in discovered["actions"]]
    if (not 2<=len(expected)<=3 or len(expected)!=len(set(expected))
        or any(not isinstance(t,str) or not SAFE_PUBLIC_LABEL.fullmatch(t) for t in expected)):
        raise ValueError("Only two or three trusted, distinct public action labels")
    points=raw.get("pointer_samples")
    if not isinstance(points,list) or len(points)<45:
        raise ValueError("Genuine cursor approach not captured")
    prior=-1.
    for p in points:
        if not isinstance(p,dict) or any(
              type(p.get(k)) not in (float,int) or not math.isfinite(p[k])
              for k in ("t","x","y")):
            raise ValueError("Recorded pointer sample invalid")
        t,x,y=(p[k] for k in ("t","x","y"))
        if not prior<t<duration or not (0<=x<width and 0<=y<height):
            raise ValueError("Actual cursor and video source clocks disagree")
        prior=t
    presses={}
    verified=[]
    for event in raw.get("events",[]):
        if not isinstance(event,dict):raise ValueError("Untrusted capture event shape")
        if event.get("kind")=="pointerdown":
            label=event.get("label")
            if label not in expected or label in presses:
                raise ValueError("Unexpected or repeated browser pointerdown")
            presses[label]=event
        if event.get("kind")=="verified_result":
            label=event.get("label")
            if label not in presses:
                raise ValueError("Outcome without matching observed browser click")
            press=presses.pop(label)
            if label!=expected[len(verified)]:
                raise ValueError("Captured browser outcomes not in proven discovery order")
            start=press.get("t");confirmed=event.get("t")
            if type(start) not in (int,float) or type(confirmed) not in (int,float):
                raise ValueError("Original browser events lack clock")
            if not 0<=start<confirmed<duration-.15 or confirmed-start>2.3:
                raise ValueError("Genuine browser event timing invalid")
            target=_rect(press.get("targetRect"),width,height)
            result=_rect(event.get("resultRect"),width,height)
            previous_samples=[p for p in points if p["t"]<=start]
            last=previous_samples[-1] if previous_samples else None
            if (last is None or start-last["t"]>.85 or
                    not(target["x"]-16<=last["x"]<=target["x"]+target["width"]+16 and
                        target["y"]-16<=last["y"]<=target["y"]+target["height"]+16)):
                raise ValueError("Genuine pointer never dwelled on clicked control")
            action={"kind":"tab_switch","start":float(start),"end":float(confirmed),
                "t":float(confirmed),"targetRect":target,"resultRect":result,
                "evidence":"Original Playwright browser ARIA tab selected, "
                           "visible actual result DOM changed and native source pixels verified",
                "observedPublicAction":label}
            verified.append(action)
    if presses or len(verified)!=len(expected):
        raise ValueError("Incomplete source-verified public tab story")
    cap=cv2.VideoCapture(str(source))
    if not cap.isOpened():raise ValueError("Cannot decode original source video")
    proofs=[]
    try:
        for action in verified:
            before=_frame_region(cap,action["start"]-.25,fps,action["resultRect"],max_t=duration)
            after=_frame_region(cap,action["t"]+.22,fps,action["resultRect"],max_t=duration)
            diff=np.max(cv2.absdiff(before,after),axis=2)
            changed=float(np.mean(diff>12))
            if changed<.022:
                raise ValueError("Recorded browser result does not actually change native pixels")
            proofs.append({"observedPublicAction":action["observedPublicAction"],
                "nativeSourceChangedFraction":round(changed,5),
                "observedResultAt":action["t"]})
    finally:cap.release()
    return {"source":raw["source"],"duration":duration,
        "cursorless":True,"capture_rect":{"width":width,"height":height},
        "events":verified,"pointer_samples":points,
        "provenance":{"sourceMethod":CAPTURE,
                      "originalSourceSha256":digest(source),
                      "originalBrowserReceiptSha256":digest(original_receipt),
                      "originalDiscoverySha256":digest(discovery_file),
                      "sourceFrameCount":int(info["nb_frames"]),
                      "nativeChangedResultProof":proofs,
                      "allowedActionType":"public anonymous reversible ARIA tabs",
                      "noSyntheticCursorOrProductPixels":True}}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",required=True,type=Path)
    parser.add_argument("--receipt",required=True,type=Path)
    parser.add_argument("--discovery",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    a=parser.parse_args()
    if a.output.exists():raise ValueError("Cannot overwrite original/adapted sidecar")
    manifest=normalize(a.source,a.receipt,a.discovery)
    a.output.parent.mkdir(exist_ok=True,parents=True)
    a.output.write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps({"nativeSourceSha256":manifest["provenance"]["originalSourceSha256"],
        "verifiedEvents":len(manifest["events"]),
        "originalPointerSamples":len(manifest["pointer_samples"]),
        "actualSourcePixelProof":manifest["provenance"]["nativeChangedResultProof"]}))
if __name__=="__main__":main()
