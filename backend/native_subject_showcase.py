"""Private autonomous native-60 public subject showcase, using Sauce's existing cloud stage.

No model selectors, actions, source coordinates, or fabricated product states.
Each selected subject is measured in Chromium, within one continuous recording,
and the camera crop is bounded by the measured subject. Not an authenticated demo.
"""
from __future__ import annotations
import argparse, json, math, os, subprocess, tempfile, time, hashlib
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright
from backend.curious_showcase import Conversation, _media
from scripts.capture_safety import validate_public_url, guard_route
from scripts.session_capture import install_presentation_cleanup
from scripts.capture_stagehand_verified_native import exact_first_party
from scripts.cloud_shadow_stage import render_cloud_overview
from scripts.quality_preview_supervisor import analyze

CSS=(1440,810)
NATIVE=(2880,1620)
FPS=60

DISCOVER=r"""() => {
 const root=document.querySelector('main,[role=main]')||document.body;
 const blocked='nav,footer,header,form,[role=dialog],[data-private],[data-secret],[data-sensitive]';
 const skip=/frequently asked|\bfaq\b|cookie|privacy policy|pricing|testimonials|trusted by|leading global institutions|\bmerch\b|shop|join the waitlist|be the first/i;
 const text=e=>(e.innerText||e.getAttribute('alt')||'').replace(/\s+/g,' ').trim();
 const box=e=>{let r=e.getBoundingClientRect();return {x:r.x+scrollX,y:r.y+scrollY,width:r.width,height:r.height}};
 const good=e=>{if(!e||e.closest(blocked))return false;let r=box(e);return e.checkVisibility({checkOpacity:true,checkVisibilityCSS:true})&&r.width>=240&&r.height>=140&&r.height<=innerHeight*.80&&r.width<=innerWidth*.96&&r.x>=0&&r.x+r.width<=innerWidth+.5};
 function path(e){let a=[];for(let n=e;n&&n!==document.body;n=n.parentElement){let sib=[...n.parentElement.children].filter(x=>x.tagName===n.tagName);a.unshift(n.tagName.toLowerCase()+':nth-of-type('+(sib.indexOf(n)+1)+')')}return 'body > '+a.join(' > ')}
 const rows=[], seen=new Set();
 function add(e,label,section,kind){if(!good(e)||!label||skip.test(section)||skip.test(label)||seen.has(e))return;seen.add(e);rows.push({id:'s'+rows.length,selector:path(e),label:label.slice(0,180),section:section.slice(0,140),kind,rect:box(e)})}
 const hero=root.querySelector('h1');
 if(hero){let best=null;for(let e=hero.parentElement,d=0;e&&d<6;e=e.parentElement,d++){if(good(e)&&e.querySelectorAll('img,svg,canvas').length&&text(e).length<1100)best=e}
 if(best)add(best,text(hero),text(hero),'hero')}
 for(const media of [...root.querySelectorAll('img,canvas,video')].slice(0,160)){
   if(media.closest(blocked))continue;
   let m=box(media);if(m.width<220||m.height<120)continue;
   let section=media.closest('section,article');let title=section?.querySelector('h2,h1');let heading=title?text(title):'';
   if(!section||!title||skip.test(heading)||title===hero)continue;
   for(let e=media.parentElement,d=0;e&&e!==section&&d<6;e=e.parentElement,d++){
      let label=text(e.querySelector('h3,h4,figcaption,p')||e),r=box(e);
      if(good(e)&&label.length>=8&&label.length<180&&r.height>=m.height+20&&r.width>=m.width-2&&text(e).length<500){
         add(e,label,heading,'product-illustration');break;
      }
   }
 }
 return rows.slice(0,12)
}"""

def write(path,value):
    Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n")
def sha(path):
    with Path(path).open("rb") as f:return hashlib.file_digest(f,"sha256").hexdigest()
def probe(path):
    return json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","stream=width,height,avg_frame_rate,nb_frames:format=duration","-of","json",str(path)],text=True))
def same(page,url):
    if not exact_first_party(url,page.url):raise RuntimeError("Public source left allowed host")
def scroll_position(page,row):
    loc=page.locator(row["selector"])
    if loc.count()!=1 or not loc.is_visible():raise ValueError("Subject no longer uniquely visible")
    b=loc.bounding_box()
    if not b:raise ValueError("No source geometry")
    y=page.evaluate("scrollY")+b["y"]
    return max(0,round(y-(CSS[1]-b["height"])/2))
def measure(page,row):
    loc=page.locator(row["selector"])
    if loc.count()!=1 or not loc.is_visible():raise ValueError("Lost subject")
    b=loc.bounding_box()
    if not b or not all(math.isfinite(v) for v in b.values()):raise ValueError("Invalid bounds")
    if min(b["x"],b["y"])<-.5 or b["x"]+b["width"]>CSS[0]+.5 or b["y"]+b["height"]>CSS[1]+.5:
        raise ValueError("Subject not fully in original source")
    if row["kind"]=="hero":
        text=loc.evaluate("e=>(e.querySelector('h1')?.innerText||'').replace(/\\s+/g,' ').trim()")
        if text[:180]!=row["label"]:raise ValueError("Hero identity changed")
    else:
        text=loc.evaluate("e=>(e.querySelector('h3,h4,figcaption,p')?.innerText||e.innerText||'').replace(/\\s+/g,' ').trim()")
        if text[:180]!=row["label"]:raise ValueError("Subject identity changed")
    return {k:round(v*2,3) for k,v in b.items()}
def shortlist(raw,rows):
    valid={r["id"]:r for r in rows if r["kind"]!="hero"}
    if not isinstance(raw,dict) or not isinstance(raw.get("shots"),list):return None
    shots=raw["shots"]
    if len(shots)!=2:return None
    out=[]
    for s in shots:
        if not isinstance(s,dict) or not isinstance(s.get("id"),str) or s["id"] not in valid or s.get("camera") not in ("detail","context"):return None
        out.append({"id":s["id"],"camera":s["camera"]})
    if out[0]["id"]==out[1]["id"]:return None
    return sorted(out,key=lambda s:valid[s["id"]]["rect"]["y"])
def fallback(rows):
    choices=[r for r in rows if r["kind"]!="hero"]
    if len(choices)<2:raise ValueError("Insufficient public product subjects")
    a=choices[0];b=next((r for r in choices if r["section"]!=a["section"]),choices[1])
    return [{"id":a["id"],"camera":"detail"},{"id":b["id"],"camera":"detail"}]
def crop_for(rect,mode):
    """Bounded isotropic detail crop, with full subject and padding inside source."""
    if mode not in ("detail","context"):raise ValueError("Unsupported camera mode")
    x,y,w,h=[float(rect[k]) for k in ("x","y","width","height")]
    sw,sh=NATIVE
    if not all(math.isfinite(v) for v in (x,y,w,h)) or min(w,h)<=0 or x<-.5 or y<-.5 or x+w>sw+.5 or y+h>sh+.5:raise ValueError("Invalid source rect")
    pad=1.13 if mode=="detail" else 1.32
    width=min(sw,max(sw/(1.72 if mode=="detail" else 1.28),w*pad,h*pad*16/9))
    width=min(sw,math.ceil(width/32)*32)
    height=width*9/16
    left=max(0,min(sw-width,x+w/2-width/2))
    top=max(0,min(sh-height,y+h/2-height/2))
    if left>x+.6 or top>y+.6 or left+width<x+w-.6 or top+height<y+h-.6:raise ValueError("Camera clips subject")
    return np.array([left,top,width,height],dtype=float)
def ease(t):
    p=max(0.,min(1.,t));return p**3*(10-15*p+6*p*p)
def camera_crop(rect,mode,t,hero=False):
    wide=np.array([0.,0.,*NATIVE])
    target=crop_for(rect,mode)
    # Source scroll ends before the close-up. Hero starts moving immediately.
    progress=ease((t-(.10 if hero else 1.15))/(1.0 if hero else .92))
    return wide+(target-wide)*progress
def continuous_crop(beats, shots, t):
    """One C2 camera curve, wide during real scrolls, no resets or cuts."""
    wide=np.array([0.,0.,*NATIVE])
    for beat,shot in zip(beats,shots):
        a,b,c,d=(beat[k] for k in ("push_start","push_end","release_start","release_end"))
        if a<=t<=d:
            weight=ease((t-a)/(b-a)) if t<b else 1. if t<=c else 1.-ease((t-c)/(d-c))
            target=crop_for(beat["rect"],shot["camera"])
            return wide+(target-wide)*weight
    return wide

def compile_camera_direction(source, direction):
    """Compile a source-bound, cut-free editorial JSON into checked camera keys.

    Targets are observed subjects or wide. No arbitrary source pixel rectangles.
    A close-up may only follow its actual arrival; co-visible subjects on the
    same measured scroll row may share that arrival and transition directly.
    """
    if (not isinstance(direction,dict) or direction.get("schema")!="sauce-continuous-camera-v1"
            or direction.get("source_sha256")!=source["sha256"]):
        raise ValueError("Camera direction does not bind to source")
    beats=source["beats"]; scrolls=source["scrolls"]
    observed={b["id"]:b for b in beats}
    if len(scrolls)!=len(beats)-1:raise ValueError("Missing arrival evidence")
    windows={beats[0]["id"]:(0.,scrolls[0]["start"])}
    for i,b in enumerate(beats[1:]):
        lo=hi=i
        while lo>0 and scrolls[lo-1]["target_scroll_css"]==scrolls[i]["target_scroll_css"]:lo-=1
        while hi+1<len(scrolls) and scrolls[hi+1]["target_scroll_css"]==scrolls[i]["target_scroll_css"]:hi+=1
        windows[b["id"]]=(scrolls[lo]["end"],scrolls[hi+1]["start"] if hi+1<len(scrolls) else source["seconds"])
    raw=direction.get("keys")
    if not isinstance(raw,list) or not 2<=len(raw)<=24:raise ValueError("Invalid camera key count")
    keys=[]
    for k in raw:
        if not isinstance(k,dict) or type(k.get("t")) not in (float,int) or not math.isfinite(k["t"]):
            raise ValueError("Invalid camera time")
        t=float(k["t"]); target=k.get("target"); mode=k.get("mode")
        if not 0<=t<=source["seconds"] or keys and t<=keys[-1][0]:
            raise ValueError("Camera clock must be monotonic")
        if target=="wide":crop=np.array([0.,0.,*NATIVE])
        elif isinstance(target,str) and target in observed and mode in ("detail","context"):
            lo,hi=windows[target]
            if not lo<=t<=hi:raise ValueError("Camera target not yet observed or no longer visible")
            crop=crop_for(observed[target]["rect"],mode)
        else:raise ValueError("Unknown camera target")
        keys.append((t,crop,target))
    if keys[0][0]!=0 or abs(keys[-1][0]-source["seconds"])>1e-6:
        raise ValueError("Camera plan must cover entire source")
    # Real vertical scrolls must retain wide framing; zero-distance transitions
    # do not impose a pointless wide reset between adjacent subjects.
    prev=0
    for scroll in scrolls:
        target=scroll["target_scroll_css"]
        if target!=prev:
            for n in range(math.ceil(scroll["start"]*FPS),math.floor(scroll["end"]*FPS)+1):
                if not np.allclose(sample_camera_direction(keys,n/FPS),[0,0,*NATIVE]):
                    raise ValueError("Detail camera during unverified scroll")
        prev=target
    crops=np.array([sample_camera_direction(keys,n/FPS) for n in range(source["frames"])])
    if np.abs(np.diff(crops,axis=0)).max(initial=0)>45:raise ValueError("Camera exceeds per-frame motion limit")
    return keys

def sample_camera_direction(keys,t):
    for (a,x,_),(b,y,_) in zip(keys,keys[1:]):
        if t<=b:return x+(y-x)*ease((t-a)/(b-a))
    return keys[-1][1].copy()

def viewer_camera_direction(source, shots):
    """Compile attention -> transport -> readable payoff from measured arrivals.

    This is a showcase, so a detail is an illustration, not a verified action.
    Never invent pointer events. Adjacent subjects on the same settled page
    can share attention without an unnecessary zoom-out. Keep the last payoff
    in view rather than spending its reading time on a decorative release.
    """
    beats, scrolls = source["beats"], source["scrolls"]
    if len(beats) != len(shots) or len(scrolls) != len(beats)-1:
        raise ValueError("Viewer plan needs a measured subject sequence")
    if [b["id"] for b in beats] != [s["id"] for s in shots]:
        raise ValueError("Viewer plan subject mismatch")
    keys = []
    def key(t, target="wide", mode=None):
        t = float(t)
        item = {"t":t,"target":target}
        if mode is not None:item["mode"]=mode
        if keys and t <= keys[-1]["t"]:
            raise ValueError("Insufficient source time for viewer attention")
        keys.append(item)
    def focus(t,i):
        key(t,shots[i]["id"],shots[i]["camera"])
    # Quintic easing peak speed is 1.875 times average. Keep margin below
    # the existing 45 source-pixel/frame movement gate.
    wide=np.array([0.,0.,*NATIVE])
    targets=[crop_for(b["rect"],s["camera"]) for b,s in zip(beats,shots)]
    def transition(a,b):
        return max(.55,1.875*float(np.abs(a-b).max())/(FPS*40))
    def travel_after(i):
        return i < len(scrolls) and scrolls[i]["target_scroll_css"] != (
            scrolls[i-1]["target_scroll_css"] if i else 0)
    key(0)
    key(.10)
    focus(.10+transition(wide,targets[0]),0)
    for i in range(len(beats)):
        if i:
            if travel_after(i-1):
                arrival=float(scrolls[i-1]["end"])
                key(arrival+.04)
                focus(arrival+.04+transition(wide,targets[i]),i)
            else:
                # The page has not moved: establish the next subject by a
                # smooth pan after the preceding reading hold, not a reset.
                focus(keys[-1]["t"]+max(1.25,transition(targets[i-1],targets[i])),i)
        if i==len(beats)-1:
            hold=source["seconds"]-keys[-1]["t"]
            if hold<.7:raise ValueError("Insufficient final payoff hold")
            # Preserve the result through a restrained contextual release;
            # the final image still contains the entire measured subject.
            end=float(source["seconds"])
            context=crop_for(beats[i]["rect"],"context")
            release=max(1.25,transition(targets[i],context))
            if shots[i]["camera"]=="detail" and hold>=1.45+release and not np.allclose(targets[i],context):
                focus(end-release,i)
                key(end,shots[i]["id"],"context")
            else:
                focus(end,i)
        elif travel_after(i):
            departure=float(scrolls[i]["start"])
            release=departure-.03-transition(targets[i],wide)
            if release-keys[-1]["t"]<.25:
                raise ValueError("Insufficient context before travel")
            focus(release,i)
            key(departure-.03)
        else:
            # Use the otherwise idle same-row source interval for comprehension.
            hold_end=max(keys[-1]["t"]+.85,float(scrolls[i]["start"])-.45)
            focus(hold_end,i)
    direction={"schema":"sauce-continuous-camera-v1","source_sha256":source["sha256"],
               "director":"viewer-attention-v1","keys":keys}
    compile_camera_direction(source,direction)
    return direction

def render_viewer_plan(source,shots,out):
    """Keep existing safe camera as a disclosed fallback for tight source clocks."""
    try:
        direction=viewer_camera_direction(source,shots)
    except ValueError as exc:
        direction=None
        fallback_reason=str(exc)
    else:
        fallback_reason=None
    master,stats=render(source,shots,out,direction=direction)
    write(out/"viewer-direction.json",{"direction":direction,"fallback_reason":fallback_reason,
          "scope":"public illustrations, not verified product interaction",
          "creative_approved":False})
    return master,stats

def scroll_seconds(distance):
    return min(3.0,max(1.15,abs(distance)/850.))

def capture_continuous(page,url,rows,folder,display):
    """A single uninterrupted X11 capture. Only pre-recording scouting jumps."""
    same(page,url)
    page.evaluate("()=>window.scrollTo({top:0,behavior:'instant'})")
    page.wait_for_timeout(500)
    hero=measure(page,rows[0])
    targets=[scroll_position(page,row) for row in rows[1:]]
    if targets!=sorted(targets) or targets[0]<100:raise ValueError("Subjects must advance through page")
    durations=[scroll_seconds(y-x) for x,y in zip([0,*targets],targets)]
    # Reserve a reading hold after each true arrival, and release before travel.
    total=math.ceil((2.15+sum(durations)+2*3.05+.35)*FPS)/FPS
    path=folder/"continuous-native.mp4"
    command=["ffmpeg","-v","error","-y","-f","x11grab","-draw_mouse","0",
             "-video_size","2880x1620","-framerate","60","-i",display,
             "-t",str(total),"-c:v","libx264","-preset","ultrafast","-crf","13",
             "-pix_fmt","yuv420p","-threads","4","-an",str(path)]
    beats=[]; travel=[]; checks=[]
    def now():return time.monotonic()-clock
    def wait_until(t):
        remaining=t-now()
        if remaining>0:page.wait_for_timeout(remaining*1000)
    def check(row,rect):
        png=page.screenshot(type="png")
        img=cv2.imdecode(np.frombuffer(png,np.uint8),cv2.IMREAD_COLOR)
        checks.append((now(),cv2.resize(img,(160,90))))
    with (folder/"continuous.log").open("w") as log:
        recorder=subprocess.Popen(command,stdout=subprocess.DEVNULL,stderr=log)
        clock=time.monotonic()
        try:
            beats.append({"id":rows[0]["id"],"rect":hero,"push_start":.15,"push_end":.95,
                          "release_start":1.35,"release_end":2.05})
            wait_until(.35);check(rows[0],hero)
            deadline=2.15
            for row,target,duration in zip(rows[1:],targets,durations):
                wait_until(deadline)
                start=now()
                # Smooth real browser motion, using the same easing grammar as existing scroll.
                page.evaluate("""async ({y,ms})=>{let a=scrollY,d=y-a;await new Promise(resolve=>{
                  let start=performance.now();function tick(n){let u=Math.min(1,(n-start)/ms);
                    let q=u*u*u*(10-15*u+6*u*u);
                    window.scrollTo({top:a+d*q,behavior:'instant'});
                    if(u<1)requestAnimationFrame(tick);else resolve();}
                  requestAnimationFrame(tick);});}""",{"y":target,"ms":duration*1000})
                page.wait_for_timeout(130)
                same(page,url)
                rect=measure(page,row)
                arrival=now()
                travel.append({"start":round(start,4),"end":round(arrival,4),"target_scroll_css":target})
                # Use true measured arrival, never a guessed source timestamp.
                beat={"id":row["id"],"rect":rect,"push_start":arrival+.12,
                      "push_end":arrival+1.02,"release_start":arrival+1.98,
                      "release_end":arrival+2.75}
                beats.append(beat)
                wait_until(arrival+1.35);check(row,rect)
                if max(abs(measure(page,row)[k]-rect[k]) for k in rect)>12:
                    raise ValueError("Subject moved during hold")
                deadline=arrival+2.80
            if beats[-1]["release_end"]>total-.10:raise ValueError("Recording budget missed final release")
            recorder.wait(timeout=total+15)
            if recorder.returncode:raise RuntimeError("Native X11 capture failed")
        finally:
            if recorder.poll() is None:recorder.terminate();recorder.wait(timeout=5)
    stream=probe(path)["streams"][0]
    if (stream["width"],stream["height"],stream["avg_frame_rate"],int(stream["nb_frames"]))!=(*NATIVE,"60/1",round(total*FPS)):
        raise ValueError("Source native geometry or frame clock failed")
    cap=cv2.VideoCapture(str(path));deltas=[]
    try:
        for t,reference in checks:
            cap.set(cv2.CAP_PROP_POS_FRAMES,min(round(t*FPS),round(total*FPS)-1))
            ok,frame=cap.read()
            if not ok or frame.shape!=(NATIVE[1],NATIVE[0],3):raise ValueError("Capture geometry mismatch")
            delta=float(np.abs(reference.astype(float)-cv2.resize(frame,(160,90)).astype(float)).mean())
            if delta>18:raise ValueError(f"Native viewport mismatch: {delta:.3f}")
            deltas.append(round(delta,3))
    finally:cap.release()
    return {"path":str(path),"sha256":sha(path),"frames":round(total*FPS),"seconds":total,
            "beats":beats,"scrolls":travel,"viewport_match_mae":deltas,"source_fps":60,
            "source_dpr":2,"intentional_cuts_seconds":[]}

def render(source,shots,out,*,direction=None):
    cv2.setNumThreads(2)
    out.mkdir(exist_ok=False,parents=True)
    master=out/"master-1080p60.mp4"
    if sha(source["path"])!=source["sha256"]:raise ValueError("Native source changed")
    keys=compile_camera_direction(source,direction) if direction is not None else None
    cmd=["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","bgr24","-s","1920x1080",
         "-r","60","-i","pipe:0","-an","-c:v","libx264","-preset","fast","-crf","17",
         "-threads","4","-movflags","+faststart",str(master)]
    encoder=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    cap=cv2.VideoCapture(source["path"]);stats=[];last=None;max_step=0.
    try:
        for n in range(source["frames"]):
            ok,frame=cap.read()
            if not ok or frame.shape!=(NATIVE[1],NATIVE[0],3):raise RuntimeError("Incomplete native frame")
            crop=sample_camera_direction(keys,n/FPS) if keys is not None else continuous_crop(source["beats"],shots,n/FPS)
            if last is not None:max_step=max(max_step,float(np.max(np.abs(crop-last))))
            last=crop
            x,y,w,h=crop
            matrix=np.array([[1920/w,0,-x*1920/w],[0,1080/h,-y*1080/h]],np.float32)
            cropped=cv2.warpAffine(frame,matrix,(1920,1080),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
            encoder.stdin.write(render_cloud_overview(
                cropped,stage_preset="cloud_window_sky_v1").tobytes())
    finally:
        cap.release();encoder.stdin.close()
        err=encoder.stderr.read()
        if encoder.wait(timeout=120):raise RuntimeError("Encoding failed: "+err.decode()[-500:])
    for beat,shot in zip(source["beats"],shots):
        final=crop_for(beat["rect"],shot["camera"])
        stats.append({"id":beat["id"],"zoom":round(NATIVE[0]/final[2],3),
                      "subject_area_fraction":round(beat["rect"]["width"]*beat["rect"]["height"]/(final[2]*final[3])*.875**2,4)})
    subprocess.run(["ffmpeg","-v","error","-xerror","-i",str(master),"-f","null","-"],check=True,timeout=90)
    if int(probe(master)["streams"][0]["nb_frames"])!=source["frames"]:raise RuntimeError("Output source clock changed")
    write(out/"camera-receipt.json",{"source_sha256":source["sha256"],"source_frames":source["frames"],
          "output_frames":source["frames"],"cuts":0,"max_crop_step_source_px":round(max_step,4),
          "shots":stats,"direction_schema":direction.get("schema") if direction else None,"master_sha256":sha(master),"creative_approved":False})
    return master,stats

def run(url,out,display):
    validate_public_url(url)
    if not display.startswith(":") or not display[1:].isdigit() or not 160<=int(display[1:])<=220:raise ValueError("Private numeric X11 display required")
    out=Path(out).resolve();out.mkdir(mode=0o700,parents=True,exist_ok=False)
    conv=Conversation(out/"curiosity")
    with (out/"xvfb.log").open("w") as log:
        xvfb=subprocess.Popen(["Xvfb",display,"-screen","0","2880x1620x24","-nolisten","tcp","-ac"],stdout=log,stderr=subprocess.STDOUT)
        old=os.environ.get("DISPLAY")
        try:
            time.sleep(.5)
            if xvfb.poll() is not None:raise RuntimeError("Dedicated display unavailable")
            os.environ["DISPLAY"]=display
            with tempfile.TemporaryDirectory(prefix="sauce-native-showcase-") as profile,sync_playwright() as pw:
                context=pw.chromium.launch_persistent_context(profile,headless=False,executable_path="/opt/continuity-remote/chromium/chrome",args=["--no-sandbox","--disable-dev-shm-usage","--window-position=0,0","--window-size=1440,810","--force-device-scale-factor=2","--app=about:blank","--disable-extensions"],viewport={"width":1440,"height":810},device_scale_factor=2,accept_downloads=False,service_workers="block",permissions=[],reduced_motion="reduce")
                try:
                    context.route("**/*",guard_route);install_presentation_cleanup(context)
                    page=context.pages[0];response=page.goto(url,wait_until="domcontentloaded",timeout=30000)
                    if response and response.status>=400:raise RuntimeError("Public source not available")
                    same(page,url)
                    cdp=context.new_cdp_session(page)
                    window=cdp.send('Browser.getWindowForTarget')['windowId']
                    cdp.send('Browser.setWindowBounds',{'windowId':window,'bounds':{'windowState':'fullscreen'}})
                    page.wait_for_timeout(450)
                    page.evaluate("document.fonts.ready");page.wait_for_timeout(650)
                    if page.evaluate("()=>[innerWidth,innerHeight,devicePixelRatio]")!=[1440,810,2]:raise ValueError("Unexpected native viewport")
                    page.evaluate(r"""() => {for(const e of document.querySelectorAll('body *')){let r=e.getBoundingClientRect(),t=e.innerText||'';if(getComputedStyle(e).position==='fixed'&&r.height<innerHeight*.4&&r.bottom>innerHeight*.7&&/^\s*(cookies?\s*(?:&|and)\s*analytics|cookie (?:consent|notice)|we use cookies)\b/i.test(t)&&/accept|allow/i.test(t)&&/necessary|decline|reject|essential/i.test(t))e.style.setProperty('visibility','hidden','important')}}""")
                    rows=page.evaluate(DISCOVER)
                    if len(rows)<3 or rows[0]["kind"]!="hero":raise ValueError("No three useful source subjects")
                    # Private contact sheet, source pixels only plus external evidence labels.
                    sheet=Image.new("RGB",(1200,((len(rows)+2)//3)*270),"#f3f3f3");draw=ImageDraw.Draw(sheet)
                    eligible=[]
                    for row in rows:
                        try:
                            target=scroll_position(page,row);page.evaluate("(y)=>window.scrollTo(0,y)",target);page.wait_for_timeout(230)
                            b=measure(page,row)
                            png=page.screenshot(type="png")
                            img=cv2.imdecode(np.frombuffer(png,np.uint8),cv2.IMREAD_COLOR)
                            x,y,w,h=[round(b[k]) for k in ("x","y","width","height")]
                            tile=Image.fromarray(cv2.cvtColor(img[y:y+h,x:x+w],cv2.COLOR_BGR2RGB));tile.thumbnail((390,225))
                            i=len(eligible);left=i%3*400;top=i//3*270
                            sheet.paste(tile,(left+(400-tile.width)//2,top));draw.text((left+8,top+228),row["id"]+" "+row["label"][:56],fill="#222")
                            eligible.append(row)
                        except (ValueError,RuntimeError):continue
                    rows=eligible
                    if len(rows)<3 or rows[0]["kind"]!="hero":raise RuntimeError("Source subject evidence incomplete")
                    sheet=sheet.crop((0,0,1200,((len(rows)+2)//3)*270));sheet.save(out/"subjects.jpg",quality=87)
                    write(out/"subjects.json",rows)
                    packet=json.dumps([{k:r[k] for k in ("id","label","section","kind")} for r in rows],ensure_ascii=False)
                    media=(_media(out/"subjects.jpg","image/jpeg",2*1024*1024),)
                    first=conv.ask("Hey Gemini, I want to make a short beautiful film of this product. Look at the REAL subject contact sheet. Imagine you are the viewer, not the director. What do you understand in the first second? What question makes you want to see more? Which two real details answer that question and leave you with one useful outcome? What would you skip because it repeats an idea or makes you read too much? Be curious about the visual evidence, not marketing claims. These are public illustrations, not verified live app actions. Think like a motion designer: what deserves a close-up and why? "+packet,media=media,phase="explore")
                    chosen=None
                    if first:
                        answer=conv.ask("But what does a stranger know after the first detail that they did not know before? What question does it raise, and does the second detail actually answer it? Compare other visible cards and choose a stronger sequence if needed. Would the viewer understand it on a phone? Prefer a readable payoff to a flashy visual. Avoid redundant claims. The hero already opens. Choose two distinct subject IDs in downward source order, each with a detail or context camera. This is ONE unbroken scrolling film; choose subjects that make a natural continuous journey, no cuts or jumps. No invented UI. Return JSON only: {\"shots\":[{\"id\":\"s1\",\"camera\":\"detail\"},{\"id\":\"s2\",\"camera\":\"context\"}],\"reason\":\"why\"}. "+packet,media=media,json_mode=True,phase="challenge")
                        try:chosen=shortlist(json.loads(answer),rows)
                        except (TypeError,ValueError):pass
                    directed=chosen is not None
                    shots=[{"id":rows[0]["id"],"camera":"detail"},*(chosen or fallback(rows))]
                    write(out/"direction.json",{"shots":shots,"gemini_directed":directed,"calls":conv.calls})
                    folder=out/"native";folder.mkdir()
                    lookup={r["id"]:r for r in rows}
                    recording=capture_continuous(page,url,[lookup[s["id"]] for s in shots],folder,display)
                finally:context.close()
        finally:
            if old is None:os.environ.pop("DISPLAY",None)
            else:os.environ["DISPLAY"]=old
            xvfb.terminate();xvfb.wait(timeout=5)
    manifest=out/"source-receipt.json"
    write(manifest,{"url":url,"events":[],"continuous_recording":True,**recording})
    evidence={"source_path":recording["path"],"source_sha256":recording["sha256"],
              "event_manifest_path":str(manifest),"event_manifest_sha256":sha(manifest)}
    master,stats=render_viewer_plan(recording,shots,out/"baseline")
    qa=analyze(master,evidence);write(out/"baseline"/"encoded-quality.json",qa)
    selected="baseline"
    selected_shots=shots
    selected_stats=stats
    if directed and conv.calls<4:
        response=conv.ask("We made it. Watch this exact unbroken MP4. Watch as a first-time viewer. At what timestamp do you understand the product? Where does your attention drift during travel? Does the next detail answer the question raised by the previous one? Can you read the final payoff without rushing? Which actual shot is too distant or crops context? Be specific with timestamps. You can revise only the two selected camera modes, detail or context; no new source footage or fake actions. Return JSON only: {\"critique\":\"under 100 words\",\"shots\":[{\"id\":\"same first ID\",\"camera\":\"detail\"},{\"id\":\"same second ID\",\"camera\":\"context\"}]}. Current shots "+json.dumps(shots[1:]),media=(_media(master,"video/mp4",12*1024*1024),),json_mode=True,phase="watch-and-challenge")
        try:
            raw=json.loads(response);revision=shortlist(raw,rows)
        except (ValueError,TypeError):revision=None
        if revision and [s["id"] for s in revision]==[s["id"] for s in shots[1:]] and revision!=shots[1:]:
            revised,rs=render_viewer_plan(recording,[shots[0],*revision],out/"revision")
            rq=analyze(revised,evidence);write(out/"revision"/"encoded-quality.json",rq)
            # No new QA finding; select only if measured framing improves.
            if not ({f["code"] for f in rq["findings"]}-{f["code"] for f in qa["findings"]}) and sum(s["subject_area_fraction"] for s in rs)>sum(s["subject_area_fraction"] for s in stats)+.03:
                selected="revision"
                selected_shots=[shots[0],*revision]
                selected_stats=rs
    result={"selected":selected,"master":str(out/selected/"master-1080p60.mp4"),"gemini_directed":directed,"calls":conv.calls,"creative_approved":False,"native_fps":60,"source_dpr":2,"cuts":0,"shots":selected_shots,"camera_stats":selected_stats}
    write(out/"result.json",result);return result

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--url",required=True);p.add_argument("--out",required=True,type=Path);p.add_argument("--display",default=":183");a=p.parse_args()
    print(json.dumps(run(a.url,a.out,a.display),indent=2),flush=True)
