"""Smoothly reconcile sparse mouse traces with observed click positions."""
from __future__ import annotations
from math import hypot

def align_click_positions(points,events,start_ms,fps,lead_ms=230,settle_ms=150):
    """Anchor the visual pointer to existing clicks without changing actions."""
    if not points:return points
    result=[list(p) for p in points]
    previous=-1
    for event in sorted(events,key=lambda e:e.get("t",0)):
        if event.get("type")!="pointerdown" or event.get("x") is None or event.get("y") is None:
            continue
        idx=round((event["t"]-start_ms)*fps/1000)
        if idx<0 or idx>=len(result):continue
        dx=float(event["x"])-result[idx][0]
        dy=float(event["y"])-result[idx][1]
        if hypot(dx,dy)<=3:continue
        first=max(previous+1,0,idx-round(lead_ms*fps/1000))
        last=min(len(result)-1,idx+round(settle_ms*fps/1000))
        for frame in range(first,last+1):
            if frame<=idx:
                q=(frame-first)/max(1,idx-first)
                weight=q*q*(3-2*q)
            else:
                q=(frame-idx)/max(1,last-idx)
                weight=1-q*q*(3-2*q)
            result[frame][0]+=dx*weight
            result[frame][1]+=dy*weight
        previous=idx
    return [tuple(p) for p in result]
