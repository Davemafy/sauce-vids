"""The reference is creative metadata, never authorization to invent product footage."""
import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from reference_director_packet import load_reference, build_director_packet


@pytest.fixture
def recipe():
    return load_reference(ROOT / "references/arcade-stack-by-ramp.reference.json")


@pytest.fixture
def capture():
    return {
        "duration": 8.6,
        "events": [
            {"kind": "slider_change", "t": 3.45,
             "evidence": "Real slider changed price from $20 to $35",
             "targetRect": {"x": 300, "y": 300, "width": 500, "height": 25},
             "resultRect": {"x": 360, "y": 610, "width": 200, "height": 80},
             "componentRect": {"x": 310, "y": 490, "width": 300, "height": 520},
             "price_change": {"before": "$20", "after": "$35"}},
            {"kind": "interaction_complete", "t": 6},
        ],
        "source_url": "https://private-example.invalid/secret?key=TOKEN",
    }


def packet(recipe, capture):
    return build_director_packet(recipe, capture, "1" * 64, "2" * 64,
        "Show the real pricing slider and resulting change", 8, 1920, 1080,
        research_only=True)


def test_actual_reference_recipe_has_grounded_frames(recipe):
    assert recipe["source"]["sha256"] == (
        "7d22a17f97d3183cae73df90321f7be7943006d9bf7f4ecd7c2a79f15215bbbf"
    )
    assert recipe["source"]["mediaRights"] == "analysis-only"
    assert len(recipe["observedFrames"]) >= 10
    assert not recipe["review"]["cutTimesMeasured"]
    assert not recipe["review"]["exactPixelRecreationPermitted"]


def test_packet_uses_actual_source_geometry_but_never_reference_product_pixels(recipe, capture):
    result = packet(recipe, capture)
    text = json.dumps(result)
    assert result["schema"] == "sauce-director-packet-v1"
    assert "event:0:component" in result["actualCapture"]["verifiedEvents"][0]["allowedAnchors"]
    assert "event:0:result" in result["actualCapture"]["verifiedEvents"][0]["allowedAnchors"]
    assert result["actualCapture"]["verifiedEvents"][0]["resultObservedAt"] == 3.45
    assert len(result["actualCapture"]["verifiedEvents"]) == 1
    assert '"price_change"' not in text
    assert "secret" not in text and "TOKEN" not in text
    assert "arcade.software" not in text
    assert "Stack by Ramp" not in text
    assert "arcade-stack-by-ramp" not in text
    assert len(result["referenceGrammar"]["recipeFingerprint"]) == 16
    assert result["constraints"]["source_truth_from_capture_only"]


def test_unverified_event_grants_no_model_anchor(recipe, capture):
    capture["events"][0]["evidence"] = ""
    with pytest.raises(ValueError, match="No externally shareable"):
        packet(recipe, capture)


def test_missing_component_does_not_grant_component_anchor(recipe, capture):
    capture["events"][0].pop("componentRect")
    anchors = packet(recipe, capture)["actualCapture"]["verifiedEvents"][0]["allowedAnchors"]
    assert "event:0:component" not in anchors
    assert "event:0:result" in anchors


def test_offscreen_component_is_rejected_from_anchor_list(recipe, capture):
    capture["events"][0]["componentRect"]["height"] = 1200
    anchors = packet(recipe, capture)["actualCapture"]["verifiedEvents"][0]["allowedAnchors"]
    assert "event:0:component" not in anchors


def test_reference_cannot_claim_unmeasured_exact_cuts(recipe, tmp_path):
    bogus = copy.deepcopy(recipe)
    bogus["review"]["cutTimesMeasured"] = True
    p = tmp_path / "bogus.json"
    p.write_text(json.dumps(bogus))
    with pytest.raises(ValueError, match="Unmeasured cuts"):
        load_reference(p)


def test_reference_requires_explicit_no_copy_restrictions(recipe, tmp_path):
    bogus = copy.deepcopy(recipe)
    bogus["transfer"]["neverTransfer"] = []
    p = tmp_path / "bogus.json"
    p.write_text(json.dumps(bogus))
    with pytest.raises(ValueError, match="copyright/source-truth"):
        load_reference(p)


def test_no_manufactured_capture_hashes(recipe, capture):
    with pytest.raises(ValueError, match="SHA256-pinned"):
        build_director_packet(recipe, capture, "unverified", "2" * 64,
            "Show verified result", 8, 1920, 1080)


def test_source_evidence_must_use_finite_timestamp(recipe, capture):
    capture["events"][0]["t"] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        packet(recipe, capture)


def test_manifest_not_sent_with_unapproved_user_data(recipe, capture):
    capture["privateOwner"] = {"name": "DO NOT EXPORT"}
    result = packet(recipe, capture)
    assert "DO NOT EXPORT" not in json.dumps(result)


def test_requested_duration_cannot_exceed_actual_source(recipe, capture):
    with pytest.raises(ValueError, match="exceeds verified source"):
        build_director_packet(recipe, capture, "1" * 64, "2" * 64,
            "Show verified result", 12, 1920, 1080)


def test_manifest_requires_source_duration(recipe, capture):
    capture.pop("duration")
    with pytest.raises(ValueError, match="verified source duration"):
        packet(recipe, capture)


def test_evidence_timestamp_cannot_exceed_source_duration(recipe, capture):
    capture["events"][0]["t"] = 9.1
    with pytest.raises(ValueError, match="finite"):
        packet(recipe, capture)


def test_analysis_only_reference_rejected_for_production_packet(recipe, capture):
    with pytest.raises(ValueError, match="production Gemini packet blocked"):
        build_director_packet(recipe, capture, "1"*64, "2"*64,
            "Demonstrate verified pricing action", 8, 1920, 1080)


def test_false_claim_of_verified_reference_cannot_bypass_gate(recipe, tmp_path):
    claimed=copy.deepcopy(recipe)
    claimed["review"]["fidelityTier"]="verified_1to1"
    claimed["review"]["oneToOneEngineMatch"]=True
    path=tmp_path/"false-claim.json"
    path.write_text(json.dumps(claimed))
    with pytest.raises(ValueError, match="independently verified render-match"):
        load_reference(path)


def test_research_packet_explicitly_not_production_eligible(recipe, capture):
    p=packet(recipe, capture)
    assert p["constraints"]["productionGeminiEligible"] is False
    assert p["constraints"]["reference_fidelity"]=="analysis_only"
