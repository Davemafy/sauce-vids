"""Reframe a verified result while keeping its center fixed across the cut."""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


@dataclass(frozen=True)
class ResultCut:
    frame: int
    matrix: np.ndarray


def plan_result_cut(events, source_size, output_size, fps, duration):
    """Return one bounded cut, or preserve the normal camera when evidence is absent."""
    width, height = source_size
    out_width, out_height = output_size
    if width * out_height != height * out_width:
        return None
    wide = out_width / width
    for index, event in enumerate(events):
        evidence = event.get("evidence")
        if event.get("kind") != "state_change" or not isinstance(evidence, str) or not evidence.strip():
            continue
        bounds = event.get("resultRect")
        if not isinstance(bounds, dict):
            continue
        try:
            observed = float(event["t"])
            x, y, w, h = (float(bounds[key]) for key in ("x", "y", "width", "height"))
        except (KeyError, TypeError, ValueError):
            continue
        if not all(map(math.isfinite, (observed, x, y, w, h))):
            continue
        # The recorded outcome must follow the most recent click.
        click = next((item for item in reversed(events[:index]) if item.get("kind") == "click"), None)
        clicked_at = click.get("t") if click else None
        if (not click or not click.get("semanticGoal") or
                not isinstance(clicked_at, (int, float)) or
                not 0 <= observed - clicked_at <= 1.8):
            continue
        if not (w > 0 and h > 0 and 0 <= x < x + w <= width and 0 <= y < y + h <= height):
            continue
        # Allow source video and DOM event clocks to settle before the cut.
        frame = math.ceil((observed + .25) * fps)
        if frame < 1 or frame / fps + 1.25 > duration:
            continue
        cx, cy = x + w / 2, y + h / 2
        # At the larger scale, retain the entire result plus a small safe margin.
        space_x = min(cx, width - cx) - width * .02
        space_y = min(cy, height - cy) - height * .02
        zoom = min(1.85, 2 * space_x / w, 2 * space_y / h)
        if zoom < 1.25:
            continue
        scale = wide * zoom
        return ResultCut(frame, np.array([
            [scale, 0., (wide - scale) * cx],
            [0., scale, (wide - scale) * cy],
        ], dtype=np.float64))
    return None
