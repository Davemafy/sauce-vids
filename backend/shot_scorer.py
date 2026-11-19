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


# Review mode preserves the existing URL reel planner until the crops have been accepted.
_PRODUCT_EVIDENCE_JS = r"""() => {
 const root = document.querySelector('main,[role="main"]') || document.body;
 const privateRegion = '[data-private],[data-secret],[data-sensitive]';
 const chrome = 'header,nav,footer,[role="navigation"],[role="banner"],[role="contentinfo"],' +
   '[role="dialog"],[role="alertdialog"],[id*="cookie" i],[class*="cookie-banner" i]';
 const mediaSelector = 'img,video,iframe,canvas,svg';
 const gridSelector = 'table,[role="grid"],[role="treegrid"],[role="table"]';
 const controlSelector = 'button,input:not([type="hidden"]),select,textarea,' +
   '[role="button"],[role="tab"],[role="switch"],[role="checkbox"],[role="radio"],summary';
 const targetSelector = 'button[role="tab"],button[aria-pressed],button[aria-expanded],' +
   'button[role="switch"],input[type="checkbox"],input[type="radio"],summary';
 const bait = /rick\s*roll|never gonna give you up|watch (?:our |the )?video|share on/i;
 const preview = /\b(?:app|interface|dashboard|editor|spreadsheet|database|calendar|booking|schedule|product|demo|preview|screenshot|workflow|newsletter|publishing|member(?:ship)?|content management)\b/i;
 const stock = /\b(?:logo|brandmark|portrait|headshot|wallpaper|background|avatar|illustration|testimonial|banner|office|desk|dancing|party|on stage)\b/i;
 const liveProduct = /\b(?:editor|dashboard|spreadsheet|database|calendar|booking|screenshot|demo|workflow|newsletters?|publishing|members(?:hip)?)\b/i;
 const bookingText = /\b(?:booking|booked|calendar|schedule|availability|timezone|time zone|available times)\b/i;
 const price = /(?:[$€£₦]\s*\d+(?:[.,]\d+)?(?![\d.,]|\s*[KMB]\b)|\d\s*(?:USD|EUR|GBP)\b)/i;
 const billing = /(?:\b(?:billed|per (?:seat|month|year|user)|monthly|annually)\b|\/\s*(?:mo(?:nth)?|yr|year)\b)/i;
 const viewport = [innerWidth, innerHeight];
 const maxY = Math.min(document.documentElement.scrollHeight, innerHeight * 30);
 const rects = new WeakMap();
 const visibles = new WeakMap();
 function rectangle(node) {
   if (rects.has(node)) return rects.get(node);
   const {x,y,width,height} = node.getBoundingClientRect();
   const rect = {x:x+scrollX, y:y+scrollY, width, height};
   rects.set(node, rect);
   return rect;
 }
 function visible(node) {
   if (!visibles.has(node)) {
     const {width,height} = rectangle(node);
     visibles.set(node, width >= 7 && height >= 7 &&
       node.checkVisibility({opacityProperty:true, visibilityProperty:true}));
   }
   return visibles.get(node);
 }
 function path(node) {
   const parts = [];
   for (let e = node; e && parts.length < 24; e = e.parentElement) {
     if (e.id && /^[a-z][a-z0-9_-]{0,45}$/i.test(e.id) &&
         !/secret|password|token/i.test(e.id)) {
       const anchor = '#' + CSS.escape(e.id);
       if (document.querySelectorAll(anchor).length === 1) {
         parts.unshift(anchor);
         return parts.join(' > ');
       }
     }
     if (e === document.body) {
       parts.unshift('body');
       return parts.join(' > ');
     }
     const tag = e.localName;
     let index = 1;
     for (let s = e.previousElementSibling; s; s = s.previousElementSibling) {
       if (s.localName === tag) index++;
     }
     parts.unshift(tag + ':nth-of-type(' + index + ')');
   }
   return '';
 }
 function label(node) {
   return (node.getAttribute('aria-label') || node.getAttribute('alt') ||
      node.getAttribute('title') || node.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120);
 }
 function contained(child, parent) {
   return child.x >= parent.x-3 && child.y >= parent.y-3 &&
     child.x+child.width <= parent.x+parent.width+3 &&
     child.y+child.height <= parent.y+parent.height+3;
 }
 function bits(node, selector, rect, cap) {
   return [...node.querySelectorAll(selector)].slice(0, cap * 5)
     .filter(e => visible(e) && contained(rectangle(e), rect) && !e.closest(chrome+','+privateRegion))
     .slice(0, cap);
 }
 function substantialMedia(node) {
   const r = rectangle(node);
   if (!visible(node) || r.width * r.height <= 40000) return false;
   if (node.matches('img')) return node.complete && node.naturalWidth >= r.width * .8;
   if (node.matches('video')) return node.readyState >= 2 && node.videoWidth >= r.width * .8;
   if (node.matches('iframe')) {
     const nested = node.contentDocument;
     return !!nested?.body && nested.readyState !== 'loading' &&
       !!nested.body.querySelector('main,article,button,[role],img,canvas');
   }
   if (node.matches('svg')) return node.querySelectorAll('path,text,rect,image,use').length >= 12;
   return true;
 }
 function mediaSource(node) {
   const url = node.currentSrc || node.src || '';
   if (!url) return null;
   try { return new URL(url, location.href); }
   catch (error) { return null; }
 }
 function mediaLabel(node) {
   let source = '';
   try { source = decodeURIComponent(mediaSource(node)?.pathname || ''); }
   catch (error) { /* An inline or unparseable source has no useful path. */ }
   return [label(node), node.getAttribute('data-testid') || '', node.getAttribute('class') || '',
     node.closest('figure')?.getAttribute('class') || '', source].join(' ').replace(/[_.\/-]/g, ' ');
 }
 function primaryFont(node, rect) {
   const textSelector = 'h1,h2,h3,h4,button,[role="tab"],[role="switch"],td,th,code,p,[aria-label],[data-day]';
   const samples = (node.matches(textSelector) ? [node] : []).concat(bits(node,textSelector,rect,65))
     .filter(e => /[a-z0-9]{2,}/i.test(label(e)) && !bait.test(label(e)));
   const sizes = samples.map(e => {
     const width = rectangle(e).width;
     const scale = e.offsetWidth && width < e.offsetWidth ? width/e.offsetWidth : 1;
     return parseFloat(getComputedStyle(e).fontSize) * scale;
   }).filter(Number.isFinite).sort((a,b)=>a-b);
   // Primary text is the upper quartile in a complex interface. Secondary
   // labels and badges still show up in the actual crop for visual review.
   return sizes.length ? sizes[Math.floor((sizes.length-1)*.75)] : null;
 }
 function rgb(color) {
   return (color.match(/[\d.]+/g)||[]).map(Number);
 }
 function luminance(color) {
   const [r=0,g=0,b=0] = rgb(color).map(n=>n/255)
     .map(n=>n<=.04045?n/12.92:Math.pow((n+.055)/1.055,2.4));
   return .2126*r+.7152*g+.0722*b;
 }
 function background(node) {
   for (let e=node;e;e=e.parentElement) {
     const color=getComputedStyle(e).backgroundColor;
     const channels=rgb(color);
     if (channels.length===3 || channels[3]>=.85) return color;
   }
   return 'rgb(255,255,255)';
 }
 const seed = [
   ...root.querySelectorAll('section,article,figure,form,pre,code,'+gridSelector+','+mediaSelector+
     ',[role="tabpanel"],[class*="preview" i],[class*="demo" i],[class*="card" i],[class*="terminal" i]'),
 ].slice(0, 4400);
 const elements = new Set(seed);
 const calendarLabel = /^(?:\d{1,2}:\d{2}(?:\s*(?:am|pm))?|mon|tue|wed|thu|fri|sat|sun)$/i;
 const passiveCalendar = [...root.querySelectorAll('span,li,time')].slice(0,6000)
   .filter(e=>!e.children.length && calendarLabel.test((e.innerText || '').trim())).slice(0,180);
 const anchors = [...passiveCalendar, ...root.querySelectorAll(controlSelector+','+gridSelector+','+mediaSelector+
   ',pre,[data-day],[aria-label*="calendar" i]')];
 for (const e of anchors.slice(0, 2000)) {
   if (!visible(e) || e.closest(chrome+','+privateRegion)) continue;
   for (let parent=e.parentElement, depth=0; parent && parent!==root && depth<5;
        parent=parent.parentElement,depth++) elements.add(parent);
 }

 const candidates = [];
 for (const node of elements) {
   if (!node.matches('section,article,figure,div,form,pre,code,details,'+
        gridSelector+','+mediaSelector+', [role="tabpanel"]') ||
       !visible(node) || node.closest(chrome+','+privateRegion)) continue;
   const r = rectangle(node);
   if (r.width < 145 || r.height < 63 || r.width*r.height < 12000 ||
       r.x < -2 || r.y < 0 || r.x+r.width > innerWidth+2 || r.y+r.height > maxY ||
       r.height > innerHeight * (node.matches(mediaSelector) ? 1.35 : 1.1) ||
       r.width / r.height < .5 || r.width / r.height > 2.4) continue;
   const own = String(node.innerText || '').trim().slice(0, 3200);
   const visibleControls = bits(node,controlSelector,r,54);
   const controls = visibleControls.filter(e => !bait.test(label(e)) &&
     !/^(?:learn more|get started|contact|sign up|sign in|read more)$/i.test(label(e)));
   const topLinks = r.y < 80 ? bits(node,'a[href]',r,16).length : 0;
   if (topLinks >= 4 && topLinks > controls.length) continue;
   const text = own.replace(/\s+/g,' ');
   const timeLabel = /^\d{1,2}:\d{2}(?:\s*(?:am|pm))?$/i;
   const times = controls.filter(e=>timeLabel.test(label(e))).length;
   const timeText = bits(node,'span,time,li,div',r,100)
     .filter(e=>e.children.length===0 && !e.matches('time') && !e.closest(controlSelector) &&
       timeLabel.test(label(e))).length;
   const dateText = /^(?:[1-9]|[12]\d|3[01])$/;
   const dateButtons = controls.filter(e => dateText.test(label(e))).length;
   const passiveDates = bits(node,'span,div,li,td',r,120)
     .filter(e=>e.children.length===0 && !e.closest(controlSelector) && dateText.test(label(e)));
   const dateLabels = passiveDates.length;
   const weekdays = new Set((text.match(/\b(?:mon(?:day)?|tue(?:sday)?|wed(?:nesday)?|thu(?:rsday)?|fri(?:day)?|sat(?:urday)?|sun(?:day)?)\b/gi) || [])
     .map(day=>day.slice(0,3).toLowerCase())).size;
   const calendar = dateButtons + dateLabels >= 7 &&
     (weekdays >= 3 || passiveDates.filter(e=>e.hasAttribute('data-day')).length >= 7);
   const nearbyMeme = [node.parentElement,node.parentElement?.parentElement].some(e=>{
     if (!e || rectangle(e).width > r.width * 2.5) return false;
     const surroundingText = (e.innerText || '').slice(0,400);
     return /rick\s*roll/i.test(surroundingText) &&
       /rick astley|never (?:gonna )?give you up/i.test(surroundingText);
   });
   const grid = node.matches(gridSelector) ? node : bits(node,gridSelector,r,4)[0];
   const cells = grid ? bits(grid,'td,th,[role="gridcell"],[role="columnheader"]',r,75).length : 0;
   const codeBlock = node.matches('pre,code') ? node : bits(node,'pre,code',r,12)[0];
   const code = !!codeBlock && label(codeBlock).length >= 8 &&
     /[\w][ \n=:{(.]|^[$>~]/.test(codeBlock.innerText || '');
   const media = (node.matches(mediaSelector) ? [node] : bits(node,mediaSelector,r,30))
     .filter(substantialMedia).sort((a,b)=>{
       const ar=rectangle(a), br=rectangle(b);
       return br.width*br.height-ar.width*ar.height;
     })[0];
   const mr = media && rectangle(media);
   const mediaArea = mr ? Math.round(mr.width * mr.height) : 0;
   const mediaFill = mediaArea / (r.width*r.height);
   const heading = bits(node,'h1,h2,h3,h4,figcaption',r,10)[0];
   const surrounding = node.closest('section,article,[role="tabpanel"]');
   const sectionHeading = surrounding?.querySelector('h1,h2,h3,h4,figcaption');
   const contextualName = label(sectionHeading || node);
   const name = calendar ? label(heading || node).match(/^(?:[A-Za-z]+ \d{4})/)?.[0] ||
     'Scheduling calendar' : label(heading || media || node) || contextualName;
   const hint = media && mediaLabel(media);
   const mediaUrl = media && mediaSource(media);
   const namedProductMedia = !!media && liveProduct.test(hint);
   const visiblePlayback = !!media && media.matches('video') && mediaUrl?.origin === location.origin;
   const productMedia = !!media && mediaFill >= .30 && !stock.test(hint) && !bait.test(name) &&
     (namedProductMedia || visiblePlayback || !media.matches('canvas,svg') &&
       (preview.test(hint) || preview.test(contextualName)));
   const scheduling = !nearbyMeme && (times >= 2 && controls.length >= 3 || calendar ||
     timeText >= 3 && bookingText.test(text) && !bait.test(text));
   const stateControls = controls.filter(e =>
     e.matches('[role="tab"],[role="switch"],[role="checkbox"],[role="radio"],[aria-pressed],input,select,textarea'));
   const widget = scheduling || stateControls.length >= 2 && controls.length >= 3;
   const pricing = price.test(text) && (billing.test(text) ||
     /\b(?:pricing|tier|plan)\b/i.test(text) && bits(node,'li,[role="listitem"]',r,10).length >= 2);

   if (!pricing && !code && cells < 6 && !widget && !productMedia) continue;
   const selector = path(node);
   if (!selector) continue;
   const sample = heading || controls[0] || codeBlock || passiveDates[0] || node;
   const front = luminance(getComputedStyle(sample).color);
   const back = luminance(background(sample));
   const targets = controls.filter(e=>e.matches(targetSelector) ||
       scheduling && e.matches('button') && (/(?:\b\d{1,2}:\d{2}\b|^(?:[1-9]|[12]\d|3[01])$)/.test(label(e))))
     .filter(e=>!e.disabled && !e.form && !e.closest('form,a,[aria-disabled="true"]') &&
       !(e.matches('button') && e.type==='submit' && e.hasAttribute('type')))
     .map(e=>({selector:path(e), rect:rectangle(e), label:label(e),
       role:e.getAttribute('role') || e.type || e.localName}))
     .filter(target=>target.selector && target.label).slice(0,35);
   candidates.push({
     selector, label:name, kind:cells>=6?'data':scheduling?'widget':code?'code':
       widget?'widget':productMedia?'media':'value',
     rect:r, controls:controls.length, state_controls:stateControls.length,
     date_buttons:dateButtons, date_labels:dateLabels, times:times+timeText, weekdays, cells, code,
     calendar,
     media_area:mediaArea, media_fill:mediaFill, named_product_media:namedProductMedia,
     media_own:node===media,
     product_media:productMedia, pricing, word_count:text.split(/\s+/).filter(Boolean).length,
     media_kind:media?.localName || null, font_px:primaryFont(node,r), viewport,
     contrast:(Math.max(front,back)+.05)/(Math.min(front,back)+.05),
     distractions:nearbyMeme || bait.test(name) || bait.test(text.slice(0,150)) && !scheduling,
     targets,
   });
   if (candidates.length >= 480) break;
 }
 return candidates;
}"""


def discover_candidates(page) -> list[dict]:
    """Measure DOM regions in CSS document coordinates in one browser evaluation."""
    return page.evaluate(_PRODUCT_EVIDENCE_JS)


def score_candidates(candidates: list[dict], *, include_unreadable: bool = False) -> list[dict]:
    """Rank evidence, retaining below-floor DOM subjects only for diagnostics."""
    ranked = []
    for candidate in candidates:
        rect = candidate["rect"]
        width, height = rect["width"], rect["height"]
        if width <= 0 or height <= 0 or not .5 <= width / height <= 2.4:
            continue
        kind = candidate["kind"]
        font = candidate["font_px"]
        # Embedded text cannot be measured via the parent DOM. Its actual
        # pixels must receive an explicit contact-sheet readability review.
        native_media = kind == "media" and candidate["media_fill"] >= .60
        projected_font = round(font * min(390 / width, (390 * 9 / 16) / height), 1) if font else None
        below_floor = not native_media and (projected_font is None or projected_font < 14)
        if below_floor and not include_unreadable:
            continue
        signals = []
        score = 0.0
        if kind in {"widget", "data"}:
            signals.append(f'{candidate["controls"]} visible controls')
            score += 35 + min(12, candidate["controls"] * .5 + candidate["state_controls"])
            if candidate["date_buttons"] + candidate["date_labels"] >= 7:
                signals.append(f'{candidate["date_buttons"] + candidate["date_labels"]} date cells')
                score += 12
            if candidate["times"] >= 2:
                signals.append(f'{candidate["times"]} time labels')
                score += 10
            if candidate["cells"] >= 6:
                signals.append(f'{candidate["cells"]} visible grid cells')
                score += min(15, candidate["cells"] * .4)
        if kind == "code":
            signals.append("visible code or terminal block")
            score += 30
        if candidate["product_media"]:
            signals.append(f'{candidate["media_area"]:,} px² product preview')
            score += (25 + min(7, candidate["media_area"] / 45000)) * candidate["media_fill"]
            if candidate["named_product_media"]:
                score += 7
            if candidate["media_kind"] == "iframe":
                score += 16
            elif candidate["media_kind"] == "video":
                score += 12
            if candidate["media_own"]:
                score += 1
        if candidate["pricing"]:
            signals.append("visible pricing with tier terms")
            score += 15
        if candidate["distractions"]:
            signals.append("distraction text")
            score -= 40
        coverage = width * height / math.prod(candidate["viewport"])
        score += min(7, max(0, candidate["contrast"] - 2))
        score -= max(0, coverage - .42) * 26
        score -= max(0, candidate["word_count"] - 70) * .09
        score = round(score, 2)
        if score <= 0:
            continue
        readability = "dom_estimate"
        if native_media:
            readability = "visual_review_required"
        elif below_floor:
            readability = "below_floor"
            measurement = f"{projected_font:g}px" if projected_font is not None else "unmeasurable"
            signals.append(f"primary text {measurement} at 390px, minimum 14px")
        ranked.append({
            **candidate,
            "score": score,
            "reason": ", ".join(signals) + f" (score={score:g})",
            "projected_font_px": None if native_media else projected_font,
            "readability": readability,
            "product_evidence": not below_floor and kind in {"widget", "data", "code", "media"},
        })
    return sorted(ranked, key=lambda c: (-c["score"], c["rect"]["y"], c["selector"]))
