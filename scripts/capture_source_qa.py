"""Source timing and DOM evidence checks; no synthetic event or frame claims.

The visual-hash assay detects repeated pictures in an encoded CFR stream.
It cannot prove a continuously changing page refreshed at capture cadence.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from pathlib import Path


@dataclass(frozen=True)
class Geometry:
    viewport_css_width: float
    viewport_css_height: float
    dpr: float
    crop_x: float = 0
    crop_y: float = 0
    crop_width: float | None = None
    crop_height: float | None = None
    hotspot_x: float = 0
    hotspot_y: float = 0

    def validate(self):
        values = [self.viewport_css_width, self.viewport_css_height, self.dpr,
                  self.crop_x, self.crop_y, self.hotspot_x, self.hotspot_y]
        if not all(isfinite(v) for v in values) or min(values[:3]) <= 0:
            raise ValueError("Invalid viewport/DPR/geometry")
        cw = self.crop_width if self.crop_width is not None else self.viewport_css_width * self.dpr
        ch = self.crop_height if self.crop_height is not None else self.viewport_css_height * self.dpr
        if not all(isfinite(v) and v > 0 for v in (cw, ch)):
            raise ValueError("Invalid crop dimensions")
        if cw > self.viewport_css_width * self.dpr + 1 or ch > self.viewport_css_height * self.dpr + 1:
            raise ValueError("Crop exceeds physical viewport")

    def source_hotspot(self, css_x: float, css_y: float) -> tuple[float, float]:
        """Physical image coordinate of real browser-pointer hotspot."""
        self.validate()
        if not (0 <= css_x < self.viewport_css_width and 0 <= css_y < self.viewport_css_height):
            raise ValueError("Pointer outside CSS viewport")
        return (css_x * self.dpr - self.crop_x, css_y * self.dpr - self.crop_y)

    def cursor_sprite_origin(self, css_x: float, css_y: float) -> tuple[float, float]:
        x, y = self.source_hotspot(css_x, css_y)
        return (x - self.hotspot_x, y - self.hotspot_y)


def parse_framemd5(path: str | Path):
    """Return ordered (PTS seconds, checksum) from FFmpeg framemd5."""
    timebase = None
    frames = []
    for line in Path(path).read_text().splitlines():
        if line.startswith("#tb "):
            a, b = line.split(":", 1)[1].strip().split("/")
            timebase = int(a) / int(b)
        elif line and not line.startswith("#"):
            fields = [x.strip() for x in line.split(",")]
            if len(fields) < 6 or timebase is None:
                raise ValueError("Malformed framemd5 record or missing timebase")
            frames.append((int(fields[2]) * timebase, fields[-1]))
    if not frames:
        raise ValueError("No decoded frames")
    if any(b[0] <= a[0] for a, b in zip(frames, frames[1:])):
        raise ValueError("Nonmonotonic or repeated presentation timestamp")
    return frames


def clock_report(frames, nominal_fps: float, *, duplicate_limit: float = 0.25):
    if not isfinite(nominal_fps) or nominal_fps <= 0:
        raise ValueError("Invalid FPS")
    if len(frames) < 2:
        raise ValueError("Need at least two frames")
    pts = [f[0] for f in frames]
    if any(not isfinite(p) for p in pts) or any(b <= a for a, b in zip(pts, pts[1:])):
        raise ValueError("Invalid source PTS")
    duplicate_count = sum(a[1] == b[1] for a, b in zip(frames, frames[1:]))
    gap_count = sum((b-a) > 1.5 / nominal_fps for a, b in zip(pts, pts[1:]))
    ratio = duplicate_count / (len(frames)-1)
    return {"frame_count": len(frames), "encoded_fps": nominal_fps,
            "adjacent_exact_duplicates": duplicate_count,
            "duplicate_transition_fraction": round(ratio, 6),
            "distinct_frame_hashes": len({f[1] for f in frames}),
            "pts_gaps": gap_count,
            "nominal_unique_fps_unproven": bool(duplicate_count or gap_count),
            "qa_pass": ratio <= duplicate_limit and gap_count == 0,
            "limitation": "Static UI holds may legitimately repeat; checksum uniqueness is not capture refresh cadence"}


def outcome_report(events, pointer_samples, *, max_outcome_delay_s=3.0):
    """Reject invalid chronology, absent click outcomes, and impossible click targets.

    Assumes event and pointer timestamps already share one declared relative clock.
    A separate independently measured offset is required for video-frame alignment.
    """
    def monotonic(xs, name):
        ts = [float(x["t"]) for x in xs]
        if any(not isfinite(t) or t < 0 for t in ts) or any(a > b for a, b in zip(ts, ts[1:])):
            raise ValueError(name + " timeline is not monotonic")
    monotonic(events, "event")
    monotonic(pointer_samples, "pointer")
    clicks = [(i, e) for i, e in enumerate(events) if e.get("kind", e.get("type")) == "click"]
    changes = [(i, e) for i, e in enumerate(events) if e.get("kind", e.get("type")) in ("state_change", "result-revealed")]
    failures = []
    matched = 0
    for index, click in clicks:
        t = float(click["t"])
        nearest = next((change for i, change in changes if i > index and 0 <= float(change["t"])-t <= max_outcome_delay_s), None)
        if nearest is None:
            failures.append(f"click at {t:.4f}s has no verified subsequent outcome")
        else:
            matched += 1
            if not (nearest.get("evidence") or nearest.get("resultEvidence")):
                failures.append(f"outcome after {t:.4f}s lacks evidence")
        rect = click.get("targetRect") or click.get("box")
        if rect is not None:
            near = min(pointer_samples, key=lambda p: abs(float(p["t"])-t), default=None)
            if near is None or abs(float(near["t"])-t) > 0.25:
                failures.append(f"click at {t:.4f}s lacks nearby pointer sample")
            elif not (rect["x"] <= near["x"] <= rect["x"]+rect["width"] and
                      rect["y"] <= near["y"] <= rect["y"]+rect["height"]):
                failures.append(f"click at {t:.4f}s pointer outside target rectangle")
    return {"clicks": len(clicks), "matched_outcomes": matched,
            "failures": failures, "qa_pass": bool(clicks) and not failures}
