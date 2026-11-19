#!/usr/bin/env python3
"""Experimental Sauce Basic per-page film, OFFLINE HTML fixtures only.

Uses the shared dry-run wheel timeline verbatim; captures actual Playwright
Chromium frames to H.264. Not a production source-replay or URL-ingestion API.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import time
from pathlib import Path

from basic_tour_planner import TourContract, plan_page
from basic_tour_discovery import read_page, settle_page

FPS=60
CHROME="/opt/devmcp-browsers/chromium_headless_shell-1254/chrome-headless-shell-linux64/chrome-headless-shell"


def scheduled_wheels(plan: dict) -> list[tuple[float,float]]:
    clock=0.0
    events=[]
    for step in plan["steps"]:
        if step["kind"]=="wheel":
            for wheel in step["steps"]:
                events.append((clock+wheel["at_ms"],wheel["dy"]))
        clock+=step["duration_ms"]
    return events


def render_offline_fixture(html_path: Path, output: Path,
                           report_path: Path, *, profile: str="balanced") -> dict:
    from playwright.sync_api import sync_playwright
    if not html_path.is_file() or html_path.suffix != ".html":
        raise ValueError("An existing local .html test fixture is required")
    if not output.parent.is_dir():
        output.parent.mkdir(parents=True)
    source=html_path.read_bytes()
    if len(source)>500_000:
        raise ValueError("Oversized fixture refused")
    contract=TourContract("https://offline.example.org/",scope="homepage",profile=profile)
    with sync_playwright() as pw:
        browser=pw.chromium.launch(
            executable_path=CHROME if Path(CHROME).is_file() else None,
            headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
        page=browser.new_page(viewport={"width":1280,"height":720},
                              device_scale_factor=2,accept_downloads=False)
        page.set_content(source.decode("utf-8"),wait_until="domcontentloaded")
        settle_page(page)
        initial=read_page(page,contract.root_url)
        plan=plan_page(initial,contract)
        planned_ms=plan["duration_ms"]
        count=math.ceil(planned_ms/1000*FPS)
        if count>3600:
            raise ValueError("This experimental fixture proof is limited to 60s")
        schedule=scheduled_wheels(plan)
        cmd=["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
             "-f","image2pipe","-vcodec","mjpeg","-framerate","60",
             "-i","pipe:0","-vf","scale=1920:1080:flags=lanczos",
             "-c:v","libx264","-preset","veryfast","-crf","21",
             "-pix_fmt","yuv420p","-r","60","-movflags","+faststart",
             str(output)]
        pipe=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,
                              stderr=subprocess.PIPE)
        checkpoints=[]
        pending=0
        started=time.monotonic()
        try:
            for frame in range(count):
                timestamp=frame*1000/FPS
                while pending<len(schedule) and schedule[pending][0]<=timestamp+0.0001:
                    page.mouse.wheel(0,schedule[pending][1])
                    pending+=1
                if frame%30==0 or frame==count-1:
                    checkpoints.append({"frame":frame,
                        "at_ms":round(timestamp,3),
                        "scroll_y":page.evaluate("scrollY")})
                data=page.screenshot(type="jpeg",quality=90,scale="device",
                                     caret="hide",animations="allow")
                pipe.stdin.write(data)
            pipe.stdin.close()
            stderr=pipe.stderr.read()
            exit_code=pipe.wait(timeout=60)
            if exit_code!=0:
                raise RuntimeError("FFmpeg failed: "+stderr.decode()[-200:])
            verified_scroll=page.evaluate("scrollY")
            expected=max(0,initial.height-initial.viewport_height)
            ffprobe=subprocess.check_output(["ffprobe","-v","error",
                "-show_entries","stream=codec_name,width,height,r_frame_rate,nb_frames:format=duration",
                "-of","json",str(output)],text=True)
            media=json.loads(ffprobe)
            video=media["streams"][0]
            assert int(video["nb_frames"])==count
            assert video["r_frame_rate"]=="60/1"
            assert(video["width"],video["height"])==(1920,1080)
            report={
                "status":"experimental_fixture_segment","source":"local HTML fixture",
                "fixture_sha256":hashlib.sha256(source).hexdigest(),
                "plan":{k:v for k,v in plan.items() if k!="steps"},
                "wheel_events_planned":len(schedule),
                "wheel_events_sent":pending,
                "planned_ms":planned_ms,
                "encoded_ms":round(1000*float(media["format"]["duration"]),3),
                "frames":count,"video":str(output),
                "wall_seconds":round(time.monotonic()-started,3),
                "final_scroll_y":verified_scroll,"expected_final_scroll_y":expected,
                "final_scroll_error_px":abs(verified_scroll-expected),
                "checkpoints":checkpoints
            }
            report_path.write_text(json.dumps(report,indent=2))
            return report
        finally:
            if pipe.poll() is None:
                pipe.kill()
            browser.close()


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--fixture",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(render_offline_fixture(args.fixture,args.output,args.report),indent=2))
