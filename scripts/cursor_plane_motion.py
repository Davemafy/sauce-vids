"""One-frame repair for a real cursor crossing Sauce's H0/H60 boundary.

The approved recording's cursor track is already smooth; the only defect
was the discrete change in visual projection at the modal edge. Preserve
EVERY other source-mapped frame. There is no simulated glide or velocity
damping, and mouse events/hotspots remain source-true.
"""
from __future__ import annotations

import math


class CursorPlaneSeamRepair:
    # Only one 60fps frame may receive a half-plane projected hotspot.
    # An 8-frame animation made the pointer feel robotic and was rejected.
    BLEND_AT_SEAM = 0.5
    # A large source time jump represents an editorial cut, not movement.
    CUT_GAP_SECONDS = 0.20

    def __init__(self) -> None:
        self._previous_hit: bool | None = None
        self._previous_time: float | None = None

    def sample(self, source_seconds: float, modal_hit: bool,
               force_exact: bool = False) -> float:
        """Return H60 weight, modifying at most the crossing frame.

        At the first post-crossing frame only, use the midpoint between
        the exact H0 and H60 projected hotspots. The very next frame is
        the original target plane, with no delayed interpolation.
        """
        if not math.isfinite(source_seconds) or source_seconds < 0:
            raise ValueError("Cursor depth projection needs valid source time")
        target = 1. if modal_hit else 0.
        in_cut = (self._previous_time is None or
                  source_seconds < self._previous_time-1e-6 or
                  source_seconds-self._previous_time > self.CUT_GAP_SECONDS)
        crossed = (not in_cut and self._previous_hit is not None and
                   self._previous_hit != modal_hit)
        self._previous_hit = modal_hit
        self._previous_time = source_seconds
        # Exact recorded click / overlay cut alignment always wins.
        if force_exact or in_cut or not crossed:
            return target
        return self.BLEND_AT_SEAM
