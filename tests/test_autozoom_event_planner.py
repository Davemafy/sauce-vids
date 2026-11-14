"""Regression tests for evidence-based Sauce camera plans (no source media needed)."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from autozoom_event_planner import plan,sample_camera

SCREEN={"width":1320,"height":720}
EV=[
 {"t":3.70,"kind":"click","label":"Reviews","semanticGoal":"open review",
  "targetRect":{"x":15.5,"y":150,"width":208,"height":28}},
 {"t":4.04,"kind":"state_change","evidence":"Diff tab loaded",
  "resultRect":{"x":559.8,"y":97,"width":750.6,"height":616}},
 {"t":10.65,"kind":"interaction_complete","label":"review inspected"},
]

class CameraTests(unittest.TestCase):
 def test_fail_closed_without_events(self):
  self.assertEqual(plan([],SCREEN,14),[])
  self.assertEqual(sample_camera(5,[]),(1,.5,.5))
 def test_no_zoom_without_real_state_change(self):
  self.assertEqual(plan(EV[:1],SCREEN,14),[])
 def test_one_evidenced_action_one_shot(self):
  clips=plan(EV,SCREEN,14)
  self.assertEqual(len(clips),1)
  self.assertGreater(clips[0].zoom,1.25)
  self.assertEqual(clips[0].action,"Reviews")
  self.assertLess(clips[0].start,EV[0]["t"])
  self.assertGreater(clips[0].settle,EV[1]["t"])
 def test_shot_does_not_chase_pointer(self):
  clips=plan(EV+[{"t":6,"kind":"cursor_dwell","cursor":{"x":15,"y":700}}],SCREEN,14)
  self.assertEqual(len(clips),1)
  self.assertEqual(clips[0].focus_x,plan(EV,SCREEN,14)[0].focus_x)
 def test_hold_stable(self):
  shots=plan(EV,SCREEN,14)
  self.assertEqual(sample_camera(7.0,shots),sample_camera(8.5,shots))
  self.assertEqual(sample_camera(13.75,shots),(1,.5,.5))
 def test_continuity(self):
  shots=plan(EV,SCREEN,14)
  frames=[sample_camera(i/60,shots) for i in range(840)]
  vel=[tuple(frames[i+1][j]-frames[i][j] for j in range(3)) for i in range(839)]
  accelerations=[tuple(vel[i+1][j]-vel[i][j] for j in range(3)) for i in range(838)]
  self.assertLess(max(abs(x) for row in accelerations for x in row),.002)
 def test_invalid_region_rejected(self):
  invalid=[EV[0],dict(EV[1],resultRect={"x":0,"y":0,"width":0,"height":0}),EV[2]]
  self.assertEqual(plan(invalid,SCREEN,14),[])

if __name__=="__main__":unittest.main()
