"""Source-backed editorial payoff after a verified product result.

No synthetic click, toast or command is generated. The post-roll camera
re-renders the same verified browser pixels at higher source resolution
using Sauce's existing H0/H60 compositor. The camera moves to the actual
DOM result rectangle, then settles for a short reading hold.
"""
from __future__ import annotations

import math
from typing import Callable
import cv2
import numpy as np

# This is a bounded, opt-in film shot, not a fixed 1.6-second freeze:
# 8 frames anticipation (132ms), 36 dolly frames (600ms), at least
# 66 result-reading frames (1100ms), and a 12-frame ease-out (200ms).
# A verified multi-line code result gets more reading time than a one-line
# confirmation. This changes the edit, not the underlying source pixels.
ANTICIPATION_FRAMES=8
DOLLY_FRAMES=36
READ_FRAMES=66
FADE_FRAMES=12
CUT_SAFE_FRAME_COUNT=ANTICIPATION_FRAMES+DOLLY_FRAMES+READ_FRAMES+FADE_FRAMES
CODE_READ_FRAMES=108     # 1.8 s for source-true commands or code, not a one-second glance
OUTPUT_READ_FRAMES=84    # 1.4 s for verified compact output
DETAIL_CONTEXT_FRAMES=12 # let the complete verified dialog register first
DETAIL_DOLLY_FRAMES=24   # then move to the actual verified result, not a new card

# Inspect only geometry; raw commands, visible text, secrets and DOM source
# are not exported to editorial metadata.
FOCUS_ANCHOR_JS=r"""() => {
  const dialog=[...document.querySelectorAll(
    '[role="dialog"],[aria-modal="true"]')].find(e=>{
      const s=getComputedStyle(e),r=e.getBoundingClientRect();
      return r.width>100&&r.height>100&&s.visibility!=="hidden"&&s.display!=="none";
  });
  if(!dialog)return null;
  const candidates=[...dialog.querySelectorAll(
    'pre,output,[role="code"],[data-result],[data-output]')];
  const visible=e=>{
    if(e.closest('[data-private],[data-sensitive],[data-secret],'+
                 'input,textarea,[contenteditable="true"]'))return false;
    const s=getComputedStyle(e),r=e.getBoundingClientRect();
    return r.width>=90&&r.height>=16&&r.height<=220&&
      s.visibility!=="hidden"&&s.display!=="none";
  };
  const el=candidates.find(visible);
  if(!el)return null;
  const box=e=>{const r=e.getBoundingClientRect();
    return {x:r.x,y:r.y,width:r.width,height:r.height};};
  return {target:box(el),dialog:box(dialog),kind:el.tagName.toLowerCase()};
}"""


def _bounds(box):
    if not isinstance(box,dict):raise ValueError("Missing verified result bounds")
    vals=tuple(box.get(k) for k in ('x','y','width','height'))
    if any(type(v) not in (float,int) or not math.isfinite(v) for v in vals):
        raise ValueError("Nonfinite result geometry")
    if vals[2]<16 or vals[3]<12 or vals[2]>1200 or vals[3]>800:
        raise ValueError("Result geometry outside viewport bounds")
    return vals


def create_payoff_plan(evidence,anchor,initial_pose):
    """Choose a real command/result rectangle and one restrained 3D dolly."""
    if not isinstance(evidence,dict) or evidence.get('evidence') not in (
        'visible-result-change','container-expansion'):
        return None
    if not isinstance(anchor,dict) or anchor.get('kind') not in (
        'pre','output','code','div','section','p'):
        return None
    x,y,w,h=_bounds(anchor.get('target'))
    mx,my,mw,mh=_bounds(anchor.get('dialog'))
    if not(mx-2<=x<=mx+mw-w+2 and my-2<=y<=my+mh-h+2):
        return None
    if not isinstance(initial_pose,dict):
        return None
    start_scale=float(initial_pose.get('scale',0))
    sx=float(initial_pose.get('focusX',float('nan')))
    sy=float(initial_pose.get('focusY',float('nan')))
    if not all(map(math.isfinite,(start_scale,sx,sy))) or start_scale<=0:
        return None
    tx=x+w/2
    ty=y+h/2
    # Frame the *verified* result with the genuine dialog header. A target
    # centered at the bottom of a tall modal loses its source context at
    # high zoom. Establish the full dialog in the preceding action shot,
    # then fill the available safe height with header-to-result pixels.
    # We may crop an unrelated footer, but never crop the observed result.
    focus_x=.65*tx+.35*(mx+mw/2)
    anchor_top=my
    anchor_bottom=y+h
    safe_height_px=832.-2*32.
    elevated_factor=(1480./1280.)*(1200./(1200.-60.))
    safe_zoom=safe_height_px/((anchor_bottom-anchor_top)*elevated_factor)
    zoom=min(1.82,max(start_scale*1.34,start_scale+.23),safe_zoom)
    # A low-resolution or extremely tall source may already exceed the safe
    # crop at the starting pose. Don't zoom out *past* the real source pose
    # or invent a wider dialog; settle at the existing scale instead.
    zoom=max(start_scale,zoom)
    focus_y=(anchor_top+anchor_bottom)/2
    # Refs.video's published product-demo timing illustrates picture-led
    # action -> outcome -> reading, not 60 fps constant motion. Select a
    # bounded hold from the verified result element KIND, never from private
    # text or a guessed marketing script; compact non-code results keep the
    # historical 66-frame default.
    read_frames=(CODE_READ_FRAMES if anchor['kind'] in ('pre','code') else
                 OUTPUT_READ_FRAMES if anchor['kind']=='output' else READ_FRAMES)
    # Large source-true result details (code/commands) need a second shot:
    # establish the whole dialog, then reframe the existing pixels around
    # the output text. Never create a duplicate pane or retype the command.
    # The measured Loom reference similarly lets a real UI control become
    # the close composition. This is a technique transfer, not a shot copy.
    detail_scale=zoom
    detail_x,detail_y=focus_x,focus_y
    detail_frames=0
    context_frames=0
    if anchor['kind'] in ('pre','code'):
        factor=(1480./1280.)*(1200./(1200.-60.))
        detail_safe=min(2.90,1536./(w*factor),774./(h*factor))
        if detail_safe>=zoom+.24:
            detail_scale=detail_safe
            detail_x,detail_y=tx,ty
            detail_frames=DETAIL_DOLLY_FRAMES
            context_frames=DETAIL_CONTEXT_FRAMES
    total_frames=(ANTICIPATION_FRAMES+DOLLY_FRAMES+context_frames+
                  detail_frames+read_frames+FADE_FRAMES)
    return {'startScale':start_scale,'endScale':round(zoom,6),
            'startFocusX':sx,'startFocusY':sy,
            'endFocusX':round(focus_x,5),'endFocusY':round(focus_y,5),
            'sourceKind':anchor['kind'],
            'detailScale':round(detail_scale,6),
            'detailFocusX':round(detail_x,5),
            'detailFocusY':round(detail_y,5),
            'detailFrames':detail_frames,
            'contextFrames':context_frames,
            'anticipationFrames':ANTICIPATION_FRAMES,
            'dollyFrames':DOLLY_FRAMES,
            'readFrames':read_frames,'fadeFrames':FADE_FRAMES,
            'totalFrames':total_frames}


def ease(u:float)->float:
    u=max(0.,min(1.,u))
    return u*u*u*(u*(u*6-15)+10)


def pose_at(plan,frame):
    """Frame-locked quintic dolly, zero acceleration at both endpoints."""
    u=0. if frame<ANTICIPATION_FRAMES else (
        (frame-ANTICIPATION_FRAMES+1)/DOLLY_FRAMES)
    blend=ease(u)
    return (
        plan['startScale']+(plan['endScale']-plan['startScale'])*blend,
        plan['startFocusX']+(plan['endFocusX']-plan['startFocusX'])*blend,
        plan['startFocusY']+(plan['endFocusY']-plan['startFocusY'])*blend,
    )


def append_payoff(encoder,last_frame:np.ndarray,plan:dict,
                  render_pose:Callable[[float,float,float,int],np.ndarray],
                  fps:int=60)->dict:
    if fps!=60 or last_frame is None or last_frame.dtype!=np.uint8:
        raise ValueError("Payoff needs a real 60fps uint8 final render")
    if last_frame.shape!=(1080,1920,3):
        raise ValueError("Payoff requires native 1080p60 BGR frames")
    read_frames=plan.get('readFrames',READ_FRAMES)
    if type(read_frames) is not int or read_frames not in (
        READ_FRAMES,OUTPUT_READ_FRAMES,CODE_READ_FRAMES):
        raise ValueError("Result read hold must be a validated editorial duration")
    detail_frames=plan.get('detailFrames',0)
    context_frames=plan.get('contextFrames',0)
    if (detail_frames,context_frames) not in (
        (0,0),(DETAIL_DOLLY_FRAMES,DETAIL_CONTEXT_FRAMES)):
        raise ValueError("Invalid detail-shot structure")
    total_frames=(ANTICIPATION_FRAMES+DOLLY_FRAMES+context_frames+
                  detail_frames+read_frames+FADE_FRAMES)
    if plan.get('totalFrames')!=total_frames:
        raise ValueError("Result shot frame budget is inconsistent")
    if detail_frames:
        values=(plan.get('detailScale'),plan.get('detailFocusX'),plan.get('detailFocusY'),
                plan.get('endScale'),plan.get('endFocusX'),plan.get('endFocusY'))
        if any(type(x) not in (float,int) or not math.isfinite(x) for x in values):
            raise ValueError("Invalid detail camera geometry")
        if not plan['endScale']+.24<=plan['detailScale']<=2.9:
            raise ValueError("Detail closeup must have a bounded, distinct scale")
    last=last_frame
    # No fake cursor travel on the first frame of the outro; the original
    # final frame remains untouched, then the actual 3D reframe begins.
    for i in range(ANTICIPATION_FRAMES):
        encoder.stdin.write(last.tobytes())
    final=None
    for i in range(DOLLY_FRAMES):
        s,x,y=pose_at(plan,ANTICIPATION_FRAMES+i)
        frame=render_pose(s,x,y,ANTICIPATION_FRAMES+i)
        if frame.shape!=last.shape or frame.dtype!=np.uint8:
            raise ValueError("Camera renderer returned wrong frame shape")
        encoder.stdin.write(frame.tobytes())
        final=frame
    if final is None:raise RuntimeError("No source-backed payoff shot")
    for _ in range(context_frames):
        encoder.stdin.write(final.tobytes())
    for i in range(detail_frames):
        u=ease((i+1)/detail_frames)
        z=plan['endScale']+(plan['detailScale']-plan['endScale'])*u
        x=plan['endFocusX']+(plan['detailFocusX']-plan['endFocusX'])*u
        y=plan['endFocusY']+(plan['detailFocusY']-plan['endFocusY'])*u
        frame=render_pose(z,x,y,ANTICIPATION_FRAMES+DOLLY_FRAMES+context_frames+i)
        if frame.shape!=last.shape or frame.dtype!=np.uint8:
            raise ValueError("Detail camera renderer returned wrong frame shape")
        encoder.stdin.write(frame.tobytes())
        final=frame
    for _ in range(read_frames):
        encoder.stdin.write(final.tobytes())
    source=final.astype(np.float32)
    # Fade only after a sharp, settled shot. A 200ms ease prevents a dead
    # half-second black tail while landing without a hard edge.
    dark=np.array([15.,10.,9.],dtype=np.float32)[None,None,:]
    for k in range(FADE_FRAMES):
        u=ease((k+1)/FADE_FRAMES)
        encoder.stdin.write(np.uint8(np.rint(np.clip(
            source*(1-u)+dark*u,0,255))).tobytes())
    return {'holdFrames':ANTICIPATION_FRAMES+context_frames+read_frames,
            'cameraMoveFrames':DOLLY_FRAMES+detail_frames,
            'detailFrames':detail_frames,'fadeFrames':FADE_FRAMES,
            'totalFrames':total_frames,
            'mode':'source-result-dolly',
            'targetKind':plan['sourceKind'],
            'endScale':plan['detailScale'] if detail_frames else plan['endScale'],
            'endFocusX':plan['detailFocusX'] if detail_frames else plan['endFocusX'],
            'endFocusY':plan['detailFocusY'] if detail_frames else plan['endFocusY']}
