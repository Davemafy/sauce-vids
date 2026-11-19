#!/usr/bin/env python3
"""Capture a real public pricing UI as native DPR2 continuous X11 video.

The fixture is data-only; each browser action is performed and visually
verified by Chromium. No screenshot synthesis, navigation fiction or hidden
form value mutation. No native cursor is drawn in the plate; browser mouse
samples are retained for a single source-timed compositor pointer.
"""
from __future__ import annotations
import argparse, hashlib, json, ipaddress, math, os, subprocess, time
from urllib.parse import urlsplit
from pathlib import Path
from playwright.sync_api import sync_playwright

FPS=60
CSS=(1440,900)
NATIVE=(2880,1800)
DISPLAY=":115"
CHROME=Path("/srv/devmcp-workspaces/5c407ce984e7defcf77da3f1f9cb7f67/sauce-v05-release/studio/.tmp/educational-pilot/browsers/chromium-1254/chrome-linux64/chrome")


def validate_public_url(value:str)->str:
    if not isinstance(value,str) or len(value)>2048:
        raise ValueError("Invalid public product URL")
    try:parsed=urlsplit(value)
    except ValueError as exc:raise ValueError("Invalid public URL") from exc
    host=parsed.hostname
    if parsed.scheme!="https" or not host or not "." in host:
        raise ValueError("Only HTTPS public hostnames are allowed")
    if parsed.username or parsed.password or parsed.fragment:
        raise ValueError("Credential-bearing or fragment URLs are prohibited")
    hostname=host.lower().rstrip(".")
    if (hostname in ("localhost","localhost.localdomain") or
        hostname.endswith((".local",".internal",".test",".localhost"))):
        raise ValueError("Private browser targets not authorized")
    try:
        address=ipaddress.ip_address(hostname)
    except ValueError:
        address=None
    if address is not None and not address.is_global:
        raise ValueError("Non-public IP target prohibited")
    return hostname


def sha256(file):
    digest=hashlib.sha256()
    with open(file,"rb") as handle:
        for data in iter(lambda:handle.read(1048576),b""):digest.update(data)
    return digest.hexdigest()


def capture(config,folder):
    allowed_host=validate_public_url(config["url"])
    folder=Path(folder)
    folder.mkdir(parents=True,exist_ok=True)
    video=folder/"source-real-dpr2-60.mp4"
    receipt=folder/"source-events.json"
    events=[];pointer=[]
    with (folder/"xvfb.log").open("w") as log:
        xvfb=subprocess.Popen(["Xvfb",DISPLAY,"-screen","0","2880x1800x24",
            "-nolisten","tcp","-ac"],stdout=log,stderr=subprocess.STDOUT)
    time.sleep(.7)
    if xvfb.poll() is not None:raise RuntimeError("Dedicated Xvfb screen unavailable")
    old_display=os.environ.get("DISPLAY")
    os.environ["DISPLAY"]=DISPLAY
    try:
        with sync_playwright() as pw:
            ctx=pw.chromium.launch_persistent_context(
                str(folder/"ephemeral-chrome-profile"),headless=False,
                executable_path=str(CHROME),
                args=["--no-sandbox","--disable-dev-shm-usage",
                      "--window-position=0,0","--window-size=1440,900",
                      "--force-device-scale-factor=2",
                      "--app="+config["url"],
                      "--disable-extensions","--disable-infobars"],
                viewport=dict(width=CSS[0],height=CSS[1]),
                device_scale_factor=2,color_scheme="dark",
                reduced_motion="reduce")
            page=ctx.pages[0] if ctx.pages else ctx.new_page()
            if not page.url.startswith(config["url"]):
                page.goto(config["url"],wait_until="domcontentloaded",timeout=40000)
            final_host=validate_public_url(page.url)
            if final_host!=allowed_host:
                raise ValueError("Unapproved product URL redirect")
            page.evaluate("document.fonts.ready")
            selector=config["controlSelector"]
            slider=page.locator(selector).first
            slider.wait_for(state="visible",timeout=25000)
            box=slider.bounding_box()
            if not box or not 500<=box["width"]<=900:raise RuntimeError("Pricing slider changed shape")
            # A genuine baseline state—not a modified DOM snapshot.
            y=box["y"]+box["height"]*.5
            def px_of(frac):return box["x"]+box["width"]*frac
            page.mouse.click(px_of(config["initialFraction"]),y)
            page.wait_for_timeout(350)
            initial=float(page.locator(config["rangeSelector"]).input_value())
            if abs(initial-config["initialValue"])>.007:raise RuntimeError("Unverified initial slider state")
            def price_list():
                return page.locator("body").inner_text()
            assert all(word in price_list() for word in config["initialExpected"])
            browser=page.evaluate("""()=>({
              dpr:devicePixelRatio,width:innerWidth,height:innerHeight,
              outerWidth,outerHeight,screenX,screenY})""")
            if browser["dpr"]!=2 or browser["width"]!=1440 or browser["height"]!=900:
                raise RuntimeError("Native DPR2 source requirements failed "+json.dumps(browser))
            print("GEOMETRY",json.dumps(browser),"CONTROL",json.dumps(box),flush=True)
            start_clock=[None]
            pos=[0.,0.]
            def now():
                return max(0.,time.monotonic()-start_clock[0]) if start_clock[0] else 0.
            def log(kind,**kwargs):
                e=dict(kind=kind,t=round(now(),6),**kwargs)
                events.append(e)
                print("EVENT",json.dumps(e),flush=True)
            def mouse(x,y):
                page.mouse.move(x,y)
                pos[:]=[x,y]
                if start_clock[0]:
                    pointer.append(dict(t=round(now(),6),x=round(2*x,3),y=round(2*y,3)))
            def wait_until(t):
                while now()<t:
                    time.sleep(min(.02,max(.002,t-now())))
            def move(x,y,period):
                sx,sy=pos
                n=max(8,round(period*65))
                start=time.monotonic()
                for k in range(1,n+1):
                    u=k/n
                    eased=u*u*u*(u*(u*6-15)+10)
                    mouse(sx+(x-sx)*eased,sy+(y-sy)*eased)
                    remain=start+period*u-time.monotonic()
                    if remain>0:time.sleep(remain)
            def rect_css(r):
                return {k:round(2*float(r[k]),4)
                        for k in ("x","y","width","height")}
            def price_rect(text):
                locator=page.get_by_text(text,exact=True).first
                if not locator.is_visible():raise RuntimeError("Observed price not visible "+text)
                r=locator.bounding_box()
                if not r or r["width"]<60 or r["height"]<15:
                    raise RuntimeError("Result price has no valid rectangle")
                return rect_css(r)
            # Invisible recorded cursor; the final film draws one verified pointer.
            mouse(1060.,700.)
            command=["ffmpeg","-hide_banner","-loglevel","error","-y",
                "-f","x11grab","-draw_mouse","0","-video_size","2880x1800",
                "-framerate","60","-i",DISPLAY,"-t",str(config["rawSeconds"]),
                "-c:v","libx264","-preset","ultrafast","-crf","16",
                "-pix_fmt","yuv420p","-threads","4","-g","120",
                "-an","-movflags","+faststart",str(video)]
            with (folder/"capture.log").open("w") as caplog:
                encoder=subprocess.Popen(command,stdin=subprocess.DEVNULL,stderr=caplog)
                start_clock[0]=time.monotonic()
                try:
                    log("capture_start",source=config["url"],controlRect=rect_css(box),
                        initialRangeValue=initial,initialPrices=config["initialExpected"])
                    # Physically re-sample the already-positioned real mouse
                    # immediately on the source clock, preventing a cursor
                    # that abruptly materializes halfway into the film.
                    mouse(pos[0],pos[1])
                    for action in config["actions"]:
                        wait_until(float(action["approachStart"]))
                        log("pointer_approach",label=action["label"],
                            targetRect=rect_css(box))
                        move(px_of(action["from"]),y,float(action["approachDuration"]))
                        wait_until(float(action["dragStart"]))
                        page.mouse.down()
                        log("pointerdown",button="left",label=action["label"],
                            targetRect=rect_css(box),
                            pointer=dict(x=round(pos[0]*2,3),y=round(pos[1]*2,3)))
                        move(px_of(action["to"]),y,float(action["dragDuration"]))
                        page.mouse.up()
                        log("pointerup",button="left",label=action["label"])
                        page.wait_for_timeout(135)
                        final=float(page.locator(config["rangeSelector"]).input_value())
                        if abs(final-float(action["expectedValue"]))>.009:
                            raise RuntimeError("Real browser range failed "+action["label"]+": "+str(final))
                        text=price_list()
                        if action["expectedPrice"] not in text:
                            raise RuntimeError("Price outcome not observed "+action["expectedPrice"])
                        rr=price_rect(action["expectedPrice"])
                        log("verified_result",label=action["label"],
                            rangeValue=final,price=action["expectedPrice"],
                            resultRect=rr,evidence="Live browser visible price and range value changed")
                    wait_until(float(config["parkAt"]))
                    move(1180,681,float(config["parkDuration"]))
                    wait_until(float(config["completionAt"]))
                    log("completion",verified=True,finalPrice=config["actions"][-1]["expectedPrice"])
                finally:
                    try:encoder.wait(timeout=38)
                    except subprocess.TimeoutExpired:
                        encoder.terminate()
                        try:encoder.wait(timeout=12)
                        except subprocess.TimeoutExpired:encoder.kill()
            if encoder.returncode!=0:
                raise RuntimeError("Source recorder failed: "+(folder/"capture.log").read_text()[-1800:])
            result=json.loads(subprocess.check_output(["ffprobe","-v","error",
                "-show_entries","stream=width,height,r_frame_rate,nb_frames:format=duration",
                "-of","json",str(video)],text=True))
            print("CAPTURE",json.dumps(result),flush=True)
            meta=dict(source=config["url"],capture="Chromium X11 native DPR2 60fps",
                fps=60,source_sha256=sha256(video),source_dimensions=dict(width=2880,height=1800),
                capture_rect=dict(width=2880,height=1800),
                viewport=dict(width=1440,height=900,dpr=2),
                recordingOrigin="ffmpeg process start monotonic after subprocess.Popen",
                timingAccuracy="requires visual state-change frame calibration before frame-locked Foley",
                frameCount=int(result["streams"][0]["nb_frames"]),
                events=events,pointer_samples=pointer,cursorless=True,
                slider=dict(controlRect=rect_css(box),initialValue=initial),
                configName=config.get("name","verified slider"))
            receipt.write_text(json.dumps(meta,indent=2)+"\n")
            print("RECEIPT",receipt,meta["source_sha256"],flush=True)
            ctx.close()
    finally:
        xvfb.terminate()
        try:xvfb.wait(timeout=4)
        except subprocess.TimeoutExpired:xvfb.kill()
        if old_display is None:os.environ.pop("DISPLAY",None)
        else:os.environ["DISPLAY"]=old_display


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--fixture",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    capture(json.loads(args.fixture.read_text()),args.out)
