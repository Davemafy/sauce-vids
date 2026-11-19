"""Source-true UI separation for Sauce's JSON-directed compositor.

Only real, hash-pinned browser frames may supply UI pixels. This primitive
intentionally creates editorial *still* cutouts, not fictitious interactive UI.
Source windows are measured verified event rectangles with bounded padding.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from pathlib import Path

import cv2
import numpy as np

from source_region_mask import rounded_region_mask

MAX_LAYERS = 6


def _number(value, name, minimum, maximum):
    if type(value) not in (int, float) or not math.isfinite(value) or not minimum <= float(value) <= maximum:
        raise ValueError(f"{name} must be finite and between {minimum} and {maximum}")
    return float(value)


def _object(value, allowed, required, label):
    if not isinstance(value, dict) or set(value)-set(allowed) or not set(required)<=set(value):
        raise ValueError(f"Invalid {label} fields")
    return value


def _point(v, label):
    if not isinstance(v, list) or len(v)!=2:
        raise ValueError(f"{label} must be [x,y] normalized to output")
    return (_number(v[0],f"{label}.x",0,1),
            _number(v[1],f"{label}.y",0,1))


def _anchor_box(anchor, manifest, width, height, source_at):
    if not isinstance(anchor,str):
        raise ValueError("UI layer anchor must be a verified event reference")
    parts=anchor.split(":")
    if len(parts)!=3 or parts[0]!="event" or not parts[1].isdigit() or parts[2] not in ("target","result","component"):
        raise ValueError("UI layer requires event:N:target, event:N:result or event:N:component")
    idx=int(parts[1]);events=manifest.get("events")
    if not isinstance(events,list) or idx>=len(events):
        raise ValueError("Missing verified UI event")
    event=events[idx]
    if not isinstance(event,dict) or not isinstance(event.get("evidence"),str) or not event["evidence"].strip():
        raise ValueError("UI layer requires genuine verified outcome evidence")
    at=_number(event.get("t"),"event outcome time",0,float("inf"))
    if parts[2] in ("result","component") and source_at < at:
        raise ValueError("Cannot extract a result before it exists")
    rect=event.get({"target":"targetRect","result":"resultRect",
                    "component":"componentRect"}[parts[2]])
    if not isinstance(rect,dict):
        raise ValueError("Missing verified source rectangle")
    try:
        x,y,w,h=(_number(rect[k],f"rect.{k}",0,float("inf")) for k in ("x","y","width","height"))
    except KeyError as exc:
        raise ValueError("Incomplete UI source rectangle") from exc
    if w<2 or h<2 or x+w>width or y+h>height:
        raise ValueError("UI region outside verified source pixels")
    return (x,y,x+w,y+h), at


@dataclass(frozen=True)
class IsolatedLayer:
    id: str
    anchor: str
    source_at: float
    start_at: float
    end_at: float
    position: tuple[float,float]
    enter_from: tuple[float,float]
    enter_seconds: float
    width_fraction: float
    padding_px: int
    radius_px: int
    z_index: int
    source_bounds: tuple[int,int,int,int]
    source_frame_index: int
    source_crop_sha256: str
    crop: np.ndarray


@dataclass(frozen=True)
class IsolationComposition:
    start_at: float
    background_bgr: tuple[int,int,int]
    layers: tuple[IsolatedLayer,...]

    def active(self, t):
        return self.start_at <= t and any(layer.start_at <= t < layer.end_at for layer in self.layers)


def load_isolation_composition(raw, manifest, source_path, source_size, source_duration):
    """Validate, and extract a bounded number of immutable browser-frame crops."""
    if raw is None:
        return None
    _object(raw,("mode","startAt","background","layers"),
            ("mode","startAt","background","layers"),"isolation composition")
    if raw["mode"]!="isolated-ui":
        raise ValueError("Unsupported composition mode")
    start=_number(raw["startAt"],"isolation.startAt",0,source_duration)
    color=raw["background"]
    if (not isinstance(color,list) or len(color)!=3 or any(type(v) is not int or not 0<=v<=255 for v in color)):
        raise ValueError("Background must be three RGB bytes")
    raw_layers=raw["layers"]
    if not isinstance(raw_layers,list) or not 1<=len(raw_layers)<=MAX_LAYERS:
        raise ValueError(f"Isolation accepts 1..{MAX_LAYERS} layers")
    sw,sh=source_size
    video=cv2.VideoCapture(str(source_path))
    if not video.isOpened():
        raise ValueError("Cannot read genuine browser source video")
    fps=video.get(cv2.CAP_PROP_FPS)
    frames=video.get(cv2.CAP_PROP_FRAME_COUNT)
    if not math.isfinite(fps) or fps<=0 or not math.isfinite(frames) or frames<=0:
        video.release()
        raise ValueError("Video needs a real frame clock")
    decoded=[]
    seen=set()
    try:
        for layer in raw_layers:
            _object(layer,("id","anchor","sourceAt","startAt","endAt","position","enterFrom",
                           "enterSeconds","widthFraction","paddingPx","radiusPx","zIndex"),
                    ("id","anchor","sourceAt","startAt","endAt","position","widthFraction"),"UI layer")
            layer_id=layer["id"]
            if not isinstance(layer_id,str) or not layer_id or len(layer_id)>40 or not all(c.isalnum() or c in "_-" for c in layer_id) or layer_id in seen:
                raise ValueError("Layer id must be unique and simple")
            seen.add(layer_id)
            source_at=_number(layer["sourceAt"],f"{layer_id}.sourceAt",0,source_duration-.001)
            first=_number(layer["startAt"],f"{layer_id}.startAt",start,source_duration)
            last=_number(layer["endAt"],f"{layer_id}.endAt",first+.05,source_duration+.001)
            if source_at > first:
                raise ValueError("Cannot introduce future UI state before source frame")
            padding=round(_number(layer.get("paddingPx",0),f"{layer_id}.paddingPx",0,180))
            box,at=_anchor_box(layer["anchor"],manifest,sw,sh,source_at)
            if first<at:
                raise ValueError("Cannot present an unobserved action result")
            x0=max(0,int(math.floor(box[0]-padding)))
            y0=max(0,int(math.floor(box[1]-padding)))
            x1=min(sw,int(math.ceil(box[2]+padding)))
            y1=min(sh,int(math.ceil(box[3]+padding)))
            if x1-x0<8 or y1-y0<8:
                raise ValueError("Invalid UI crop geometry")
            desired=_point(layer["position"],f"{layer_id}.position")
            origin=_point(layer.get("enterFrom",layer["position"]),f"{layer_id}.enterFrom")
            ease=_number(layer.get("enterSeconds",0.4),f"{layer_id}.enterSeconds",0.05,1.5)
            width=_number(layer["widthFraction"],f"{layer_id}.widthFraction",.05,.85)
            radius=round(_number(layer.get("radiusPx",12),f"{layer_id}.radiusPx",0,28))
            z=int(_number(layer.get("zIndex",0),f"{layer_id}.zIndex",-20,20))
            source_frame_index=round(source_at*fps)
            if source_frame_index>=int(frames):
                raise ValueError("Sampled UI source frame outside source footage")
            video.set(cv2.CAP_PROP_POS_FRAMES,source_frame_index)
            ok,frame=video.read()
            if not ok or frame.shape[:2]!=(sh,sw):
                raise ValueError("Browser media cannot supply requested source frame")
            crop=frame[y0:y1,x0:x1].copy()
            crop_sha=hashlib.sha256(crop.tobytes()).hexdigest()
            decoded.append(IsolatedLayer(layer_id,layer["anchor"],source_at,first,last,
                                        desired,origin,ease,width,padding,radius,z,
                                        (x0,y0,x1,y1),source_frame_index,crop_sha,crop))
    finally:
        video.release()
    # rgb -> cv2 bgr
    return IsolationComposition(start,tuple(reversed(color)),
                                tuple(sorted(decoded,key=lambda x:x.z_index)))


def _blend(frame,overlay,mask,x,y):
    height,width=frame.shape[:2]
    hh,ww=mask.shape
    left=max(0,x);top=max(0,y);right=min(width,x+ww);bottom=min(height,y+hh)
    if left>=right or top>=bottom:return
    region=frame[top:bottom,left:right]
    f=overlay[top-y:bottom-y,left-x:right-x]
    alpha=mask[top-y:bottom-y,left-x:right-x].astype(np.float32)[:,:,None]/255.0
    region[:]=np.clip(region.astype(np.float32)*(1-alpha)+f.astype(np.float32)*alpha,0,255).astype(np.uint8)


def render_isolated_stage(spec,t,output_size):
    """Return one BGR frame or None when original browser video owns the shot."""
    if spec is None or not spec.active(t):
        return None
    ow,oh=output_size
    bg=np.empty((oh,ow,3),dtype=np.uint8)
    bg[:]=spec.background_bgr
    for layer in spec.layers:
        if not layer.start_at<=t<layer.end_at:continue
        u=min(1.0,max(0.0,(t-layer.start_at)/layer.enter_seconds))
        ease=u*u*(3-2*u)
        nx=layer.enter_from[0]+(layer.position[0]-layer.enter_from[0])*ease
        ny=layer.enter_from[1]+(layer.position[1]-layer.enter_from[1])*ease
        alpha=ease
        target_width=max(8,round(ow*layer.width_fraction))
        src_height,src_width=layer.crop.shape[:2]
        target_height=max(8,round(target_width*src_height/src_width))
        if target_height>oh*.91:
            factor=(oh*.91)/target_height
            target_height=round(target_height*factor)
            target_width=round(target_width*factor)
        center_x=round(nx*ow);center_y=round(ny*oh)
        x=center_x-target_width//2;y=center_y-target_height//2
        if x<12 or y<12 or x+target_width>ow-12 or y+target_height>oh-12:
            raise ValueError("JSON isolated UI shot exceeds output safe margins")
        scaled=cv2.resize(layer.crop,(target_width,target_height),
                          interpolation=cv2.INTER_AREA if target_width<src_width else cv2.INTER_CUBIC)
        matte=rounded_region_mask((target_height,target_width),
                                  (0,0,target_width-1,target_height-1),layer.radius_px)
        # Neutral-stage shadow is a film treatment, never a reconstruction
        # of missing source UI pixels.
        shadow=cv2.GaussianBlur(cv2.copyMakeBorder(matte,22,22,22,22,cv2.BORDER_CONSTANT),
                                (0,0),13)
        shadow=np.uint8(np.clip(shadow.astype(np.float32)*.26*alpha,0,255))
        _blend(bg,np.full((target_height+44,target_width+44,3),(12,14,18),np.uint8),
               shadow,x-22,y-11)
        matte=np.uint8(np.round(matte.astype(np.float32)*alpha))
        _blend(bg,scaled,matte,x,y)
    return bg
