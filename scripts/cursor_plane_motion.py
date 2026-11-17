"""Continuously move one real cursor hotspot between Sauce H0/H60 planes.

An instantaneous Boolean choice at a rounded-dialog boundary creates a
perceptible 10–25px pointer teleport even when recorded CSS mouse positions
are continuous. This class affects only visual depth projection. It never
changes captured events, mouse clicks, camera movement, or Chromium hover.
"""
from __future__ import annotations

import math


class CursorPlaneGlide:
    # Eight-ish output frames at 60fps let a cursor visibly settle onto a
    # 60px-elevated modal without a sudden 3D parallax hop.
    TRANSITION_SECONDS = 0.14
    # A beat-locked source jump is a cut, not a physical 3D flight. Reset
    # depth on such jumps rather than animating across omitted source time.
    CUT_GAP_SECONDS = 0.20

    def __init__(self) -> None:
        self._last_time: float | None = None
        self._target: float = 0.
        self._start: float = 0.
        self._start_time: float = 0.

    def _value(self, t: float) -> float:
        fraction = max(0., min(1., (t-self._start_time)
                               / self.TRANSITION_SECONDS))
        # Quintic smoothstep: both velocity and acceleration are zero at
        # the H0 and H60 endpoints, avoiding a new jerk in the projection.
        ease = fraction*fraction*fraction*(fraction*(fraction*6-15)+10)
        return self._start+(self._target-self._start)*ease

    def sample(self, source_seconds: float, modal_hit: bool) -> float:
        if not math.isfinite(source_seconds) or source_seconds < 0:
            raise ValueError("Cursor projection requires valid source time")
        destination = 1. if modal_hit else 0.
        if (self._last_time is None or
            source_seconds < self._last_time-1e-6 or
            source_seconds-self._last_time > self.CUT_GAP_SECONDS):
            self._target = self._start = destination
            self._start_time = source_seconds
        elif destination != self._target:
            current = self._value(source_seconds)
            self._start=current
            self._target=destination
            self._start_time=source_seconds
        self._last_time=source_seconds
        return self._value(source_seconds)
