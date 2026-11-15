#!/usr/bin/env python3
"""Verify silent Sauce StudioMotion video exports and optional frame determinism.

Usage:
    python scripts/verify_studio_motion_export.py <release-directory> [<repeat-directory>]

Does not read or process audio. Fails if any output contains an audio track.
Comparison uses FFmpeg decoded-frame hashes, not container or timestamp metadata.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def probe(video: Path, width: int, height: int, fps: int) -> dict:
    if not video.is_file():
        raise FileNotFoundError(video)
    process = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames",
         "-of", "json", str(video)],
        text=True, capture_output=True, check=True, timeout=30,
    )
    streams = json.loads(process.stdout)["streams"]
    if len(streams) != 1 or streams[0].get("codec_type") != "video":
        raise ValueError(f"Silent export required; unexpected streams in {video}")
    stream = streams[0]
    if (stream.get("width"), stream.get("height")) != (width, height):
        raise ValueError(f"Unexpected dimensions in {video}")
    numerator, denominator = map(int, stream["r_frame_rate"].split("/"))
    if denominator == 0 or numerator != fps * denominator:
        raise ValueError(f"Unexpected FPS in {video}")
    if stream.get("codec_name") != "h264":
        raise ValueError(f"Unexpected codec in {video}")
    return stream


def frame_hashes(video: Path) -> tuple[str, int]:
    frames = subprocess.run(
        ["ffmpeg", "-v", "error", "-xerror", "-i", str(video),
         "-map", "0:v:0", "-f", "framemd5", "-"],
        text=True, capture_output=True, check=True, timeout=120,
    )
    rows = [line for line in frames.stdout.splitlines()
            if line and not line.startswith("#")]
    if not rows:
        raise ValueError(f"No decoded frames: {video}")
    digest = hashlib.sha256("\n".join(rows).encode("ascii")).hexdigest()
    return digest, len(rows)


def verify_release(path: Path) -> dict:
    receipt = json.loads((path / "release.json").read_text())
    sm = receipt.get("studio_motion") or {}
    config = receipt.get("studio_config") or {}
    if not sm.get("enabled") or not sm.get("studio_floor"):
        raise ValueError("StudioMotion floor/time-warp release expected")
    if not config.get("enableTimeWarp") or not config.get("enableCallouts"):
        raise ValueError("TimeWarp and callouts must be active")
    if receipt.get("audio_reactive") is not None:
        raise ValueError("Audio processing is forbidden in this release")
    if receipt.get("source_dpr", 0) < 2:
        raise ValueError("High-DPI source expected")
    if receipt.get("preview_resampling") != "lanczos":
        raise ValueError("Lanczos preview expected")
    if sm.get("protected_actions", 0) < 1:
        raise ValueError("Action windows were not protected")
    if sm.get("speed_peak", 0) > 4.0:
        raise ValueError("Time warp exceeds configured speed cap")
    master = path / "master-1080p60.mp4"
    preview = path / "preview.mp4"
    meta = probe(master, 1920, 1080, 60)
    probe(preview, 1280, 720, 30)
    digest, count = frame_hashes(master)
    expected = receipt.get("studio_output_frames")
    if count != expected or (meta.get("nb_frames") and int(meta["nb_frames"]) != count):
        raise ValueError(f"Frame count mismatch: {count}, expected {expected}")
    return {
        "path": str(path),
        "frames": count,
        "decoded_sha256": digest,
        "max_warp_speed": sm.get("speed_peak"),
        "protected_action_windows": sm.get("protected_actions"),
        "callouts": sm.get("callouts"),
        "floor_reflection_intensity": config.get("floorReflectionIntensity"),
        "source_dpr": receipt["source_dpr"],
        "audio_streams": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("first", type=Path)
    parser.add_argument("second", type=Path, nargs="?")
    args = parser.parse_args()
    first = verify_release(args.first)
    result: dict = {"first": first, "deterministic": None}
    if args.second:
        second = verify_release(args.second)
        result["second"] = second
        result["deterministic"] = (
            first["frames"] == second["frames"] and
            first["decoded_sha256"] == second["decoded_sha256"]
        )
        if not result["deterministic"]:
            raise ValueError("Decoded output frames differ between runs")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
