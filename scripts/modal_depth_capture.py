"""Temporary evidence-backed modal masking for multi-plane film compositing.

The Chromium page is the verified replay, not a synthetic clean-room UI.
A modal is hidden ONLY during the background screenshot and restored even if
screenshot capture fails. Never substitute an unrelated pre-modal screenshot.
"""
from __future__ import annotations

import cv2
import numpy as np

_HIDE_VERIFIED_MODAL = r"""(expected) => {
  const elements = [...document.querySelectorAll(
    '[role="dialog"], dialog[open], [aria-modal="true"]')];
  const available = elements.map(el => {
    const box = el.getBoundingClientRect(), style = getComputedStyle(el);
    return {el, box, style};
  }).filter(v => v.box.width > 32 && v.box.height > 32 &&
    v.style.visibility !== 'hidden' && v.style.display !== 'none');
  const center = b => ({x:b.x+b.width/2,y:b.y+b.height/2});
  const anchor = center(expected);
  const ranked = available.map(v => ({
    ...v, error: Math.hypot(center(v.box).x-anchor.x,
                         center(v.box).y-anchor.y),
    size: Math.max(v.box.width/expected.width,expected.width/v.box.width,
                   v.box.height/expected.height,expected.height/v.box.height)
  })).sort((a,b)=>a.error-b.error);
  const hit=ranked[0];
  if (!hit || hit.error > 70 || hit.size > 1.6) return null;
  const el=hit.el, original=el.style.cssText;
  el.style.setProperty('visibility','hidden','important');
  if (getComputedStyle(el).visibility !== 'hidden') {
    el.style.cssText=original;
    return null;
  }
  window.__sauceDepthCaptureState={el,original};
  return {box:{x:hit.box.x,y:hit.box.y,width:hit.box.width,
               height:hit.box.height},
          radiusCss:Math.max(0,parseFloat(hit.style.borderTopLeftRadius)||0)};
}"""

_RESTORE_VERIFIED_MODAL = r"""() => {
  const item=window.__sauceDepthCaptureState;
  if (!item) return;
  item.el.style.cssText=item.original;
  delete window.__sauceDepthCaptureState;
}"""

def verified_modal_background(page, expected_box:dict, shape:tuple[int,int]):
    """Return (BGR background, live CSS box, CSS radius), else None.

    No masking is used unless a live dialog closely matches trace geometry.
    This is intentionally an optional pass with a safe one-plane fallback.
    """
    if not isinstance(expected_box,dict): return None
    try:
        selected=page.evaluate(_HIDE_VERIFIED_MODAL,expected_box)
    except Exception:
        return None
    if not selected: return None
    try:
        screenshot=page.screenshot(scale='device',animations='allow',caret='hide')
        clean=cv2.imdecode(np.frombuffer(screenshot,dtype=np.uint8),
                           cv2.IMREAD_COLOR)
        if clean is None or clean.shape[:2]!=shape:
            return None
        return clean,selected['box'],float(selected['radiusCss'])
    finally:
        page.evaluate(_RESTORE_VERIFIED_MODAL)
