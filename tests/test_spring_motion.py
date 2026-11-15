"""Physics and interaction-integrity tests for Sauce motion tracks."""
from __future__ import annotations
import math
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from spring_motion import Spring1D, Spring2D, camera_track, cursor_track


class SpringPhysicsTests(unittest.TestCase):
    def test_critical_step_matches_two_half_steps(self):
        a=Spring1D(position=0.,velocity=3.,stiffness=100.,damping=20.)
        b=Spring1D(position=0.,velocity=3.,stiffness=100.,damping=20.)
        a.step(15.,1/30)
        b.step(15.,1/60)
        b.step(15.,1/60)
        self.assertAlmostEqual(a.position,b.position,places=11)
        self.assertAlmostEqual(a.velocity,b.velocity,places=11)

    def test_all_damping_branches_substep_invariance(self):
        for c in (5.,20.,35.):
            with self.subTest(damping=c):
                a=Spring1D(12.,velocity=-6.,stiffness=100.,damping=c)
                b=Spring1D(12.,velocity=-6.,stiffness=100.,damping=c)
                a.step(40.,.25)
                for _ in range(15):
                    b.step(40.,1/60)
                self.assertAlmostEqual(a.position,b.position,places=9)
                self.assertAlmostEqual(a.velocity,b.velocity,places=9)

    def test_camera_critical_is_monotone_for_single_target(self):
        camera=camera_track(fps=60,duration=2,anchors=[
            (0.,1.,800.,450.),(.25,1.8,700.,410.)])
        scales=[p[0] for p in camera]
        self.assertTrue(all(scales[i]<=scales[i+1]+1e-10
                            for i in range(len(scales)-1)))
        self.assertLessEqual(max(scales),1.8+1e-8)
        self.assertGreater(scales[-1],1.799)
        self.assertAlmostEqual(camera[0][0],1.)
        self.assertAlmostEqual(camera[0][1],800.)

    def test_initial_motion_is_not_position_jump(self):
        camera=camera_track(fps=60,duration=2,anchors=[
            (0.,1.,800.,450.),(.50,1.8,650.,420.)])
        start=camera[round(.5*60)-1]
        first=camera[round(.5*60)]
        second=camera[round(.5*60)+1]
        self.assertLess(abs(first[0]-start[0]),.02)
        self.assertLess(abs(second[0]-first[0]),.03)
        self.assertLess(abs(first[1]-start[1]),5.)

    def test_camera_random_access_is_deterministic(self):
        kwargs=dict(fps=60,duration=4.2,anchors=[
            (0.,1.08,800.,450.),(1.25,1.34,670.,450.),
            (3.,1.8,800.,450.)])
        a=camera_track(**kwargs)
        b=camera_track(**kwargs)
        self.assertEqual(a,b)
        self.assertEqual(len(a),252)
        for index in (0,30,150,251,90):
            self.assertEqual(a[index],b[index])

    def test_cursor_settles_onto_real_click(self):
        samples=[
          (0.,100.,100.),(.2,110.,110.),(.35,210.,200.),
          (.5,240.,240.),(.7,240.,240.),(1.,240.,240.),
        ]
        track=cursor_track(samples=samples,fps=60,duration=1.5)
        self.assertEqual(len(track),90)
        self.assertLess(math.dist(track[round(1.*60)],(240.,240.)),.25)
        self.assertEqual(track, cursor_track(samples=samples,fps=60,duration=1.5))

    def test_invalid_parameters(self):
        with self.assertRaises(ValueError):Spring1D(0.,stiffness=0.)
        with self.assertRaises(ValueError):Spring1D(0.,damping=-1.)
        with self.assertRaises(ValueError):Spring1D(0.).step(float('nan'),1/60)
        with self.assertRaises(ValueError):Spring1D(0.).step(5.,-.01)
        with self.assertRaises(ValueError):
            cursor_track(samples=[(0,0,0),(0,10,10)],fps=60,duration=1.)
        with self.assertRaises(ValueError):
            camera_track(fps=60,duration=1.,anchors=[(.5,1.,800.,450.)])

if __name__=="__main__":
    unittest.main()
