"""Evidence, reachability and non-execution gates for conversational Sauce."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"scripts"))
from conversation_director_experiment import validate_compilation
from compile_conversation_capture import normalize_route
from session_replay import replay


def control(id,text,kind="link",href=None,classification="read_only_navigation"):
    return {"id":id,"text":text,"kind":kind,"href":href,
            "policy":{"class":classification,
                      "auto_execute":classification=="read_only_navigation",
                      "requires_authorization":classification!="read_only_navigation"}}


def product_report():
    origin="https://example.test/"
    return {
        "requested_url":origin,
        "pages":[
            {"id":"p0","url":origin,"title":"Example", "headings":[],
             "text":"RECORDED EVALUATION Source model 24/24 Replacement 13/24 With adaptation 24/24. Open workspace. See the evidence.",
             "controls":[control("p0:a1","See the evidence",href=origin+"#evidence"),
                         control("p0:a18","Open workspace",href=origin+"app")]},
            {"id":"p1","url":origin+"app","title":"Workspace", "headings":[],
             "text":"Run refund agent. Workspace overview. Evidence.",
             "controls":[control("p1:a0","Run refund agent","button",
                                 classification="costly_or_nondeterministic"),
                         control("p1:a6","Evidence",href=origin+"app/evidence")]},
            {"id":"p3","url":origin+"app/evidence","title":"Evidence", "headings":[],
             "text":"Review recorded executions and independent verification.",
             "controls":[]},
        ]
    }


def sample_plan():
    return {
        "schema":"sauce-conversation-capture-plan-v1",
        "title":"Evidence-first product film","format":"landscape_1920x1080_60",
        "hook":{"page_id":"p0","quote":"Replacement 13/24"},
        "steps":[
            {"type":"navigate","page_id":"p0","control_id":"p0:a1","quote":"See the evidence","purpose":"Open benchmark"},
            {"type":"inspect","page_id":"p0","control_id":None,"quote":"Replacement 13/24","purpose":"Read historical result"},
            {"type":"navigate","page_id":"p0","control_id":"p0:a18","quote":"Open workspace","purpose":"Show workspace"},
            {"type":"propose_action","page_id":"p1","control_id":"p1:a0","quote":"Run refund agent","purpose":"Needs owner authorization"},
            {"type":"navigate","page_id":"p1","control_id":"p1:a6","quote":"Evidence","purpose":"Read archived run"},
            {"type":"inspect","page_id":"p3","control_id":None,"quote":"Review recorded executions","purpose":"Inspect run"},
        ],
        "core_claims":[{"page_id":"p0","quote":"Replacement 13/24",
                        "provenance":"site_recorded"}],
        "fallback":"Recorded evidence only",
        "narration_mode":"draft_only",
    }


class ConversationalDirectorTests(unittest.TestCase):
    def test_real_same_origin_page_order_is_grounded(self):
        p=validate_compilation(sample_plan(),product_report())
        self.assertTrue(p["steps"][0]["may_execute"])
        self.assertEqual(p["steps"][3]["action_class"],"costly_or_nondeterministic")
        self.assertFalse(p["steps"][3]["may_execute"])
        self.assertFalse(p["action_execution_authorized"])
        self.assertFalse(p["live_product_execution_verified"])
        self.assertEqual(p["story_type"],"recorded_results_showcase")

    def test_anchor_fragment_does_not_teleport_into_application(self):
        plan=sample_plan()
        plan["steps"][2]={"type":"inspect","page_id":"p3","control_id":None,
                          "quote":"Review recorded executions","purpose":"Wrong destination"}
        with self.assertRaisesRegex(ValueError,"Unreachable page"):
            validate_compilation(plan,product_report())

    def test_an_app_link_is_not_an_authorization_to_run(self):
        plan=sample_plan()
        plan["steps"][3]["type"]="navigate"
        with self.assertRaisesRegex(ValueError,"unapproved navigation"):
            validate_compilation(plan,product_report())

    def test_invalid_source_quote_and_element_are_rejected(self):
        plan=sample_plan()
        plan["steps"][1]["quote"]="The live patched model hit all tests."
        with self.assertRaisesRegex(ValueError,"Unobserved quote"):
            validate_compilation(plan,product_report())
        plan=sample_plan()
        plan["steps"][3]["control_id"]="p1:unseen404"
        with self.assertRaisesRegex(ValueError,"Imagined interactive"):
            validate_compilation(plan,product_report())

    def test_recording_claim_without_label_is_downgraded(self):
        report=product_report()
        report["pages"][0]["text"]=report["pages"][0]["text"].replace("RECORDED EVALUATION ","")
        plan=sample_plan()
        compiled=validate_compilation(plan,report)
        self.assertEqual(compiled["story_type"],"public_website_showcase_only")
        self.assertEqual(compiled["core_claims"][0]["provenance"],"site_claim")
        self.assertTrue(compiled["core_claims"][0]["downgraded_unverified_recording"])

    def test_a_safe_link_misclassified_as_costly_is_never_promoted_to_click(self):
        plan=sample_plan()
        plan["steps"][0]["type"]="propose_action"
        compiled=validate_compilation(plan,product_report())
        self.assertEqual(compiled["steps"][0]["type"],"inspect")
        self.assertFalse(compiled["steps"][0]["may_execute"])

    def test_first_frame_hook_must_be_on_start_page(self):
        plan=sample_plan()
        plan["hook"]={"page_id":"p3","quote":"Review recorded executions"}
        with self.assertRaisesRegex(ValueError,"First-frame hook"):
            validate_compilation(plan,product_report())

    def test_cursorless_source_rejects_regular_presentation(self):
        with self.assertRaisesRegex(ValueError,"Cursorless source"):
            replay(Path("unused"),Path("unused"),Path("unused"),
                   presentation_v15=True,cursorless_source=True)

    def test_route_strips_only_fragment_not_origin(self):
        self.assertEqual(normalize_route("https://example.test/#evidence"),
                         normalize_route("https://example.test/"))
        self.assertNotEqual(normalize_route("https://example.test/app/evidence"),
                            normalize_route("https://example.test/#evidence"))


if __name__=="__main__":
    unittest.main()
