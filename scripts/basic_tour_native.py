#!/usr/bin/env python3
"""Sauce Basic — bounded, deterministic native-browser website tours.

This is a PRIVATE PILOT CLI, NOT safe for public arbitrary-URL submission.
It reuses the existing Chromium/Playwright video helper and Sauce source-true
film-plan JSON contract, never a new frame-by-frame recording engine.

Preflight: public same-origin route crawl, robots, explicit allowhost, bounded.
Capture: independently recorded original Chromium WebM per page, real wheel
input, known presentation cleanup, in-page original existing Sauce arrow,
per-hold evidence and omissions. No forms, login, arbitrary clicks or LLM.
Render: source-faithful H264 1080p60 *resample* (source FPS is reported),
hard-cut chaptered MP4. Source and manifest hashes pin each JSON film plan.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright
from basic_tour_planner import TourContract,plan_page
from basic_tour_discovery import (crawl_public_site,read_page,settle_page,
                                   trigger_lazy_content,get_robots,USER_AGENT)
from basic_tour_quality import (quality_scan,park_cursor,visible_text_boxes,
                                ensure_observable,settle_visible_text,
                                settle_visible_images)
from session_capture import (PRESENTATION_CLEANUP_STYLE,
                             install_presentation_cleanup)
from capture_safety import validate_public_url,guard_route

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.live_capture import (ensure_video_helper,ARROW_CURSOR_JS)
from scripts.film_plan import load_film_plan
from basic_tour_media_qa import analyse_master
from basic_tour_autodirect import run as automatically_direct_basic_preview

CHROME=os.environ.get("SAUCE_CHROME_BIN") or (
    "/opt/devmcp-browsers/chromium_headless_shell-1254/"
    "chrome-headless-shell-linux64/chrome-headless-shell")

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):
            h.update(b)
    return h.hexdigest()

def probe(path):
    return json.loads(subprocess.check_output([
        "ffprobe","-v","error","-show_entries",
        "stream=codec_name,codec_type,width,height,r_frame_rate,nb_frames:"
        "format=duration,size","-of","json",str(path)],text=True,timeout=40))

def write_json(path,thing):
    path=Path(path)
    path.write_text(json.dumps(thing,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def safe_filename(url,index):
    return f"scene-{index:02d}" # no customer-controlled filesystem components

def render_segment(source:Path,output:Path,trim_seconds:float,
                   expected_duration:float, width:int,height:int)->dict:
    evidence=probe(source)
    stream=next(s for s in evidence["streams"] if s.get("codec_type")=="video")
    if (stream["width"],stream["height"])!=(width,height):
        raise RuntimeError("Browser video frame geometry mismatch; refuse fake native 1080p")
    raw_duration=float(evidence["format"]["duration"])
    trim=min(max(0.,trim_seconds),max(0.,raw_duration-1.))
    remaining=raw_duration-trim
    if remaining < expected_duration*.84:
        raise RuntimeError(f"Source too short: {remaining:.2f}s < {expected_duration:.2f}s planned")
    # Do not truncate an observed real-life delayed scroll. The browser's
    # true duration wins when it is longer than the planner's prediction.
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
         "-ss",f"{trim:.4f}","-i",str(source),"-map","0:v:0",
         "-vf",f"scale={width}:{height}:flags=lanczos,setsar=1,fps=60,format=yuv420p",
         "-an","-c:v","libx264","-preset","veryfast","-crf","19",
         "-movflags","+faststart",str(output)]
    subprocess.run(cmd,check=True,timeout=300)
    media=probe(output)
    video=media["streams"][0]
    if (video["width"],video["height"],video["r_frame_rate"])!=(width,height,"60/1"):
        raise RuntimeError("Output stream invalid")
    subprocess.run(["ffmpeg","-v","error","-xerror","-i",str(output),
                   "-f","null","-"],check=True,timeout=180)
    return {
        "source_dimensions":[width,height],"source_codec":stream["codec_name"],
        "source_rate":stream["r_frame_rate"],
        "source_sha256":sha(source),
        "recorded_source_seconds":round(raw_duration,4),
        "trimmed_initial_seconds":round(trim,4),
        "encoded_seconds":float(media["format"]["duration"]),
        "encoded_sha256":sha(output),
        "encoded_frames":int(video.get("nb_frames") or round(float(media["format"]["duration"])*60)),
        "native_1080p_css_source":width==1920 and height==1080,
        "native_60_source_verified":stream["r_frame_rate"]=="60/1",
    }

def capture_budget_seconds(plan_seconds:float)->float:
    """Hard bounded live-capture wall budget, distinct from video runtime.

    Source web pages can block CDP wheel calls for tens of seconds. Refuse
    runaway jobs rather than quietly rendering a two-minute film from a
    39-second recording contract. Does not silently speed up or drop source.
    """
    if not 1 <= plan_seconds <= 3600:
        raise ValueError("Plan duration outside bounded capture contract")
    return round(min(180., max(24., plan_seconds*1.65+12.)),3)


def assert_capture_budget(started:float, budget:float, *,
                          clock=time.monotonic) -> None:
    elapsed=clock()-started
    if elapsed>budget:
        raise TimeoutError(f"browser_capture_budget_exceeded: {elapsed:.2f}s > {budget:.2f}s")


def safe_video_pointer(page,width,height)->list[int]:
    boxes=visible_text_boxes(page)
    spot=park_cursor((width,height),boxes)
    page.mouse.move(*spot)
    return [*spot]

def capture_page(browser, contract:TourContract, url:str,
                 directory:Path,source_plan:dict,
                 *,cursor_policy:str="none")->dict:
    directory.mkdir(exist_ok=True,parents=True)
    ensure_video_helper()
    folder=directory/"recorded"
    folder.mkdir(exist_ok=True)
    context=browser.new_context(
        viewport={"width":contract.width,"height":contract.height},
        device_scale_factor=2,
        record_video_dir=str(folder),
        record_video_size={"width":contract.width,"height":contract.height},
        service_workers="block",permissions=[],accept_downloads=False,
        user_agent=USER_AGENT,
    )
    context.route("**/*",guard_route)
    install_presentation_cleanup(context)
    started=time.monotonic()
    page=context.new_page()
    video=page.video
    issues=[]
    actions=[]
    try:
        resp=page.goto(url,wait_until="domcontentloaded",timeout=22000)
        if not resp or resp.status>=400 or urlsplit(page.url).hostname!=urlsplit(url).hostname:
            raise RuntimeError("URL redirect or site response changed")
        settle_page(page)
        page.add_style_tag(content=PRESENTATION_CLEANUP_STYLE)
        lazy_probe=trigger_lazy_content(page,max_steps=20)
        if lazy_probe["capped"]:
            issues.append("lazy_discovery_step_limit")
        page.evaluate("window.scrollTo(0,0)")
        page.wait_for_timeout(150)
        observed=read_page(page,url)
        if abs(observed.height-source_plan["source_height"])>max(80,source_plan["source_height"]*.05):
            raise RuntimeError("Page geometry changed since preflight; re-plan before recording")
        # A scroll-only tour has no meaningful mouse interaction: hiding
        # a permanently parked arrow is more honest than drawing fake moves.
        # Existing Sauce artwork remains available for opt-in real pointer
        # tracks; never fabricate a click between independently recorded pages.
        if cursor_policy=="arrow":
            page.evaluate(ARROW_CURSOR_JS)
        elif cursor_policy!="none":
            raise ValueError("Unsupported Basic cursor policy")
        initial=ensure_observable(page,max_attempts=3,interval_ms=150)
        issues+=initial["issues"]
        page_plan=plan_page(observed,contract)
        capture_start=time.monotonic()
        budget_s=capture_budget_seconds(page_plan["duration_ms"]/1000)
        trim_s=max(0.,capture_start-started-.6)
        hold_samples=[]
        drift_ms=[]
        for item in page_plan["steps"]:
            assert_capture_budget(capture_start,budget_s)
            if item["kind"]=="wheel":
                step_begin=time.monotonic()
                for entry in item["steps"]:
                    assert_capture_budget(capture_start,budget_s)
                    expected=entry["at_ms"]/1000.
                    remaining=expected-(time.monotonic()-step_begin)
                    if remaining>0:
                        page.wait_for_timeout(remaining*1000)
                    page.mouse.wheel(0,entry["dy"])
                drift_ms.append(round(((time.monotonic()-step_begin)*1000-item["duration_ms"]),1))
                actions.append({"type":"wheel","start":item["start"],"end":item["end"],
                                "count":len(item["steps"]),"t":round(time.monotonic()-capture_start,3)})
            else:
                # Observe real opacity transitions while stationary; do not
                # make transparent headings opaque or fake their text.
                text_settle=settle_visible_text(page,checks=3,interval_ms=140)
                issues.extend(text_settle["issues"])
                snap=quality_scan(page)
                if "incomplete_visible_images" in snap["issues"]:
                    snap=settle_visible_images(page,timeout_ms=1300)
                issues.extend(snap["issues"])
                pointer=None
                if cursor_policy=="arrow":
                    try:
                        pointer=safe_video_pointer(page,contract.width,contract.height)
                    except RuntimeError:
                        issues.append("cursor_park_not_proven")
                real_y=page.evaluate("scrollY")
                expected_y=item["scroll_y"]
                if abs(real_y-expected_y)>max(25,contract.height*.07):
                    issues.append("scroll_destination_mismatch")
                hold_samples.append({"scroll_y":real_y,"expected_scroll_y":expected_y,
                                     "duration_ms":item["duration_ms"],
                                     "cursor_css":pointer,"readiness":snap["readiness"],
                                     "text_settle":text_settle,
                                     "issues":snap["issues"]+text_settle["issues"]})
                assert_capture_budget(capture_start,budget_s)
                page.wait_for_timeout(item["duration_ms"])
        assert_capture_budget(capture_start,budget_s)
        # Final hold for a natural ending, not a fabricated CTA
        page.wait_for_timeout(350)
        end_y=page.evaluate("scrollY")
        max_y=page.evaluate("document.documentElement.scrollHeight-innerHeight")
        if abs(end_y-max_y)>max(25,contract.height*.07):
            issues.append("did_not_reach_bottom")
        active_seconds=time.monotonic()-capture_start
        if active_seconds>page_plan["duration_ms"]/1000*1.2+1.:
            issues.append("runtime_exceeded_preflight_by_20_percent")
        page.close()
        context.close()
        source=directory/"source.webm"
        shutil.copyfile(video.path(),source)
        output=directory/"segment-1080p60.mp4"
        media=render_segment(source,output,trim_s,page_plan["duration_ms"]/1000,
                             contract.width,contract.height)
        # This is the existing SourceTrue general film-plan JSON contract,
        # not a second, conflicting JSON engine. We compile a neutral plan.
        event_manifest={
            "schema":"sauce-basic-capture-v1","capture_rect":{
                "width":contract.width,"height":contract.height},
            "cursorless":True,  # no SECOND cursor should be added to video
            "source_url":url,"events":[],"observed_scroll":actions,
            "resting_pointer":("baked_into_source_pixels" if cursor_policy=="arrow"
                               else "none_for_scroll_only"),
        }
        manifest_path=directory/"capture-manifest.json"
        write_json(manifest_path,event_manifest)
        duration=media["encoded_seconds"]
        film_plan={
            "schema":"sauce-film-plan-v1",
            "sourceSha256":media["encoded_sha256"],
            "manifestSha256":sha(manifest_path),
            "durationSeconds":duration,
            "presentation":"fullscreen","cursor":"none",
            "audio":{"mode":"clean"},
            "camera":[{"at":0.0,"anchor":"wide","zoom":1.0},
                      {"at":duration,"anchor":"wide","zoom":1.0}],
        }
        film_path=directory/"film-plan.json"
        write_json(film_path,film_plan)
        # Compile through existing production FilmPlan validator. The film
        # is already source-faithful: this proves JSON edit compatibility.
        load_film_plan(film_plan,event_manifest,output,manifest_path,
                       (contract.width,contract.height),duration,film_path)
        result={
            "status":"captured","url":url,"title":observed.title,
            "cursor_policy":cursor_policy,
            "source_height_css":observed.height,"lazy_probe":lazy_probe,
            "planned_seconds":round(page_plan["duration_ms"]/1000,3),
            "observed_active_seconds":round(active_seconds,3),
            "capture_budget_seconds":budget_s,
            "capture_initial_seconds":round(trim_s,3),
            "wheel_events":sum(a["count"] for a in actions),
            "wheel_drift_max_ms":max([abs(x) for x in drift_ms],default=0),
            "actual_scroll_bottom_css":end_y,"expected_scroll_bottom_css":max_y,
            "source_output":str(source),"segment_output":str(output),
            "manifest":str(manifest_path),"film_plan":str(film_path),
            "hold_samples":hold_samples,
            "issues":sorted(set(issues)),
            "status_quality":"low_confidence" if issues else "requires_visual_review",
            **media
        }
        write_json(directory/"receipt.json",result)
        return result
    except Exception:
        try:page.close()
        except Exception:pass
        try:context.close()
        except Exception:pass
        raise

def chapter_metadata(scenes):
    lines=[";FFMETADATA1"]
    elapsed=0
    for s in scenes:
        duration=round(s["encoded_seconds"]*1000)
        title=s["title"].replace("\\","\\\\").replace("=","\\=").replace(";","\\;").replace("#","\\#").replace("\n"," ")[:90]
        lines.extend(["[CHAPTER]","TIMEBASE=1/1000",
            f"START={elapsed}",f"END={elapsed+duration}",f"title={title}"])
        elapsed+=duration
    return "\n".join(lines)+"\n"

def join_scenes(scenes,out:Path)->dict:
    if not scenes:raise ValueError("No successful page segments")
    out.mkdir(parents=True,exist_ok=True)
    listing=out/"private-concat.txt"
    # Paths are private generated paths, not user controlled
    listing.write_text("".join("file '"+str(Path(s["segment_output"]).resolve()).replace("'","'\\''")+"'\n" for s in scenes))
    raw=out/"joined-nochapters.mp4"
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
                   "-f","concat","-safe","0","-i",str(listing),
                   "-c","copy","-movflags","+faststart",str(raw)],check=True,timeout=200)
    chapters=out/"chapters.ffmeta"
    chapters.write_text(chapter_metadata(scenes))
    master=out/"master-1080p60.mp4"
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
                   "-i",str(raw),"-f","ffmetadata","-i",str(chapters),
                   "-map","0:v:0","-map_metadata","1","-c:v","copy",
                   "-movflags","+faststart",str(master)],check=True,timeout=130)
    media=probe(master)
    subprocess.run(["ffmpeg","-v","error","-xerror","-i",str(master),
                   "-f","null","-"],check=True,timeout=180)
    return {"path":str(master),"sha256":sha(master),
            "duration":float(media["format"]["duration"]),
            "source_fps_warning":"Chromium WebM input fps can be lower than 60; master is CFR resampled",
            "chapters":len(scenes),"bytes":master.stat().st_size}

def run(url,root:Path,allowed_hosts,*,scope="navigation",max_pages=3,
        profile="balanced",quality="1080",max_minutes=5,
        cursor_policy="none",auto_preview=True,preflight_only=False):
    if (urlsplit(url).hostname or "").lower() not in set(allowed_hosts):
        raise ValueError("Explicit test host allowlist required")
    validate_public_url(url)
    if quality!="1080":
        raise ValueError("This native tour proof supports only 1080p CSS capture")
    contract=TourContract(url,scope=scope,max_pages=max_pages,
                          max_minutes=max_minutes,profile=profile,
                          width=1920,height=1080)
    root.mkdir(parents=True,exist_ok=True)
    preflight=crawl_public_site(contract,allowed_hosts=tuple(allowed_hosts))
    write_json(root/"preflight.json",preflight)
    if preflight["status"]!="preflight_only" or not preflight.get("selected"):
        raise RuntimeError("Preflight did not find a valid public page")
    if preflight["limit_exceeded"]:
        raise RuntimeError("Predicted tour exceeds configured duration; reduce scope")
    print(json.dumps({"phase":"discovery","pages":len(preflight["selected"]),
        "estimate":preflight["estimated_seconds"],
        "range":preflight["estimate_range_seconds"]}),flush=True)
    if preflight_only:
        return {"status":"preflight_only","pages":preflight["selected"],
                "estimate":preflight["estimated_seconds"],"skipped":preflight["skipped"]}
    ensure_video_helper()
    scenes=[]
    errors=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=CHROME,
            args=["--no-sandbox","--disable-dev-shm-usage"])
        try:
            for index,selected in enumerate(preflight["selected"]):
                url=selected["url"]
                plan=next(p for p in preflight["timeline"] if p["url"]==url)
                started=time.monotonic()
                print(json.dumps({"phase":"capture","index":index,
                    "url":url,"plan_s":plan["duration_ms"]/1000}),flush=True)
                try:
                    report=capture_page(browser,contract,url,
                        root/safe_filename(url,index),plan,
                        cursor_policy=cursor_policy)
                    scenes.append(report)
                    print(json.dumps({"phase":"done","index":index,
                        "wall_s":round(time.monotonic()-started,2),
                        "issues":report["issues"],"source_fps":report["source_rate"]}),flush=True)
                except Exception as exc:
                    errors.append({"url":url,"reason":type(exc).__name__+":"+str(exc)[:260]})
                    print(json.dumps({"phase":"skip","index":index,"reason":errors[-1]["reason"]}),flush=True)
        finally:
            browser.close()
    if not scenes:
        raise RuntimeError("All selected page captures failed; see per-page log")
    master=join_scenes(scenes,root)
    qa=analyse_master(Path(master["path"]),root,chapters=len(scenes),
                      source_rates=[scene["source_rate"] for scene in scenes])
    quality_issues=sorted(set(
        issue for scene in scenes for issue in scene["issues"]))
    automatic_preview=None
    if auto_preview and not qa["issues"]:
        try:
            automatic_preview=automatically_direct_basic_preview(
                [Path(scene["manifest"]).parent for scene in scenes],
                root/"automatic-preview",max_seconds=30)
        except Exception as exc:
            automatic_preview={
                "schema":"sauce.basic.autodirect.v1",
                "status":"rejected_automatic_preview_error",
                "error":type(exc).__name__+":"+str(exc)[:180],
                "acceptedByAutomaticChecks":False,
                "creativeQualityVerified":False,
            }
    preview_rejected=bool(auto_preview and (
        not automatic_preview or
        not automatic_preview.get("acceptedByAutomaticChecks",False)))
    result={"schema":"sauce.basic.tour-release.v1",
        "status":("technical_reject" if qa["issues"] else
                  "automatic_preview_rejected" if preview_rejected else
                  "low_confidence_review_required" if quality_issues or errors else
                  "review_required"),
        "mode":"basic","contract":contract.manifest(),
        "selected":preflight["selected"],"skipped":preflight["skipped"]+errors,
        "source_fingerprint":preflight["source_fingerprint"],
        "chapters":preflight["chapters"],
        "recordings":[{k:v for k,v in s.items() if k!="hold_samples"} for s in scenes],
        "master":master,"qa":qa,"quality_issues":quality_issues,
        "automaticPreview":automatic_preview,
        "automaticPreviewPublicationAllowed":False,
        "limitations":["Not authorized for public user URL ingestion",
        "Requires film-level quality approval before sale",
        "60fps CFR presentation does not establish native 60fps browser capture",
        "Existing master files are private until explicitly reviewed"]}
    write_json(root/"release.json",result)
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--url",required=True)
    p.add_argument("--allow-host",action="append",required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--scope",choices=["homepage","navigation","all"],default="navigation")
    p.add_argument("--max-pages",type=int,default=3)
    p.add_argument("--max-minutes",type=int,default=5)
    p.add_argument("--profile",choices=["relaxed","balanced","quick"],default="balanced")
    p.add_argument("--quality",choices=["1080"],default="1080")
    p.add_argument("--cursor-policy",choices=["none","arrow"],default="none")
    p.add_argument("--preflight-only",action="store_true")
    p.add_argument("--skip-auto-preview",action="store_true",
                   help="Operator QA only: disable bounded automatic preview")
    p.add_argument("--experimental",action="store_true",required=True)
    a=p.parse_args()
    print(json.dumps(run(a.url,a.out,a.allow_host,scope=a.scope,
        max_pages=a.max_pages,max_minutes=a.max_minutes,profile=a.profile,
        quality=a.quality,cursor_policy=a.cursor_policy,
        auto_preview=not a.skip_auto_preview,
        preflight_only=a.preflight_only),indent=2),flush=True)

if __name__=="__main__":
    main()
