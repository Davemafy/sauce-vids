"""Continuous Chromium video capture for public website demonstration.

Unlike still-state montages this records every real browser animation frame,
including scroll, pointer movement and safe state transitions.
"""
from __future__ import annotations
import hashlib,json,math,shutil,time,re,os
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
from scripts.capture_safety import validate_public_url,guard_route
from scripts.session_contract import safe_url
from .shot_scorer import crop_for_subject
from .product_explorer import CHROME,known_dialog_opener,allowed,JS,TAB_TARGET_JS

CURSOR_JS=r"""(() => {
 if(window.__saucePointerInstalled)return;
 window.__saucePointerInstalled=true;
 const marker=document.createElement('div');
 marker.setAttribute('aria-hidden','true');
 marker.id='sauce-motion-pointer';
 marker.style.cssText='position:fixed;left:0;top:0;width:16px;height:16px;border:2px solid #f9eee4;background:#2d221e;box-shadow:0 0 0 1px #201c1b,0 1px 5px #0006;border-radius:50%;z-index:2147483646;pointer-events:none;transform:translate3d(-35px,-35px,0);will-change:transform';
 let point={x:-35,y:-35},last=0;
 const install=()=>{if(!marker.isConnected)(document.body||document.documentElement).appendChild(marker)};
 install();
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});
 window.addEventListener('pointermove',e=>{
  point={x:e.clientX,y:e.clientY};
  marker.style.transform='translate3d('+(point.x-8)+'px,'+(point.y-8)+'px,0)';
 },true);
 window.addEventListener('pointerdown',()=>{
  marker.style.background='#efae7d';marker.style.width='12px';marker.style.height='12px';
 },true);
 window.addEventListener('pointerup',()=>{
  marker.style.background='#2d221e';marker.style.width='16px';marker.style.height='16px';
 },true);
 window.__sauceGetPointer=()=>point;
})();"""
ARROW_CURSOR_JS=r"""(() => {
 if(window.__saucePointerInstalled)return;
 window.__saucePointerInstalled=true;
 // Genuine Chromium mouse events drive one native-shaped presentation cursor.
 // SVG tip starts at (3,2); translate it back to the actual event hotspot.
 const svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 30">'
  +'<path d="M3 2.5v22.2l5.65-5.8 4.64 9.18 4.4-2.26-4.55-8.48h8.15L3 2.5Z"'
  +' fill="#17191e" stroke="#fff" stroke-width="2" stroke-linejoin="round"/>'
  +'</svg>';
 const marker=document.createElement('div');
 marker.id='sauce-motion-pointer';
 marker.setAttribute('aria-hidden','true');
 marker.style.cssText='position:fixed;left:0;top:0;width:20px;height:25px;'
  +'z-index:2147483646;pointer-events:none;transform:translate3d(-99px,-99px,0);'
  +'background-size:100% 100%;background-repeat:no-repeat;'
  +'filter:drop-shadow(0 1px 2px rgba(0,0,0,.35));will-change:transform';
 marker.style.backgroundImage='url("data:image/svg+xml,'+encodeURIComponent(svg)+'")';
 const install=()=>{if(!marker.isConnected)(document.body||document.documentElement).appendChild(marker)};
 install();
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});
 let point={x:-35,y:-35};
 window.addEventListener('pointermove',e=>{
   point={x:e.clientX,y:e.clientY};
   marker.style.transform='translate3d('+(point.x-2.5)+'px,'+(point.y-2)+'px,0)';
 },true);
 window.addEventListener('pointerdown',()=>{marker.style.opacity='.82'},true);
 window.addEventListener('pointerup',()=>{marker.style.opacity='1'},true);
 window.__sauceGetPointer=()=>point;
})();"""

def capture_cursor_style():
 style=os.environ.get('SAUCE_CAPTURE_CURSOR','circle')
 if style not in ('circle','arrow'):
  raise ValueError('Invalid SAUCE_CAPTURE_CURSOR (circle or arrow)')
 return style

def hash_file(path:Path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(2**20),b''):h.update(chunk)
 return h.hexdigest()

def pointer_to(page,x,y,*,steps=19):
 try:origin=page.evaluate("window.__sauceGetPointer?window.__sauceGetPointer():({x:0,y:0})")
 except Exception:origin={'x':0,'y':0}
 x0=origin['x'] if origin['x']>=0 else 930;y0=origin['y'] if origin['y']>=0 else 530
 dx=x-x0;dy=y-y0
 dist=max(1,math.hypot(dx,dy))
 for i in range(steps):
  u=(i+1)/steps
  p=u*u*(3-2*u)
  bend=math.sin(math.pi*p)*min(dist*.08,24)
  page.mouse.move(x0+dx*p-dy/dist*bend,y0+dy*p+dx/dist*bend)
  page.wait_for_timeout(13)

def smooth_to(page,target):
 """Frame-driven browser scroll, avoiding a 6000px jump in one instant."""
 y=max(0,int(target))
 current=float(page.evaluate('window.scrollY'))
 distance=abs(y-current)
 if distance<8:return
 duration=min(3600,max(780,int(distance*.50)))
 page.evaluate("""async args => {
  const start=window.scrollY,delta=args.y-start;
  await new Promise(resolve=>{
   const began=performance.now();
   function tick(now){
    const t=Math.min(1,(now-began)/args.duration);
    const ease=t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;
    window.scrollTo({top:start+delta*ease,behavior:'instant'});
    if(t<1)requestAnimationFrame(tick);else resolve();
   }
   requestAnimationFrame(tick);
  });
 }""",{'y':y,'duration':duration})
 page.wait_for_timeout(180)

def ensure_video_helper(browser_dir:Path=Path('/opt/devmcp-browsers')):
 """Use an existing shared Playwright FFmpeg helper on Vultr.

 Chromium itself can be available even when Playwright's recording helper is
 missing from the service user's home cache. This path only applies if a
 genuine installed ffmpeg-* helper exists; don't download or install anything.
 An explicit browser cache selection from the operator is always respected.
 """
 if os.environ.get('PLAYWRIGHT_BROWSERS_PATH'):
  return os.environ['PLAYWRIGHT_BROWSERS_PATH']
 if any(p.is_file() for p in browser_dir.glob('ffmpeg-*/ffmpeg-linux')):
  os.environ['PLAYWRIGHT_BROWSERS_PATH']=str(browser_dir)
 return os.environ.get('PLAYWRIGHT_BROWSERS_PATH','')

def capture_quality():
 """Keep existing pilot intact; opt in to high-density source experiments.

 DPR 2 is rendered by Chromium; recording at 1920x1080 preserves much
 more of its actual source pixels than the old 1280x720 browser video.
 The final 60fps export still does not imply 60 unique source frames.
 """
 quality=os.environ.get('SAUCE_CAPTURE_QUALITY','standard')
 if quality not in ('standard','high'):
  raise ValueError('Invalid SAUCE_CAPTURE_QUALITY (standard or high)')
 # Playwright records CSS viewport pixels, then pads when the output
 # video size exceeds that viewport. Preserve a full-frame native capture:
 # a 1920px recording must use a real 1920px CSS viewport (not 1280px
 # pixels parked in the top-left of a nominally 1080p file).
 width,height=(1920,1080) if quality=='high' else (1280,720)
 return {'quality':quality,'dpr':2 if quality=='high' else 1,
         'viewport':{'width':width,'height':height},
         'video_size':{'width':width,'height':height}}

def capture_slider(page, loc, time_zero):
 """Record a real drag and verify one dependent visible value group."""
 if loc.count()!=1 or not loc.is_enabled():
  print('Slider locator unavailable',loc.count(),flush=True)
  return None
 setup=loc.evaluate_handle(r"""e => {
  if (!e.matches('input[type=range]') ||
      e.closest('form,[data-private],[data-secret],[data-sensitive]') ||
      getComputedStyle(e).direction !== 'ltr') return null;
  const group=e.closest('[role=group][aria-label]');
  const hidden=getComputedStyle(e).clipPath!=='none';
  const track=(group||e).getBoundingClientRect();
  const thumb=(hidden?e.parentElement:e).getBoundingClientRect();
  const min=Number(e.min||0), max=Number(e.max||100), value=Number(e.value);
  if (!(min<max) || track.left<0||track.right>innerWidth||
      track.top<0||track.bottom>innerHeight||track.width<120||track.width<2*track.height) return null;
  const left=track.left+1, right=track.right-1, y=thumb.top+thumb.height/2;
  const x=hidden?thumb.left+thumb.width/2:
      track.left+8+(track.width-16)*(value-min)/(max-min);
  if (!(left<=x&&x<=right&&track.top<=y&&y<=track.bottom)) return null;
  if (!(document.elementFromPoint(x,y)?.closest('[role=group]')===group&&group ||
        document.elementFromPoint(x,y)===e)) return null;
  const width=right-left, step=Math.abs(Number(e.step))/(max-min)||.01;
  const distance=Math.max(width*.245, width*step*1.2);
  const end=x+distance<=right?x+distance:Math.max(left,x-distance);
  let scope=group||e;
  for(let i=0;i<3&&scope.parentElement;i++)scope=scope.parentElement;
  const candidates=[];
  for(const node of scope.querySelectorAll('*')){
   if(node.childElementCount||node.closest('form,[data-private],[data-secret],[data-sensitive]'))continue;
   const r=node.getBoundingClientRect(), text=node.innerText?.trim();
   if(!text||text.length>70||!/\d/.test(text)||r.width<6||r.height<10||
      r.top<track.top+22||r.bottom>Math.min(innerHeight,track.bottom+360)||
      r.left<0||r.right>innerWidth||node.checkVisibility?.({opacityProperty:true,visibilityProperty:true})===false)continue;
   candidates.push({node,text});
   if(candidates.length>=100)break;
  }
  if(!candidates.length)return null;
  return {e,value,x,end,y,track:track.toJSON(),candidates};
 }""")
 try:
  geometry=setup.evaluate('s => s && ({x:s.x,y:s.y,end:s.end,track:s.track})')
  if geometry is None:
   print('Slider geometry or candidate result unavailable',flush=True)
   return None
  x,y=geometry['x'],geometry['y']
  page.mouse.move(x,y)
  page.wait_for_timeout(120)
  start=time.monotonic()-time_zero
  points=[{'t':start,'x':x,'y':y}]
  page.mouse.down()
  try:
   page.wait_for_timeout(380)
   for i in range(1,25):
    u=i/24
    px=x+(geometry['end']-x)*u*u*(3-2*u)
    page.mouse.move(px,y)
    points.append({'t':time.monotonic()-time_zero,'x':px,'y':y})
    page.wait_for_timeout(32)
  finally:
   page.mouse.up()
  released=time.monotonic()-time_zero
  points.append({'t':released,'x':geometry['end'],'y':y})
  page.wait_for_timeout(280)
  result=setup.evaluate(r"""s => {
    if(!s.e.isConnected || Number(s.e.value)===s.value)return null;
    const rects=s.candidates.filter(({node,text})=>node.isConnected&&
      node.innerText?.trim()!==text&&/\d/.test(node.innerText)&&
      node.checkVisibility?.({opacityProperty:true,visibilityProperty:true})!==false)
      .map(({node})=>node.getBoundingClientRect())
      .filter(r=>r.width>6&&r.height>10&&r.left>=0&&r.right<=innerWidth&&
            r.top>=s.track.top&&r.bottom<=innerHeight&&r.width<innerWidth*.48);
    if(!rects.length)return null;
    const x=Math.min(...rects.map(r=>r.left)),y=Math.min(...rects.map(r=>r.top));
    return {x,y,width:Math.max(...rects.map(r=>r.right))-x,
                 height:Math.max(...rects.map(r=>r.bottom))-y};
  }""")
  if result is None:
   print('Slider drag did not verify dependent text',flush=True)
   return None
  track=geometry['track']
  return {'kind':'slider_change','start':start,'t':released,'end':released,
          'evidence':'Range changed with a visible dependent numeric result',
          'targetRect':{k:track[k] for k in ('x','y','width','height')},
          'resultRect':result,'pointer_samples':points}
 finally:
  setup.dispose()


def record_subjects(page, beats, video_begin):
 """Measure each subject after settling and reserve genuine footage around it."""
 shots=[]
 for beat in beats:
  loc=page.locator(beat['selector'])
  if loc.count()!=1 or not loc.is_visible():
   continue
  loc.evaluate("e => e.scrollIntoView({block:'center',behavior:'instant'})")
  page.wait_for_timeout(550)
  region=loc.evaluate("""e => {
   const b=e.getBoundingClientRect(), h=document.elementFromPoint(b.x+b.width/2,b.y+b.height/2);
   const hit=h&&(e.contains(h)||h.contains(e));
   if(!hit || e.closest('nav,footer,form,[data-private],[data-secret],[data-sensitive]'))
    return null;
   return {x:b.x,y:b.y,width:b.width,height:b.height};
  }""")
  if not region:
   continue
  width,height=(page.viewport_size[k] for k in ('width','height'))
  try:
   crop=crop_for_subject(region,width,height)
  except ValueError:
   continue
  x,y,w,h=crop
  margin=min((region['x']-x)/w,(x+w-region['x']-region['width'])/w,
             (region['y']-y)/h,(y+h-region['y']-region['height'])/h)
  begin=time.monotonic()-video_begin
  page.wait_for_timeout(2200)
  box=loc.bounding_box()
  if box and all(abs(box[k]-region[k])<4 for k in region):
   shots.append({'start':begin+.16,'frames':112,'crop':crop,
                 'zoom_delta':max(0,min(.047,margin*1.8)),
                 'purpose':beat['purpose'],'kind':beat['kind'],'score':beat['score']})
 if len(shots)<3 or shots[0]['purpose']!='hook':
  raise RuntimeError('Page no longer exposes three stable product subjects')
 return shots

def capture(url:str,private:Path,report:dict,plan:dict):
 quality=capture_quality()
 cursor_style=capture_cursor_style()

 ensure_video_helper()
 validate_public_url(url)
 private=Path(private);private.mkdir(parents=True,exist_ok=True)
 actions={c['id']:c for c in report.get('controls',[])}
 headings={h['id']:h for h in report.get('headings',[])}
 selected=plan.get('action_ids',[])
 cursorless=(plan.get('mode')=='interactive' and len(selected)==1 and
             actions.get(selected[0],{}).get('kind')=='slider')
 beats=plan.get('beats',[]) if plan.get('mode')=='showcase' else []
 cursor_script=('' if cursorless or beats else ARROW_CURSOR_JS if cursor_style=='arrow' else CURSOR_JS)
 events=[];moment=0.0
 with sync_playwright() as pw:
  b=pw.chromium.launch(headless=True,executable_path=CHROME,
   args=['--no-sandbox','--disable-dev-shm-usage'])
  try:
   folder=private/'live-video';folder.mkdir(exist_ok=True)
   context=b.new_context(viewport=quality['viewport'],
    device_scale_factor=quality['dpr'],record_video_dir=str(folder),
    record_video_size=quality['video_size'],service_workers='block')
   context.route('**/*',guard_route)
   if cursor_script:context.add_init_script(cursor_script)
   video_begin=time.monotonic()
   page=context.new_page()
   response=page.goto(url,wait_until='domcontentloaded',timeout=30000)
   if response and response.status>=400:raise RuntimeError('Source page returned HTTP '+str(response.status))
   validate_public_url(page.url)
   page.wait_for_timeout(600)
   if cursor_script:page.evaluate(cursor_script)
   video=page.video
   if video is None:raise RuntimeError('Browser video recording unavailable')
   start=time.monotonic()
   lead_in=max(0,start-video_begin)
   page.mouse.move(930,530)
   page.wait_for_timeout(500)
   evidence=[]
   editorial_events=[]
   def mark(label):
    # Records nonsecret public evidence only; values, HAR, content excluded.
    page.screenshot(path=str(private/('mark-'+str(len(evidence))+'.jpg')),
                    type='jpeg',quality=60,animations='disabled')
    evidence.append({'phase':label,'time_s':round(time.monotonic()-start,2),
          'url':page.url.split('?')[0],'scroll':page.evaluate('Math.round(window.scrollY)')})
   mark('opening')
   if plan.get('mode')=='interactive':
    for ident in plan.get('action_ids',[])[:2]:
     c=actions.get(ident)
     if not c or not allowed(c,report['url']):continue
     selector=c['selector']
     loc=page.locator(selector)
     try:
      if c['kind']=='slider':
       before=page.url
       slider=capture_slider(page,loc,video_begin)
       if not slider or urlsplit(page.url)[:3]!=urlsplit(before)[:3]:
        raise RuntimeError('No visible dependent result from public slider')
       editorial_events.append(slider)
       mark('action-'+ident)
       events.append({'id':ident,'label':c['text'],'kind':'slider',
                      'from':safe_url(before),'to':safe_url(page.url)})
       continue
      if loc.count()!=1 or not loc.is_visible():continue
      box=loc.bounding_box()
      if not box:continue
      before=page.url
      dialog_opener=known_dialog_opener(c,before)
      dialogs=page.locator('[role="dialog"]:visible,dialog[open]:visible')
      if dialog_opener and (dialogs.count() or not loc.evaluate("e => !e.form && !e.closest('form')")):
       continue
      if box['y']<70 or box['y']>580:
       doc_y=page.evaluate("""s => {
         const e=document.querySelector(s);
         return e?Math.round(e.getBoundingClientRect().top+window.scrollY):0;
       }""",selector)
       smooth_to(page,max(0,doc_y-270))
       box=loc.bounding_box()
      if not box:continue
      tab_target=loc.evaluate(TAB_TARGET_JS) if c['kind']=='tab' else None
      if c['kind']=='tab' and not tab_target:continue
      pointer_to(page,box['x']+box['width']*.5,box['y']+box['height']*.5)
      page.wait_for_timeout(300)
      # Trust visible ARIA panel geometry only after an observed state change.
      controls=(loc.get_attribute('aria-controls') or '').split()
      was_collapsed=loc.get_attribute('aria-expanded')=='false'
      click_time=time.monotonic()-video_begin
      loc.click(timeout=3500)
      page.wait_for_timeout(950)
      if urlsplit(page.url).netloc.lower()!=urlsplit(url).netloc.lower():
       raise RuntimeError('Unsafe navigation outside original product')
      if dialog_opener:
       if page.url!=before or dialogs.count()!=1:
        raise RuntimeError('Public setup dialog did not open')
       dialog=dialogs.first
       region=dialog.bounding_box()
       heading=dialog.get_by_role('heading',name='Connect your agent',exact=True)
       w,h=(page.viewport_size[k] for k in ('width','height'))
       if (not region or heading.count()!=1 or not heading.is_visible()
           or region['x']<0 or region['y']<0
           or region['x']+region['width']>w or region['y']+region['height']>h):
        raise RuntimeError('Public setup instructions are not fully visible')
       editorial_events.extend([
        {'kind':'click','t':click_time,'label':c['text'],'semanticGoal':'Reveal public agent setup'},
        {'kind':'state_change','t':time.monotonic()-video_begin,
         'evidence':'Public agent setup dialog visibly opened','resultRect':region}])
      if tab_target:
       region=loc.evaluate("""(e,id) => {
        const pane=document.getElementById(id);
        if(e.getAttribute('aria-selected')!=='true'||e.getAttribute('aria-controls')!==id||
           !pane?.matches('[role="tabpanel"]')||
           pane.closest('form,[data-private],[data-secret],[data-sensitive]')||
           pane.querySelector('input[type=password], [data-private], [data-secret], [data-sensitive]')||
           !pane.checkVisibility({checkOpacity:true, checkVisibilityCSS:true})) return null;
        const r=pane.getBoundingClientRect();
        if(r.width<20||r.height<16||r.left<0||r.top<0||r.bottom>innerHeight||r.right>innerWidth)
         return null;
        if(!pane.innerText.trim()&&!pane.querySelector('img,svg,canvas,video'))return null;
        return {x:r.x,y:r.y,width:r.width,height:r.height};
       }""",tab_target)
       if page.url!=before or not region:
        raise RuntimeError('Public tab did not reveal a visible local panel')
       editorial_events.extend([
        {'kind':'click','t':click_time,'label':c['text'],'semanticGoal':'Inspect public tab content'},
        {'kind':'state_change','t':time.monotonic()-video_begin,
         'evidence':'Inactive tab selected and its panel visibly opened','resultRect':region}])
      mark('action-'+ident)
      events.append({'id':ident,'label':c['text'],'kind':c['kind'],
                     'from':safe_url(before),'to':safe_url(page.url)})
      if was_collapsed and len(controls)==1 and page.url==before:
       panel=page.evaluate('''id => {
        const node=document.getElementById(id);
        if (!node || node.closest('[data-private],[data-secret],[data-sensitive]')) return null;
        const rect=node.getBoundingClientRect(), css=getComputedStyle(node);
        if (css.display==='none'||css.visibility!=='visible'||Number(css.opacity)<=.04||
            rect.width<16||rect.height<16||rect.left<0||rect.top<0||
            rect.right>innerWidth||rect.bottom>innerHeight) return null;
        return {x:rect.x,y:rect.y,width:rect.width,height:rect.height};
       }''',controls[0])
       if panel and loc.get_attribute('aria-expanded')=='true':
        editorial_events.extend([
         {'kind':'click','t':click_time,'label':c['text'],'semanticGoal':'Inspect expanded public panel'},
         {'kind':'state_change','t':time.monotonic()-video_begin,
          'evidence':'Collapsed control expanded with a visible ARIA panel','resultRect':panel}])
      # Demonstrate text-entry mode without sending/submitting anything.
      # Restrict to an explicit observed paste-text action and a single
      # publicly visible textarea; never fill private or password fields.
      if re.search(r'paste text|type text|enter text',c['text'],re.I):
       fields=page.locator('textarea:not([disabled]):not([readonly])')
       visible=[fields.nth(k) for k in range(min(fields.count(),8))
                if fields.nth(k).is_visible()]
       if len(visible)==1:
        field=visible[0]
        if field.bounding_box():
         rect=field.bounding_box()
         pointer_to(page,rect['x']+min(80,rect['width']*.2),rect['y']+min(28,rect['height']*.2))
         field.click(timeout=3500)
         page.wait_for_timeout(210)
         page.keyboard.type('Demo message for this walkthrough. No personal information.',delay=38)
         page.wait_for_timeout(500)
         mark('demo-text-entered-without-submission')
         events.append({'id':ident+'-demo-text','kind':'local-example',
                        'label':'Benign text fixture typed; no submission'})
     except Exception as exc:
      # Individual disappearing dynamic controls are not a fatal job error.
      if cursorless:raise
      events.append({'id':ident,'skipped':type(exc).__name__})
   subject_shots=record_subjects(page,beats,video_begin) if beats else []
   if not subject_shots and (not events or all('skipped' in x for x in events)):
    # Public-site preview when there is no safe meaningful app action.
    positions=[headings[x]['y'] for x in plan.get('heading_ids',[])[:2] if x in headings]
    height=page.evaluate('document.documentElement.scrollHeight')
    if height>1600 and (len(positions)<2 or max(positions)<550):
     positions=[min(height-720,round(height*.32)),min(height-720,round(height*.64))]
    elif not positions and height>900:
     positions=[min(height-720,round(height*.35)),min(height-720,round(height*.66))]
    for i,y in enumerate(positions[:2]):
     smooth_to(page,max(0,y-210))
     pointer_to(page,900-i*240,340+i*75)
     page.wait_for_timeout(360)
     mark('read-'+str(i))
   if editorial_events:
    page.wait_for_timeout(1950 if cursorless else 2000)
    editorial_events.append({'kind':'interaction_complete','t':time.monotonic()-video_begin})
   page.wait_for_timeout(1000)
   length=time.monotonic()-start
   context.close()
   source=Path(video.path())
   output=private/'continuous-source.webm'
   shutil.copy2(source,output)
   receipt={'continuous_recording':True,'video':output.name,
      'sha256':hash_file(output),'duration_wall_s':round(length,3),
      'lead_in_seconds':round(lead_in,3),
      'actions':events,'evidence':evidence,'editorial_events':editorial_events,
      'subject_shots':subject_shots,
      'source_url':url.split('?')[0],'mode':plan.get('mode','showcase'),
      'capture_quality':quality['quality'],'source_dpr':quality['dpr'],
      'requested_video_size':quality['video_size'],
      'viewport_css_size':quality['viewport'],
      'cursorless':cursorless,'presentation_cursor':'composited-arrow' if cursorless else 'hidden' if beats else cursor_style}
   (private/'continuous-capture.json').write_text(json.dumps(receipt,indent=2))
   return receipt
  finally:b.close()

if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser()
 ap.add_argument('--url',required=True)
 ap.add_argument('--out',type=Path,required=True)
 ap.add_argument('--inspection',type=Path,required=True)
 ap.add_argument('--plan',type=Path,required=True)
 a=ap.parse_args()
 print(json.dumps(capture(a.url,a.out,json.loads(a.inspection.read_text()),
  json.loads(a.plan.read_text()))),flush=True)
