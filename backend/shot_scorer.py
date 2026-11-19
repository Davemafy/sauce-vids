"""Rank real public-page subjects and choose an editorial sequence."""
from __future__ import annotations

import math

# Run inside the existing inspector. Keep text samples local and bounded.
DISCOVER_JS = r"""(path) => {
 const article = document.querySelector('main,[role="main"]') || document.body;
 const blocked='nav,footer,aside,[role="navigation"],[role="dialog"],[role="alertdialog"],form,[data-private],[data-secret],[data-sensitive]';
 const selector='pre,table,img,h1,section,article,figure,[role="tabpanel"],[role="grid"],[class*="card" i],[class*="preview" i],[class*="terminal" i],[class*="demo" i],button,select,input';
 const rgb=color=>(color.match(/[\d.]+/g)||[]).map(Number);
 function luminance(color){
   const [r=0,g=0,b=0]=rgb(color).map(n=>n/255).map(n=>n<=.04045?n/12.92:Math.pow((n+.055)/1.055,2.4));
   return .2126*r+.7152*g+.0722*b;
 }
 function background(node){
   for(let e=node;e;e=e.parentElement){
     const c=getComputedStyle(e).backgroundColor, p=rgb(c);
     if(p.length===3 || p[3]>=.85)return c;
   }
   return 'rgb(255,255,255)';
 }
 function words(e){return (e.innerText||'').trim().split(/\s+/).filter(Boolean);}
 const candidates=[], elements=[...article.querySelectorAll(selector)].slice(0,2200);
 // A bespoke app may be built entirely from divs. Look at bounded
 // ancestors of real controls, rather than crawling every wrapper.
 for(const e of elements.slice()){
   if(!e.matches('button,select,input')||e.closest(blocked))continue;
   for(let n=e.parentElement, depth=0;n&&n!==article&&depth<5;n=n.parentElement,depth++)
     elements.push(n);
 }
 for(const e of new Set(elements)){
   if(e.matches('button,select,input')||e.closest(blocked))continue;
   if(!e.checkVisibility({checkOpacity:true,checkVisibilityCSS:true}))continue;
   const r=e.getBoundingClientRect(), y=r.top+scrollY, w=innerWidth, h=innerHeight;
   if(r.width<w*.15||r.height<66||r.height>h*.96||r.width>w*.99||
      r.left<-2||r.right>w+2||y<0||y>Math.min(document.documentElement.scrollHeight,h*20))continue;
   const text=words(e);
   if(text.length>170)continue;
   if(/\brickroll/i.test(text.slice(0,12).join(' ')))continue;
   const label=(e.getAttribute('aria-label')||e.getAttribute('alt')||
     e.querySelector('h1,h2,h3,h4,figcaption')?.innerText||text.slice(0,9).join(' ')).trim().slice(0,100);
   if(/\b(cookie|rickroll|privacy preferences|newsletter|sign in|log in|subscribe)\b/i.test(label))continue;
   const media=e.matches('img,video,canvas')?e:e.querySelector('video,canvas,img');
   const mediaRect=media?.getBoundingClientRect();
   const substantialMedia=!!(mediaRect&&mediaRect.width>=180&&mediaRect.height>=100&&
     mediaRect.width*mediaRect.height>=r.width*r.height*.23);
   const code=e.matches('pre')||!!e.querySelector('pre');
   const table=e.matches('table,[role="grid"]')||!!e.querySelector('table,[role="grid"]');
   const controls=[...e.querySelectorAll('button,select,input,[role="button"]')]
     .filter(n=>!n.closest(blocked)&&n.getClientRects().length).slice(0,16).length;
   const times=(e.innerText||'').slice(0,1800).match(/\b\d{1,2}:\d{2}\b/g)?.length||0;
   const headings=e.querySelectorAll('h1,h2,h3,h4').length;
   if(headings>3 && !table)continue;
   const tag=e.tagName.toLowerCase();
   const product=(code||table||times>=2 && /\b(utc|booked|schedule|availability)\b/i.test(text.join(' '))||controls>=3&&text.length>=6&&!substantialMedia);
   if(!product&&media?.matches('video,canvas'))continue;
   if(!product&&!substantialMedia&&(text.length<5||!headings&&tag!=='article'))continue;
   const identity=path(e);
   if(!identity)continue;
   const textElement=e.querySelector('p,button,code,td')||e;
   const front=luminance(getComputedStyle(textElement).color), back=luminance(background(textElement));
   candidates.push({selector:identity,label,kind:code?'code':table?'data':product?'widget':substantialMedia?'media':'value',
     rect:{x:r.x,y,width:r.width,height:r.height}, word_count:text.length,controls,times,tag,
     font_px:parseFloat(getComputedStyle(textElement).fontSize)||14,
     contrast:(Math.max(front,back)+.05)/(Math.min(front,back)+.05),
     viewport:[w,h]});
   if(candidates.length>=220)break;
 }
 return candidates;
}"""


def _score(candidate: dict) -> float:
    width, height = candidate["viewport"]
    rect = candidate["rect"]
    share = rect["width"] * rect["height"] / (width * height)
    priority = {"code": 3.3, "data": 3.5, "widget": 3.7, "media": 2.2, "value": 1.45}
    return (priority[candidate["kind"]] + min(1.25, share * 4)
            + min(1.0, candidate["contrast"] / 7)
            + min(.7, candidate["font_px"] / 28)
            + min(.9, candidate["times"] * .24)
            + (.55 if candidate.get("tag") == "h1" and candidate["kind"] == "widget" else 0)
            - min(.7, rect['y'] / height * .075)
            - max(0, share - .48) * 2.5
            - max(0, candidate["word_count"] - 45) / 75
            - max(0, candidate["controls"] - 11) * .12)


def _overlap(a: dict, b: dict) -> float:
    width = max(0.0, min(a["x"] + a["width"], b["x"] + b["width"]) - max(a["x"], b["x"]))
    height = max(0.0, min(a["y"] + a["height"], b["y"] + b["height"]) - max(a["y"], b["y"]))
    return width * height / min(a["width"] * a["height"], b["width"] * b["height"])


def select_beats(candidates: list[dict], limit: int = 4) -> list[dict]:
    """Start on product evidence, then add distinct detail and value beats."""
    ranked = sorted(
        ({**c, "score": round(_score(c), 2)} for c in candidates),
        key=lambda c: (-c["score"], c["rect"]["y"], c["selector"]),
    )
    product = {"widget", "data", "code"}
    hook = next((c for c in ranked if c["kind"] in product and c["score"] >= 4.1), None)
    if hook is None:
        return []
    chosen = [hook]
    reasons = {
        "widget": "focused interface with several real controls",
        "data": "visible product data in a bounded region",
        "code": "bounded source or command block",
        "media": "prominent product-page media",
        "value": "compact nearby product copy",
    }
    for c in ranked:
        if c["score"] < 2.5 or len(chosen) >= limit:
            break
        if c["kind"] == "value" and any(s["kind"] == "value" for s in chosen):
            continue
        if any(_overlap(c["rect"], s["rect"]) > .48 or
               (c["label"] and c["label"].casefold() == s["label"].casefold()) for s in chosen):
            continue
        chosen.append(c)
    if len(chosen) < 3:
        return []
    # Show supporting product details before broader proof or value footage.
    chosen[1:] = sorted(chosen[1:], key=lambda c: (c["kind"] not in product, c["rect"]["y"]))
    return [{**c, "purpose": "hook" if i == 0 else "detail" if i < len(chosen) - 1 else "payoff",
             "reason": reasons[c["kind"]]} for i, c in enumerate(chosen)]


def crop_for_subject(rect: dict, width: int, height: int) -> tuple[int, int, int, int]:
    """Return an even 16:9 crop containing the subject and its breathing room."""
    x, y, w, h = (float(rect[k]) for k in ("x", "y", "width", "height"))
    if not all(math.isfinite(v) for v in (x, y, w, h)) or (
            min(x, y) < 0 or min(w, h) <= 0 or x+w > width or y+h > height):
        raise ValueError("Subject outside recorded viewport")
    units = min(width // 32, height // 18, math.ceil(max(w * 1.22 / 32, h * 1.22 / 18, width / 68)))
    cw, ch = units * 32, units * 18
    if cw < w or ch < h:
        raise ValueError("Subject does not fit output")
    left = int(max(0, min(width-cw, x+w/2-cw/2))) // 2 * 2
    top = int(max(0, min(height-ch, y+h/2-ch/2))) // 2 * 2
    if left > x or top > y or left+cw < x+w or top+ch < y+h:
        raise ValueError("Framing clipped subject")
    return left, top, cw, ch
