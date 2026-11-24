"""Opt-in, bounded public SVG drawing research. Not a customer release path."""
from __future__ import annotations
import argparse,json,os,time,subprocess,tempfile,re,hashlib,sys,math
from pathlib import Path
from urllib.parse import urljoin
import cv2,numpy as np
from playwright.sync_api import sync_playwright
from backend.story_discovery import route_robots_allowed,focused_route_allowed,discover_public_product
from scripts.capture_safety import guard_route,validate_public_url
from backend.source_action_preflight import visible_authentication_barrier
from scripts.session_capture import MOCKUP_SCROLLBAR_STYLE
from backend.outcome_editorial_gate import evaluate
from backend.product_explorer import CHROME

def require(value,message):
    if not value: raise ValueError(message)

def select_drawing_route(research):
    """Require explicit freehand instructions on a unique observed public route."""
    origin=research["requested_url"]
    pages=[p for p in research["pages"] if
           focused_route_allowed(p["url"],origin) and
           re.search(r"freehand.{0,20}draw|drawing tool",p["title"],re.I) and
           re.search(r"start drawing|freehand draw",p["text"],re.I)]
    require(len(pages)==1,"No unique observed public drawing route")
    validate_public_url(pages[0]["url"])
    return pages[0]

SURFACE_JS="""()=>[...document.querySelectorAll('svg')].map(e=>{
 const r=e.getBoundingClientRect(),p=e.parentElement;
 return {tag:e.localName,id:e.id,box:{x:r.x,y:r.y,width:r.width,height:r.height},
   handler:[...p.attributes].some(a=>['@mousedown','onmousedown','@pointerdown','onpointerdown'].includes(a.name)),
   visible:e.checkVisibility(),safe:!e.closest('a,button,form,[role=dialog]')};
 }).filter(s=>s.id&&s.visible&&s.safe&&s.handler&&s.box.width>=400&&s.box.height>=300&&s.box.x>=0&&s.box.y>=0&&s.box.x+s.box.width<=innerWidth&&s.box.y+s.box.height<=innerHeight)"""
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def native(b):return {k:round(b[k]*2,4) for k in ('x','y','width','height')}
def crop(im,r):
 x,y,w,h=[round(r[k]) for k in ('x','y','width','height')];return im[y:y+h,x:x+w]
def change(a,b):return float(np.mean(np.max(cv2.absdiff(a,b),axis=2)>25))


def drawing_path(width,height,count=84):
    """A recognizable continuous heart, sampled by arc length in real pixels.

    Shape is an authored demo gesture, never a generated SVG or screenshot.
    Fit to a measured empty surface, leaving an ample safe border.
    """
    require(width>=400 and height>=300 and 48<=count<=100,"Invalid drawing geometry")
    t=np.linspace(0,2*np.pi,513)
    x=16*np.sin(t)**3
    y=-(13*np.cos(t)-5*np.cos(2*t)-2*np.cos(3*t)-np.cos(4*t))
    x-=.5*(x.max()+x.min());y-=.5*(y.max()+y.min())
    factor=min(.68*width/np.ptp(x),.72*height/np.ptp(y))
    px=.5*width+factor*x;py=.5*height+factor*y
    lengths=np.r_[0,np.cumsum(np.hypot(np.diff(px),np.diff(py)))]
    distance=np.linspace(0,lengths[-1],count+1)
    return list(zip(np.interp(distance,lengths,px)/width,
                    np.interp(distance,lengths,py)/height))



# Measure the editor's actual control visibility, including sticky overlays.
LAYOUT_JS="""id=>{
 const surface=document.getElementById(id);
 if(!surface)return null;
 let root=surface.parentElement;
 while(root&&root!==document.body&&!root.querySelector('input[type=range]'))root=root.parentElement;
 if(!root||root===document.body)return null;
 const rows=[...root.querySelectorAll('button,input,select,[role=button]')]
 .filter(e=>e.checkVisibility()&&!e.disabled&&e.type!=='hidden')
 .map(e=>{
   const r=e.getBoundingClientRect();
   const inside=r.x>=0&&r.y>=0&&r.right<=innerWidth&&r.bottom<=innerHeight;
   const points=[[.5,.5],[.15,.15],[.85,.15],[.15,.85],[.85,.85]];
   const covered=inside&&!points.every(([x,y])=>{const hit=document.elementFromPoint(r.x+r.width*x,r.y+r.height*y);return hit&&(e===hit||e.contains(hit))});
   return {inside,covered,w:r.width,h:r.height};
 }).filter(r=>r.w>=8&&r.h>=8);
 return {controls:rows.length,offscreen:rows.filter(r=>!r.inside).length,
         occluded:rows.filter(r=>r.covered).length};
}"""

def layout(page,surface):
    result=page.evaluate(LAYOUT_JS,surface["id"])
    require(result is not None and result["controls"]>=3,"No measurable editor controls")
    return result

def layout_ok(result):
    return result["controls"]>=3 and result["offscreen"]==0 and result["occluded"]==0

def choose_viewport(origin,u):
    require(focused_route_allowed(u,origin),"Unsafe source route")
    trials=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=CHROME,headless=True,args=["--no-sandbox"])
        try:
            c=browser.new_context(viewport={"width":1440,"height":900},
                                  service_workers="block",accept_downloads=False,permissions=[])
            def route(r):
                if r.request.is_navigation_request() and r.request.url not in (u,urljoin(u,"/robots.txt")):
                    return r.abort("blockedbyclient")
                return guard_route(r)
            c.route("**/*",route);c.route_web_socket("**/*",lambda ws:ws.close())
            require(route_robots_allowed(c,u),"Robots disallows route")
            page=c.new_page();res=page.goto(u,wait_until="domcontentloaded",timeout=25000)
            require(res and res.status==200 and page.url==u,"Unexpected layout route")
            page.wait_for_timeout(1000)
            for width,height in ((1440,900),(1600,1100),(1600,1160),(1600,1240)):
                page.set_viewport_size({"width":width,"height":height})
                page.wait_for_timeout(250)
                surfaces=page.evaluate(SURFACE_JS)
                if len(surfaces)!=1:continue
                row=layout(page,surfaces[0]);trials.append({"width":width,"height":height,**row})
                # Reserve extra footer room for newly revealed result controls.
                if layout_ok(row) and height>=1160:
                    return width,height,trials
        finally:browser.close()
    raise ValueError("No complete supported editor viewport: "+str(trials))

def capture(origin,u,out,display):
    require(__debug__,'Optimized Python disables research assertions')
    require(focused_route_allowed(u,origin),'Unsafe source route')
    require(re.fullmatch(r':[0-9]{2,3}',display),'Invalid dedicated display')
    validate_public_url(u)
    require(not Path('/tmp/.X11-unix/X'+display[1:]).exists(),'Display already in use')
    old_display=os.environ.get('DISPLAY')
    out.mkdir(mode=0o700,parents=True,exist_ok=False)
    width,height,trials=choose_viewport(origin,u)
    pixel_width,pixel_height=width*2,height*2
    (out/'layout.json').write_text(json.dumps({"trials":trials,"chosen":[width,height]},indent=2))
    duration=7.5
    x=subprocess.Popen(['Xvfb',display,'-screen','0',f'{pixel_width}x{pixel_height}x24','-nolisten','tcp','-ac'],stdout=subprocess.DEVNULL,stderr=(out/'xvfb.log').open('w'))
    try:
     time.sleep(.6);require(x.poll() is None,'Display unavailable');os.environ['DISPLAY']=display
     with sync_playwright() as pw,tempfile.TemporaryDirectory() as profile:
      c=pw.chromium.launch_persistent_context(profile,headless=False,executable_path='/opt/continuity-remote/chromium/chrome',args=['--no-sandbox','--disable-dev-shm-usage','--window-position=0,0',f'--window-size={width},{height}','--force-device-scale-factor=2','--app=about:blank'],viewport={'width':width,'height':height},device_scale_factor=2,service_workers='block',accept_downloads=False,permissions=[])
      try:
       def route(r):
        if r.request.is_navigation_request() and r.request.url not in (u,urljoin(u,'/robots.txt')):return r.abort('blockedbyclient')
        return guard_route(r)
       c.route('**/*',route)
       c.route_web_socket('**/*',lambda ws:ws.close())
       require(route_robots_allowed(c,u),'Robots disallows route')
       page=c.pages[0];res=page.goto(u,wait_until='domcontentloaded',timeout=25000);assert res.status==200 and page.url==u
       cdp=c.new_cdp_session(page);window=cdp.send('Browser.getWindowForTarget')['windowId'];cdp.send('Browser.setWindowBounds',{'windowId':window,'bounds':{'windowState':'fullscreen'}})
       page.wait_for_timeout(6000);page.add_style_tag(content=MOCKUP_SCROLLBAR_STYLE)
       assert page.evaluate('()=>[innerWidth,innerHeight,devicePixelRatio]')==[width,height,2]
       assert not visible_authentication_barrier(page)
       ss=page.evaluate(SURFACE_JS);require(len(ss)==1, 'No unique visible drawing surface')
       surface=ss[0];b=surface['box'];rect=native(b);loc=page.locator('[id='+json.dumps(surface['id'])+']');assert loc.count()==1
       def paths():return loc.evaluate("e=>[...e.querySelectorAll('path')].map(p=>p.getAttribute('d'))")
       initial=paths();require(len(initial)==0, 'Drawing surface is not empty')
       before_layout=layout(page,surface)
       require(layout_ok(before_layout),'Editor controls obstructed before recording')
       # Real local color preparation, never fabricated pixels or a claimed event.
       palette=page.evaluate("""()=>[...document.querySelectorAll('[style]')].map(e=>{
        const r=e.getBoundingClientRect(),bg=getComputedStyle(e).backgroundColor;
        return {x:r.x+r.width/2,y:r.y+r.height/2,w:r.width,h:r.height,bg,
          safe:e.checkVisibility()&&!e.closest('a,button,form,[role=dialog]')&&e.classList.contains('swatch')&&e.hasAttribute('@click')&&document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)===e};
       }).filter(e=>e.safe&&e.w>=20&&e.w<=100&&e.h>=20&&e.h<=100&&e.bg==='rgb(179, 51, 26)')""")
       if len(palette)==1:
        sw=palette[0];page.mouse.click(sw["x"],sw["y"]);page.wait_for_timeout(200)
        require(page.url==u and not visible_authentication_barrier(page),'Unsafe palette outcome')
        require(paths()==initial,'Palette unexpectedly modified drawing')
       require(page.url==u,'Unexpected route before gesture')
       pts=drawing_path(b['width'],b['height'],count=64)
       point=lambda pt:(b['x']+b['width']*pt[0],b['y']+b['height']*pt[1])
       pos=[b['x']+b['width']*.39,b['y']+b['height']*.24];page.mouse.move(*pos)
       page.screenshot(path=str(out/'before.png'),animations='disabled')
       page.wait_for_timeout(250);page.screenshot(path=str(out/'steady.png'),animations='disabled')
       steady=cv2.imread(str(out/'steady.png'));assert change(crop(cv2.imread(str(out/'before.png')),rect),crop(steady,rect))<.002
       video=out/'source.mp4';samples=[];events=[]
       enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','x11grab','-draw_mouse','0','-video_size',f'{pixel_width}x{pixel_height}','-framerate','60','-i',display,'-t',str(duration),'-c:v','libx264','-preset','ultrafast','-crf','14','-pix_fmt','yuv420p','-threads','4','-an','-movflags','+faststart',str(video)],stderr=(out/'record.log').open('w'))
       start=time.monotonic()
       def now():return round(time.monotonic()-start,6)
       def move(a,b):
        page.mouse.move(a,b);pos[:]=[a,b];t=now()
        if not samples or t>samples[-1]['t']:samples.append({'t':t,'x':round(a*2,4),'y':round(b*2,4)})
       def wait(t):time.sleep(max(0,t-now()))
       def travel(target,sec,ease=False):
        sx,sy=pos;tx,ty=target;start2=time.monotonic();n=max(8,round(sec*60))
        for k in range(1,n+1):
         v=k/n;q=v*v*(3-2*v) if ease else v
         move(sx+(tx-sx)*q,sy+(ty-sy)*q);time.sleep(max(0,start2+sec*v-time.monotonic()))
       try:
        move(*pos);wait(.12);travel(point(pts[0]),.57,True);wait(.83);move(*pos)
        require(page.evaluate('''([id,points])=>{const e=document.getElementById(id);return !!e&&points.every(([x,y])=>{const hit=document.elementFromPoint(x,y);return !!hit&&e.contains(hit)&&!hit.closest('a,button,form,[role=dialog]')})}''',[surface['id'],[point(pt) for pt in pts]]),'Drawing path occluded');page.mouse.down();down=now()
        label='Freehand SVG stroke';events.append({'kind':'pointerdown','actionKind':'draw_stroke','label':label,'t':down,'targetRect':rect})
        try:
         started=time.monotonic()
         for i,pt in enumerate(pts[1:],1):
          move(*point(pt));time.sleep(max(0,started+1.6*i/(len(pts)-1)-time.monotonic()))
        finally:page.mouse.up()
        up=now();events.append({'kind':'pointerup','label':label,'t':up});page.wait_for_timeout(280)
        assert page.url==u and not visible_authentication_barrier(page)
        final=paths();assert len(final)>len(initial)
        page.screenshot(path=str(out/'after.png'),animations='disabled');after=cv2.imread(str(out/'after.png'));delta=change(crop(steady,rect),crop(after,rect));assert delta>.004
        confirmed=now();assert confirmed<duration-2.0
        after_layout=layout(page,surface)
        (out/'layout.json').write_text(json.dumps({"trials":trials,"chosen":[width,height],
            "before":before_layout,"after":after_layout,"palettePrepared":len(palette)==1},indent=2))
        require(layout_ok(after_layout),'Editor controls obstructed after drawing')
        events.append({'kind':'verified_result','label':label,'t':confirmed,'resultRect':rect,'evidence':'Observed SVG path count increased and real drawing-surface pixels changed; local public freehand stroke'})
        wait(5.05);travel(point((.85,.78)),.52,True);wait(7.1)
        enc.wait(timeout=20);assert enc.returncode==0
       finally:
        if enc.poll() is None:enc.terminate();enc.wait(timeout=10)
       meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=width,height,avg_frame_rate,nb_frames','-of','json',str(video)]))['streams'][0]
       assert (meta['width'],meta['height'],meta['avg_frame_rate'],int(meta['nb_frames']))==(pixel_width,pixel_height,'60/1',450)
       # Match independent browser stills to decoded video frames: no chrome displacement.
       cap=cv2.VideoCapture(str(video))
       def read(t):
        cap.set(cv2.CAP_PROP_POS_FRAMES,round(t*60));ok,f=cap.read();assert ok;return f
       def mae(a,b):return float(np.mean(np.abs(cv2.resize(a,(480,300)).astype(float)-cv2.resize(b,(480,300)).astype(float))))
       first=read(.35);late=read(confirmed+.25);assert mae(first,steady)<4 and mae(late,after)<4,(mae(first,steady),mae(late,after))
       decoded_delta=change(crop(first,rect),crop(late,rect));assert decoded_delta>.004;cap.release()
       raw={'schema':'sauce-native-draw-research-v1','source':u,'capture':'Chromium X11 native DPR2 60fps','source_sha256':sha(video),'cursorless':True,'capture_rect':{'width':pixel_width,'height':pixel_height},'frameCount':450,'events':events,'pointer_samples':samples,'before_paths':len(initial),'after_paths':len(final),'surface_pixel_change':delta,'decoded_surface_pixel_change':decoded_delta,'creativeApproved':False}
       (out/'original-source-events.json').write_text(json.dumps(raw,indent=2));print(json.dumps({k:v for k,v in raw.items() if k!='pointer_samples'},indent=2),flush=True)
      finally:c.close()
    finally:
     if x.poll() is None:x.terminate();x.wait(timeout=6)
     if old_display is None:os.environ.pop('DISPLAY',None)
     else:os.environ['DISPLAY']=old_display


    return out/'original-source-events.json'

def run(url,out,display,*,request=None):
    out=Path(out).resolve();out.mkdir(mode=0o700,parents=True,exist_ok=False)
    result={"schema":"sauce-public-drawing-research-v1","source_url":url,
            "creative_approved":False,"production_ready":False,"decision":"not_admitted"}
    receipt=out/"receipt.json"
    def save():receipt.write_text(json.dumps(result,indent=2)+"\n")
    save()
    research=discover_public_product(url,out/"research",max_pages=3,route_focus=True)
    try:
        page=select_drawing_route(research)
    except ValueError as exc:
        result.update(reason=str(exc));save();return result
    result.update(route=page["url"],decision="capture_started");save()
    native_dir=out/"native"
    original=capture(url,page["url"],native_dir,display)
    from scripts.verified_capture_receipt_adapter import convert
    manifest=convert(native_dir/"source.mp4",original)
    manifest_path=native_dir/"manifest.json";manifest_path.write_text(json.dumps(manifest,indent=2)+"\n")
    result.update(decision="source_verified",source_sha256=sha(native_dir/"source.mp4"),manifest_sha256=sha(manifest_path));save()
    pair={"id":"a1","label":"Freehand stroke on observed SVG drawing surface","before":native_dir/"steady.png","after":native_dir/"after.png","before_sha256":sha(native_dir/"steady.png"),"after_sha256":sha(native_dir/"after.png")}
    review=evaluate(page["title"][:160], [pair],out/"editorial",request=request)
    result.update(editorial=review,decision="core_admitted" if review["admitted_id"]=="a1" else "editorial_not_admitted");save()
    return result

def render_admitted(out,music_root=None):
    """Render only an admitted, hash-verified private capture, using existing engine."""
    out=Path(out).resolve()
    receipt=out/"receipt.json";result=json.loads(receipt.read_text())
    native=out/"native";source=native/"source.mp4";manifest=native/"manifest.json"
    review=json.loads((out/"editorial"/"decision.json").read_text())
    require(result.get("schema")=="sauce-public-drawing-research-v1" and
            result.get("decision")=="core_admitted" and result.get("editorial")==review and
            review.get("admitted_id")=="a1" and review.get("decision",{}).get("decision")=="admit",
            "No admitted editorial decision")
    require(sha(source)==result["source_sha256"] and sha(manifest)==result["manifest_sha256"],
            "Native capture changed")
    from scripts.verified_capture_receipt_adapter import convert
    require(convert(source,native/"original-source-events.json")==json.loads(manifest.read_text()),
            "Native evidence no longer verifies")
    require(review["candidates"][0]["before_sha256"]==sha(native/"steady.png") and
            review["candidates"][0]["after_sha256"]==sha(native/"after.png"),
            "Editorial evidence changed")
    root=Path(__file__).resolve().parents[1]
    film=out/"film";film.mkdir(mode=0o700,exist_ok=False)
    plan=film/"plan.json";master=film/"master.mp4"
    def command(script,*args,timeout=120):
        with (film/(script+".log")).open("a") as log:
            subprocess.run([sys.executable,str(root/"scripts"/script),*map(str,args)],
                cwd=root,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=timeout)
    command("source_event_director.py","--source",source,"--manifest",manifest,"--out",plan)
    common=("--video",source,"--manifest",manifest,"--film-plan",plan)
    command("render_event_video.py",*common,"--validate-only")
    command("render_event_video.py",*common,"--output",master)
    final=master
    if music_root is not None:
        command("soundtrack_catalog.py","--root",Path(music_root).resolve(),"--film",master,
            "--foley",film/"source-verified-event-foley.wav",
            "--receipt",film/"source-verified-foley-receipt.json",
            "--role","transformation","--foley-gain","0","--out",film/"music")
        track=json.loads((film/"music"/"catalog.json").read_text())["selection"]["chosen"]
        final=film/"music"/(track+".mp4")
    from scripts.quality_preview_supervisor import analyze
    quality=analyze(final,{"source_path":str(source),"source_sha256":result["source_sha256"],
                     "event_manifest_path":str(manifest),"event_manifest_sha256":result["manifest_sha256"]},
                     seconds=json.loads(manifest.read_text())["duration"])
    (film/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    result.update(film_path=str(final),film_sha256=sha(final),plan_sha256=sha(plan),
                  direction_source="deterministic-source-event",quality=quality["verdict"])
    receipt.write_text(json.dumps(result,indent=2)+"\n")
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--url");p.add_argument("--out",type=Path,required=True)
    p.add_argument("--display");p.add_argument("--render",action="store_true")
    p.add_argument("--music-root",type=Path);a=p.parse_args()
    if a.url:
        if not a.display:p.error("--display required for fresh capture")
        result=run(a.url,a.out,a.display)
        if a.render and result["decision"]=="core_admitted":result=render_admitted(a.out,a.music_root)
    elif a.render:result=render_admitted(a.out,a.music_root)
    else:p.error("--url or --render required")
    print(json.dumps(result,indent=2))
