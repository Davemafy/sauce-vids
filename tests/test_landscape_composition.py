"""Visual composition invariants that earlier Sauce exports repeatedly broke."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import landscape_layout as layout

class LandscapeCompositionTests(unittest.TestCase):
    def test_browser_occupies_correct_16_by_9_shape(self):
        self.assertEqual(layout.BROWSER_W/layout.BROWSER_H,16/9)
        self.assertEqual(layout.BROWSER_X,(layout.MASTER_W-layout.BROWSER_W)//2)

    def test_captions_have_separate_gutter(self):
        browser_end=layout.BROWSER_Y+layout.BROWSER_H
        self.assertGreaterEqual(layout.CAPTION_Y1-browser_end,55)
        self.assertGreaterEqual(layout.MASTER_H-layout.CAPTION_Y2,20)
        self.assertLess(layout.CAPTION_Y2,layout.MASTER_H)

    def test_cursor_stays_os_sized(self):
        self.assertLessEqual(layout.CURSOR_W,30)
        self.assertLessEqual(layout.CURSOR_H,40)
        self.assertGreaterEqual(layout.CURSOR_W,20)

    def test_scene_uses_no_horizontal_letterboxing(self):
        self.assertEqual(2*layout.BROWSER_X+layout.BROWSER_W,
                         layout.MASTER_W)
        self.assertGreater(layout.BROWSER_W,layout.MASTER_W*.80)
        self.assertLess(layout.BROWSER_W,layout.MASTER_W*.9)

if __name__=='__main__':unittest.main()
