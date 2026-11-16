"""DOM-aware deterministic source acquisition for new scripted sessions.

Unlike editing an archived screenshot, selector-based redaction must run in
the real Chromium page where bounding rectangles can be verified. Captured
images are saved privately and should then be SHA-pinned in a Sauce session.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import cv2
import numpy as np

from scripted_v2_render import redact


def settle_chromium_step(page,network_timeout_ms:int=12000):
    """Fail closed if the requested source state cannot actually settle."""
    # Do not silently treat a never-idle page as deterministic.
    page.wait_for_load_state("networkidle",timeout=network_timeout_ms)
    complete=page.evaluate("""async () => {
      await document.fonts.ready;
      const images=[...document.images].filter(el=>el.getBoundingClientRect().width>0
        && el.getBoundingClientRect().height>0);
      await Promise.all(images.map(async img=>{
        if (!img.complete)await new Promise((resolve,reject)=>{
          img.addEventListener('load',resolve,{once:true});
          img.addEventListener('error',reject,{once:true});
        });
        if (img.naturalWidth<1)throw new Error('Visible image did not load');
        await img.decode();
      }));
      // Fast-forward only finite CSS/Web Animations. Infinite spinners are
      // excluded instead of extending playback by unpredictable real time.
      const animations=document.getAnimations({subtree:true});
      for(const a of animations){
        if(Number.isFinite(a.effect?.getComputedTiming().endTime||Infinity)){
          try{a.finish()}catch{}
        }
      }
      await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
      return {fonts:document.fonts.status,images:images.length,
              animations:animations.length};
    }""")
    if complete["fonts"]!="loaded":
        raise RuntimeError("Capture must wait until source fonts are loaded")
    return complete


def capture_frame_with_selector_redaction(page,output:Path,
                                          blur_selectors:list[str]=[],
                                          expected_dpr:int=2)->dict:
    """Acquire one settled, frame-stepped browser state with privacy masking."""
    if expected_dpr<2:
        raise ValueError("Native screenshot must be HiDPI >= 2")
    status=settle_chromium_step(page)
    browser_dpr=float(page.evaluate("window.devicePixelRatio"))
    if browser_dpr!=expected_dpr:
        raise RuntimeError("Unexpected captured DPR; do not upscale missing pixels")
    bounds=[]
    for selector in blur_selectors:
        if not isinstance(selector,str) or not 1<=len(selector)<=180:
            raise ValueError("Invalid privacy selector")
        locator=page.locator(selector)
        if locator.count()==0:
            raise RuntimeError("Required private field selector not found: "+selector)
        for j in range(locator.count()):
            box=locator.nth(j).bounding_box()
            if box is None:
                raise RuntimeError("Private field missing visible geometry")
            bounds.append(box)
    raw=page.screenshot(scale='device',animations='disabled',caret='hide')
    image=cv2.imdecode(np.frombuffer(raw,dtype=np.uint8),cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError("Failed to acquire Chromium pixels")
    for box in bounds:
        image=redact(image,box)
    output=Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    if not cv2.imwrite(str(output),image,[cv2.IMWRITE_PNG_COMPRESSION,3]):
        raise RuntimeError("Cannot save sanitized browser screenshot")
    return {'stateFile':str(output),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
            'redactionSelectors':len(blur_selectors),'redactionRegions':len(bounds),
            'settled':status,'deviceScaleFactor':browser_dpr}
