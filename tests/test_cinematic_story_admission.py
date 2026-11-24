"""Cinematic mode requires real, substantial public-browser evidence before capture.

Tests for this narrow opt-in fail-closed behavior do not claim a premium film.
"""
from __future__ import annotations
import copy
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.url_engine import require_cinematic_story_proof,execute

HASH="a"*64
PLAN={"mode":"interactive","action_ids":["a1"],"heading_ids":[],
      "title":"Real demo","reason":"observed"}
REPORT={"url":"https://example.com/demo","controls":[
    {"id":"a1","kind":"button","text":"Show real result",
     "selector":"button#real","in_form":False,"controlled_panel":True}]}
PROOF={"schema":"sauce-source-action-preflight-v1",
       "decision":"visible_outcome_candidate",
       "source_control_id":"a1","control_kind":"button",
       "source_url":"https://example.com/demo",
       "before_sha256":HASH,"steady_sha256":HASH,"after_sha256":HASH,
       "change_above_baseline":.087,"observable_dom_change":True,
       "viewport_shift_px":0.0,"result_area_fraction":.155,
       "changed_result_fraction":.56,
       "result_rect":{"x":440,"y":180,"width":400,"height":360},
       "human_film_approval":False}


class CinematicStoryAdmission(unittest.TestCase):
    def test_valid_browser_action_admitted_only_as_candidate(self):
        self.assertIs(require_cinematic_story_proof(PLAN,REPORT,PROOF),PLAN)

    def test_no_hero_marketing_showcase_fallback(self):
        with self.assertRaisesRegex(RuntimeError,"single real product"):
            require_cinematic_story_proof({**PLAN,"mode":"showcase"},REPORT,PROOF)

    def test_small_visual_change_rejected_even_with_dom_change(self):
        proof={**PROOF,"change_above_baseline":.006}
        with self.assertRaisesRegex(RuntimeError,"too small"):
            require_cinematic_story_proof(PLAN,REPORT,proof)

    def test_large_film_requires_matching_control_and_exact_source(self):
        for key,value in (("source_control_id","irrelevant"),
                          ("control_kind","slider"),
                          ("source_url","https://other.example.com/"),
                          ("source_url","http://example.com/demo")):
            with self.subTest(key=key):
                with self.assertRaises(RuntimeError):
                    require_cinematic_story_proof(PLAN,REPORT,{**PROOF,key:value})

    def test_rejected_or_forged_source_proof_fails_closed(self):
        for proof in (
            {"decision":"visible_outcome_candidate"},
            {**PROOF,"decision":"no_proven_visible_outcome"},
            {**PROOF,"before_sha256":"not-a-hash"},
            {**PROOF,"change_above_baseline":float("nan")},
            {**PROOF,"human_film_approval":True},
            {**PROOF,"change_above_baseline":True},
            {**PROOF,"viewport_shift_px":9.0},
            {**PROOF,"viewport_shift_px":None},
            {**PROOF,"result_area_fraction":.002},
            {**PROOF,"changed_result_fraction":.001},
            {**PROOF,"result_rect":None},
        ):
            with self.subTest(proof=proof):
                with self.assertRaises(RuntimeError):
                    require_cinematic_story_proof(PLAN,REPORT,proof)

    def test_premium_showcase_is_rejected_before_capture(self):
        with tempfile.TemporaryDirectory(prefix="sauce-cinematic-reject-") as tmp:
            plan={**PLAN,"mode":"showcase"}
            with (patch.dict(os.environ,{"SAUCE_CINEMATIC_ONLY":"1","GEMINI_API_KEY":""}),
                  patch("backend.url_engine.validate_public_url"),
                  patch("backend.url_engine.inspect",return_value=REPORT),
                  patch("backend.url_engine.direction",return_value=(plan,0,"local")),
                  patch("backend.url2video.previous_feedback",return_value=[]),
                  patch("backend.url_engine.captured") as captured):
                with self.assertRaisesRegex(RuntimeError,"verified public product interaction"):
                    execute(REPORT["url"],Path(tmp))
                captured.assert_not_called()

    def test_premium_mode_always_probes_real_action(self):
        # Missing optional SAUCE_VERIFY_VISIBLE_ACTION must not disable the
        # public action probe for explicit cinematic captures.
        with tempfile.TemporaryDirectory(prefix="sauce-cinematic-probe-") as tmp:
            env={"SAUCE_CINEMATIC_ONLY":"1","SAUCE_VERIFY_VISIBLE_ACTION":"0",
                 "GEMINI_API_KEY":""}
            with (patch.dict(os.environ,env),
                  patch("backend.url_engine.validate_public_url"),
                  patch("backend.url_engine.inspect",return_value=REPORT),
                  patch("backend.url_engine.direction",return_value=(PLAN,0,"local")),
                  patch("backend.url_engine.workflow",return_value=[]),
                  patch("backend.url2video.previous_feedback",return_value=[]),
                  patch("backend.source_action_preflight.probe_public_action",
                        return_value={**PROOF,"change_above_baseline":.009}) as probe,
                  patch("backend.url_engine.captured") as captured):
                with self.assertRaisesRegex(RuntimeError,"too small"):
                    execute(REPORT["url"],Path(tmp))
                self.assertEqual(probe.call_count,1)
                captured.assert_not_called()

    def test_premium_does_not_downgrade_malformed_selector_to_showcase(self):
        with tempfile.TemporaryDirectory(prefix="sauce-cinematic-selector-") as tmp:
            with (patch.dict(os.environ,{"SAUCE_CINEMATIC_ONLY":"1","GEMINI_API_KEY":""}),
                  patch("backend.url_engine.validate_public_url"),
                  patch("backend.url_engine.inspect",return_value=REPORT),
                  patch("backend.url_engine.direction",return_value=(PLAN,0,"local")),
                  patch("backend.url_engine.workflow",return_value=[{"action":"hover"}]),
                  patch("backend.url_engine.preflight",return_value=[]),
                  patch("backend.url2video.previous_feedback",return_value=[]),
                  patch("backend.source_action_preflight.probe_public_action") as probe):
                with self.assertRaisesRegex(RuntimeError,"selector preflight"):
                    execute(REPORT["url"],Path(tmp))
                probe.assert_not_called()


if __name__=="__main__":
    unittest.main()



class SourceViewportProof(unittest.TestCase):
    def test_scroll_before_click_no_longer_scores_as_product_payoff(self):
        from backend.source_action_preflight import viewport_shift_px
        a={"x":0,"y":800};b={"x":0,"y":800}
        box={"x":310,"y":260,"width":420,"height":80}
        self.assertEqual(viewport_shift_px(a,b,box,box),0.0)
        with self.assertRaisesRegex(RuntimeError,"viewport"):
            require_cinematic_story_proof(
                PLAN,REPORT,{**PROOF,"viewport_shift_px":35.})

    def test_actual_scroll_or_nested_scroller_shift_is_detected(self):
        from backend.source_action_preflight import viewport_shift_px
        a={"x":0,"y":250};b={"x":0,"y":900}
        box={"x":310,"y":260,"width":420,"height":80}
        self.assertEqual(viewport_shift_px(a,b,box,box),650.)
        self.assertEqual(viewport_shift_px(
            {"x":0,"y":0},{"x":0,"y":0},box,{**box,"y":510}),250.)

    def test_missing_viewport_geometry_fails_closed(self):
        from backend.source_action_preflight import viewport_shift_px
        with self.assertRaises(ValueError):
            viewport_shift_px({"x":0}, {"x":0,"y":0}, {"x":0,"y":0},
                              {"x":0,"y":0})



class SourceLocalVisualDelta(unittest.TestCase):
    def test_genuine_panel_occupies_measurable_view_and_changes(self):
        import numpy as np
        from backend.source_action_preflight import measured_result_region
        before=np.full((720,1280,3),40,dtype=np.uint8)
        after=before.copy()
        after[180:540,440:840,:]=210
        result=measured_result_region(
            before,after,{"x":440,"y":180,"width":400,"height":360})
        self.assertAlmostEqual(result["result_area_fraction"],.15625)
        self.assertGreater(result["changed_result_fraction"],.95)

    def test_fullscreen_overlay_does_not_qualify_tiny_modal(self):
        import numpy as np
        from backend.source_action_preflight import measured_result_region
        before=np.full((720,1280,3),200,dtype=np.uint8)
        after=np.full_like(before,70)
        after[250:275,500:525]=255
        result=measured_result_region(
            before,after,{"x":500,"y":250,"width":25,"height":25})
        self.assertLess(result["result_area_fraction"],.005)
        with self.assertRaisesRegex(RuntimeError,"result region"):
            require_cinematic_story_proof(
                PLAN,REPORT,{**PROOF,**result})

    def test_missing_semantic_result_does_not_admit_background_motion(self):
        from backend.source_action_preflight import measured_result_region
        import numpy as np
        before=np.full((720,1280,3),20,dtype=np.uint8)
        after=np.full((720,1280,3),230,dtype=np.uint8)
        result=measured_result_region(before,after,None)
        with self.assertRaisesRegex(RuntimeError,"result region"):
            require_cinematic_story_proof(PLAN,REPORT,{**PROOF,**result})
