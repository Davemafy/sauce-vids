"""Optional, witnessed component detail; never a substitute for whole-result proof."""
import cv2
import numpy as np

# Only complete semantic regions with a visible heading. No model selectors.
QUERY = r"""() => {
 const rows=[];
 for(const e of [...document.querySelectorAll('[data-slot="card"],article,section,[role="region"]')].slice(0,120)){
   if(e.closest('form,[data-private],[data-secret],[data-sensitive],[inert]'))continue;
   const h=e.querySelector('h1,h2,h3,h4,[data-slot="card-title"]');
   if(!h)continue;
   const label=(h.innerText||'').trim().replace(/\s+/g,' ');
   const r=e.getBoundingClientRect(),hr=h.getBoundingClientRect();
   if(!label||label.length>80||r.width<180||r.height<120||r.left<0||r.top<0||r.right>innerWidth||r.bottom>innerHeight||
     hr.left<r.left||hr.top<r.top||hr.right>r.right||hr.bottom>r.bottom)continue;
   const points=[[r.left+20,r.top+20],[r.right-20,r.top+20],[r.left+20,r.bottom-20],[r.right-20,r.bottom-20],[hr.x+hr.width/2,hr.y+hr.height/2]];
   if(!points.every(([x,y])=>e.contains(document.elementFromPoint(x,y))))continue;
   rows.push({label,rect:{x:r.x,y:r.y,width:r.width,height:r.height}});
 }
 return rows;
}"""

def contained(inner,outer):
    return (inner["x"]>=outer["x"] and inner["y"]>=outer["y"]
            and inner["x"]+inner["width"]<=outer["x"]+outer["width"]
            and inner["y"]+inner["height"]<=outer["y"]+outer["height"])

def _observed_components(page,box):
    from backend.curious_sequence import safe_label
    from backend.story_discovery import focused_route_allowed
    from backend.source_action_preflight import same_local_tab_route
    from urllib.parse import urljoin,urlsplit
    import re
    roots=[(page,{"x":0,"y":0,"width":page.viewport_size["width"],"height":page.viewport_size["height"]},None)]
    for loc in page.locator('iframe[title]:visible').all()[:8]:
        title=(loc.get_attribute("title") or "").lower()
        declared=urljoin(page.url,loc.get_attribute("src") or "")
        if (title not in ("preview","product preview","live preview") or
            not focused_route_allowed(declared,page.url.split("?")[0]) or
            not re.match(r"^/previews?(?:/|$)",urlsplit(declared).path)):continue
        handle=loc.element_handle()
        frame=handle.content_frame() if handle else None
        bounds=loc.bounding_box()
        if frame and bounds and same_local_tab_route(declared,frame.url):
            # Use the actual content box, not iframe border geometry.
            content=loc.evaluate("e=>({x:e.getBoundingClientRect().x+e.clientLeft,y:e.getBoundingClientRect().y+e.clientTop,width:e.clientWidth,height:e.clientHeight})")
            if content["width"]>0 and content["height"]>0 and loc.evaluate("e=>getComputedStyle(e).transform==='none'"):
                roots.append((frame,content,loc))
    rows=[]
    for root,offset,iframe in roots:
        for item in root.evaluate(QUERY):
            r=item["rect"]
            if not safe_label(item["label"]):continue
            if not contained(r,{"x":0,"y":0,"width":offset["width"],"height":offset["height"]}):continue
            r={**r,"x":r["x"]+offset["x"],"y":r["y"]+offset["y"]}
            # Inner rounding avoids claiming pixels beyond the actual card.
            x,y=int(np.ceil(r["x"])),int(np.ceil(r["y"]))
            r={"x":x,"y":y,"width":int(np.floor(r["x"]+r["width"]))-x,"height":int(np.floor(r["y"]+r["height"]))-y}
            fraction=r["width"]*r["height"]/(box["width"]*box["height"])
            if .025<=fraction<=.45 and contained(r,box):
                if iframe is not None and not iframe.evaluate("""(e,r)=>[[r.x+20,r.y+20],[r.x+r.width-20,r.y+20],[r.x+20,r.y+r.height-20],[r.x+r.width-20,r.y+r.height-20],[r.x+r.width/2,r.y+r.height/2]].every(([x,y])=>document.elementFromPoint(x,y)===e)""",r):continue
                rows.append({"label":item["label"],"rect":r})
    return [r for r in rows if sum(x["label"]==r["label"] for x in rows)==1][:24]

def observed_components(page,box):
    from playwright.sync_api import Error
    try:return _observed_components(page,box)
    except Error:return [] # detached optional preview; original outcome still verified independently

def select_component(before,after,old,new,box):
    """Require same named complete DOM component and substantial real pixel change."""
    if before.shape!=after.shape:return None
    candidates=[]
    for item in new:
        r=item["rect"]
        prior=next((x["rect"] for x in old if x["label"]==item["label"]),None)
        if prior is None or not contained(r,box):continue
        x,y,w,h=(r[k] for k in ("x","y","width","height"))
        # Avoid calling a reflow/cross-card replacement a local transformation.
        ix=max(0,min(x+w,prior["x"]+prior["width"])-max(x,prior["x"]))
        iy=max(0,min(y+h,prior["y"]+prior["height"])-max(y,prior["y"]))
        if ix*iy<.65*max(w*h,prior["width"]*prior["height"]):continue
        a,b=before[y:y+h,x:x+w],after[y:y+h,x:x+w]
        if not a.size or a.shape!=b.shape:continue
        coarse=float(np.mean(np.max(cv2.absdiff(cv2.resize(a,(128,64)),cv2.resize(b,(128,64))),axis=2)>12))
        if coarse>=.04:candidates.append((coarse,item))
    if not candidates:return None
    score,item=max(candidates,key=lambda v:v[0])
    return {"label":item["label"],"rect":item["rect"],"changedFraction":round(score,5)}
