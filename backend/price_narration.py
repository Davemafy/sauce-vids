"""Narration derived from a single observed billing change, with offline synthesis."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import wave
from pathlib import Path

PRICE = re.compile(r"\$\s*(\d{1,4})(?:\s*/\s*mo)?", re.IGNORECASE)
RATE = 24000


def price_lines(event: dict, brief: str = "") -> list[dict]:
    change = event.get("price_change") or {}
    before = PRICE.fullmatch(change.get("before", ""))
    after = PRICE.fullmatch(change.get("after", ""))
    if change.get("period") != "month" or not before or not after or before[1] == after[1]:
        return []
    if brief and not re.search(r"pric|cost|\bplan\b|\bbilling\b|\bmonthly\b", brief, re.I):
        return []
    # A brief supplies editorial intent. Product facts come only from the receipt.
    return [
        {"start": .14, "deadline": event["t"], "text": f"It starts at {int(before[1])} dollars a month."},
        {"start": event["t"] + .12, "text": f"Now it's {int(after[1])} dollars a month."},
    ]


def narration_config():
    return [os.getenv(key) for key in ("SAUCE_KOKORO_PYTHON", "SAUCE_KOKORO_MODEL", "SAUCE_KOKORO_VOICES")]


def render_narration(folder: Path, events: list[dict], duration: float, brief: str, requested: str):
    if requested == "clean":
        return None
    config = narration_config()
    slider = next((e for e in events if e["kind"] == "slider_change"), {})
    lines = price_lines(slider, brief)
    if not (lines and all(config)):
        if requested == "narrated":
            raise ValueError("Narration requires a grounded monthly price change and configured Kokoro")
        return None
    plan = folder / "narration-plan.json"
    wav = folder / "narration.wav"
    receipt = folder / "narration-timing.json"
    plan.write_text(json.dumps({"lines": lines, "duration": duration}))
    python, model, voices = config
    subprocess.run([python, str(Path(__file__).resolve()), model, voices, str(plan),
                    str(wav), str(receipt)], check=True, timeout=90)
    return wav


def synthesize(model: str, voices: str, plan: Path, wav: Path, receipt: Path):
    import numpy as np
    from kokoro_onnx import Kokoro

    request = json.loads(plan.read_text())
    audio = np.zeros(int(request["duration"] * RATE), dtype=np.float32)
    kokoro = Kokoro(model, voices)
    timings = []
    for line in request["lines"]:
        samples, rate = kokoro.create(line["text"], voice="af_heart", speed=1.09, lang="en-us")
        start = round(line["start"] * RATE)
        stop = start + len(samples)
        deadline = min(len(audio), int(line.get("deadline", request["duration"]) * RATE))
        if rate != RATE or stop > deadline or (timings and line["start"] < timings[-1]["end"]):
            raise ValueError("Narration exceeds its verified timing window")
        audio[start:stop] = samples
        timings.append({**line, "end": stop / RATE})
    peak = float(np.max(np.abs(audio)))
    if not np.isfinite(peak) or peak < .01:
        raise ValueError("Kokoro did not produce usable speech")
    audio *= .69 / peak
    with wave.open(str(wav), "wb") as output:
        output.setparams((1, 2, RATE, 0, "NONE", "not compressed"))
        output.writeframes((audio * 32767).astype("<i2").tobytes())
    receipt.write_text(json.dumps(timings, indent=2))


if __name__ == "__main__":
    synthesize(sys.argv[1], sys.argv[2], *(Path(value) for value in sys.argv[3:]))
