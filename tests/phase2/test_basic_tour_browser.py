"""Offline browser DOM evidence for Basic preflight (no external site requests)."""
from __future__ import annotations
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright=None
from basic_tour_discovery import read_page
from basic_tour_planner import TourContract,create_preflight


class BasicBrowserEvidenceTest(unittest.TestCase):
    @unittest.skipUnless(sync_playwright is not None,"Playwright not installed")
    def test_sections_and_real_nav_anchors_from_dom(self):
        with sync_playwright() as pw:
            executable=os.environ.get("SAUCE_CHROME_BIN") or (
                "/opt/devmcp-browsers/chromium_headless_shell-1254/"
                "chrome-headless-shell-linux64/chrome-headless-shell"
            )
            try:
                b=pw.chromium.launch(headless=True,
                    executable_path=executable if Path(executable).is_file() else None,
                    args=["--no-sandbox"])
            except Exception as exc:
                self.skipTest("Chromium unavailable: "+str(exc)[:90])
            try:
                page=b.new_page(viewport={"width":1280,"height":720})
                page.set_content("""
                  <html><head><title>Actual Fixture</title></head>
                  <body><header><nav>
                    <a href="#features">Features</a>
                    <a href="/pricing">Pricing</a>
                    <a href="#missing">Broken</a>
                  </nav></header><main>
                    <section id="features" style="min-height:1300px">
                      <h2>Real feature section</h2>
                      <p>A simple description of real software.</p>
                    </section></main></body></html>
                """)
                root="https://site.example.org/"
                item=read_page(page,root)
                self.assertIn("features",item.anchor_ids)
                self.assertGreater(item.height,1200)
                self.assertEqual(item.title,"Actual Fixture")
                self.assertEqual(item.links[0].area,"header")
                plan=create_preflight(TourContract(root),[item])
                self.assertEqual([a["id"] for a in plan["anchors"][root]],["features"])
                self.assertTrue(any(x["reason"]=="unresolved_anchor" for x in plan["skipped"]))
                self.assertTrue(any(x["reason"]=="not_observed_or_unreachable"
                    for x in plan["skipped"]))
            finally:
                b.close()


if __name__=="__main__":
    unittest.main()
