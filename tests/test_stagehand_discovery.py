"""Fail-closed contracts for Stagehand -> Sauce public-control matching."""
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from backend.stagehand_discovery import choose_observed_action, run_stagehand_discovery, SCHEMA


class StagehandBridgeTests(unittest.TestCase):
    def setUp(self):
        self.report = {
            "url": "https://demo.example.com/", "source_url": "https://demo.example.com/",
            "title": "A Real Product",
            "headings": [{"id": "h0", "text": "Demo", "selector": "#intro"}],
            "controls": [
                {"id": "a0", "text": "Try sample", "kind": "button", "button_type": "button", "selector": "#try"},
                {"id": "a1", "text": "Delete all", "kind": "button", "button_type": "button", "selector": "#delete"},
                {"id": "a2", "text": "Try demo", "kind": "link", "href": "https://demo.example.com/demo", "selector": "#demo"},
                {"id": "a3", "text": "Share", "kind": "button", "button_type": "button", "selector": "#share"},
            ],
        }

    def hint(self, *descriptions, url=None):
        return {"schema": SCHEMA, "url": url or self.report["source_url"],
                "observations": [
                    {"description": s, "selector": "https://attacker.test/malicious"}
                    for s in descriptions
                ]}

    def test_matches_safe_exact_label_without_ai_selector(self):
        plan = choose_observed_action(self.report, self.hint("Click the Try sample button"))
        self.assertEqual(plan["action_ids"], ["a0"])
        self.assertNotIn("attacker", json.dumps(plan))
        self.assertEqual(plan["mode"], "interactive")

    def test_rejects_unsafe_and_unknown_controls(self):
        self.assertIsNone(choose_observed_action(self.report, self.hint("Click Delete all")))
        self.assertIsNone(choose_observed_action(self.report, self.hint("Purchase premium")))
        # A navigation link is not a product-state change; reject it even
        # when its observed label was supplied by a model.
        self.assertIsNone(choose_observed_action(self.report, self.hint("Send", "Try demo")))

    def test_capture_accepts_www_alias_not_a_foreign_origin(self):
        from backend.live_capture import same_canonical_public_origin
        self.assertTrue(same_canonical_public_origin(
            "https://brimble.io/", "https://www.brimble.io/"))
        self.assertTrue(same_canonical_public_origin(
            "https://www.heroui.com/", "https://heroui.com/"))
        self.assertFalse(same_canonical_public_origin(
            "https://brimble.io/", "https://evil.brimble.io/"))
        self.assertFalse(same_canonical_public_origin(
            "https://brimble.io/", "http://brimble.io/"))
        self.assertFalse(same_canonical_public_origin(
            "https://brimble.io/", "https://evil.com/"))

    def test_canonical_apex_and_www_redirects_only(self):
        from scripts.stagehand_public_discovery import first_party_hosts
        self.assertEqual(first_party_hosts("https://www.heroui.com/"),
                         ["heroui.com", "www.heroui.com"])
        self.assertNotIn("evil.heroui.com", first_party_hosts("https://heroui.com"))

    def test_rejects_wrong_url_schema_and_oversized_hints(self):
        self.assertIsNone(choose_observed_action(self.report, self.hint("Try demo", url="https://evil.test/")))
        self.assertIsNone(choose_observed_action(
            self.report, {"schema": "other", "url": self.report["url"], "observations": []}))
        self.assertIsNone(choose_observed_action(self.report, self.hint(*(["Try demo"] * 7))))

    def test_ambiguous_observation_never_picks_random_selector(self):
        self.report["controls"].append({"id": "a4", "text": "Try demo", "kind": "button",
                                         "button_type": "button", "selector": "#demo2"})
        self.assertIsNone(choose_observed_action(self.report, self.hint("Try demo")))

    def test_no_credentials_does_not_run_stagehand(self):
        with TemporaryDirectory() as td, patch.dict(
            "os.environ", {"SAUCE_STAGEHAND_DISCOVERY": "1", "GEMINI_API_KEY": "",
                           "GOOGLE_GENERATIVE_AI_API_KEY": "", "BROWSERBASE_API_KEY": ""}):
            with patch("backend.stagehand_discovery.subprocess.run") as run:
                self.assertIsNone(run_stagehand_discovery(self.report, Path(td)))
                run.assert_not_called()

    def test_private_receipt_contains_no_raw_model_selector_or_credentials(self):
        data = self.hint("Try sample")
        data["provider"] = "google"
        class Proc:
            returncode = 0
            stdout = json.dumps(data)
        with TemporaryDirectory() as td, patch.dict(
            "os.environ", {"SAUCE_STAGEHAND_DISCOVERY": "1", "GEMINI_API_KEY": "fake"},
            clear=False):
            with patch("backend.stagehand_discovery.validate_public_url"), patch("backend.stagehand_discovery.subprocess.run", return_value=Proc()) as run:
                plan = run_stagehand_discovery(self.report, Path(td))
                self.assertEqual(plan["action_ids"], ["a0"])
                receipt = (Path(td) / "stagehand-discovery.json").read_text()
                self.assertNotIn("fake", receipt)
                self.assertNotIn("attacker", receipt)
                self.assertFalse(json.loads(receipt)["outcome_verified"])
                self.assertIn("--inspection", run.call_args.args[0])



class StagehandPipelineTests(unittest.TestCase):
    def test_unverified_agent_selection_is_downgraded_before_capture(self):
        """Opt-in agent cannot turn an unverified click into an interactive film."""
        import os
        from contextlib import ExitStack
        from pathlib import Path
        import backend.url_engine as engine
        import backend.source_action_preflight  # import for mock patch target
        report = {
            "url": "https://example.com/", "source_url": "https://example.com/",
            "title": "A Demo", "headings": [
                {"id": "h0", "text": "A Demo", "selector": "#intro"}],
            "controls": [{"id": "a0", "kind": "button",
                          "text": "Try sample", "selector": "#button",
                          "button_type": "button"}],
        }
        stagehand_plan = choose_observed_action(report, {
            "schema": SCHEMA, "url": report["source_url"],
            "observations": [{"description": "Try sample"}]})
        self.assertEqual(stagehand_plan["action_ids"], ["a0"])
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as td, patch.dict(os.environ, {
            "SAUCE_STAGEHAND_DISCOVERY": "1", "SAUCE_CINEMATIC_ONLY": "0",
            "SAUCE_VERIFY_VISIBLE_ACTION": "0"}, clear=False):
            with ExitStack() as stack:
                stack.enter_context(patch("backend.url_engine.validate_public_url"))
                stack.enter_context(patch("backend.url_engine.load_render_checkpoint", return_value=None))
                stack.enter_context(patch("backend.url_engine.inspect", return_value=report))
                scout = stack.enter_context(patch(
                    "backend.stagehand_discovery.run_stagehand_discovery",
                    return_value=stagehand_plan))
                stack.enter_context(patch(
                    "backend.url_engine.direction",
                    side_effect=AssertionError("old director unexpectedly used")))
                stack.enter_context(patch(
                    "backend.url_engine.preflight", side_effect=lambda url, steps: steps))
                probe = stack.enter_context(patch(
                    "backend.source_action_preflight.probe_public_action",
                    return_value={"decision": "action_not_verified",
                                  "schema": "sauce-source-action-preflight-v1"}))
                stack.enter_context(patch("backend.url_engine.write_render_checkpoint"))
                stack.enter_context(patch("backend.url_engine.render_checkpoint", return_value="rendered"))
                def fake_capture(args, **kwargs):
                    out = Path(args[args.index("--out") + 1])
                    out.mkdir(parents=True, exist_ok=True)
                    (out / "continuous-capture.json").write_text(
                        json.dumps({"continuous_recording": True, "actions": []}))
                    self.assertEqual(
                        json.loads(Path(args[args.index("--plan") + 1]).read_text())["mode"],
                        "showcase")
                    return type("Completed", (), {"returncode": 0})()
                stack.enter_context(patch(
                    "backend.url_engine.subprocess.run", side_effect=fake_capture))
                result = engine.execute(report["source_url"], Path(td) / "job")
                self.assertEqual(result, "rendered")
                scout.assert_called_once()
                probe.assert_called_once()
                receipt = json.loads((Path(td) / "job" / "direction.json").read_text())
                self.assertEqual(receipt["direction_source"], "stagehand-observed-id")
                self.assertEqual(receipt["mode"], "showcase")
                self.assertEqual(receipt["visible_action_probe"], "action_not_verified")

if __name__ == "__main__":
    unittest.main()
