"""Fail-closed self-repair planning from observed footage, never fabricated UI."""
from dataclasses import replace

import pytest

from backend.url_film_quality import assess_url_film
from backend.url_film_recovery import plan_repair, MAX_REPAIR_ATTEMPTS


def captured_nav_only():
    inspection = {
        "url": "https://cmokit.co/",
        "controls": [
            {"id": "a3", "kind": "link", "href": "https://cmokit.co/#how"},
            {"id": "a4", "kind": "link", "href": "https://cmokit.co/#pricing"},
        ],
        "headings": [{"id": "h0", "text": "The CMO your startup can afford"}],
    }
    scenes = [
        {"actionId": None, "startMs": 0,
         "focusBox": {"width": 760, "height": 180}},
        {"actionId": "a3", "startMs": 7515.62, "actualAction": "click",
         "focusBox": {"width": 82, "height": 21.59}, "transitionVerified": True},
        {"actionId": None, "startMs": 15040,
         "focusBox": {"width": 230.66, "height": 22.39}},
        {"actionId": "a4", "startMs": 22555.18, "actualAction": "click",
         "focusBox": {"width": 44, "height": 21.59}, "transitionVerified": True},
    ]
    return inspection, scenes


def test_actual_cmokit_defect_rewrites_source_plan_not_claimed_features():
    inspection, scenes = captured_nav_only()
    assessment = assess_url_film(
        inspection, scenes, source_size=(1280, 720), source_fps=25)
    decision = plan_repair(inspection, scenes, assessment)
    assert decision.status == "draft_required"
    assert decision.film_kind == "public-website-showcase"
    assert decision.attempt == 1
    assert decision.draft_seconds == 3
    assert decision.requires_human_review
    assert not decision.allow_paid_ai_retry
    assert not decision.can_claim_verified_product_demo
    targets = [s.source_ref for s in decision.steps
               if s.op == "resolve_destination_region_in_browser"]
    assert targets == ["how", "pricing"]
    ops = [s.op for s in decision.steps]
    assert "capture_native_dpr2" in ops
    assert "record_true_source_fps" in ops
    assert "render_three_second_storyboard_only" == ops[-1]


def test_same_failed_cut_cannot_loop_indefinitely():
    inspection, scenes = captured_nav_only()
    assessment = assess_url_film(
        inspection, scenes, source_size=(1280, 720), source_fps=25)
    same = ("navigation|tiny|late|lowres|lowfps",)
    decision = plan_repair(
        inspection, scenes, assessment, attempt=1,
        previous_failure_signatures=same,
    )
    assert decision.status == "rejected"
    assert decision.steps == ()
    assert decision.draft_seconds == 0
    assert decision.attempt == 1
    assert not decision.can_claim_verified_product_demo


def test_attempt_budget_stops_and_preserves_original():
    inspection, scenes = captured_nav_only()
    a = assess_url_film(
        inspection, scenes, source_size=(1280, 720), source_fps=25)
    d = plan_repair(inspection, scenes, a, attempt=MAX_REPAIR_ATTEMPTS)
    assert d.status == "rejected"
    assert "preserve original" in d.reasons[0]
    assert d.steps == ()


def test_true_onpage_action_can_go_to_visual_review_only():
    report = {
        "url": "https://example.org/",
        "controls": [{"id": "a0", "kind": "button", "text": "Try sample"}],
    }
    scenes = [{"actionId": "a0", "startMs": 1800,
               "actualAction": "click", "transitionVerified": True,
               "focusBox": {"width": 160, "height": 45}}]
    assessment = assess_url_film(
        report, scenes, source_size=(1920, 1080), source_fps=60)
    d = plan_repair(report, scenes, assessment)
    assert d.status == "needs_visual_review"
    assert d.film_kind == "product-demo-candidate"
    assert d.can_claim_verified_product_demo
    assert not d.allow_paid_ai_retry
    assert d.requires_human_review


def test_broken_evidence_cannot_trick_repair():
    report, scenes = captured_nav_only()
    a = assess_url_film(report, scenes, source_size=(1280, 720), source_fps=25)
    with pytest.raises(ValueError):
        plan_repair({}, scenes, a)
    with pytest.raises(ValueError):
        plan_repair(report, scenes, object())
    with pytest.raises(ValueError):
        plan_repair(report, scenes, a, attempt=-1)
    with pytest.raises(ValueError):
        plan_repair(report, scenes, a, attempt=3)


def test_absent_destination_falls_back_to_real_geometry_capture():
    report = {"url": "https://example.org/", "controls": []}
    scenes = [{"startMs": 0, "focusBox": {"width": 20, "height": 11}}]
    a = assess_url_film(report, scenes, source_size=(1920, 1080), source_fps=60)
    d = plan_repair(report, scenes, a)
    ops = [s.op for s in d.steps]
    assert "capture_safe_source_regions" in ops
    assert "resolve_destination_region_in_browser" not in ops
    assert d.film_kind == "public-website-showcase"


def test_anchor_target_must_be_verified_click():
    report, scenes = captured_nav_only()
    scenes[-1]["transitionVerified"] = False
    a = assess_url_film(report, scenes, source_size=(1280, 720), source_fps=25)
    d = plan_repair(report, scenes, a)
    targets = [s.source_ref for s in d.steps
               if s.op == "resolve_destination_region_in_browser"]
    assert targets == ["how"]


def test_provenance_unchanged_and_receipt_machine_readable():
    report, scenes = captured_nav_only()
    a = assess_url_film(report, scenes, source_size=(1280, 720), source_fps=25)
    d = plan_repair(report, scenes, a)
    receipt = d.as_receipt()
    assert receipt["source_url"] == "https://cmokit.co/"
    assert receipt["steps"][0]["op"] == "reclassify_as_public_showcase"
    assert all("fake" not in s["op"] for s in receipt["steps"])
    assert d.schema == "sauce-url-repair-v1"


def test_post_navigation_focus_is_full_section_not_original_nav_button():
    from backend.url_film_recovery import verify_visible_destination
    class Page:
        def evaluate(self, script, fragment):
            assert "getElementById" in script
            assert fragment == "how"
            return {
                "anchor": fragment,
                "viewport": {"width": 1280, "height": 720},
                "section": {"x": 0, "y": 5, "width": 1280, "height": 672},
                "headings": [{
                    "text": "Two minutes, start to first campaign.",
                    "rect": {"x": 220, "y": 150, "width": 835, "height": 58},
                    "visible": True,
                }],
            }
    shot=verify_visible_destination(Page(), "how")
    assert shot["section"]["width"] == 1280
    assert shot["headings"][0]["rect"]["width"] > 90


def test_missing_or_offscreen_destination_is_rejected():
    from backend.url_film_recovery import verify_visible_destination
    class Missing:
        def evaluate(self, script, fragment):
            return None
    class Offscreen:
        def evaluate(self, script, fragment):
            return {
                "anchor": fragment,
                "viewport": {"width": 1280, "height": 720},
                "section": {"x": 0, "y": -700, "width": 1280, "height": 450},
                "headings": [{"text": "Real evidence", "visible": True}],
            }
    with pytest.raises(ValueError):
        verify_visible_destination(Missing(), "how")
    with pytest.raises(ValueError):
        verify_visible_destination(Offscreen(), "how")
    with pytest.raises(ValueError):
        verify_visible_destination(Offscreen(), 'a#nav')
