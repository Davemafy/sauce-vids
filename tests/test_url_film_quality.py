"""Quality admission regressions: don't call anchor tours product demos."""
from backend.url_film_quality import assess_url_film


def _site():
    return {
        "url": "https://demo.example/",
        "controls": [
            {"id": "a1", "kind": "link", "href": "https://demo.example/#how"},
            {"id": "a2", "kind": "link", "href": "https://demo.example/#pricing"},
            {"id": "a3", "kind": "button", "text": "Try sample"},
        ],
    }


def _scene(action, start, focus, verified=True):
    return {
        "actionId": action,
        "startMs": start,
        "actualAction": "click" if action else "focus",
        "transitionVerified": verified,
        "focusBox": focus,
    }


def test_cmokit_navigation_only_rejected_as_product_demo():
    report = _site()
    scenes = [
        _scene(None, 0, {"width": 760, "height": 180}),
        _scene("a1", 7500, {"width": 82, "height": 21.6}),
        _scene(None, 15000, {"width": 230, "height": 22}),
        _scene("a2", 22500, {"width": 44, "height": 22}),
    ]
    outcome = assess_url_film(report, scenes, source_size=(1280, 720),
                              source_fps=25)
    assert not outcome.eligible_product_demo
    assert outcome.navigation_only
    assert outcome.actual_product_action_candidates == 0
    assert outcome.bad_camera_targets == 3
    assert outcome.opener_seconds == 7.5
    assert not outcome.source_is_native_master
    assert not outcome.source_is_native_fps
    assert len(outcome.reasons) >= 4


def test_real_on_page_action_is_only_candidate_not_quality_approval():
    scenes = [
        _scene(None, 0, {"width": 760, "height": 100}),
        _scene("a3", 2500, {"width": 230, "height": 84}),
    ]
    outcome = assess_url_film(_site(), scenes,
                              source_size=(1920, 1080), source_fps=60)
    assert outcome.eligible_product_demo
    assert outcome.actual_product_action_candidates == 1
    assert outcome.reasons == ()
    assert outcome.as_receipt()["eligible_product_demo"] is True


def test_unverified_button_does_not_count():
    outcome = assess_url_film(
        _site(), [_scene("a3", 1000, {"width": 200, "height": 100}, False)],
        source_size=(1920, 1080), source_fps=60,
    )
    assert not outcome.eligible_product_demo


def test_off_site_navigation_is_not_feature_evidence():
    report = _site()
    report["controls"].append({
        "id": "a4", "kind": "link", "href": "https://other.example/"
    })
    outcome = assess_url_film(
        report, [_scene("a4", 200, {"width": 200, "height": 100})],
        source_size=(1920, 1080), source_fps=60,
    )
    assert outcome.actual_product_action_candidates == 0
    assert not outcome.eligible_product_demo


def test_bad_camera_focus_disqualifies_even_a_changed_button():
    outcome = assess_url_film(
        _site(), [_scene("a3", 1000, {"width": 44, "height": 21})],
        source_size=(1920, 1080), source_fps=60,
    )
    assert not outcome.eligible_product_demo
    assert outcome.bad_camera_targets == 1


def test_bad_provenance_rejected():
    import pytest
    with pytest.raises(ValueError):
        assess_url_film({}, [], source_size=(1920, 1080), source_fps=60)
    with pytest.raises(ValueError):
        assess_url_film(_site(), [_scene("a3", 10, {})],
                        source_size=(0, 0), source_fps=60)
