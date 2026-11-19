"""Sauce Basic page quality helpers. Conservative fail-visible policies.

Deterministic, no AI. Do not mutate product UI beyond the existing
presentation-only opt-in support-widget cleanup; no consent acceptance.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import hypot

CHAT_SELECTORS = (
    "#intercom-container", ".crisp-client", "#hubspot-messages-iframe-container",
    ".woot-widget-bubble", ".woot-widget-holder", ".woot--bubble-holder",
)
SKELETON_SELECTORS=(
    "[aria-busy='true']", "[data-loading='true']", "[data-state='loading']",
    "[class*='skeleton' i]", "[class*='placeholder-loading' i]",
)
CONSENT_SELECTORS=(
    "[id*='cookie' i]", "[class*='cookie-banner' i]",
    "[id*='consent' i]", "[aria-label*='cookie' i]",
)
TEXT_BOXES_JS=r"""() => {
  const boxes=[];
  const root=document.body;
  if (!root) return boxes;
  const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
  let node;
  while((node=walker.nextNode()) && boxes.length<650){
    const txt=(node.textContent||'').trim();
    if(!txt || txt.length>1500 || !node.parentElement) continue;
    const p=node.parentElement, css=getComputedStyle(p);
    if(css.display==='none' || css.visibility==='hidden' || Number(css.opacity)<.15)
      continue;
    const range=document.createRange();
    range.selectNodeContents(node);
    for (const rect of range.getClientRects()){
      if(rect.width<4 || rect.height<4 || rect.bottom<=0 || rect.top>=innerHeight
         || rect.right<=0 || rect.left>=innerWidth) continue;
      boxes.push({x:Math.max(0,rect.x),y:Math.max(0,rect.y),
                  w:Math.min(rect.width,innerWidth),h:Math.min(rect.height,innerHeight),
                  font:parseFloat(css.fontSize)||0});
    }
  }
  return boxes;
}"""
BLOCKER_JS=r"""(selectors) => {
  const shown=(e)=>{
    const s=getComputedStyle(e),r=e.getBoundingClientRect();
    return s.display!=='none' && s.visibility!=='hidden' && parseFloat(s.opacity)>.10
      && r.width>16 && r.height>12 && r.bottom>0 && r.top<innerHeight;
  };
  return Object.fromEntries(Object.entries(selectors).map(([name,ss])=>[
    name,[...document.querySelectorAll(ss)].filter(shown).slice(0,16)
       .map(e=>({selector:ss,tag:e.tagName.toLowerCase(),
          box:{x:e.getBoundingClientRect().x,y:e.getBoundingClientRect().y,
               w:e.getBoundingClientRect().width,h:e.getBoundingClientRect().height}}))
  ]));
}"""
READINESS_JS=r"""() => {
  const images=[...document.images].filter(e=>{
    const r=e.getBoundingClientRect();
    return r.width>20 && r.height>20 && r.bottom>0 && r.top<innerHeight;
  }).slice(0,100);
  const suspect=[...document.querySelectorAll(
    "[aria-busy='true'],[data-loading='true'],[data-state='loading'],[class*='skeleton' i]"
  )].filter(e=>{
    const s=getComputedStyle(e),r=e.getBoundingClientRect();
    return r.width>60&&r.height>20&&r.bottom>0&&r.top<innerHeight
      && s.display!=='none'&&s.visibility!=='hidden'
  });
  const height=Math.max(document.documentElement.scrollHeight,document.body.scrollHeight);
  return {scrollY,scrollHeight:height,
    viewportHeight:innerHeight,
    pendingImages:images.filter(e=>!e.complete || (e.currentSrc && e.naturalWidth===0)).length,
    visibleImages:images.length,
    visibleSkeletons:suspect.length,
    fontState:document.fonts.status,
    url:location.href};
}"""


def visible_text_boxes(page) -> list[dict]:
    return page.evaluate(TEXT_BOXES_JS)


def quality_scan(page) -> dict:
    """No assertions about full-page state from one viewport snapshot."""
    policy = {
        "chat": ",".join(CHAT_SELECTORS),
        "consent": ",".join(CONSENT_SELECTORS),
        "skeleton": ",".join(SKELETON_SELECTORS),
    }
    blockers=page.evaluate(BLOCKER_JS,policy)
    readiness=page.evaluate(READINESS_JS)
    status="clear"
    issues=[]
    if blockers["consent"]:
        issues.append("visible_consent_overlay")
    if blockers["chat"]:
        issues.append("visible_chat_overlay")
    if readiness["pendingImages"]:
        issues.append("incomplete_visible_images")
    if readiness["visibleSkeletons"]:
        issues.append("visible_skeleton")
    if issues:
        status="low_confidence"
    return {"status":status,"issues":issues,"readiness":readiness,
            "visible":{name:len(items) for name,items in blockers.items()}}


def overlaps_text(point:tuple[float,float], boxes:list[dict],
                  sprite_size:tuple[int,int]=(30,39), margin:int=6)->bool:
    x,y=point
    sw,sh=sprite_size
    # x/y is the arrow hotspot; body extends rightward and downward.
    # Slightly pessimistic bounding rectangle prevents text occlusion.
    a=(x-3-margin,y-3-margin,x+sw+margin,y+sh+margin)
    for b in boxes:
        bb=(b["x"],b["y"],b["x"]+b["w"],b["y"]+b["h"])
        if a[0]<bb[2] and a[2]>bb[0] and a[1]<bb[3] and a[3]>bb[1]:
            return True
    return False


def park_cursor(viewport:tuple[int,int], boxes:list[dict],
                preferred:tuple[float,float]|None=None) -> tuple[int,int]:
    """Return an in-viewport resting hotspot wholly outside text rectangles.

    Reject rather than falsely certifying a cursor-safe page when every
    candidate overlaps text. Prefer edge gutters; do not hide the pointer.
    """
    width,height=viewport
    candidates=[
        (18,height-62),(width-56,height-62),
        (18,round(height*.60)),(width-56,round(height*.60)),
        (18,round(height*.35)),(width-56,round(height*.35)),
        (round(width*.50),height-62),(18,96),(width-56,96),
    ]
    if preferred:
        candidates.insert(0,(int(preferred[0]),int(preferred[1])))
    for candidate in candidates:
        if not overlaps_text(candidate,boxes):
            return candidate
    raise RuntimeError("No verified safe idle-cursor position on this viewport")


def ensure_observable(page,*,max_attempts:int=3,interval_ms:int=180)->dict:
    """Fail-visible bounded checks. Does NOT infer all background loads done.

    Compare visible skeleton/image status and coarse document dimensions at
    controlled intervals. A stable DOM isn't proof of a settled CSS animation.
    """
    scans=[]
    for i in range(max_attempts):
        scan=quality_scan(page)
        scans.append(scan)
        if i+1<max_attempts:
            page.wait_for_timeout(interval_ms)
    heights=[s["readiness"]["scrollHeight"] for s in scans]
    stable=max(heights)-min(heights)<=2
    issues=sorted(set(x for s in scans for x in s["issues"]))
    if not stable:
        issues.append("layout_height_unstable")
    return {"confidence":"low" if issues else "provisional",
            "issues":issues,
            "height_stable":stable,
            "readiness":scans[-1]["readiness"],
            "policy":"no_auto_consent_acceptance"}

TEXT_OPACITY_JS=r"""() => {
  const rows=[];
  for(const [i,e] of [...document.querySelectorAll("main h1,main h2,main h3,article h1,article h2,article h3,section h1,section h2,section h3")].entries()){
    if(rows.length>=40)break;
    const r=e.getBoundingClientRect();
    if(r.width<32||r.height<12||r.bottom<=20||r.top>=innerHeight-20)continue;
    let opacity=1,n=e;
    for(let depth=0;n && depth<12;depth++,n=n.parentElement){
      const c=getComputedStyle(n);
      if(c.display==="none"||c.visibility==="hidden"){opacity=0;break;}
      opacity*=Number(c.opacity)||0;
    }
    rows.push({index:i,opacity:Math.round(opacity*1000)/1000,
               textLength:(e.innerText||"").trim().length});
  }
  return rows;
}"""


def settle_visible_text(page, *, checks:int=3, interval_ms:int=140)->dict:
    """Bounded evidence for active text fades at a stationary real scroll stop.

    Does NOT force final opacity or fabricate visual states. Intentionally
    translucent text may receive a low-confidence flag, not be recolored.
    """
    before=page.evaluate(TEXT_OPACITY_JS)
    movement=0.
    previous={r["index"]:r["opacity"] for r in before}
    samples=[before]
    for i in range(checks-1):
        page.wait_for_timeout(interval_ms)
        current=page.evaluate(TEXT_OPACITY_JS)
        current_map={r["index"]:r["opacity"] for r in current}
        movement=max((abs(previous[idx]-value) for idx,value
                      in current_map.items() if idx in previous),default=0.)
        samples.append(current)
        if movement<=.045 and i>0:
            break
        previous=current_map
    last=samples[-1]
    low=[x for x in last if x["textLength"]>=6 and .12<x["opacity"]<.72]
    issues=[]
    if movement>.045:
        issues.append("scroll_linked_text_not_settled")
    if low:
        issues.append("prominent_heading_low_opacity")
    return {"issues":issues,"heading_count":len(last),
            "low_opacity_headings":len(low),
            "opacity_change_last":round(movement,3),
            "wait_ms":(len(samples)-1)*interval_ms}

def settle_visible_images(page, *, timeout_ms:int=1300)->dict:
    """Give genuine visible images a bounded decode/retry opportunity.

    A failed or missing image stays an explicit low-confidence issue.
    Never replace website imagery with invented pixels or blank it out.
    """
    rounds=max(1,min(12,timeout_ms//150))
    for i in range(rounds):
        snapshot=quality_scan(page)
        if "incomplete_visible_images" not in snapshot["issues"]:
            return snapshot
        page.evaluate("""async () => {
          const imgs=[...document.images].filter(e=>{
            const r=e.getBoundingClientRect();
            return r.width>20&&r.height>20&&r.bottom>0&&r.top<innerHeight
              && (!e.complete||(e.currentSrc&&e.naturalWidth===0));
          }).slice(0,40);
          await Promise.race([
            Promise.all(imgs.map(e=>e.decode().catch(()=>{}))),
            new Promise(resolve=>setTimeout(resolve,100))
          ]);
        }""")
        if i<rounds-1:
            page.wait_for_timeout(50)
    return quality_scan(page)
