"""Source-verified, same-Chromium-clock visible/hidden frame capture.

Use only on an existing authorized Playwright page; no hidden UI construction.
The hidden plate comes from the very same DOM state, never content-aware fill.
All capture-local CSS modifications are reverted even on failed screenshot.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
import math
import cv2
import numpy as np


@dataclass(frozen=True)
class Pair:
    visible:bytes
    clean:bytes
    rect:tuple[int,int,int,int]
    dpr:float
    changed_fraction:float
    outside_fraction:float
    visible_sha256:str
    clean_sha256:str
    opaque_surface:bool
    radius_px:float


def _frame(raw:bytes):
    image=cv2.imdecode(np.frombuffer(raw,dtype=np.uint8),cv2.IMREAD_COLOR)
    if image is None or image.ndim!=3:
        raise ValueError("Chromium screenshot decode failed")
    return image


def check_pair(visible:bytes,clean:bytes,rect,*,max_outside_fraction=.00008,
               min_inside_fraction=.012):
    """Pixel check against exact DOM geometry, no OCR, no guessed card shape."""
    a=_frame(visible);b=_frame(clean)
    if a.shape!=b.shape:
        raise ValueError("Paired browser screenshots have mismatched source dimensions")
    H,W=a.shape[:2]
    if (not isinstance(rect,(tuple,list)) or len(rect)!=4 or
        not all(type(x) is int for x in rect)):
        raise ValueError("Source-pixel DOM rectangle required")
    x,y,w,h=rect
    if x<0 or y<0 or w<16 or h<16 or x+w>W or y+h>H:
        raise ValueError("Live DOM plane is outside the real source")
    # Allow <=12px genuinely rendered native browser shadow around rect;
    # everything else MUST be unchanged between same-state screenshots.
    pad=12
    xx=max(0,x-pad);yy=max(0,y-pad)
    rr=min(W,x+w+pad);bb=min(H,y+h+pad)
    inside=np.zeros((H,W),bool)
    inside[yy:bb,xx:rr]=True
    diff=np.max(cv2.absdiff(a,b),axis=2)
    outside_fraction=float(np.mean(diff[~inside]>12))
    changed_fraction=float(np.mean(diff[y:y+h,x:x+w]>12))
    if outside_fraction>max_outside_fraction:
        raise ValueError(f"Unmatched browser state outside verified plane: {outside_fraction:.6f}")
    if changed_fraction<min_inside_fraction:
        raise ValueError(f"Verified DOM plane hide left no meaningful source pixels: {changed_fraction:.6f}")
    return outside_fraction,changed_fraction


_CAPTURE_INFO=r"""(selector) => {
  if (typeof selector!=='string'||selector.length>150) return null;
  const matches=Array.from(document.querySelectorAll(selector));
  if (matches.length!==1) return null;
  const el=matches[0],r=el.getBoundingClientRect(),s=getComputedStyle(el);
  if (s.visibility==='hidden'||s.display==='none'||+s.opacity<.95 ||
      r.width<60||r.height<40||r.left<0||r.top<0||
      r.right>innerWidth||r.bottom>innerHeight||
      !Number.isFinite(devicePixelRatio)) return null;
  const rect={x:r.x,y:r.y,w:r.width,h:r.height};
  const bg=s.backgroundColor.replace(/\s+/g,'');
  const alpha=(bg.startsWith('rgba(')?Number(bg.split(',').at(-1).replace(')','')):bg.startsWith('rgb(')?1:0);
  const radius=parseFloat(s.borderTopLeftRadius)||0;
  return {rect,dpr:devicePixelRatio,backgroundColor:s.backgroundColor,
          opaqueSurface:Number.isFinite(alpha)&&alpha>=.995,
          radiusNativePixels:radius*devicePixelRatio};
}"""

_HIDE=r"""(selector) => {
  if (window.__sauceActiveDomPlane) throw new Error('Already hidden');
  const matches=[...document.querySelectorAll(selector)];
  if (matches.length!==1) throw new Error('Unmatched verified layer selector');
  const e=matches[0],css=e.style.cssText, rect=e.getBoundingClientRect();
  window.__sauceActiveDomPlane={element:e,css};
  e.style.setProperty('visibility','hidden','important');
  if(getComputedStyle(e).visibility!=='hidden'){
    e.style.cssText=css;delete window.__sauceActiveDomPlane;
    throw new Error('DOM layer could not be hidden safely');
  }
  const end=e.getBoundingClientRect();
  if(Math.abs(end.x-rect.x)>1||Math.abs(end.y-rect.y)>1||
     Math.abs(end.width-rect.width)>1||Math.abs(end.height-rect.height)>1){
    e.style.cssText=css;delete window.__sauceActiveDomPlane;
    throw new Error('DOM layer hide changed layout geometry');
  }
  return true;
}"""

_RESTORE=r"""() => {
  const s=window.__sauceActiveDomPlane;
  if(!s)return false;
  s.element.style.cssText=s.css;
  delete window.__sauceActiveDomPlane;
  return true;
}"""


async def capture_pair(page,selector:str,*,expected_native_size=(1920,1080)):
    """Returns same-clock PNG pair; fails closed on mismatch or layout shift."""
    info=await page.evaluate(_CAPTURE_INFO,selector)
    if not info:
        raise ValueError("No unique visible, source-verified DOM element")
    scale=info['dpr'];r=info['rect']
    if not info.get("opaqueSurface"):
        raise ValueError("DOM plane cannot lift a transparent element with unknown background")
    if float(info.get("radiusNativePixels",0))>18:
        raise ValueError("DOM plane radius exceeds supported source-true stencil")
    rect=tuple(int(round(r[k]*scale)) for k in ('x','y','w','h'))
    # Chromium real screenshots, no replacement HTML or post-screenshot painting.
    visible=await page.screenshot(type='png',animations='disabled',caret='hide')
    await page.evaluate(_HIDE,selector)
    try:
        clean=await page.screenshot(type='png',animations='disabled',caret='hide')
    finally:
        await page.evaluate(_RESTORE)
    a=_frame(visible)
    if a.shape[:2]!=(expected_native_size[1],expected_native_size[0]):
        raise ValueError("Unexpected native screenshot pixel resolution")
    outside,changed=check_pair(visible,clean,rect)
    return Pair(visible,clean,rect,float(scale),changed,outside,
                hashlib.sha256(visible).hexdigest(),
                hashlib.sha256(clean).hexdigest(),
                True,float(info["radiusNativePixels"]))

_DISCOVER=r"""expected => {
  // Accept only visible, opaque, semantic, reasonably sized DOM elements;
  // reject overlays and sensitive inputs. Never create a replacement element.
  const nodes=[...document.querySelectorAll(
    '[data-slot="card"],[role="dialog"],article,section,[data-testid]')];
  const actual=expected;
  if(!actual||!Number.isFinite(actual.x)||!Number.isFinite(actual.y)||
     !Number.isFinite(actual.width)||!Number.isFinite(actual.height))return null;
  const iou=(a,b)=>{
    let x=Math.max(a.left,b.x),y=Math.max(a.top,b.y);
    let r=Math.min(a.right,b.x+b.width),t=Math.min(a.bottom,b.y+b.height);
    let inter=Math.max(0,r-x)*Math.max(0,t-y);
    return inter / Math.max(1,a.width*a.height+b.width*b.height-inter);
  };
  const candidates=nodes.map(el=>{
    const r=el.getBoundingClientRect(),s=getComputedStyle(el),
          bg=s.backgroundColor.replace(/\s+/g,''),
          alpha=(bg.startsWith('rgba(')?Number(bg.split(',').at(-1).replace(')','')):
                 bg.startsWith('rgb(')?1:0);
    const overlap=iou(r,actual);
    if(r.width<140||r.height<90||r.width>innerWidth*.74||
       r.height>innerHeight*.72||r.left<0||r.top<0||
       r.right>innerWidth||r.bottom>innerHeight||
       s.visibility==='hidden'||s.display==='none'||Number(s.opacity)<.995||
       !Number.isFinite(alpha)||alpha<.995||overlap<.65||
       el.querySelector('input[type="password"],[contenteditable="true"],iframe'))return null;
    return {el,rect:{x:r.x,y:r.y,width:r.width,height:r.height},
            score:overlap};
  }).filter(Boolean).sort((a,b)=>b.score-a.score);
  if(!candidates.length)return null;
  const chosen=candidates[0];
  const old=chosen.el.getAttribute('data-sauce-verified-plane');
  if(old!==null)throw new Error('Existing capture marker collision');
  chosen.el.setAttribute('data-sauce-verified-plane','true');
  return {selector:'[data-sauce-verified-plane="true"]',rect:chosen.rect,
          matches:candidates.length,score:chosen.score};
}"""


async def discover_verified_dom_plane(page,expected_css_rect):
    """Generic result-geometry -> live semantic element. No per-site selectors."""
    result=await page.evaluate(_DISCOVER,expected_css_rect)
    if not result or result["score"]<.65:
        return None
    return result
