"""Root compositor contract: never regress to a white unstyled film."""
from __future__ import annotations
from pathlib import Path
import ast
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))


class CinematicStageRootTests(unittest.TestCase):
    def test_root_component_is_declared_and_fixed_at_1480_width(self):
        src=(ROOT/'scripts/cinematic_stage.py').read_text()
        tree=ast.parse(src)
        names={node.name for node in tree.body if isinstance(node,ast.ClassDef)}
        self.assertIn('CinematicStage',names)
        self.assertIn('CinematicCursor',names)
        self.assertIn('STAGE_BACKGROUND=(9,10,15)',src)
        self.assertIn('WINDOW_WIDTH=1480',src)
        self.assertIn('WINDOW_RADIUS=16',src)
        self.assertIn('GLOW_BLUR=140',src)
        self.assertIn('BACKDROP_BLUR=24',src)
        self.assertIn('FRAME_RGB=(18,18,24)',src)
        self.assertIn('FRAME_OPACITY=.90',src)
        self.assertIn('SHADOWS=((40,80,-20,.70),(80,160,-40,.50))',src)

    def test_root_is_the_last_frame_operation_before_encoding(self):
        src=(ROOT/'scripts/session_replay.py').read_text()
        pos=src.index('output_image=root_stage.render(')
        emit=src.index('encoder.stdin.write(output_image.tobytes())',pos)
        self.assertLess(pos,emit)
        self.assertIn('root_stage=(CinematicStage(',src)
        self.assertIn('root_cursor=(CinematicCursor(root_stage',src)
        self.assertIn('if root_stage:\n                # CinematicStage has already drawn',src)
        self.assertIn('cursor_art=None if vector_mode',src)
        self.assertIn('cursor:none !important;',src)

    def test_video_uses_real_spring_positions(self):
        src=(ROOT/'scripts/session_replay.py').read_text()
        spring=(ROOT/'scripts/spring_motion.py').read_text()
        root=(ROOT/'scripts/cinematic_stage.py').read_text()
        self.assertIn('cursor_track(samples=picked',src)
        self.assertIn('Spring2D',spring)
        self.assertIn('press_scale(age)',root)
        self.assertIn('click_ring_frames()',root)
        self.assertIn("ev['type']!='pointerdown'",root)

    def test_production_wont_publish_if_root_is_missing(self):
        src=(ROOT/'scripts/produce_cinematic_demo.py').read_text()
        self.assertIn("'cinematic_stage_root'",src)
        self.assertIn("CinematicStage root compositor is mandatory for production",src)

    def test_web_template_wraps_actual_root(self):
        src=(ROOT/'docs/sauce-premium-player-template.html').read_text()
        self.assertIn('<body><div class="CinematicStage"><main>',src)
        self.assertIn('</main></div></body></html>',src)
        self.assertIn('background:#090a0f',src)
        self.assertIn('filter:blur(140px)',src)
        self.assertIn('backdrop-filter:blur(24px)',src)
        self.assertIn('border-radius:16px',src)
        for shadow in (
            '0 0 0 1px rgba(255,255,255,.08)',
            '0 40px 80px -20px rgba(0,0,0,.7)',
            '0 80px 160px -40px rgba(0,0,0,.5)',
        ):
            self.assertIn(shadow,src)

if __name__=='__main__':unittest.main()
