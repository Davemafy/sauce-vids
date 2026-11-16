"""Deterministic, cache-friendly stage materials; never composites over product UI.

Inputs are normalized scene coordinates. All three materials are computed only
when a stage preset is first requested, not per 60fps output frame. BGR output
matches OpenCV; no image, network or shader asset dependencies.
"""
from __future__ import annotations

import cv2
import numpy as np

STYLES = ("obsidian-grain", "fluted-glass", "chromatic-bloom")


def procedural_backdrop(style: str, width: int = 1920,
                        height: int = 1080) -> np.ndarray:
    if style not in STYLES:
        raise ValueError(f"Unsupported stage material: {style}")
    if width < 64 or height < 64:
        raise ValueError("Stage material dimensions are too small")
    x = np.arange(width, dtype=np.float32)[None, :]
    y = np.arange(height, dtype=np.float32)[:, None]

    # #090a0f in BGR. Keeping the stage dark protects white browser edges.
    base = np.empty((height, width, 3), np.float32)
    base[:] = (15., 10., 9.)

    def bloom(cx: float, cy: float, sx: float, sy: float,
              tint: tuple[float, float, float],
              displaced_x: np.ndarray | None = None) -> None:
        xx = x if displaced_x is None else displaced_x
        field = np.exp(-.5 * (((xx - cx) / sx) ** 2 +
                              ((y - cy) / sy) ** 2))
        base[:] += field[:, :, None] * np.array(tint, np.float32)

    if style == "fluted-glass":
        # Uniform 45px ribs: refraction displaces the *background light*
        # laterally, while narrow facet highlights describe the glass surface.
        # Constant phase down Y prevents artificial vertical wave/wobble.
        phase = x * (2. * np.pi / 45.)
        refracted_x = x + 8. * np.sin(phase)
        bloom(260, 485, 480, 400, (27., 12., 13.), refracted_x)
        bloom(1660, 395, 430, 420, (22., 11., 26.), refracted_x)
        bloom(1060, 1090, 660, 275, (13., 10., 9.), refracted_x)
        ridge = (2.1 * np.cos(phase) +
                 3.5 * np.maximum(0., np.cos(phase)) ** 18 -
                 1.3 * np.abs(np.sin(phase)) ** 10)
        # A slight top-to-bottom glass attenuation, never strong edge bars.
        rib_gain = .74 + .26 * (1. - y / float(height))
        base[:] += (ridge * rib_gain)[:, :, None]
    elif style == "chromatic-bloom":
        # Three blurred, slightly offset color lobes provide edge dispersion
        # without colored fringes on the real browser window/text.
        bloom(335, 540, 520, 460, (24., 12., 10.))
        bloom(1620, 485, 495, 510, (12., 13., 27.))
        bloom(980, 980, 640, 330, (13., 9., 13.))
        # Offset each channel's luminous fringe by only 13px.
        edge = np.exp(-.5 * (((x - 1510) / 350) ** 2 +
                              ((y - 355) / 370) ** 2))
        base[:, :, 0] += np.roll(edge, 13, axis=1) * 3.0
        base[:, :, 2] += np.roll(edge, -13, axis=1) * 3.0
        base[:] = cv2.GaussianBlur(base, (0, 0), 4.0)
    else:
        # Obsidian is the quiet matte option; subtle brand light is carried by
        # the existing RMS-gated ambient map only when real audio supplies it.
        bloom(410, 570, 670, 550, (4.5, 2.1, 2.1))
        bloom(1570, 510, 660, 560, (3.0, 2.0, 4.0))

    # Fixed-seed, subpixel-scale analog grain. No frame-index jitter.
    rng = np.random.default_rng(20261116)
    noise = rng.integers(-4, 5, size=(height, width),
                         dtype=np.int8).astype(np.float32)
    amplitude = 0.45 if style == "obsidian-grain" else .38
    base[:] += (noise * amplitude)[:, :, None]
    return np.uint8(np.clip(np.rint(base), 0, 66))
