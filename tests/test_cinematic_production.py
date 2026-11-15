"""Production preset and reusable page: dependency-free CI acceptance."""
from __future__ import annotations
from pathlib import Path
import sys,tempfile,unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from cinematic_spec import (DPR_CHOICES,DEFAULT_DPR,MASTER_SIZE,PREVIEW_SIZE,
    FPS,CURSOR_FILM_SCALE,CURSOR_PRESS_PEAK,CSS_STAGE_SHADOW,AMBIENT_BLUR,
    SHADOW_LAYERS,enforce_hidpi,ffmpeg_lanczos_preview)
from produce_cinematic_demo import build_web_player,ensure_private_capture_separate


class CinematicProductionPresetTests(unittest.TestCase):
    def test_new_capture_dpr_is_hidpi_only(self):
        self.assertEqual(DPR_CHOICES,(2,3))
        self.assertEqual(DEFAULT_DPR,2)
        self.assertEqual(enforce_hidpi(2),2)
        self.assertEqual(enforce_hidpi(3),3)
        for bad in (1,0,4,2.5):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                enforce_hidpi(bad)

    def test_1080p_master_preview_and_lanczos_filter(self):
        self.assertEqual(MASTER_SIZE,(1920,1080))
        self.assertEqual(PREVIEW_SIZE,(1280,720))
        self.assertEqual(FPS,60)
        self.assertEqual(ffmpeg_lanczos_preview(),
                         'fps=30,scale=1280:720:flags=lanczos')
        with self.assertRaises(ValueError):
            ffmpeg_lanczos_preview(1920,1080,1280,800)

    def test_cursor_stays_proportional(self):
        self.assertEqual(CURSOR_FILM_SCALE,.56)
        self.assertEqual(CURSOR_PRESS_PEAK,.88)
        self.assertEqual(round(58*CURSOR_FILM_SCALE),32)
        self.assertEqual(round(70*CURSOR_FILM_SCALE),39)

    def test_stage_matches_shadow_and_glow_spec(self):
        self.assertEqual(AMBIENT_BLUR,120)
        self.assertIn('0 25px 50px -12px rgba(0,0,0,0.5)',CSS_STAGE_SHADOW)
        self.assertIn('0 50px 100px -20px rgba(0,0,0,0.3)',CSS_STAGE_SHADOW)
        self.assertEqual(len(SHADOW_LAYERS),3)
        src=(ROOT/'scripts/cinematic_presentation_v13.py').read_text()
        self.assertIn('for offset,blur,spread,opacity in SHADOW_LAYERS',src)
        self.assertIn('GaussianBlur(AMBIENT_BLUR)',src)

    def test_browser_captures_device_pixels_at_2_or_3(self):
        src=(ROOT/'scripts/session_capture.py').read_text()
        self.assertIn('enforce_hidpi(dpr)',src)
        self.assertIn('device_scale_factor',src)
        self.assertIn('choices=DPR_CHOICES',src)

    def test_native_cursor_hidden_in_cinematic_replay(self):
        src=(ROOT/'scripts/session_replay.py').read_text()
        self.assertIn('cursor_art=None if vector_mode',src)
        self.assertIn('cursor:none !important',src)
        self.assertIn('root_stage.render(source,cinematic_cursor=draw_cursor)',src)
        self.assertIn('CURSOR_FILM_SCALE',src)
        self.assertIn('cursor_track(',src)

    def test_dark_template_contains_exact_stage_css(self):
        template=(ROOT/'docs/sauce-premium-player-template.html').read_text()
        self.assertIn('filter:blur(140px)',template)
        self.assertIn('<body><div class="CinematicStage"><main>',template)
        self.assertIn('background:#090a0f',template)
        for shadow in ('0 0 0 1px rgba(255,255,255,.08)',
                       '0 40px 80px -20px rgba(0,0,0,.7)',
                       '0 80px 160px -40px rgba(0,0,0,.5)'):
            self.assertIn(shadow,template)
        self.assertIn('aspect-ratio:16/9',template)
        self.assertIn('playsinline',template)

    def test_public_export_never_contains_raw_capture(self):
        with tempfile.TemporaryDirectory() as d:
            private=Path(d)/'capture'
            public=Path(d)/'release'
            ensure_private_capture_separate(private,public)
            for unsafe in (private,private/'web',Path(d)):
                with self.subTest(unsafe=unsafe),self.assertRaises(ValueError):
                    ensure_private_capture_separate(private,unsafe)

    def test_player_escapes_content_and_resolves_all_tokens(self):
        with tempfile.TemporaryDirectory() as d:
            page=build_web_player(
                ROOT/'docs/sauce-premium-player-template.html',Path(d),
                '<b>Test & review</b>','Check "this" <script>',4.2)
            html=page.read_text()
            self.assertIn('&lt;b&gt;Test &amp; review&lt;/b&gt;',html)
            self.assertNotIn('<script>Check',html)
            self.assertIn('&lt;script&gt;',html)
            self.assertNotIn('{{',html)
            self.assertIn('master-1080p60.mp4',html)
            self.assertIn('preview.mp4',html)

if __name__=='__main__':
    unittest.main()
