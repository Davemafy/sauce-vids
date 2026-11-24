import json
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from pathlib import Path

import cv2
import numpy as np

from backend.outcome_editorial_gate import checked_decision, evaluate, sha


class OutcomeEditorialGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.pair = {"id":"a1","label":"Preview"}
        for name, value in (("before", 0), ("after", 150)):
            path = self.root / (name + ".png")
            cv2.imwrite(str(path), np.full((120,160,3), value, np.uint8))
            self.pair[name] = path
            self.pair[name+"_sha256"] = sha(path.read_bytes())

    def decision(self, status="core_visible", decision="admit", selected="a1"):
        return {"selected_id":selected,"decision":decision,"reason":"Verified preview",
                "assessment":[{"id":"a1","status":status,"evidence":"Visible layout changed"}]}

    def test_strict_decisions(self):
        self.assertIsNotNone(checked_decision(self.decision(), {"a1"}))
        for status in ("locked_or_hidden", "generic_setting", "supporting_visible", "uncertain"):
            self.assertIsNone(checked_decision(self.decision(status), {"a1"}))
        self.assertIsNone(checked_decision(self.decision(selected="a999"), {"a1"}))
        self.assertIsNone(checked_decision(self.decision(decision="abstain"), {"a1"}))
        self.assertIsNotNone(checked_decision(self.decision("locked_or_hidden","abstain",None), {"a1"}))
        self.assertIsNotNone(checked_decision(self.decision("supporting_visible","investigate",None), {"a1"}))

    def test_images_and_replay_no_duplicate_inference(self):
        calls=[]
        def request(model, contents, json_mode):
            calls.append(contents)
            return json.dumps(self.decision()), {"finishReason":"STOP"}
        result=evaluate("Test", [self.pair], self.root/"result", request=request)
        again=evaluate("Test", [self.pair], self.root/"result", request=request)
        self.assertEqual(result,again)
        self.assertEqual(result["admitted_id"], "a1")
        self.assertFalse(result["creative_approved"])
        self.assertEqual(len(calls),1)
        self.assertEqual(sum("inline_data" in x for x in calls[0][-1]["parts"]),2)

    def test_tampered_evidence_never_calls_model(self):
        self.pair["after_sha256"]="0"*64
        with self.assertRaises(ValueError):
            evaluate("Test", [self.pair], self.root/"bad", request=lambda *args: self.fail("called model"))

    def test_truncated_or_locked_decision_not_admitted(self):
        for i, (answer, finish) in enumerate(((self.decision(), "MAX_TOKENS"),
                    (self.decision("locked_or_hidden"), "STOP"))):
            result=evaluate("Test", [self.pair], self.root/str(i),
                    request=lambda *args: (json.dumps(answer), {"finishReason":finish}))
            self.assertIsNone(result["admitted_id"])

    def test_duplicate_ids_and_identical_images_rejected(self):
        with self.assertRaises(ValueError):
            evaluate("Test", [self.pair,self.pair], self.root/"dup")
        self.pair.update(after=self.pair["before"],after_sha256=self.pair["before_sha256"])
        with self.assertRaises(ValueError):
            evaluate("Test", [self.pair], self.root/"same")


    def test_rate_limit_defers_resumes_once_and_retains_history(self):
        calls=[]
        def limited(model, contents, json_mode):
            calls.append(model)
            raise HTTPError("https://example.test",429,"quota",{"Retry-After":"1800"},None)
        directory=self.root/"retry"
        with patch.dict("os.environ",{"SAUCE_DIRECTOR_MODEL":"gemini-test-a",
                                     "SAUCE_CURIOUS_FALLBACK_MODEL":"gemini-test-b"}):
            with patch("backend.outcome_editorial_gate.time.time",return_value=1000):
                first=evaluate("Test",[self.pair],directory,request=limited)
                self.assertEqual(first["state"],"provider_deferred")
                self.assertEqual(first["retry_not_before"],2800)
                self.assertIsNone(first["admitted_id"])
                self.assertEqual(len(calls),1)
            with patch("backend.outcome_editorial_gate.time.time",return_value=2799):
                self.assertEqual(evaluate("Test",[self.pair],directory,request=limited,resume=True),first)
            with patch("backend.outcome_editorial_gate.time.time",return_value=2800):
                second=evaluate("Test",[self.pair],directory,request=limited,resume=True)
                self.assertEqual(second["state"],"no_admission")
                self.assertEqual(second["round_number"],2)
                self.assertEqual(len(second["model_attempts"]),2)
            with patch("backend.outcome_editorial_gate.time.time",return_value=10000):
                self.assertEqual(evaluate("Test",[self.pair],directory,request=limited,resume=True),second)
        self.assertEqual(len(calls),2)

    def test_503_fallback_and_valid_abstention_is_terminal(self):
        calls=[]
        def request(model, contents, json_mode):
            calls.append(model)
            if len(calls)==1:
                raise HTTPError("https://example.test",503,"unavailable",{},None)
            return json.dumps(self.decision("locked_or_hidden","abstain",None)),{"finishReason":"STOP"}
        with patch.dict("os.environ",{"SAUCE_DIRECTOR_MODEL":"gemini-test-a",
                                     "SAUCE_CURIOUS_FALLBACK_MODEL":"gemini-test-b"}):
            d=self.root/"fallback"
            result=evaluate("Test",[self.pair],d,request=request)
            self.assertEqual(result["state"],"decided")
            self.assertIsNone(result["admitted_id"])
            self.assertEqual(evaluate("Test",[self.pair],d,request=request,resume=True),result)
            self.assertEqual(calls,["gemini-test-a","gemini-test-b"])

    def test_nontransient_invalid_response_never_resumes(self):
        d=self.root/"invalid"
        result=evaluate("Test",[self.pair],d,request=lambda *a: ("{}",{"finishReason":"STOP"}))
        self.assertEqual(result["state"],"no_admission")
        self.assertEqual(evaluate("Test",[self.pair],d,request=lambda *a:self.fail("retried"),resume=True),result)

    def test_provider_recovery_preserves_attempts_and_admits_only_valid_result(self):
        d=self.root/"recovery"
        def fail(*args):
            raise HTTPError("https://example.test",503,"unavailable",{},None)
        with patch.dict("os.environ",{"SAUCE_DIRECTOR_MODEL":"gemini-test-a",
                                     "SAUCE_CURIOUS_FALLBACK_MODEL":"gemini-test-a"}):
            with patch("backend.outcome_editorial_gate.time.time",return_value=1000):
                first=evaluate("Test",[self.pair],d,request=fail)
                self.assertEqual(first["state"],"provider_deferred")
            with patch("backend.outcome_editorial_gate.time.time",return_value=1900):
                second=evaluate("Test",[self.pair],d,request=lambda *a:(json.dumps(self.decision()),{"finishReason":"STOP"}),resume=True)
        self.assertEqual(second["admitted_id"],"a1")
        self.assertEqual(len(second["model_attempts"]),2)
        self.assertFalse(second["creative_approved"])


if __name__ == "__main__":
    unittest.main()
