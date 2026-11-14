#!/usr/bin/env python3
"""Record Linear's real official interactive preview, pointer and DOM events.

We record an official public *interactive preview*, NOT a real customer account.
The capture and sidecar share monotonic time. Uses a full Linux browser,
X11 mouse pointer, and ffmpeg x11grab at 60fps.
"""
from __future__ import annotations
import os,json,math,time,subprocess
from pathlib import Path
from Xlib import display as xdisplay
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]/"studio"/".tmp"/"sauce-autozoom-v1"
ROOT.mkdir(parents=True,exist_ok=True)
SOURCE_URL="https://linear.app/"
FPS=60
LENGTH=14.0
os.environ["DISPLAY"]=":91"
RAW=ROOT/"linear-official-preview-real-60.mp4"
MANIFEST=ROOT/"linear-interactions.json"

class Interactor:
    def __init__(self,page):
        self.page=page
        self.display=xdisplay.Display(":91")
        self.pos=(435.0,258.0)
        self.epoch=None
        self.pointer=[]
        self.actions=[]
    def now(self):
        return time.monotonic()-self.epoch if self.epoch else 0.0
    def log(self,kind,**kwargs):
        item={"t":round(self.now(),4),"kind":kind,**kwargs}
        self.actions.append(item)
        print("ACTION",json.dumps(item),flush=True)
        return item
    def warp(self,x,y,mark=True):
        self.display.screen().root.warp_pointer(int(round(x)),int(round(y)))
        self.display.sync()
        self.page.mouse.move(float(x),float(y))
        self.pos=(float(x),float(y))
        if mark:
            self.pointer.append({"t":round(self.now(),4),
                "x":round(x-53,3),"y":round(y-90,3),"source":"X11+Playwright"})
    def move(self,x,y,seconds=.7):
        x0,y0=self.pos
        steps=max(12,int(seconds*85))
        start=time.monotonic()
        for i in range(1,steps+1):
            u=i/steps
            e=u*u*u*(u*(u*6-15)+10)
            self.warp(x0+(x-x0)*e,y0+(y-y0)*e)
            time.sleep(max(0,start+seconds*u-time.monotonic()))
    def until(self,t):
        while self.now()<t:time.sleep(min(.02,max(.001,t-self.now())))
    @staticmethod
    def rect(box):
        return {k:round(float(box[k]),3) for k in ("x","y","width","height")}
    def local_rect(self,box):
        return {**self.rect(box),"x":round(box["x"]-53,3),"y":round(box["y"]-90,3)}
    def to(self,locator,seconds=.6):
        box=locator.bounding_box(timeout=6000)
        if not box:raise RuntimeError("No element box")
        self.move(box["x"]+box["width"]*.52,box["y"]+box["height"]*.54,seconds)
        return box

def result_bbox(page):
    """Derive the changed content region from the actual Linear DOM."""
    # A real code file header exists in Linear's public interactive preview.
    code=page.get_by_text("HomeScreen.tsx",exact=False).first
    if code.count():
        # Traverse upward to a substantial readable code region; avoid hard-coded coordinates.
        return code.evaluate("""el=>{
            let p=el,best=null;
            const host=document.querySelector('.WS84WW_frame').getBoundingClientRect();
            for(let i=0;i<9&&p;i++,p=p.parentElement){
              const r=p.getBoundingClientRect();
              if(r.width>450&&r.width<host.width*.84&&r.height>340&&r.height<host.height*.94)
                best={x:r.x,y:r.y,width:r.width,height:r.height};
            }
            return best;
        }""")
    return None

with sync_playwright() as pw:
    browser=pw.chromium.launch_persistent_context(
        str(ROOT/f"chrome-profile-{int(time.time()*1000)}"),
        headless=False,
        args=["--no-sandbox","--disable-dev-shm-usage",
              "--window-position=0,0","--window-size=1440,900",
              f"--app={SOURCE_URL}","--disable-infobars",
              "--disable-features=Translate"],
        viewport={"width":1440,"height":900},
        device_scale_factor=1,reduced_motion="reduce",color_scheme="dark")
    page=browser.pages[0] if browser.pages else browser.new_page()
    if "linear.app" not in page.url:
        page.goto(SOURCE_URL,wait_until="domcontentloaded",timeout=30000)
    page.wait_for_timeout(1300)
    page.evaluate("""() => {
      const f=document.querySelector('.WS84WW_frame');
      if(!f)throw new Error("Linear's official preview not found");
      window.scrollTo({top:f.getBoundingClientRect().top+window.scrollY-90,behavior:'instant'});
    }""")
    page.wait_for_timeout(620)
    app=page.locator(".WS84WW_frame")
    frame_rect=app.bounding_box()
    print("REAL_PREVIEW",frame_rect,"URL",page.url,flush=True)
    if not frame_rect or any(abs(frame_rect[k]-v)>3 for k,v in
       {"x":53,"y":90,"width":1320,"height":720}.items()):
        raise RuntimeError("Recording region shifted; cancel rather than crop bad footage")
    assert page.get_by_role("button",name="Reviews",exact=True).count()==1
    click_target=page.get_by_role("button",name="Reviews",exact=True)
    film=Interactor(page)
    film.warp(*film.pos,mark=False)
    args=[
        "ffmpeg","-hide_banner","-loglevel","error","-y",
        "-f","x11grab","-draw_mouse","1","-video_size","1320x720",
        "-framerate",str(FPS),"-i",":91+53,90",
        "-t",str(LENGTH),"-c:v","libx264","-pix_fmt","yuv420p",
        "-profile:v","high","-preset","ultrafast","-crf","17",
        "-threads","5","-g","120","-an","-movflags","+faststart",str(RAW)
    ]
    log=ROOT/"record.log"
    with log.open("w") as f:
        ff=subprocess.Popen(args,stdin=subprocess.DEVNULL,stderr=f)
        time.sleep(.28)
        film.epoch=time.monotonic()
        try:
            film.log("session_start",scene="linear_official_interactive_preview",
                     viewport={"width":1320,"height":720},
                     framing="browser-source-crop",clicks_expected=1)
            film.until(2.35)
            rect=film.to(click_target,seconds=.83)
            film.log("cursor_dwell",target="Reviews",targetRect=film.local_rect(rect))
            film.until(3.55)
            style=click_target.evaluate("(e)=>getComputedStyle(e).cursor")
            film.page.mouse.down()
            film.log("pointer_down",button="left",cursorStyle=style,
                     target="Reviews",targetRect=film.local_rect(rect),
                     cursor={"x":round(film.pos[0]-53,2),"y":round(film.pos[1]-90,2)})
            time.sleep(.095)
            film.page.mouse.up()
            film.log("click",button="left",role="button",label="Reviews",
                     targetRect=film.local_rect(rect),
                     cursor={"x":round(film.pos[0]-53,2),"y":round(film.pos[1]-90,2)},
                     semanticGoal="open code review")
            page.get_by_role("button",name="Diff",exact=True).wait_for(timeout=4500)
            page.wait_for_timeout(300)
            computed=result_bbox(page)
            if computed is None:
                # Fall back to real pane tab and its parent bounding box.
                tab=page.get_by_role("button",name="Diff",exact=True)
                tb=tab.bounding_box()
                computed={"x":tb["x"]-38,"y":tb["y"]-12,"width":620,"height":500}
            focus=film.local_rect(computed)
            film.log("state_change",fromState="Issue detail",toState="Reviews",
                     evidence="Diff tab and review list visible",resultRect=focus,
                     semanticGoal="inspect code changes")
            # The pointer approaches the actual code without another click.
            target=page.get_by_text("HomeScreen.tsx",exact=False).first
            if target.count():
                film.to(target,seconds=1.08)
                film.log("cursor_dwell",target="Code diff file",cursor={
                    "x":round(film.pos[0]-53,2),"y":round(film.pos[1]-90,2)})
            film.until(10.65)
            film.log("interaction_complete",label="Review code inspected")
            film.until(LENGTH-.25)
        finally:
            try:ff.wait(timeout=25)
            except subprocess.TimeoutExpired:
                ff.terminate()
                try:ff.wait(timeout=12)
                except:ff.kill()
            page.screenshot(path=str(ROOT/"browser-final.png"),animations="disabled")
            manifest={
                "source":SOURCE_URL,
                "source_kind":"official interactive marketing preview; not a signed-in Linear account",
                "source_capture":"ffmpeg X11 continuous 60fps original OS cursor",
                "fps":FPS,"duration":LENGTH,
                "capture_rect":{"x":53,"y":90,"width":1320,"height":720},
                "events":film.actions,"pointer_samples":film.pointer,
                "raw_video":str(RAW),
                "provenance":"Live interactions on official Linear website",
                "review_target_verified":bool(page.get_by_role("button",name="Diff",exact=True).count()),
                "frame_at_end":app.bounding_box(),
            }
            try:
                manifest["probe"]=json.loads(subprocess.check_output([
                    "ffprobe","-v","error","-show_entries",
                    "stream=width,height,avg_frame_rate,nb_frames:format=duration,size",
                    "-of","json",str(RAW)],text=True,timeout=10))
            except Exception as e:manifest["probe_error"]=str(e)
            MANIFEST.write_text(json.dumps(manifest,indent=2))
            print("RECEIPT",json.dumps({"events":len(film.actions),"pointer_samples":len(film.pointer),
                  "result":manifest.get("probe"),"review":manifest["review_target_verified"]}),flush=True)
            browser.close()
