"""Operator-supplied offline synthetic workspace agent. No real site or auth access."""
import json,time,hashlib
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright,Error
from backend.product_explorer import CHROME
from backend.customer_browser_agent import DENY,SECRET
from backend.customer_story import shot,media
from backend.curious_interactive import parse

BASE="https://benchmark.example.com/"
SELECTOR="a[href],button,input,textarea,select,canvas"
CSP="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; form-action 'none'; frame-src 'none'; base-uri 'none'"
OBS=r"""()=>{
 const visible=e=>{let r=e.getBoundingClientRect(),s=getComputedStyle(e);return r.width>1&&r.height>1&&s.visibility==='visible'&&s.display!=='none'&&+s.opacity>0};
 const privateSel='[data-private],[data-secret],[data-sensitive],input[type=password],input[autocomplete=one-time-code],input[type=email],input[type=tel],input[type=file]';
 if([...document.querySelectorAll(privateSel)].some(visible))throw Error('Sensitive surface');
 return [...document.querySelectorAll('a[href],button,input,textarea,select,canvas')].flatMap((e,i)=>{
  if(!visible(e)||e.closest(privateSel+',form,[inert]')||e.disabled||e.readOnly||e.getAttribute('aria-disabled')==='true')return [];
  let r=e.getBoundingClientRect(),h=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);
  let name=(e.getAttribute('aria-label')||[...(e.labels||[])].map(l=>[...l.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent).join(' ')).join(' ')||e.innerText||'').trim().replace(/\s+/g,' ');
  let op=({A:'navigate',SELECT:'select',CANVAS:'drag',TEXTAREA:'type'}[e.tagName]|| (e.tagName==='BUTTON'&&e.type==='button'?'click':e.tagName==='INPUT'&&['text','search'].includes(e.type)?'type':null));
  if(!op||!name||name.length>120||(!h||!e.contains(h))&&op!=='navigate')return [];
  return [{id:'e'+i,name,allowed:op,rect:[r.x,r.y,r.width,r.height],href:op==='navigate'?e.getAttribute('href'):null,options:op==='select'?[...e.options].filter(o=>!o.disabled&&!o.parentElement.disabled).map(o=>o.label):[]}];
 });
}"""
def observe(page,docs):
    rows={}
    for r in page.evaluate(OBS):
        if DENY.search(r['name']) or SECRET.search(r['name']) or any(SECRET.search(o) for o in r['options']):continue
        if r['allowed']=='navigate' and urljoin(page.url,r['href'] or '') not in docs:continue
        rows[r['id']]=r
    state=page.locator('section,article').first.inner_text() if page.locator('section,article').count() else ''
    return {'elements':list(rows.values()),'result_regions':[],'result':state,'scroll_y':page.evaluate('()=>scrollY'),'path':page.url},rows

def act(page,docs,rows,c):
    op=c.get('operation')
    if op in ('scroll_up','scroll_down'):
        page.mouse.wheel(0,-360 if op=='scroll_up' else 360);page.wait_for_timeout(300);return True
    target=c.get('target')
    if not isinstance(target,str) or target not in rows or rows[target]['allowed']!=op:return False
    _,live=observe(page,docs);r=rows[target]
    if live.get(target)!=r:return False
    loc=page.locator(SELECTOR).nth(int(target[1:]))
    if op=='navigate':page.goto(urljoin(page.url,r['href']),wait_until='domcontentloaded',timeout=3000)
    elif op=='click':loc.click(timeout=2500)
    elif op=='select':
        value=c.get('value')
        if not isinstance(value,str) or r['options'].count(value)!=1:return False
        loc.select_option(label=value,timeout=2500)
        if loc.locator('option:checked').inner_text()!=value:return False
    elif op=='type':
        v=c.get('value')
        if not isinstance(v,str) or not 1<=len(v)<=120 or SECRET.search(v) or any(ord(ch)<32 for ch in v):return False
        loc.fill(v,timeout=2500)
        if loc.input_value()!=v:return False
    elif op=='drag':
        g=c.get('gesture')
        if not isinstance(g,dict):return False
        points=[];x,y,w,h=r['rect']
        for k in ('from','to'):
            p=g.get(k)
            if not isinstance(p,list) or len(p)!=2 or any(type(n) not in (int,float) for n in p) or not (1<=p[0]<w-1 and 1<=p[1]<h-1):return False
            point=[x+p[0],y+p[1]]
            if not loc.evaluate('(e,p)=>document.elementFromPoint(p[0],p[1])===e',point):return False
            points.append(point)
        page.mouse.move(*points[0]);page.mouse.down()
        try:page.mouse.move(*points[1],steps=16)
        finally:page.mouse.up()
    else:return False
    page.wait_for_timeout(200)
    return page.url in docs

def run(docs,goal,conv,out):
    if not isinstance(docs,dict) or BASE not in docs or len(docs)>16 or any(not isinstance(k,str) or not k.startswith(BASE) or '?' in k or '#' in k or not isinstance(v,str) or len(v)>200000 for k,v in docs.items()):raise ValueError('Synthetic documents required')
    if not isinstance(goal,str) or not 1<=len(goal)<=500:raise ValueError('Bounded synthetic task required')
    out=Path(out);out.mkdir(mode=0o700,parents=True,exist_ok=False)
    events=[];denied=[];start=time.monotonic()
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path=CHROME,headless=True,args=['--no-sandbox'])
        try:
            ctx=b.new_context(viewport={'width':1920,'height':1080},offline=True,service_workers='block',accept_downloads=False,permissions=[])
            def route(r):
                q=r.request
                if q.url in docs and q.method=='GET' and q.is_navigation_request() and q.resource_type=='document':return r.fulfill(status=200,content_type='text/html',headers={'Content-Security-Policy':CSP},body=docs[q.url])
                denied.append(q.resource_type);r.abort()
            ctx.route('**/*',route);ctx.route_web_socket('**/*',lambda ws:ws.close())
            page=ctx.new_page();ctx.on('page',lambda p:p.close() if p!=page else None);page.goto(BASE)
            for _ in range(8):
                before,rows=observe(page,docs)
                reply=conv.ask('Achieve the supplied offline synthetic task: '+goal+'. Choose one observed ID and allowed operation. type/select use value, drag uses gesture with from/to canvas-relative coordinates, finish when done. JSON operation,target,value,gesture. History: '+json.dumps(events)+' Current public DOM observation: '+json.dumps(before),media=(media(shot(page)),),json_mode=True,phase='controlled-workspace',stop_on_rate_limit=True,max_attempts=1)
                if not reply:events.append({'status':'provider-unavailable'});break
                try:c=parse(reply)
                except (ValueError,TypeError):events.append({'status':'invalid-response'});continue
                if not isinstance(c,dict):continue
                if c.get('operation')=='finish':break
                img=shot(page)
                try:ok=act(page,docs,rows,c)
                except Error:ok=False
                after,_=observe(page,docs);end=shot(page)
                events.append({'status':'verified-change' if ok and before!=after else 'no-result-or-denied','operation':c.get('operation'),'result':after['result'],'before_sha256':hashlib.sha256(img).hexdigest(),'after_sha256':hashlib.sha256(end).hexdigest()})
            final,_=observe(page,docs)
            receipt={'events':events,'final_state':final['result'],'decisions':conv.calls,'denied_requests':denied,'elapsed_seconds':round(time.monotonic()-start,3)}
            (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt
        finally:b.close()
