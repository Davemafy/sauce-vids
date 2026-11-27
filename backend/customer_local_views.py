"""Guarded exclusive view/filter controls in named public demo regions."""
import re
from backend.curious_sequence import safe_label,assert_local

DEMO=re.compile(r"\b(demo|playground|preview)\b",re.I)
FILTER=re.compile(r"\b(filter|business unit|segment|category|period|range|metric|dimension|region|channel|view|department|product|status|timeframe)\b",re.I)
SCAN=r"""(pick)=>{
 const unsafe='form,a[href],nav,[role=navigation],[inert],[data-private],[data-secret],[data-sensitive]';
 const regions='[role=region][aria-label],[role=region][aria-labelledby],section:not([role])[aria-label],section:not([role])[aria-labelledby]';
 const name=e=>(e.getAttribute('aria-label')||((e.getAttribute('aria-labelledby')||'').split(/\s+/).map(id=>document.getElementById(id)).filter(Boolean).map(n=>n.innerText).join(' '))).trim().replace(/\s+/g,' ');
 const box=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}};
 const text=e=>(e.getAttribute('aria-label')||e.innerText||'').trim().replace(/\s+/g,' ');
 const visible=e=>{const r=box(e),h=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return r.x>=0&&r.y>=0&&r.x+r.width<=innerWidth&&r.y+r.height<=innerHeight&&r.width>=8&&r.height>=8&&h&&e.contains(h)};
 const rows=[],hits=[];
 for(const region of [...document.querySelectorAll(regions)].slice(0,32)){
  if(region.closest(unsafe)||!region.checkVisibility()||region.querySelector('input[type=password],[data-private],[data-secret],[data-sensitive]'))continue;
  const groups=[];
  for(const g of [...region.querySelectorAll('[role=group],[role=tablist]')].slice(0,32)){
   if(g.closest(unsafe)||g.closest(regions)!==region||!g.checkVisibility())continue;
   const kind=g.getAttribute('role')==='tablist'?'tab':'filter',state=kind==='tab'?'aria-selected':'aria-pressed';
   const nodes=[...g.querySelectorAll(kind==='tab'?'button[role=tab][aria-selected]':'button[aria-pressed]')].filter(e=>e.closest('[role=group],[role=tablist]')===g);
   if(nodes.length<2||nodes.length>16||nodes.some(e=>!e.checkVisibility()||e.disabled||e.form||e.closest(unsafe)||e.getAttribute('aria-disabled')==='true'||e.getAttribute('type')==='submit'||!['true','false'].includes(e.getAttribute(state))))continue;
   const labels=nodes.map(text);
   if(new Set(labels).size!==labels.length||nodes.filter(e=>e.getAttribute(state)==='true').length!==1)continue;
   const groupName=name(g);
   const key=kind+':'+(groupName||labels.slice().sort().join(' / '));
   groups.push({kind,name:groupName,key,rect:box(g),options:nodes.map(e=>({label:text(e),selected:e.getAttribute(state)==='true',visible:!!visible(e)}))});
   if(pick&&pick.region===name(region)&&pick.group===key)
    hits.push(...nodes.filter(e=>text(e)===pick.label&&e.getAttribute(state)==='false'&&visible(e)));
  }
  rows.push({label:name(region),rect:box(region),groups});
 }
 return pick?(hits.length===1?hits[0]:null):rows;
}"""
def need(ok,msg):
    if not ok:raise ValueError(msg)
def scan(page):
    result=[]
    for r in page.evaluate(SCAN,None):
        if not DEMO.search(r["label"]) or not safe_label(r["label"]):continue
        groups=[]
        for g in r["groups"]:
            if not all(safe_label(o["label"]) for o in g["options"]):continue
            if g["kind"]=="filter" and (not safe_label(g["name"]) or not FILTER.search(g["name"])):continue
            if g["name"] and not safe_label(g["name"]):continue
            if len(g["key"])>140:continue
            groups.append(g)
        groups=[g for g in groups if sum(x["key"]==g["key"] for x in groups)==1]
        if len(groups)>=2:result.append({**r,"groups":groups})
    return [r for r in result if sum(x["label"]==r["label"] for x in result)==1]
def candidate(page):
    v=page.viewport_size
    if not v:return None
    rows=[r for r in scan(page) if r["rect"]["width"]>=v["width"]*.40 and
          v["height"]*.35<=r["rect"]["height"]<=v["height"]*.92 and
          r["rect"]["x"]>=0 and r["rect"]["x"]+r["rect"]["width"]<=v["width"]]
    return rows[0] if len(rows)==1 else None
def region_for(page,label):
    rows=[r for r in scan(page) if r["label"]==label]
    return rows[0] if len(rows)==1 else None
def result_region(page,label):
    r=region_for(page,label);v=page.viewport_size
    if not r or not v:return None
    b=r["rect"]
    if b["x"]<0 or b["y"]<0 or b["x"]+b["width"]>v["width"]+1 or b["y"]+b["height"]>v["height"]+1:return None
    # Keep every control group outside the outcome proof. A conventional
    # toolbar earns the existing below-controls rectangle; a side-by-side
    # demo earns the larger disjoint side. No guessed selector or UI pixels.
    x=round(b['x']+8);right=round(b['x']+b['width']-8)
    top=round(b['y']+8);bottom=round(b['y']+b['height']-8)
    g=[a['rect'] for a in r['groups']]
    below=round(max([b['y']]+[a['y']+a['height'] for a in g])+8)
    left=round(min([b['x']+b['width']]+[a['x'] for a in g])-8)
    after=round(max([b['x']]+[a['x']+a['width'] for a in g])+8)
    candidates=[(x,below,right,bottom),(after,top,right,bottom),(x,top,left,bottom)]
    candidates=[a for a in candidates if a[2]>a[0] and a[3]>a[1]]
    if not candidates:return None
    x,y,right,bottom=max(candidates,key=lambda a:(a[2]-a[0])*(a[3]-a[1]))
    if (right-x)*(bottom-y)<v['width']*v['height']*.18:return None
    return {'x':x,'y':y,'width':right-x,'height':bottom-y,'local_view_region':label}

def prepare(page,url,setup=None):
    r=candidate(page)
    if not r or (setup and setup.get("region")!=r["label"]):return None
    v=page.viewport_size;b=r["rect"];label=r["label"];initial=page.evaluate("()=>scrollY");shift=round(b["y"]-(v["height"]-b["height"])/2)
    if abs(shift)>6000:return None
    if abs(shift)>3:
        page.evaluate("(dy)=>window.scrollBy({top:dy,behavior:'instant'})",shift)
        page.wait_for_timeout(450);assert_local(page,url)
    r=candidate(page)
    if not r or r["label"]!=label or not result_region(page,r["label"]):
        page.evaluate("(y)=>window.scrollTo({top:y,behavior:'instant'})",initial)
        assert_local(page,url)
        return None
    now={"kind":"local-demo-views","region":r["label"]}
    return now if not setup or setup==now else None
def catalog(page,setup):
    r=region_for(page,setup["region"])
    if not r or not result_region(page,r["label"]):return []
    rows=[]
    for g in r["groups"]:
        for o in g["options"]:
            if not o["selected"] and o["visible"]:
                rows.append({"id":f"lv{len(rows)}","kind":"option","control":"local-demo-view",
                             "group":g["key"],"label":o["label"],"region":r["label"]})
    return rows[:32] if len({a["group"] for a in rows})>=2 else []
def locate(page,action):
    r=region_for(page,action["region"])
    need(r is not None,"Local demo surface lost")
    groups=[g for g in r["groups"] if g["key"]==action["group"]]
    need(len(groups)==1,"Local view group changed")
    choices=[o for o in groups[0]["options"] if o["label"]==action["label"] and not o["selected"] and o["visible"]]
    need(len(choices)==1,"Observed local option no longer inactive and visible")
    handle=page.evaluate_handle(SCAN,{k:action[k] for k in ("region","group","label")}).as_element()
    need(handle is not None,"Local option identity changed")
    return handle
def apply(page,url,action,click):
    click(locate(page,action),action["label"]);assert_local(page,url)
    r=region_for(page,action["region"])
    need(r is not None,"Local demo surface lost after click")
    g=[g for g in r["groups"] if g["key"]==action["group"]]
    need(len(g)==1 and sum(o["selected"] and o["label"]==action["label"] for o in g[0]["options"])==1,
         "Local option state was not observed")
