#!/usr/bin/env python3
"""Measure real source video continuity and calibration from its physical slider knob.

Uses measured DOM geometry and recorded pointer track, but only to compare
against independently decoded X11 source pixels. Never generates footage.
"""
from __future__ import annotations
import argparse,hashlib,json,math
from pathlib import Path
import cv2,numpy as np

def verify(video:Path,events_path:Path, *, expected_frames=960):
    m=json.loads(events_path.read_text())
    cap=cv2.VideoCapture(str(video))
    if not cap.isOpened():raise ValueError("Missing real browser source")
    width,height=int(cap.get(3)),int(cap.get(4))
    fps=cap.get(5)
    if (width,height)!=(2880,1800) or abs(fps-60)>.01:
        raise ValueError("Source is not native DPR2 2880x1800 60fps")
    box=m["slider"]["controlRect"]
    left=int(box["x"])-10;right=int(box["x"]+box["width"])+10
    top=int(box["y"])-16;bottom=int(box["y"]+box["height"])+16
    xs=[];deltas=[];last=None
    while True:
        okay,frame=cap.read()
        if not okay:break
        roi=frame[top:bottom,left:right]
        bright=np.min(roi,axis=2)>223
        count,labels,stats,centroids=cv2.connectedComponentsWithStats(
            np.uint8(bright),8)
        spots=[]
        for idx in range(1,count):
            x,y,w,h,area=[int(v) for v in stats[idx]]
            # Native slider draws a white progress track connected to its
            # white thumb. The right edge of that same verified component
            # tracks the thumb even when its aggregate width grows.
            if 350<=area<=5200 and 35<=h<=63 and 24<=w<=460:
                spots.append((float(area),float(x+w+left)))
        x=max(spots)[1] if spots else float("nan")
        xs.append(x)
        sample=cv2.resize(roi,(224,16),interpolation=cv2.INTER_AREA).astype(np.int16)
        deltas.append(float(np.mean(np.abs(sample-last))) if last is not None else 0.)
        last=sample
    cap.release()
    if len(xs)!=expected_frames:raise ValueError(f"Decoded {len(xs)} instead of {expected_frames}")
    arr=np.array(xs)
    valid=np.isfinite(arr)
    if valid.mean()<.97:raise ValueError(f"White slider knob unreadable in {(~valid).sum()} frames")
    pointer=np.array([(p["t"],p["x"],p["y"]) for p in m["pointer_samples"]])
    drags=[]
    down=None
    for e in m["events"]:
        if e["kind"]=="pointerdown":down=e
        if e["kind"]=="pointerup":
            if down is None:raise ValueError("Unpaired recorded drag")
            drags.append((down["t"],e["t"]))
            down=None
    if len(drags)!=3:raise ValueError("Need three genuinely recorded drag intervals")
    # Optimize relative browser/UI sampling delay and source-start offset.
    # Knob may lag the pointer by a browser animation frame.
    scores=[]
    for offset_frames in range(-15,16):
        pairs=[]
        for i,x in enumerate(arr):
            t=i/60+offset_frames/60
            if not valid[i]:continue
            if not any(a+.12 <= t <= b-.07 for a,b in drags):continue
            px=float(np.interp(t,pointer[:,0],pointer[:,1]))
            pairs.append((x,px))
        if len(pairs)>20:
            p=np.asarray(pairs,dtype=float)
            bias=np.median(p[:,0]-p[:,1])
            diff=np.abs((p[:,0]-p[:,1])-bias)
            scores.append((float(np.median(diff)),float(np.mean(diff)),offset_frames,len(diff),float(bias)))
    if not scores:raise ValueError("No source-side moving thumb evidence")
    scores.sort()
    median,mean,offset,matched,bias=scores[0]
    distinct=0
    for idx in range(1,len(xs)):
        if math.isfinite(arr[idx]) and math.isfinite(arr[idx-1]):
            if abs(arr[idx]-arr[idx-1])>1.2:
                distinct+=1
    # Resend's segmented range control snaps between discrete tiers.
    # There are three *genuine state transitions*, not 45 continuous
    # intermediate knob positions. Don't mislabel that as dropped source
    # frames or claim every nominal 60fps frame has unique UI pixels.
    if median>34 or distinct<3:
        raise ValueError(f"Unverified snapped source median_px={median:.2f}, transitions={distinct}")
    # Independent video-pixel proof: the price text's genuine captured
    # rectangle must change between the before and after source frames.
    actions=[e for e in m["events"] if e["kind"]=="pointerdown"]
    results=[e for e in m["events"] if e["kind"]=="verified_result"]
    if len(actions)!=3 or len(results)!=3:
        raise ValueError("Missing source action/result pair")
    cal=cv2.VideoCapture(str(video))
    changes=[]
    try:
        for action,result in zip(actions,results):
            if action["label"]!=result["label"] or result["t"]<=action["t"]:
                raise ValueError("Changed price has no causal real click")
            pre=max(0,round((action["t"]-.22-offset/60)*60))
            post=min(len(xs)-1,round((result["t"]+.25-offset/60)*60))
            box=result["resultRect"]
            x0=int(box["x"]);y0=int(box["y"])
            x1=int(box["x"]+box["width"]);y1=int(box["y"]+box["height"])
            if not (0<=x0<x1<=width and 0<=y0<y1<=height):
                raise ValueError("Source price rectangle is offscreen")
            images=[]
            for f in (pre,post):
                cal.set(cv2.CAP_PROP_POS_FRAMES,f)
                ok,frame=cal.read()
                if not ok:raise ValueError("Missing source price evidence frame")
                images.append(frame[y0:y1,x0:x1])
            delta=np.abs(images[0].astype(np.int16)-images[1].astype(np.int16))
            changed_fraction=float(np.mean(np.max(delta,axis=2)>22))
            changes.append({"label":action["label"],"beforeFrame":pre,
                            "afterFrame":post,
                            "changedPixelFraction":round(changed_fraction,5)})
            if changed_fraction<.008:
                raise ValueError("Recorded movie does not prove actual price change")
    finally:cal.release()
    sha=hashlib.sha256()
    with video.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            sha.update(chunk)
    if sha.hexdigest()!=m["source_sha256"]:
        raise ValueError("Original captured media SHA does not match sidecar")
    return {
        "schema":"sauce-native-dpr2-slider-proof-v1",
        "sourceSha256":sha.hexdigest(),"frames":len(xs),"width":width,"height":height,
        "nominalFps":fps,
        "nativeThumbTransitionFrames":distinct,
        "sourceInteractionType":"discrete snapped slider: stable UI between verified tiers",
        "thumbReadableFrames":int(valid.sum()),
        "sourceFrameToBrowserClockOffsetFrames":offset,
        "medianThumbVsRecordedCursorPx":round(median,3),
        "meanThumbVsRecordedCursorPx":round(mean,3),
        "framesCompared":matched,
        "physicalThumbRightEdgeBiasPx":round(bias,3),
        "dragCount":len(drags),
        "sourcePixelResultChanges":changes,
        "publishedSource":False,
        "comment":"Actual browser has static holds; 60fps stream is not proof every frame is unique"
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--video",type=Path,required=True)
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    d=verify(a.video,a.manifest)
    a.out.write_text(json.dumps(d,indent=2)+"\n")
    print(json.dumps(d,indent=2))
