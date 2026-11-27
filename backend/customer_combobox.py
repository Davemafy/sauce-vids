"""Local, observed presentation comboboxes in a replayable public drawer."""
import re
from backend.curious_sequence import safe_label,assert_local

OPENERS={"theme customizer","theme designer","customize theme","open the designer"}
GROUPS={"style","theme","base color","accent color","gray color","appearance","radius","scaling","font","heading","icon library","presets","layout","typography"}
BOX=r"""e=>{const r=e.getBoundingClientRect(),h=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return r.width>=8&&r.height>=8&&r.x>=0&&r.y>=0&&r.right<=innerWidth&&r.bottom<=innerHeight&&h&&e.contains(h)&&!e.disabled&&!e.form&&!e.closest('form,a[href],[data-private],[data-secret],[data-sensitive],[inert]')&&e.getAttribute('aria-disabled')!=='true'}"""
def need(ok,msg):
    if not ok:raise ValueError(msg)

def opener(page,label=None):
    rows=[]
    for e in page.locator('button[type=button][aria-haspopup=dialog][aria-expanded=false][aria-controls]').all()[:40]:
        name=(e.get_attribute("aria-label") or " ".join(e.inner_text().split())).strip()
        if name.lower() in OPENERS and (label is None or name==label) and e.is_visible() and e.evaluate(BOX):
            rows.append((name,e.element_handle()))
    return rows[0] if len(rows)==1 else None

def active_panel(page):
    rows=page.locator('[role=tabpanel]:visible').evaluate_all("""es=>es.filter(e=>!e.closest('[role=dialog],form,[data-private],[data-secret],[data-sensitive]')).map(e=>{let r=e.getBoundingClientRect();return {id:e.id,x:r.x,y:r.y,width:r.width,height:r.height}}).filter(r=>r.id&&r.width>=600&&r.height>=300&&r.y<innerHeight&&r.y+r.height>0)""")
    return max(rows,key=lambda r:r["width"]*r["height"],default=None)

def prepare(page,url,setup=None):
    if page.locator('[role=dialog]:visible').count():return None
    chosen=opener(page,setup.get("opener") if setup else None)
    if not chosen:return None
    name,_=chosen
    region=active_panel(page)
    if not region:return None
    # Initial viewport selection is before the source clock, not a fabricated action.
    if region["y"]>200:
        initial=page.evaluate("()=>scrollY")
        shift=min(900,max(0,round(region["y"]-150)))
        page.evaluate("(dy)=>window.scrollBy({top:dy,behavior:'instant'})",shift)
        page.wait_for_timeout(350)
        chosen=opener(page,name)
        if not chosen:
            page.evaluate("(y)=>window.scrollTo({top:y,behavior:'instant'})",initial)
            return None
    name,h=chosen;ident=h.get_attribute("aria-controls")
    need(ident and re.fullmatch(r"[\w:-]{1,160}",ident),"No bound presentation drawer")
    h.click(timeout=3500);page.wait_for_timeout(500);assert_local(page,url)
    d=drawer(page)
    need(d is not None and d.get_attribute("id")==ident,"No unique local presentation drawer")
    need(result_region(page) is not None,"No visible product surface outside drawer")
    return {"kind":"presentation-combobox-drawer","opener":name}

def drawer(page):
    q=page.locator('[role=dialog]:visible')
    if q.count()!=1:return None
    d=q.first;r=d.bounding_box();v=page.viewport_size
    if not r or not v or r["x"]<v["width"]*.6 or r["width"]>v["width"]*.4 or r["height"]<v["height"]*.65:return None
    if d.locator('form,input[type=password],[data-private],[data-secret],[data-sensitive]').count():return None
    return d

def result_region(page):
    d=drawer(page);r=active_panel(page)
    if d is None or not r:return None
    bounds=d.bounding_box();v=page.viewport_size
    x=max(0,round(r["x"]));y=max(0,round(r["y"]))
    right=min(round(r["x"]+r["width"]),round(bounds["x"])-8,v["width"])
    bottom=min(round(r["y"]+r["height"]),v["height"])
    if right<=x or bottom<=y or (right-x)*(bottom-y)<v["width"]*v["height"]*.18:return None
    return {"x":x,"y":y,"width":right-x,"height":bottom-y,"combo_result_id":r["id"]}

def triggers(page):
    d=drawer(page)
    if d is None:return []
    rows=[]
    for e in d.locator('button[type=button][role=combobox][aria-controls][aria-expanded=false]').all()[:24]:
        if not e.is_visible() or not e.evaluate(BOX):continue
        group=e.evaluate("""e=>{const p=e.parentElement,l=[...p.children].filter(x=>x.tagName==='LABEL');return l.length===1?l[0].innerText.trim():e.getAttribute('aria-label')||''}""")
        if group.lower() not in GROUPS or not safe_label(group):continue
        rows.append((group,e.element_handle()))
    return [(g,h) for g,h in rows if h is not None and sum(x==g for x,_ in rows)==1]

def handle(page,group):
    hits=[h for g,h in triggers(page) if g==group]
    need(len(hits)==1,"Observed combobox no longer unique")
    return hits[0]

def open_list(page,url,group,click):
    h=handle(page,group);ident=h.get_attribute("aria-controls")
    need(ident and re.fullmatch(r"[\w:-]{1,160}",ident),"Unbound combobox")
    need(page.locator('[role=listbox]:visible').count()==0,"Existing listbox")
    click(h,None)
    scope=page.locator('[role=listbox]:visible')
    scope.first.wait_for(state="visible",timeout=3000)
    need(scope.count()==1 and scope.first.get_attribute("id")==ident,"Listbox identity changed")
    need(scope.locator("form,input,textarea,a[href],[data-private],[data-secret],[data-sensitive]").count()==0,"Sensitive listbox")
    assert_local(page,url)
    return scope

def options(scope):
    rows=[]
    for e in scope.locator('[role=option][aria-selected=false]:not([aria-disabled=true])').all()[:40]:
        if not e.is_visible() or not e.evaluate(BOX):continue
        label=" ".join(e.inner_text().split())
        if safe_label(label):rows.append((label,e.element_handle()))
    return [(l,h) for l,h in rows if h is not None and sum(x==l for x,_ in rows)==1]

def catalog(page,url):
    groups=[]
    for group,_ in triggers(page):
        scope=open_list(page,url,group,lambda e,_:e.click(timeout=3500))
        labels=[l for l,_ in options(scope)]
        page.keyboard.press("Escape");scope.wait_for(state="hidden",timeout=2500)
        assert_local(page,url)
        if labels:groups.append((group,labels))
    rows=[(g,ls[j]) for j in range(max((len(ls) for _,ls in groups),default=0)) for g,ls in groups if j<len(ls)]
    return [{"id":f"c{i}","kind":"option","control":"presentation-combobox","group":g,"label":l} for i,(g,l) in enumerate(rows[:60])]

def apply(page,url,action,click):
    group,label=action["group"],action["label"]
    scope=open_list(page,url,group,click)
    hits=[h for l,h in options(scope) if l==label]
    need(len(hits)==1,"Observed combobox option no longer unique")
    click(hits[0],label);scope.wait_for(state="hidden",timeout=3000)
    assert_local(page,url)
    need(" ".join(handle(page,group).inner_text().split())==label,"Selected combobox value not observed")
