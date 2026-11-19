"""Fail-closed reference-shot geometry fit using only verified source rectangles.

This determines whether a landscape UI element can share measured stage
geometry without stretching, clipping or manufacturing component pixels.
It does NOT assert narrative/editorial compatibility or creative approval.
"""
from __future__ import annotations
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class ReferenceFit:
    eligible_geometry: bool
    padding_px: int | None
    aspect_error_fraction: float | None
    padded_bounds: tuple[int,int,int,int] | None
    reason: str

def match_landscape_component(rect, viewport, reference_shape=(1520,480),
                              *, max_padding=60, tolerance=.02):
    if not isinstance(rect,dict) or any(k not in rect for k in ('x','y','width','height')):
        return ReferenceFit(False,None,None,None,"missing verified source rectangle")
    try:
        x,y,w,h=map(float,(rect['x'],rect['y'],rect['width'],rect['height']))
        vw,vh=map(float,viewport)
        rw,rh=map(float,reference_shape)
        nums=[x,y,w,h,vw,vh,rw,rh]
        if not all(math.isfinite(a) for a in nums) or min(w,h,vw,vh,rw,rh)<=0 or min(x,y)<0 or x+w>vw or y+h>vh:
            raise ValueError
        if rw/rh<=1.1 or max_padding<0 or not 0<=tolerance<=.20:
            raise ValueError
    except (ValueError,TypeError,OverflowError):
        return ReferenceFit(False,None,None,None,"invalid source/reference geometry")
    target=rw/rh
    # Expand using real neighboring pixels, never invent or nonuniformly stretch.
    if w/h>target:
        estimate=(w-target*h)/(2*(target-1))
    elif abs(w/h-target)/target<=tolerance:
        estimate=0
    else:
        return ReferenceFit(False,None,None,None,"source component is too tall for reference shape")
    if estimate>max_padding+2:
        return ReferenceFit(False,None,None,None,"required padding exceeds source-safe budget")
    matches=[]
    for pad in range(max(0,int(math.floor(estimate))-4),min(max_padding,int(math.ceil(estimate))+4)+1):
        x0=math.floor(x-pad);y0=math.floor(y-pad)
        x1=math.ceil(x+w+pad);y1=math.ceil(y+h+pad)
        if min(x0,y0)<0 or x1>vw or y1>vh:continue
        err=abs(((x1-x0)/(y1-y0))-target)/target
        matches.append((err,pad,(x0,y0,x1,y1)))
    if not matches:
        return ReferenceFit(False,None,None,None,"padded source component would clip")
    err,pad,bounds=min(matches)
    if err>tolerance:
        return ReferenceFit(False,pad,err,bounds,"padded source shape still mismatched")
    return ReferenceFit(True,pad,err,bounds,"geometry compatible, narrative still unverified")

def scale_end_for_frames(start_width_px,end_width_px,frame_count):
    """End-held JSON scale giving exact last *sampled* frame width at CFR."""
    if not isinstance(frame_count,int) or frame_count<2:raise ValueError("Need at least two frames")
    if not 0<start_width_px<=end_width_px<1e5:raise ValueError("Invalid sampled panel width")
    v=1.0+(end_width_px/start_width_px-1.0)*frame_count/(frame_count-1)
    if v>1.1:raise ValueError("Unreasonably large source-reference motion")
    return v
