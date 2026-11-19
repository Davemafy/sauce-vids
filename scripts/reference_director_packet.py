"""Build a source-safe director packet for an external model (no network calls).

Reference JSON is style/shot grammar, never evidence of another site's features.
Only the actual capture event manifest grants product anchors and observed time.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

_HASH = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_BEATS = {
    "recognition", "orientation", "user_intent", "decision", "authorization",
    "plan", "execution", "work_evidence", "commit", "verified_payoff",
    "context_return", "closure"
}
_GEOMETRY = {"target": "targetRect", "result": "resultRect", "component": "componentRect"}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _finite(value, name, minimum=0, maximum=1e7):
    if type(value) not in (float, int) or not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be finite and between {minimum} and {maximum}")
    return float(value)


def load_reference(path: Path):
    recipe = json.loads(Path(path).read_text())
    if set(recipe) != {"schema", "id", "label", "source", "review", "observedFrames", "grammar", "transfer"}:
        raise ValueError("Unexpected reference recipe fields")
    if recipe["schema"] != "sauce-reference-grammar-v1":
        raise ValueError("Unknown reference recipe schema")
    if not re.fullmatch(r"[a-z0-9-]{4,90}", recipe["id"]):
        raise ValueError("Invalid reference recipe id")
    source = recipe["source"]
    if source.get("mediaRights") != "analysis-only" or source.get("directCaptureClaim") is not False:
        raise ValueError("Reference media must remain analysis-only and claim no live capture")
    if not _HASH.fullmatch(source["sha256"]):
        raise ValueError("Invalid reference media hash")
    duration = _finite(source["durationSeconds"], "reference duration", 1, 600)
    times = recipe["review"]["sampledSeconds"]
    if not isinstance(times, list) or len(times) < 3 or any(
        _finite(v, "sample time", 0, duration) != v for v in times
    ) or times != sorted(set(times)):
        raise ValueError("Sample times must be monotonic inside the reference")
    if recipe["review"].get("cutTimesMeasured") is not False or recipe["review"].get("exactPixelRecreationPermitted") is not False:
        raise ValueError("Unmeasured cuts or copyrighted pixels cannot be transferred")
    frames = recipe["observedFrames"]
    if not isinstance(frames, list) or not frames:
        raise ValueError("Reference must have actual observed frames")
    for frame in frames:
        if frame["seconds"] not in times or frame["editorialFunction"] not in _ALLOWED_BEATS:
            raise ValueError("Reference observations must be time-grounded and recognized")
        if not isinstance(frame["subject"], str) or not 8 <= len(frame["subject"]) <= 200:
            raise ValueError("Reference subject observation is missing")
    grammar = recipe["grammar"]
    if not isinstance(grammar.get("narrativeArc"), list) or not 2 <= len(grammar["narrativeArc"]) <= 12:
        raise ValueError("Reference needs a bounded narrative arc")
    transfer = recipe["transfer"]
    if not isinstance(transfer.get("neverTransfer"), list) or len(transfer["neverTransfer"]) < 3:
        raise ValueError("Reference requires explicit copyright/source-truth restrictions")
    if recipe["review"].get("fidelityTier") not in ("analysis_only", "verified_1to1"):
        raise ValueError("Reference must declare its fidelity tier explicitly")
    if recipe["review"].get("fidelityTier") == "verified_1to1":
        # Never trust a declaration alone; only allow a verified reference
        # after a separate actual render-vs-reference matching receipt and
        # human shot QA. Neither is implemented yet: fail closed.
        raise ValueError("Reference 1:1 certification requires independently verified render-match receipt")
    if recipe["review"].get("oneToOneEngineMatch") is not False:
        raise ValueError("Analysis-only reference cannot claim 1:1 engine match")
    return recipe


def _validated_rect(raw, width, height):
    if not isinstance(raw, dict) or set(raw) != {"x", "y", "width", "height"}:
        return None
    try:
        x, y, w, h = (_finite(raw[key], f"rect.{key}") for key in ("x", "y", "width", "height"))
    except ValueError:
        return None
    if w < 4 or h < 4 or x + w > width or y + h > height:
        return None
    return {"x": x, "y": y, "width": w, "height": h}


def build_director_packet(
    recipe: dict, manifest: dict, manifest_sha256: str, source_sha256: str,
    brief: str, requested_seconds: float, source_width: int, source_height: int,
    *, research_only: bool = False,
):
    """Create a compact local packet. This function never sends media or data to Gemini."""
    if not _HASH.fullmatch(source_sha256) or not _HASH.fullmatch(manifest_sha256):
        raise ValueError("Production source/manifest must be SHA256-pinned")
    seconds = _finite(requested_seconds, "requested duration", .5, 60)
    source_duration = _finite(manifest.get("duration"), "verified source duration", .5, 600)
    if seconds > source_duration:
        raise ValueError("Requested film duration exceeds verified source recording")
    width = int(_finite(source_width, "source width", 64, 10000))
    height = int(_finite(source_height, "source height", 64, 10000))
    if type(brief) is not str or not 4 <= len(brief.strip()) <= 600:
        raise ValueError("A concise customer-approved brief is required")
    events = manifest.get("events")
    if not isinstance(events, list) or not 1 <= len(events) <= 64:
        raise ValueError("Verified event sidecar is required")
    candidates = []
    for index, event in enumerate(events):
        if not isinstance(event, dict) or not isinstance(event.get("kind"), str):
            continue
        t = _finite(event.get("t"), f"event {index} time", 0, source_duration)
        # Do not forward source text, usernames, URLs, screenshots, arbitrary
        # DOM contents or reference-film original branding to model endpoints.
        rectangles = {}
        for anchor, key in _GEOMETRY.items():
            rect = _validated_rect(event.get(key), width, height)
            if rect is not None:
                rectangles[anchor] = rect
        observed = bool(isinstance(event.get("evidence"), str) and event["evidence"].strip())
        allowed = []
        if observed:
            for anchor in ("target", "result", "component"):
                if anchor in rectangles:
                    allowed.append(f"event:{index}:{anchor}")
            if "target" in rectangles and "result" in rectangles:
                allowed.append(f"event:{index}:group")
        if allowed:
            candidates.append({
                "index": index, "kind": event["kind"][:70], "resultObservedAt": t,
                "allowedAnchors": allowed, "rectangles": rectangles,
            })
    if not candidates:
        raise ValueError("No externally shareable verified events or anchors")
    # The original 15-frame Arcade recipe was NOT a 1:1 reconstruction.
    # It must never quietly become production model context.
    if not research_only:
        raise ValueError("Reference 1:1 match is unverified: production Gemini packet blocked")
    # Explicit research mode only; never claim a deployable Gemini prompt.
    # Absolute reference video times are *not* copied into the new product plan.
    return {
        "schema": "sauce-director-packet-v1",
        "goal": "Output a new source-verified sauce-film-plan-v1, never a copy of the reference.",
        "customerBrief": brief.strip(),
        "requestedSeconds": seconds,
        "actualCapture": {
            "sourceSha256": source_sha256, "manifestSha256": manifest_sha256,
            "sourceWidth": width, "sourceHeight": height,
            "sourceDurationSeconds": source_duration,
            "verifiedEvents": candidates,
        },
        "referenceGrammar": {
            "recipeFingerprint": hashlib.sha256(
                json.dumps(recipe["grammar"], sort_keys=True).encode()
            ).hexdigest()[:16],
            "narrativeArc": recipe["grammar"]["narrativeArc"],
            "focalHierarchy": recipe["grammar"]["focalHierarchy"],
            "framing": recipe["grammar"]["framing"],
            "pacing": recipe["grammar"]["pacing"],
            "transitionLogic": recipe["grammar"]["transitionLogic"],
            "cursorPolicy": recipe["grammar"]["cursorPolicy"],
            "finalState": recipe["grammar"]["finalState"],
            "omitWhenUnverified": recipe["transfer"]["omitWhenUnverified"],
            "neverTransfer": recipe["transfer"]["neverTransfer"],
        },
        "constraints": {
            "style_only_reference": True, "reference_fidelity": "analysis_only",
            "productionGeminiEligible": False, "source_truth_from_capture_only": True,
            "future_result_anchors_forbidden": True, "original_ui_pixels_only": True,
            "output_film_plan_schema": "sauce-film-plan-v1",
            "requires_local_strict_validation_before_render": True,
        },
    }


def main():
    ap = argparse.ArgumentParser(description="Build analysis-only Sauce direction packet; blocked for Gemini production")
    ap.add_argument("--reference", type=Path, required=True)
    ap.add_argument("--research-only", action="store_true",
                    help="Explicitly permit unverified editorial reference for local QA; never production")
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--brief", required=True)
    ap.add_argument("--seconds", type=float, default=10)
    ap.add_argument("--width", type=int, required=True)
    ap.add_argument("--height", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    recipe = load_reference(args.reference)
    manifest = json.loads(args.manifest.read_text())
    packet = build_director_packet(
        recipe, manifest, _sha256(args.manifest), _sha256(args.source),
        args.brief, args.seconds, args.width, args.height,
        research_only=args.research_only,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(packet, indent=2) + "\n")
    print(f"Created RESEARCH-ONLY director packet for {len(packet['actualCapture']['verifiedEvents'])} verified events")
    print("Not sent to any external model; no film rendered or creatively approved.")


if __name__ == "__main__":
    main()
