"""Source-backed editorial rejection and bounded repair for Sauce EDL films.

A score here is NOT a premium-design score. It detects objective editorial
failures before expensive decoding: future-state teaser openers, unestablished
first frames, actions absent from a purported demo, and off-evidence camera
anchors. It can safely remove a nonchronological teaser; it never fabricates
frames, retimes events or invents product results.
"""
from __future__ import annotations

from copy import deepcopy
import math

FPS = 60
OPENER_ZOOM_LIMIT = 1.36
LAST_HOLD_MIN_FRAMES = 48


def _source_frame(event, lead):
    return round((float(event["t"]) + lead) * FPS)


def _pose_anchor_verified(manifest, anchor, source_frame):
    if anchor == "wide":
        return True
    pieces = anchor.split(":")
    if len(pieces) != 2 or pieces[0] not in ("result", "detail", "summary", "overview"):
        return False
    try:
        index = int(pieces[1])
    except ValueError:
        return False
    events = [e for e in manifest.get("events", [])
              if isinstance(e, dict) and e.get("kind") == "state_change"]
    if not 0 <= index < len(events):
        return False
    e = events[index]
    if not isinstance(e.get("evidence"), str) or not e["evidence"].strip():
        return False
    # A camera can focus an observed, *existing* result only after the
    # source actually contains it. Two frames' allowance for capture clocks.
    return source_frame + 2 >= _source_frame(e, float(manifest.get("lead_s", 0)))


def _group_fits_frame(manifest, anchor, zoom):
    """Only claims complete coverage when every source card is visible."""
    try:
        kind, number = anchor.split(":")
        if kind != "overview":
            return True
        state=[e for e in manifest["events"] if e.get("kind")=="state_change"][int(number)]
        boxes=state["summaryRects"]
        sw=float(manifest["capture_rect"]["width"])
        sh=float(manifest["capture_rect"]["height"])
        from evidence_edl_renderer import pose
        cx,cy=pose(manifest,anchor,(sw,sh))
        scale=max(1920/sw,1080/sh)*float(zoom)
        halfw=1920/(2*scale)
        halfh=1080/(2*scale)
        cx=min(sw-halfw,max(halfw,cx))
        cy=min(sh-halfh,max(halfh,cy))
        viewport=(cx-halfw,cy-halfh,cx+halfw,cy+halfh)
        # Two source pixels of safety for interpolation and rounded cards.
        return all(b["x"]>=viewport[0]+2 and b["y"]>=viewport[1]+2
                   and b["x"]+b["width"]<=viewport[2]-2
                   and b["y"]+b["height"]<=viewport[3]-2 for b in boxes)
    except (KeyError,ValueError,TypeError,IndexError,ZeroDivisionError):
        return False


def _last_motion_end(keys):
    # Repeated identical camera poses are holds, not motion.
    last = keys[-1]
    for previous in reversed(keys[:-1]):
        if previous["zoom"] != last["zoom"] or previous["anchor"] != last["anchor"]:
            return last["f"]
        last = previous
    return 0


def inspect_editorial(manifest, edit):
    """Machine-readable findings for a candidate *already admitted* by build().

    Blockers are deterministic truth/composition failures. Warnings are
    mechanical risk factors; human review of the encoded film remains required.
    """
    shots = edit["shots"]
    lead = float(manifest.get("lead_s", 0))
    findings = []
    def note(level, code, shot, detail):
        findings.append({"level": level, "code": code, "shot": shot, "detail": detail})

    if shots[0]["startFrame"] > shots[1]["startFrame"]:
        note("reject", "NONCHRONOLOGICAL_OPENER", 0,
             "A future product result is shown before the viewer sees the product context")
    initial = shots[0]["camera"][0]
    if initial["anchor"] != "wide" or float(initial["zoom"]) > OPENER_ZOOM_LIMIT:
        note("reject", "NO_ESTABLISHING_SHOT", 0,
             "The first frame is cropped too far to identify the real product")

    clicks = [e for e in manifest.get("events", [])
              if isinstance(e, dict) and e.get("kind") == "click"
              and isinstance(e.get("semanticGoal"), str) and e["semanticGoal"].strip()
              and "t" in e]
    present = [e for e in clicks
               if any(s["startFrame"] <= _source_frame(e, lead) < s["endFrame"]
                      for s in shots)]
    if len(present) < 2:
        note("reject", "NO_DEMONSTRATED_WORKFLOW", -1,
             "The edit contains fewer than two recorded semantic actions")

    for i,s in enumerate(shots):
        for k in s["camera"]:
            if not _pose_anchor_verified(manifest, k["anchor"],
                                          s["startFrame"]+k["f"]):
                note("reject", "UNOBSERVED_CAMERA_TARGET", i,
                     "Camera moves toward a product result before its source evidence exists")
            if k["anchor"].startswith("overview:") and not _group_fits_frame(
                    manifest,k["anchor"],k["zoom"]):
                note("reject", "CLIPPED_VERIFIED_SUMMARY_GROUP", i,
                     "The camera cannot display all measured result cards together")
        first=s["camera"][0]
        if i and (float(first["zoom"]) > 1.6 or first["anchor"] != "wide"):
            note("warn", "DISORIENTING_CUT_IN", i,
                 "Cut begins too close; allow the viewer to re-establish source context")
        if i == len(shots)-1 and len(s["camera"]) >= 2:
            if s["endFrame"]-s["startFrame"]-_last_motion_end(s["camera"]) < LAST_HOLD_MIN_FRAMES:
                note("warn", "NO_FINAL_READING_HOLD", i,
                     "The last camera move ends too close to the final film frame")
    return findings


def bounded_repair(manifest, edit):
    """Remove only a future-result teaser when the remaining film is valid.

    If other failures remain, stop with findings: never invent transitions,
    rewrite authentic clicks, or silently scale away a visual defect.
    """
    result = deepcopy(edit)
    notes=[]
    shots=result.get("shots",[])
    if len(shots)>=4 and shots[0]["startFrame"]>shots[1]["startFrame"]:
        keep=sum(s["endFrame"]-s["startFrame"] for s in shots[1:])
        if keep>=7*FPS and len(shots[1:])>=3:
            result["shots"]=shots[1:]
            notes.append({"action":"drop_future_teaser",
                          "removedSourceFrames":[shots[0]["startFrame"],
                                                 shots[0]["endFrame"]],
                          "reason":"First frame must establish an actual action"})
    return result, notes, inspect_editorial(manifest, result)
