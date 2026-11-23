#!/usr/bin/env python3
"""Native-60fps X11 browser recorder for two SCOUT-VERIFIED safe UI actions.

Explicit per-run hostname allowlist, safe request routing, no forms/auth,
no invented cursor, no site-specific selectors, original source + receipt
sha256. Private experiment only; NOT public arbitrary-URL execution.
"""
from __future__ import annotations
import argparse,hashlib,json,os,subprocess,time,math,tempfile
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
from capture_safety import validate_public_url,guard_route
from public_interaction_scout import JS,STATE,safe_action,diff_score,sha,CHROME,select_story_actions
from basic_tour_discovery import settle_page
from session_capture import MOCKUP_SCROLLBAR_STYLE,install_presentation_cleanup

FPS=60
CSS=(1440,900)
FRAME=(2880,1800)


def _filehash(file):
    h=hashlib.sha256()
    with open(file,"rb") as stream:
        for buf in iter(lambda:stream.read(1024*1024),b""):
            h.update(buf)
    return h.hexdigest()


def capture(scout_file,folder,allowed_host,*,labels,seconds=12,display=":149"):
    folder=Path(folder)
    if folder.exists() and list(folder.iterdir()):
        raise ValueError("Recording directory must be new; no overwrites")
    if not 10<=seconds<=20:
        raise ValueError("Only bounded 10..20-second real recordings")
    scout=json.loads(Path(scout_file).read_text())
    selection=select_story_actions(scout)
    if labels is None:
        labels=[x["label"] for x in selection["actions"]]
    if len(labels)!=2 or len(set(labels))!=2:
        raise ValueError("Exactly two distinct source-verified actions required")
    url=scout["observedLandingUrl"]
    host=(urlsplit(validate_public_url(url)).hostname or "").lower()
    if host!=allowed_host.lower():
        raise ValueError("Explicit hostname allowlist required")
    approved={e["label"]:e for e in scout["accepted"]}
    if any(label not in approved for label in labels):
        raise ValueError("Requested action has no independent live pixel admission")
    if not display.startswith(":") or not display[1:].isdigit() or not 120<=int(display[1:])<=200:
        raise ValueError("Use a dedicated private Xvfb display")
    folder.mkdir(parents=True,exist_ok=True)
    log=(folder/"xvfb.log").open("w")
    xvfb=subprocess.Popen(["Xvfb",display,"-screen","0","2880x1800x24",
                  "-nolisten","tcp","-ac"],stdout=log,stderr=subprocess.STDOUT)
    time.sleep(.65)
    if xvfb.poll() is not None:raise RuntimeError("Dedicated private X11 server unavailable")
    old_display=os.environ.get("DISPLAY")
    os.environ["DISPLAY"]=display
    events=[];ptr=[];proof=[];stamp=[None]
    video=folder/"source-native-dpr2-60.mp4"
    def now():
        return max(0.,time.monotonic()-stamp[0]) if stamp[0] is not None else 0.
    try:
        with tempfile.TemporaryDirectory(prefix="sauce-scout-public-chrome-") as profile:
            with sync_playwright() as pw:
                ctx=pw.chromium.launch_persistent_context(
                    profile,headless=False,
                    executable_path=os.environ.get("SAUCE_SCOUT_CHROME_BIN") or
                      "/srv/devmcp-workspaces/5c407ce984e7defcf77da3f1f9cb7f67/sauce-v05-release/studio/.tmp/educational-pilot/browsers/chromium-1254/chrome-linux64/chrome",
                    args=["--no-sandbox","--disable-dev-shm-usage","--window-position=0,0",
                         "--window-size=1440,900","--force-device-scale-factor=2",
                         "--app="+url,"--disable-extensions","--disable-infobars"],
                    viewport={"width":CSS[0],"height":CSS[1]},device_scale_factor=2,
                    reduced_motion="reduce",accept_downloads=False,
                    service_workers="block",permissions=[])
                ctx.route("**/*",guard_route)
                install_presentation_cleanup(ctx)
                page=ctx.pages[0] if ctx.pages else ctx.new_page()
                if page.url!=url:
                    page.goto(url,wait_until="domcontentloaded",timeout=35000)
                if (urlsplit(page.url).hostname or "").lower()!=host:
                    raise ValueError("Unexpected cross-host navigation")
                settle_page(page)
                # This recorder was missing the existing Sauce presentation
                # cleanup. Apply BEFORE original screenshot or X11 capture.
                # Scrollability and source CSS layout remain independently
                # verified; the scrollbar chrome is not product content.
                page.add_style_tag(content=MOCKUP_SCROLLBAR_STYLE)
                measured=page.evaluate("()=>({width:innerWidth,height:innerHeight,dpr:devicePixelRatio})")
                if measured!={"width":CSS[0],"height":CSS[1],"dpr":2}:
                    raise ValueError("Original browser DPR2 geometry not proven: "+str(measured))
                available=page.evaluate(JS)
                for label in labels:
                    items=[x for x in available if x["label"]==label and safe_action(x)]
                    if len(items)!=1:raise ValueError("Source UI action changed or ambiguous: "+label)
                pos=[1200.,715.]
                def move(x,y):
                    page.mouse.move(x,y)
                    pos[:]=[x,y]
                    if stamp[0] is not None:
                        t=round(now(),6)
                        if not ptr or t>ptr[-1]["t"]:
                            ptr.append({"t":t,"x":round(x*2,3),"y":round(y*2,3)})
                def smooth(x,y,sec):
                    start=time.monotonic();sx,sy=pos
                    count=max(12,int(sec*56))
                    for i in range(1,count+1):
                        q=i/count;v=q*q*(3-2*q)
                        move(sx+(x-sx)*v,sy+(y-sy)*v)
                        until=start+q*sec-time.monotonic()
                        if until>0:time.sleep(until)
                def wait(t):
                    while now()<t:time.sleep(min(.01,max(.001,t-now())))
                def rect(r):
                    return {k:round(float(r[key])*2,4)
                            for k,key in (("x","x"),("y","y"),("width","w"),("height","h"))}
                move(*pos)
                if page.screenshot(type="png")[:8]!=b"\x89PNG\r\n\x1a\n":
                    raise ValueError("Native Chromium screenshot failed")
                argv=["ffmpeg","-hide_banner","-loglevel","error","-y",
                      "-f","x11grab","-draw_mouse","0",
                      "-video_size","2880x1800","-framerate","60","-i",display,
                      "-t",str(seconds),"-c:v","libx264","-preset","ultrafast",
                      "-crf","14","-threads","4","-pix_fmt","yuv420p",
                      "-g","120","-an","-movflags","+faststart",str(video)]
                with (folder/"capture.log").open("w") as capture_log:
                    encoder=subprocess.Popen(argv,stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL,stderr=capture_log)
                    stamp[0]=time.monotonic()
                    move(*pos)
                    try:
                        for index,label in enumerate(labels):
                            wait(1.25+index*4.05)
                            items=[x for x in page.evaluate(JS)
                                   if x["label"]==label and safe_action(x)]
                            if len(items)!=1:
                                raise ValueError("Source action vanished after first state")
                            c=items[0]
                            before=page.screenshot(type="png",animations="disabled")
                            baseline=page.evaluate(STATE)
                            panels_before=page.evaluate("""() => [
                              ...document.querySelectorAll('[role="dialog"],[aria-modal="true"],table,[role="grid"]')
                            ].filter(e=>{const r=e.getBoundingClientRect();const st=getComputedStyle(e);
                              return st.display!=='none'&&st.visibility!=='hidden'&&r.width>200
                              &&r.height>150&&r.x>=0&&r.y>=0
                              &&r.right<=innerWidth&&r.bottom<=innerHeight;
                            }).map(e=>{const r=e.getBoundingClientRect();return {
                              tag:e.tagName,role:e.getAttribute('role')||'',
                              x:r.x,y:r.y,w:r.width,h:r.height,
                              text:(e.innerText||'').slice(0,500)};})""")
                            cx=c["x"]+c["w"]/2;cy=c["y"]+c["h"]/2
                            smooth(cx,cy,.65)
                            target=rect(c)
                            page.mouse.down()
                            events.append({"kind":"pointerdown","t":round(now(),6),
                                "label":label,"actionKind":"click","targetRect":target,
                                "pointer":{"x":round(pos[0]*2,3),"y":round(pos[1]*2,3)}})
                            time.sleep(.08)
                            page.mouse.up()
                            events.append({"kind":"pointerup","t":round(now(),6),
                                           "label":label})
                            page.wait_for_timeout(400)
                            if ((urlsplit(page.url).hostname or "").lower()!=host or
                                urlsplit(page.url).path!=urlsplit(url).path):
                                raise ValueError("Action navigated away from admitted public state")
                            after=page.screenshot(type="png",animations="disabled")
                            changed=diff_score(before,after)
                            state=page.evaluate(STATE)
                            if (changed["changedFraction"]<.085 or
                                not (baseline["text"]!=state["text"] or
                                     baseline["theme"]!=state["theme"] or
                                     baseline["body"]!=state["body"] or
                                     baseline["controls"]!=state["controls"])):
                                raise ValueError("Actual action did not verify state+pixels")
                            # Source-measured dialog surface for an explanatory
                            # modal; whole genuine browser for a theme.
                            dialog=page.evaluate("""() => {
                               const el=[...document.querySelectorAll('[role="dialog"]')]
                                  .find(e=>{const r=e.getBoundingClientRect();
                                    return r.width>280&&r.height>120&&r.left>=0
                                      &&r.top>=0&&r.right<=innerWidth&&r.bottom<=innerHeight});
                               return el?el.getBoundingClientRect().toJSON():null
                            }""")
                            discovered=None
                            if not dialog:
                                after_panels=page.evaluate("""() => [
                                  ...document.querySelectorAll('[role="dialog"],[aria-modal="true"],table,[role="grid"]')
                                ].filter(e=>{const r=e.getBoundingClientRect();const st=getComputedStyle(e);
                                  return st.display!=='none'&&st.visibility!=='hidden'&&r.width>200
                                  &&r.height>150&&r.x>=0&&r.y>=0
                                  &&r.right<=innerWidth&&r.bottom<=innerHeight;
                                }).map(e=>{const r=e.getBoundingClientRect();return {
                                  tag:e.tagName,role:e.getAttribute('role')||'',
                                  x:r.x,y:r.y,w:r.width,h:r.height,
                                  text:(e.innerText||'').slice(0,500)};})""")
                                old={(v["tag"],v["text"][:100]) for v in panels_before}
                                fresh=[v for v in after_panels
                                       if (v["tag"],v["text"][:100]) not in old and
                                       v["w"]*v["h"]>=.075*CSS[0]*CSS[1]]
                                if fresh:
                                    discovered=max(fresh,key=lambda v:v["w"]*v["h"])
                            result_panel=dialog or discovered
                            if result_panel:
                                result={"x":round(2*result_panel["x"],4),
                                    "y":round(2*result_panel["y"],4),
                                    "width":round(2*result_panel.get("width",result_panel.get("w")),4),
                                    "height":round(2*result_panel.get("height",result_panel.get("h")),4)}
                            else:
                                result={"x":0,"y":0,"width":2880,"height":1800}
                            ev={"kind":"verified_result","label":label,
                                "t":round(now(),6),"resultRect":result,
                                "evidence":"Original Chromium DOM state and screenshot pixel change confirmed"}
                            events.append(ev)
                            proof.append({"label":label,"beforeSha256":sha(before),
                                "afterSha256":sha(after),
                                "actualChangedFraction":changed["changedFraction"],
                                "changedMeanChannelDelta":changed["meanChannelDelta"]})
                            (folder/f"real-before-{index}.png").write_bytes(before)
                            (folder/f"real-after-{index}.png").write_bytes(after)
                            print("VERIFIED",label,changed,result,flush=True)
                        wait(seconds-1.3)
                        smooth(1220.,700.,.35)
                        wait(seconds-.4)
                    finally:
                        try:encoder.wait(timeout=35)
                        except subprocess.TimeoutExpired:
                            encoder.terminate()
                            try:encoder.wait(timeout=8)
                            except subprocess.TimeoutExpired:encoder.kill()
                if encoder.returncode!=0:
                    raise RuntimeError("Original native 60fps encoder error")
                if len(events)!=6 or len(ptr)<50:raise ValueError("Insufficient true pointer interactions")
                meta=json.loads(subprocess.check_output(["ffprobe","-v","error",
                    "-show_entries","stream=width,height,avg_frame_rate,nb_frames:format=duration",
                    "-of","json",str(video)],text=True))
                x=meta["streams"][0]
                if (x["width"],x["height"],x["avg_frame_rate"])!=(2880,1800,"60/1"):
                    raise ValueError("Native X11 source encoding geometry mismatch")
                if abs(float(meta["format"]["duration"])-seconds)>.08:
                    raise ValueError("Captured native video duration not accurate")
                # Mirror existing long source capture receipt, not a synthetic
                # editorial plan. A generic manifest adapter can validate it.
                receipt={"schema":"sauce-public-real-actions-v1",
                  "source":url,"capture":"Chromium X11 native DPR2 60fps",
                  "fps":60,"cursorless":True,
                  "source_sha256":_filehash(video),
                  "frameCount":int(x["nb_frames"]),
                  "capture_rect":{"width":2880,"height":1800},
                  "viewport":{"width":1440,"height":900,"dpr":2},
                  "events":events,"pointer_samples":ptr,
                  "sourcePixelProof":proof,
                  "scoutAutonomousSelection":selection if labels==[
                      x["label"] for x in selection["actions"]] else None,
                  "premiumApproved":False}
                (folder/"original-source-events.json").write_text(json.dumps(receipt,indent=2)+"\n")
                print("ORIGINAL_VIDEO",video,receipt["source_sha256"],"frames",x["nb_frames"],
                     "pointer",len(ptr),"events",len(events),flush=True)
                return receipt
    finally:
        if old_display is None:os.environ.pop("DISPLAY",None)
        else:os.environ["DISPLAY"]=old_display
        xvfb.terminate()
        try:xvfb.wait(timeout=5)
        except subprocess.TimeoutExpired:xvfb.kill()
        log.close()


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--scout",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--allow-host",required=True)
    p.add_argument("--action",action="append",
                   help="Optional R&D override; by default select two distinct verified actions")
    p.add_argument("--display",default=":149")
    p.add_argument("--seconds",type=float,default=12)
    a=p.parse_args()
    capture(a.scout,a.out,a.allow_host,labels=a.action,display=a.display,seconds=a.seconds)
