"""Source-level cursor contract: editable SVG, no platform hand glyph."""
from __future__ import annotations
import sys,unittest
from pathlib import Path
from xml.etree import ElementTree
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from spring_motion import Spring2D,cursor_track


ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'assets'/'cursors'


class VectorCursorTests(unittest.TestCase):
    def test_cursor_is_real_editable_svg(self):
        p=ASSETS/'sauce-pointer.svg'
        xml=ElementTree.parse(p).getroot()
        self.assertTrue(xml.tag.endswith('svg'))
        self.assertEqual(xml.attrib['viewBox'],'0 0 28 38')
        paths=[e for e in xml.iter() if e.tag.endswith('path')]
        self.assertGreaterEqual(len(paths),1)
        self.assertTrue(any('fill' in path.attrib for path in paths))
        self.assertNotIn('image',p.read_text().lower())
        self.assertNotIn('http://',p.read_text().replace('http://www.w3.org/2000/svg',''))

    def test_ripple_is_svg_and_has_animatable_radius_and_opacity(self):
        data=(ASSETS/'sauce-click-ripple.svg').read_text()
        self.assertIn('{{RADIUS}}',data)
        self.assertIn('{{OPACITY}}',data)
        self.assertIn('circle',data)

    def test_spring2d_keeps_velocity_in_both_dimensions(self):
        spring=Spring2D(0,0,stiffness=900,damping=60)
        path=[]
        for f in range(60):
            target=400 if f>=8 else 0
            path.append(spring.step(target,target/2,1/60))
        self.assertEqual(path[0],(0,0))
        self.assertGreater(path[12][0],0)
        self.assertLess(path[12][0],400)
        self.assertAlmostEqual(path[59][0],400,delta=.01)
        self.assertAlmostEqual(path[59][1],200,delta=.01)

    def test_cursor_track_is_deterministic(self):
        args=dict(samples=[(0,500,330),(.3,325,360),(.66,300,350),
                                  (1.,300,350)],fps=60,duration=1.5,
                  stiffness=900,damping=60)
        self.assertEqual(cursor_track(**args),cursor_track(**args))


if __name__=='__main__':
    unittest.main()
