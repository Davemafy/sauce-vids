import copy
import unittest
from scripts.drawing_detail_direction import compact_drawing

class DrawingDetailDirectionTests(unittest.TestCase):
    def setUp(self):
        self.plan={"durationSeconds":7.5,"studioStage":{},"sourceSha256":"source","manifestSha256":"manifest"}
        self.box={"x":36,"y":254,"width":2417,"height":1359.7656}
        self.event={"kind":"draw_stroke","start":.841667,"end":3.41349,"t":4.222266,"evidence":"actual source","targetRect":self.box,"resultRect":self.box}
        self.manifest={"capture_rect":{"width":3200,"height":2320},"events":[self.event]}

    def test_source_clock_and_hold(self):
        p=compact_drawing(copy.deepcopy(self.plan),self.manifest)
        self.assertEqual(p["sourceSha256"],"source")
        self.assertEqual(p["manifestSha256"],"manifest")
        self.assertAlmostEqual(p["durationSeconds"]*60,362)
        keys=p["studioStage"]["camera"]
        self.assertGreaterEqual(keys[1]["startAt"],self.event["start"])
        self.assertGreaterEqual(keys[3]["startAt"],self.event["t"])
        self.assertGreater(p["durationSeconds"]-keys[3]["at"],.5)
        self.assertEqual(keys[0]["scale"],keys[-1]["scale"])
        self.assertFalse(any(k.get("cut") for k in keys))
        self.assertEqual(p["studioStage"]["payoff"]["minContextVisible"],.99)

    def test_reject_non_drawing_and_unverified(self):
        for change in ({"kind":"click"},{"evidence":""},{"t":3.0},{"t":7.0}):
            with self.assertRaises(ValueError):
                compact_drawing(copy.deepcopy(self.plan),{**self.manifest,"events":[{**self.event,**change}]})
