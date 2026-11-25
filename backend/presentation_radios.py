"""Read-only presentation radio groups in a visible fixed public theme panel.

No arbitrary form controls, model-provided selectors, or account preferences.
"""
GROUPS={"Accent color","Gray color","Appearance","Radius","Scaling","Panel background"}
SCAN=r"""(allowed)=>{
 const rows=[];
 for(const e of document.querySelectorAll('input[type=radio]')){
  const g=e.closest('[role=group][aria-labelledby]'),l=e.closest('label');
  if(!g||!l||e.disabled||e.form||e.closest('form,a[href],[data-private],[data-secret],[data-sensitive],[inert]'))continue;
  const ids=g.getAttribute('aria-labelledby').split(/\s+/);
  if(ids.length!==1)continue;
  const title=document.getElementById(ids[0]);
  if(!title)continue;
  const group=title.innerText.trim();
  if(!allowed.includes(group)||!e.value.match(/^[a-zA-Z0-9][a-zA-Z0-9 %_-]{0,30}$/))continue;
  let panel=g;
  while(panel&&getComputedStyle(panel).position!=='fixed')panel=panel.parentElement;
  if(!panel)continue;
  const p=panel.getBoundingClientRect(),r=l.getBoundingClientRect();
  if(p.x<innerWidth*.65||p.width<innerWidth*.12||p.width>innerWidth*.35||p.height<innerHeight*.4||
     p.right>innerWidth+1||p.y<0||p.bottom>innerHeight+1||r.width<8||r.height<8||
     r.x<p.x||r.y<p.y||r.right>p.right||r.bottom>p.bottom||getComputedStyle(l).visibility!=='visible')continue;
  const hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);
  if(!hit||!l.contains(hit))continue;
  rows.push({group,label:e.value,checked:e.checked,panel:{x:p.x,y:p.y,width:p.width,height:p.height},e,l});
 }
 return rows;
}"""
def catalog(page):
    rows=page.evaluate(f"""allowed=>({SCAN})(allowed).map(({{e,l,...r}})=>r)""",sorted(GROUPS))
    groups={}
    for row in rows:
        if not row["checked"] and sum(x["group"]==row["group"] and x["label"]==row["label"] for x in rows)==1:
            groups.setdefault(row["group"],[]).append(row["label"])
    if len(groups)<2:return []
    result=[]
    for i in range(max(map(len,groups.values()),default=0)):
        for group,labels in groups.items():
            if i<len(labels):result.append({"id":f"v{len(result)}","kind":"option","control":"visible-radio","group":group,"label":labels[i]})
    return result[:60]
def handle(page,action):
    return page.evaluate_handle(f"""args=>{{const hits=({SCAN})(args.groups).filter(r=>r.group===args.group&&r.label===args.label&&!r.checked);return hits.length===1?hits[0].l:null}}""",
        {"groups":sorted(GROUPS),"group":action["group"],"label":action["label"]}).as_element()
def applied(page,action):
    rows=page.evaluate(f"""allowed=>({SCAN})(allowed).map(({{e,l,...r}})=>r)""",sorted(GROUPS))
    return sum(r["group"]==action["group"] and r["label"]==action["label"] and r["checked"] for r in rows)==1
def result_region(page):
    rows=page.evaluate(f"""allowed=>({SCAN})(allowed).map(({{e,l,...r}})=>r)""",sorted(GROUPS))
    if len({r["group"] for r in rows})<2:return None
    rects={tuple(r["panel"][k] for k in ("x","y","width","height")) for r in rows}
    if len(rects)!=1:return None
    x,y,w,h=next(iter(rects))
    # Independent large rendered product area, excluding fixed settings panel.
    # Header exclusion follows observed top of panel; no generated UI.
    viewport=page.viewport_size
    if not viewport or x<viewport["width"]*.65 or y>viewport["height"]*.2:return None
    return {"x":0,"y":int(y),"width":int(x)-8,"height":viewport["height"]-int(y)}
