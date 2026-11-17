"""Private Sauce product-value indicators from real on-disk film receipts.

Deliberately does not equate a completed render with customer satisfaction,
a paying customer, or a premium-quality source film.
"""
from __future__ import annotations

from collections import Counter
import json
import os
from pathlib import Path
import re
import tempfile
import time

JOB_ID = re.compile(r"^[a-f0-9]{24}$")
MAX_JOBS = 10000


def calculate(jobs_root: Path, *, clock: float | None = None) -> dict:
    clock = time.time() if clock is None else float(clock)
    counts: Counter[str] = Counter()
    recent: Counter[str] = Counter()
    total_seconds = 0.
    reviewed = 0
    positive = 0
    ratings = []
    if jobs_root.is_dir():
        for folder in jobs_root.iterdir():
            if sum(counts.values()) >= MAX_JOBS:
                break
            if not folder.is_dir() or folder.is_symlink() or not JOB_ID.fullmatch(folder.name):
                continue
            file = folder / "status.json"
            if not file.is_file() or file.is_symlink():
                continue
            try:
                record = json.loads(file.read_text(encoding="utf-8"))
            except (OSError, ValueError, UnicodeError):
                continue
            if not isinstance(record, dict) or record.get("id") != folder.name:
                continue
            status = record.get("status")
            if status not in ("needs_review", "needs_access", "failed", "needs_key", "queued"):
                continue
            counts["accepted"] += 1
            recent_window = isinstance(record.get("created_at"), (int, float)) and (
                0 <= clock - float(record["created_at"]) < 86400
            )
            if recent_window:
                recent["accepted"] += 1
            category = {
                "needs_review": "ready_for_review",
                "needs_access": "unsupported_access",
                "failed": "failed",
                "needs_key": "configuration_blocked",
                "queued": "queued_or_running",
            }[status]
            counts[category] += 1
            if recent_window:
                recent[category] += 1

            if status != "needs_review":
                continue
            artifact = folder / "export" / "release.json"
            video = folder / "export" / "preview.mp4"
            if not artifact.is_file() or not video.is_file():
                continue
            try:
                release = json.loads(artifact.read_text(encoding="utf-8"))
                size = video.stat().st_size
            except (OSError, ValueError):
                continue
            if (release.get("render_mode") != "continuous-browser-capture"
                    or release.get("continuous_motion") is not True
                    or release.get("source_verified") is not True
                    or size <= 1024):
                continue
            counts["verified_continuous_outputs"] += 1
            if recent_window:
                recent["verified_continuous_outputs"] += 1
            seconds = release.get("duration_seconds")
            if isinstance(seconds, (int,float)) and 1 <= seconds <= 75:
                total_seconds += seconds
            feedback = record.get("feedback")
            rating = feedback.get("rating") if isinstance(feedback, dict) else None
            if type(rating) is int and 1 <= rating <= 5:
                reviewed += 1
                ratings.append(rating)
                if rating >= 4:
                    positive += 1
    return {
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(clock)),
        "all_time": dict(counts),
        "last_24h": dict(recent),
        "verified_continuous_seconds": round(total_seconds, 1),
        "review_count": reviewed,
        "positive_review_count": positive,
        "average_review_rating": round(sum(ratings)/len(ratings), 2) if ratings else None,
        "meaning": {
            "verified_continuous_outputs": "Real continuous browser recordings with stored playable previews, not premium-approved films",
            "positive_review_count": "Optional user ratings of 4 or 5, not proof of payment or retention",
        },
        "revenue": None,
        "payments_integrated": False,
    }


def write_report(report: dict, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=".value-", suffix=".tmp", dir=destination.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            os.fchmod(stream.fileno(), 0o600)
            json.dump(report, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, destination)
    finally:
        try: os.unlink(name)
        except FileNotFoundError: pass


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobs", type=Path, default=Path("/var/lib/sauce-url2video/jobs"))
    parser.add_argument("--output", type=Path, default=Path("/var/lib/sauce-steward/value-report.json"))
    args = parser.parse_args()
    report = calculate(args.jobs)
    write_report(report, args.output)
    print(json.dumps(report, indent=2))
