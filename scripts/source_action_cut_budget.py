"""Bounded source-verified 3-event camera-cut compiler.

When the model chooses six ACTION/RESULT cuts for exactly three REAL events,
the renderer supports at most three intentional cuts. Preserve original
RESULT frame cuts. Keep the model's ACTION shot as a gentle movement only
when recorded pre-press pointer samples show actual approach; do not pull
the whole browser toward a tiny top-edge tab where its context disappears.

If source evidence is absent/incomplete, drop only redundant ACTION cuts.
Original creative JSON, source MP4, cursor, UI, result times remain unmodified.
The unchanged source-true strict renderer is final safety authority.
"""
from __future__ import annotations
import copy,math

def _finite(value):
    return type(value) in (int,float) and math.isfinite(value)

def _actual_approach(manifest,source_size,event_index,start):
    """Prove >8 genuine samples approaching a press, not synthetic path."""
    if (not isinstance(manifest,dict) or
        not isinstance(manifest.get("pointer_samples"),list) or
        not isinstance(source_size,(tuple,list)) or len(source_size)!=2):
        return None
    w,h=source_size
    event=manifest["events"][event_index]
    rect=event.get("targetRect",{})
    if any(not _finite(rect.get(k)) for k in ("x","y","width","height")):
        return None
    x,y,rw,rh=[rect[k] for k in ("x","y","width","height")]
    if not 0<=x<x+rw<=w or not 0<=y<y+rh<=h:return None
    samples=manifest["pointer_samples"]
    near=[p for p in samples if isinstance(p,dict)
          and all(_finite(p.get(k)) for k in ("t","x","y"))
          and max(0.,start-2.25)<=p["t"]<=start-.16]
    if len(near)<9:return None
    for a,b in zip(near,near[1:]):
        if b["t"]<=a["t"]:return None
    last=near[-1]
    if not (x-20<=last["x"]<=x+rw+20 and
            y-20<=last["y"]<=y+rh+20 and start-last["t"]<=.9):
        return None
    # A source tab at the top edge does not warrant camera-centering.
    # Context changes are grounded in its ORIGINAL measured browser rect.
    center_y=(y+rh/2)/h
    tiny_edge=center_y<.25 and rh/h<.078 and rw/w<.20
    return {"firstPointAt":near[0]["t"],"lastPointAt":last["t"],
            "sampleCount":len(near),"tinyEdgeControl":tiny_edge,
            "sourceRect":copy.deepcopy(rect)}

def fit_verified_result_cut_budget(plan,manifest,fps,*,source_size=None,
                                   preserve_real_approaches=True):
    draft=copy.deepcopy(plan)
    stage=draft.get("studioStage")
    if not isinstance(stage,dict):return draft,[]
    keys=stage.get("camera")
    events=manifest.get("events",[]) if isinstance(manifest,dict) else []
    if (not isinstance(keys,list) or len(events)!=3 or
            not _finite(fps) or fps<=0 or
            draft.get("cursor")!="recorded"):
        return draft,[]
    cuts=[(i,k) for i,k in enumerate(keys) if isinstance(k,dict) and k.get("cut") is True]
    if len(cuts)!=6 or any(e.get("evidence") is None for e in events):
        return draft,[]
    pairs=[]
    for ix,event in enumerate(events):
        target=[(i,k) for i,k in cuts if k.get("focus")==f"event:{ix}:target"]
        result=[(i,k) for i,k in cuts if k.get("focus")==f"event:{ix}:result"]
        if len(target)!=1 or len(result)!=1:return draft,[]
        ti,tk=target[0];ri,rk=result[0]
        press=event.get("start");observed=event.get("t")
        if any(not _finite(a) for a in (press,observed,tk.get("at"),rk.get("at"))):
            return draft,[]
        if (not ti<ri or
                tk["at"]<press-1e-6 or tk["at"]>observed+1/fps or
                rk["at"]<observed-1e-6 or rk["at"]-observed>.25 or
                rk["at"]-tk["at"]<.35 or
                abs(tk["at"]*fps-round(tk["at"]*fps))>.0001 or
                abs(rk["at"]*fps-round(rk["at"]*fps))>.0001):
            return draft,[]
        pairs.append((ti,tk,ri,rk))
    if sorted(i for i,_,_,_ in pairs)!=[
        i for i,k in cuts if k.get("focus","").endswith(":target")]:
        return draft,[]
    if sorted(i for _,_,i,_ in pairs)!=[
        i for i,k in cuts if k.get("focus","").endswith(":result")]:
        return draft,[]
    if any(a[2]>=b[0] for a,b in zip(pairs,pairs[1:])):
        return draft,[]
    changes=[]
    redundant=set()
    # Store original key indices for truthful receipts even after edits.
    for ix,(ti,tk,ri,rk) in enumerate(pairs):
        previous=keys[ti-1] if ti>0 else None
        approach=(_actual_approach(manifest,source_size,ix,events[ix]["start"])
                  if preserve_real_approaches else None)
        if (approach is not None and isinstance(previous,dict)
                and _finite(previous.get("at"))
                and _finite(tk.get("at"))):
            transition=max(previous["at"],approach["firstPointAt"])
            # Do not create a new pre-action key or move the source mouse:
            # replace ONLY the model-selected original target cut with a
            # source-timed smooth approach, bounded by genuine pointer.
            if transition<=tk["at"]-.27:
                before=copy.deepcopy(tk)
                tk.pop("cut",None)
                tk["startAt"]=round(transition,9)
                if approach["tinyEdgeControl"]:
                    tk.pop("focus",None)
                    tk["center"]=[.5,.5]
                changes.append({
                  "field":f"studioStage.camera[{ti}]",
                  "from":before,"to":copy.deepcopy(tk),
                  "eventIndex":ix,
                  "sourcePointerApproachSamples":approach["sampleCount"],
                  "actualNativeSourceRect":approach["sourceRect"],
                  "reason":"Preserve model ACTION framing as original pointer-proven "
                    "smooth approach instead of a redundant action hard cut; "
                    "source-measured tiny top-edge target retains full "
                    "product-window context. Original source/video and three "
                    "result hard cuts remain unchanged."})
                continue
        redundant.add(ti)
        changes.append({
            "field":f"studioStage.camera[{ti}]",
            "from":copy.deepcopy(tk),"to":None,"eventIndex":ix,
            "reason":"Delete redundant ACTION hard cut without enough "
                    "independent actual pointer approach evidence. Preserve "
                    "all three original RESULT source-frame cuts and UI."})
    draft["studioStage"]["camera"]=[
        key for i,key in enumerate(keys) if i not in redundant]
    return draft,changes
