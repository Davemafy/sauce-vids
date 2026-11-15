"""Production presentation rules: the rendered click must always be visible."""
from __future__ import annotations
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from presentation_contract import presentation_css_cursor,press_scale,modal_spring_scale

class PresentationContractTests(unittest.TestCase):
    def setUp(self):
        self.box=[dict(x=250.,y=340.,width=170.,height=44.)]
        self.events=[
            dict(type='pointermove',t=350.,x=275.,y=351.),
            dict(type='pointerdown',t=750.,x=310.,y=360.),
            dict(type='pointerup',t=791.,x=310.,y=360.),
        ]

    def test_css_none_never_hides_cursor(self):
        for css in (None,'none','auto','default'):
            self.assertIn(presentation_css_cursor(css,(0,0),[]),
                          ('default','pointer','text'))

    def test_css_none_still_renders_hand_over_real_click(self):
        self.assertEqual(presentation_css_cursor('none',(310,360),self.box),
                         'pointer')

    def test_css_none_elsewhere_is_standard_arrow(self):
        self.assertEqual(presentation_css_cursor('none',(900,700),self.box),
                         'default')

    def test_text_input_uses_native_ibeam(self):
        self.assertEqual(presentation_css_cursor('text',(310,360),self.box),
                         'text')

    def test_press_has_natural_contraction_and_settle(self):
        self.assertEqual(press_scale(self.events,.74,0),1.)
        self.assertAlmostEqual(press_scale(self.events,.75,0),1.)
        self.assertLess(press_scale(self.events,.815,0),.895)
        self.assertGreater(press_scale(self.events,.925,0),.97)
        self.assertEqual(press_scale(self.events,1.02,0),1.)

    def test_press_never_applies_to_hover_only(self):
        self.assertEqual(press_scale(self.events[:1],.76,0),1.)

    def test_modal_scale_monotone_to_one(self):
        values=[modal_spring_scale(i/60) for i in range(22)]
        self.assertAlmostEqual(values[0],.95,places=8)
        self.assertTrue(all(a<=b for a,b in zip(values,values[1:])))
        self.assertGreater(values[-1],.999)
        self.assertEqual(modal_spring_scale(-.01),1.)

    def test_presses_are_triggered_by_real_mouse_down(self):
        shifted=[dict(type='pointermove',t=750.,x=310.,y=360.)]
        self.assertEqual(press_scale(shifted,.815,0),1.)

if __name__=='__main__':unittest.main()
