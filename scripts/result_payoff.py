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
# 8 frames anticipation (132ms), 36 dolly frames (600ms), 42 result-reading
# frames (700ms), and a 12-frame ease-out (200ms) at 60fps.
ANTICIPATION_FRAMES=8
DOLLY_FRAMES=36
READ_FRAMES=42
FADE_FRAMES=12
CUT_SAFE_FRAME_COUNT=ANTICIPATION_FRAMES+DOLLY_FRAMES+READ_FRAMES+FADE_FRAMES

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
    # Result is the center of attention, but 35% dialog context remains
    # so the Codex label and origin are still legible in the final shot.
    focus_x=.65*tx+.35*(mx+mw/2)
    focus_y=.65*ty+.35*(my+mh/2)
    zoom=min(1.82,max(start_scale*1.34,start_scale+.23))
    return {'startScale':start_scale,'endScale':round(zoom,6),
            'startFocusX':sx,'startFocusY':sy,
            'endFocusX':round(focus_x,5),'endFocusY':round(focus_y,5),
            'sourceKind':anchor['kind'],
            'anticipationFrames':ANTICIPATION_FRAMES,
            'dollyFrames':DOLLY_FRAMES,
            'readFrames':READ_FRAMES,'fadeFrames':FADE_FRAMES,
            'totalFrames':CUT_SAFE_FRAME_COUNT}


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
    for _ in range(READ_FRAMES):
        encoder.stdin.write(final.tobytes())
    source=final.astype(np.float32)
    # Fade only after a sharp, settled shot. A 200ms ease prevents a dead
    # half-second black tail while landing without a hard edge.
    dark=np.array([15.,10.,9.],dtype=np.float32)[None,None,:]
    for k in range(FADE_FRAMES):
        u=ease((k+1)/FADE_FRAMES)
        encoder.stdin.write(np.uint8(np.rint(np.clip(
            source*(1-u)+dark*u,0,255))).tobytes())
    return {'holdFrames':ANTICIPATION_FRAMES+READ_FRAMES,
            'cameraMoveFrames':DOLLY_FRAMES,'fadeFrames':FADE_FRAMES,
            'totalFrames':CUT_SAFE_FRAME_COUNT,
            'mode':'source-result-dolly',
            'targetKind':plan['sourceKind'],
            'endScale':plan['endScale'],
            'endFocusX':plan['endFocusX'],
            'endFocusY':plan['endFocusY']}
