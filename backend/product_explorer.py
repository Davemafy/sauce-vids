"""Sauce public-site explorer. Discover actual controls before asking an LLM to direct."""
import json,re
from pathlib import Path
from urllib.parse import urlsplit
from scripts.capture_safety import validate_public_url,guard_route
from scripts.session_contract import validate_actions

SAFE_LABEL=re.compile(r'paste text instead|show example|try (?:a )?sample|demo|preview|show more|read more|learn more|details|see how it works|view example|explore example|open menu|toggle menu|view features|expand|^toggle (?:first|second|both) elements?$|reveal|play video',re.I)
UNSAFE_LABEL=re.compile(r'delete|remove|purchase|pay|checkout|order|submit|send|register|sign.?up|log.?in|sign.?in|logout|invite|share|publish|subscribe|follow|reset|clear|cancel|upload|download|add to cart|connect|authorize|approve|confirm|book|reserve|refund',re.I)
UNSAFE_PATH=re.compile(r'/(api|auth|signin|signup|login|logout|register|account|checkout|payment|billing|purchase|unsubscribe|delete|submit|admin|invite|callback|token|session)(/|$)',re.I)
JS=r"""() => {
const text=e=>(e.innerText||e.getAttribute('aria-label')||e.getAttribute('title')||'').replace(/\s+/g,' ').trim().slice(0,110);
const visible=e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect();return r.width>=8&&r.height>=8&&s.visibility!=='hidden'&&s.display!=='none'&&Number(s.opacity)>0.04};
function path(e){let parts=[];for(let n=e;n instanceof Element;n=n.parentElement){
if(n.id&&/^[A-Za-z][\w-]{0,45}$/.test(n.id)&&!/secret|password|token/i.test(n.id)){parts.unshift('#'+CSS.escape(n.id));break}
if(n===document.body){parts.unshift('body');break}
const siblings=n.parentElement?[...n.parentElement.children].filter(x=>x.tagName===n.tagName):[];
parts.unshift(n.tagName.toLowerCase()+':nth-of-type('+(siblings.indexOf(n)+1)+')');
if(parts.length>20)break
}return parts.join(' > ').slice(0,295)}
const headings=[];
for(const e of document.querySelectorAll('h1,h2,h3,h4')){
 if(!visible(e)||!text(e))continue;
 const r=e.getBoundingClientRect();
 headings.push({id:'h'+headings.length,text:text(e),tag:e.tagName.toLowerCase(),selector:path(e),y:Math.round(r.top+scrollY)});
 if(headings.length>=30)break;
}
const controls=[];
for(const e of document.querySelectorAll('input[type="range"]:enabled')){
 if(e.closest('form,[data-private],[data-secret],[data-sensitive]'))continue;
 const group=e.closest('[role="group"][aria-label]');
 const label=text(e)||text(group||e);
 if(!label||!/\b(value selector|volume|calculator|estimator|range|slider)\b/i.test(label))continue;
 const track=group||e;
 if(!visible(track)||track.getBoundingClientRect().width<120)continue;
 controls.push({id:'a'+controls.length,text:label,kind:'slider',selector:path(e)});
 if(controls.length>=4)break;
}

const candidates = [...document.querySelectorAll('a[href],button,[role="button"],summary')];
const priority = e => e.matches('button[aria-controls][aria-expanded="false"],[role="button"][aria-controls][aria-expanded="false"]') ? 0 : e.closest('main') ? 1 : 2;
candidates.sort((a,b)=>priority(a)-priority(b));
for(const e of candidates){
 if(!visible(e)||!text(e)||e.closest('[data-private],[data-secret],[data-sensitive]'))continue;
 const tag=e.tagName.toLowerCase(),kind=tag==='a'?'link':'button';
 const href=kind==='link'?e.href:null;
 const controlled_panel=e.hasAttribute('aria-controls')&&e.getAttribute('aria-expanded')==='false';
 controls.push({id:'a'+controls.length,text:text(e),tag,kind,href,controlled_panel,selector:path(e),button_type:tag==='button'?e.type||'':'',in_form:!!e.form||!!e.closest('form'),y:Math.round(e.getBoundingClientRect().top+scrollY)});
 if(controls.length>=80)break;
}
const root=getComputedStyle(document.documentElement),body=getComputedStyle(document.body);
const vars={};for(const n of [...root].filter(n=>/^--(primary|accent|background|foreground|brand)/i.test(n)).slice(0,15))vars[n]=root.getPropertyValue(n).trim().slice(0,90);
return {title:document.title.slice(0,140),url:location.origin+location.pathname,headings,controls,
height:document.documentElement.scrollHeight,
brand:{theme:document.querySelector('meta[name="theme-color"]')?.content||'',background:body.backgroundColor,vars},
challenge:!!document.querySelector('#challenge-stage,.cf-turnstile,iframe[src*="captcha"]')};
}"""
CHROME='/opt/devmcp-browsers/chromium_headless_shell-1254/chrome-headless-shell-linux64/chrome-headless-shell'

def known_dialog_opener(control, origin):
 # This public Brimble control opens setup instructions locally.
 base=urlsplit(origin)
 return (base.scheme=='https' and base.netloc in ('www.brimble.io','brimble.io')
         and base.path in ('','/') and control.get('tag')=='button'
         and control.get('in_form') is False
         and control.get('text')=='Connect your agent')

def allowed(c,origin):
 if known_dialog_opener(c,origin):return True
 label=c['text']
 if UNSAFE_LABEL.search(label):return False
 if c['kind']=='slider':return bool(re.search(r'\b(value selector|volume|calculator|estimator|range|slider)\b',label,re.I))
 if c['kind']=='button':return c.get('button_type')!='submit' and bool(SAFE_LABEL.search(label))
 try:
  u=urlsplit(c['href']);base=urlsplit(origin)
  return u.scheme==base.scheme and u.netloc.lower()==base.netloc.lower() and not u.query and not UNSAFE_PATH.search(u.path)
 except Exception:return False

def inspect(url,private):
 from playwright.sync_api import sync_playwright
 validate_public_url(url)
 private=Path(private);private.mkdir(parents=True,exist_ok=True)
 with sync_playwright() as pw:
  b=pw.chromium.launch(headless=True,executable_path=CHROME,args=['--no-sandbox','--disable-dev-shm-usage'])
  try:
   c=b.new_context(viewport={'width':1280,'height':720},service_workers='block')
   c.route('**/*',guard_route)
   p=c.new_page();response=p.goto(url,wait_until='domcontentloaded',timeout=28000)
   if response and response.status>=400:raise RuntimeError('Source HTTP '+str(response.status))
   validate_public_url(p.url)
   p.wait_for_timeout(500)
   report=p.evaluate(JS)
   if report['challenge'] or re.match(r'just a moment|attention required',report['title'],re.I):
    raise RuntimeError('Access challenge prevents public capture')
   if not(report['title'] or report['headings'] or report['controls']):
    raise RuntimeError('No readable public website')
   report['controls']=[x for x in report['controls'] if allowed(x,report['url'])][:35]
   report['headings']=report['headings'][:25]
   report['source_url']=url
   shot=private/'inspection.jpg';p.screenshot(path=str(shot),type='jpeg',quality=72,animations='disabled')
   report['screenshot']=str(shot)
   (private/'inspection.json').write_text(json.dumps(report,indent=2))
   return report
  finally:b.close()

def normalize(plan,report):
 if not isinstance(plan,dict):plan={}
 controls={x['id'] for x in report['controls']}
 headings={x['id'] for x in report['headings']}
 proposed=plan.get('action_ids',[])
 if not isinstance(proposed,list):proposed=[]
 chosen=list(dict.fromkeys(x for x in proposed if isinstance(x,str) and x in controls))[:2]
 # A glass shot uses a dedicated cursorless take with one real drag.
 slider=next((x for x in chosen if any(c['id']==x and c['kind']=='slider'
                                      for c in report['controls'])),None)
 if slider:chosen=[slider]
 proposed_h=plan.get('heading_ids',[])
 if not isinstance(proposed_h,list):proposed_h=[]
 h=list(dict.fromkeys(x for x in proposed_h if isinstance(x,str) and x in headings))[:2]
 if not h:h=[x['id'] for x in report['headings'][:2]]
 mode='interactive' if plan.get('mode')=='interactive' and chosen else 'showcase'
 return {'mode':mode,'action_ids':chosen,'heading_ids':h,
    'title':str(plan.get('title') or report.get('title') or 'Public website')[:95],
    'reason':str(plan.get('reason') or 'Observed public browser states')[:240]}

def workflow(plan,report):
 actions=[]
 if plan['mode']=='interactive':
  lookup={x['id']:x for x in report['controls']}
  for id in plan['action_ids']:
   control=lookup[id]
   sel=control['selector']
   if control['kind']=='slider':
    actions.append({'action':'hover','selector':sel,'expect_selector':sel,'settle_ms':300})
    continue
   actions.extend([{'action':'hover','selector':sel,'expect_selector':sel,'settle_ms':300},
                   {'action':'click','selector':sel,'settle_ms':800}])
 else:
  lookup={x['id']:x for x in report['headings']}
  for id in plan['heading_ids']:
   sel=lookup[id]['selector']
   actions.append({'action':'hover','selector':sel,'expect_selector':sel,'settle_ms':420})
 if not actions:actions=[{'action':'wait','ms':800,'settle_ms':200}]
 validate_actions(actions)
 return actions

def preflight(url,actions):
 """Selector validity on a fresh browser before expensive capture."""
 from playwright.sync_api import sync_playwright
 with sync_playwright() as pw:
  b=pw.chromium.launch(headless=True,executable_path=CHROME,args=['--no-sandbox','--disable-dev-shm-usage'])
  try:
   c=b.new_context(viewport={'width':1280,'height':720},service_workers='block')
   c.route('**/*',guard_route);p=c.new_page()
   p.goto(url,wait_until='domcontentloaded',timeout=28000);p.wait_for_timeout(450)
   valid=[]
   for action in actions:
    if 'selector' in action:
     try:
      loc=p.locator(action['selector'])
      if loc.count()!=1 or not loc.is_visible():continue
     except Exception:continue
    valid.append(action)
   return valid or [{'action':'wait','ms':750,'settle_ms':200}]
  finally:b.close()
