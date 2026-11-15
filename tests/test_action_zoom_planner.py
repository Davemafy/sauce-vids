"""Contract tests: auto zoom must be causally tied to cursor and click events."""
from __future__ import annotations
import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from action_zoom_planner import Rect,build_action_camera,first_intentional_motion


class ActionZoomTests(unittest.TestCase):
    def setUp(self):
        self.samples=[
          (0.,1400.,700.),(3.,1400.,700.),
          (3.50,1350.,686.),(3.65,1100.,590.),
          (3.90,770.,500.),(4.10,465.,416.),
          (4.50,464.,416.),
          (6.,464.,416.),(6.3,550.,460.),
          (6.6,665.,550.),(7.,665.,550.),
          (10.,665.,550.),
        ]
        self.kw=dict(
           fps=60,duration=10.,
           pointer_samples=self.samples,
           click_time=4.30,
           click_rect=Rect(361.,400.,206.,32.),
           modal_open_time=4.45,
           picker_rect=Rect(600.,270.,400.,360.),
           copied_time=7.15,
           result_rect=Rect(600.,212.,400.,476.),
        )

    def test_no_camera_motion_until_cursor_moves(self):
        frames,meta=build_action_camera(**self.kw)
        self.assertGreater(meta["first_pointer_motion"],3.0)
        for i in range(math.floor(meta["first_pointer_motion"]*60)):
            self.assertEqual(frames[i],(1.,800.,450.))

    def test_camera_targets_follow_pointer_approach(self):
        frames,_=build_action_camera(**self.kw)
        self.assertGreater(frames[round(4.30*60)][0],1.20)
        self.assertLess(frames[round(4.30*60)][1],740.)
        self.assertGreater(frames[round(4.30*60)][1],625.)

    def test_modal_zoom_starts_only_after_modal_is_real(self):
        frames,_=build_action_camera(**self.kw)
        before=frames[round(4.30*60)]
        after=frames[round(5.1*60)]
        self.assertLess(before[0],1.33)
        self.assertGreater(after[0],1.57)
        self.assertGreater(after[1],780.)

    def test_copied_state_never_preempted(self):
        frames,_=build_action_camera(**self.kw)
        self.assertLess(frames[round(6.9*60)][0],1.63)
        self.assertGreater(frames[round(8.0*60)][0],1.64)

    def test_output_deterministic_and_bounded(self):
        frames,meta=build_action_camera(**self.kw)
        again,_=build_action_camera(**self.kw)
        self.assertEqual(frames,again)
        self.assertEqual(len(frames),600)
        self.assertEqual(meta["first_click"],4.30)
        self.assertLessEqual(max(z for z,x,y in frames),1.67)
        self.assertTrue(all(math.isfinite(v) for row in frames for v in row))

    def test_cursor_was_not_moving(self):
        with self.assertRaisesRegex(ValueError,"No intentional cursor movement"):
            first_intentional_motion(
                [(0.,100.,100.),(3.,100.,100.),(4.,100.,100.)],
                click_time=4.)

    def test_unrelated_cursor_movement_does_not_trigger_zoom(self):
        samples=[(0.,100.,100.),(1.,100.,100.),
                 (1.1,50.,70.),(1.2,25.,50.),
                 (1.3,0.,0.)]
        with self.assertRaisesRegex(ValueError,"No intentional cursor movement"):
            first_intentional_motion(samples,click_time=1.5,
                                     target=(200.,200.))

    def test_incorrect_event_order_rejected(self):
        with self.assertRaises(ValueError):
            build_action_camera(**{**self.kw,"modal_open_time":4.2})

    def test_result_fits_safe_frame(self):
        frames,_=build_action_camera(**self.kw)
        # Source renderer width 1744, height 981; user viewport 1600x900.
        for t in (7.8,8.5,9.5):
            z,cx,cy=frames[round(t*60)]
            f=1744/1600*z
            dx=max(1744-1600*f,min(0.,872-cx*f))
            dy=max(981-900*f,min(0.,490.5-cy*f))
            x1=dx+600*f;x2=dx+1000*f
            y1=dy+212*f;y2=dy+688*f
            self.assertGreaterEqual(x1,0)
            self.assertLessEqual(x2,1744)
            self.assertGreaterEqual(y1,0)
            self.assertLessEqual(y2,981)


if __name__=="__main__":
    unittest.main()
