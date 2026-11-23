"""Capture ONE Stagehand-selected, independently verified public UI action at native 60fps.

Private experiment only. Browser interaction is performed by Sauce's trusted
Playwright selector from its own inspection, never a Stagehand-generated selector.
X11 captures genuine Chromium output, no synthetic product frames or fake pointer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))

from playwright.sync_api import sync_playwright

from backend.product_explorer import allowed, CHROME
from backend.stagehand_discovery import choose_observed_action, SCHEMA
from backend.source_action_preflight import probe_public_action
from scripts.capture_safety import validate_public_url, guard_route
from scripts.session_capture import MOCKUP_SCROLLBAR_STYLE, install_presentation_cleanup

FPS = 60
CSS = (1440, 900)
NATIVE = (2880, 1800)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_pair(url):
    host = (urlsplit(url).hostname or "").lower()
    base = host.removeprefix("www.")
    return {base, "www." + base}


def exact_first_party(original, target):
    a, b = urlsplit(original), urlsplit(target)
    return (a.scheme == "https" and b.scheme == "https"
            and a.port in (None, 443) and b.port in (None, 443)
            and b.hostname in canonical_pair(original))


def verify_selection(report, observation, url):
    """No self-reported model outcome/selector has authority."""
    validate_public_url(url)
    if not isinstance(report, dict) or report.get("source_url") != url:
        raise ValueError("Source inspection URL mismatch")
    if not exact_first_party(url, report.get("url", "")):
        raise ValueError("Inspection left authorized public product")
    if not isinstance(observation, dict) or observation.get("schema") != SCHEMA:
        raise ValueError("No actual Stagehand observation receipt")
    if observation.get("actions_executed") != 0:
        raise ValueError("Scout must have performed zero browser actions")
    plan = choose_observed_action(report, observation)
    if not plan or plan.get("mode") != "interactive" or len(plan["action_ids"]) != 1:
        raise ValueError("No unique, safe, independently observed local product control")
    cid = plan["action_ids"][0]
    controls = [x for x in report["controls"] if x.get("id") == cid]
    if len(controls) != 1 or not allowed(controls[0], report["url"]):
        raise ValueError("No permitted observed control")
    return cid, controls[0]


def _real_result(page, control, before_state, after_state):
    """Measure real post-click UI, never infer result coordinates from a model."""
    if before_state == after_state:
        raise ValueError("Original product DOM did not visibly change")
    dialog = page.locator('[role="dialog"]:visible,dialog[open]:visible')
    panels = []
    for i in range(min(5, dialog.count())):
        rect = dialog.nth(i).bounding_box()
        if rect:
            panels.append(rect)
    if panels:
        measured = max(panels, key=lambda x:x["width"]*x["height"])
    else:
        # When the verified action genuinely changes a theme/preview without
        # a bounded panel, only a FULL genuine source frame can be admitted.
        before_theme = (before_state.get("theme"), before_state.get("body"))
        after_theme = (after_state.get("theme"), after_state.get("body"))
        if before_theme == after_theme:
            raise ValueError("No verified bounded result DOM or global theme state")
        measured = {"x":0,"y":0,"width":CSS[0],"height":CSS[1]}
    x,y,width,height=(float(measured[k]) for k in ("x","y","width","height"))
    if (not math.isfinite(x+y+width+height) or
        width<30 or height<20 or x<0 or y<0 or
        x+width>CSS[0] or y+height>CSS[1]):
        raise ValueError("Product result lies outside original visible viewport")
    return {k: round(2*float(measured[k]),4)
            for k in ("x","y","width","height")}


def capture(url, inspection, observations, folder, *, display=":174", seconds=10.0):
    if not 9.5<=seconds<=16 or not display.startswith(":") or not display[1:].isdigit():
        raise ValueError("Bounded private 9.5-16s / numeric Xvfb display required")
    if not 160<=int(display[1:])<=220:
        raise ValueError("Private Xvfb display must be in 160..220")
    folder = Path(folder)
    if folder.exists() and any(folder.iterdir()):
        raise ValueError("Do not overwrite original capture")
    report = json.loads(Path(inspection).read_text())
    observation = json.loads(Path(observations).read_text())
    control_id, control = verify_selection(report,observation,url)
    # Fresh independent Browser+pixel probe before any movie work.
    probe = probe_public_action(url,report,control_id,folder.parent/"independent-live-probe")
    if probe.get("decision") != "visible_outcome_candidate":
        raise ValueError("Source-independent UI action probe rejected capture")
    folder.mkdir(parents=True,exist_ok=False,mode=0o700)
    (folder/"preflight-summary.json").write_text(json.dumps({
        "decision":probe["decision"],"sourceControlId":control_id,
        "creativeApproved":False},indent=2))
    output = folder/"source-native-dpr2-60.mp4"
    argv = ["Xvfb",display,"-screen","0","2880x1800x24",
            "-nolisten","tcp","-ac"]
    with (folder/"xvfb.log").open("w") as xvlog:
        xvfb = subprocess.Popen(argv,stdout=xvlog,stderr=subprocess.STDOUT)
        time.sleep(.6)
        if xvfb.poll() is not None:raise RuntimeError("Dedicated Xvfb unavailable")
        saved_display=os.environ.get("DISPLAY")
        os.environ["DISPLAY"]=display
        events=[];samples=[];clock=[None];lastpos=[1190.,720.]
        try:
            with tempfile.TemporaryDirectory(prefix="sauce-stagehand-native-profile-") as profile:
                with sync_playwright() as pw:
                    chrome=os.getenv("SAUCE_NATIVE_CHROME") or "/opt/continuity-remote/chromium/chrome"
                    context=pw.chromium.launch_persistent_context(
                        profile,headless=False,executable_path=chrome,
                        args=["--no-sandbox","--disable-dev-shm-usage",
                              "--window-position=0,0","--window-size=1440,900",
                              "--force-device-scale-factor=2","--app="+url,
                              "--disable-extensions","--disable-infobars"],
                        viewport={"width":1440,"height":900},
                        device_scale_factor=2,accept_downloads=False,
                        service_workers="block", permissions=[],reduced_motion="reduce")
                    try:
                        context.route("**/*",guard_route)
                        install_presentation_cleanup(context)
                        page=context.pages[0] if context.pages else context.new_page()
                        if not exact_first_party(url,page.url):
                            page.goto(url,wait_until="domcontentloaded",timeout=35000)
                        if not exact_first_party(url,page.url):
                            raise ValueError("Source redirected outside apex/www")
                        page.evaluate("document.fonts.ready")
                        page.add_style_tag(content=MOCKUP_SCROLLBAR_STYLE)
                        geometry=page.evaluate("()=>({w:innerWidth,h:innerHeight,dpr:devicePixelRatio})")
                        if geometry!={"w":1440,"h":900,"dpr":2}:
                            raise ValueError("Source DPR2/viewport geometry mismatch")
                        locator=page.locator(control["selector"])
                        if locator.count()!=1:raise ValueError("Inspected selector is no longer unique")
                        locator.scroll_into_view_if_needed(timeout=10000)
                        if not locator.is_visible() or not locator.is_enabled():
                            raise ValueError("Source selected control not actionable")
                        live_label=locator.evaluate("""e => (e.getAttribute('aria-label')||
                           e.getAttribute('title')||e.innerText||'').replace(/\\s+/g,' ').trim()""")
                        if live_label.casefold()!=control["text"].casefold():
                            raise ValueError("Source control label changed since Stagehand selection")
                        box=locator.bounding_box()
                        if not box or any(not math.isfinite(float(v)) for v in box.values()):
                            raise ValueError("Source control lost real DOM geometry")
                        def now(): return max(0.,time.monotonic()-clock[0])
                        def move(x,y):
                            page.mouse.move(x,y)
                            lastpos[:]=[x,y]
                            if clock[0] is not None:
                                t=round(now(),6)
                                if not samples or t>samples[-1]["t"]:
                                    samples.append({"t":t,"x":round(x*2,4),"y":round(y*2,4)})
                        def smooth(x,y,duration):
                            sx,sy=lastpos
                            start=time.monotonic()
                            count=max(25,round(duration*70))
                            for step in range(1,count+1):
                                v=step/count
                                eased=v*v*(3-2*v)
                                move(sx+(x-sx)*eased,sy+(y-sy)*eased)
                                wait=start+v*duration-time.monotonic()
                                if wait>0: time.sleep(wait)
                        def wait_until(t):
                            while now()<t:
                                time.sleep(min(.012,max(.001,t-now())))
                        def page_state():
                            return page.evaluate("""() => ({
                              theme:document.documentElement.className,
                              body:document.body.className,
                              text:(document.body.innerText||'').slice(0,6000),
                              dialogs:[...document.querySelectorAll('[role=dialog]')].filter(
                                e=>e.checkVisibility()).map(e=>(e.innerText||'').slice(0,200))
                            })""")
                        encoder_argv=["ffmpeg","-hide_banner","-loglevel","error",
                              "-y","-f","x11grab","-draw_mouse","0",
                              "-video_size","2880x1800","-framerate","60",
                              "-i",display,"-t",str(seconds),
                              "-c:v","libx264","-preset","ultrafast","-crf","14",
                              "-pix_fmt","yuv420p","-threads","4","-g","120",
                              "-an","-movflags","+faststart",str(output)]
                        with (folder/"recording.log").open("w") as recorder_log:
                            encoder=subprocess.Popen(encoder_argv,
                                stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                                stderr=recorder_log)
                            clock[0]=time.monotonic()
                            try:
                                move(*lastpos)
                                # Start actual cursor approach promptly: a
                                # long motionless opening is not a useful demo.
                                # Still allow a real contextual wide frame.
                                wait_until(.20)
                                rect=locator.bounding_box()
                                if not rect:raise ValueError("Control vanished during native recording")
                                cx=rect["x"]+rect["width"]*.5
                                cy=rect["y"]+rect["height"]*.5
                                smooth(cx,cy,.54)
                                before=page.screenshot(type="png",animations="disabled")
                                before_state=page_state()
                                target={k:round(2*float(rect[k]),4)
                                        for k in ("x","y","width","height")}
                                # Record a genuine final Playwright mouse move
                                # adjacent to its actual press. The source-time
                                # provenance gate allows <=160ms between pointer
                                # evidence and a real click, never guessed points.
                                move(cx,cy)
                                page.mouse.down()
                                tdown=round(now(),6)
                                events.append({"kind":"pointerdown","t":tdown,
                                  "actionKind":"click","label":control["text"],
                                  "targetRect":target})
                                time.sleep(.085)
                                page.mouse.up()
                                events.append({"kind":"pointerup","t":round(now(),6),
                                               "label":control["text"]})
                                page.wait_for_timeout(460)
                                if not exact_first_party(url,page.url):
                                    raise ValueError("Original product navigated outside permitted host")
                                after=page.screenshot(type="png",animations="disabled")
                                after_state=page_state()
                                from scripts.public_interaction_scout import diff_score
                                delta=diff_score(before,after)
                                if delta["changedFraction"]<.025:
                                    raise ValueError("Native product action had no meaningful pixel change")
                                result=_real_result(page,control,before_state,after_state)
                                events.append({"kind":"verified_result","t":round(now(),6),
                                  "label":control["text"],"resultRect":result,
                                  "evidence":"Live same-origin Chromium DOM state and observed screenshot pixel change"})
                                print("REAL_ACTION",control_id,delta,result,flush=True)
                                wait_until(seconds-1.6)
                                smooth(1200.,700.,.35)
                                wait_until(seconds-.5)
                            finally:
                                encoder.wait(timeout=40)
                        if encoder.returncode:
                            raise RuntimeError("Real X11 60fps recording failed")
                    finally:
                        context.close()
        finally:
            if saved_display is None:os.environ.pop("DISPLAY",None)
            else:os.environ["DISPLAY"]=saved_display
            xvfb.terminate()
            try:xvfb.wait(timeout=4)
            except subprocess.TimeoutExpired:xvfb.kill()
    meta=json.loads(subprocess.check_output(["ffprobe","-v","error",
      "-show_entries","stream=width,height,avg_frame_rate,nb_frames:format=duration",
      "-of","json",str(output)],text=True))
    stream=meta["streams"][0]
    if ((int(stream["width"]),int(stream["height"]),stream["avg_frame_rate"])
         !=(*NATIVE,"60/1")):
        raise ValueError("Native video source geometry/fps mismatch")
    frames=int(stream["nb_frames"])
    if frames!=round(seconds*FPS) or len(samples)<25 or len(events)!=3:
        raise ValueError("Incomplete original source frames, cursor or real UI event")
    receipt={"schema":"sauce-stagehand-native-real-action-v1",
      "source":url,"capture":"Chromium X11 native DPR2 60fps",
      "fps":FPS,"cursorless":True,"source_sha256":sha(output),
      "frameCount":frames,
      "capture_rect":{"width":NATIVE[0],"height":NATIVE[1]},
      "viewport":{"width":CSS[0],"height":CSS[1],"dpr":2},
      "events":events,"pointer_samples":samples,
      "independentProof":"Separate source UI probe passed before recording",
      "stagehandObservedControlId":control_id,
      "creativeApproved":False}
    (folder/"original-source-events.json").write_text(json.dumps(receipt,indent=2)+"\n")
    return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--url",required=True)
    p.add_argument("--inspection",required=True,type=Path)
    p.add_argument("--observations",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--seconds",type=float,default=10.)
    p.add_argument("--display",default=":174")
    args=p.parse_args()
    data=capture(args.url,args.inspection,args.observations,args.out,
                 seconds=args.seconds,display=args.display)
    print(json.dumps({"sourceSha256":data["source_sha256"],
       "realSourceEvents":len(data["events"]),"pointerSamples":len(data["pointer_samples"]),
       "sourceFrames":data["frameCount"],"premiumApproved":False}))


if __name__=="__main__":
    main()
