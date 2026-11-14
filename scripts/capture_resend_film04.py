#!/usr/bin/env python3
"""Authentic one-take browser/OS pointer capture of Resend's live pricing controls."""
import json, os, subprocess, time, signal, math
from pathlib import Path
from Xlib import display as xdisplay
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]/"studio"/".tmp"/"film-04"
ROOT.mkdir(parents=True,exist_ok=True)
DISPLAY=":96"
W,H,FPS,LENGTH=1440,900,60,16.0
CHROME=Path(os.environ.get("SAUCE_CHROME_BIN") or (Path(__file__).resolve().parents[1]/"studio"/".tmp"/"educational-pilot"/"browsers"/"chromium-1254"/"chrome-linux64"/"chrome"))
REC=ROOT/"resend-cursorless-60.mp4"
SIDECAR=ROOT/"cursor-events.json"
xvfb=subprocess.Popen(["Xvfb",DISPLAY,"-screen","0",f"{W}x{H}x24","-nolisten","tcp","-ac"],stdout=(ROOT/"xvfb.log").open("w"),stderr=subprocess.STDOUT)
time.sleep(.7)
if xvfb.poll() is not None: raise RuntimeError("Xvfb display not available")
os.environ["DISPLAY"]=DISPLAY
events=[];path=[];t0=None
def now():return 0 if t0 is None else round(time.perf_counter()-t0,4)
try:
 with sync_playwright() as pw:
  ctx=pw.chromium.launch_persistent_context(
   str(ROOT/("profile-"+str(int(time.time()*1000)))),headless=False,
   executable_path=str(CHROME),
   args=["--no-sandbox","--disable-dev-shm-usage","--window-position=0,0","--window-size=1440,900",
         "--app=https://resend.com/pricing","--disable-infobars","--disable-features=Translate"],
   viewport={"width":1440,"height":900},device_scale_factor=1,
   reduced_motion="reduce",color_scheme="dark")
  page=ctx.pages[0] if ctx.pages else ctx.new_page()
  if "resend.com/pricing" not in page.url:page.goto("https://resend.com/pricing",wait_until="domcontentloaded",timeout=45000)
  page.wait_for_timeout(1500)
  control=page.locator('[data-base-ui-slider-control]')
  control.wait_for(state="visible",timeout=20000)
  box=control.bounding_box()
  if not box or abs(box["width"]-672)>150:raise RuntimeError("Pricing slider layout unexpected")
  print("SLIDER",box,"WINDOW",page.evaluate("() => [screenX,screenY,outerWidth,outerHeight,innerWidth,innerHeight]"),flush=True)
  # Use native desktop X pointer plus real Chromium pointer dispatch.
  xdisp=xdisplay.Display(DISPLAY)
  root=xdisp.screen().root
  screen=page.evaluate("() => ({x:screenX,y:screenY,outerW:outerWidth,outerH:outerHeight,innerW:innerWidth,innerH:innerHeight})")
  offx=float(screen["x"])
  offy=float(screen["y"]+max(0,screen["outerH"]-screen["innerH"]))
  # Bounds guard: if X11 WM positions are not reliable use the page window origin.
  offx=min(80,max(0,offx));offy=min(70,max(0,offy))
  print("MOUSE_OFFSET",offx,offy,flush=True)
  pos=[970.,680.]
  def warp(x,y):
   root.warp_pointer(int(max(1,min(W-2,x+offx))),int(max(1,min(H-2,y+offy))))
   xdisp.sync()
   page.mouse.move(float(x),float(y))
   pos[:]=[x,y]
   path.append({"t":now(),"x":round(x,2),"y":round(y,2)})
  def move(x,y,dur):
   sx,sy=pos
   n=max(4,round(dur*60))
   begin=time.perf_counter()
   for i in range(1,n+1):
    u=i/n
    ease=u*u*(3-2*u)
    warp(sx+(x-sx)*ease,sy+(y-sy)*ease)
    time.sleep(max(0,begin+dur*u-time.perf_counter()))
  def until(t):
   while now()<t:time.sleep(min(.025,max(.005,t-now())))
  def event(kind,**k):
   e={"t":now(),"kind":kind,**k};events.append(e);print("EVENT",json.dumps(e),flush=True)
  def expected(value,amount):
   inp=page.locator('input[type=range]')
   page.wait_for_timeout(170)
   curr=float(inp.input_value())
   text=page.locator('body').inner_text()
   if abs(curr-value)>.01 or ("$"+amount+" / mo") not in text:
    raise RuntimeError(f"Price interaction invalid: expected {value} and {amount}, got {curr}; "+text[200:430])
  warp(970,690)
  ff_cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-f","x11grab","-draw_mouse","0",
          "-video_size",f"{W}x{H}","-framerate",str(FPS),"-i",DISPLAY,
          "-t",str(LENGTH),"-c:v","libx264","-preset","veryfast","-crf","17",
          "-pix_fmt","yuv420p","-threads","6","-g","120","-movflags","+faststart",str(REC)]
  with (ROOT/"capture.log").open("w") as caplog:
   ff=subprocess.Popen(ff_cmd,stdin=subprocess.DEVNULL,stderr=caplog)
   time.sleep(.3);t0=time.perf_counter()
   try:
    event("capture_start",url=page.url,visible_slider_box=box)
    # Overview: full page context, then the real slider control.
    until(2.15)
    move(470,box["y"]+10,1.25)
    until(4.42)
    page.mouse.down();time.sleep(.075);page.mouse.up()
    expected(.125,"20")
    event("click",label="50,000 emails",value=.125,targetRect={"x":box["x"],"y":box["y"],"width":box["width"],"height":box["height"]},
          plan="Pro",price="$20 / mo",semanticGoal="view real Pro pricing")
    until(7.28)
    move(552,box["y"]+10,.85)
    until(8.47)
    page.mouse.down();time.sleep(.075);page.mouse.up()
    # Browser range selection is snapped to nearest 1/8th.
    value=float(page.locator("input[type=range]").input_value())
    text=page.locator("body").inner_text()
    amount="35" if "$35 / mo" in text else "unknown"
    if value<.24 or amount!="35":raise RuntimeError(f"Final price change not verified: value={value} price={amount}")
    event("state_change",label="100,000 emails",value=value,plan="Pro",price="$35 / mo",
          evidence="Price text updated in actual Resend application",
          targetRect={"x":box["x"],"y":box["y"],"width":box["width"],"height":box["height"]},
          semanticGoal="see pricing change")
    until(10.5)
    move(830,590,1.1)
    until(15.3)
    event("completion",verified=True)
   finally:
    try:ff.wait(timeout=30)
    except subprocess.TimeoutExpired:
     ff.terminate();ff.wait(timeout=10)
  print("VIDEO",REC,REC.stat().st_size,flush=True)
  page.screenshot(path=str(ROOT/"capture-final.png"))
  receipt={"source":"https://resend.com/pricing","mode":"live browser+native X11 cursor",
           "duration":LENGTH,"fps":FPS,"resolution":[W,H],
           "events":events,"pointer_samples":path,"offset":[offx,offy],
           "video":str(REC)}
  SIDECAR.write_text(json.dumps(receipt,indent=2))
  ctx.close()
finally:
 xvfb.terminate()
 try:xvfb.wait(timeout=5)
 except: xvfb.kill()
