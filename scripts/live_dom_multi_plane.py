"""Genuine paired-Chromium multiple independently moving DOM layers.

The *single* real browser clean plate must have every selected DOM component
hidden in the exact source frame, and no other DOM content removed. The
compositor restores non-active real UI components to their native positions,
and lets independently moving components float with their original pixels.
"""
from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass
import numpy as np
from live_dom_depth_plane import (
    LiveDomPlane,load_live_dom_plane,check_multi_pair_video_frames,
    composite_real_dom_element,PlaneFrameReader)


@dataclass(frozen=True)
class LiveDomPlaneGroup:
    members:tuple[LiveDomPlane,...]
    plate_file:Path
    source_sha256:str
    plate_sha256:str
    source_rects:tuple[tuple[int,int,int,int],...]
    first_frame:int

    def active(self,t):
        return any(member.amount(t)>0 for member in self.members)

    def reader(self):
        return PlaneFrameReader(self.members[0])


def load_live_dom_planes(configs,manifest,source_path,manifest_path,
                         *,source_size,fps,duration):
    if not isinstance(configs,list) or not 2<=len(configs)<=3:
        raise ValueError("Select exactly two or three independently captured DOM planes")
    captures=manifest.get("domPlanes")
    if not isinstance(captures,list) or len(captures)!=len(configs):
        raise ValueError("Entire genuine source hidden-plate group must be selected")
    if not all(isinstance(c,dict) for c in configs):
        raise ValueError("Invalid multi-plane creative JSON")
    ids=[c.get("id") for c in configs]
    record_ids=[c.get("id") for c in captures]
    if len(set(ids))!=len(ids) or set(ids)!=set(record_ids):
        raise ValueError("Only ALL genuine captured source-plane IDs may be animated")
    if any(record.get("captureMethod")!=
           "playwright-visible-then-multiple-DOM-elements-hidden-and-restored"
           for record in captures):
        raise ValueError("No valid simultaneous DOM multi-capture provenance")
    if len({c.get("plateFile") for c in captures})!=1 or        len({c.get("plateSha256") for c in captures})!=1 or        len({c.get("sourceSha256") for c in captures})!=1 or        len({c.get("firstPairedFrame") for c in captures})!=1:
        raise ValueError("DOM source planes were not captured with one synchronized clean plate")
    from live_dom_depth_plane import _source_rect
    native_rects=tuple(_source_rect(c["rect"],source_size) for c in captures)
    # Verify source rectangles are disjoint independent UI elements.
    for i,(x,y,w,h) in enumerate(native_rects):
        for xx,yy,ww,hh in native_rects[:i]:
            if max(0,min(x+w,xx+ww)-max(x,xx))*max(
               0,min(y+h,yy+hh)-max(y,yy))>0:
                raise ValueError("Overlapping source DOM components cannot be independently projected")
    members=tuple(load_live_dom_plane(
        config,manifest,source_path,manifest_path,
        source_size=source_size,fps=fps,duration=duration,
        multi_rects=native_rects) for config in configs)
    if len({m.plate_file for m in members})!=1:
        raise ValueError("Source-dom-plane group plate changed unexpectedly")
    # Camera avoids projected layer clipping even if a model asks for a
    # dramatic unusable lift/scale. These are limits on layer movement,
    # *not* on genuine source pixels.
    return LiveDomPlaneGroup(
        members,members[0].plate_file,members[0].source_sha256,
        members[0].plate_sha256,native_rects,members[0].first_frame)


def verify_source_relative_material(group:LiveDomPlaneGroup,stage,source_path):
    """Reject pale-on-pale source UI only; never mandate an aesthetic palette.

    Professional footage depends on actual subject-to-stage separation.
    Source luminance is sampled from a *verified native frame* and each real
    DOM component, not inferred from marketing text, site brand or model claims.
    Dark-on-dark scenes can retain controlled shadows and remain available.
    """
    import cv2
    reader=cv2.VideoCapture(str(source_path))
    try:
        reader.set(cv2.CAP_PROP_POS_FRAMES,group.first_frame)
        ok,source=reader.read()
    finally:reader.release()
    if not ok:raise ValueError("Cannot inspect real DOM component luminance")
    luminances=[]
    for x,y,w,h in group.source_rects:
        crop=source[y:y+h,x:x+w]
        if crop.size==0:raise ValueError("Invalid genuine layer source region")
        small=cv2.resize(crop,(80,50),interpolation=cv2.INTER_AREA)
        rgb=np.median(small.astype(np.float32),axis=(0,1))[::-1]
        lum=float((.2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2]))
        luminances.append(lum)
    backdrop=np.array(stage.color,dtype=np.float32)
    backdrop_lum=float(.2126*backdrop[0]+.7152*backdrop[1]+.0722*backdrop[2])
    if (backdrop_lum>185 and min(luminances)>190 and
          all(abs(backdrop_lum-lum)<54 for lum in luminances)):
        raise ValueError(
            f"Source-relative studio separation fails: actual UI elements luminance "
            f"{[round(v) for v in luminances]}, backdrop {backdrop_lum:.0f}. "
            "This real product is already bright; choose a substantially "
            "contrasting stage, not a washed-out pale browser on a pale field. "
            "The engine does not choose the color for you.")
    return {"sourcePanelLuminances":[round(x,2) for x in luminances],
            "studioBackdropLuminance":round(backdrop_lum,2),
            "sourceRelativeSeparationVerified":True}


def verify_group_projected_visibility(stage,group:LiveDomPlaneGroup):
    """Fail closed when real foreground UI is cut off in its hero shot.

    The model owns what to foreground. We gate only actual projected
    source geometry, frame-by-frame; never replace creative decisions.
    """
    import cv2
    from live_dom_depth_plane import projected_real_element_quad
    fps=group.members[0].native_fps
    ow,oh=stage.output_size
    boundary=np.float32([[0,0],[ow,0],[ow,oh],[0,oh]])
    checked=0
    worst=1.
    for frame in range(round(stage.duration*fps)):
        t=frame/fps
        raised=[]
        for plane in group.members:
            amount=plane.amount(t)
            if amount<.50:continue
            polygon=projected_real_element_quad(stage,plane,t)
            area=abs(cv2.contourArea(polygon))
            if area<200:raise ValueError("Tiny source UI foreground subject")
            inside,_=cv2.intersectConvexConvex(polygon,boundary)
            fraction=float(inside)/area
            worst=min(worst,fraction)
            if fraction<.965:
                raise ValueError(
                    f"Source-verified UI hero {plane.id} clipped at source frame "
                    f"{frame}: {fraction:.3f} visible. Adjust creative "
                    "camera or heroCenter; do not crop genuine source text.")
            checked+=1
            if amount>.78:raised.append((plane,polygon,area))
        if len(raised)>1:
            for i,(_,pa,area) in enumerate(raised):
                for _,pb,other_area in raised[:i]:
                    intersection,_=cv2.intersectConvexConvex(pa,pb)
                    overlap=float(intersection)/min(area,other_area)
                    if overlap>.34:
                        raise ValueError(
                            f"Independently animated real UI cards obscure "
                            f"each other at source frame {frame}: {overlap:.3f}")
    return {"realHeroFramesChecked":checked,
            "minimumRealUIHeroVisibility":round(worst,5),
            "allProjectedUIFromSource":True}


def render_live_dom_planes(stage,source_frame,clean_frame,group:LiveDomPlaneGroup,t):
    from spatial_studio_stage import render_studio_stage
    if not group.active(t):
        return render_studio_stage(stage,source_frame,t)
    check_multi_pair_video_frames(source_frame,clean_frame,group.source_rects)
    result=render_studio_stage(stage,clean_frame,t).astype(np.float32)
    # Draw genuine inactive elements in native position, then the actively
    # lifted ones. No hidden card disappears just because its peer animates.
    sorted_layers=sorted(group.members,key=lambda m:(m.amount(t)>0,m.id))
    for member in sorted_layers:
        result=composite_real_dom_element(stage,result,source_frame,member,t).astype(np.float32)
    return np.uint8(np.clip(result,0,255))
