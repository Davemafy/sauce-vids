"""Actual source event timing, not guessed source editorials."""
import unittest
from backend.live_render import verified_action_intro_trim
from scripts.autozoom_event_planner import plan,sample_camera


class CustomerActionFirstMotionTests(unittest.TestCase):
    def setUp(self):
        self.events=[
            {"kind":"click","t":4.15,"label":"Open modal","semanticGoal":"Real modal"},
            {"kind":"state_change","t":5.14,"evidence":"Real UI appeared",
             "resultRect":{"x":807.,"y":54.,"width":306.,"height":205.}},
            {"kind":"interaction_complete","t":7.35},
        ]

    def test_original_click_and_outcome_fully_preserved(self):
        self.assertAlmostEqual(verified_action_intro_trim(self.events,.63),3.60)
        self.assertAlmostEqual(self.events[0]["t"]-3.60,.55)
        self.assertAlmostEqual(self.events[1]["t"]-3.60,1.54)
        self.assertAlmostEqual(verified_action_intro_trim(self.events,3.8),3.8)

    def test_no_result_no_timeline_rewrite(self):
        for events in (
            [],self.events[:1],
            [self.events[0],{**self.events[1],"evidence":""}],
            [self.events[0],{**self.events[1],"t":7.2}],
            [{**self.events[0],"semanticGoal":""},self.events[1]],
        ):
            self.assertEqual(verified_action_intro_trim(events,.6),.6)
        for invalid in (float("nan"),-.2):
            with self.assertRaises(ValueError):
                verified_action_intro_trim(self.events,invalid)

    def test_source_measured_compact_modal_is_readable_without_early_reveal(self):
        raw=self.events
        film=[{**e,**({"t":e["t"]-3.60} if "t" in e else {})} for e in raw]
        shots=plan(film,{"width":1920,"height":1080},5.2,profile="action-first")
        self.assertEqual(len(shots),1)
        shot=shots[0]
        self.assertAlmostEqual(shot.zoom,2.1)
        self.assertGreater(shot.start,film[1]["t"])
        self.assertGreater(shot.settle-shot.start,1.0)
        self.assertGreater(shot.end-shot.release,.9)
        self.assertEqual(sample_camera(film[0]["t"],shots),(1,.5,.5))
        self.assertEqual(sample_camera(film[1]["t"],shots),(1,.5,.5))
        self.assertLess(shot.end,5.2)


if __name__=="__main__":
    unittest.main()
