import unittest
import numpy as np
from backend.native_subject_showcase import crop_for,camera_crop,shortlist,NATIVE
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
if __name__=="__main__":unittest.main()
