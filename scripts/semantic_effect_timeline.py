"""Fail-closed, frame-indexed effect scheduling on verified Sauce source regions.

Only semantic-layer-separation is wired to the MP4 compositor today.
The compositor supplies evidence only AFTER existing Chromium, source-package
and clean-background verification. This module never synthesizes UI.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from semantic_spatial_handoff import eased

EffectFamily = Literal["semantic-layer-separation"]
PASS_ORDER = (
    "source-background", "background-focus", "source-foreground",
    "foreground-edge", "projected-cursor"
)
IMPLEMENTED_FAMILIES = frozenset({"semantic-layer-separation"})


@dataclass(frozen=True)
class VerifiedEffectEvidence:
    """Caller-verified facts; not independent proof of source authenticity."""
    real_pixels: bool
    stable_geometry: bool
    clean_background: bool
    single_projected_cursor: bool

    def complete(self) -> bool:
        return (self.real_pixels and self.stable_geometry and
                self.clean_background and self.single_projected_cursor)


@dataclass(frozen=True)
class EffectSample:
    family: EffectFamily
    target_id: str
    start_frame: int
    frame: int
    progress: float
    mask: str
    passes: tuple[str, ...]

    @property
    def depth_fraction(self) -> float:
        return self.progress

    @property
    def background_focus_fraction(self) -> float:
        return self.progress


class SemanticEffectTimeline:
    """Track effect ownership on the same integer frame clock as the renderer.

    Missing source or geometry evidence immediately revokes ownership;
    no interpolation survives a failed browser-source verification.
    """
    def __init__(self, fps: int = 60):
        if fps not in (30, 60):
            raise ValueError("Unsupported Sauce effect output frame rate")
        self.fps = fps
        self._active: dict[str, tuple[str, int, int]] = {}
        self._last_frame: int | None = None

    def release(self, target_id: str) -> None:
        self._active.pop(target_id, None)

    def sample(self, *, family: str, target_id: str, frame: int,
               evidence: VerifiedEffectEvidence, duration_ms: int = 300,
               mask: str = "verified-dialog") -> EffectSample | None:
        if family not in IMPLEMENTED_FAMILIES:
            raise ValueError("Unimplemented or unapproved Sauce effect family")
        if not isinstance(target_id, str) or not target_id.strip():
            raise ValueError("Effect target requires persistent semantic identity")
        if not isinstance(frame, int) or frame < 0:
            raise ValueError("Effect frame must be a nonnegative integer")
        if self._last_frame is not None and frame < self._last_frame:
            raise ValueError("Effect clock moved backwards")
        self._last_frame = frame
        if not isinstance(evidence, VerifiedEffectEvidence):
            raise ValueError("Effect requires independently verified evidence")
        if not evidence.complete():
            self.release(target_id)
            return None
        if not isinstance(duration_ms, int) or not 100 <= duration_ms <= 1200:
            raise ValueError("Effect duration outside legibility-safe limits")
        if mask != "verified-dialog":
            raise ValueError("Unsupported mask: never distort the whole UI")
        duration_frames = self.fps * duration_ms / 1000
        existing = self._active.get(target_id)
        if existing is not None and existing[0] != family:
            raise ValueError("Incompatible effect owns the same source region")
        if existing is None:
            self._active[target_id] = (family, frame, duration_ms)
            start_frame = frame
        else:
            _, start_frame, old_duration = existing
            if old_duration != duration_ms:
                raise ValueError("Cannot retime an active effect mid-shot")
        progress = eased((frame - start_frame) / duration_frames)
        return EffectSample(
            family=family, target_id=target_id, start_frame=start_frame,
            frame=frame, progress=progress, mask=mask, passes=PASS_ORDER
        )
