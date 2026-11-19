"""Sauce Basic native recorder contract: no arbitrary URL execution."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from basic_tour_native import (chapter_metadata,safe_filename,run,
                                capture_budget_seconds,assert_capture_budget)


class NativeTourContractTests(unittest.TestCase):
    def test_safe_generated_filenames(self):
        self.assertEqual(safe_filename("https://abc.invalid/../../../secret",2),"scene-02")
        self.assertEqual(safe_filename("https://other.com/?token=never-log",0),"scene-00")

    def test_chapters_are_monotonic_and_sanitized(self):
        content=chapter_metadata([
            {"title":"Home","encoded_seconds":3.4},
            {"title":"Pricing;\nNo leak","encoded_seconds":4.0},
        ])
        self.assertEqual(content.count("[CHAPTER]"),2)
        self.assertIn("START=0\nEND=3400",content)
        self.assertIn("START=3400\nEND=7400",content)
        self.assertNotIn("title=Pricing;\n",content)

    def test_public_input_blocked_without_allowlist(self):
        with self.assertRaisesRegex(ValueError,"allowlist"):
            run("https://www.brimble.io/",Path("/tmp/should-not-exist-basic"),
                allowed_hosts=[],preflight_only=True)

    def test_capture_budget_rejects_runaway_live_pages(self):
        self.assertLess(capture_budget_seconds(38.728),90.)
        self.assertLess(capture_budget_seconds(58.0),120.)
        self.assertLessEqual(capture_budget_seconds(300.),180.)
        with self.assertRaisesRegex(TimeoutError,"browser_capture_budget_exceeded"):
            assert_capture_budget(0,capture_budget_seconds(38.728),clock=lambda:132.)
        assert_capture_budget(0,capture_budget_seconds(38.728),clock=lambda:55.)

    def test_wrong_geometry_is_not_allowed_to_be_native(self):
        from basic_tour_planner import TourContract
        with self.assertRaises(ValueError):
            TourContract("https://www.brimble.io/",width=1280,height=1080)

if __name__=="__main__":
    unittest.main()
