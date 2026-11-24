"""Source-true Sauce cloud stage for a CUSTOMER-captured interaction.

No generated UI or invented pointer: every frame is the same actual decoded
Chromium source frame. The light physical push begins only after the recorded
click and separately verified visible state change. Clouds stay fixed.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import math
import cv2
import numpy as np

from cloud_shadow_stage import render_cloud_overview
from cloud_window_sky_stage import sky_background,object_mask

_PRESET = "cloud_window_fullglass_v1"


def _number(value, lo=0., hi=75.):
    return type(value) in (int, float) and math.isfinite(value) and lo <= value <= hi


def _rect(rect, w, h):
    if not isinstance(rect, dict):
        return False
    if not all(_number(rect.get(k), 0., max(w, h)) for k in ("x","y","width","height")):
        return False
    return (rect["width"] >= 8 and rect["height"] >= 8
            and rect["x"] + rect["width"] <= w
            and rect["y"] + rect["height"] <= h)


@dataclass(frozen=True)
class VerifiedCloudMoment:
    click: float
    result: float
    complete: float
    bounds: dict

    def amplitude(self, t):
        if t < self.result + .08:
            return 0.
        def s(x):
            x = max(0., min(1., x))
            return x*x*x*(x*(x*6-15)+10)
        rise = s((t - self.result - .08)/1.10)
        fall = s((t - self.complete - .08)/.90)
        return max(0., min(1., rise*(1. - fall)))


def verified_cloud_moment(events, duration, size):
    """Fail closed without a REAL, paired click / observed DOM outcome / hold."""
    if not isinstance(events, list) or not _number(duration, 1.7, 75):
        raise ValueError("Customer cloud stage requires source events and duration")
    w,h=size
    if min(w,h)<360 or w/h < 1.30:
        raise ValueError("Customer cloud stage requires landscape source pixels")
    for i,click in enumerate(events):
        if (not isinstance(click,dict) or click.get("kind")!="click"
            or not isinstance(click.get("semanticGoal"),str)
            or not click["semanticGoal"].strip() or not _number(click.get("t"),0,duration)):
            continue
        result=next((e for e in events[i+1:]
                     if isinstance(e,dict) and e.get("kind")=="state_change"
                     and _number(e.get("t"),click["t"],min(duration,click["t"]+1.8))
                     and isinstance(e.get("evidence"),str) and e["evidence"].strip()
                     and _rect(e.get("resultRect"),w,h)),None)
        if result is None:
            continue
        end=next((e for e in events[i+1:]
                  if isinstance(e,dict) and e.get("kind")=="interaction_complete"
                  and _number(e.get("t"),result["t"]+.3,duration)),None)
        if end is not None and end["t"]>result["t"]+1.20:
            return VerifiedCloudMoment(float(click["t"]),float(result["t"]),
                                       float(end["t"]),result["resultRect"])
    raise ValueError("No independently verified, readable customer interaction")


def verified_detail_matrix(moment, t, size):
    """Source-only crop after the result: no pre-action or fabricated pixels.

    The exact original result bounds determine the framing. Clamp every
    edge so the actual Chromium image fills the source aperture, avoiding
    replicated/black fake UI margins or an off-screen verified result.
    """
    if not isinstance(moment, VerifiedCloudMoment):
        raise ValueError("Real verified outcome required")
    w,h=size
    power=moment.amplitude(t)
    z=1.+.55*power
    r=moment.bounds
    cx=r["x"]+r["width"]*.5
    cy=r["y"]+r["height"]*.5
    x=max(w*(1.-z),min(0.,w*.5-z*cx))
    wanted=max(h*.25,min(h*.75,cy))
    y=max(h*(1.-z),min(0.,wanted-z*cy))
    # Never discard the observed payoff. Source coordinates are unaffected
    # by the decorative sky, acrylic shell or user-facing frame.
    if power>.001 and (r["x"]*z+x < -.01 or
                       (r["x"]+r["width"])*z+x > w+.01 or
                       r["y"]*z+y < -.01 or
                       (r["y"]+r["height"])*z+y > h+.01):
        raise ValueError("Customer detail would clip genuine visible result")
    return np.float32([[z,0.,x],[0.,z,y]])


def verified_detail_source(frame,t,moment):
    """A genuinely sampled same-frame camera crop of only real product UI."""
    if moment.amplitude(t)<1e-6:
        return frame
    h,w=frame.shape[:2]
    M=verified_detail_matrix(moment,t,(w,h))
    return cv2.warpAffine(frame,M,(w,h),flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_CONSTANT)


@lru_cache(maxsize=4)
def _moving_shell_matte(size, output_size):
    # The original physical plate includes a very wide blurred stationary
    # shadow. Translate only the genuine glass/browser and its near contact
    # shadow, never the owner's cobalt halftone sky in the outside corners.
    shell=object_mask(output_size,size)
    pad=max(22,round(output_size[1]*.034))
    kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(pad*2+1,pad*2+1))
    nearby=cv2.dilate(shell,kernel)
    blurred=cv2.GaussianBlur(nearby,(0,0),12).astype(np.float32)/255.
    return np.where(blurred<.03,0.,blurred).astype(np.float32)


def render_customer_cloud(frame, t, moment, *, output_size=(1920,1080)):
    if not isinstance(moment, VerifiedCloudMoment):
        raise ValueError("Cloud stage requires a verified customer moment")
    if (not isinstance(frame,np.ndarray) or frame.dtype!=np.uint8
        or frame.ndim!=3 or frame.shape[2]!=3 or not _number(t,0,75)):
        raise ValueError("Invalid exact Chromium source frame")
    # IMPORTANT: optical clouds stay OUTSIDE the real source pixels. Applying
    # coat_glass_face to a dimmed modal page had made the product unreadable.
    # The fixed premium glass shell is still used; only its decorative
    # transmission over the UI is disabled in the customer production path.
    camera_source=verified_detail_source(frame,t,moment)
    base=render_cloud_overview(camera_source,output_size,stage_preset=_PRESET,
                               coat_source=False)
    weight=moment.amplitude(t)
    # Move a premultiplied PHYSICAL browser/shell over an unchanged sky.
    # Never move a (browser - old_sky) delta: adding it to the *new* sky
    # makes halftone clouds leak through the real source as the camera zooms.
    ow,oh=output_size
    sky=sky_background(output_size)
    zoom=1.+.043*weight
    M=np.float32([[zoom,0.,(1.-zoom)*ow/2.],
                  [0.,zoom,(1.-zoom)*oh/2.]])
    alpha=_moving_shell_matte((frame.shape[1],frame.shape[0]),output_size)
    # The zero-movement frame must use the SAME fixed-sky alpha contract
    # as the zoomed frames; otherwise the entire sky changes on onset.
    if weight<1e-6:
        image=np.rint(np.clip(
            sky.astype(np.float32)*(1.-alpha[:,:,None]) +
            base.astype(np.float32)*alpha[:,:,None],0,255)).astype(np.uint8)
        image[alpha<.005]=sky[alpha<.005]
        return image
    # The opaque Chromium aperture sits INSIDE the alpha=1 physical shell.
    premultiplied=base.astype(np.float32)*alpha[:,:,None]
    shifted=cv2.warpAffine(premultiplied,M,(ow,oh),flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_CONSTANT,borderValue=0)
    shifted_alpha=cv2.warpAffine(alpha,M,(ow,oh),flags=cv2.INTER_LINEAR,
                                borderMode=cv2.BORDER_CONSTANT,borderValue=0)
    image=np.rint(np.clip(sky.astype(np.float32)*(1.-shifted_alpha[:,:,None])
                 +shifted,0,255)).astype(np.uint8)
    # Preserve exact original cobalt pixels in the outer sky when no
    # foreground/browser is present. Contact shadows move with the shell.
    image[shifted_alpha<.005]=sky[shifted_alpha<.005]
    return image
