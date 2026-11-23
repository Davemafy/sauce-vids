"""Fail-closed tests for Stagehand → source-verified native60 film bridge."""
import unittest
from copy import deepcopy
from unittest.mock import patch

from scripts.capture_stagehand_verified_native import (
    canonical_pair,exact_first_party,verify_selection,_real_result,SCHEMA)


class StagehandNativeBridgeTests(unittest.TestCase):
    def setUp(self):
        self.url = "https://example.com/"
        self.report = {"source_url":self.url,"url":self.url,"title":"Demo",
            "controls":[{"id":"a0","text":"Try sample","kind":"button",
                         "tag":"button","button_type":"button",
                         "selector":"#sample","in_form":False},
                        {"id":"a2","text":"Delete account","kind":"button",
                         "tag":"button","button_type":"button","selector":"#bad"}],
            "headings":[]}
        self.observation = {"schema":SCHEMA,"url":self.url,
            "observations":[{"description":"Try sample"}],
            "actions_executed":0,"outcome_verified":False}

    def selected(self, report=None, observation=None, url=None):
        with patch("scripts.capture_stagehand_verified_native.validate_public_url"):
            return verify_selection(report or self.report,
                                    observation or self.observation,
                                    url or self.url)

    def test_true_local_verified_id_without_model_selector(self):
        self.observation["observations"][0]["selector"]="https://attacker.test/evil"
        chosen, control = self.selected()
        self.assertEqual(chosen,"a0")
        self.assertEqual(control["selector"],"#sample")

    def test_reject_unobserved_destructive_hallucinated_actions(self):
        for description in ("Delete account","Purchase now","Unsafe fake button"):
            model=deepcopy(self.observation)
            model["observations"]=[{"description":description}]
            with self.subTest(description=description),self.assertRaises(ValueError):
                self.selected(observation=model)

    def test_scout_cannot_execute_any_actions(self):
        model=deepcopy(self.observation)
        model["actions_executed"]=1
        with self.assertRaises(ValueError):self.selected(observation=model)

    def test_redirect_not_foreign_domain_or_protocol(self):
        self.assertTrue(exact_first_party("https://example.com/","https://www.example.com/"))
        self.assertTrue(exact_first_party("https://www.example.com/","https://example.com/"))
        for redirect in ("http://example.com/","https://other.example.com/",
                         "https://evil.com/","https://example.com:444/"):
            with self.subTest(redirect=redirect):
                self.assertFalse(exact_first_party(self.url,redirect))
        self.assertNotIn("evil.example.com",canonical_pair(self.url))

    def test_wrong_source_receipts_and_untrusted_labels_refused(self):
        altered=deepcopy(self.report)
        altered["source_url"]="https://evil.com/"
        with self.assertRaises(ValueError):self.selected(report=altered)
        altered=deepcopy(self.report)
        altered["controls"][0]["id"]="invented"
        with self.assertRaises(ValueError):self.selected(report=altered)
        altered=deepcopy(self.observation);altered["schema"]="invented"
        with self.assertRaises(ValueError):self.selected(observation=altered)

    def test_result_geometry_must_be_real_and_on_screen(self):
        class Local:
            def __init__(self,box):self.box=box
            def count(self):return 1
            def nth(self, i):return self
            def bounding_box(self):return self.box
        class Page:
            def __init__(self,box):self.box=box
            def locator(self,selector):return Local(self.box)
        before={"theme":"","body":"","text":"Before"}
        after={"theme":"","body":"","text":"After"}
        rect=_real_result(Page({"x":500,"y":200,"width":400,"height":300}),
                          {},before,after)
        self.assertEqual(rect,{"x":1000.,"y":400.,"width":800.,"height":600.})
        with self.assertRaises(ValueError):
            _real_result(Page({"x":1400,"y":200,"width":400,"height":300}),
                         {},before,after)
        with self.assertRaises(ValueError):
            _real_result(Page({"x":500,"y":200,"width":400,"height":300}),
                         {},before,before)


if __name__=="__main__":
    unittest.main()
