"""Validated, source-backed storyboards for Sauce Scripted Renderer v2.

A storyboard re-edits existing SHA-verified captured UI states. It does not
claim that a hold, camera move, or caption is a new interaction.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import math
import re

from session_contract import verify_package

FPS = 60  # Exact 800 audio samples per frame at 48 kHz.
CSS_SIZE = (1280, 720)
MOTION_MAX = 0.95  # Short enough to make an action feel like a cut, not a tour.
FINAL_MIN_FRAMES = 60  # Minimum full second to read the observed result.
PRIVATE = re.compile(
    r"password|secret|(?:api|access)[_ -]?key|bearer|"
    r"(?:^|[^a-z])token(?:[^a-z]|$)|[\w.+-]+@[\w.-]+\.[a-z]{2,}", re.I
)
RECT_KEYS = ("x", "y", "width", "height")


@dataclass(frozen=True)
class Shot:
    index: int
    state: int
    action: str
    target: dict
    zoom: float
    transition_frames: int
    hold_frames: int
    caption: str
    callout: str
    hide_terminal: bool
    blur_regions: tuple[dict, ...]


def _rect(obj: dict, label: str) -> dict:
    if not isinstance(obj, dict) or any(k not in obj for k in RECT_KEYS):
        raise ValueError(f"{label}: expected explicit CSS rectangle")
    v = {k: float(obj[k]) for k in RECT_KEYS}
    if not all(math.isfinite(x) for x in v.values()):
        raise ValueError(f"{label}: non-finite coordinate")
    if v["width"] <= 0 or v["height"] <= 0:
        raise ValueError(f"{label}: empty rectangle")
    if v["x"] < 0 or v["y"] < 0 or v["x"] + v["width"] > CSS_SIZE[0] + 1 or (
        v["y"] + v["height"] > CSS_SIZE[1] + 1
    ):
        raise ValueError(f"{label}: rectangle outside verified browser viewport")
    return v


def _frames(x, name, minimum=0, maximum=20) -> int:
    if not isinstance(x, (int, float)) or not math.isfinite(x):
        raise ValueError(f"{name}: invalid duration")
    if not minimum <= x <= maximum:
        raise ValueError(f"{name}: duration out of range")
    return int(round(x * FPS))


def load_script(path: Path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != "sauce-scripted-demo-v2":
        raise ValueError("Script schema must be sauce-scripted-demo-v2")
    session_dir = Path(data["sessionDir"]).expanduser().resolve()
    # A scripted film cannot silently substitute a URL for a pinned capture.
    session_file = session_dir / "session.json"
    session = json.loads(session_file.read_text(encoding="utf-8"))
    info = verify_package(session, session_dir)
    if info["viewport"] != list(CSS_SIZE) or info["dpr"] < 2:
        raise ValueError("Source must be a verified 1280x720 capture at DPR >= 2")
    if not 2 <= len(data.get("steps", [])) <= 32:
        raise ValueError("Script requires 2–32 explicitly authored steps")
    shot_list = []
    prev_state = -1
    for i, step in enumerate(data["steps"]):
        state = step.get("state")
        if not isinstance(state, int) or not prev_state <= state < len(session["states"]):
            raise ValueError("Storyboard state references must be monotonic and verified")
        prev_state = state
        action = step.get("action")
        if action not in ("start", "approach", "click", "dialog", "inspect", "result", "final"):
            raise ValueError(f"Step {i}: unsupported action")
        # A click state must be captured following an actual recorded click.
        if action == "click" and not any(
            e.get("action") == "click" and e.get("index") == state
            for e in session.get("workflow", [])
        ):
            raise ValueError(f"Step {i}: cannot invent a click in state {state}")
        target = _rect(step.get("target"), f"step[{i}].target")
        zoom = float(step.get("zoom", 1.3))
        if not math.isfinite(zoom) or not 1.0 <= zoom <= 1.7:
            raise ValueError(f"Step {i}: camera zoom outside 1.0–1.7")
        move = _frames(step.get("moveSeconds", 0), "moveSeconds", 0, MOTION_MAX)
        hold = _frames(step.get("holdSeconds", 1), "holdSeconds", 0.1, 10)
        caption = str(step.get("caption", ""))
        callout = str(step.get("callout", ""))
        if any(len(s) > cap or PRIVATE.search(s) for s, cap in (
            (caption, 105), (callout, 44)
        )):
            raise ValueError(f"Step {i}: private or oversized editorial overlay")
        blur_regions = tuple(_rect(r, "blurRegion") for r in step.get("blurRegions", []))
        if step.get("blurSelectors"):
            raise ValueError(
                "Selector redactions must be resolved in a live Chromium capture; "
                "never guess DOM locations from saved image pixels"
            )
        conceal = bool(step.get("hideTerminalWhenModal", False))
        # The real terminal is an observed element in this verified trace.
        # Presentation-only concealment is permitted even during the opening;
        # this prevents a truncated dark panel from intruding into a crop.
        shot_list.append(Shot(i, state, action, target, zoom, move, hold,
                              caption, callout, conceal, blur_regions))
    if shot_list[-1].action != "final" or shot_list[-1].hold_frames < FINAL_MIN_FRAMES:
        raise ValueError("Final observed state must hold fully sharp for >=1.0 second")
    if shot_list[0].action != "start" or shot_list[0].transition_frames:
        raise ValueError("Opening starts already framed on the first verified action")
    duration_frames = sum(s.transition_frames + s.hold_frames for s in shot_list)
    if duration_frames > 120 * FPS:
        raise ValueError("Script exceeds two-minute guarded demonstration limit")
    return session_dir, session, shot_list, duration_frames
