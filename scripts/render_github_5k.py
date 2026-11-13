#!/usr/bin/env python3
"""Reproducible, brand-free Sauce 5K render benchmark for GitHub Actions.

Captures a public product in actual 5120x2880 browser pixels, records a
deliberate scroll path, and exports a 5K master plus Android-compatible 720p.
No 1080p source is upscaled, and no synthetic product UI is generated.
"""
from __future__ import annotations

import argparse
from io import BytesIO
import json
from pathlib import Path
import shutil
import subprocess
import time

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright


URL = "https://www.brimble.io/agent"
WIDTH, HEIGHT = 5120, 2880
CSS_W, CSS_H, SCALE = 1280, 720, 4
APERTURE_W, APERTURE_H = 4800, 2700
FPS = 24


def ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def scroll_y(t: float, duration: float) -> int:
    # Scaled to the clip duration, keeping a first-shot reading pause.
    t *= 12.0 / duration
    for start, end, a, b in (
        (0.0, 1.2, 0, 0),
        (1.2, 2.8, 0, 580),
        (2.8, 3.45, 580, 580),
        (3.45, 5.1, 580, 1120),
        (5.1, 5.85, 1120, 1120),
        (5.85, 7.55, 1120, 1700),
        (7.55, 8.15, 1700, 1700),
        (8.15, 10.25, 1700, 2260),
        (10.25, 12.0, 2260, 2260),
    ):
        if start <= t < end:
            return round(a + (b - a) * ease((t - start) / (end - start)))
    return 2260


def command(args: list[str], timeout: int = 900) -> None:
    print("RUN", " ".join(args[:13]), flush=True)
    subprocess.run(args, timeout=timeout, check=True)


def video_info(path: Path) -> dict:
    return json.loads(subprocess.check_output(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=codec_name,profile,level,width,height,avg_frame_rate,nb_frames,pix_fmt",
         "-of", "json", str(path)],
        text=True,
    ))["streams"][0]


def capture_frames(directory: Path, duration: int) -> dict:
    frames = directory / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    last_position = None
    last_path = None
    distinct_positions = 0
    started = time.monotonic()

    base = Image.new("RGB", (WIDTH, HEIGHT), "#e7e6e3")
    offset = ((WIDTH - APERTURE_W) // 2, (HEIGHT - APERTURE_H) // 2)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--hide-scrollbars"],
        )
        context = browser.new_context(
            viewport={"width": CSS_W, "height": CSS_H},
            device_scale_factor=SCALE,
            reduced_motion="reduce",
            color_scheme="light",
        )
        page = context.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(1600)
        title = page.title()
        hero = page.locator("h1").first.inner_text(timeout=15000).strip()
        if not title or not hero:
            raise RuntimeError("Expected a real product page with title and visible heading")
        page.evaluate(
            "() => {document.documentElement.style.scrollBehavior='auto';"
            "document.body.style.scrollBehavior='auto';}"
        )
        total_frames = duration * FPS
        for i in range(total_frames):
            scroll = scroll_y(i / FPS, duration)
            dest = frames / f"{i:04d}.jpg"
            if last_position == scroll and last_path is not None:
                dest.hardlink_to(last_path)
                continue
            page.evaluate("(y) => window.scrollTo(0,y)", scroll)
            jpeg = page.screenshot(
                type="jpeg", quality=92, animations="disabled",
                caret="hide", timeout=45000,
            )
            with Image.open(BytesIO(jpeg)) as photo:
                if photo.size != (WIDTH, HEIGHT):
                    raise RuntimeError(f"Capture is not native 5K: {photo.size}")
                page_pixels = photo.convert("RGB").resize(
                    (APERTURE_W, APERTURE_H), Image.Resampling.LANCZOS
                )
            frame = base.copy()
            frame.paste(page_pixels, offset)
            frame.save(dest, "JPEG", quality=91, subsampling=0)
            if i == 0:
                frame.save(directory / "poster.jpg", "JPEG", quality=88)
            if i % 48 == 0:
                print(f"CAPTURE {i}/{total_frames}, scroll={scroll}", flush=True)
            last_position = scroll
            last_path = dest
            distinct_positions += 1
        browser.close()

    if len(list(frames.glob("*.jpg"))) != duration * FPS:
        raise RuntimeError("Capture frame count is incomplete")
    if distinct_positions < max(2, duration):
        raise RuntimeError("Capture did not contain enough real scroll movement")
    with Image.open(frames / "0000.jpg") as first:
        with Image.open(frames / f"{duration * FPS - 1:04d}.jpg") as last:
            diff = ImageChops.difference(
                first.convert("RGB").resize((480, 270)),
                last.convert("RGB").resize((480, 270)),
            )
            if diff.getbbox() is None:
                raise RuntimeError("First and last frames are visually identical")
    return {
        "page_title": title, "hero": hero,
        "distinct_scroll_positions": distinct_positions,
        "capture_seconds": round(time.monotonic() - started, 2),
    }


def render(directory: Path, duration: int) -> dict:
    frames = directory / "frames" / "%04d.jpg"
    master = directory / "brimble-5k-master.mp4"
    phone = directory / "brimble-android-720p.mp4"
    start = time.monotonic()
    command([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-framerate", str(FPS), "-i", str(frames),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-threads", "4",
        "-movflags", "+faststart", str(master),
    ])
    command([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-framerate", str(FPS), "-i", str(frames),
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
        "-map", "0:v:0", "-map", "1:a:0", "-t", str(duration),
        "-vf", "scale=1280:720:flags=lanczos,format=yuv420p",
        "-c:v", "libx264", "-profile:v", "baseline", "-level:v", "3.1",
        "-bf", "0", "-refs", "1", "-g", "48", "-crf", "19",
        "-preset", "veryfast", "-threads", "4",
        "-c:a", "aac", "-b:a", "64k", "-ar", "44100",
        "-movflags", "+faststart", str(phone),
    ])
    expected_frames = duration * FPS
    for path, expected_wh in (
        (master, (WIDTH, HEIGHT)),
        (phone, (1280, 720)),
    ):
        stream = video_info(path)
        if (stream["width"], stream["height"]) != expected_wh:
            raise RuntimeError(f"Wrong output dimensions: {path}: {stream}")
        if stream["codec_name"] != "h264":
            raise RuntimeError(f"Unexpected codec: {path}")
        if int(stream["nb_frames"]) != expected_frames:
            raise RuntimeError(f"Unexpected video frame count: {path}: {stream}")
        command([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-xerror",
            "-i", str(path), "-f", "null", "-",
        ])
    mobile = video_info(phone)
    if mobile.get("profile") not in ("Constrained Baseline", "Baseline"):
        raise RuntimeError("Mobile export must use the H.264 Baseline profile")
    if int(mobile["level"]) > 31:
        raise RuntimeError("Mobile export exceeds H.264 level 3.1")
    return {
        "encode_and_verify_seconds": round(time.monotonic() - start, 2),
        "master": {
            "file": master.name, "bytes": master.stat().st_size,
            "stream": video_info(master),
        },
        "phone": {
            "file": phone.name, "bytes": phone.stat().st_size,
            "stream": mobile,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("out/5k-benchmark"))
    parser.add_argument("--duration", type=int, default=12)
    args = parser.parse_args()
    if not 3 <= args.duration <= 30:
        parser.error("duration must be between 3 and 30 seconds")
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        parser.error("ffmpeg and ffprobe are required")

    directory = args.out.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    capture = capture_frames(directory, args.duration)
    encoded = render(directory, args.duration)
    receipt = {
        "input_url": URL, "duration_seconds": args.duration, "fps": FPS,
        "render_size": [WIDTH, HEIGHT],
        "source": "Playwright real browser, CSS 1280x720 at 4x device scale",
        "stage": "plain neutral background; no Sauce branding",
        "not_upscaled_from_1080p_video": True,
        "note": "5K Level 6 H.264 is a master, not a phone-compatible playback format",
        "timing": {**{k: v for k, v in capture.items() if k == "capture_seconds"},
                   "encode_and_verify_seconds": encoded["encode_and_verify_seconds"],
                   "total_seconds": round(time.monotonic() - t0, 2)},
        "page_title": capture["page_title"], "hero": capture["hero"],
        "distinct_scroll_positions": capture["distinct_scroll_positions"],
        "master": encoded["master"], "phone": encoded["phone"],
    }
    (directory / "benchmark.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    print("BENCHMARK_RECEIPT " + json.dumps(receipt), flush=True)


if __name__ == "__main__":
    main()
