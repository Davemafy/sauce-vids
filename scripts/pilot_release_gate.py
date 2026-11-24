"""Private concierge delivery gate. Automated quality is not owner approval.

This is an operator CLI, not a public endpoint or authentication mechanism.
Review links remain available for diagnostics. Customer delivery requires
an explicit decision on the exact encoded MP4 and fresh source-bound QA.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from scripts.quality_preview_supervisor import analyze, digest, probe

KINDS = frozenset(("interactive", "showcase"))


def prepare(film, source, manifest, *, source_sha, manifest_sha, kind):
    film, source, manifest = map(Path, (film, source, manifest))
    if kind not in KINDS:
        raise ValueError("Declare interactive demo or public showcase")
    if digest(source) != source_sha or digest(manifest) != manifest_sha:
        raise ValueError("Original evidence identity mismatch")
    raw = json.loads(manifest.read_text())
    if not isinstance(raw, dict):
        raise ValueError("Missing original event receipt")
    events = raw.get("events")
    if not isinstance(events, list):
        raise ValueError("Missing original events")
    if kind == "interactive" and not any(
        isinstance(e, dict) and e.get("kind") in ("click", "slider_change", "tab_switch")
        and isinstance(e.get("evidence"), str) and e["evidence"].strip()
        for e in events
    ):
        raise ValueError("No verified public product interaction")
    info = probe(film)
    video = next((s for s in info["streams"] if s["codec_type"] == "video"), {})
    if (video.get("width"), video.get("height"), video.get("avg_frame_rate")) != (1920, 1080, "60/1"):
        raise ValueError("Expected landscape 1080p60 master")
    subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(film),
                    "-f", "null", "-"], check=True, timeout=120)
    qa = analyze(film, {"source_path": str(source), "source_sha256": source_sha,
        "event_manifest_path": str(manifest), "event_manifest_sha256": manifest_sha},
        seconds=float(info["format"]["duration"]))
    return {"schema": "sauce-pilot-candidate-v1", "film_sha256": qa["film_sha256"],
            "source_sha256": source_sha, "manifest_sha256": manifest_sha, "kind": kind,
            "duration": qa["duration"], "technical_verdict": qa["verdict"],
            "findings": qa["findings"], "creative_approved": False}


def approved(candidate, decision):
    return (isinstance(candidate, dict) and isinstance(decision, dict)
            and candidate.get("schema") == "sauce-pilot-candidate-v1"
            and candidate.get("technical_verdict") == "HUMAN_REVIEW_REQUIRED"
            and candidate.get("findings") == []
            and decision.get("schema") == "sauce-owner-film-review-v1"
            and decision.get("decision") == "approved"
            and isinstance(decision.get("reviewer"), str)
            and bool(decision["reviewer"].strip())
            and isinstance(candidate.get("film_sha256"), str)
            and len(candidate["film_sha256"]) == 64
            and decision.get("film_sha256") == candidate["film_sha256"])


def deliver(film, candidate, decision, output):
    """Only local owner-approved copy; never exposes an endpoint or publishes."""
    film, output = Path(film), Path(output)
    if not approved(candidate, decision) or digest(film) != candidate["film_sha256"]:
        raise ValueError("Exact film has no matching technical and owner approval")
    # Exclusive create prevents accidentally replacing a customer's existing file.
    with film.open("rb") as src, output.open("xb") as dst:
        shutil.copyfileobj(src, dst)
    if digest(output) != candidate["film_sha256"]:
        output.unlink()
        raise ValueError("Delivery copy integrity failure")
    return output


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("review")
    for name in ("film", "source", "manifest", "out"):
        r.add_argument("--"+name, required=True, type=Path)
    r.add_argument("--source-sha", required=True)
    r.add_argument("--manifest-sha", required=True)
    r.add_argument("--kind", required=True, choices=sorted(KINDS))
    d = sub.add_parser("deliver")
    for name in ("film", "candidate", "decision", "out"):
        d.add_argument("--"+name, required=True, type=Path)
    a = p.parse_args()
    if a.command == "review":
        result = prepare(a.film, a.source, a.manifest, source_sha=a.source_sha,
                         manifest_sha=a.manifest_sha, kind=a.kind)
        with a.out.open("x") as f:
            json.dump(result, f, indent=2)
        print(result["technical_verdict"], "owner approval required")
    else:
        deliver(a.film, json.loads(a.candidate.read_text()),
                json.loads(a.decision.read_text()), a.out)
        print("Owner-approved local delivery copy")


if __name__ == "__main__":
    main()
