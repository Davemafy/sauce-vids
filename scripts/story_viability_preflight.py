#!/usr/bin/env python3
"""Sauce source-first visible-change admission, before any full-film render.

A conservative *technical triage* of genuine browser before/after screenshots.
Requires observed user action, measured result region and right-to-use proof.
No LLM, synthesized UI, semantic invention or automatic premium scoring.

The preflight's passing status only permits a SHORT HUMAN-REVIEW CANDIDATE;
it never approves launch, film quality, or full video production.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import urlsplit

import cv2
import numpy as np

SAMPLE = (640, 360)
MIN_RESULT_FRAME_FRACTION = .055
MIN_CHANGED_FRAME_FRACTION = .035
MIN_CHANGED_RESULT_FRACTION = .075


def _rect(value, width, height):
    if not isinstance(value, dict):
        raise ValueError("Missing browser-measured result rectangle")
    try:
        x, y, w, h = [float(value[k]) for k in ("x", "y", "width", "height")]
    except (ValueError, KeyError, TypeError) as exc:
        raise ValueError("Invalid browser result rectangle") from exc
    if (not all(math.isfinite(v) for v in (x, y, w, h))
        or min(w, h) < 8 or x < 0 or y < 0
        or x + w > width + 2 or y + h > height + 2):
        raise ValueError("Result rectangle is not fully visible in source")
    return (x, y, w, h)


def _verified_event(proof, width, height):
    if not isinstance(proof, dict):
        raise ValueError("Missing source evidence")
    action, changed = proof.get("action"), proof.get("result")
    if not isinstance(action, dict) or not isinstance(changed, dict):
        raise ValueError("Expected real action and DOM-change receipts")
    if action.get("kind") not in ("click", "slider_change", "drag", "input"):
        raise ValueError("Unsupported real action for visual product payoff")
    if changed.get("kind") != "state_change":
        raise ValueError("No observed product state change")
    if not all(isinstance(x, str) and x.strip() for x in
               (action.get("semanticGoal"), changed.get("evidence"))):
        raise ValueError("Missing real action intent or observed result")
    action_t, result_t = action.get("t"), changed.get("t")
    if (type(action_t) not in (int, float)
        or type(result_t) not in (int, float)
        or not all(math.isfinite(x) for x in (action_t, result_t))
        or not 0 <= result_t-action_t <= 3.0):
        raise ValueError("Action and result are out of the verified capture clock")
    a = _rect(action.get("targetRect"), width, height)
    b = _rect(changed.get("resultRect"), width, height)
    return a, b


def measure(before: np.ndarray, after: np.ndarray, proof: dict) -> dict:
    """Compute robust, bounded visible change in actual unaltered screenshots.

    Pixel-motion evidence cannot determine taste, value or cinematography.
    Coordinates in proof are SOURCE IMAGE pixels, not CSS pixels.
    """
    if (not isinstance(before, np.ndarray) or not isinstance(after, np.ndarray)
        or before.ndim != 3 or before.shape != after.shape
        or before.shape[2] != 3 or before.dtype != np.uint8
        or after.dtype != np.uint8
        or min(before.shape[:2]) < 360):
        raise ValueError("Need matching real RGB/BGR 8-bit browser screenshots")
    height, width = before.shape[:2]
    action, result = _verified_event(proof, width, height)
    source = proof.get("source_url")
    if not isinstance(source, str) or urlsplit(source).scheme not in ("http", "https"):
        raise ValueError("Missing identifiable product source URL")
    if not urlsplit(source).netloc:
        raise ValueError("Missing identifiable product host")
    # Retain source-local geometric evidence; the rollup is not a video quality score.
    first = cv2.resize(before, SAMPLE, interpolation=cv2.INTER_AREA)
    second = cv2.resize(after, SAMPLE, interpolation=cv2.INTER_AREA)
    # A small Gaussian suppresses subpixel antialias/flicker without
    # removing genuine major color, graphic and layout transformations.
    first = cv2.GaussianBlur(first, (3, 3), 0)
    second = cv2.GaussianBlur(second, (3, 3), 0)
    delta = np.max(cv2.absdiff(first, second), axis=2)
    active = delta > 28
    rx, ry, rw, rh = result
    x0 = max(0, int(math.floor(rx/width*SAMPLE[0])))
    x1 = min(SAMPLE[0], int(math.ceil((rx+rw)/width*SAMPLE[0])))
    y0 = max(0, int(math.floor(ry/height*SAMPLE[1])))
    y1 = min(SAMPLE[1], int(math.ceil((ry+rh)/height*SAMPLE[1])))
    region = active[y0:y1, x0:x1]
    if region.size < 16:
        raise ValueError("Result region is too small to assess")
    result_area = (rw*rh)/(width*height)
    changed_whole = float(active.mean())
    changed_result = float(region.mean())
    # Distinct identifiers: tool cannot accept a different source or a synthetic
    # source preview later by claiming these filenames refer to the same pixels.
    issues = []
    rights = proof.get("rights")
    if rights not in ("verified_internal_qa", "approved_public_demo"):
        issues.append("SOURCE_RIGHTS_NOT_VERIFIED")
    if result_area < MIN_RESULT_FRAME_FRACTION:
        issues.append("RESULT_TOO_SMALL_FOR_SHORT_SILENT_FILM")
    if (changed_whole < MIN_CHANGED_FRAME_FRACTION or
        changed_result < MIN_CHANGED_RESULT_FRACTION):
        issues.append("WEAK_VISIBLE_TRANSFORMATION")
    report = {
        "schema": "sauce-story-viability-preflight-v1",
        "source_url": source,
        "right_to_use": rights,
        "size": [width, height],
        "action_kind": proof["action"]["kind"],
        "outcome_kind": proof["result"]["kind"],
        "action_t": proof["action"]["t"],
        "result_t": proof["result"]["t"],
        "action_rect": action,
        "result_rect": result,
        "result_fraction_of_frame": round(result_area, 5),
        "changed_fraction_of_frame": round(changed_whole, 5),
        "changed_fraction_inside_result": round(changed_result, 5),
        "issues": issues,
        "decision": "reject_source_before_video" if issues else
                    "candidate_first_three_seconds_only",
        "premium_film_approved": False,
        "human_critic_required": True,
        "scope": "Opt-in, visually transformative short product demos; "
                 "subtle text changes can still work with different editorial treatment.",
    }
    return report


def inspect_paths(before: Path, after: Path, proof: dict) -> dict:
    a = cv2.imread(str(before), cv2.IMREAD_COLOR)
    b = cv2.imread(str(after), cv2.IMREAD_COLOR)
    if a is None or b is None:
        raise ValueError("Could not decode genuine before/after browser screenshots")
    result = measure(a, b, proof)
    result["before_sha256"] = hashlib.sha256(before.read_bytes()).hexdigest()
    result["after_sha256"] = hashlib.sha256(after.read_bytes()).hexdigest()
    return result



def validate_preview_admission(report: dict, manifest: dict,
                               max_frames: int | None, opening_study: bool) -> None:
    """Enforce a real screenshot-admitted three-second EDL study only.

    This never signs off a full film. An independently directed full video
    requires a separate human creative decision not represented here.
    """
    if not isinstance(report, dict) or report.get("schema") != "sauce-story-viability-preflight-v1":
        raise ValueError("Missing verifiable pre-render story review")
    if (report.get("decision") != "candidate_first_three_seconds_only"
        or report.get("issues") != []
        or report.get("premium_film_approved") is not False
        or report.get("human_critic_required") is not True
        or report.get("right_to_use") not in ("verified_internal_qa", "approved_public_demo")):
        raise ValueError("Story preflight did not permit a review candidate")
    if type(max_frames) is not int or not 30 <= max_frames <= 180 or opening_study is not True:
        raise ValueError("Preflight grants only a three-second opening study, not a full render")
    for key in ("before_sha256", "after_sha256"):
        value = report.get(key)
        if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise ValueError("Missing actual browser-frame provenance")
    if not isinstance(manifest, dict):
        raise ValueError("Missing capture manifest")
    source = manifest.get("source_url") or manifest.get("url") or manifest.get("source")
    if not isinstance(source, str) or not source:
        raise ValueError("Cannot match preflight to original product source")
    from urllib.parse import urlsplit
    a, b = urlsplit(source), urlsplit(report.get("source_url", ""))
    if (a.scheme, a.netloc.lower(), a.path.rstrip("/")) != (
        b.scheme, b.netloc.lower(), b.path.rstrip("/")):
        raise ValueError("Preflight source and captured product do not match")
    # A forged or stale report cannot be replayed for a different interaction.
    events = manifest.get("events")
    if not isinstance(events, list):
        raise ValueError("No source-verified interaction events")
    actions = [e for e in events if isinstance(e, dict) and
               e.get("kind") == report.get("action_kind") and
               e.get("t") == report.get("action_t")]
    results = [e for e in events if isinstance(e, dict) and
               e.get("kind") == "state_change" and
               e.get("t") == report.get("result_t") and
               isinstance(e.get("evidence"), str) and e["evidence"].strip()]
    if not actions or not results:
        raise ValueError("Preflight action/result is absent from the true source clock")
    try:
        result = tuple(float(results[0]["resultRect"][k]) for k in ("x", "y", "width", "height"))
        candidate = report["result_rect"]
        if not isinstance(candidate, (tuple, list)) or len(candidate) != 4:
            raise ValueError("Invalid source result geometry receipt")
        measured = tuple(float(x) for x in candidate)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Preflight has malformed result geometry") from exc
    if (not all(math.isfinite(v) for v in (*result, *measured))
        or any(abs(a-b) > 0.01 for a, b in zip(result, measured))):
        raise ValueError("Preflight result geometry differs from captured product")

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--before", required=True, type=Path)
    p.add_argument("--after", required=True, type=Path)
    p.add_argument("--evidence", required=True, type=Path)
    p.add_argument("--out", type=Path)
    a = p.parse_args()
    try:
        report = inspect_paths(a.before, a.after, json.loads(a.evidence.read_text()))
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"decision": "reject_source_before_video",
                          "error": type(exc).__name__ + ": " + str(exc),
                          "premium_film_approved": False}))
        return 2
    if a.out:
        a.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["decision"] == "candidate_first_three_seconds_only" else 3


if __name__ == "__main__":
    raise SystemExit(main())
