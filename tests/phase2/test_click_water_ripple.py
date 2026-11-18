"""Click-water refraction is source-timed, isolated and deterministic."""
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from click_water_ripple import apply_click_water_ripple,LIFETIME_S


class WaterRippleTests(unittest.TestCase):
    @staticmethod
    def source():
        y,x=np.mgrid[0:420,0:600]
        return np.stack(((x//3 % 2)*170+44,(y//4 % 2)*190+30,
                         ((x+y)//6 % 2)*170+55),axis=-1).astype(np.uint8)

    def test_pre_click_after_click_or_invalid_coordinates_no_effect(self):
        source=self.source()
        for age,location in [(-.01,(300,200)),(LIFETIME_S,(300,200)),
                             (2,(300,200)),(.1,(-1,220)),(.1,(200,800)),
                             (float('nan'),(200,200)),(.1,(float('inf'),300))]:
            image=source.copy()
            self.assertFalse(apply_click_water_ripple(image,location,age))
            np.testing.assert_array_equal(image,source)

    def test_refracts_real_source_pixels_only_in_nearby_wavefront(self):
        source=self.source()
        frame=source.copy()
        self.assertTrue(apply_click_water_ripple(frame,(300,220),.20))
        difference=np.any(frame!=source,axis=2)
        self.assertGreater(int(difference.sum()),500)
        self.assertTrue(np.array_equal(frame[:20],source[:20]))
        self.assertTrue(np.array_equal(frame[:,:50],source[:,:50]))
        self.assertTrue(np.array_equal(frame[-20:],source[-20:]))
        self.assertTrue(np.array_equal(frame[220,300],source[220,300]))

    def test_wavefront_expands_over_time_then_fades_without_trace(self):
        src=self.source()
        middle=np.array([300,220])
        frames=[]
        for time in (.10,.22,.40,.54):
            frame=src.copy()
            apply_click_water_ripple(frame,tuple(middle),time)
            frames.append(np.any(frame!=src,axis=2))
        # Farther pixels only become involved as the wave travels outward.
        self.assertFalse(frames[0][220,440])
        self.assertGreater(int(frames[2][185:255,465:505].sum()),100)
        self.assertLess(frames[-1].sum(),frames[2].sum())

    def test_determinism_and_no_source_mutation(self):
        src=self.source()
        original=src.copy()
        a,b=src.copy(),src.copy()
        self.assertTrue(apply_click_water_ripple(a,(230,200),.27))
        self.assertTrue(apply_click_water_ripple(b,(230,200),.27))
        np.testing.assert_array_equal(a,b)
        np.testing.assert_array_equal(src,original)

    def test_real_foreground_quad_remains_exact(self):
        source=self.source()
        altered=source.copy()
        quad=np.float32([[240,160],[360,160],[360,280],[240,280]])
        self.assertTrue(apply_click_water_ripple(
            altered,(300,220),.20,protected_quad=quad))
        np.testing.assert_array_equal(altered[165:275,245:355],
                                      source[165:275,245:355])
        self.assertGreater(np.count_nonzero(altered[:,400:]!=source[:,400:]),20)

    def test_small_inside_modal_wave_settles_early(self):
        source=self.source()
        frame=source.copy()
        self.assertTrue(apply_click_water_ripple(frame,(300,220),.08,
                        intensity=.38,lifetime_s=.27))
        self.assertGreater(int(np.count_nonzero(frame != source)),100)
        after=source.copy()
        self.assertFalse(apply_click_water_ripple(after,(300,220),.28,
                         intensity=.38,lifetime_s=.27))
        np.testing.assert_array_equal(after,source)

    def test_rejects_bad_frame_shapes(self):
        with self.assertRaisesRegex(ValueError,'BGR'):
            apply_click_water_ripple(np.zeros((40,40),np.uint8),(20,20),.2)

    def test_real_capture_wiring_is_opt_in_and_cursor_stays_last(self):
        production=(ROOT/'scripts/produce_cinematic_demo.py').read_text()
        compositor=(ROOT/'scripts/cinematic_stage.py').read_text()
        replay=(ROOT/'scripts/session_replay.py').read_text()
        self.assertIn("--click-water-ripple",production)
        self.assertIn("water_ripple=click_water_ripple",replay)
        self.assertIn("ev['type']!='pointerdown'",compositor)
        self.assertIn("apply_click_water_ripple(",compositor)
        self.assertIn("output,(px,py),age,",compositor)
        self.assertLess(compositor.index("apply_click_water_ripple("),
                        compositor.index("glyph_x=round(x-image.hotspot[0]*scale)"))


if __name__=='__main__':
    unittest.main()
