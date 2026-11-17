"""Privacy-bounded, DOM-verified result detection for Sauce editorial holds.

The page compares text locally in Chromium; no plaintext, CSS content,
clipboard, input values or text digests leave the page. The proof exports
only a boolean change and container geometry.
"""
from __future__ import annotations

import math

RESULT_PROBE_JS = r"""(phase) => {
  const visible=(el)=>{
    if(!el)return false;
    const s=getComputedStyle(el),r=el.getBoundingClientRect();
    return r.width>2&&r.height>2&&s.display!=='none'&&
      s.visibility!=='hidden'&&+s.opacity>.05;
  };
  const safe=(el)=>!el.closest(
    '[data-private],[data-sensitive],[data-secret],[autocomplete="one-time-code"],'+
    'input,textarea,[contenteditable="true"],[type="password"],'+
    '#intercom-container,.crisp-client,.woot-widget-bubble');
  // Semantic dialogs must win over full-viewport Radix backdrops, which
  // also carry data-state=open but contain no product content.
  const modal=[...document.querySelectorAll(
     '[role="dialog"],[aria-modal="true"]')]
     .find(el=>visible(el)&&safe(el)) ||
    [...document.querySelectorAll('[data-state="open"]')]
      .find(el=>{const st=getComputedStyle(el),r=el.getBoundingClientRect();
        return visible(el)&&safe(el)&&
          ['fixed','absolute'].includes(st.position)&&
          parseInt(st.zIndex||'0',10)>=40&&r.height>=150&&
          r.width<=innerWidth*.96&&r.height<=innerHeight*.96;});
  const region=modal || document.querySelector('main') || document.body;
  if(!region||!visible(region)||!safe(region))
    return {valid:false};
  const rect=region.getBoundingClientRect();
  const walker=document.createTreeWalker(region,NodeFilter.SHOW_TEXT);
  const pieces=[];
  while(walker.nextNode()&&pieces.length<1200){
    const node=walker.currentNode,parent=node.parentElement;
    if(!parent||!safe(parent)||!visible(parent))continue;
    const txt=(node.textContent||'').trim();
    if(txt)pieces.push(txt);
  }
  // Retain comparison material solely inside this Chromium document.
  const snap={text:pieces.join('\u001e'),
              count:pieces.length,modal:!!modal,
              height:Math.round(rect.height),width:Math.round(rect.width)};
  if(phase==='before'){
    window.__saucePrivateResultBaseline=snap;
    return {valid:true,modal:snap.modal};
  }
  const old=window.__saucePrivateResultBaseline;
  if(!old)return {valid:false};
  return {valid:true,modal:snap.modal,
    changedText:snap.text!==old.text,
    addedTextNodes:Math.max(0,snap.count-old.count),
    heightGain:Math.max(0,snap.height-old.height),
    widthGain:Math.max(0,snap.width-old.width),
    newModal:snap.modal&&!old.modal};
}"""


def classify_result(observation: dict, source_ms: float) -> dict | None:
    """Only genuine text changes or meaningful growth qualify for a hold.

    No values from the product, including text length/hash or a secret,
    appear in the exported result receipt.
    """
    if not isinstance(observation, dict) or not observation.get("valid"):
        return None
    text = observation.get("changedText") is True
    added = observation.get("addedTextNodes", 0)
    growth = observation.get("heightGain", 0)
    if type(added) is not int or not 0 <= added <= 1200:
        return None
    if type(growth) is not int or not 0 <= growth <= 1440:
        return None
    if not text and growth < 16:
        return None
    if not math.isfinite(source_ms) or source_ms < 0:
        return None
    # 1.2–1.8s of genuinely readable state, followed by 0.35s fade.
    # Each new visible text node earns 80ms; each px of expanded height
    # earns 3ms, both capped to prevent unbounded end padding.
    hold_ms = min(1800, 1200 + min(600, added*80 + growth*3))
    return {"sourceMs":round(source_ms,3),
            "evidence":"visible-result-change" if text else "container-expansion",
            "holdMs":int(round(hold_ms/1000*60))*1000/60,
            "fadeMs":350}


def append_result_hold(encoder, last_frame, fps: int,
                       evidence: dict | None) -> dict:
    """Append source-identical sharp frames, then ease to the dark studio.

    Called *before* FFmpeg closes: no second H.264 encode, no shrunken text.
    The producer pads 48kHz Foley WAV to the new exact output frame count.
    """
    if evidence is None:
        return {"holdFrames":0,"fadeFrames":0,"totalFrames":0}
    if fps != 60 or last_frame is None:
        raise ValueError("Result hold needs a decoded 60fps final frame")
    import numpy as np
    hold = round(evidence["holdMs"]*fps/1000)
    fade = round(evidence["fadeMs"]*fps/1000)
    if not 72 <= hold <= 108 or fade != 21:
        raise ValueError("Result dwell is outside editorial bounds")
    frozen = last_frame.tobytes()
    for _ in range(hold):
        encoder.stdin.write(frozen)
    dark=np.array((15,10,9),dtype=np.float32)[None,None,:]
    source=last_frame.astype(np.float32)
    for i in range(fade):
        u=(i+1)/fade
        # Cosine ease gives a stationary, fully sharp hold followed by
        # a smooth fade with zero slope at both ends.
        visible=.5*(1+math.cos(math.pi*u))
        frame=np.uint8(np.rint(np.clip(source*visible+dark*(1-visible),0,255)))
        encoder.stdin.write(frame.tobytes())
    return {"holdFrames":hold,"fadeFrames":fade,"totalFrames":hold+fade}
