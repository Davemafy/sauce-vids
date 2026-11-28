"""General UI primitives for public, explicitly browser-local sample demos.

Authorization is separate from DOM semantics. No account, form, consent, data
submission or remote operation is admitted. Before any primitive executes,
the disposable browser is disconnected; existing capture/replay is retained.
"""
import re,json,time
import cv2
import numpy as np
from backend.curious_sequence import safe_label,assert_local
from backend.source_action_preflight import visible_authentication_barrier,image_change

LOCAL=re.compile(r"(?:runs?|works?|processed|processing|stays?) (?:entirely |fully |locally )?(?:in|on|inside) your browser|browser.only|browser.local|client.side|nothing (?:leaves|is uploaded|is saved or sent)|no (?:network requests|server|backend)|no data leaves",re.I)
SAMPLE=re.compile(r"\b(?:demo|sample data|example data|illustrative data|playground|sandbox)\b",re.I)
EXTERNAL=re.compile(r"\b(?:buy|pay|purchase|checkout|subscribe|login|log in|sign in|sign up|register|account|password|token|secret|credential|permission|consent|cookie|privacy|terms|send|submit|publish|share|invite|join|connect|sync|download|upload|export|import|install|delete|remove|reset|run|execute|api key|contact|book|schedule|email|phone|message|collaborat\w*)\b",re.I)
SECRET=re.compile(r"(?i)(?:[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}|(?:sk-|AIza)[A-Za-z0-9_-]{15,}|bearer\s+\S+)")
SCAN=r"""(pick)=>{
 const norm=s=>(s||'').trim().replace(/\s+/g,' ');
 const box=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}};
 const hit=e=>{let r=box(e),h=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return r.width>=8&&r.height>=8&&r.x>=0&&r.y>=0&&r.x+r.width<=innerWidth+1&&r.y+r.height<=innerHeight+1&&h&&e.contains(h)&&e.checkVisibility()};
 const blocked='form,a[href],nav,header,footer,[role=navigation],[role=dialog],dialog,[aria-modal=true],[inert],[data-private],[data-secret],[data-sensitive]';
 const rows=[],hits=[];
 for(const e of [...document.querySelectorAll('button,[role=button],[role=tab]')].slice(0,300)){
  if(!hit(e)||e.closest(blocked)||e.form||e.disabled||e.getAttribute('aria-disabled')==='true'||e.getAttribute('aria-selected')==='true')continue;
  if(e.tagName!=='BUTTON'&&e.getAttribute('tabindex')==='-1')continue;
  const name=norm(e.getAttribute('aria-label')||e.innerText||e.getAttribute('title'));
  if(!name||name.length>100||e.querySelector('input,textarea,select,[contenteditable=true]'))continue;
  const parent=e.closest('section,article,[role=region],[role=group],[role=tablist],main');
  const context=parent?norm(parent.getAttribute('aria-label')||parent.querySelector('h1,h2,h3,h4')?.innerText).slice(0,100):'';
  const key=JSON.stringify([e.tagName,e.getAttribute('role')||'',name,context]);
  const row={key,label:name,group:context||'Local sample workflow',rect:box(e)};
  rows.push(row);if(key===pick)hits.push(e);
 }
 return pick?(hits.length===1?hits[0]:null):rows;
}"""

def admitted(page):
    if visible_authentication_barrier(page):return False
    if page.locator('form:visible,input:visible,textarea:visible,select:visible,[contenteditable=true]:visible,[data-private]:visible,[data-secret]:visible,[data-sensitive]:visible,[role=dialog]:visible,dialog:visible,[aria-modal=true]:visible,iframe:visible').count():return False
    text=page.locator('body').inner_text(timeout=1800)[:24000]
    return bool(LOCAL.search(text) and SAMPLE.search(text))

def scan(page):
    if not admitted(page):return []
    rows=page.evaluate(SCAN,None)
    return [r for r in rows if safe_label(r['label']) and safe_label(r['group']) and not EXTERNAL.search(r['label']) and not EXTERNAL.search(r['group']) and not SECRET.search(r['label']) and not SECRET.search(r['group']) and sum(x['key']==r['key'] for x in rows)==1]

def primitives(page):
    return [{'kind':'option','control':'local-primitive','operation':'click','key':r['key'],'label':r['label'],'group':r['group'],'source_context':'disconnected public sample'} for r in scan(page)[:48]]

def locate(page,action):
    rows=[r for r in scan(page) if r['key']==action['key'] and r['label']==action['label'] and r['group']==action['group']]
    if len(rows)!=1:raise ValueError('Local primitive identity or admission changed')
    h=page.evaluate_handle(SCAN,action['key']).as_element()
    if h is None:raise ValueError('Local primitive obstructed')
    return h

def panel(page,action):
    h=locate(page,action)
    rect=h.bounding_box()
    size=page.viewport_size
    return {'x':0,'y':0,'width':size['width'],'height':size['height'],'primitive_target':rect}

def isolate(page):
    # Existing customer contexts block service workers, WebSockets, downloads
    # and nonpublic destinations. Keep a second deny-all route after disconnect.
    if getattr(page.context,'_sauce_sample_isolated',False):return
    page.context.route('**/*',lambda route:route.abort('blockedbyclient'))
    page.route('**/*',lambda route:route.abort('blockedbyclient'))
    page.context.set_offline(True)
    page.context._sauce_sample_isolated=True

def apply(page,url,action,click):
    locate(page,action)
    isolate(page)
    h=locate(page,action)
    click(h,action['label'])
    assert_local(page,url)
    if not admitted(page):raise ValueError('Local sample admission lost after action')

def verify(page,url,before,old,snapshot):
    from backend.customer_story import pixels,WeakVisualOutcome,StoryRejected
    target=old['primitive_target'];a=pixels(before)
    last=None
    for _ in range(3):
        page.wait_for_timeout(500);assert_local(page,url)
        if not admitted(page):raise StoryRejected('Local sample admission lost before proof')
        after=snapshot(page);t=time.monotonic();page.wait_for_timeout(250)
        if not admitted(page):raise StoryRejected('Local sample admission lost before settled proof')
        settled=snapshot(page)
        b,c=pixels(after),pixels(settled)
        if image_change(b,c)>.025:continue
        mask=(np.max(cv2.absdiff(a,b),axis=2)>25).astype(np.uint8)
        # A selected button, hover, cursor or menu highlight is not a result.
        x,y,w,h=[round(target[k]) for k in ('x','y','width','height')]
        mask[max(0,y-24):y+h+24,max(0,x-24):x+w+24]=0
        mask[np.max(cv2.absdiff(b,c),axis=2)>25]=0
        mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,np.ones((2,2),np.uint8))
        count=int(mask.sum());last=(count/mask.size,after)
        if count<mask.size*.006:continue
        ys,xs=np.nonzero(mask)
        x0=max(0,int(np.quantile(xs,.01))-20);x1=min(mask.shape[1],int(np.quantile(xs,.99))+21)
        y0=max(0,int(np.quantile(ys,.01))-20);y1=min(mask.shape[0],int(np.quantile(ys,.99))+21)
        if (x1-x0)*(y1-y0)<mask.size*.035:continue
        delta=float(mask[y0:y1,x0:x1].mean())
        if delta<.035:continue
        return after,{'x':x0,'y':y0,'width':x1-x0,'height':y1-y0},delta,t
    if last is not None:raise WeakVisualOutcome(*last)
    raise StoryRejected('Local sample did not settle')
