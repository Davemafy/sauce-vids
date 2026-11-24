import unittest
import numpy as np
from backend.native_subject_showcase import crop_for,camera_crop,continuous_crop,shortlist,NATIVE,compile_camera_direction,sample_camera_direction
class NativeShowcaseTests(unittest.TestCase):
    def test_detail_contains_real_subject(self):
        rect={"x":288,"y":360,"width":1525,"height":900}
        for mode in ("detail","context"):
            x,y,w,h=crop_for(rect,mode)
            self.assertAlmostEqual(w/h,16/9)
            self.assertLessEqual(x,rect["x"])
            self.assertLessEqual(y,rect["y"])
            self.assertGreaterEqual(x+w,rect["x"]+rect["width"])
            self.assertGreaterEqual(y+h,rect["y"]+rect["height"])
            self.assertLessEqual(x+w,NATIVE[0])
            self.assertLessEqual(y+h,NATIVE[1])
        self.assertLess(crop_for(rect,"detail")[2],crop_for(rect,"context")[2])
    def test_camera_waits_for_scroll(self):
        rect={"x":288,"y":360,"width":1525,"height":900}
        np.testing.assert_allclose(camera_crop(rect,"detail",1.0),[0,0,*NATIVE])
        np.testing.assert_allclose(camera_crop(rect,"detail",3.1),crop_for(rect,"detail"))
    def test_invalid_subject_and_camera_rejected(self):
        with self.assertRaises(ValueError):crop_for({"x":-10,"y":0,"width":100,"height":100},"detail")
        with self.assertRaises(ValueError):crop_for({"x":0,"y":0,"width":100,"height":100},"invented")
    def test_model_can_only_choose_observed_ids_and_modes(self):
        rows=[{"id":"s0","kind":"hero","rect":{"y":0}},{"id":"s1","kind":"product-illustration","rect":{"y":100}},{"id":"s2","kind":"product-illustration","rect":{"y":300}}]
        self.assertIsNone(shortlist({"shots":[{"id":"s0","camera":"detail"},{"id":"s2","camera":"context"}]},rows))
        self.assertIsNone(shortlist({"shots":[{"id":"s1","camera":"arbitrary"},{"id":"s2","camera":"context"}]},rows))
        self.assertEqual([s["id"] for s in shortlist({"shots":[{"id":"s2","camera":"detail"},{"id":"s1","camera":"context"}]},rows)],["s1","s2"])
    def test_continuous_camera_is_wide_between_subjects_and_has_no_jump(self):
        rect={"x":288,"y":360,"width":1525,"height":900}
        beats=[{"rect":rect,"push_start":1.,"push_end":1.9,"release_start":2.9,"release_end":3.7},
               {"rect":rect,"push_start":5.,"push_end":5.9,"release_start":6.9,"release_end":7.7}]
        shots=[{"camera":"detail"},{"camera":"context"}]
        wide=np.array([0,0,*NATIVE])
        for t in (0,1,3.7,4,5,7.7,8):
            np.testing.assert_allclose(continuous_crop(beats,shots,t),wide)
        np.testing.assert_allclose(continuous_crop(beats,shots,2.5),crop_for(rect,"detail"))
        frames=np.array([continuous_crop(beats,shots,t/60) for t in range(481)])
        self.assertLess(np.abs(np.diff(frames,axis=0)).max(),45)
        self.assertTrue((frames[:,:2]>=0).all())
        self.assertTrue((frames[:,:2]+frames[:,2:]<=np.array(NATIVE)+1e-6).all())

    def test_source_bound_direct_pan_does_not_reset_wide(self):
        rect={"x":288,"y":360,"width":746,"height":900}
        right={"x":1066,"y":360,"width":1525,"height":900}
        source={"sha256":"fixture","seconds":10.,"frames":600,"beats":[{"id":"s0","rect":rect},{"id":"s1","rect":rect},{"id":"s2","rect":right}],"scrolls":[{"start":1.,"end":3.,"target_scroll_css":1000},{"start":6.,"end":7.,"target_scroll_css":1000}]}
        plan={"schema":"sauce-continuous-camera-v1","source_sha256":"fixture","keys":[{"t":0,"target":"wide"},{"t":3,"target":"wide"},{"t":4.5,"target":"s1","mode":"detail"},{"t":6,"target":"s1","mode":"detail"},{"t":7.8,"target":"s2","mode":"detail"},{"t":10,"target":"s2","mode":"detail"}]}
        keys=compile_camera_direction(source,plan)
        np.testing.assert_allclose(sample_camera_direction(keys,2),[0,0,*NATIVE])
        self.assertLess(sample_camera_direction(keys,6.9)[2],NATIVE[0])
        self.assertGreater(sample_camera_direction(keys,6.9)[0],sample_camera_direction(keys,6)[0])
        with self.assertRaises(ValueError):compile_camera_direction(source,{**plan,"source_sha256":"wrong"})
        bad={**plan,"keys":[{**plan["keys"][0],"target":"s1","mode":"detail"},*plan["keys"][1:]]}
        with self.assertRaises(ValueError):compile_camera_direction(source,bad)

if __name__=="__main__":unittest.main()
