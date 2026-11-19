import unittest

from backend.beat_selector import select_story


def candidate(kind, y, *, score=45, product=True):
    return {"kind": kind, "score": score, "label": f"{kind} at {y}",
            "reason": "Measured evidence", "product_evidence": product,
            "pricing": kind == "pricing",
            "rect": {"x": 20, "y": y, "width": 400, "height": 280}}


class StoryDiagnosticTests(unittest.TestCase):
    def test_no_story_from_pricing_or_weak_ui_alone(self):
        candidates = [candidate("pricing", 0, product=False), candidate("media", 500, score=20)]
        self.assertEqual(select_story("https://example.com", candidates)["status"],
                         "insufficient_product_evidence")

    def test_distinct_secondary_preview_and_pricing_payoff(self):
        candidates = [candidate("widget", 0), candidate("widget", 3), candidate("media", 500),
                      candidate("pricing", 900, product=False)]
        plan = select_story("https://example.com", candidates)
        self.assertEqual(plan["status"], "ready")
        self.assertEqual([b["role"] for b in plan["beats"]],
                         ["product_ui", "secondary_ui_preview", "pricing_card"])
        self.assertEqual(plan["beats"][1]["source_rect"]["y"], 500)

    def test_verified_outcome_can_share_hook_region(self):
        hook, payoff = candidate("widget", 0), candidate("media", 500)
        interaction = {"type": "click", "target_rect": hook["rect"],
                       "verified_mutation": "aria-selected changed false → true"}
        plan = select_story("https://example.com", [hook, payoff], interaction)
        self.assertEqual(plan["status"], "ready")
        self.assertEqual(plan["beats"][1]["interaction"], interaction)
        self.assertEqual(plan["beats"][0]["source_rect"], plan["beats"][1]["source_rect"])

    def test_never_pad_a_two_beat_plan(self):
        plan = select_story("https://example.com", [candidate("media", 0), candidate("media", 500)])
        self.assertEqual(plan["status"], "insufficient_product_evidence")
        self.assertEqual(len(plan["beats"]), 2)


class PreflightTests(unittest.TestCase):
    def test_http_challenge_stops_before_browser_settle(self):
        from types import SimpleNamespace
        from backend.preflight import check_page

        for status in (403, 429, 503):
            with self.subTest(status=status):
                result = check_page(None, SimpleNamespace(status=status), "https://example.com")
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["reason"], "waf_challenge")
                self.assertEqual(result["signal"], f"http_{status}")

    def test_challenge_title_stops_before_browser_settle(self):
        from types import SimpleNamespace
        from backend.preflight import check_page

        page = SimpleNamespace(evaluate=lambda _: {"title": "Just a moment..."})
        result = check_page(page, SimpleNamespace(status=200), "https://example.com")
        self.assertEqual(result["signal"], "challenge_title")

    def test_normal_content_can_coexist_with_security_terms(self):
        from types import SimpleNamespace
        from backend.preflight import check_page

        page = SimpleNamespace(
            evaluate=lambda _: {"title": "Observability", "topText": "Debug access denied errors",
                                "meaningfulBlocks": 22, "marked": False},
            wait_for_load_state=lambda *args, **kwargs: None,
            wait_for_timeout=lambda _: None,
        )
        result = check_page(page, SimpleNamespace(status=200), "https://example.com")
        self.assertEqual(result["status"], "ready")


class InteractionProbeTests(unittest.TestCase):
    def test_click_records_visible_selected_state_below_fold(self):
        import os
        from pathlib import Path

        if not os.getenv("SAUCE_BROWSER_TEST"):
            self.skipTest("Browser verification is opt-in")
        from playwright.sync_api import sync_playwright
        from backend.product_explorer import CHROME
        from backend.story_diagnostic import _probe
        from backend.shot_scorer import discover_candidates, score_candidates

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=CHROME if Path(CHROME).is_file() else None,
                args=["--no-sandbox"],
            )
            try:
                context = browser.new_context(viewport={"width": 1280, "height": 720})
                context.route("**/*", lambda route: route.fulfill(
                    content_type="text/html",
                    body="""<style>
                    body { margin:0 } #schedule { margin:900px 0 0 100px; width:400px; height:200px }
                    button { width:100px; height:40px; background:white; font-size:18px }
                    button[aria-pressed=true] { background:teal }
                    </style><main><section id=schedule><button id=slot aria-pressed=false
                    onclick="this.setAttribute('aria-pressed','true')">10:30 AM</button><button>11:30 AM</button><button>12:30 PM</button>
                    </section><button>Get Rickrolled</button></main>""",
                ))
                page = context.new_page()
                page.goto("https://example.com/")
                candidates = score_candidates(discover_candidates(page))
                self.assertEqual(candidates[0]["selector"], "#schedule")
                self.assertEqual([c["label"] for c in candidates[0]["targets"]],
                                 ["10:30 AM", "11:30 AM", "12:30 PM"])
                page.close()
                rect = {"x": 100, "y": 900, "width": 400, "height": 200}
                target = {"x": 100, "y": 900, "width": 100, "height": 40}
                proof, crop = _probe(context, "https://example.com/", {
                    "selector": "#schedule", "rect": rect,
                    "targets": [{"selector": "#slot", "rect": target}],
                })
                self.assertEqual(proof["verified_mutation"], "aria-pressed changed false → true")
                self.assertEqual(proof["target_rect"], target)
                self.assertEqual(crop.size, (400, 200))
            finally:
                browser.close()
