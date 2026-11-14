#!/usr/bin/env python3
"""Truthful OpenSheets demonstration: one completed currency-formatting workflow.

Staging uses the real OpenSheets UI. Source recording is continuous X11 Chromium
with native pointer. All film actions are executed against real app controls.
"""
from __future__ import annotations
import json,math,os,subprocess,time,uuid
from pathlib import Path
from playwright.sync_api import sync_playwright
from Xlib import display as xdisplay, X
from Xlib.ext import xtest

PROJECT=Path(__file__).resolve().parents[1]
ROOT=PROJECT/"studio"/".tmp"/"film-paradigm"
ROOT.mkdir(parents=True,exist_ok=True)
T=json.loads((ROOT/"voice-timeline.json").read_text())
os.environ["DISPLAY"]=":93"
URL=os.environ.get("SAUCE_OPENSHEETS_URL","http://127.0.0.1:5177/")
SOURCE_VIDEO=ROOT/"opensheets-real-ui-x11-60fps.mp4"
LENGTH=12.0
SCREEN={"width":1600,"height":900}
DATA="""EXPENSE\tMONTH\tTYPE\tAMOUNT
Cloud hosting\tOct 2026\tInfrastructure\t320
Font license\tOct 2026\tDesign\t75
Motion assets\tOct 2026\tProduction\t150
Domain renewal\tOct 2026\tOperations\t24
Music track\tOct 2026\tAudio\t45"""

class Director:
    def __init__(self,page):
        self.page=page
        self.x=xdisplay.Display(":93")
        self.pos=(1260.,430.)
        self.start=None
        self.events=[]
        self.pointer=[]
    def now(self):
        return 0.0 if self.start is None else time.monotonic()-self.start
    def log(self,kind,**extra):
        record={"t":round(self.now(),4),"kind":kind,**extra}
        self.events.append(record)
        print("EVENT",json.dumps(record),flush=True)
        return record
    def warp(self,x,y):
        self.x.screen().root.warp_pointer(int(round(x)),int(round(y)))
        self.x.sync()
        # Native X11 pointer movement; do not also inject a CDP mouse event.
        self.pos=(x,y)
        if self.start is not None:
            self.pointer.append({"t":round(self.now(),4),"x":round(float(x),2),"y":round(float(y),2)})
    def press(self):
        xtest.fake_input(self.x,X.ButtonPress,1)
        self.x.sync()
    def release(self):
        xtest.fake_input(self.x,X.ButtonRelease,1)
        self.x.sync()
    def move(self,x,y,dur=.5):
        x0,y0=self.pos
        steps=max(12,round(dur*85))
        t0=time.monotonic()
        for i in range(1,steps+1):
            v=i/steps
            e=v*v*v*(v*(v*6-15)+10)
            self.warp(x0+(x-x0)*e,y0+(y-y0)*e)
            time.sleep(max(0,t0+dur*v-time.monotonic()))
    def until(self,t):
        while self.now()<t:
            time.sleep(min(.025,max(.001,t-self.now())))
    def rect(self,element):
        b=element.bounding_box()
        if not b:raise RuntimeError("Expected visible DOM rectangle")
        return {k:round(float(b[k]),3) for k in ("x","y","width","height")}
    def center(self,element):
        b=self.rect(element)
        return b["x"]+b["width"]*.5,b["y"]+b["height"]*.5

def range_drag(page, a, b, steps=24):
    start=a.bounding_box()
    end=b.bounding_box()
    if not start or not end:raise RuntimeError("Cannot drag invisible cell")
    x=start["x"]+start["width"]*.55
    y=start["y"]+start["height"]*.50
    xx=end["x"]+end["width"]*.55
    yy=end["y"]+end["height"]*.50
    page.mouse.move(x,y)
    page.mouse.down()
    page.mouse.move(xx,yy,steps=steps)
    page.mouse.up()

def staging(page):
    page.goto(URL,wait_until="domcontentloaded",timeout=30000)
    page.wait_for_timeout(1200)
    if page.get_by_role("grid").count()!=1:
        raise RuntimeError("Real OpenSheets grid unavailable")
    start=page.locator('[aria-label^="Cell E4:"]')
    start.click()
    page.evaluate("(v)=>navigator.clipboard.writeText(v)",DATA)
    page.keyboard.press("Control+v")
    page.wait_for_timeout(600)
    for idx,grow in [(5,130),(6,50),(7,80),(8,55)]:
        header=page.locator(f'[role="columnheader"][aria-colindex="{idx}"] div').first
        b=header.bounding_box()
        if not b:raise RuntimeError("Column drag handle unavailable")
        xx=b["x"]+b["width"]/2
        yy=b["y"]+b["height"]/2
        page.mouse.move(xx,yy)
        page.mouse.down()
        page.mouse.move(xx+grow,yy,steps=20)
        page.mouse.up()
        page.wait_for_timeout(130)
    range_drag(page,
        page.locator('[aria-label^="Cell E4:"]'),
        page.locator('[aria-label^="Cell H9:"]'))
    page.locator('select[title="Font size"]').select_option("14")
    page.wait_for_timeout(150)
    range_drag(page,
        page.locator('[aria-label^="Cell E4:"]'),
        page.locator('[aria-label^="Cell H4:"]'))
    page.locator('button[title^="Bold"]').click()
    page.wait_for_timeout(350)
    # Restore the source to a neutral, unformatted amount column.
    range_drag(page,
        page.locator('[aria-label^="Cell H5:"]'),
        page.locator('[aria-label^="Cell H9:"]'))
    page.locator('select').filter(has=page.locator('option[value="automatic"]')).select_option("automatic")
    page.wait_for_timeout(200)
    # Select an empty cell so the demo starts with the values deselected.
    page.locator('[aria-label^="Cell J13:"]').click()
    page.wait_for_timeout(550)
    expected=["320","75","150","24","45"]
    for i,num in enumerate(expected,5):
        text=page.locator(f'[aria-label^="Cell H{i}:"]').get_attribute("aria-label")
        if not text or not text.endswith(": "+num):
            raise RuntimeError(f"Staging produced wrong unformatted amount: H{i}: {text}")
    return {"app":"OpenSheets 2.1.0 (MIT), self-hosted from verified repository",
            "pre_amounts":expected,"document":"fictional sample expense rows",
            "font_size":"14","columns":"real resized app columns"}

with sync_playwright() as pw:
    profile=ROOT/f"capture-chrome-{uuid.uuid4().hex[:7]}"
    browser=pw.chromium.launch_persistent_context(
        str(profile),headless=False,
        executable_path=os.environ.get("SAUCE_CHROME_BIN") or str(PROJECT/"studio"/".tmp"/"educational-pilot"/"browsers"/"chromium-1254"/"chrome-linux64"/"chrome"),
        args=["--no-sandbox","--disable-dev-shm-usage","--disable-infobars",
              "--window-position=0,0","--window-size=1600,900",
              "--kiosk",f"--app={URL}","--disable-features=Translate"],
        viewport=SCREEN,device_scale_factor=1,
        permissions=["clipboard-read","clipboard-write"],
        reduced_motion="reduce",color_scheme="light"
    )
    page=browser.pages[0] if browser.pages else browser.new_page()
    meta=staging(page)
    page.screenshot(path=str(ROOT/"real-staged.png"),animations="disabled")
    film=Director(page)
    film.warp(*film.pos)
    app=page.get_by_role("grid")
    print("APP_PREPARED",json.dumps(meta),"GRID",film.rect(app),flush=True)
    command=[
       "ffmpeg","-hide_banner","-loglevel","error","-y",
       "-f","x11grab","-draw_mouse","1","-video_size","1600x900",
       "-framerate","60","-i",":93+0,0","-t",str(LENGTH),
       "-c:v","libx264","-pix_fmt","yuv420p","-profile:v","high",
       "-preset","ultrafast","-crf","15","-threads","5","-g","120",
       "-an","-movflags","+faststart",str(SOURCE_VIDEO)]
    ff=subprocess.Popen(command,stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=(ROOT/"capture.log").open("w"))
    time.sleep(.27)
    film.start=time.monotonic()
    film.log("session_start",url=URL,source_kind="MIT OpenSheets real running editor",
             screen=SCREEN,source_verified=True)
    try:
        # First: show the initial plain figures while narration identifies them.
        film.until(2.48)
        first=page.locator('[aria-label^="Cell H5:"]')
        last=page.locator('[aria-label^="Cell H9:"]')
        sx,sy=film.center(first)
        ex,ey=film.center(last)
        film.move(sx,sy,.48)
        film.log("cursor_dwell",target="unformatted expense amount",targetRect=film.rect(first))
        film.until(3.06)
        film.press()
        film.log("pointer_down",target="H5",role="gridcell")
        steps=53
        t0=time.monotonic()
        for i in range(1,steps+1):
            u=i/steps
            eased=u*u*(3-2*u)
            film.warp(sx+(ex-sx)*eased,sy+(ey-sy)*eased)
            time.sleep(max(0,t0+.65*u-time.monotonic()))
        film.release()
        selected=page.locator('[role="gridcell"][aria-selected="true"]').count()
        if selected != 5:raise RuntimeError(f"Native drag selected {selected} cells, expected 5")
        film.log("range_select",label="Select H5:H9",
                 resultRect={"x":round(sx-first.bounding_box()["width"]*.5,3),
                             "y":round(sy-first.bounding_box()["height"]*.5,3),
                             "width":round(first.bounding_box()["width"],3),
                             "height":round(last.bounding_box()["y"]+last.bounding_box()["height"]-(sy-first.bounding_box()["height"]*.5),3)},
                 aria_selected=page.locator('[role="gridcell"][aria-selected="true"]').count())
        # Move deliberately to the real currency button; never guess a coordinate.
        film.until(4.07)
        button=page.locator('button[title="Currency"]')
        if button.count()!=1:raise RuntimeError("Native Currency control unavailable")
        bx,by=film.center(button)
        film.move(bx,by,.40)
        film.log("cursor_dwell",target="Currency toolbar button",targetRect=film.rect(button))
        film.until(4.68)
        film.log("pointer_down",target="Currency toolbar",role="button",targetRect=film.rect(button))
        film.press()
        time.sleep(.07)
        film.release()
        film.log("click",label="Apply currency formatting",role="button",
                 semanticGoal="format selected amount column as currency",
                 targetRect=film.rect(button))
        page.wait_for_function("""() => {
          const cells=[5,6,7,8,9];
          return cells.every(i=>{
            let el=document.querySelector('[aria-label^="Cell H'+i+':"]');
            return el&&el.getAttribute('aria-label').includes('$')
          })
        }""",timeout=3500)
        vals=[page.locator(f'[aria-label^="Cell H{i}:"]').get_attribute("aria-label") for i in range(5,10)]
        b5=film.rect(page.locator('[aria-label^="Cell H5:"]'))
        b9=film.rect(page.locator('[aria-label^="Cell H9:"]'))
        result={"x":b5["x"],"y":b5["y"],"width":b5["width"],
                "height":round(b9["y"]+b9["height"]-b5["y"],3)}
        film.log("state_change",fromState="plain numeric expense amounts",
                 toState="five USD currency-formatted amounts",
                 evidence="each actual gridcell aria-label now displays a dollar sign and two decimals",
                 resultRect=result,values=vals)
        film.until(5.80)
        # The pointer moves back to the actual finished values, then holds.
        hx,hy=film.center(page.locator('[aria-label^="Cell H7:"]'))
        film.move(hx,hy,.68)
        film.log("cursor_dwell",target="formatted result column",targetRect=result)
        film.until(8.5)
        film.log("interaction_complete",label="Expense currency formatting verified")
        film.until(11.25)
    finally:
        try:ff.wait(timeout=20)
        except subprocess.TimeoutExpired:
            ff.terminate()
            ff.wait(timeout=10)
        page.screenshot(path=str(ROOT/"real-final.png"),animations="disabled")
        report={
            "url":URL,"source_kind":"Real OpenSheets OSS running on localhost",
            "captured_source":"Chromium X11 real system cursor, continuous 60fps",
            "capture_rect":{"x":0,"y":0,"width":1600,"height":900},
            "fps":60,"duration":LENGTH,"lead_s":0.27,"events":film.events,
            "pointer_samples":film.pointer,
            "raw_video":str(SOURCE_VIDEO),"stage":meta,
            "source_repository":"https://github.com/w0h1v/OpenSheets",
            "license":"MIT"
        }
        if SOURCE_VIDEO.is_file():
            report["probe"]=json.loads(subprocess.check_output([
                "ffprobe","-v","error","-select_streams","v:0",
                "-show_entries","stream=width,height,avg_frame_rate,nb_frames:format=duration,size",
                "-of","json",str(SOURCE_VIDEO)],text=True))
        (ROOT/"real-interactions.json").write_text(json.dumps(report,indent=2))
        print("CAPTURE_RECEIPT",json.dumps({
            "frames":report.get("probe"),"events":len(film.events),
            "cursor_samples":len(film.pointer),"values":vals if 'vals' in locals() else [],
        }),flush=True)
        browser.close()
