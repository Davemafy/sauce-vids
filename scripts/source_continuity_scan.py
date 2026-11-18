"""Inspect *real decoded browser frames* and reject navigation-remount gaps.

This module is an evidence classifier, not a generative transition. It never
alters a pixel, invents a missing frame, or infers application behavior.
Stable-source ranges can be passed to the existing EDL renderer, which must
still verify every click, actual DOM outcome, cursor track, and framing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import cv2
import numpy as np

FPS = 60
SAMPLE_WIDTH = 264
SAMPLE_HEIGHT = 144
MIN_GLITCH_FRAMES = 3
POST_GAP_FRAMES = 1


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for part in iter(lambda: handle.read(2 ** 20), b""):
            digest.update(part)
    return digest.hexdigest()


def _sample_metrics(frame: np.ndarray) -> tuple[float, float]:
    """Near-white fraction and white border, not an absolute 'dark theme' rule."""
    small = cv2.resize(
        frame, (SAMPLE_WIDTH, SAMPLE_HEIGHT), interpolation=cv2.INTER_AREA
    )
    white = np.min(small, axis=2) > 235
    border = np.zeros((SAMPLE_HEIGHT, SAMPLE_WIDTH), dtype=np.bool_)
    border[:8] = True
    border[-8:] = True
    border[:, :8] = True
    border[:, -8:] = True
    return float(np.mean(white)), float(np.mean(white[border]))


def runs_of_flags(flags: np.ndarray, min_frames=MIN_GLITCH_FRAMES):
    if flags.ndim != 1:
        raise ValueError("Expected one truth value per decoded frame")
    if min_frames < 1:
        raise ValueError("Minimum span must be positive")
    padded = np.pad(flags.astype(np.int8), (1, 1))
    starts = np.flatnonzero(np.diff(padded) == 1)
    stops = np.flatnonzero(np.diff(padded) == -1)
    if len(starts) != len(stops):
        raise AssertionError("Inconsistent source quality scan")
    return [[int(a), int(b - 1)] for a, b in zip(starts, stops)
            if b - a >= min_frames]


def unstable_runs(white_fractions, border_fractions) -> list[list[int]]:
    """Detect unusually bright, persistent edge flashes *relative to source*.

    Light-themed websites with consistently bright content are not rejected.
    Hard upper bounds keep accidental bright buttons from becoming a 'flash.'
    This is deliberately conservative and may return none for other glitch
    types; those still require visual review.
    """
    white = np.asarray(white_fractions, dtype=np.float64)
    border = np.asarray(border_fractions, dtype=np.float64)
    if white.ndim != 1 or border.shape != white.shape or not len(white):
        raise ValueError("Missing per-frame quality metrics")
    if not (np.isfinite(white).all() and np.isfinite(border).all()):
        raise ValueError("Nonfinite source-frame quality measurements")
    if np.any(white < 0) or np.any(white > 1) or np.any(border < 0) or np.any(border > 1):
        raise ValueError("Invalid source-frame fractions")

    baseline_white = float(np.median(white))
    baseline_border = float(np.median(border))
    flags = ((white > max(.075, baseline_white + .065)) &
             (border > max(.22, baseline_border + .20)))
    windows = runs_of_flags(flags)
    # A single bright first frame is often a premature browser screenshot.
    # Mark it only if the remainder gives evidence of a different baseline.
    if flags[0] and not (len(white) > 1 and flags[1]):
        windows.insert(0, [0, 0])
    return windows


def stable_segments(frame_count, unstable_ranges, tail_guard=POST_GAP_FRAMES):
    if type(frame_count) is not int or frame_count <= 0:
        raise ValueError("Invalid source frame count")
    if type(tail_guard) is not int or not 0 <= tail_guard <= 4:
        raise ValueError("Source guard must be 0-4 captured frames")
    segments = []
    cursor = 0
    for lo, hi in unstable_ranges:
        if not (type(lo) is int and type(hi) is int
                and cursor <= lo <= hi < frame_count):
            raise ValueError("Unsorted or overlapping unstable source intervals")
        if lo > cursor:
            segments.append([cursor, lo])  # half-open ranges
        cursor = hi + 1 + tail_guard
    if cursor < frame_count:
        segments.append([cursor, frame_count])
    return segments


def scan_source(video: Path, expected_sha256=None) -> dict:
    video = Path(video)
    if not video.exists() or not video.is_file():
        raise ValueError("Missing recorded video")
    if expected_sha256 and _sha256(video) != expected_sha256:
        raise ValueError("Raw source SHA256 does not match receipt")

    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise ValueError("Unable to decode captured source")
    frame_count = 0
    metrics = []
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    if fps != FPS or width < 480 or height < 270:
        cap.release()
        raise ValueError("Expected original 60fps landscape source")
    try:
        while True:
            valid, frame = cap.read()
            if not valid:
                break
            metrics.append(_sample_metrics(frame))
            frame_count += 1
            if frame_count > 30 * FPS:
                raise ValueError("Source exceeds 30-second review bound")
    finally:
        cap.release()
    if frame_count < 120:
        raise ValueError("Insufficient real captured footage")
    values = np.asarray(metrics, dtype=np.float64)
    unstable = unstable_runs(values[:, 0], values[:, 1])
    return {
        "schema": "sauce-source-instability-v1",
        "sourceSha256": expected_sha256 or _sha256(video),
        "sourceWidth": width,
        "sourceHeight": height,
        "fps": FPS,
        "decodedFrames": frame_count,
        "unstableRanges": unstable,
        "stableSegments": stable_segments(frame_count, unstable),
        "thresholds": {"whiteIncrement": .065, "borderIncrement": .20,
                       "minimumGlitchFrames": MIN_GLITCH_FRAMES},
        "requiresHumanVisualReview": True,
    }


def validate_continuity_receipt(receipt:dict, *, source_sha256:str,
                                source_frames:int, source_size:tuple[int,int],
                                edit:dict)->bool:
    """Reject hand-waved or stale source cuts before the compositor runs."""
    if receipt.get("schema")!="sauce-source-instability-v1":
        raise ValueError("Unverified source-continuity schema")
    if receipt.get("sourceSha256")!=source_sha256:
        raise ValueError("Source video does not match continuity scan SHA256")
    if (receipt.get("decodedFrames")!=source_frames or
        (receipt.get("sourceWidth"),receipt.get("sourceHeight"))!=source_size or
        receipt.get("fps")!=FPS):
        raise ValueError("Continuity receipt and source stream disagree")
    gaps=receipt.get("unstableRanges")
    if not isinstance(gaps,list):
        raise ValueError("Continuity receipt missing source gaps")
    expected=stable_segments(source_frames,gaps)
    if expected!=receipt.get("stableSegments"):
        raise ValueError("Continuity receipt stable spans have been modified")
    if gaps!=edit.get("unstableRanges"):
        raise ValueError("EDL contains different instability gaps than decoded source")
    for shot in edit.get("shots",[]):
        a,b=shot.get("startFrame"),shot.get("endFrame")
        if (type(a) is not int or type(b) is not int or
            not any(lo<=a<b<=hi for lo,hi in expected)):
            raise ValueError("EDL contains an unverified unstable source frame")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--source-hash")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    receipt = scan_source(args.video, args.source_hash)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"frames": receipt["decodedFrames"],
                      "unstableRanges": receipt["unstableRanges"],
                      "stableSegments": receipt["stableSegments"]}))


if __name__ == "__main__":
    main()
