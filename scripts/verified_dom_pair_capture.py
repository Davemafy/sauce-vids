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


@dataclass(frozen=True)
class MultiPair:
    """One authentic visible browser frame and one with all listed real DOM layers hidden."""
    visible:bytes
    clean:bytes
    layers:tuple[dict,...]
    outside_fraction:float
    visible_sha256:str
    clean_sha256:str


def check_multi_pair(visible,clean,rects,*,max_outside_fraction=.00008,
                     min_inside_fraction=.012):
    if not 2<=len(rects)<=3:
        raise ValueError("Paired multi-plane capture requires two or three DOM rectangles")
    front=_frame(visible);back=_frame(clean)
    if front.shape!=back.shape:
        raise ValueError("Paired multi-plane captures must have identical resolution")
    H,W=front.shape[:2]
    outside=np.ones((H,W),bool)
    for i,rect in enumerate(rects):
        if len(rect)!=4 or not all(type(v) is int for v in rect):
            raise ValueError("Unverified native DOM plane rectangle")
        x,y,w,h=rect
        if x<0 or y<0 or w<40 or h<30 or x+w>W or y+h>H:
            raise ValueError("DOM multi-plane element not fully inside actual page")
        for other in rects[:i]:
            ox,oy,ow,oh=other
            if max(0,min(x+w,ox+ow)-max(x,ox))*max(0,min(y+h,oy+oh)-max(y,oy))>0:
                raise ValueError("Multi-plane elements overlap in genuine source")
        pad=12
        outside[max(0,y-pad):min(H,y+h+pad),max(0,x-pad):min(W,x+w+pad)]=False
    diff=np.max(cv2.absdiff(front,back),axis=2)
    external=float(np.mean(diff[outside]>12))
    if external>max_outside_fraction:
        raise ValueError(f"Changed pixels outside union of verified live DOM elements {external:.6f}")
    fractions=[float(np.mean(diff[y:y+h,x:x+w]>12)) for x,y,w,h in rects]
    if any(frac<min_inside_fraction for frac in fractions):
        raise ValueError("One of the real DOM component planes has no distinct captured pixels")
    return external,fractions


_MULTI_INFO=r"""selectors => {
  if (!Array.isArray(selectors)||selectors.length<2||selectors.length>3)return null;
  return selectors.map(selector=>{
    if(typeof selector!=='string'||selector.length>150)return null;
    const matches=[...document.querySelectorAll(selector)];
    if(matches.length!==1)return null;
    const el=matches[0],r=el.getBoundingClientRect(),s=getComputedStyle(el);
    const bg=s.backgroundColor.replace(/\s+/g,'');
    const alpha=bg.startsWith('rgba(')?Number(bg.split(',').at(-1).replace(')','')):
                bg.startsWith('rgb(')?1:0;
    if(!Number.isFinite(alpha)||alpha<.995||
       s.visibility==='hidden'||s.display==='none'||Number(s.opacity)<.995||
       r.width<60||r.height<40||r.left<0||r.top<0||
       r.right>innerWidth||r.bottom>innerHeight||
       el.querySelector('input[type="password"],[contenteditable="true"],iframe'))
         return null;
    return {rect:{x:r.x,y:r.y,w:r.width,h:r.height},
            radiusNativePixels:(parseFloat(s.borderTopLeftRadius)||0)*devicePixelRatio,
            opaqueSurface:true};
  });
}"""

_MULTI_HIDE=r"""selectors => {
  if(window.__sauceActiveDomPlane||window.__sauceMultiCapture)return false;
  const els=selectors.map(sel=>[...document.querySelectorAll(sel)]);
  if(els.some(e=>e.length!==1))return false;
  const records=els.map(v=>({el:v[0],css:v[0].style.cssText,
                             before:v[0].getBoundingClientRect()}));
  try{
    for(const item of records)item.el.style.setProperty('visibility','hidden','important');
    for(const item of records){
      const after=item.el.getBoundingClientRect();
      if(getComputedStyle(item.el).visibility!=='hidden'||
          Math.abs(after.x-item.before.x)>1||
          Math.abs(after.y-item.before.y)>1||
          Math.abs(after.width-item.before.width)>1||
          Math.abs(after.height-item.before.height)>1){
        throw new Error('Verified DOM multi-plane hide changed browser layout');
      }
    }
  }catch(error){
    for(const item of records)item.el.style.cssText=item.css;
    return false;
  }
  window.__sauceMultiCapture=records;
  return true;
}"""

_MULTI_RESTORE=r"""() => {
  const records=window.__sauceMultiCapture;
  if(!records)return false;
  for(const item of records)item.el.style.cssText=item.css;
  delete window.__sauceMultiCapture;
  return true;
}"""

async def capture_multi_pair(page,selectors,*,expected_native_size):
    """One source and one collectively-hidden real browser plate, same virtual time."""
    info=await page.evaluate(_MULTI_INFO,selectors)
    if not info or any(not item for item in info):
        raise ValueError("No unique eligible opaque DOM capture surfaces")
    dpr=float(await page.evaluate('devicePixelRatio'))
    if not math.isfinite(dpr) or dpr<1:
        raise ValueError("Invalid browser screenshot device pixel ratio")
    rects=[]
    for row in info:
        if row["radiusNativePixels"]>18:
            raise ValueError("DOM plane source radius exceeds verified stencil bounds")
        rects.append(tuple(round(row["rect"][k]*dpr) for k in ("x","y","w","h")))
    # Validate disjoint measured DOM rectangles before touching the DOM.
    for i,(x,y,w,h) in enumerate(rects):
        if w<40 or h<30:
            raise ValueError("Invalid DOM rectangle")
        for ox,oy,ow,oh in rects[:i]:
            if max(0,min(x+w,ox+ow)-max(x,ox))*max(0,min(y+h,oy+oh)-max(y,oy))>0:
                raise ValueError("Overlapping UI components cannot be independently captured")
    visible=await page.screenshot(type="png",animations="disabled",caret="hide")
    if not await page.evaluate(_MULTI_HIDE,selectors):
        raise ValueError("Cannot safely hide multiple genuine DOM components")
    try:
        clean=await page.screenshot(type="png",animations="disabled",caret="hide")
    finally:
        await page.evaluate(_MULTI_RESTORE)
    im=_frame(visible)
    if im.shape[:2]!=(expected_native_size[1],expected_native_size[0]):
        raise ValueError("Wrong native source resolution for paired UI video")
    outside,inside=check_multi_pair(visible,clean,rects)
    return MultiPair(
        visible,clean,
        tuple({"rect":rect,"radiusPx":float(row["radiusNativePixels"]),
               "opaqueSurface":True,"changedFraction":fraction}
              for rect,row,fraction in zip(rects,info,inside)),
        outside,hashlib.sha256(visible).hexdigest(),
        hashlib.sha256(clean).hexdigest())


_DISCOVER_MULTI=r"""(bounds) => {
  if(!Array.isArray(bounds)||bounds.length<2||bounds.length>3)return null;
  const options=[...document.querySelectorAll(
    '[data-slot="card"],article,[role="dialog"],section,[data-testid]')];
  const iou=(a,b)=>{
    const x=Math.max(a.left,b.x),y=Math.max(a.top,b.y);
    const r=Math.min(a.right,b.x+b.width),t=Math.min(a.bottom,b.y+b.height);
    const n=Math.max(0,r-x)*Math.max(0,t-y);
    return n/Math.max(1,a.width*a.height+b.width*b.height-n);
  };
  const used=new Set(),chosen=[];
  for(const expected of bounds){
    const candidate=options.map(el=>{
      const r=el.getBoundingClientRect(),s=getComputedStyle(el),
            bg=s.backgroundColor.replace(/\s+/g,''),
            alpha=bg.startsWith('rgba(')?Number(bg.split(',').at(-1).replace(')','')):
                  bg.startsWith('rgb(')?1:0;
      if(used.has(el)||!Number.isFinite(alpha)||alpha<.995||
         s.display==='none'||s.visibility==='hidden'||Number(s.opacity)<.995||
         r.width<140||r.height<90||r.left<0||r.top<0||
         r.right>innerWidth||r.bottom>innerHeight||
         el.querySelector('input[type="password"],[contenteditable="true"],iframe'))
          return null;
      return {el,r,score:iou(r,expected)};
    }).filter(x=>x&&x.score>.80).sort((a,b)=>b.score-a.score)[0];
    if(!candidate)return null;
    used.add(candidate.el);chosen.push(candidate);
  }
  for(let i=0;i<chosen.length;i++){
    const r=chosen[i].r;
    for(let j=0;j<i;j++){
      const q=chosen[j].r;
      if(Math.max(0,Math.min(r.right,q.right)-Math.max(r.left,q.left))*
         Math.max(0,Math.min(r.bottom,q.bottom)-Math.max(r.top,q.top))>0)
        return null;
    }
  }
  if(chosen.some(c=>c.el.hasAttribute('data-sauce-multiplane')))return null;
  return chosen.map((candidate,i)=>{
    const marker='sauce-verified-'+i;
    candidate.el.setAttribute('data-sauce-multiplane',marker);
    return {selector:'[data-sauce-multiplane="'+marker+'"]',
            score:candidate.score,
            rect:{x:candidate.r.x,y:candidate.r.y,
                  width:candidate.r.width,height:candidate.r.height}};
  });
}"""

async def discover_verified_dom_planes(page,expected_css_rectangles):
    """Measure exact live semantic elements; caller provides real DOM target bounds."""
    result=await page.evaluate(_DISCOVER_MULTI,expected_css_rectangles)
    return result if result and len(result)==len(expected_css_rectangles) else None
