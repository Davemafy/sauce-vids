"""Adversarial offline probes for Sauce Basic crawler assumptions.

These checks establish that wheel events and DOM discovery encounter tricky
surfaces. They DO NOT certify the future film's overlay handling or visual QA.
"""
from __future__ import annotations
import os
from pathlib import Path
import sys
import time
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from basic_tour_discovery import read_page,trigger_lazy_content,discover_hover_navigation,normalized_landing_route

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright=None

CHROME="/opt/devmcp-browsers/chromium_headless_shell-1254/chrome-headless-shell-linux64/chrome-headless-shell"


@unittest.skipUnless(sync_playwright is not None,"Playwright required")
class BrowserAdversarialDiscovery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw=sync_playwright().start()
        try:
            executable=os.environ.get("SAUCE_CHROME_BIN") or CHROME
            cls.browser=cls.pw.chromium.launch(headless=True,
                    executable_path=executable if Path(executable).is_file() else None,
                    args=["--no-sandbox"])
        except Exception:
            cls.pw.stop()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def setUp(self):
        self.page=self.browser.new_page(viewport={"width":1280,"height":720})

    def tearDown(self):
        self.page.close()

    def test_safe_home_redirect_to_welcome_but_not_auth_or_external(self):
        self.assertEqual(normalized_landing_route(
            "https://sentry.io/","https://sentry.io/welcome/"),
            "https://sentry.io/welcome")
        for requested,dest in [
            ("https://sentry.io/","https://sentry.io/logout"),
            ("https://sentry.io/","https://evil.example/welcome"),
            ("https://sentry.io/","https://sentry.io/welcome?token=a"),
            ("https://sentry.io/projects","https://sentry.io/login")]:
            self.assertIsNone(normalized_landing_route(requested,dest))

    def test_lazy_content_requires_real_wheel(self):
        self.page.set_content("""<html><body style="height:1800px"><main>
          <section id="first" style="height:900px">First section</section>
          </main><script>
          window.addEventListener("wheel",()=>{
            if(!document.getElementById("lazy")) {
              const child=document.createElement("section");
              child.id="lazy";child.style.height="1000px";
              child.textContent="This section loaded after a real wheel";
              document.querySelector("main").appendChild(child);
            }
          },{once:true});
          </script></body></html>""")
        before=read_page(self.page,"https://test.example/")
        self.assertNotIn("lazy",before.anchor_ids)
        self.page.mouse.wheel(0,400)
        self.page.wait_for_timeout(130)
        after=read_page(self.page,"https://test.example/")
        self.assertIn("lazy",after.anchor_ids)
        self.assertGreater(after.height,before.height)

    def test_pinned_hero_state_requires_wheel_event(self):
        self.page.set_content("""<html><body style="height:2300px">
          <div id="pinned" style="position:sticky;top:0;height:160px;background:white">
          State 0</div>
          <script>
          let count=0;
          window.addEventListener('wheel',()=>{
            document.getElementById('pinned').textContent="Wheel "+(++count)
          });
          </script></body></html>""")
        self.page.evaluate("window.scrollTo(0,500)")
        self.assertEqual(self.page.locator("#pinned").inner_text(),"State 0")
        self.page.mouse.wheel(0,300)
        self.page.wait_for_timeout(120)
        self.assertTrue(self.page.locator("#pinned").inner_text().startswith("Wheel "))
        self.assertEqual(self.page.locator("#pinned").evaluate(
            "e=>getComputedStyle(e).position"),"sticky")

    def test_infinite_scroll_probe_has_step_bound(self):
        self.page.set_content("""<html><body><main>
        <section id="first" style="height:1100px"></section></main>
        <script>
        let count=0;
        addEventListener('wheel',()=>{
          if(count++<100) {
            const section=document.createElement('section');
            section.style.height='600px';section.id="more-"+count;
            document.querySelector("main").appendChild(section);
          }
        });
        </script></body></html>""")
        started=time.monotonic()
        result=trigger_lazy_content(self.page,max_steps=4)
        self.assertTrue(result["capped"])
        self.assertEqual(result["steps"],4)
        self.assertTrue(result["content_grew"])
        count=self.page.locator("main section").count()
        self.assertLessEqual(count,5)
        self.assertLess(time.monotonic()-started,3.0)
        self.assertEqual(self.page.evaluate("scrollY"),0)

    def test_hover_only_nav_child_is_discovered_without_click(self):
        self.page.set_content("""<html><body><header><nav>
          <button id="products">Products</button>
          </nav></header><main><h1>Homepage</h1></main>
          <script>
          window.__clicks=0;
          document.querySelector("#products").addEventListener("click",
            ()=>{ window.__clicks++ });
          document.querySelector("#products").addEventListener("mouseenter",()=>{
            if(!document.querySelector("#child")) {
              let a=document.createElement("a");
              a.id="child";a.href="/products";a.textContent="All products";
              document.querySelector("nav").append(a);
            }
          });
          </script></body></html>""")
        before=read_page(self.page,"https://test.example/")
        self.assertFalse(any(x.href=="/products" for x in before.links))
        after=discover_hover_navigation(self.page,before)
        self.assertTrue(any(x.href=="/products" for x in after.links))
        self.assertEqual(self.page.evaluate("window.__clicks"),0)

    def test_consent_wall_is_not_automatically_accepted(self):
        self.page.set_content("""<html><body><main><h1>A product</h1></main>
        <div id="cookie-banner" role="dialog"
             style="position:fixed;bottom:0;height:170px;background:#fff">
        Cookies <button id="accept">Accept all</button></div>
        <script>
          document.getElementById('accept').onclick=()=>{
            window.__consentAccepted=true;
            document.getElementById('cookie-banner').remove()
          };
        </script></body></html>""")
        self.page.mouse.wheel(0,100)
        self.assertTrue(self.page.locator("#cookie-banner").is_visible())
        self.assertIsNone(self.page.evaluate("window.__consentAccepted"))
        # This is a documented unresolved overlay, NOT a passed cleanup check.


if __name__=="__main__":
    unittest.main()
