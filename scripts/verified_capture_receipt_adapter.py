"""Bridge genuine Chromium native-60fps click/result receipts into Sauce EDL.

Never fabricate interactions. Original source and receipts stay unchanged.
"""
from __future__ import annotations
import argparse,hashlib,json,math,subprocess,re
from pathlib import Path
import cv2,numpy as np

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def convert(source,receipt):
    source=Path(source);receipt=Path(receipt)
    old=json.loads(receipt.read_text())
    if (old.get("capture")!="Chromium X11 native DPR2 60fps" or
        old.get("cursorless") is not True or
        old.get("source_sha256")!=digest(source)):
        raise ValueError("Original Chromium provenance or source hash mismatch")
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error",
        "-show_entries","stream=width,height,avg_frame_rate,nb_frames:format=duration",
        "-of","json",str(source)],text=True))
    stream=probe["streams"][0];w,h=int(stream["width"]),int(stream["height"])
    duration=float(probe["format"]["duration"]);frames=int(stream["nb_frames"])
    if (stream["avg_frame_rate"]!="60/1" or
        frames!=round(duration*60) or old.get("frameCount")!=frames or
        (old.get("capture_rect") or {}).get("width")!=w or
        (old.get("capture_rect") or {}).get("height")!=h or
        not 5<=duration<=30):
        raise ValueError("Source frame/time geometry contradicts original receipt")
    pts=old.get("pointer_samples",[])
    if len(pts)<25:raise ValueError("No genuine cursor approach samples")
    prev=-1.
    for p in pts:
        values=[p.get(k) for k in ("t","x","y")]
        if any(type(v) not in (int,float) or not math.isfinite(v) for v in values):
            raise ValueError("Invalid real pointer values")
        t,x,y=values
        if not prev<t<duration or not 0<=x<w or not 0<=y<h:
            raise ValueError("Bad recorded pointer source timeline")
        prev=t
    def rect(obj):
        if not isinstance(obj,dict):raise ValueError("Real DOM bounds missing")
        v=[obj.get(k) for k in ("x","y","width","height")]
        if any(type(a) not in (int,float) or not math.isfinite(a) for a in v):
            raise ValueError("Unverified DOM bounds")
        x,y,bw,bh=v
        if not 0<=x<x+bw<=w or not 0<=y<y+bh<=h or bw<20 or bh<15:
            raise ValueError("Real DOM result/target not visible")
        return {k:round(float(a),4) for k,a in zip(("x","y","width","height"),v)}
    outstanding={};actions=[]
    for e in old.get("events",[]):
        if e.get("kind")=="pointerdown":
            label=e.get("label")
            if not label or label in outstanding:raise ValueError("Duplicate pointerdown")
            outstanding[label]=e
        elif e.get("kind")=="verified_result":
            label=e.get("label")
            if label not in outstanding:raise ValueError("No genuine matching press")
            press=outstanding.pop(label);start=press.get("t");end=e.get("t")
            if (type(start) not in (int,float) or type(end) not in (int,float)
                or not 0<=start<end<duration or end-start>3.5 or
                not e.get("evidence")):
                raise ValueError("No source-verifiable mouse action/result")
            target=rect(press.get("targetRect"));result=rect(e.get("resultRect"))
            if not any(abs(p["t"]-start)<.16 and
                target["x"]-18<=p["x"]<=target["x"]+target["width"]+18 and
                target["y"]-18<=p["y"]<=target["y"]+target["height"]+18
                for p in pts):
                raise ValueError("Recorded pointer does not approach observed control")
            action={"kind":"slider_change","start":float(start),
                "t":float(end),"end":float(end),"targetRect":target,"resultRect":result,
                "evidence":"Original Chromium press and live observed result: "+
                    str(e["evidence"])[:160]}
            # The original browser receipt already verified this PUBLIC
            # pricing text was visibly present in the real page after the
            # drag. Pass only a strict, non-sensitive price token to the
            # director; never infer or invent product/plan labels.
            price=e.get("price")
            if isinstance(price,str) and re.fullmatch(
                    r"\$[0-9][0-9,]*(?:\.[0-9]{2})? / mo",price):
                action["observedPublicPrice"]=price
            actions.append(action)
    if outstanding or not 1<=len(actions)<=6:raise ValueError("Incomplete action chain")
    cap=cv2.VideoCapture(str(source))
    if not cap.isOpened():raise ValueError("Cannot decode source")
    changes=[]
    try:
        for e in actions:
            r=e["resultRect"];x,y,rw,rh=[int(round(r[k])) for k in ("x","y","width","height")]
            def crop(at):
                cap.set(cv2.CAP_PROP_POS_FRAMES,round(at*60))
                ok,frame=cap.read()
                if not ok:raise ValueError("Source result proof frame missing")
                return cv2.resize(frame[y:y+rh,x:x+rw],(128,64))
            before=crop(max(0,e["start"]-.3))
            after=crop(min(duration-1/60,e["t"]+.15))
            frac=float(np.mean(np.max(cv2.absdiff(before,after),axis=2)>12))
            if frac<.013:raise ValueError("Observed outcome lacks original source pixel change")
            changes.append(round(frac,5))
    finally:cap.release()
    return {"source":old["source"],"duration":duration,"cursorless":True,
        "capture_rect":{"width":w,"height":h},"events":actions,
        "pointer_samples":pts,
        "provenance":{"originalSourceSha256":digest(source),
            "originalReceiptSha256":digest(receipt),
            "sourcePixelChangedFractions":changes,
            "capturedFrames":frames,"capture":"Chromium X11 native DPR2 60fps"}}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True,type=Path)
    p.add_argument("--receipt",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    if a.output.exists():raise ValueError("Will not overwrite a source or existing manifest")
    data=convert(a.source,a.receipt)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(data,indent=2)+"\n")
    print(json.dumps({"verifiedEvents":len(data["events"]),
       "realPointerSamples":len(data["pointer_samples"]),
       "sourcePixelChangedFractions":data["provenance"]["sourcePixelChangedFractions"]}))
if __name__=="__main__":main()
