"""Actual Chromium fixture gates for overlays, loading and cursor safety."""
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from basic_tour_quality import (overlaps_text,park_cursor,quality_scan,
                                visible_text_boxes,ensure_observable,settle_visible_text,settle_visible_images)
from session_capture import install_presentation_cleanup, PRESENTATION_CLEANUP_STYLE
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright=None


@unittest.skipUnless(sync_playwright is not None,"Playwright unavailable")
class BasicQualityBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw=sync_playwright().start()
        chromium=os.environ.get("SAUCE_CHROME_BIN") or (
            "/opt/devmcp-browsers/chromium_headless_shell-1254/"
            "chrome-headless-shell-linux64/chrome-headless-shell")
        try:
            cls.browser=cls.pw.chromium.launch(headless=True,
                executable_path=chromium if Path(chromium).is_file() else None,
                args=["--no-sandbox"])
        except Exception:
            cls.pw.stop()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def test_idle_cursor_never_overlaps_text(self):
        page=self.browser.new_page(viewport={"width":1280,"height":720})
        try:
            page.set_content("""<html><body style="margin:0">
              <h1 style="position:absolute;left:3px;top:595px;width:170px;">
                Important text</h1>
              <p style="position:absolute;right:4px;bottom:2px;width:150px">
                Footer text</p></body></html>""")
            boxes=visible_text_boxes(page)
            self.assertGreater(len(boxes),1)
            self.assertTrue(overlaps_text((18,658),boxes))
            place=park_cursor((1280,720),boxes)
            self.assertFalse(overlaps_text(place,boxes))
        finally:
            page.close()

    def test_chat_widget_hidden_no_consent_mutation(self):
        context=self.browser.new_context(viewport={"width":1280,"height":720})
        install_presentation_cleanup(context)
        page=context.new_page()
        try:
            page.set_content("""<html><body>
              <button class="woot-widget-bubble" style="
                position:fixed;bottom:20px;right:20px;width:100px;height:100px">
                Support</button>
              <div id="cookie-banner" style="position:fixed;bottom:0;
                left:0;background:#fff;height:120px;width:100%">
                Cookies <button id="accept">Accept</button></div>
              <script>document.querySelector("#accept").onclick=()=>
                window.__trackedConsent=true</script>
              </body></html>""")
            # set_content changes about:blank after context init; reinforce
            # the existing Sauce presentation CSS as live capture does.
            page.add_style_tag(content=PRESENTATION_CLEANUP_STYLE)
            result=quality_scan(page)
            self.assertEqual(result["visible"]["chat"],0)
            self.assertEqual(result["visible"]["consent"],1)
            self.assertIn("visible_consent_overlay",result["issues"])
            self.assertIsNone(page.evaluate("window.__trackedConsent"))
        finally:
            context.close()

    def test_visible_skeleton_fails_observable_check(self):
        page=self.browser.new_page(viewport={"width":1280,"height":720})
        try:
            page.set_content("""<body><main>
              <div class="skeleton" style="width:520px;height:210px;background:#ddd">
              </div></main></body>""")
            quality=ensure_observable(page,max_attempts=2,interval_ms=15)
            self.assertEqual(quality["confidence"],"low")
            self.assertIn("visible_skeleton",quality["issues"])
        finally:
            page.close()

    def test_visible_text_fade_is_sampled_without_forcing_opacity(self):
        page=self.browser.new_page(viewport={"width":1280,"height":720})
        try:
            page.set_content("""<body><main>
              <h1 id="headline" style="opacity:0.2;transition:opacity .10s">
                This heading actually fades</h1></main></body>""")
            page.evaluate("document.querySelector('#headline').style.opacity='1'")
            result=settle_visible_text(page,checks=5,interval_ms=90)
            self.assertEqual(result["low_opacity_headings"],0)
            self.assertGreaterEqual(result["wait_ms"],90)
            self.assertGreater(
                float(page.locator("#headline").evaluate("e=>getComputedStyle(e).opacity")),.94)
        finally:
            page.close()

    def test_unsettled_translucent_heading_is_flagged_not_modified(self):
        page=self.browser.new_page(viewport={"width":1280,"height":720})
        try:
            page.set_content("""<body><main><h1 id="headline"
              style="opacity:.45">Unsettled copy</h1></main></body>""")
            result=settle_visible_text(page,checks=2,interval_ms=10)
            self.assertIn("prominent_heading_low_opacity",result["issues"])
            self.assertAlmostEqual(float(page.locator("#headline").evaluate(
                "e=>getComputedStyle(e).opacity")),.45,places=2)
        finally:
            page.close()

    def test_visible_image_can_finish_loading_without_faking_pixels(self):
        page=self.browser.new_page(viewport={"width":1280,"height":720})
        try:
            page.set_content("""<body><img id="hero" src="data:image/svg+xml,bad"
              style="width:400px;height:230px">
              <script>
              setTimeout(()=>{
                document.getElementById('hero').src='data:image/svg+xml,'+
                  encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="400" height="230"><rect width="400" height="230" fill="blue"/></svg>');
              },140)
              </script></body>""")
            result=settle_visible_images(page,timeout_ms=850)
            self.assertNotIn("incomplete_visible_images",result["issues"])
            self.assertEqual(result["readiness"]["pendingImages"],0)
            self.assertEqual(page.locator("#hero").evaluate("e=>e.naturalWidth"),400)
        finally:
            page.close()

    def test_visible_broken_image_is_detected(self):
        page=self.browser.new_page(viewport={"width":1280,"height":720})
        try:
            page.set_content("""<body><img src="data:image/png;base64,broken"
              style="width:500px;height:250px"/></body>""")
            result=quality_scan(page)
            self.assertIn("incomplete_visible_images",result["issues"])
        finally:
            page.close()

if __name__=="__main__":
    unittest.main()
