"""Keep real Tabler MIT cursor sources and the film-cursor route stable in CI."""
from __future__ import annotations
import hashlib
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'assets'/'cursors'/'tabler'
EXPECT={
 'pointer-filled.svg':'80615e4b6980aa33a000c6dc22a976221e9fd3a1c1d9d5ba3be7f15d5ea224fa',
 'pointer-outline.svg':'811735d187eaf6c8a7b7f06053140b8284cf4b1b2ea7ba1c8f340f1fbafbac24',
}


class TablerCursorAssetsTests(unittest.TestCase):
    def test_source_icons_are_verbatim_official_assets(self):
        for name,digest in EXPECT.items():
            with self.subTest(icon=name):
                self.assertEqual(hashlib.sha256((ASSETS/name).read_bytes()).hexdigest(),digest)

    def test_license_bundled(self):
        lic=(ASSETS/'LICENSE').read_text()
        self.assertIn('MIT License',lic)
        self.assertIn('Paweł Kuna',lic)

    def test_svg_paths_are_real_vectors_not_bitmaps(self):
        for name in EXPECT:
            with self.subTest(icon=name):
                root=ET.parse(ASSETS/name).getroot()
                self.assertEqual(root.attrib.get('viewBox'),'0 0 24 24')
                self.assertTrue(any(el.tag.endswith('path') for el in root.iter()))
                self.assertFalse(any(el.tag.endswith('image') for el in root.iter()))

    def test_styles_use_independent_original_source_geometry(self):
        ink=ET.parse(ASSETS/'pointer-filled.svg').getroot()
        outline=ET.parse(ASSETS/'pointer-outline.svg').getroot()
        a=' '.join(el.attrib.get('d','') for el in ink.iter())
        b=' '.join(el.attrib.get('d','') for el in outline.iter())
        self.assertNotEqual(a,b)

    def test_presentation_renderer_never_falls_back_to_x11_for_v14(self):
        code=(ROOT/'scripts'/'session_replay.py').read_text()
        self.assertIn('vector_mode=presentation_v13 or presentation_v14',code)
        self.assertIn('cursor_art=None if vector_mode',code)
        self.assertIn('render_tabler_cursor(',code)
        self.assertIn('if presentation_v14:',code)

    def test_style_and_click_hotspots_are_declared(self):
        code=(ROOT/'scripts'/'online_cursor_assets.py').read_text()
        self.assertIn('SVG_APEX=',code)
        self.assertIn('hotspot(style)',code)
        self.assertIn('CURSOR_SIZE=',code)
        self.assertIn('cursor_press_scale',code)
        self.assertIn('supersample=4',code)

    def test_choice_is_available_in_video_export_cli(self):
        code=(ROOT/'scripts'/'session_replay.py').read_text()
        self.assertIn("choices=('ink','outline')",code)
        self.assertIn('--presentation-v14',code)

if __name__=='__main__':
    unittest.main()
