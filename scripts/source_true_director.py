"""Conservative reference-backed automatic storyboard for stable real UI footage.

Supports an evidence pattern with three genuine clicks, three verified DOM
outcomes, and three browser remount discontinuities. Other shapes fail
closed rather than producing a bad generic film. It does not run an LLM,
construct fake scenes, or invent pointer movement or state transitions.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

import numpy as np

from cinematic_recorded_pointer import (
    CinematicRecordedPointer, pointer_visibility_report
)
from editorial_quality_gate import inspect_editorial
from evidence_edl_renderer import build, camera, pose
from recorded_pointer import pointer_track

FPS = 60
SUPPORTED_CLICKS = 3
LAST_RESULT_HOLD_FRAMES = 264
STAGE_SCALE = .86


def source_frame(t: float, lead: float) -> int:
    if not isinstance(t, (int, float)) or not math.isfinite(t):
        raise ValueError("Nonfinite source-clock event")
    return round((t + lead) * FPS)


def _keys(length: int, focus: str | None, zoom: float,
          *, final: bool = False, has_group: bool = False) -> list[dict]:
    def key(f, z, a):
        return {"f": int(f), "zoom": float(z), "anchor": a}
    if focus is None:
        return [key(0, 1.06, "wide"), key(length - 1, 1.06, "wide")]
    if final:
        if has_group:
            # First establish the observed KPI, then release to the entire
            # measured KPI group. No metric is cropped in the reading hold.
            return [
                key(0, 1.08, "wide"),
                key(round(.067 * (length - 1)), 1.08, "wide"),
                key(round(.238 * (length - 1)), zoom, focus),
                key(round(.487 * (length - 1)), zoom, focus),
                key(round(.676 * (length - 1)), 1.12, "overview:2"),
                key(length - 1, 1.12, "overview:2"),
            ]
        return [key(0, 1.07, "wide"),
                key(round(.22 * (length - 1)), zoom, focus),
                key(round(.58 * (length - 1)), zoom, focus),
                key(round(.74 * (length - 1)), 1.10, "wide"),
                key(length - 1, 1.10, "wide")]
    if length < 110:
        raise ValueError("Short captured result cannot receive full camera grammar")
    return [
        key(0, 1.06, "wide"),
        key(round(.18 * (length - 1)), zoom, focus),
        key(round(.49 * (length - 1)), zoom, focus),
        key(round(.69 * (length - 1)), 1.12, "wide"),
        key(length - 1, 1.12, "wide"),
    ]


def _focus_kind(event: dict) -> str:
    evidence = event.get("evidence")
    if not isinstance(evidence, str) or not evidence.strip():
        raise ValueError("Missing real observed outcome")
    lowered = evidence.lower()
    if isinstance(event.get("summaryRects"), list) and len(event["summaryRects"]) >= 2:
        return "group"
    # Current destination wins over the origin mentioned in a transition
    # receipt such as "from code diff to agent task columns".
    if any(word in lowered for word in ("columns", "tasks", "board")):
        return "board"
    if any(word in lowered for word in
           ("code", "diff", "source file", ".tsx", ".ts ", ".py ", "editor")):
        return "code"
    return "other"


def _validate_clicks(manifest: dict, clicks: list[dict], track: np.ndarray):
    for event in clicks:
        target = event.get("targetRect")
        if not isinstance(target, dict):
            raise ValueError("Cannot direct an unverified click location")
        px, py = (
            float(np.interp(event["t"], track[:, 0], track[:, k]))
            for k in (1, 2)
        )
        try:
            x, y, w, h = (float(target[k])
                          for k in ("x", "y", "width", "height"))
        except (KeyError, ValueError, TypeError) as exc:
            raise ValueError("Invalid recorded click target") from exc
        if not all(math.isfinite(v) for v in (x, y, w, h)):
            raise ValueError("Nonfinite actual click geometry")
        if w <= 0 or h <= 0 or not x - 4 <= px <= x + w + 4 or not y - 4 <= py <= y + h + 4:
            raise ValueError("Cursor hotspot disagrees with captured target")


def create_directed_edl(manifest: dict, receipt: dict, *,
                        output_size=(1920, 1080), stage_scale=STAGE_SCALE):
    if receipt.get("schema") != "sauce-source-instability-v1":
        raise ValueError("Source instability must come from verified decoded video")
    if receipt.get("sourceSha256") != manifest.get("source_sha256"):
        raise ValueError("Capture and continuity receipt hashes disagree")
    sw, sh = int(receipt["sourceWidth"]), int(receipt["sourceHeight"])
    if (manifest.get("cursorless") is not True or
        manifest.get("capture_rect", {}).get("width") != sw or
        manifest.get("capture_rect", {}).get("height") != sh or
        receipt.get("fps") != FPS):
        raise ValueError("Source dimensions or pointer-capture contract mismatched")
    lead = float(manifest["lead_s"])
    clicks = [e for e in manifest["events"] if e.get("kind") == "click"]
    outcomes = [e for e in manifest["events"] if e.get("kind") == "state_change"
                and isinstance(e.get("evidence"), str) and e["evidence"].strip()]
    if len(clicks) != SUPPORTED_CLICKS or len(outcomes) != SUPPORTED_CLICKS:
        raise ValueError("This bounded director requires three verified click/outcome pairs")
    track = pointer_track(manifest, sw, sh)
    if track is None:
        raise ValueError("Cannot direct without authentic monotonic pointer samples")
    _validate_clicks(manifest, clicks, track)

    spans = [tuple(s) for s in receipt["stableSegments"]]
    # This style needs N+1 stable spans separated by N real remounts.
    # Other flows need a different proven editorial grammar, not this template.
    if len(spans) != SUPPORTED_CLICKS + 1:
        raise ValueError("Cannot safely plan an unknown source continuity shape")
    if any(a >= b or b - a < 70 for a, b in spans):
        raise ValueError("Observed source states too short for a readable product film")
    first_pointer = math.ceil((float(track[0, 0]) + lead) * FPS)
    start = max(spans[0][0], first_pointer, source_frame(clicks[0]["t"], lead)-100)
    limits = [(start, spans[0][1]), spans[1], spans[2]]
    final_end = min(spans[-1][1], source_frame(outcomes[-1]["t"], lead)
                    + LAST_RESULT_HOLD_FRAMES)
    limits.append((spans[-1][0], final_end))

    for index, click in enumerate(clicks):
        at = source_frame(click["t"], lead)
        changed = source_frame(outcomes[index]["t"], lead)
        if not (click["t"] < outcomes[index]["t"] and
                limits[index][0] <= at < limits[index][1] and
                limits[index+1][0] <= changed < limits[index+1][1]):
            raise ValueError("Source timeline does not prove causal action-to-result order")
    shots = []
    def add(label, lo, hi, keys):
        shots.append({"label": label, "startFrame": int(lo),
                      "endFrame": int(hi), "camera": keys})
    a,b=limits[0]
    add("Observed product and "+str(clicks[0].get("label","recorded action")),
        a,b,_keys(b-a,None,1.06))
    for index in (1,2,3):
        a,b=limits[index]
        event=outcomes[index-1]
        category=_focus_kind(event)
        selector=("result-upper" if category=="code" else "result")+f":{index-1}"
        zoom={"code":1.60,"board":1.49,"group":1.50,"other":1.36}[category]
        name="Observed "+str(event["evidence"])[:90]
        add(name,a,b,_keys(b-a,selector,zoom,final=index==3,
                            has_group=category=="group"))

    edit={
        "reference": "Real-source temporal continuity + verified DOM result grammar",
        "purpose": "Automatically selected stable browser footage; review required",
        "unstableRanges": receipt["unstableRanges"],
        "autoDirected": {"schema":"sauce-bounded-director-v1",
                         "sourceSha256":receipt["sourceSha256"],
                         "actualClicks":len(clicks),
                         "actualResults":len(outcomes),
                         "manualShotSelection":False},
        "shots":shots
    }
    pointer=CinematicRecordedPointer(track,[e["t"] for e in clicks])
    for candidate in range(9):
        # Readability first; reduce only zoom strength for violating shots.
        built,total=build(manifest,edit,(sw,sh),int(receipt["decodedFrames"]))
        findings=inspect_editorial(manifest,edit)
        blockers=[f for f in findings if f["level"]=="reject"]
        visibility=pointer_visibility_report(
            pointer,built,manifest,(sw,sh),output_size,camera,stage_scale)
        if not blockers and not visibility["offscreenFrames"] and not visibility["unrecordedOpeningFrames"]:
            if total > 20*FPS:
                raise ValueError("Automatic film exceeds 20-second bounded review")
            return edit,{"schema":"sauce-auto-direction-evidence-v1",
                         "frames":total,"fps":FPS,
                         "sourceSha256":receipt["sourceSha256"],
                         "cursorVisibility":visibility,
                         "qualityFindings":findings,
                         "zoomAdjustments":candidate,
                         "creativeApproved":False}
        adjusted=False
        bad_indices={f.get("shot") for f in blockers if f.get("shot",-1)>0}
        bad_indices.update(visibility["offscreenByShotIndex"])
        for idx in bad_indices:
            if not isinstance(idx,int) or not 1<=idx<=3:
                continue
            for key in edit["shots"][idx]["camera"]:
                if key["anchor"]!="wide" and key["zoom"]>1.13:
                    key["zoom"]=max(1.12,round(key["zoom"]-.09,2))
                    adjusted=True
        if not adjusted:
            raise ValueError("Cannot keep authentic pointer and verified result visible")
    raise ValueError("Bounded camera corrections exhausted")


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest",type=Path,required=True)
    ap.add_argument("--continuity",type=Path,required=True)
    ap.add_argument("--out-edl",type=Path,required=True)
    ap.add_argument("--out-report",type=Path,required=True)
    a=ap.parse_args()
    m=json.loads(a.manifest.read_text())
    r=json.loads(a.continuity.read_text())
    edl,report=create_directed_edl(m,r)
    for path,body in ((a.out_edl,edl),(a.out_report,report)):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(body,indent=2)+"\n")
    print(json.dumps({"frames":report["frames"],"cursor":report["cursorVisibility"],
                      "source":"verified", "creativeApproved":False}))


if __name__=="__main__":
    main()
