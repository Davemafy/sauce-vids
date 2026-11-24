"""Private autonomous native-60 public subject showcase, using Sauce's existing cloud stage.

No model selectors, actions, source coordinates, or fabricated product states.
Each selected subject is measured in Chromium, each shot is an actual recording,
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
from backend.live_capture import smooth_to
from scripts.capture_safety import validate_public_url, guard_route
from scripts.session_capture import install_presentation_cleanup
from scripts.capture_stagehand_verified_native import exact_first_party
from scripts.cloud_shadow_stage import render_cloud_overview
from scripts.quality_preview_supervisor import analyze

CSS=(1440,810)
NATIVE=(2880,1620)
FPS=60
SECONDS=3.2

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
def render(scenes,shots,out):
    cv2.setNumThreads(2)
    out.mkdir(exist_ok=False,parents=True)
    master=out/"master-1080p60.mp4"
    cmd=["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","bgr24","-s","1920x1080","-r","60","-i","pipe:0","-an","-c:v","libx264","-preset","fast","-crf","17","-threads","4","-movflags","+faststart",str(master)]
    encoder=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    stats=[]
    try:
        for scene,shot in zip(scenes,shots):
            path=Path(scene["path"])
            if sha(path)!=scene["sha256"]:raise ValueError("Native source changed")
            cap=cv2.VideoCapture(str(path));frames=0
            try:
                while frames<round(SECONDS*FPS):
                    ok,frame=cap.read()
                    if not ok or frame.shape!=(NATIVE[1],NATIVE[0],3):raise RuntimeError("Incomplete native frame")
                    t=frames/FPS
                    x,y,w,h=camera_crop(scene["rect"],shot["camera"],t,scene["kind"]=="hero")
                    # Warp source once into a 16:9 crop at native-scale resolution;
                    # existing cloud compositor downsamples without changing source colors.
                    iw,ih=1920,1080
                    matrix=np.array([[iw/w,0,-x*iw/w],[0,ih/h,-y*ih/h]],np.float32)
                    cropped=cv2.warpAffine(frame,matrix,(iw,ih),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
                    encoder.stdin.write(render_cloud_overview(cropped).tobytes())
                    frames+=1
            finally:cap.release()
            final=crop_for(scene["rect"],shot["camera"])
            stats.append({"id":scene["id"],"frames":frames,"zoom":round(NATIVE[0]/final[2],3),
                          "subject_area_fraction":round(scene["rect"]["width"]*scene["rect"]["height"]/(final[2]*final[3])*.875**2,4),
                          "settled_subject_within_crop":True})
    finally:
        encoder.stdin.close()
        err=encoder.stderr.read()
        if encoder.wait(timeout=120):raise RuntimeError("Encoding failed: "+err.decode()[-500:])
    subprocess.run(["ffmpeg","-v","error","-xerror","-i",str(master),"-f","null","-"],check=True,timeout=90)
    meta=probe(master)
    if int(meta["streams"][0]["nb_frames"])!=round(SECONDS*FPS)*len(scenes):raise RuntimeError("Output length changed")
    write(out/"camera-receipt.json",{"source_segments":scenes,"shots":stats,"master_sha256":sha(master),"creative_approved":False})
    return master,stats

def capture_scene(page,url,row,folder,display):
    same(page,url)
    target=scroll_position(page,row)
    page.evaluate("(y)=>window.scrollTo(0,y)",target)
    page.wait_for_timeout(400)
    rect=measure(page,row)
    hero=row["kind"]=="hero"
    # Small real scroll, not a synthesized transition or a long empty page pass.
    if not hero:
        page.evaluate("(y)=>window.scrollTo(0,y)",max(0,target-145))
        page.wait_for_timeout(140)
    path=folder/(row["id"]+".mp4")
    command=["ffmpeg","-v","error","-y","-f","x11grab","-draw_mouse","0","-video_size","2880x1620","-framerate","60","-i",display,"-t",str(SECONDS),"-c:v","libx264","-preset","ultrafast","-crf","13","-pix_fmt","yuv420p","-threads","4","-an",str(path)]
    with (folder/(row["id"]+".log")).open("w") as log:
        recorder=subprocess.Popen(command,stdout=subprocess.DEVNULL,stderr=log)
        try:
            page.wait_for_timeout(160)
            if not hero:smooth_to(page,target)
            page.wait_for_timeout(150)
            same(page,url)
            observed=measure(page,row)
            if max(abs(observed[k]-rect[k]) for k in rect)>12:raise ValueError("Subject shifted during capture")
            recorder.wait(timeout=22)
            if recorder.returncode:raise RuntimeError("Native X11 capture failed")
        finally:
            if recorder.poll() is None:recorder.terminate();recorder.wait(timeout=5)
    stream=probe(path)["streams"][0]
    if (stream["width"],stream["height"],stream["avg_frame_rate"],int(stream["nb_frames"]))!=(*NATIVE,"60/1",round(SECONDS*FPS)):
        raise ValueError("Source native geometry or frame clock failed")
    # Compare actual recorded pixels to independent Chromium screenshot at settled state.
    reference=cv2.imdecode(np.frombuffer(page.screenshot(type="png"),np.uint8),cv2.IMREAD_COLOR)
    cap=cv2.VideoCapture(str(path));cap.set(cv2.CAP_PROP_POS_FRAMES,round(SECONDS*FPS)-8);ok,frame=cap.read();cap.release()
    if not ok or reference.shape!=frame.shape:raise ValueError("Screen capture geometry mismatch")
    delta=float(np.abs(cv2.resize(reference,(160,90)).astype(float)-cv2.resize(frame,(160,90)).astype(float)).mean())
    if delta>18:raise ValueError(f"Native capture differs from browser viewport: {delta:.3f}")
    return {"id":row["id"],"kind":row["kind"],"label":row["label"],"path":str(path),"sha256":sha(path),"rect":observed,"source_fps":60,"source_frames":round(SECONDS*FPS),"viewport_match_mae":round(delta,3)}

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
                    first=conv.ask("Hey Gemini, I want to make a short beautiful film of this product. Look at the REAL subject contact sheet. What makes someone care? Which two actual product details best communicate that, beyond the hero? Be curious about the visual evidence, not marketing claims. These are public illustrations, not verified live app actions. Think like a motion designer: what deserves a close-up and why? "+packet,media=media,phase="explore")
                    chosen=None
                    if first:
                        answer=conv.ask("But would your choices still work for a stranger on a phone? Compare the actual cards; avoid redundant claims. The hero already opens. Choose two distinct subject IDs in downward source order, each with a detail or context camera. No invented UI. Return JSON only: {\"shots\":[{\"id\":\"s1\",\"camera\":\"detail\"},{\"id\":\"s2\",\"camera\":\"context\"}],\"reason\":\"why\"}. "+packet,media=media,json_mode=True,phase="challenge")
                        try:chosen=shortlist(json.loads(answer),rows)
                        except (TypeError,ValueError):pass
                    directed=chosen is not None
                    shots=[{"id":rows[0]["id"],"camera":"context"},*(chosen or fallback(rows))]
                    write(out/"direction.json",{"shots":shots,"gemini_directed":directed,"calls":conv.calls})
                    folder=out/"native";folder.mkdir()
                    lookup={r["id"]:r for r in rows}
                    scenes=[capture_scene(page,url,lookup[s["id"]],folder,display) for s in shots]
                finally:context.close()
        finally:
            if old is None:os.environ.pop("DISPLAY",None)
            else:os.environ["DISPLAY"]=old
            xvfb.terminate();xvfb.wait(timeout=5)
    # Source join is just the actual ordered native recordings, not recreated UI.
    concat=out/"source-list.txt";concat.write_text("".join("file '"+s["path"].replace("'","'\\''")+"'\n" for s in scenes))
    source=out/"source-native.mp4"
    subprocess.run(["ffmpeg","-v","error","-y","-f","concat","-safe","0","-i",str(concat),"-c","copy",str(source)],check=True,timeout=45)
    manifest=out/"source-receipt.json";write(manifest,{"url":url,"native_fps":60,"dpr":2,"segments":scenes,"events":[],"intentional_cuts_seconds":[SECONDS,2*SECONDS],"source_sha256":sha(source)})
    evidence={"source_path":str(source),"source_sha256":sha(source),"event_manifest_path":str(manifest),"event_manifest_sha256":sha(manifest)}
    master,stats=render(scenes,shots,out/"baseline")
    qa=analyze(master,evidence);write(out/"baseline"/"encoded-quality.json",qa)
    selected="baseline"
    selected_shots=shots
    selected_stats=stats
    if directed and conv.calls<4:
        response=conv.ask("We made it. Watch this exact MP4. Where does the camera help or hurt readability? Which actual shot is too distant or crops context? Be specific with timestamps. You can revise only the two selected camera modes, detail or context; no new source footage or fake actions. Return JSON only: {\"critique\":\"under 100 words\",\"shots\":[{\"id\":\"same first ID\",\"camera\":\"detail\"},{\"id\":\"same second ID\",\"camera\":\"context\"}]}. Current shots "+json.dumps(shots[1:]),media=(_media(master,"video/mp4",12*1024*1024),),json_mode=True,phase="watch-and-challenge")
        try:
            raw=json.loads(response);revision=shortlist(raw,rows)
        except (ValueError,TypeError):revision=None
        if revision and [s["id"] for s in revision]==[s["id"] for s in shots[1:]] and revision!=shots[1:]:
            revised,rs=render(scenes,[shots[0],*revision],out/"revision")
            rq=analyze(revised,evidence);write(out/"revision"/"encoded-quality.json",rq)
            # No new QA finding; select only if measured framing improves.
            if not ({f["code"] for f in rq["findings"]}-{f["code"] for f in qa["findings"]}) and sum(s["subject_area_fraction"] for s in rs)>sum(s["subject_area_fraction"] for s in stats)+.03:
                selected="revision"
                selected_shots=[shots[0],*revision]
                selected_stats=rs
    result={"selected":selected,"master":str(out/selected/"master-1080p60.mp4"),"gemini_directed":directed,"calls":conv.calls,"creative_approved":False,"native_fps":60,"source_dpr":2,"shots":selected_shots,"camera_stats":selected_stats}
    write(out/"result.json",result);return result

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--url",required=True);p.add_argument("--out",required=True,type=Path);p.add_argument("--display",default=":183");a=p.parse_args()
    print(json.dumps(run(a.url,a.out,a.display),indent=2),flush=True)
