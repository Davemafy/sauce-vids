#!/usr/bin/env python3
"""Sauce session capture: verified browser pixels + structured interaction trace.

Capture a permitted, scripted web workflow once. This does NOT claim events
alone can reconstruct arbitrary JS applications. The saved screenshots are
evidence of real states; source assets and network state may also be needed.
No credentials, input values or sensitive URL query strings in the trace.
"""
from __future__ import annotations
import argparse,hashlib,json,os,re,time
from pathlib import Path
from session_contract import SCHEMA,safe_url,validate_actions
from cinematic_spec import enforce_hidpi,DPR_CHOICES,DEFAULT_DPR
from playwright.sync_api import sync_playwright

CAPTURE_JS=r"""
(() => {
 if (window.__sauceCapture) return;
 const timeline=[],start=performance.now();
 let currentPointer={x:0,y:0};
 const dialogs=new WeakSet();
 const sensitive=/password|token|secret|api.?key|credit|card|otp/i;
 const safeSelector=(e)=>{
   if(!(e instanceof Element)) return '';
   if(e.id && !sensitive.test(e.id)) return '#'+CSS.escape(e.id);
   const test=e.getAttribute('data-testid');
   const sauceId=e.getAttribute('data-sauce-id');
   if(test && !sensitive.test(test)) return '[data-testid="'+test.replace(/"/g,'')+'"]';
   if(sauceId && !sensitive.test(sauceId)) return '[data-sauce-id="'+sauceId.replace(/"/g,'')+'"]';
   const tag=e.tagName.toLowerCase();
   const name=e.getAttribute('name');
   if(name && !sensitive.test(name)) return tag+'[name="'+name.replace(/"/g,'')+'"]';
   const classes=[...e.classList].filter(x=>/^[a-z][a-z0-9_-]{1,30}$/i.test(x)).slice(0,2);
   return tag+(classes.length ? '.'+classes.join('.') : '');
 };
 const push=(type,e,override={})=>{
   const el=e?.target instanceof Element ? e.target : null;
   const box=el?.getBoundingClientRect();
   const css=el?getComputedStyle(el):null;
   const entry={
     t:Math.max(0,+(performance.now()-start).toFixed(3)),
     type,selector:safeSelector(el),
     box:box?{x:+box.x.toFixed(2),y:+box.y.toFixed(2),
       width:+box.width.toFixed(2),height:+box.height.toFixed(2)}:null,
     cursor:css?.cursor||'default',
     x:e&&typeof e.clientX==='number'?+e.clientX.toFixed(2):null,
     y:e&&typeof e.clientY==='number'?+e.clientY.toFixed(2):null,
     scroll:{x:window.scrollX,y:window.scrollY},
     ...override
   };
   timeline.push(entry);
 };
 let lastMove=-100;
 document.addEventListener('pointermove',e=>{
   currentPointer={x:e.clientX,y:e.clientY};
   const now=performance.now();
   if(now-lastMove>=24){lastMove=now;push('pointermove',e);}
 },true);
 function watchDialog(){
   try {
     for(const d of document.querySelectorAll('[role="dialog"]')){
       if(dialogs.has(d))continue;
       const rect=d.getBoundingClientRect(),style=getComputedStyle(d);
       if(rect.width>0&&rect.height>0&&style.visibility==='visible'&&
         Number(style.opacity)>.07){
         dialogs.add(d);
         push('dialog-visible',{target:d});
       }
     }
   }catch{}
   requestAnimationFrame(watchDialog);
 }
 requestAnimationFrame(watchDialog);
 for(const type of ['pointerdown','pointerup','click','mouseover','focusin'])
   document.addEventListener(type,e=>{
      if(type==='mouseover'){
        const prev=e.relatedTarget;
        if(prev && e.target===prev)return;
      }
      push(type,e);
   },true);
 document.addEventListener('input',e=>{
   const el=e.target;
   push('input',e,{redacted:true,
     length:el instanceof HTMLInputElement||el instanceof HTMLTextAreaElement?
       (sensitive.test(el.name||'')||el.type==='password' ? null:el.value.length):null});
 },true);
 document.addEventListener('scroll',e=>push('scroll',e),true);
 window.__sauceCapture={version:1,entries:timeline,flush:()=>timeline.splice(0),elapsed:()=>performance.now()-start,
   pointer:()=>currentPointer};
})();
"""

def approach_element(page,selector:str,duration_ms:int=640) -> None:
    """Record a real Bezier hand approach to a visible control, not teleport.

    The pointer must physically move through intermediate browser events.
    Quintic timing accelerates and decelerates; the small perpendicular
    curvature prevents an uncanny axis-aligned trajectory. No random noise.
    """
    import math
    locator=page.locator(selector).first
    locator.wait_for(state='visible',timeout=12000)
    locator.scroll_into_view_if_needed(timeout=12000)
    rect=locator.bounding_box()
    if not rect:raise RuntimeError('Approach target has no visible bounds')
    target_x=rect['x']+rect['width']/2.
    target_y=rect['y']+rect['height']/2.
    previous=page.evaluate('window.__sauceCapture.pointer()')
    x0,y0=float(previous['x']),float(previous['y'])
    dx,dy=target_x-x0,target_y-y0
    distance=math.hypot(dx,dy)
    if distance<6:return
    seconds=max(320,min(1100,int(duration_ms)))/1000.
    steps=max(22,min(32,round(seconds*33)))
    perp_x,perp_y=-dy/distance,dx/distance
    curve=min(42.,distance*.085)
    # Draw the real pointer path while the browser runs in real wall time.
    for index in range(1,steps+1):
        u=index/steps
        p=u*u*u*(u*(u*6-15)+10)
        bend=curve*math.sin(math.pi*p)
        x=x0+dx*p+perp_x*bend
        y=y0+dy*p+perp_y*bend
        page.mouse.move(x,y)
        # Chromium pointer dispatch itself has nonzero wall-clock cost.
        # Account for it to avoid turning a ~700ms gesture into 1.8s.
        page.wait_for_timeout(max(6,round(1000*seconds/steps*.42)))
    # Ensure a precise endpoint for clicking even after scroll events.
    page.mouse.move(target_x,target_y)


def run_workflow(page,actions:list[dict],images:Path,trace:list[dict]) -> list[dict]:
    phases=[]
    def snapshot(tag,action_index,action=None):
        image=images/(f'{action_index:03d}-{tag}.png')
        page.screenshot(path=str(image),scale='device',animations='disabled',caret='hide',timeout=30000)
        entry={'index':action_index,'name':tag,'file':image.name,
               'at_ms':round(page.evaluate('window.__sauceCapture.elapsed()'),3),
               'sha256':hashlib.sha256(image.read_bytes()).hexdigest(),
               'size_bytes':image.stat().st_size,
               'visible':page.evaluate("""() => ({
                 x:scrollX,y:scrollY,innerWidth,innerHeight,
                 title:document.title,readyState:document.readyState
               })""")}
        if action:
            loc=None
            if action.get('expect_selector'):loc=page.locator(action['expect_selector']).first
            elif action.get('expect_text'):loc=page.get_by_text(action['expect_text'],exact=False).first
            if loc and loc.count():
                box=loc.bounding_box()
                if box:
                    entry['focus_rect']={k:round(float(box[k]),2)
                                         for k in ('x','y','width','height')}
        trace.append(entry)
    snapshot('start',0)
    for i,action in enumerate(actions,1):
        kind=action['action']
        phase={'index':i,'action':kind,
               'at_ms':round(page.evaluate('window.__sauceCapture.elapsed()'),3)}
        if kind=='approach':
            approach_element(page,action['selector'],int(action.get('duration_ms',640)))
        elif kind in ('click','hover'):
            loc=page.locator(action['selector']).first
            loc.wait_for(state='visible',timeout=12000)
            if kind=='click':loc.click(timeout=12000)
            else:loc.hover(timeout=12000)
        elif kind=='fill':
            page.locator(action['selector']).first.fill(str(action.get('value','')),timeout=12000)
        elif kind=='move':
            page.mouse.move(float(action['x']),float(action['y']),steps=max(1,int(action.get('steps',12))))
        elif kind=='scroll':
            page.mouse.wheel(float(action.get('dx',0)),float(action.get('dy',0)))
        elif kind=='wait':
            page.wait_for_timeout(min(3000,int(action.get('ms',200))))
        page.wait_for_timeout(int(action.get('settle_ms',180)))
        if action.get('expect_selector') and not page.locator(action['expect_selector']).first.is_visible():
            raise RuntimeError(f'Action {i} did not produce expected element: {action["expect_selector"]}')
        if action.get('expect_text') and not page.get_by_text(action['expect_text'],exact=False).first.is_visible():
            raise RuntimeError(f'Action {i} did not produce expected text: {action["expect_text"]}')
        snapshot(kind,i,action)
        phase['end_ms']=round(page.evaluate('window.__sauceCapture.elapsed()'),3)
        phases.append(phase)
    return phases

def record(url:str, actions:list[dict],output:Path,
           width:int=1280,height:int=720,dpr:int=DEFAULT_DPR,
           capture_har:bool=False,browser_binary:str|None=None) -> dict:
    validate_actions(actions)
    if not (320<=width<=2560 and 240<=height<=1440):
        raise ValueError('Viewport outside safe bounds')
    enforce_hidpi(dpr)
    output.mkdir(parents=True,exist_ok=True)
    images=output/'states';images.mkdir(exist_ok=True)
    opts={'viewport':{'width':width,'height':height},'device_scale_factor':dpr,
          'service_workers':'block','permissions':['clipboard-read','clipboard-write']}
    if capture_har:
        opts.update(record_har_path=str(output/'network.har'),
                    record_har_content='embed',record_har_mode='full')
    with sync_playwright() as pw:
        chrome=browser_binary or os.environ.get('SAUCE_CHROME_BIN') or '/opt/devmcp-browsers/chromium_headless_shell-1254/chrome-headless-shell-linux64/chrome-headless-shell'
        browser=pw.chromium.launch(headless=True,executable_path=chrome,
                args=['--no-sandbox','--disable-dev-shm-usage'])
        context=browser.new_context(**opts)
        context.add_init_script(CAPTURE_JS)
        page=context.new_page()
        response=page.goto(url,wait_until='domcontentloaded',timeout=35000)
        if response and response.status>=400:raise RuntimeError('Page returned '+str(response.status))
        page.evaluate(CAPTURE_JS)
        page.wait_for_timeout(500)
        # The opening composition is the relevant product surface, not an
        # unrelated homepage above the clicked UI. Stage this before t=0.
        if actions and actions[0]['action']=='approach':
            page.locator(actions[0]['selector']).first.scroll_into_view_if_needed()
            page.wait_for_timeout(260)
        page.mouse.move(round(width*.78),round(height*.73))
        page.wait_for_timeout(70)
        actions_meta=[]
        states=[]
        started=time.monotonic()
        for i,action in enumerate(actions):
            actions_meta.append({k:v for k,v in action.items()
                      if k not in ('value','password','secret')})
        phases=run_workflow(page,actions,images,states)
        for item,phase in zip(actions_meta,phases):item.update(phase)
        captured=page.evaluate('window.__sauceCapture.flush()')
        # Browser event timestamps are authoritative for gesture ordering;
        # do not estimate physical cursor movement from click centers.
        page_info={'url':safe_url(page.url),'title':page.title(),
                   'viewport':[width,height],'dpr':dpr,
                   'browser':'Chromium via Playwright'}
        context.close()
        browser.close()
    session={'schema':SCHEMA,'source_url':safe_url(url),
             'page':page_info,'workflow':actions_meta,'events':captured,
             'states':states,'replay_status':'unverified',
             'capture_elapsed_wall_s':round(time.monotonic()-started,3),
             'har':'network.har' if capture_har else None,
             'warnings':['Screenshots are actual Chromium pixels. An event log alone cannot reconstruct arbitrary page state.',
               'Text input values are intentionally not stored. Supply a separate authorized workflow to replay inputs.',
               'A HAR can contain private data: keep recordings local and review before sharing.']}
    dest=output/'session.json';dest.write_text(json.dumps(session,indent=2))
    return session

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--url',required=True)
    p.add_argument('--workflow',required=True,type=Path)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--width',type=int,default=1280)
    p.add_argument('--height',type=int,default=720)
    p.add_argument('--dpr',type=int,choices=DPR_CHOICES,default=DEFAULT_DPR)
    p.add_argument('--har',action='store_true')
    args=p.parse_args()
    actions=json.loads(args.workflow.read_text())
    result=record(args.url,actions,args.out,args.width,args.height,args.dpr,args.har)
    print(json.dumps({'file':str(args.out/'session.json'),'events':len(result['events']),
         'states':len(result['states']),'page':result['page']},indent=2))
if __name__=='__main__':main()
