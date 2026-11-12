"""One URL -> observed site -> defensible shots -> actual edited MP4.

A conservative offline director: heuristics choose safe public-page content,
Hermes may improve decisions by inspecting the evidence and rerunning a plan.
This module never fabricates product UI, interactions, or visual judgments.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import re
from urllib.parse import urlsplit

from . import director, tools

BLOCKLIST = re.compile(
    r"\b(login|log in|sign in|sign up|pricing|billing|checkout|subscribe|faq|trial|"
    r"buy|delete|logout|log out|account|terms|privacy|legal|cookie)\b", re.I
)
FOOTER = re.compile(r"\b(footer|contact us|newsletter|legal|copyright)\b", re.I)


def select_actions(observed: dict, target_seconds: float) -> list[dict]:
    """Choose verified scroll targets, never invent a selector or action."""
    if not isinstance(observed, dict):
        raise ValueError("Invalid scout observations")
    headings = observed.get("headings", [])
    if not isinstance(headings, list):
        raise ValueError("Invalid heading observations")
    actions = [{"type": "wait", "seconds": min(3.0, max(2.2, target_seconds/8))}]
    page_height = max(900.0, float(observed.get("document_height", 900)))
    candidates = []
    seen = set()
    for item in headings:
        if not isinstance(item, dict):
            continue
        text = item.get("text", "").strip()
        selector = item.get("selector")
        y = item.get("document_y")
        if not isinstance(y, (int, float)) or not math.isfinite(y):
            continue
        section_title = str(item.get("section_title", ""))
        if (not isinstance(text, str) or not 5 <= len(text) <= 105
            or not isinstance(selector, str) or len(selector) > 150
            or not selector or FOOTER.search(text) or BLOCKLIST.search(text)
            or BLOCKLIST.search(section_title)
            or text.endswith("?") or section_title.lower().startswith("faq")
            or item.get("tag") not in ("H1", "H2", "H3")):
            continue
        y = float(y)
        # Initial hero is already shown in the opening scene.
        if y < 480 or y > page_height - 50:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        candidates.append({"text": text, "selector": selector, "y": y,
                           "tag": item["tag"],
                           "x": float(item.get("center_x", 720)),
                           "media_x": item.get("media_center_x")})
    candidates.sort(key=lambda c: c["y"])
    feature_headings = [item for item in candidates if item["tag"] == "H3"]
    if len(feature_headings) >= 4:
        # A clustered sequence of feature cards usually shows the actual
        # interface better than a distant generic closing/value statement.
        candidates = feature_headings

    max_actions = min(8, max(2, int((target_seconds - 3.0) / 2.3)))
    # Reduce coverage evenly across the document, rather than choosing the first
    # cluster of marketing headings or a repetitive series of H3 features.
    if len(candidates) > max_actions:
        picks = [round(i * (len(candidates)-1) / (max_actions-1))
                 for i in range(max_actions)]
        candidates = [candidates[i] for i in picks]
    dwell = min(3.0,max(2.25,(target_seconds-3.5)/max(1,len(candidates))))
    for item in candidates:
        action={"type": "focus", "selector": item["selector"],
                "label": item["text"][:100], "seconds": dwell}
        if (isinstance(item.get("media_x"),(int,float))
            and 100 <= item["media_x"] <= 1340):
            action["camera_x"]=item["media_x"]
        actions.append(action)

    if len(candidates) < 2 and page_height > 1600:
        # Fallback for pages with few semantic headings: real scrolling only.
        for _ in range(min(4, max(1, int((page_height-900) / 850)))):
            actions.append({"type": "scroll", "pixels": 850, "seconds": 2.0})
    # Interactions with tabs are safe only if the DOM explicitly identifies them.
    for item in observed.get("controls", []):
        if len(actions) >= max_actions + 1:
            break
        if (isinstance(item, dict) and item.get("type") == "click_tab"
            and isinstance(item.get("selector"), str)
            and 0 < len(item["selector"]) <= 150
            and not BLOCKLIST.search(item.get("label", ""))):
            actions.append({"type": "click_tab", "selector": item["selector"],
                            "label": str(item.get("label", "Tab"))[:100],
                            "seconds": 1.8})
            break
    return tools._check_actions(actions)


def make_shots(events: list[dict], source_duration: float,
               target_seconds: float) -> list[dict]:
    """Cut around actual completed browser actions. Never fabricate timestamps."""
    if not events or source_duration < 1:
        raise ValueError("No meaningful recorded footage")
    result = []
    for event in events:
        if event.get("type") == "page":
            continue
        event_end = event.get("time")
        event_start = event.get("start_time")
        if not all(isinstance(t,(int,float)) and math.isfinite(t)
                   for t in (event_end, event_start)):
            continue
        if event_end <= event_start:
            continue
        mode = event["type"]
        if mode == "wait":
            start = event_start + 0.08
        else:
            # Avoid capturing the scroll's initial layout jump. Keep some
            # arrival motion where it improves orientation.
            start = event_start + min(0.38, (event_end-event_start)*0.2)
        end = min(event_end - 0.08, source_duration-0.05)
        if result:
            start = max(start, result[-1]["end_s"]+0.02)
        if end-start < 0.5:
            continue
        title = event.get("label") or ("Overview" if mode=="wait" else mode.replace("_"," ").title())
        pos = event.get("position") or {}
        fx = max(0.1,min(0.9,float(pos.get("x",720))/1440))
        fy = max(0.1,min(0.9,float(pos.get("y",450))/900))
        zoom = 1.0 if mode=="wait" else (1.18 if event.get("media_guided") else 1.08)
        result.append({"start_s":round(start,3), "end_s":round(end,3),
                       "zoom":zoom,"focus_x":round(fx,3),"focus_y":round(fy,3),
                       "label":str(title)[:120]})
    if not result:
        end=min(float(source_duration), float(target_seconds), 20)
        result=[{"start_s":0.15,"end_s":end,"zoom":1.0,
                 "focus_x":0.5,"focus_y":0.5,"label":"Overview"}]
    # Allocate time across ALL observed sections. Truncating the tail drops
    # key product features when smooth scrolling takes longer than expected.
    total = sum(s["end_s"]-s["start_s"] for s in result)
    if total <= target_seconds:
        return result
    if len(result) == 1:
        first=result[0]
        return [{**first,"end_s":round(min(first["end_s"],first["start_s"]+target_seconds),3)}]
    first=result[0]
    opening=min(first["end_s"]-first["start_s"],
                max(1.6,min(2.5,target_seconds*0.13)))
    remaining=max(0,target_seconds-opening)
    others=result[1:]
    budget=remaining/len(others)
    selected=[{**first,"end_s":round(first["start_s"]+opening,3)}]
    for shot in others:
        # Keep the latest stable portion after the verified scroll settles.
        cut=min(shot["end_s"]-shot["start_s"],budget)
        if cut < 0.55:
            continue
        selected.append({**shot,"start_s":round(shot["end_s"]-cut,3)})
    return selected


def run(args: dict, **kwargs) -> str:
    """Autonomous first cut. One call, no invented clicks, no claims of aesthetic QA."""
    stage = "validate"
    try:
        url = args.get("url")
        project = tools._id(args.get("project", "demo"))
        tools._url(url)
        seconds = float(args.get("duration_seconds", 20))
        if not math.isfinite(seconds) or not 8 <= seconds <= 30:
            raise ValueError("duration_seconds must be 8–30")
        music = args.get("music_asset")
        background = args.get("background_asset")
        # Validate filenames before spending resources on capture.
        if music:
            director._asset(music,{".mp3",".wav",".ogg",".m4a"})
        if background:
            director._asset(background,{".png",".jpg",".jpeg"})

        stage = "scout"
        scouting = json.loads(director.scout({"url":url,"project":project}))
        if not scouting.get("ok"):
            raise RuntimeError("Site scout failed: "+str(scouting.get("error", "unknown")))
        actions = select_actions(scouting, seconds)
        stage = "capture"
        recording = json.loads(tools.capture({"url":url,"project":project,
                                              "actions":actions}))
        if not recording.get("ok"):
            raise RuntimeError("Browser capture failed: "+str(recording.get("error", "unknown")))
        run_id = recording["run_id"]
        folder = tools._dir(run_id)
        media_duration = director._duration(folder/"recording.webm")
        stage = "plan"
        shots = make_shots(recording["events"],media_duration,seconds)
        planned = json.loads(director.plan({"run_id":run_id,"shots":shots}))
        if not planned.get("ok"):
            raise RuntimeError("Editing plan failed: "+str(planned.get("error", "unknown")))
        stage = "render"
        rendered = json.loads(tools.render({"run_id":run_id,"use_edit_plan":True,
                                             "music_asset":music,
                                             "background_asset":background}))
        if not rendered.get("ok"):
            raise RuntimeError("Video render failed: "+str(rendered.get("error", "unknown")))
        stage = "review"
        review = json.loads(director.review({"run_id":run_id}))
        if not review.get("ok"):
            raise RuntimeError("Video review failed: "+str(review.get("error", "unknown")))
        metadata = json.loads(tools.inspect({"run_id":run_id}))
        if not metadata.get("ok"):
            raise RuntimeError("Metadata check failed: "+str(metadata.get("error", "unknown")))
        outputs = metadata.get("video_metadata",{}).get("streams",[])
        videos = [s for s in outputs if s.get("codec_type")=="video"]
        video_ok = bool(videos and videos[0].get("width")==1920
                        and videos[0].get("height")==1080)
        black = review.get("black_intervals",[])
        # Black frames / wrong output dimensions are an objective quality failure.
        passed = video_ok and not black and review["duration_s"] >= min(8,seconds*0.58)
        result = {
            "ok": passed, "run_id":run_id,
            "video":rendered["video"], "edit_plan":planned["edit_plan"],
            "capture_receipt":str(folder/"capture.json"),
            "scout_receipt":scouting["scout_id"],
            "review_receipt":str(folder/"review.json"),
            "review_frames":review["frames"],
            "duration_s":review["duration_s"],
            "requested_duration_s":seconds,
            "observed_actions":len(recording["events"])-1,
            "shots":len(planned["shots"]),
            "objective_quality_checks":{"full_hd":video_ok,
                                       "no_black_segments":not bool(black),
                                       "duration_sufficient":review["duration_s"] >= min(8,seconds*0.58)},
            "visual_art_direction_verified":False,
            "notes":"Real public-page footage only. Human or Hermes vision review is still needed for artistic quality."
        }
        (folder/"auto-report.json").write_text(json.dumps(result,indent=2))
        return json.dumps(result)
    except Exception as exc:
        return json.dumps({"ok":False,"stage":stage,"error":str(exc)[:800]})
