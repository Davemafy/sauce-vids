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
from .product_explorer import CHROME,known_dialog_opener,safe_public_modal_opener,allowed,JS,TAB_TARGET_JS


def same_canonical_public_origin(original, current):
 """Accept only a strict apex/www redirect, never a foreign host or downgrade."""
 a,b=urlsplit(original),urlsplit(current)
 if a.scheme!='https' or b.scheme!='https' or a.port not in (None,443) or b.port not in (None,443):
  return False
 ah=(a.hostname or '').lower().removeprefix('www.')
 bh=(b.hostname or '').lower().removeprefix('www.')
 return bool(ah and ah==bh)


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

def capture_cursor_style(requested=None):
 from backend.cursor_capture_js import CURSOR_STYLES
 style=requested if requested is not None else os.environ.get('SAUCE_CAPTURE_CURSOR','founder-reference')
 if style not in (*CURSOR_STYLES,'circle','arrow','tabler-legacy'):
  raise ValueError('Invalid Sauce capture cursor style')
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

def smooth_to(page,target,*,speed=1.):
 """Frame-driven browser scroll, avoiding a 6000px jump in one instant."""
 y=max(0,int(target))
 current=float(page.evaluate('window.scrollY'))
 distance=abs(y-current)
 if distance<8:return
 duration=min(3600,max(780,int(distance*.50/speed)))
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

# Browser-derived geometry, never guessed from pricing-card names or site CSS.
# If an outcome text node lives inside a compact, visually bounded DOM component,
# capture the entire component when it is fully visible. Failure to find one is
# explicit: an unbounded price-text rectangle must not masquerade as a full card.
COMPONENT_RECT_JS = r"""node => {
  if (!(node instanceof Element) || node.closest('form,[data-private],[data-secret],[data-sensitive]'))
    return null;
  const leaf=node.getBoundingClientRect();
  const visibleRect=r=>r.width>0&&r.height>0&&r.left>=0&&r.top>=0&&r.right<=innerWidth&&r.bottom<=innerHeight;
  for(let a=node.parentElement,depth=0;a&&depth<8;depth++,a=a.parentElement){
    if(a.matches('body,html,main,nav,footer,form') ||
       a.closest('[data-private],[data-secret],[data-sensitive]'))break;
    const r=a.getBoundingClientRect(), css=getComputedStyle(a);
    if(!visibleRect(r) || r.width<160 || r.height<120 ||
       r.width>innerWidth*.50 || r.height>innerHeight*.90 ||
       r.width*r.height<leaf.width*leaf.height*3)continue;
    const radius=parseFloat(css.borderTopLeftRadius)||0;
    const bordered=parseFloat(css.borderTopWidth)>0&&css.borderTopStyle!=='none';
    const backed=css.backgroundColor!=='rgba(0, 0, 0, 0)'&&css.backgroundColor!=='transparent';
    if(!(radius>=6&&(bordered||backed)||css.boxShadow!=='none'))continue;
    // A component is not a full-page panel. Return only the nearest qualifying container.
    return {x:r.x,y:r.y,width:r.width,height:r.height};
  }
  return null;
}"""

def prepare_slider_component_view(page, loc):
 """Move a compact pricing component fully into frame before the real drag.

 Only the existing visible numerical price and its bordered DOM ancestor can
 justify a tiny scroll. This is an optional source-quality improvement; if the
 slider and whole component cannot coexist, no artificial reconstruction occurs.
 """
 if loc.count()!=1:return 0
 delta=loc.evaluate(r"""e => {
   let root=e;
   for(let i=0;root?.parentElement&&i<9;i++){
     if(root.querySelectorAll('span').length>0 && root.innerText?.includes('/ mo'))break;
     root=root.parentElement;
   }
   if(!root)return 0;
   const input=e.getBoundingClientRect();
   const findCard=node=>{
     for(let a=node.parentElement,d=0;a&&d<7;d++,a=a.parentElement){
       const r=a.getBoundingClientRect(),style=getComputedStyle(a);
       if(r.width>=160&&r.width<=innerWidth*.5&&r.height>=120&&
          r.height<=innerHeight*.90&&parseFloat(style.borderTopWidth)>0&&
          (parseFloat(style.borderTopLeftRadius)||0)>=6)return r;
     }
     return null;
   };
   const candidates=[...root.querySelectorAll('span,p')]
      .filter(n=>n.children.length===0&&/^\$\s*\d{1,4}\s*\/\s*mo$/i.test(n.innerText?.trim()||''));
   for(const node of candidates){
      const card=findCard(node);
      if(!card||card.height>innerHeight-96||card.left<0||card.right>innerWidth)continue;
      const needed=Math.ceil(card.bottom-innerHeight+52);
      if(needed>0 && needed<=210 && input.top-needed>=90)return needed;
   }
   return 0;
 }""")
 if delta>0:
  page.evaluate("delta=>window.scrollBy({top:delta,behavior:'instant'})",delta)
  page.wait_for_timeout(260)
 return delta

def capture_slider(page, loc, time_zero):
 """Record a real drag and verify one dependent visible value group."""
 if loc.count()!=1 or not loc.is_enabled():
  print('Slider locator unavailable',loc.count(),flush=True)
  return None
 prepare_slider_component_view(page,loc)
 setup=loc.evaluate_handle(r"""e => {
  if (!e.matches('input[type=range]') ||
      e.closest('form,[data-private],[data-secret],[data-sensitive]') ||
      getComputedStyle(e).direction !== 'ltr') return null;
  const group=e.closest('[role=group]');
  const trackEl=group?.querySelector('[data-slot="slider-track"]')||group||e;
  const thumbEl=e.closest('[data-slot="slider-thumb"]')||
    (getComputedStyle(e.parentElement).clipPath!=='none' ? e.parentElement.parentElement : e);
  const track=trackEl.getBoundingClientRect();
  const thumb=thumbEl.getBoundingClientRect();
  const min=Number(e.min||0), max=Number(e.max||100), value=Number(e.value);
  if (!(min<max) || track.left<0||track.right>innerWidth||
      track.top<0||track.bottom>innerHeight||track.width<120||track.width<2*track.height) return null;
  const left=track.left+1, right=track.right-1, y=thumb.top+thumb.height/2;
  const x=thumbEl!==e?thumb.left+thumb.width/2:
      track.left+8+(track.width-16)*(value-min)/(max-min);
  if (!(left<=x&&x<=right&&track.top<=y&&y<=track.bottom)) return null;
  const hit=document.elementFromPoint(x,y);
  // The visual thumb is distinct from the clipped screen-reader input in
  // accessible component libraries. Never drag an unrelated overlay.
  if (!(thumbEl!==e ? (hit===thumbEl||thumbEl.contains(hit)) : hit===e)) return null;
  const width=right-left, step=Math.abs(Number(e.step))/(max-min)||.01;
  const distance=Math.max(width*.245, width*step*1.2);
  const end=x+distance<=right?x+distance:Math.max(left,x-distance);
  let scope=group||e;
  for(let i=0;i<3&&scope.parentElement;i++)scope=scope.parentElement;
  const candidates=[];
  for(const node of scope.querySelectorAll('*')){
   if(node.childElementCount||node.closest('form,[data-private],[data-secret],[data-sensitive]'))continue;
   const r=node.getBoundingClientRect(), text=node.innerText?.trim();
   const output=!!(group&&group.contains(node)&&
       node.matches('output,[data-slot="slider-output"]'));
   if(!text||text.length>70||!/\d/.test(text)||r.width<6||r.height<10||
      r.top<(output?track.top-110:track.top+22)||
      r.bottom>Math.min(innerHeight,track.bottom+360)||
      r.left<0||r.right>innerWidth||node.checkVisibility?.({opacityProperty:true,visibilityProperty:true})===false)continue;
   candidates.push({node,text});
   if(candidates.length>=100)break;
  }
  if(!candidates.length)return null;
  return {e,group,value,x,end,y,track:track.toJSON(),candidates};
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
  result=setup.evaluate("s => {\n    const componentFor = "+COMPONENT_RECT_JS+";\n"+r"""
    if(!s.e.isConnected || Number(s.e.value)===s.value)return null;
    const changes=s.candidates.flatMap(({node,text})=>{
      if(!node.isConnected || node.checkVisibility?.({opacityProperty:true,visibilityProperty:true})===false)
        return [];
      const after=node.innerText?.trim(), r=node.getBoundingClientRect();
      const output=!!(s.group&&s.group.contains(node)&&
          node.matches('output,[data-slot="slider-output"]'));
      if(!after || after===text || !/\d/.test(after) || r.width<=6 || r.height<=10 ||
         r.left<0 || r.right>innerWidth ||
         r.top<(output?s.track.top-110:s.track.top) ||
         r.bottom>innerHeight || r.width>=innerWidth*.48) return [];
      const currency=/^\$\s*\d{1,4}(?:\s*\/\s*mo)?$/i;
      // Record a numeric claim only when both values and the billing period
      // are visible inside the same compact pricing row.
      const row=(node.parentElement?.innerText||'').replace(/\s+/g,' ').trim();
      const monthly=/\/\s*mo\b/i;
      const price=currency.test(text)&&currency.test(after) &&
        (monthly.test(text)&&monthly.test(after) || row.length<=90&&monthly.test(row));
      return [{r,node, price:price ? {before:text,after,period:'month'} : null}];
    });
    if(!changes.length)return null;
    const rects=changes.map(c=>c.r);
    const x=Math.min(...rects.map(r=>r.left)),y=Math.min(...rects.map(r=>r.top));
    const prices=changes.map(c=>c.price).filter(Boolean);
    const priced=changes.filter(c=>c.price);
    // A precise card boundary is only admitted for a single verified
    // numeric product outcome, not an unverified marketing container.
    const componentRect=priced.length===1?componentFor(priced[0].node):null;
    return {rect:{x,y,width:Math.max(...rects.map(r=>r.right))-x,
                 height:Math.max(...rects.map(r=>r.bottom))-y},
            componentRect,
            price:prices.length===1 ? prices[0] : null};
  }""")
  if result is None:
   print('Slider drag did not verify dependent text',flush=True)
   return None
  track=geometry['track']
  return {'kind':'slider_change','start':start,'t':released,'end':released,
          'evidence':'Range changed with a visible dependent numeric result',
          'targetRect':{k:track[k] for k in ('x','y','width','height')},
          'resultRect':result['rect'],'componentRect':result['componentRect'],
          'price_change':result['price'],'pointer_samples':points}
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

def capture(url:str,private:Path,report:dict,plan:dict,*,cursor_pack=None):
 quality=capture_quality()
 cursor_style=capture_cursor_style(cursor_pack)

 ensure_video_helper()
 validate_public_url(url)
 private=Path(private);private.mkdir(parents=True,exist_ok=True)
 actions={c['id']:c for c in report.get('controls',[])}
 headings={h['id']:h for h in report.get('headings',[])}
 selected=plan.get('action_ids',[])
 cursorless=(plan.get('mode')=='interactive' and len(selected)==1 and
             actions.get(selected[0],{}).get('kind')=='slider')
 beats=plan.get('beats',[]) if plan.get('mode')=='showcase' else []
 from backend.cursor_capture_js import build_cursor_script
 from backend.native60_capture import Native60Recorder,capture_mode,FULL_CHROME
 native_mode=capture_mode()=='x11grab60'
 if native_mode and quality['quality']!='high':
  raise RuntimeError('Native60 requires full-width DPR2 high quality capture')
 sequence_pace=plan.get('sequence_pace','balanced')
 if sequence_pace not in ('balanced','compact') or (sequence_pace=='compact' and not (plan.get('sequence') and native_mode and plan.get('local_only_action') is True)):
  raise ValueError('Compact pace requires verified local native60 sequence')
 compact=sequence_pace=='compact'
 native_recorder=Native60Recorder(private) if native_mode else None
 if native_recorder:
  try:native_recorder.start_display()
  except BaseException:
   native_recorder.close()
   raise
 passive_showcase=plan.get('mode')=='showcase' and not beats
 pace=plan.get('showcase_pace','balanced') if passive_showcase else 'balanced'
 pacing={'balanced':(500,360,1000,1.),'brisk':(180,240,650,1.15),
         'readable':(350,800,1100,1.)}
 if pace not in pacing:raise ValueError('Unsupported showcase pace')
 lead_ms,read_ms,final_ms,scroll_speed=pacing[pace]
 if compact:lead_ms,final_ms=180,350
 cursor_script=('' if cursorless or beats or passive_showcase else
                ARROW_CURSOR_JS if cursor_style in ('arrow','tabler-legacy') else
                CURSOR_JS if cursor_style=='circle' else
                build_cursor_script(cursor_style))
 events=[];moment=0.0
 with sync_playwright() as pw:
  browser_args=(native_recorder.launch_arguments() if native_recorder
                else ['--no-sandbox','--disable-dev-shm-usage'])
  try:
   b=pw.chromium.launch(
    headless=not native_mode,
    executable_path=str(FULL_CHROME if native_recorder else CHROME),
    env=native_recorder.browser_environment() if native_recorder else None,
    args=browser_args)
  except BaseException:
   if native_recorder:native_recorder.close()
   raise
  try:
   folder=private/'live-video';folder.mkdir(exist_ok=True)
   kwargs={'viewport':quality['viewport'],'device_scale_factor':quality['dpr'],
           'service_workers':'block'}
   if not native_recorder:
    kwargs.update(record_video_dir=str(folder),record_video_size=quality['video_size'])
   context=b.new_context(**kwargs)
   local_only=plan.get('local_only_action') is True
   loaded=False
   def capture_route(route):
    if local_only and loaded and route.request.is_navigation_request():
     return route.abort('blockedbyclient')
    return guard_route(route)
   context.route('**/*',capture_route)
   if passive_showcase:
    from scripts.session_capture import install_presentation_cleanup
    install_presentation_cleanup(context)
   if cursor_script:context.add_init_script(cursor_script)
   video_begin=time.monotonic()  # Legacy recorder starts before navigation.
   page=context.new_page()
   response=page.goto(url,wait_until='domcontentloaded',timeout=30000)
   if response and response.status>=400:raise RuntimeError('Source page returned HTTP '+str(response.status))
   validate_public_url(page.url)
   loaded=True
   page.wait_for_timeout(600)
   if cursor_script:page.evaluate(cursor_script)
   if passive_showcase:
    page.evaluate(r"""() => {
      for (const e of document.querySelectorAll('body *')) {
        if (getComputedStyle(e).position !== 'fixed') continue;
        const r=e.getBoundingClientRect(), t=e.innerText||'';
        if (r.width<120 || r.height<30 || r.height>innerHeight*.4 ||
            r.width*r.height>innerWidth*innerHeight*.32 || r.bottom<innerHeight*.7 ||
            !/^\s*(cookies?\s*(?:&|and)\s*analytics|cookie (?:consent|preferences|notice)|we use cookies)\b/i.test(t)) continue;
        const buttons=[...e.querySelectorAll('button')].map(b=>b.innerText||'').join(' ');
        if (/accept|allow/i.test(buttons) && /necessary|reject|decline|essential/i.test(buttons))
          e.style.setProperty('visibility','hidden','important');
      }
    }""")
   baseline=None
   if compact:
    from backend.curious_sequence import shot,panels
    page.mouse.move(930,530)
    before=shot(page);page.wait_for_timeout(350);steady=shot(page)
    baseline=(before,steady,panels(page))
    (private/'sequence-opening.png').write_bytes(before)
   if native_recorder:
    # Two independently read real browser frames align page pixels to the
    # full X11 window. The capture excludes browser chrome and is rejected
    # rather than guessed when the geometry differs.
    native_recorder.calibrate(page)
    video_begin=native_recorder.start_recording()
    video=None
   else:
    video=page.video
    if video is None:raise RuntimeError('Browser video recording unavailable')
   start=time.monotonic()
   lead_in=max(0,start-video_begin)
   page.mouse.move(930,530)
   page.wait_for_timeout(lead_ms)
   evidence=[]
   editorial_events=[]
   def mark(label):
    # Records nonsecret public evidence only; values, HAR, content excluded.
    page.screenshot(path=str(private/('mark-'+str(len(evidence))+'.jpg')),
                    type='jpeg',quality=60,animations='disabled')
    evidence.append({'phase':label,'time_s':round(time.monotonic()-start,2),
          'url':page.url.split('?')[0],'scroll':page.evaluate('Math.round(window.scrollY)')})
   if not compact:mark('opening')
   sequence_proof=None
   if plan.get('sequence') and local_only:
    from backend.curious_sequence import capture_sequence
    sequence_events,sequence_proof=capture_sequence(page,url,plan['sequence'],video_begin,pointer_to,baseline=baseline,compact=compact)
    editorial_events.extend(sequence_events)
    events.append({'id':'sequence','kind':'button','label':'Observed local option selection'})
    mark('sequence-result')
   elif plan.get('mode')=='interactive':
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
      generic_modal=safe_public_modal_opener(c)
      dialogs=page.locator('[role="dialog"]:visible,dialog[open]:visible')
      if (dialog_opener or generic_modal) and (
           dialogs.count() or not loc.evaluate("e => !e.form && !e.closest('form')")):
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
      if not same_canonical_public_origin(url,page.url):
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
      if generic_modal:
       # A non-submitting trigger is not an outcome by itself: a new real,
       # readable, bounded dialog must appear at this same public source.
       if page.url!=before or dialogs.count()!=1:
        raise RuntimeError('Source public modal did not open')
       dialog=dialogs.first
       region=dialog.bounding_box()
       vw,vh=(page.viewport_size[k] for k in ('width','height'))
       if (not region or region['width']<60 or region['height']<60
           or region['x']<0 or region['y']<0
           or region['x']+region['width']>vw
           or region['y']+region['height']>vh
           or len(dialog.inner_text().strip())<18
           or dialog.locator('input[type=password]').count()):
        raise RuntimeError('Source modal content not safely visible')
       editorial_events.extend([
        {'kind':'click','t':click_time,'label':c['text'],
         'semanticGoal':'Inspect source-verified public modal'},
        {'kind':'state_change','t':time.monotonic()-video_begin,
         'evidence':'Public modal visibly opened in source browser',
         'resultRect':region}])
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
       from backend.source_action_preflight import same_local_tab_route
       same_page=(same_local_tab_route(before,page.url) if local_only else page.url==before)
       if not same_page or not region:
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
    positions=[]
    for ident in plan.get('heading_ids',[])[:2]:
     h=headings.get(ident)
     if not h:continue
     loc=page.locator(h['selector'])
     if loc.count()!=1 or not loc.is_visible():continue
     label=' '.join(loc.inner_text().split())[:110]
     if label!=h['text']:continue
     positions.append(round(loc.evaluate("e=>e.getBoundingClientRect().top+scrollY")))
    positions=sorted(set(positions))
    height=page.evaluate('document.documentElement.scrollHeight')
    if passive_showcase and 'showcase_pace' in plan and len(positions)!=len(plan['heading_ids']):
     raise RuntimeError('Model-selected public heading is no longer source verified')
    if 'showcase_pace' in plan and passive_showcase and positions:
     pass
    elif height>1600 and (len(positions)<2 or max(positions)<550):
     positions=[min(height-720,round(height*.32)),min(height-720,round(height*.64))]
    elif not positions and height>900:
     positions=[min(height-720,round(height*.35)),min(height-720,round(height*.66))]
    for i,y in enumerate(positions[:2]):
     smooth_to(page,max(0,y-210),speed=scroll_speed)
     if not passive_showcase:pointer_to(page,900-i*240,340+i*75)
     page.wait_for_timeout(read_ms)
     mark('read-'+str(i))
   if editorial_events:
    page.wait_for_timeout(1450 if compact else 1950 if cursorless else 2000)
    editorial_events.append({'kind':'interaction_complete','t':time.monotonic()-video_begin})
   page.wait_for_timeout(final_ms)
   length=time.monotonic()-start
   # Keep Chromium and the verified viewport ALIVE until x11grab has
   # stopped and finalized. Closing the context first made Xvfb draw a
   # completely black final source frame, then the MP4 displayed a
   # one-frame black browser flash against the unchanged cloud stage.
   # The Playwright recorder still requires context.close() first.
   if native_recorder:
    native_proof=native_recorder.stop_recording()
    context.close()
   else:
    context.close()
    native_proof=None
   if native_recorder:
    output=native_proof['source_path']
   else:
    source=Path(video.path())
    output=private/'continuous-source.webm'
    shutil.copy2(source,output)
   receipt={'continuous_recording':True,'video':output.name,
      'sha256':hash_file(output),'duration_wall_s':round(length,3),
      'lead_in_seconds':round(lead_in,3),
      'actions':events,'evidence':evidence,'editorial_events':editorial_events,
      'subject_shots':subject_shots,'showcase_pace':pace if passive_showcase else None,
      'source_url':url.split('?')[0],'mode':plan.get('mode','showcase'),
      'capture_quality':quality['quality'],'source_dpr':quality['dpr'],
      'requested_video_size':quality['video_size'],
      'viewport_css_size':quality['viewport'],
      'cursorless':cursorless,'presentation_cursor':'composited-arrow' if cursorless else 'hidden' if beats or passive_showcase else cursor_style}
   if sequence_proof:
    receipt['sequence_proof']=sequence_proof
    receipt['sequence_pace']=sequence_pace
   if native_proof:
    # FPS is the actual recorded source stream, not the export bitrate or
    # postproduced frame rate. Original source hashes remain authoritative.
    receipt['native_source_capture']={
      k:v for k,v in native_proof.items() if k!='source_path'}
   (private/'continuous-capture.json').write_text(json.dumps(receipt,indent=2))
   return receipt
  finally:
   try:b.close()
   finally:
    if native_recorder:native_recorder.close()

if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser()
 ap.add_argument('--url',required=True)
 ap.add_argument('--out',type=Path,required=True)
 ap.add_argument('--inspection',type=Path,required=True)
 ap.add_argument('--plan',type=Path,required=True)
 from backend.cursor_capture_js import CURSOR_STYLES
 ap.add_argument('--cursor-pack',choices=(*CURSOR_STYLES,'circle','arrow'),default=None)
 a=ap.parse_args()
 print(json.dumps(capture(a.url,a.out,json.loads(a.inspection.read_text()),
  json.loads(a.plan.read_text()),cursor_pack=a.cursor_pack)),flush=True)
