"""Compile a source-bound, event-relative camera edit into timed keyframes."""
from __future__ import annotations

import math
from dataclasses import dataclass

SCHEMA = "sauce-live-edit-v1"


def _object(value, keys, name):
    if not isinstance(value, dict) or value.keys() != set(keys):
        raise ValueError(f"{name} must contain exactly {', '.join(keys)}")
    return value


def _number(value, low, high, name):
    if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"{name} must be between {low} and {high}")
    return value


@dataclass(frozen=True)
class LiveEditPlan:
    lead: float
    hold: float
    camera: tuple
    cursor_scale: float
    audio: str

    def camera_timeline(self, result_time, duration, fit):
        return compile_camera(self.camera, result_time, duration, fit)


def compile_camera(camera, result_time, duration, fit):
    """Resolve semantic time and zoom against the measured capture."""
    keys = []
    for basis, offset, zoom in camera:
        at = offset + (result_time if basis == "result" else 0.)
        zoom = fit if zoom == "fit" else zoom
        if zoom > fit + 1e-9:
            raise ValueError(f"Requested zoom {zoom:g} exceeds measured action/result fit {fit:.3f}")
        if at < 0 or at > duration or (keys and at <= keys[-1][0]):
            raise ValueError("Camera times must increase and stay inside the clip")
        if keys and zoom != keys[-1][1] and keys[-1][0] < result_time - 1e-9:
            raise ValueError("Camera changes must begin at or after the observed result")
        keys.append((at, zoom))
    # A duplicate hold marker on the exclusive endpoint adds no visible frame.
    if len(keys) > 1 and math.isclose(keys[-1][0], duration, abs_tol=1e-9):
        if keys[-1][1] != keys[-2][1]:
            raise ValueError("Camera move ends outside the last visible frame")
        keys.pop()
    return tuple(keys)


def parse_live_edit(raw, receipt):
    plan = _object(raw, ("schema", "source_sha256", "event", "trim", "camera", "audio"), "plan")
    if plan["schema"] != SCHEMA:
        raise ValueError("Unsupported edit-plan schema")
    if not isinstance(plan["source_sha256"], str) or plan["source_sha256"] != receipt.get("sha256"):
        raise ValueError("Edit plan references a different capture")
    events = receipt.get("editorial_events", [])
    if (plan["event"] != "slider_change" or receipt.get("cursorless") is not True
            or sum(e.get("kind") == plan["event"] for e in events) != 1):
        raise ValueError("This edit needs exactly one verified cursorless slider result")
    trim = _object(plan["trim"], ("lead_seconds", "hold_seconds"), "trim")
    lead = _number(trim["lead_seconds"], .25, 4., "lead_seconds")
    hold = _number(trim["hold_seconds"], .8, 7., "hold_seconds")
    camera = _object(plan["camera"], ("anchor", "cursor_scale", "keys"), "camera")
    if camera["anchor"] != "action-and-result":
        raise ValueError("Camera anchor must be the observed action and result")
    scale = _number(camera["cursor_scale"], .55, 1.1, "cursor_scale")
    if not isinstance(camera["keys"], list) or not 1 <= len(camera["keys"]) <= 12:
        raise ValueError("An edit needs 1 to 12 camera keys")
    keys = []
    for raw_key in camera["keys"]:
        key = _object(raw_key, ("at", "offset_seconds", "zoom"), "camera key")
        if key["at"] not in ("clip_start", "result"):
            raise ValueError("Camera time anchor must be clip_start or result")
        offset = _number(key["offset_seconds"], 0., 11., "camera offset_seconds")
        zoom = key["zoom"]
        if zoom != "fit":
            zoom = _number(zoom, 1., 2.55, "camera zoom")
        keys.append((key["at"], offset, zoom))
    if keys[0][:2] != ("clip_start", 0.):
        raise ValueError("First camera key must establish the opening frame")
    if plan["audio"] not in ("auto", "clean", "narrated"):
        raise ValueError("Unknown audio choice")
    return LiveEditPlan(lead, hold, tuple(keys), scale, plan["audio"])


def sample_zoom(t, keys, ease):
    previous = keys[0]
    for current in keys[1:]:
        if t < current[0]:
            progress = ease((t - previous[0]) / (current[0] - previous[0]))
            return previous[1] + (current[1] - previous[1]) * progress
        previous = current
    return previous[1]
