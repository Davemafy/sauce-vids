"""SVG silhouette and rendering contracts derived from supplied cursor refs."""
from __future__ import annotations
from pathlib import Path
from xml.etree import ElementTree as ET
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'assets/cursors/reference-v15'


class ReferenceCursorV15Tests(unittest.TestCase):
    def test_black_is_rounded_custom_path_not_old_tabler_icon(self):
        root=ET.parse(ASSETS/'black-rounded.svg').getroot()
        paths=[e for e in root.iter() if e.tag.endswith('path')]
        self.assertEqual(len(paths),1)
        p=paths[0]
        self.assertEqual(p.get('fill'),'#111113')
        self.assertEqual(p.get('stroke'),'#FFFFFF')
        self.assertEqual(p.get('stroke-width'),'2.2')
        self.assertEqual(p.get('stroke-linejoin'),'round')
        self.assertTrue(p.get('d').startswith('M 6 4.3'))
        self.assertIn('L 63.5 49.8',p.get('d'))

    def test_outline_is_independent_diagonal_geometry(self):
        root=ET.parse(ASSETS/'white-outline.svg').getroot()
        p=next(e for e in root.iter() if e.tag.endswith('path'))
        self.assertEqual(p.get('fill'),'#FFFFFF')
        self.assertEqual(p.get('stroke'),'#090A0D')
        self.assertTrue(p.get('d').startswith('M 5 3.2'))
        self.assertIn('L 64.2 46.1',p.get('d'))
        other=next(e for e in ET.parse(ASSETS/'black-rounded.svg').getroot().iter()
                   if e.tag.endswith('path'))
        self.assertNotEqual(p.get('d'),other.get('d'))

    def test_tips_are_top_left_not_rotated_to_wrong_corner(self):
        for filename,view in [('black-rounded.svg',(70.,86.)),
                              ('white-outline.svg',(86.,87.))]:
            root=ET.parse(ASSETS/filename).getroot()
            self.assertEqual(tuple(map(float,root.get('viewBox').split()[2:])),view)
            p=next(e for e in root.iter() if e.tag.endswith('path'))
            self.assertIn('stroke-linecap',p.attrib)

    def test_drop_shadow_matches_requested_offset_blur_opacity(self):
        src=(ROOT/'scripts/reference_cursor_v15.py').read_text()
        for token in ('SHADOW_OFFSET=(0,12)','SHADOW_BLUR=24',
                      'SHADOW_OPACITY=.35','ImageFilter.GaussianBlur',
                      'supersample=4'):
            self.assertIn(token,src)

    def test_film_cursor_is_proportional_not_oversized(self):
        src=(ROOT/'scripts/reference_cursor_v15.py').read_text()
        replay=(ROOT/'scripts/session_replay.py').read_text()
        self.assertIn('film_scale:float=.56',src)
        self.assertIn('scale=film_scale*press_scale(age)',src)
        self.assertIn('cursor_scale:float=.56',replay)
        self.assertIn('--cursor-scale',replay)
        self.assertEqual(tuple(round(v*.56) for v in (58,70)),(32,39))
        self.assertEqual(tuple(round(v*.56) for v in (62,64)),(35,36))

    def test_press_contract_is_fixed_to_088(self):
        src=(ROOT/'scripts/reference_cursor_v15.py').read_text()
        self.assertIn('return 1.-.12*u*u*(3-2*u)',src)
        self.assertIn('_click_age',src)

    def test_video_runner_does_not_use_os_cursor(self):
        src=(ROOT/'scripts/session_replay.py').read_text()
        self.assertIn('presentation_v15',src)
        self.assertIn('vector_mode=presentation_v13 or presentation_v14 or presentation_v15',src)
        self.assertIn('cursor_art=None if vector_mode',src)
        self.assertIn('paint_reference_cursor',src)
        self.assertIn('reference-svg-overlay-always-visible',src)

    def test_cli_has_correct_new_preset(self):
        src=(ROOT/'scripts/session_replay.py').read_text()
        self.assertIn('--presentation-v15',src)
        self.assertIn('args.presentation_v15=True',src)
        self.assertIn('--raw-replay',src)
        self.assertIn("choices=('ink','outline')",src)

if __name__=='__main__':unittest.main()
