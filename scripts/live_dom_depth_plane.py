"""Opt-in independent LIVE DOM plane from two source-truth-verified browser streams.

One Chromium capture records visible and temporarily DOM-hidden frames at the
same page-clock time. The matching clean plate is a real page screenshot,
never inpainted, cloned from another time or reconstructed from an LLM.

No saved source footage may be paired with an unrelated screenshot. Cryptographic
and per-frame outside-ROI pixel checks are mandatory. Source frame and true
clean plate still contain all original pixels; only post-result stage motion
of the genuinely observed element is artistic.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import math
import json
import subprocess

import cv2
import numpy as np


def _num(x,label,a,b):
    if type(x) not in (int,float) or not math.isfinite(x) or not a<=x<=b:
        raise ValueError(f"domPlane {label} must be within [{a}, {b}]")
    return float(x)


def _sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as file:
        for part in iter(lambda:file.read(1024*1024),b""):h.update(part)
    return h.hexdigest()


def _details(path):
    data=json.loads(subprocess.check_output([
        "ffprobe","-v","error","-select_streams","v:0",
        "-show_entries","stream=width,height,nb_frames,avg_frame_rate:format=duration",
        "-of","json",str(path)],timeout=20))
    return data["streams"][0],data["format"]


def _source_rect(raw,size):
    if not isinstance(raw,dict) or set(raw)!={"x","y","width","height"}:
        raise ValueError("domPlane has no measured source rectangle")
    dims=tuple(int(_num(raw.get(k),f"rect.{k}",0,max(size))) for k in
               ("x","y","width","height"))
    x,y,w,h=dims;sw,sh=size
    if w<40 or h<30 or x+w>sw or y+h>sh:
        raise ValueError("domPlane rect outside source or too small")
    return dims


def _eased(t):
    t=max(0.,min(1.,t))
    return t*t*t*(t*(6*t-15)+10)


@dataclass(frozen=True)
class LiveDomPlane:
    plate_file:Path
    plate_sha256:str
    source_sha256:str
    rect:tuple[int,int,int,int]
    id:str
    first_frame:int
    start_at:float
    peak_at:float
    end_at:float
    lift_px:float
    scale:float
    shadow_strength:float
    native_fps:int
    event_index:int
    radius_px:float
    drift_x_px:float=0.
    hero_center:tuple[float,float]|None=None

    def amount(self,t):
        if not self.start_at<=t<=self.end_at:return 0.
        up=_eased((t-self.start_at)/max(.001,self.peak_at-self.start_at))
        # Hold a visually readable feature for >=.4s; no temporal surgery.
        return up*(1.-_eased((t-(self.end_at-.60))/.60))

    def source_quad(self):
        x,y,w,h=self.rect
        return np.float32([[x,y],[x+w,y],[x+w,y+h],[x,y+h]])


def validate_matched_frames(source,plate,rect):
    if source is None or plate is None or source.shape!=plate.shape:
        raise ValueError("domPlane source/clean-plate frames do not match")
    H,W=source.shape[:2]
    x,y,w,h=rect
    if x<0 or y<0 or x+w>W or y+h>H:raise ValueError("DOM plane ROI invalid")
    diff=cv2.absdiff(source,plate).max(axis=2)
    outside=np.ones((H,W),bool)
    pad=12
    outside[max(0,y-pad):min(H,y+h+pad),max(0,x-pad):min(W,x+w+pad)]=False
    escaped=float(np.mean(diff[outside]>12))
    content=float(np.mean(diff[y:y+h,x:x+w]>12))
    if escaped>.00008:
        raise ValueError(f"domPlane unverified frame pixels OUTSIDE real element {escaped:.6f}")
    if content<.012:
        raise ValueError(f"domPlane lacks identifiable element pixels {content:.6f}")
    return {"outsideDifferentFraction":escaped,"insideDifferentFraction":content}


def check_multi_pair_video_frames(a,b,multi_rects):
    """Decoded video frame pair: all selected source regions and genuine remainder."""
    if a is None or b is None or a.shape!=b.shape:
        raise ValueError("Unmatched decoded multi-plane source/plate")
    H,W=a.shape[:2]
    outside=np.ones((H,W),dtype=bool)
    for i,(x,y,w,h) in enumerate(multi_rects):
        if x<0 or y<0 or w<40 or h<30 or x+w>W or y+h>H:
            raise ValueError("Invalid native DOM rectangle")
        for ox,oy,ow,oh in multi_rects[:i]:
            overlap=max(0,min(x+w,ox+ow)-max(x,ox))*max(0,min(y+h,oy+oh)-max(y,oy))
            if overlap>0:raise ValueError("DOM component source rectangles overlap")
        outside[max(0,y-12):min(H,y+h+12),
                max(0,x-12):min(W,x+w+12)]=False
    diff=cv2.absdiff(a,b).max(axis=2)
    escaped=float(np.mean(diff[outside]>12))
    if escaped>.00008:
        raise ValueError(f"Unproven pixels outside independently hidden DOM planes: {escaped:.6f}")
    inside=[float(np.mean(diff[y:y+h,x:x+w]>12)) for x,y,w,h in multi_rects]
    if min(inside)<.012:
        raise ValueError("Missing genuine DOM pixels in at least one captured element")
    return {"outsideDifferentFraction":escaped,"insideChangedFraction":inside}


def load_live_dom_plane(config,manifest,source_path,manifest_path,
                        *,source_size,fps,duration,multi_rects=None):
    """Trusted captures describe eligible plates; the model may select IDs only."""
    if config is None:return None
    if not isinstance(config,dict) or set(config)-{
        "id","eventIndex","startAt","peakAt","endAt",
        "liftPx","scale","shadowStrength","driftXPx","heroCenter"}:
        raise ValueError("Unknown domPlane creative parameters")
    if not isinstance(manifest.get("domPlanes"),list):
        raise ValueError("domPlane requires a real paired-browser capture")
    if len(manifest["domPlanes"])>5:
        raise ValueError("Too many manifest DOM plate candidates")
    matches=[p for p in manifest["domPlanes"] if isinstance(p,dict) and
             p.get("id")==config.get("id")]
    if len(matches)!=1 or not isinstance(config.get("id"),str):
        raise ValueError("domPlane ID is not from a unique verified capture")
    record=matches[0]
    ix=config.get("eventIndex")
    if type(ix) is not int or ix<0 or ix>=len(manifest.get("events",[])):
        raise ValueError("domPlane needs a real verified event")
    event=manifest["events"][ix]
    if not isinstance(event.get("evidence"),str) or not event["evidence"].strip():
        raise ValueError("No real event outcome evidence")
    first=record.get("firstPairedFrame")
    if type(first) is not int or first<0 or first>=int(round(duration*fps)):
        raise ValueError("domPlane first paired source frame invalid")
    start=_num(config.get("startAt"),"startAt",0,duration)
    peak=_num(config.get("peakAt"),"peakAt",0,duration)
    end=_num(config.get("endAt"),"endAt",0,duration)
    if not (start>=first/fps-1e-6 and start>=event["t"]+.12 and
            peak-start>=.35-1e-6 and end-peak>=.9-1e-6 and end<=duration+1e-6):
        raise ValueError("DOM plane may rise only after source-proof and must hold/return safely")
    if (abs(start*fps-round(start*fps))>.001 or
        abs(peak*fps-round(peak*fps))>.001 or
        abs(end*fps-round(end*fps))>.001):
        raise ValueError("domPlane effect timestamps must use exact native source frames")
    lift=_num(config.get("liftPx",60),"liftPx",0,160)
    center_value=config.get("heroCenter")
    hero_center=None
    if center_value is not None:
        if not isinstance(center_value,list) or len(center_value)!=2:
            raise ValueError("DOM heroCenter must be normalized [x,y]")
        hero_center=tuple(_num(v,f"heroCenter[{i}]",.14,.86)
                          for i,v in enumerate(center_value))
    scale=_num(config.get("scale",1.06),"scale",1,1.55 if hero_center else 1.18)
    shadow=_num(config.get("shadowStrength",.34),"shadowStrength",0,.6)
    drift=_num(config.get("driftXPx",0),"driftXPx",-120,120)
    rect=_source_rect(record.get("rect"),source_size)
    # Move only an actual DOM component materially belonging to the verified
    # source outcome; not a random decor card the model finds attractive.
    evidence_boxes=[event.get("componentRect"),event.get("resultRect")]
    def coverage_against(real):
        if not isinstance(real,dict):return 0.
        try:
            bx,by,bw,bh=[float(real[k]) for k in ("x","y","width","height")]
        except (KeyError,TypeError,ValueError):return 0.
        x,y,w,h=rect
        shared=max(0,min(x+w,bx+bw)-max(x,bx))*max(0,min(y+h,by+bh)-max(y,by))
        return shared/max(float(w*h),1.)
    if max(coverage_against(box) for box in evidence_boxes)<.6:
        raise ValueError("DOM plane does not belong to the verified real result")
    if record.get("opaqueSurface") is not True:
        raise ValueError("Independent source plane requires truly opaque DOM surface")
    native_radius=_num(record.get("radiusPx"),"radiusPx",0,18)
    captured=record.get("plateFile")
    if not isinstance(captured,str) or not captured.endswith(".mp4") or "/" in captured or "\\" in captured:
        raise ValueError("Plate file must be a local capture-owned filename")
    parent=Path(manifest_path).resolve().parent
    file=(parent/captured).resolve()
    if file.parent!=parent or not file.is_file() or file.is_symlink() or file.stat().st_size>40*1024*1024:
        raise ValueError("Paired plate missing or unsafe location/size")
    if not all(isinstance(record.get(k),str) and len(record[k])==64
               for k in ("sourceSha256","plateSha256")):
        raise ValueError("Unhashed paired plate evidence")
    shasrc=_sha(source_path);shaplate=_sha(file)
    if shasrc!=record["sourceSha256"] or shaplate!=record["plateSha256"]:
        raise ValueError("Source/plate byte hashes differ from real capture receipt")
    src_stream,src_info=_details(source_path)
    plate_stream,plate_info=_details(file)
    if (src_stream["width"],src_stream["height"])!=(plate_stream["width"],plate_stream["height"]):
        raise ValueError("DOM source and plate frame sizes not identical")
    if str(src_stream["avg_frame_rate"])!=str(plate_stream["avg_frame_rate"]):
        raise ValueError("DOM plate frame rate differs from real source")
    if int(src_stream.get("nb_frames",0))!=int(plate_stream.get("nb_frames",0)):
        raise ValueError("DOM plate frame count differs from real source")
    if abs(float(src_info["duration"])-float(plate_info["duration"]))>.0001:
        raise ValueError("DOM plate duration differs from source video")
    if multi_rects is not None:
        if record.get("captureMethod")!="playwright-visible-then-multiple-DOM-elements-hidden-and-restored":
            raise ValueError("No genuine synchronized multi-plane capture provenance")
        if not 2<=len(multi_rects)<=3 or rect not in multi_rects:
            raise ValueError("No matching independent DOM plane geometry in shared capture")
    elif record.get("captureMethod")!="playwright-visible-then-CSS-visibility-hidden-and-restored":
        raise ValueError("DOM plate has no approved dual-capture provenance")

    sc=cv2.VideoCapture(str(source_path));pc=cv2.VideoCapture(str(file))
    sample_indices=sorted(set([first,round((first+end*fps)*.5),
                               min(round(end*fps),int(src_stream["nb_frames"])-1)]))
    seen=[]
    try:
        for frame_index in sample_indices:
            sc.set(cv2.CAP_PROP_POS_FRAMES,frame_index)
            pc.set(cv2.CAP_PROP_POS_FRAMES,frame_index)
            ok,a=sc.read();ok2,b=pc.read()
            if not(ok and ok2):raise ValueError("DOM source/plate cannot decode sampled frame")
            if multi_rects is None:
                seen.append(validate_matched_frames(a,b,rect))
            else:
                seen.append(check_multi_pair_video_frames(a,b,multi_rects))
    finally:
        sc.release();pc.release()
    return LiveDomPlane(file,shaplate,shasrc,rect,record["id"],first,
        start,peak,end,lift,scale,shadow,int(fps),ix,native_radius,drift,hero_center)


def render_live_dom_plane(stage,source_frame,plate_frame,plane:LiveDomPlane,t):
    """Independently lift ORIGINAL DOM pixels over ORIGINAL browser clean plate.

    Caller renders clean page stage first. The isolated card is a real frame
    crop, projected by the same source-world homography, then lifted.
    """
    if plane.amount(t)<=0:
        # Render original full source before/after motion, no silent plate swap.
        from spatial_studio_stage import render_studio_stage
        return render_studio_stage(stage,source_frame,t)
    validate_matched_frames(source_frame,plate_frame,plane.rect)
    from spatial_studio_stage import render_studio_stage
    surface=render_studio_stage(stage,plate_frame,t).astype(np.float32)
    return composite_real_dom_element(stage,surface,source_frame,plane,t)


def projected_real_element_quad(stage,plane:LiveDomPlane,t):
    """Source component homography plus independently authored real-pixel placement."""
    sw,sh=stage.source_size
    ow,oh=stage.output_size
    source_quad=np.float32([[0,0],[sw-1,0],[sw-1,sh-1],[0,sh-1]])
    base_h=cv2.getPerspectiveTransform(source_quad,stage.quad(t))
    current=cv2.perspectiveTransform(plane.source_quad()[None,:,:],base_h)[0]
    a=plane.amount(t)
    if plane.hero_center is not None and a>0:
        departure_h=cv2.getPerspectiveTransform(
            source_quad,stage.quad(plane.start_at))
        departure=cv2.perspectiveTransform(
            plane.source_quad()[None,:,:],departure_h)[0]
        projected=current*(1-a)+departure*a
    else:
        projected=current
    center=projected.mean(axis=0)
    factor=1+(plane.scale-1)*a
    projected=(projected-center)*factor+center
    if plane.hero_center is not None:
        goal=np.array([plane.hero_center[0]*ow,
                       plane.hero_center[1]*oh],np.float32)
        projected+=(goal-center)*a
    projected+=np.array([plane.drift_x_px*a,-plane.lift_px*a],np.float32)
    return projected


def composite_real_dom_element(stage,surface,source_frame,plane:LiveDomPlane,t):
    """Render genuine DOM source pixels over the original clean browser source."""
    surface=np.asarray(surface,dtype=np.float32)
    ow,oh=stage.output_size
    projected=projected_real_element_quad(stage,plane,t)
    a=plane.amount(t)
    x,y,w,h=plane.rect
    crop=source_frame[y:y+h,x:x+w]
    if crop.size==0:raise ValueError("empty genuinely captured DOM source crop")
    source_quad=np.float32([[0,0],[w-1,0],[w-1,h-1],[0,h-1]])
    roi_x=max(0,int(np.floor(projected[:,0].min()-34)))
    roi_y=max(0,int(np.floor(projected[:,1].min()-34)))
    roi_r=min(ow,int(np.ceil(projected[:,0].max()+34)))
    roi_b=min(oh,int(np.ceil(projected[:,1].max()+34)))
    if roi_r<=roi_x or roi_b<=roi_y:raise ValueError("Projected DOM plane outside film")
    if (roi_r-roi_x)<20 or (roi_b-roi_y)<20:
        raise ValueError("Projected DOM plane would be too small to read")
    target=projected-np.array([roi_x,roi_y],np.float32)
    hmat=cv2.getPerspectiveTransform(source_quad,target)
    size=(roi_r-roi_x,roi_b-roi_y)
    rendered=cv2.warpPerspective(crop,hmat,size,flags=cv2.INTER_LINEAR)
    source_mask=np.full((h,w),255,np.uint8)
    radius=int(round(plane.radius_px))
    if radius>1:
        # Rounded DOM surface stencil is taken from the verified real CSS
        # border radius, never invented by compositing. Keep text sharp.
        source_mask[:]=0
        r=min(radius,w//3,h//3)
        cv2.rectangle(source_mask,(r,0),(w-r-1,h-1),255,-1)
        cv2.rectangle(source_mask,(0,r),(w-1,h-r-1),255,-1)
        for cx in (r,w-r-1):
            for cy in (r,h-r-1):
                cv2.circle(source_mask,(cx,cy),r,255,-1,lineType=cv2.LINE_AA)
    coverage=cv2.warpPerspective(source_mask,hmat,size,
                                flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
    alpha=coverage.astype(np.float32)/255
    # Source-derived element gets independent physical-depth shadow; only
    # outside source window pixels are painted. No fake screen contents.
    shadow_mask=np.zeros_like(alpha)
    depth=8+14*a
    q_shadow=np.rint(target+np.array([depth*.65,depth],np.float32)).astype(np.int32)
    cv2.fillConvexPoly(shadow_mask,q_shadow,1,lineType=cv2.LINE_AA)
    shadow_mask=cv2.GaussianBlur(shadow_mask,(0,0),6+10*a)
    shadow=shadow_mask*plane.shadow_strength*a*(1-alpha)
    patch=surface[roi_y:roi_b,roi_x:roi_r]
    patch*= (1-shadow[:,:,None])
    patch[:]=rendered.astype(np.float32)*alpha[:,:,None]+patch*(1-alpha[:,:,None])
    return np.uint8(np.clip(surface,0,255))


class PlaneFrameReader:
    """Frame-index-matched decoder: never seek forward/back by guessed time."""
    def __init__(self,plane:LiveDomPlane):
        self.plane=plane
        self.reader=cv2.VideoCapture(str(plane.plate_file))
        if not self.reader.isOpened():
            raise ValueError("Verified clean plate cannot be decoded")
        self.index=0

    def read(self,expected_frame:int):
        if expected_frame!=self.index:
            self.reader.set(cv2.CAP_PROP_POS_FRAMES,expected_frame)
        ok,img=self.reader.read()
        if not ok:raise ValueError(f"Missing genuine clean plate frame {expected_frame}")
        self.index=expected_frame+1
        return img

    def close(self):
        self.reader.release()
