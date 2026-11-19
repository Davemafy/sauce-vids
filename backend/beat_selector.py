"""Select a product-led story from scored public-page evidence."""
from __future__ import annotations

from .shot_scorer import _overlap

EVIDENCE_REASON = "No credible UI preview, interactive widget, or code proof found"
PRODUCT_SCORE = 25


def story_hook(candidates: list[dict]) -> dict | None:
    return next((c for c in candidates if _is_product(c)), None)


def _is_product(candidate: dict) -> bool:
    return candidate["product_evidence"] and candidate["score"] >= PRODUCT_SCORE


def select_story(url: str, candidates: list[dict], interaction: dict | None = None) -> dict:
    """Return a three-to-four beat diagnostic or a typed editorial rejection."""
    products = [c for c in candidates if _is_product(c)]
    if not products:
        return {"url": url, "status": "insufficient_product_evidence", "reason": EVIDENCE_REASON}
    hook = products[0]
    chosen = [hook]
    beats = []

    def beat(candidate, role, **details):
        beats.append({"beat_index": len(beats) + 1, "role": role,
                      "source_rect": candidate["rect"], "score": candidate["score"],
                      "reason": candidate["reason"], **details})

    beat(hook, "terminal_proof" if hook["kind"] == "code" else "product_ui")
    if interaction:
        beat(hook, "verified_interaction", interaction=interaction)
    else:
        secondary = next((c for c in products[1:] if _distinct(c, chosen)), None)
        if secondary:
            chosen.append(secondary)
            beat(secondary, "secondary_ui_preview")

    payoff_pool = [c for c in candidates if c.get("pricing") and not c["product_evidence"] or c in products]
    payoff = next((c for c in payoff_pool if _distinct(c, chosen)), None)
    if len(beats) < 2 or payoff is None:
        return {"url": url, "status": "insufficient_product_evidence",
                "reason": "Product evidence found, but there are fewer than three supported story beats",
                "beats": beats}

    chosen.append(payoff)
    beat(payoff, "pricing_card" if payoff.get("pricing") and not payoff["product_evidence"] else "workflow_proof")
    return {"url": url, "status": "ready", "beats": beats}


def _distinct(candidate: dict, chosen: list[dict]) -> bool:
    label = candidate.get("label", "").strip().casefold()
    return all(
        _overlap(candidate["rect"], prior["rect"]) <= .35
        and (not label or label != prior.get("label", "").strip().casefold())
        for prior in chosen
    )
