"""Regress same-frame hover/click verification ordering seen on Refit."""
import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from session_replay import source_checks_before_action


class ReplaySemanticOrderTests(unittest.TestCase):
    def test_hover_is_checked_before_navigation_in_same_video_frame(self):
        # Captured Refit hover ends 0.9ms before click. At 60fps both
        # can occur during the same output frame; the old replay checked
        # after navigation and falsely rejected the real earlier hover.
        stored = [
            {"at_ms": 789.5, "end_ms": 1497.8},
            {"at_ms": 1498.9, "end_ms": 2023.7},
            {"at_ms": 2024.6, "end_ms": 3019.0},
        ]
        self.assertEqual(source_checks_before_action(stored, 0, 2), (0, 1))
        self.assertEqual(source_checks_before_action(stored, 1, 2), (1,))
        self.assertEqual(source_checks_before_action(stored, 2, 2), ())

    def test_overlapping_source_action_does_not_claim_earlier_check(self):
        stored = [
            {"at_ms": 100, "end_ms": 205},
            {"at_ms": 203, "end_ms": 240},
        ]
        self.assertEqual(source_checks_before_action(stored, 0, 1), ())
        self.assertEqual(source_checks_before_action(stored, 4, 1), ())
