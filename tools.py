"""Sauce Vids execution boundary. Hermes makes artistic decisions; this plugin records and renders."""
import ipaddress
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import time
import uuid
from urllib.parse import urljoin, urlsplit

ROOT = Path(os.environ.get("SAUCE_RUN_DIR", str(Path.home() / ".sauce-vids"))).expanduser()

def _receipt(**items):
    return json.dumps(items, ensure_ascii=False)

def _id(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,39}", value):
        raise ValueError("Invalid identifier")
    return value

def _url(value, host=None):
    if not isinstance(value, str) or len(value) > 2048:
        raise ValueError("Invalid URL")
    p = urlsplit(value)
    hosts = {x.strip().lower() for x in os.environ.get("SAUCE_ALLOWED_HOSTS", "").split(",") if x.strip()}
    if not hosts:
        raise ValueError("Set SAUCE_ALLOWED_HOSTS to the domains you explicitly approve")
    if p.scheme != "https" or p.hostname not in hosts or p.username or p.password or p.port not in (None, 443):
        raise ValueError("Only approved public HTTPS origins are permitted")
    if host and p.hostname != host:
        raise ValueError("Navigation leaves the approved host")
    # The browser worker should additionally enforce egress and DNS policies.
    for answer in socket.getaddrinfo(p.hostname, 443):
        if not ipaddress.ip_address(answer[4][0]).is_global:
            raise ValueError("Host resolves to non-public IP")
    return p.hostname

def _dir(run_id):
    path = ROOT / _id(run_id)
    path.mkdir(parents=True, exist_ok=True)
    return path

def _check_actions(actions):
    if not isinstance(actions, list) or len(actions) > 24:
        raise ValueError("Maximum 24 actions")
    result = []
    for a in actions:
        if not isinstance(a, dict) or a.get("type") not in ("wait", "scroll", "hover", "click_link", "click_tab", "focus"):
            raise ValueError("Unsupported action")
        mode = a["type"]
        seconds = float(a.get("seconds", 0.65))
        if not 0.1 <= seconds <= 3:
            raise ValueError("Action time outside 0.1–3 seconds")
        item = {"type": mode, "seconds": seconds}
        if mode in ("hover", "click_link", "click_tab", "focus"):
            sel = a.get("selector", "")
            if not isinstance(sel, str) or not 1 <= len(sel) <= 150:
                raise ValueError("Missing or excessively long selector")
            item["selector"] = sel
        if "camera_x" in a:
            x = a["camera_x"]
            if (mode != "focus" or type(x) not in (int,float)
                or not 0 <= x <= 1440):
                raise ValueError("camera_x only accepts on-page focus positions")
            item["camera_x"] = float(x)
        if "label" in a:
            label = a["label"]
            if not isinstance(label, str) or not 1 <= len(label.strip()) <= 100:
                raise ValueError("Action label must be 1–100 characters")
            item["label"] = label.strip()
        if "expected_visible_heading" in a:
            if mode not in ("click_link", "click_tab"):
                raise ValueError("expected_visible_heading supported only on clicks")
            heading = a["expected_visible_heading"]
            if not isinstance(heading, str) or not 1 <= len(heading.strip()) <= 160:
                raise ValueError("expected_visible_heading must be 1–160 non-whitespace characters")
            item["expected_visible_heading"] = heading.strip()
        if mode == "scroll":
            pixels = a.get("pixels", 400)
            if type(pixels) is not int or not -1300 <= pixels <= 1300:
                raise ValueError("Scroll outside supported range")
            item["pixels"] = pixels
        result.append(item)
    return result

def _wait_for_expected_heading(page, heading):
    """Wait for rendered content, not just DOMContentLoaded (important for SPAs).

    Exact accessible heading match avoids accidentally advancing on unrelated text.
    A missing heading raises instead of marking an incomplete shot successful.
    """
    page.get_by_role("heading", name=heading, exact=True).first.wait_for(
        state="visible", timeout=15000
    )


# Cursor rendering deliberately happens AFTER capture. Browser-screencast
# footage is kept clean; hand-drawn DOM pointers are not acceptable artifacts.
# Playwright record_video_size determines the container size; it does not
# scale the page. A smaller viewport creates grey padding around content.
CAPTURE_VIEWPORT = {"width": 1920, "height": 1080}
CAPTURE_SIZE = {"width": 1920, "height": 1080}
CAPTURE_FPS = 30
CAPTURE_DEVICE_SCALE = 1

def _verify_recording(path):
    """Verify real frames were saved; a valid EBML header alone is not proof."""
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe is required to verify the browser recording")
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,width,height,avg_frame_rate",
         "-of", "json", str(path)],
        capture_output=True, text=True, timeout=25,
    )
    if result.returncode:
        raise RuntimeError("Browser recording is unreadable or empty")
    metadata = json.loads(result.stdout)
    videos = [v for v in metadata.get("streams", []) if v.get("codec_type") == "video"]
    if not videos:
        raise RuntimeError("No video stream in browser recording")
    video = videos[0]
    from fractions import Fraction
    fps = float(Fraction(video.get("avg_frame_rate", "0/1")))
    duration = float(metadata.get("format", {}).get("duration", 0))
    if duration <= 0.5 or video.get("width") != 1920 or video.get("height") != 1080 or fps < 29.5:
        raise RuntimeError("Recording does not meet native 1080p/30fps baseline")
    return {"duration_s":duration, "width":1920, "height":1080, "fps":fps}


def capture(args, **kwargs):
    try:
        project = _id(args.get("project"))
        url = args.get("url", "")
        host = _url(url)
        actions = _check_actions(args.get("actions", []))
        from playwright.sync_api import sync_playwright
        run_id = project + "-" + uuid.uuid4().hex[:10]
        folder = _dir(run_id)
        events = []
        start = time.monotonic()
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
            context = browser.new_context(
                viewport=CAPTURE_VIEWPORT,
                device_scale_factor=CAPTURE_DEVICE_SCALE,
                record_video_dir=str(folder),
                record_video_size=CAPTURE_SIZE,
                record_video_fps=CAPTURE_FPS,
                reduced_motion="reduce",
            )
            page = context.new_page()
            page.set_default_timeout(10000)
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            _url(page.url, host)
            page.wait_for_timeout(900)
            events.append({"time": round(time.monotonic()-start,2), "type": "page", "url": page.url})
            for action in actions:
                mode = action["type"]
                heading_verified = False
                action_started = round(time.monotonic()-start,2)
                position = None
                if mode == "scroll":
                    page.mouse.wheel(0, action["pixels"])
                elif mode in ("hover", "focus"):
                    el = page.locator(action["selector"]).first
                    if mode == "focus":
                        el.evaluate("(node)=>node.scrollIntoView({behavior:'smooth',block:'center'})")
                        page.wait_for_timeout(650)
                    else:
                        el.scroll_into_view_if_needed()
                    box = el.bounding_box()
                    if box is None: raise RuntimeError("Target not visible")
                    x,y = box["x"]+box["width"]/2,box["y"]+box["height"]/2
                    # A demo shot must contain BOTH the heading and its
                    # adjacent product illustration. Frame their midpoint,
                    # rather than zooming off-axis into one column.
                    framing_x = (x + action.get("camera_x",x)) / 2
                    position = {"x":round(framing_x,1),"y":round(y,1)}
                    page.mouse.move(x,y,steps=26)
                elif mode == "click_link":
                    el = page.locator(action["selector"]).first
                    el.scroll_into_view_if_needed()
                    if el.evaluate("(e)=>e.tagName.toLowerCase()") != "a":
                        raise ValueError("Only actual anchor links can be clicked")
                    href = el.get_attribute("href")
                    if not href: raise ValueError("Missing href")
                    target = urljoin(page.url, href)
                    _url(target, host)
                    box = el.bounding_box()
                    if box is None: raise RuntimeError("Target not visible")
                    x,y = box["x"]+box["width"]/2, box["y"]+box["height"]/2
                    page.mouse.move(x,y,steps=25)
                    page.mouse.click(x,y)
                    page.wait_for_load_state("domcontentloaded",timeout=15000)
                    _url(page.url, host)
                elif mode == "click_tab":
                    el = page.locator(action["selector"]).first
                    if el.get_attribute("role") != "tab":
                        raise ValueError("Only role=tab controls can use click_tab")
                    el.scroll_into_view_if_needed()
                    box = el.bounding_box()
                    if box is None: raise RuntimeError("Tab target invisible")
                    x,y=box["x"]+box["width"]/2,box["y"]+box["height"]/2
                    page.mouse.move(x,y,steps=25)
                    page.mouse.click(x,y)
                    _url(page.url, host)
                if mode in ("click_link", "click_tab") and action.get("expected_visible_heading"):
                    _wait_for_expected_heading(page, action["expected_visible_heading"])
                    heading_verified = True
                page.wait_for_timeout(int(action["seconds"]*1000))
                event = {"time": round(time.monotonic()-start,2),
                         "start_time":action_started, "type": mode,
                         "url": page.url, "selector": action.get("selector")}
                if position:
                    event["position"] = position
                    if "camera_x" in action:
                        event["media_guided"] = True
                if action.get("label"):
                    event["label"] = action["label"]
                if heading_verified:
                    event["expected_visible_heading"] = action["expected_visible_heading"]
                    event["heading_verified"] = True
                events.append(event)
            page.wait_for_timeout(700)
            video = page.video
            page.close()
            context.close()
            video.save_as(str(folder/"recording.webm"))
            browser.close()
        media = _verify_recording(folder/"recording.webm")
        info = {"run_id":run_id,"source":"continuous Chromium recording","url":url,
                "events":events,"recording":str(folder/"recording.webm"),
                "verified_media":media,
                "capture_profile":{"viewport":CAPTURE_VIEWPORT,
                                   "video":CAPTURE_SIZE,
                                   "fps":CAPTURE_FPS,
                                   "device_scale_factor":CAPTURE_DEVICE_SCALE,
                                   "reduced_motion":"reduce",
                                   "cursor":"not_baked_into_pixels"},
                "claims":"Public website only; no authenticated deployment or customer action proved."}
        (folder/"capture.json").write_text(json.dumps(info,indent=2))
        return _receipt(ok=True, **info)
    except Exception as e:
        return _receipt(ok=False,error=str(e))

def render(args, **kwargs):
    try:
        if args.get("use_edit_plan"):
            from . import director
            return _receipt(ok=True, **director.render_edited(args))
        folder = _dir(args.get("run_id"))
        video = folder/"recording.webm"
        if not video.is_file(): raise ValueError("Missing recorded video")
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg: raise ValueError("FFmpeg is required")
        background = args.get("background_asset")
        output = folder/"final.mp4"
        command = [ffmpeg,"-y","-hide_banner","-loglevel","error","-i",str(video)]
        if background:
            if not isinstance(background,str) or not re.fullmatch(r"[a-zA-Z0-9_.-]{1,90}\.(png|jpg|jpeg)",background):
                raise ValueError("Invalid background filename")
            asset_root = Path(os.environ.get("SAUCE_ASSET_DIR","")).expanduser()
            if not os.environ.get("SAUCE_ASSET_DIR"):
                raise ValueError("SAUCE_ASSET_DIR is not configured")
            asset = asset_root/background
            if not asset.is_file(): raise ValueError("Licensed background file not found")
            command += ["-loop","1","-i",str(asset),"-filter_complex",
                "[0:v]fps=30,scale=1600:900:flags=lanczos[content];"
                "[1:v]scale=1920:1080:flags=lanczos[wall];"
                "[wall][content]overlay=160:90:shortest=1,format=yuv420p[v]",
                "-map","[v]"]
        else:
            command += ["-vf","fps=30,scale=1920:1080:flags=lanczos","-an"]
        command += ["-c:v","libx264","-crf","19","-preset","veryfast",
                    "-pix_fmt","yuv420p","-movflags","+faststart",str(output)]
        result = subprocess.run(command,capture_output=True,text=True,timeout=300)
        if result.returncode: raise RuntimeError(result.stderr[-1500:])
        receipt={"run_id":args["run_id"],"video":str(output),"bytes":output.stat().st_size,
                 "background_asset":background or None,"audio":"none","source":"real browser recording"}
        (folder/"render.json").write_text(json.dumps(receipt,indent=2))
        return _receipt(ok=True,**receipt)
    except Exception as e:
        return _receipt(ok=False,error=str(e))

def inspect(args, **kwargs):
    try:
        folder = _dir(args.get("run_id"))
        path = folder/"final.mp4"
        if not path.is_file(): raise ValueError("Render first")
        ffprobe=shutil.which("ffprobe")
        if not ffprobe: raise ValueError("ffprobe is required")
        res = subprocess.run([ffprobe,"-v","error","-show_streams","-show_format",
                              "-of","json",str(path)],capture_output=True,text=True,timeout=20,check=True)
        data = json.loads(res.stdout)
        capture_file = folder/"capture.json"
        provenance=json.loads(capture_file.read_text()) if capture_file.is_file() else {}
        return _receipt(ok=True,run_id=args["run_id"],video=str(path),
                        video_metadata=data,events=provenance.get("events",[]),
                        claims=provenance.get("claims"))
    except Exception as e:
        return _receipt(ok=False,error=str(e))
