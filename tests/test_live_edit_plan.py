import json
from pathlib import Path
import unittest

from scripts.live_edit_plan import compile_camera, parse_live_edit, sample_zoom


class LiveEditPlanTests(unittest.TestCase):
    def setUp(self):
        fixture = Path(__file__).parent / "fixtures" / "resend-live-edit-v1.json"
        self.plan = json.loads(fixture.read_text())
        self.receipt = {
            "sha256": self.plan["source_sha256"],
            "cursorless": True,
            "editorial_events": [{"kind": "slider_change"}],
        }

    def test_event_relative_push_and_hold(self):
        plan = parse_live_edit(self.plan, self.receipt)
        keys = plan.camera_timeline(3.44, 6.99, 2.47)
        self.assertEqual(keys, ((0., 2.38), (3.44, 2.38), (3.99, 2.47)))
        self.assertEqual(sample_zoom(2.8, keys, lambda x: x), 2.38)
        self.assertAlmostEqual(sample_zoom(3.715, keys, lambda x: x), 2.425)
        self.assertEqual(sample_zoom(6.5, keys, lambda x: x), 2.47)

    def test_proposal_cannot_swap_source_or_hide_result(self):
        with self.assertRaisesRegex(ValueError, "different capture"):
            parse_live_edit(self.plan, {**self.receipt, "sha256": "other"})
        plan = parse_live_edit(self.plan, self.receipt)
        with self.assertRaisesRegex(ValueError, "exceeds measured"):
            plan.camera_timeline(3.44, 6.99, 2.10)

    def test_neutral_boundary_marker_is_removed(self):
        keys = (("clip_start", 0, 1.50), ("result", 3, 1.50))
        self.assertEqual(compile_camera(keys, 3, 6, 2), ((0., 1.50),))
        with self.assertRaisesRegex(ValueError, "outside the last visible frame"):
            compile_camera((keys[0], ("result", 0, 1.50), ("result", 3, 1.75)), 3, 6, 2)

    def test_rejects_preemptive_camera_change(self):
        keys = (("clip_start", 0, 1.50), ("result", 0, 1.75))
        with self.assertRaisesRegex(ValueError, "observed result"):
            compile_camera(keys, 3, 6, 2)
