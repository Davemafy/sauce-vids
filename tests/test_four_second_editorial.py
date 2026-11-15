"""Regression tests for the filmed four-second agency-comparison shot."""
from __future__ import annotations
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from editorial_closeup_camera import closeup_camera
from finish_four_second_test import ass_document,timestamp

def _events():
    box={'x':440.,'y':182.59,'width':400.,'height':360.}
    a={'x':200.,'y':344.,'width':208.,'height':32.}
    codex={'x':487.,'y':443.,'width':254.,'height':54.}
    return [
      {'type':'pointermove','t':1000.,'x':998.,'y':526.},
      {'type':'pointermove','t':1090.,'x':920.,'y':485.},
      {'type':'pointermove','t':1220.,'x':725.,'y':425.},
      {'type':'pointermove','t':1500.,'x':460.,'y':385.},
      {'type':'pointermove','t':1740.,'x':304.,'y':360.},
      {'type':'pointerdown','t':1786.,'x':304.,'y':360.,'box':a},
      {'type':'dialog-visible','t':1916.,'box':box},
      {'type':'pointermove','t':2250.,'x':370.,'y':395.},
      {'type':'pointermove','t':2520.,'x':540.,'y':448.},
      {'type':'pointermove','t':2920.,'x':614.,'y':461.},
      {'type':'pointerdown','t':3069.,'x':614.,'y':461.,'box':codex},
    ]


class FourSecondEditorialTests(unittest.TestCase):
    def setUp(self):
        self.expanded={'x':440.,'y':122.,'width':400.,'height':476.}

    def test_look_ahead_is_based_on_measured_expansion(self):
        t,meta=closeup_camera(_events(),1000.,4.0,60,expanded_rect=self.expanded)
        self.assertEqual(len(t),240)
        self.assertEqual(meta['expanded_dialog_css_rect'],self.expanded)
        self.assertTrue(meta['editorial_closeup'])
        self.assertGreater(meta['max_zoom'],1.60)
        for i in range(round(2.07*60),240):
            zoom,cx,cy=t[i]
            # A 476px-high actual dialog fits in 832px content height.
            height=476.*832/720*zoom
            self.assertLessEqual(height,832-90)
            self.assertAlmostEqual(cy,360.,delta=3.)

    def test_camera_does_not_zoom_before_pointer_moves(self):
        t,meta=closeup_camera(_events(),1000.,4.0,60,expanded_rect=self.expanded)
        self.assertTrue(all(abs(t[i][0]-1.)<.00001 for i in range(5)))
        self.assertGreater(t[90][0],1.4)
        self.assertLess(t[180][0],1.34)

    def test_missing_expanded_geometry_is_a_hard_error(self):
        with self.assertRaisesRegex(ValueError,'Expanded modal geometry'):
            closeup_camera(_events(),1000.,4.,60)
        with self.assertRaisesRegex(ValueError,'Incomplete'):
            closeup_camera(_events(),1000.,4.,60,expanded_rect={'height':476})

    def test_ass_times_are_valid_no_extra_hours_field(self):
        self.assertEqual(timestamp(.16),'0:00:00.16')
        self.assertEqual(timestamp(3.6),'0:00:03.60')
        self.assertEqual(timestamp(.999),'0:00:01.00')
        text=ass_document([
            {'start':.16,'end':1.517,'text':'Connect it to Brimble.'},
            {'start':2.08,'end':3.598,'text':'Copy the setup command.'},
        ])
        self.assertIn('0:00:00.16,0:00:01.52',text)
        self.assertIn('0:00:02.08,0:00:03.60',text)
        self.assertNotIn('0:00:00:00.',text)
        self.assertIn('Inter,37',text)
        self.assertIn('46,1',text)

if __name__=='__main__': unittest.main()
