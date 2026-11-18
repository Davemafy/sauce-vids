"""Deterministic, source-timed water refraction on real recorded pointer presses.

This function does not invent UI states or mouse events. It remaps an isolated
ROI of the already-composited BGR film; the cursor is painted afterward.
"""
from __future__ import annotations

import math

import cv2
import numpy as np

LIFETIME_S = 0.56
SPEED_PX_S = 490.0
MAX_DISPLACEMENT_PX = 10.5


def apply_click_water_ripple(
    stage: np.ndarray, center: tuple[float, float], age_s: float,
    *, intensity: float = 1.0, lifetime_s: float = LIFETIME_S,
    protected_quad: np.ndarray | None = None
) -> bool:
    """Refract stage in-place; return whether a visible wave was sampled.

    The advancing wavefront is a finite-width damped oscillation. Its back
    edge recovers exact source pixels after it passes, leaving text sharp and
    the page unmodified. No fake rings or screen-space click positions.
    """
    if (stage.ndim != 3 or stage.shape[2] != 3 or stage.dtype != np.uint8):
        raise ValueError("Expected a uint8 BGR film frame")
    if not (isinstance(age_s, (int, float)) and math.isfinite(age_s)
            and 0.0 <= age_s < lifetime_s):
        return False
    try:
        cx, cy = (float(v) for v in center)
    except (TypeError, ValueError, OverflowError):
        return False
    if not (math.isfinite(cx) and math.isfinite(cy)):
        return False
    if not (math.isfinite(intensity) and 0 <= intensity <= 1.0
            and 0.05 <= lifetime_s <= LIFETIME_S):
        raise ValueError("Invalid bounded ripple strength or lifetime")
    h, w = stage.shape[:2]
    if not (0 <= cx < w and 0 <= cy < h):
        return False

    # Smooth launch and terminal damping; at 60 fps never a one-frame pop.
    head = SPEED_PX_S * age_s
    envelope = min(1.0, age_s / 0.065) ** 2
    tail = max(0.0, (lifetime_s - age_s) / min(0.17, lifetime_s * 0.50))
    envelope *= min(1.0, tail) ** 2 * math.exp(-1.35 * age_s)
    if envelope < 0.0001:
        return False

    # 35 px wave band with a trailing echo. Bounds stay local as the front grows.
    reach = head + 67.0
    x0 = max(0, int(math.floor(cx - reach)))
    y0 = max(0, int(math.floor(cy - reach)))
    x1 = min(w, int(math.ceil(cx + reach + 1)))
    y1 = min(h, int(math.ceil(cy + reach + 1)))
    if x1 <= x0 or y1 <= y0:
        return False

    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dx, dy = xx - cx, yy - cy
    radius = np.hypot(dx, dy)
    delta = radius - head
    ring = np.exp(-0.5 * (delta / 23.0) ** 2)
    echo = np.exp(-0.5 * ((delta + 45.0) / 24.0) ** 2)
    travel = (ring * np.sin(delta * (math.pi / 30.0))
              + 0.30 * echo * np.sin((delta + 45.0) * (math.pi / 30.0)))
    displacement = (MAX_DISPLACEMENT_PX * intensity * envelope) * travel
    unit = 1.0 / np.maximum(radius, 1.0)
    map_x = np.asarray(xx - dx * unit * displacement, dtype=np.float32)
    map_y = np.asarray(yy - dy * unit * displacement, dtype=np.float32)

    roi = stage[y0:y1, x0:x1]
    sampled = cv2.remap(
        stage, map_x, map_y, cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )
    # Low-strength bright/dark refraction at the wavefront, not neon rings.
    caustic = (1.0 + 0.032 * intensity * envelope * ring
               * np.cos(delta * math.pi / 30.0)).astype(np.float32)
    # A blackbox remap can round even unchanged samples. Explicitly preserve
    # exact source bytes everywhere outside the physically active waveband.
    active = (((np.abs(delta) < 58.0) | (np.abs(delta + 45.0) < 42.0))
              & ((np.abs(displacement) > 0.12)
                 | (np.abs(caustic - 1.0) > 0.004)))
    if protected_quad is not None:
        # Exact projected occlusion: do not bend an actual elevated dialog
        # through a wave emitted on the browser plane behind it.
        quad = np.asarray(protected_quad, dtype=np.float32)
        if quad.shape != (4, 2) or not np.isfinite(quad).all():
            raise ValueError("Expected a finite projected modal quadrilateral")
        matte = np.zeros(active.shape, np.uint8)
        relative = np.rint(quad - [x0, y0]).astype(np.int32)
        cv2.fillConvexPoly(matte, relative, 255, lineType=cv2.LINE_AA)
        active &= matte == 0
    if not np.any(active):
        return False
    distorted = np.uint8(np.clip(sampled.astype(np.float32)
                                 * caustic[..., None], 0, 255))
    roi[active] = distorted[active]
    return True
