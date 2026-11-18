"""Single authentic UI-plane camera: input truth, geometry and time contract."""
import sys
from pathlib import Path
import unittest
import cv2
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from semantic_editorial_camera import EditorialFocus,ease5


class EditorialCameraTest(unittest.TestCase):
    def test_no_camera_anticipation_and_exact_frame(self):
        f=EditorialFocus(1920,1080,711,575,553,276,211,210,2.92)
        self.assertEqual(f.params(0),(1.,960.,540.))
        image=np.random.default_rng(1).integers(0,256,(1080,1920,3),dtype=np.uint8)
        self.assertTrue(np.array_equal(f.render(image,0),image))

    def test_center_and_safe_region(self):
        f=EditorialFocus(1920,1080,711,575,553,276,211,210,2.92)
        self.assertAlmostEqual(f.params(1)[0],2.92)
        self.assertAlmostEqual(f.params(1)[1],987.5)
        x1,y1,x2,y2=f.source_bbox_at_output(1)
        self.assertGreater(x1,0)
        self.assertGreater(y1,0)
        self.assertLess(x2,1920)
        self.assertLess(y2,1080)
        self.assertGreater(x2-x1,1500)

    def test_camera_never_predicts_result(self):
        with self.assertRaises(ValueError):
            EditorialFocus(1920,1080,711,575,553,276,120,210,2.4)

    def test_crop_must_fit(self):
        with self.assertRaisesRegex(ValueError,"clip"):
            EditorialFocus(1920,1080,711,575,553,276,211,210,3.5)

    def test_wrong_aspect_fails_closed(self):
        f=EditorialFocus(1600,900,1000,200,300,170,310,308,1.8,
                         output_width=1920,output_height=1024)
        with self.assertRaisesRegex(ValueError,"aspect ratio"):
            f.matrix(.3)

    def test_reject_generated_or_wrong_format(self):
        f=EditorialFocus(1920,1080,711,575,553,276,211,210,2.92)
        with self.assertRaises(ValueError):
            f.render(np.zeros((1080,1920,3),dtype=np.float32),.5)

    def test_cinematic_curve_is_endpoint_stationary(self):
        self.assertAlmostEqual(ease5(.001),0,places=6)
        self.assertAlmostEqual(ease5(.999),1,places=6)
        self.assertAlmostEqual(ease5(.5),.5)
        with self.assertRaises(ValueError):
            ease5(float("nan"))

if __name__=="__main__":unittest.main()
