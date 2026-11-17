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
from .product_explorer import CHROME,allowed,JS

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

def capture(url:str,private:Path,report:dict,plan:dict):
 quality=capture_quality()
 cursor_style=capture_cursor_style()
 cursor_script=ARROW_CURSOR_JS if cursor_style=='arrow' else CURSOR_JS
 ensure_video_helper()
 validate_public_url(url)
 private=Path(private);private.mkdir(parents=True,exist_ok=True)
 actions={c['id']:c for c in report.get('controls',[])}
 headings={h['id']:h for h in report.get('headings',[])}
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
   context.add_init_script(cursor_script)
   video_begin=time.monotonic()
   page=context.new_page()
   response=page.goto(url,wait_until='domcontentloaded',timeout=30000)
   if response and response.status>=400:raise RuntimeError('Source page returned HTTP '+str(response.status))
   validate_public_url(page.url)
   page.wait_for_timeout(600)
   page.evaluate(cursor_script)
   video=page.video
   if video is None:raise RuntimeError('Browser video recording unavailable')
   start=time.monotonic()
   lead_in=max(0,start-video_begin)
   page.mouse.move(930,530)
   page.wait_for_timeout(500)
   evidence=[]
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
      if loc.count()!=1 or not loc.is_visible():continue
      box=loc.bounding_box()
      if not box:continue
      before=page.url
      if box['y']<70 or box['y']>580:
       doc_y=page.evaluate("""s => {
         const e=document.querySelector(s);
         return e?Math.round(e.getBoundingClientRect().top+window.scrollY):0;
       }""",selector)
       smooth_to(page,max(0,doc_y-270))
       box=loc.bounding_box()
      if not box:continue
      pointer_to(page,box['x']+box['width']*.5,box['y']+box['height']*.5)
      page.wait_for_timeout(300)
      loc.click(timeout=3500)
      page.wait_for_timeout(950)
      if urlsplit(page.url).netloc.lower()!=urlsplit(url).netloc.lower():
       raise RuntimeError('Unsafe navigation outside original product')
      mark('action-'+ident)
      events.append({'id':ident,'label':c['text'],'kind':c['kind'],
                     'from':before.split('?')[0],'to':page.url.split('?')[0]})
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
      events.append({'id':ident,'skipped':type(exc).__name__})
   if not events or all('skipped' in x for x in events):
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
   page.wait_for_timeout(800)
   length=time.monotonic()-start
   context.close()
   source=Path(video.path())
   output=private/'continuous-source.webm'
   shutil.copy2(source,output)
   receipt={'continuous_recording':True,'video':output.name,
      'sha256':hash_file(output),'duration_wall_s':round(length,3),
      'lead_in_seconds':round(lead_in,3),
      'actions':events,'evidence':evidence,
      'source_url':url.split('?')[0],'mode':plan.get('mode','showcase'),
      'capture_quality':quality['quality'],'source_dpr':quality['dpr'],
      'requested_video_size':quality['video_size'],
      'viewport_css_size':quality['viewport'],
      'presentation_cursor':cursor_style}
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
