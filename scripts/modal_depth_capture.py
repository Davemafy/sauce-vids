"""Temporary evidence-backed modal masking for multi-plane film compositing.

The Chromium page is the verified replay, not a synthetic clean-room UI.
A modal is hidden ONLY during the background screenshot and restored even if
screenshot capture fails. Never substitute an unrelated pre-modal screenshot.
"""
from __future__ import annotations

import cv2
import numpy as np
from contextlib import contextmanager

_HIDE_VERIFIED_MODAL = r"""(options) => {
  const expected=options.expected;
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
  // Brimble-specific: hide only the DOM-verified dark terminal shell
  // BEHIND a genuinely visible dialog, in this background pass alone.
  // No painting, generic black rectangle matching, or screenshot inpainting.
  let terminal=null,terminalOriginal=null;
  if (options.hideDarkPanel) {
    const candidates=[...document.querySelectorAll('div')].filter(n=>{
      if (!n.classList.contains('bg-[#222528]') ||
          !n.classList.contains('rounded-[13.25px]')) return false;
      const b=n.getBoundingClientRect(),c=getComputedStyle(n);
      return b.width>=430 && b.width<=500 &&
        b.height>=230 && b.height<=330 &&
        b.right>hit.box.right+100 &&
        b.left<hit.box.right && b.top<hit.box.bottom &&
        b.bottom>hit.box.top && c.backgroundColor==='rgb(34, 37, 40)' &&
        c.visibility!=='hidden' && c.display!=='none';
    });
    if (candidates.length===1) {
      terminal=candidates[0];
      terminalOriginal=terminal.style.cssText;
      terminal.style.setProperty('visibility','hidden','important');
      if (getComputedStyle(terminal).visibility!=='hidden') {
        terminal.style.cssText=terminalOriginal;
        terminal=null;
      }
    }
  }
  window.__sauceDepthCaptureState={el,original,terminal,terminalOriginal};
  return {box:{x:hit.box.x,y:hit.box.y,width:hit.box.width,
               height:hit.box.height},
          radiusCss:Math.max(0,parseFloat(hit.style.borderTopLeftRadius)||0),
          terminalHidden:!!terminal};
}"""

_RESTORE_VERIFIED_MODAL = r"""() => {
  const item=window.__sauceDepthCaptureState;
  if (!item) return;
  if (item.terminal) item.terminal.style.cssText=item.terminalOriginal;
  item.el.style.cssText=item.original;
  delete window.__sauceDepthCaptureState;
}"""

def verified_modal_background(page, expected_box:dict, shape:tuple[int,int],
                              hide_dark_panel:bool=False):
    """Return (BGR background, live CSS box, CSS radius, terminalHidden), else None.

    No masking is used unless a live dialog closely matches trace geometry.
    This is intentionally an optional pass with a safe one-plane fallback.
    """
    if not isinstance(expected_box,dict): return None
    try:
        selected=page.evaluate(_HIDE_VERIFIED_MODAL,
                              {'expected':expected_box,
                               'hideDarkPanel':hide_dark_panel})
    except Exception:
        return None
    if not selected: return None
    try:
        screenshot=page.screenshot(scale='device',animations='allow',caret='hide')
        clean=cv2.imdecode(np.frombuffer(screenshot,dtype=np.uint8),
                           cv2.IMREAD_COLOR)
        if clean is None or clean.shape[:2]!=shape:
            return None
        return (clean,selected['box'],float(selected['radiusCss']),
                bool(selected.get('terminalHidden',False)))
    finally:
        page.evaluate(_RESTORE_VERIFIED_MODAL)


def expected_modal_box(modal_hints:list[dict],foreground_id:str|None,
                       source_ms:float)->dict|None:
    """The plane owner is the modal, never a later child-action spotlight box."""
    owned=next((h for h in modal_hints if h.get('id')==foreground_id),None)
    if owned is not None:return owned['box']
    imminent=next((h for h in modal_hints
        if abs(float(h['sourceMs'])-source_ms)<=350),None)
    return imminent['box'] if imminent is not None else None


# On Brimble, the authentic dialog starts its CSS fade at ~0 opacity while
# its separate decorative terminal occupies the same screen pixels. During the
# first few visible frames the dark panel literally shows through the partly
# transparent dialog (the known ~0.80s gray rectangle in the exported film).
# This OPTIONAL presentation-only capture correction renders the real dialog
# at its own final opacity while keeping genuine Chromium text, layout and
# interaction intact. No synthetic pixels, rectangular matte, or time warp.
# The site animation's opacity declaration is restored in all cases.
_OPAQUE_VERIFIED_OPENING = r"""expected => {
 const dialogs=[...document.querySelectorAll(
   '[role="dialog"],dialog[open],[aria-modal="true"]')].filter(el=>{
     const r=el.getBoundingClientRect(),s=getComputedStyle(el);
     return r.width>32&&r.height>32&&s.visibility!=='hidden'
       &&s.display!=='none';
   });
 if(dialogs.length!==1)return false;
 const el=dialogs[0],box=el.getBoundingClientRect();
 const distance=Math.hypot(box.x+box.width/2-(expected.x+expected.width/2),
   box.y+box.height/2-(expected.y+expected.height/2));
 const ratio=Math.max(box.width/expected.width,expected.width/box.width,
   box.height/expected.height,expected.height/box.height);
 if(distance>70||ratio>1.6)return false;
 const fade=Number(getComputedStyle(el).opacity);
 if(!Number.isFinite(fade)||fade<.25||fade>=.995)return false;
 // Only the observed Brimble decorative terminal, not an arbitrary app
 // panel or user content. Both geometry and native computed color must match.
 const panels=[...document.querySelectorAll('div')].filter(node=>{
   if(!node.classList.contains('bg-[#222528]')||
      !node.classList.contains('rounded-[13.25px]'))return false;
   const r=node.getBoundingClientRect(),s=getComputedStyle(node);
   return r.width>=430&&r.width<=500&&r.height>=230&&r.height<=330
     &&r.left<box.right&&r.right>box.left+100
     &&r.top<box.bottom&&r.bottom>box.top
     &&s.backgroundColor==='rgb(34, 37, 40)'
     &&s.visibility!=='hidden'&&s.display!=='none'
     &&!el.contains(node);
 });
 if(panels.length!==1||window.__sauceOpacityFrameState)return false;
 const original=el.style.getPropertyValue('opacity');
 const priority=el.style.getPropertyPriority('opacity');
 el.style.setProperty('opacity','1','important');
 if(Number(getComputedStyle(el).opacity)<.995){
   if(original)el.style.setProperty('opacity',original,priority);
   else el.style.removeProperty('opacity');
   return false;
 }
 window.__sauceOpacityFrameState={element:el,original,priority};
 return true;
}"""

_RESTORE_OPAQUE_OPENING = r"""() => {
 const state=window.__sauceOpacityFrameState;
 if(!state)return;
 if(state.original)state.element.style.setProperty(
    'opacity',state.original,state.priority);
 else state.element.style.removeProperty('opacity');
 delete window.__sauceOpacityFrameState;
}"""


@contextmanager
def stabilized_verified_dialog_opening(page,expected_box:dict|None):
    """Temporarily remove only a real Brimble dialog's occluding CSS fade.

    Caller must additionally gate this helper to verified Brimble film replay;
    raw capture and every other product are not presentation-adjusted.
    """
    changed=False
    if isinstance(expected_box,dict):
        try:
            changed=bool(page.evaluate(_OPAQUE_VERIFIED_OPENING,expected_box))
        except Exception:
            changed=False
    try:
        yield changed
    finally:
        if changed:
            page.evaluate(_RESTORE_OPAQUE_OPENING)
