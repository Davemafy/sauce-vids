#!/usr/bin/env python3
"""Source-true public URL -> reversible tab-action Chromium movie + event receipt.

Experimental, explicit test-host allowlist only. Interactions restricted to
anonymous visible ARIA tabs, same-path SPA transitions, with GET/HEAD-only
routing and full genuine browser pixel verification. No arbitrary button
clicking, logins, forms, auth, screenshots reconstructed as source footage or
synthetic pointer paths. Original capture is continuous native X11/60fps.
"""
from __future__ import annotations
import argparse,hashlib,json,math,os,re,subprocess,time
from pathlib import Path
from urllib.parse import urlsplit,urljoin
from urllib.robotparser import RobotFileParser
import cv2,numpy as np
from playwright.sync_api import sync_playwright
from capture_safety import validate_public_url,guard_route
from session_capture import MOCKUP_SCROLLBAR_STYLE,install_presentation_cleanup

FPS=60
SIZE=(1440,900)
DPR=2
DISPLAY=":118"
CHROME="/srv/devmcp-workspaces/5c407ce984e7defcf77da3f1f9cb7f67/sauce-v05-release/studio/.tmp/educational-pilot/browsers/chromium-1254/chrome-linux64/chrome"
HEADLESS="/opt/devmcp-browsers/chromium_headless_shell-1254/chrome-headless-shell-linux64/chrome-headless-shell"
SKIP_LABEL=re.compile(r"(?i)sign.?in|sign.?up|register|create account|purchase|delete|"
                      r"remove|send|email|checkout|subscribe|billing|submit|buy now|reset|log.?out|payment")
TAB_JS=r"""() => [...document.querySelectorAll('[role="tab"]')].map((e,i)=>{
 const r=e.getBoundingClientRect(),root=e.closest('[role="tablist"]');
 const group=root?.getBoundingClientRect();
 const name=(e.getAttribute('aria-label')||e.innerText||'').replace(/\s+/g,' ').trim();
 const panel=e.getAttribute('aria-controls');
 const bad=e.closest('form,nav,header,footer,[role="navigation"],[role="menu"]');
 return {name,index:i,selected:e.getAttribute('aria-selected')==='true',
  state:e.getAttribute('data-state'),panel,
  group:group?[Math.round(group.x),Math.round(group.y),Math.round(group.width)]:[],
  rect:[r.x,r.y,r.width,r.height],inDisallowedContainer:!!bad,
  disabled:e.disabled||e.getAttribute('aria-disabled')==='true',
  hasUnsafeForm:!!e.closest('form'),
  isLink:e.matches('a[href]')};
}).filter(x=>x.rect[2]>34&&x.rect[3]>18&&x.rect[0]>=0&&x.rect[1]>=0&&
 x.rect[0]+x.rect[2]<=innerWidth&&x.rect[1]+x.rect[3]<=innerHeight)"""
PANEL_JS=r"""name => {
 const t=[...document.querySelectorAll('[role="tab"]')]
    .find(e=>(e.getAttribute('aria-label')||e.innerText||'').replace(/\s+/g,' ').trim()===name);
 if(!t)return null;
 const a=t.getAttribute('aria-selected'),state=t.getAttribute('data-state');
 const id=t.getAttribute('aria-controls'),panel=id?document.getElementById(id):null;
 const r=panel?.getBoundingClientRect();
 const b=t.getBoundingClientRect();
 return {selected:a==='true'||state==='active',
  control:[b.x,b.y,b.width,b.height],
  result:r?[r.x,r.y,r.width,r.height]:null,
  panelState:panel?.getAttribute('data-state')||null,
  panelVisible:panel?getComputedStyle(panel).display!=='none':false};
}"""

def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for part in iter(lambda:f.read(1<<20),b""):h.update(part)
    return h.hexdigest()

def as_rect(raw,*,dpr=1):
    if raw is None or len(raw)!=4:raise ValueError("Missing genuine DOM bounds")
    vals=[float(v) for v in raw]
    x,y,w,h=vals
    if not all(math.isfinite(v) for v in vals) or x<0 or y<0 or w<20 or h<18:
        raise ValueError("Invalid actual DOM element")
    if x+w>SIZE[0]+.1 or y+h>SIZE[1]+.1:
        raise ValueError("Actual DOM rectangle outside screen")
    return {k:round(v*dpr,3) for k,v in zip(("x","y","width","height"),vals)}

def screenshot_bgr(page):
    png=page.screenshot(type="png",animations="disabled",caret="hide")
    a=cv2.imdecode(np.frombuffer(png,dtype=np.uint8),cv2.IMREAD_COLOR)
    if a is None or a.shape[:2]!=(SIZE[1]*page.evaluate("devicePixelRatio"),SIZE[0]*page.evaluate("devicePixelRatio")):
        raise ValueError("Original Chromium screenshot geometry mismatch")
    return a

def wait_for_real_initial_preview(page,*,timeout_steps=13):
    """Start filming ONLY after genuine source UI has populated and settled.

    This waits and examines live DOM/browser screenshots; it does not inject
    replacements, hide loading animations, alter product data or synthesize
    a finished page. Fail closed if anonymous public preview remains blank.
    """
    last=None
    for _ in range(timeout_steps):
        panes=page.evaluate(r"""() => [...document.querySelectorAll('[role="tab"][aria-selected="true"]')]
          .map(tab=>{
            let target=document.getElementById(tab.getAttribute('aria-controls'));
            if(!target)return null;
            const r=target.getBoundingClientRect();
            return {x:r.x,y:r.y,w:r.width,h:r.height,
              chars:(target.innerText||'').trim().length};
          }).filter(x=>x&&x.x>innerWidth*.20&&x.w>innerWidth*.44&&
            x.h>innerHeight*.40).sort((a,b)=>b.w*b.h-a.w*a.h)[0] || null""")
        if panes:
            native=screenshot_bgr(page)
            scale=page.evaluate("devicePixelRatio")
            x,y,w,h=[round(panes[k]*scale) for k in ("x","y","w","h")]
            crop=native[y:y+h,x:x+w]
            if crop.size:
                gray=cv2.cvtColor(crop,cv2.COLOR_BGR2GRAY)
                contrast=float(gray.std())
                # Require content to exist BEFORE starting the X11 movie.
                # A screenshot of a loading spinner is not an intro shot.
                if panes["chars"]>=500 and contrast>=22:
                    if last is not None:
                        prev=last
                        if prev.shape==crop.shape:
                            changed=float(np.mean(
                                np.max(cv2.absdiff(prev,crop),axis=2)>16))
                            if changed<.05:
                                return {"originalVisibleTextChars":panes["chars"],
                                        "originalPreviewGrayStd":round(contrast,3),
                                        "lastPreviewChangeFraction":round(changed,5)}
                    last=crop
                else:
                    last=None
        page.wait_for_timeout(340)
    raise ValueError("Original public preview still blank, skeletal or unstable")

def score_actual_tab(page,name,before):
    clicked=page.get_by_role("tab",name=name,exact=True)
    clicked.click(timeout=2500)
    page.wait_for_timeout(440)
    state=page.evaluate(PANEL_JS,name)
    if not state or not state["selected"] or not state["panelVisible"]:
        raise ValueError("No actual browser state change")
    target=as_rect(state["result"],dpr=1)
    if target["width"]<240 or target["height"]<180:
        raise ValueError("Tab does not expose an actual substantial result panel")
    after=screenshot_bgr(page)
    r=target
    x,y,w,h=(round(r[k]) for k in ("x","y","width","height"))
    region=after[y:y+h,x:x+w]
    diff=np.max(cv2.absdiff(before[y:y+h,x:x+w],region),axis=2)
    changed=float(np.mean(diff>16))
    if changed<.045:raise ValueError("No substantive genuine result pixel change")
    # A tab may replace a rich preview with a mostly empty "connect your
    # website" instruction. Large pixel diff is NOT a cinematic payoff.
    # Admit only visibly populated, contrast-bearing original DOM panels.
    # The content count is observed from rendered real DOM, not generated
    # by the model or injected into the page.
    actual_text_chars=page.evaluate(r"""(name) => {
      const t=[...document.querySelectorAll('[role="tab"]')]
         .find(e=>(e.getAttribute('aria-label')||e.innerText||'').replace(/\s+/g,' ').trim()===name);
      const panel=t?document.getElementById(t.getAttribute('aria-controls')):null;
      return panel?(panel.innerText||'').trim().length:0;
    }""",name)
    gray=cv2.cvtColor(region,cv2.COLOR_BGR2GRAY)
    contrast=float(gray.std())
    if actual_text_chars<550 or contrast<22:
        raise ValueError("Real tab changed pixels but lacks readable visual substance")
    return {"score":round(changed,6),"name":name,"controlRect":as_rect(state["control"]),
            "resultRect":target,"selected":True,
            "observedVisibleTextChars":actual_text_chars,
            "originalResultGrayStd":round(contrast,3)}

def _robots_allowed(context,url):
    robot=context.new_page()
    try:
        target=urljoin(url,"/robots.txt")
        response=robot.goto(target,wait_until="domcontentloaded",timeout=12000)
        if response and response.status==404:return True
        if not response or response.status!=200:
            raise ValueError("Cannot verify site robots policy")
        value=robot.locator("body").inner_text(timeout=3000)[:160000]
        parser=RobotFileParser()
        parser.parse(value.splitlines())
        return parser.can_fetch("SauceBasicPreviewBot/0.1",url)
    finally:robot.close()

def _prepare_browser(page,url):
    response=page.goto(url,wait_until="domcontentloaded",timeout=28000)
    if not response or response.status>=400:raise ValueError("No successful public page response")
    final=urlsplit(page.url);asked=urlsplit(url)
    if final.hostname!=asked.hostname or final.path.rstrip("/")!=asked.path.rstrip("/") or final.query:
        raise ValueError("Unexpected navigation/redirect outside requested public page")
    page.evaluate("document.fonts.ready")
    page.add_style_tag(content=MOCKUP_SCROLLBAR_STYLE)
    page.wait_for_timeout(850)
    page.evaluate("window.scrollTo(0,0)")
    return page

def _candidates(page):
    rows=page.evaluate(TAB_JS)
    group_counts={}
    for row in rows:
        key=tuple(row.get("group",[]))
        group_counts[key]=group_counts.get(key,0)+1
    options=[]
    for row in rows:
        name=row["name"]
        if not 1<=len(name)<=42 or SKIP_LABEL.search(name) or row["selected"]:
            continue
        if row["inDisallowedContainer"] or row["disabled"] or row["isLink"] or row["hasUnsafeForm"]:
            continue
        group=tuple(row["group"])
        if len(group)!=3 or group_counts[group]<3:continue
        options.append(row)
    # The experimental whitelist does not authorize unstructured "buttons."
    return options[:12]

def _new_context(browser,*,dpr=1):
    context=browser.new_context(viewport=dict(width=SIZE[0],height=SIZE[1]),
        device_scale_factor=dpr,service_workers="block",accept_downloads=False,
        permissions=[],color_scheme="dark")
    context.route("**/*",guard_route)
    install_presentation_cleanup(context)
    return context

def discover(url,allowed_host,*,max_probes=9):
    host=urlsplit(validate_public_url(url)).hostname
    if host!=allowed_host:raise ValueError("URL host absent from explicit local test allowlist")
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=HEADLESS,headless=True,
            args=["--no-sandbox","--disable-dev-shm-usage"])
        context=_new_context(browser)
        try:
            if not _robots_allowed(context,url):raise ValueError("robots disallow public discovery")
            page=context.new_page()
            _prepare_browser(page,url)
            options=_candidates(page)
            page.close()
            winners=[]
            for candidate in options[:max_probes]:
                page=context.new_page()
                try:
                    _prepare_browser(page,url)
                    before=screenshot_bgr(page)
                    observed=score_actual_tab(page,candidate["name"],before)
                    if urlsplit(page.url).path!=urlsplit(url).path:
                        raise ValueError("Tab unexpectedly navigated")
                    observed["group"]=candidate["group"]
                    winners.append(observed)
                except Exception:
                    pass
                finally:page.close()
            if not winners:raise ValueError("No reversible, pixel-verified tab actions")
            primary=sorted(winners,key=lambda x:x["score"],reverse=True)
            # Require one original tab family; choose 2-3 meaningful actions.
            chosen_group=primary[0]["group"]
            selected=[x for x in primary if x["group"]==chosen_group][:3]
            if len(selected)<2:raise ValueError("Fewer than two source-verified reversible tab outcomes")
            return {"url":url,"host":host,"candidateCount":len(options),
                "verifiedCount":len(winners),"actions":selected,
                "discoveryPolicy":"visible ARIA tabs only, anonymous public URL, GET/HEAD-only, "
                                  "browser-selected state and native changed result pixels"}
        finally:
            context.close()
            browser.close()

def record(url,plan,out,*,duration=16.):
    if not 10<=duration<=25:raise ValueError("Capture duration outside safe research range")
    out=Path(out)
    if out.exists() and any(out.iterdir()):
        raise ValueError("New capture directory must be empty")
    out.mkdir(parents=True,exist_ok=True,mode=0o700)
    video=out/"source-real-dpr2-60.mp4"
    sidecar=out/"source-events.json"
    (out/"discovery.json").write_text(json.dumps(plan,indent=2)+"\n")
    scheduled=[2.15,6.45,10.8]
    events=[];pointer=[]
    display=DISPLAY
    xvfb_log=(out/"xvfb.log").open("w")
    xvfb=subprocess.Popen(["Xvfb",display,"-screen","0","2880x1800x24",
                           "-nolisten","tcp","-ac"],stdout=xvfb_log,stderr=subprocess.STDOUT)
    time.sleep(.7)
    if xvfb.poll() is not None:raise RuntimeError("Dedicated Xvfb display unavailable")
    prior_display=os.environ.get("DISPLAY")
    os.environ["DISPLAY"]=display
    try:
        with sync_playwright() as pw:
            context=pw.chromium.launch_persistent_context(
                str(out/"temp-browser-profile"),headless=False,executable_path=CHROME,
                args=["--no-sandbox","--disable-dev-shm-usage","--disable-extensions",
                      "--disable-infobars","--window-position=0,0",
                      "--window-size=1440,900","--force-device-scale-factor=2",
                      "--app="+url],
                viewport=dict(width=SIZE[0],height=SIZE[1]),
                device_scale_factor=2,service_workers="block",permissions=[],
                accept_downloads=False,color_scheme="dark")
            context.route("**/*",guard_route)
            install_presentation_cleanup(context)
            page=context.pages[0] if context.pages else context.new_page()
            if page.url!=url:_prepare_browser(page,url)
            page.evaluate("document.fonts.ready")
            page.add_style_tag(content=MOCKUP_SCROLLBAR_STYLE)
            pre_roll=wait_for_real_initial_preview(page)
            (out/"pre-roll-source-evidence.json").write_text(
                json.dumps(pre_roll,indent=2)+"\n")
            geometry=page.evaluate("()=>({dpr:devicePixelRatio,w:innerWidth,h:innerHeight})")
            if geometry!={"dpr":2,"w":1440,"h":900}:
                raise ValueError("Browser source resolution/scale incorrect: "+str(geometry))
            pos=[1100.,790.]
            page.mouse.move(*pos)
            origin=[None]
            def clock():
                return round(max(0.,time.monotonic()-origin[0]),6)
            def log(kind,**data):
                events.append(dict(kind=kind,t=clock(),**data))
            def mouse(x,y):
                page.mouse.move(x,y)
                pos[:]=[x,y]
                if origin[0] is not None:
                    t=clock()
                    if pointer and t<=pointer[-1]["t"]:
                        t=round(pointer[-1]["t"]+.000001,6)
                    pointer.append({"t":t,"x":round(2*x,3),"y":round(2*y,3)})
            def until(t):
                while clock()<t:time.sleep(min(.02,max(.002,t-clock())))
            def trajectory(x,y,seconds):
                x0,y0=pos;n=max(10,round(seconds*55));start=time.monotonic()
                for k in range(1,n+1):
                    u=k/n;s=u*u*u*(u*(u*6-15)+10)
                    mouse(x0+(x-x0)*s,y0+(y-y0)*s)
                    delay=start+seconds*u-time.monotonic()
                    if delay>0:time.sleep(delay)
            def native_box(box):
                return {k:round(v*2,4) for k,v in box.items()}
            command=["ffmpeg","-hide_banner","-loglevel","error","-y",
                     "-f","x11grab","-draw_mouse","0","-video_size","2880x1800",
                     "-framerate","60","-i",display,"-t",str(duration),
                     "-c:v","libx264","-preset","ultrafast","-crf","14",
                     "-pix_fmt","yuv420p","-threads","4","-g","120","-an",
                     "-movflags","+faststart",str(video)]
            with (out/"record.log").open("w") as record_log:
                encoder=subprocess.Popen(command,stdin=subprocess.DEVNULL,stderr=record_log)
                origin[0]=time.monotonic()
                try:
                    mouse(*pos)
                    log("capture_start",source=url)
                    for i,chosen in enumerate(plan["actions"]):
                        name=chosen["name"]
                        button=page.get_by_role("tab",name=name,exact=True)
                        button.wait_for(state="visible",timeout=5000)
                        b=button.bounding_box()
                        if not b:raise ValueError("Genuine selected tab became hidden")
                        t=scheduled[i]
                        until(t-1.25)
                        log("pointer_approach",label=name,targetRect=native_box(chosen["controlRect"]))
                        trajectory(b["x"]+b["width"]*.52,b["y"]+b["height"]*.52,.85)
                        until(t)
                        pre=screenshot_bgr(page)
                        # Explicit real pointer-position sample at the actual
                        # press, even after a natural stationary hover dwell.
                        mouse(*pos)
                        log("pointerdown",label=name,button="left",
                            targetRect=native_box(chosen["controlRect"]))
                        page.mouse.down()
                        page.wait_for_timeout(90)
                        page.mouse.up()
                        log("pointerup",label=name)
                        page.wait_for_timeout(410)
                        state=page.evaluate(PANEL_JS,name)
                        if not state or not state["selected"] or not state["panelVisible"]:
                            raise ValueError("Browser tab failed to select actual state")
                        panel=as_rect(state["result"])
                        if urlsplit(page.url).path!=urlsplit(url).path:
                            raise ValueError("Unexpected page navigation after tab")
                        post=screenshot_bgr(page)
                        x,y,w,h=[round(panel[k]) for k in ("x","y","width","height")]
                        diff=np.max(cv2.absdiff(pre[y:y+h,x:x+w],post[y:y+h,x:x+w]),axis=2)
                        changed=float(np.mean(diff>16))
                        if changed<.035:
                            raise ValueError("Post-click source pixels did not substantiate result")
                        log("verified_result",label=name,
                            resultRect=native_box(panel),
                            evidence="Genuine selected ARIA tab; browser original rendered panel pixels changed",
                            changedFraction=round(changed,5))
                    until(duration-2.2)
                    trajectory(1310,870,.65)
                    until(duration-.6)
                    log("capture_complete",actionsVerified=len(plan["actions"]))
                finally:
                    try:encoder.wait(timeout=65)
                    except subprocess.TimeoutExpired:
                        encoder.terminate()
                        try:encoder.wait(timeout=12)
                        except subprocess.TimeoutExpired:encoder.kill()
            if encoder.returncode:
                raise RuntimeError("Source video FFmpeg failed: "+
                                   (out/"record.log").read_text()[-1500:])
            probe=json.loads(subprocess.check_output(["ffprobe","-v","error",
                "-show_entries","stream=width,height,avg_frame_rate,nb_frames:format=duration",
                "-of","json",str(video)],text=True))
            n=probe["streams"][0]
            if (n["width"],n["height"],n["avg_frame_rate"])!=(2880,1800,"60/1"):
                raise ValueError("Actual encoded source geometry/cadence differs")
            if int(n["nb_frames"])!=round(duration*FPS):
                raise ValueError("Actual source contains incorrect number of 60fps frames")
            manifest={"source":url,"duration":duration,
                      "capture":"Chromium X11 native DPR2 60fps",
                      "fps":FPS,"frameCount":int(n["nb_frames"]),
                      "cursorless":True,"source_sha256":sha(video),
                      "capture_rect":{"width":2880,"height":1800},
                      "events":events,"pointer_samples":pointer,
                      "captureMethod":"Anonymously discovered REAL ARIA tab selections via actual "
                                      "rendered DOM and physical Playwright mouse gestures",
                      "discoverySha256":sha(out/"discovery.json")}
            sidecar.write_text(json.dumps(manifest,indent=2)+"\n")
            context.close()
    finally:
        xvfb.terminate()
        try:xvfb.wait(timeout=6)
        except subprocess.TimeoutExpired:xvfb.kill()
        xvfb_log.close()
        if prior_display is None:os.environ.pop("DISPLAY",None)
        else:os.environ["DISPLAY"]=prior_display
    return {"source":str(video),"receipt":str(sidecar),"sourceSha256":sha(video),
            "verified":len(plan["actions"]),"samples":len(pointer)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--url",required=True)
    p.add_argument("--allowed-host",required=True)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--seconds",type=float,default=16.)
    p.add_argument("--discover-only",action="store_true")
    a=p.parse_args()
    host=urlsplit(validate_public_url(a.url)).hostname
    if host!=a.allowed_host:raise ValueError("Explicit --allowed-host required")
    findings=discover(a.url,a.allowed_host)
    if a.discover_only:
        print(json.dumps(findings,indent=2));return
    result=record(a.url,findings,a.out,duration=a.seconds)
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
