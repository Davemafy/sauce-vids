"""Deterministic 60fps source-true film compositor for Sauce Scripted v2.

The film's browser window never wanders on the stage. Camera tracks operate
only in screenshot CSS coordinates, with no automatic tilt or perspective.
Every displayed website pixel comes from a SHA-verified DPR2 screenshot,
except explicitly requested presentation-only concealment/redaction.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import hashlib
import json
import math
import subprocess

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from cinematic_stage import _stage_base, WINDOW_X, WINDOW_Y, WINDOW_WIDTH, WINDOW_HEIGHT
from scripted_v2_schema import Shot, FPS

CSS_WIDTH, CSS_HEIGHT = 1280, 720
DPR = 2
ZOOM_EPS = 1e-7
BG_BLUR = 6.0  # Matches the approved Phase 2 inactive-background DOF.
CONCEAL_FEATHER = 9.0  # Softens the presentation-only panel removal edge.
SITE_RADIUS = 16  # Preserve the approved external window corner radius.


def ease(u: float) -> float:
    """Quintic smoothstep has zero velocity and acceleration at both ends."""
    t = max(0., min(1., u))
    return 6*t**5 - 15*t**4 + 10*t**3


def _font(size: int):
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _css_bounds(rect):
    """Convert source CSS coordinates to the verified DPR2 pixel grid."""
    return tuple(int(round(n * DPR)) for n in (
        rect["x"], rect["y"], rect["x"] + rect["width"],
        rect["y"] + rect["height"]
    ))


def redact(image: np.ndarray, rect: dict) -> np.ndarray:
    """Intentionally destructive blur for private fields, never reversible."""
    out = image.copy()
    x0, y0, x1, y1 = _css_bounds(rect)
    # 6 CSS px extra on all sides covers glyph antialiasing and caret pixels.
    x0 = max(0, x0-12); y0 = max(0, y0-12)
    x1 = min(out.shape[1], x1+12); y1 = min(out.shape[0], y1+12)
    if x1 > x0 and y1 > y0:
        region = out[y0:y1, x0:x1]
        blurred = cv2.GaussianBlur(region, (0, 0), sigmaX=32, sigmaY=32)
        # Blur plus desaturation and dark tint suppresses recoverable glyphs.
        grey = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
        out[y0:y1, x0:x1] = np.stack((grey,grey,grey), axis=2) * .46
    return out


def conceal_terminal(image: np.ndarray, state_index:int) -> np.ndarray:
    """Hide the observed right-hand terminal panel in an existing modal state.

    Only the original modal pixels are restored afterward; we never invent
    terminal contents. The mask is presentation-only, not a synthetic event.
    Brimble's trace explicitly observes the 560x376 terminal at (640, 172).
    """
    h, w = image.shape[:2]
    before = image.copy()
    # Expand beyond the source terminal's real soft shadow (CSS px).
    x0, y0, x1, y1 = [int(v * DPR) for v in (619,155,1220,569)]
    fill = np.median(image[480:620,70:260], axis=(0,1)).astype(np.float32)
    mask = np.zeros((h,w),np.float32)
    cv2.rectangle(mask,(x0,y0),(min(w-1,x1),min(h-1,y1)),1.,-1)
    mask = cv2.GaussianBlur(mask,(0,0),CONCEAL_FEATHER)[:,:,None]
    concealed = np.uint8(np.clip(
        image.astype(np.float32)*(1-mask) + fill[None,None,:]*mask,0,255
    ))
    # Before the dialog opens, simply conceal the observed terminal. Never
    # draw an invented modal or fake UI to fill the removed area.
    if state_index<2:
        return concealed
    # Keep the full genuine Radix dialog pixels, including the real code.
    modal_top,modal_bottom=(120,602) if state_index>=4 else (180,542)
    bx0, by0, bx1, by1 = [int(v * DPR) for v in
                            (440,modal_top,840,modal_bottom)]
    modal = np.zeros((h,w),np.uint8)
    cv2.rectangle(modal,(bx0+24,by0),(bx1-24,by1),255,-1)
    cv2.rectangle(modal,(bx0,by0+24),(bx1,by1-24),255,-1)
    for cx,cy in ((bx0+24,by0+24),(bx1-24,by0+24),
                  (bx0+24,by1-24),(bx1-24,by1-24)):
        cv2.circle(modal,(cx,cy),24,255,-1,cv2.LINE_AA)
    modal = cv2.GaussianBlur(modal,(0,0),1.0).astype(np.float32)[:,:,None]/255.
    return np.uint8(np.clip(
        before.astype(np.float32)*modal +
        concealed.astype(np.float32)*(1-modal),0,255
    ))


def _camera_for(shot: Shot):
    b=shot.target
    x=b["x"]+b["width"]/2
    y=b["y"]+b["height"]/2
    # Clamp to real captured page edges; never reveal blank invented content.
    half_x=CSS_WIDTH/(2*shot.zoom)
    half_y=CSS_HEIGHT/(2*shot.zoom)
    return (
        min(CSS_WIDTH-half_x,max(half_x,x)),
        min(CSS_HEIGHT-half_y,max(half_y,y)),
        shot.zoom,
    )


class ScriptedV2Compositor:
    def __init__(self, session_dir: Path, session: dict, resolution=(1920,1080)):
        if resolution not in ((1920,1080),(2560,1440)):
            raise ValueError("Only native 1080p60 and DPR2-backed 1440p60 supported")
        self.width,self.height=resolution
        self.scale=self.width/1920.
        self.x=int(round(WINDOW_X*self.scale))
        self.y=int(round(WINDOW_Y*self.scale))
        self.w=int(round(WINDOW_WIDTH*self.scale))
        self.h=int(round(WINDOW_HEIGHT*self.scale))
        base,alpha,_ambient=_stage_base()
        self.base=cv2.resize(base,resolution,interpolation=cv2.INTER_LANCZOS4) if self.scale!=1 else base
        self.alpha=cv2.resize(alpha[:,:,0],(self.w,self.h),
                              interpolation=cv2.INTER_LINEAR)[:,:,None]
        self.states={}
        self.session_dir=session_dir
        self.session=session
        self.last_key=None
        self.last_frame=None
        self._safe_mask=np.zeros((self.h,self.w),np.uint8)
        # Full vertical centre strip reaches the top/bottom edges; without it
        # dark bars appear between otherwise bright rounded corner circles.
        cv2.rectangle(self._safe_mask,(SITE_RADIUS,0),
                      (self.w-SITE_RADIUS-1,self.h-1),255,-1)
        cv2.rectangle(self._safe_mask,(0,SITE_RADIUS),
                      (self.w-1,self.h-SITE_RADIUS-1),255,-1)
        for cx,cy in ((SITE_RADIUS,SITE_RADIUS),(self.w-SITE_RADIUS-1,SITE_RADIUS),
                      (SITE_RADIUS,self.h-SITE_RADIUS-1),
                      (self.w-SITE_RADIUS-1,self.h-SITE_RADIUS-1)):
            cv2.circle(self._safe_mask,(cx,cy),SITE_RADIUS,255,-1,cv2.LINE_AA)
        self._safe_mask = (self._safe_mask.astype(np.float32)/255.)[:,:,None]

    def state(self, shot:Shot):
        key=(shot.state,shot.hide_terminal,tuple(
            tuple(region.values()) for region in shot.blur_regions))
        if key not in self.states:
            record=self.session["states"][shot.state]
            source=self.session_dir/"states"/record["file"]
            raw=source.read_bytes()
            if hashlib.sha256(raw).hexdigest()!=record["sha256"]:
                raise ValueError("Captured screenshot changed after verification")
            image=cv2.imdecode(np.frombuffer(raw,dtype=np.uint8),cv2.IMREAD_COLOR)
            if image is None or image.shape!=(1440,2560,3):
                raise ValueError("Expected real 2560x1440 captured pixels")
            if shot.hide_terminal:
                image=conceal_terminal(image,shot.state)
            for rect in shot.blur_regions:
                image=redact(image,rect)
            if shot.state>=2:
                # The real modal stays sharp while only the inactive UI blurs.
                image=self._focus_modal(image,shot.state)
            self.states[key]=image
        return self.states[key]

    def _focus_modal(self,image,state_index:int):
        # A 6px source-plane blur is equivalent to 6px at output 1080p only
        # at approximately unity zoom; keep the modal source pixels untouched.
        neutral=cv2.GaussianBlur(image,(0,0),BG_BLUR*DPR)
        background=(neutral.astype(np.float32)*.89).astype(np.uint8)
        modal=np.zeros(image.shape[:2],np.uint8)
        top,bottom=(120,602) if state_index>=4 else (180,542)
        x0,y0,x1,y1=[int(n*DPR) for n in (440,top,840,bottom)]
        cv2.rectangle(modal,(x0+24,y0),(x1-24,y1),255,-1)
        cv2.rectangle(modal,(x0,y0+24),(x1,y1-24),255,-1)
        for cx,cy in ((x0+24,y0+24),(x1-24,y0+24),
                      (x0+24,y1-24),(x1-24,y1-24)):
            cv2.circle(modal,(cx,cy),24,255,-1,cv2.LINE_AA)
        coverage=cv2.GaussianBlur(modal,(0,0),1.0)[:,:,None].astype(np.float32)/255.
        return np.uint8(np.clip(
            background.astype(np.float32)*(1-coverage) +
            image.astype(np.float32)*coverage,0,255
        ))

    def draw(self,shot:Shot,camera:tuple[float,float,float]):
        key=(shot.index,shot.state,tuple(round(v,6) for v in camera))
        if key==self.last_key:return self.last_frame
        src=self.state(shot)
        cx,cy,zoom=camera
        site_scale=(self.w/CSS_WIDTH)*zoom
        m=np.float32([[site_scale/DPR,0,self.w/2-cx*site_scale],
                      [0,site_scale/DPR,self.h/2-cy*site_scale]])
        site=cv2.warpAffine(src,m,(self.w,self.h),
                            flags=cv2.INTER_LANCZOS4,
                            borderMode=cv2.BORDER_REPLICATE)
        out=self.base.copy()
        block=out[self.y:self.y+self.h,self.x:self.x+self.w]
        a=self.alpha*self._safe_mask
        block[:]=np.uint8(np.clip(
            block.astype(np.float32)*(1-a)+site.astype(np.float32)*a,0,255
        ))
        if shot.callout or shot.caption or shot.action in ("approach","click"):
            self._overlays(out,shot,camera)
        self.last_key=key
        self.last_frame=out
        return out

    def _overlays(self,frame,shot,camera):
        image=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)).convert("RGBA")
        draw=ImageDraw.Draw(image,"RGBA")
        k=self.scale
        cx,cy,zoom=camera
        target=shot.target
        tx=(target["x"]+target["width"]/2-cx)*self.w/CSS_WIDTH*zoom+self.x+self.w/2
        ty=(target["y"]+target["height"]/2-cy)*self.h/CSS_HEIGHT*zoom+self.y+self.h/2
        if shot.callout:
            font=_font(round(23*k))
            text=shot.callout
            width=int(draw.textlength(text,font=font)+45*k)
            height=int(48*k)
            px=int(np.clip(tx-width/2,self.x+12*k,self.x+self.w-width-12*k))
            py=int(np.clip(ty-115*k,self.y+12*k,self.y+self.h-height-12*k))
            # A single rounded border. No decorative arc or highlight line.
            draw.rounded_rectangle((px,py,px+width,py+height),radius=16*k,
                fill=(15,20,31,239),outline=(173,191,213,130),width=max(1,round(k)))
            draw.text((px+22*k,py+11*k),text,font=font,fill=(246,249,252,255))
        if shot.action in ("approach","click"):
            # One small film pointer, on the recorded action's real CSS target.
            px=int(tx);py=int(ty)
            draw.polygon([(px,py),(px,py+24*k),(px+6*k,py+18*k),
                          (px+13*k,py+29*k),(px+18*k,py+26*k),
                          (px+10*k,py+15*k),(px+22*k,py+13*k)],
                         fill=(20,22,27,255))
        if shot.caption:
            font=_font(round(25*k))
            text=shot.caption
            text_w=draw.textlength(text,font=font)
            draw.text(((self.width-text_w)/2,self.height-65*k),
                      text,font=font,fill=(235,238,245,242))
        frame[:]=cv2.cvtColor(np.asarray(image.convert("RGB")),cv2.COLOR_RGB2BGR)


def iter_story_frames(compositor:ScriptedV2Compositor,shots:list[Shot]):
    prev=_camera_for(shots[0])
    absolute=0
    for shot in shots:
        nxt=_camera_for(shot)
        for i in range(shot.transition_frames):
            # Easing requires a known start and end; the following hold
            # guarantees the camera has fully settled before another move.
            t=(i+1)/shot.transition_frames
            k=ease(t)
            cam=tuple(a+(b-a)*k for a,b in zip(prev,nxt))
            yield absolute,compositor.draw(shot,cam)
            absolute+=1
        for _ in range(shot.hold_frames):
            yield absolute,compositor.draw(shot,nxt)
            absolute+=1
        prev=nxt
