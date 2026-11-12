import importlib.util
from pathlib import Path
import sys
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("plugin", ROOT/"__init__.py", submodule_search_locations=[str(ROOT)])
module = importlib.util.module_from_spec(spec)
sys.modules["plugin"] = module
spec.loader.exec_module(module)
from plugin import tools
from unittest.mock import MagicMock

class PluginTest(unittest.TestCase):
    def test_registration(self):
        class C:
            def __init__(self): self.registered=[]; self.skills=[]
            def register_tool(self,**kw): self.registered.append(kw)
            def register_skill(self,*a): self.skills.append(a)
        c=C();module.register(c)
        self.assertEqual([x["name"] for x in c.registered],["sauce_capture","sauce_render","sauce_inspect","sauce_scout","sauce_plan","sauce_review","sauce_auto"])
        self.assertEqual(c.skills[0][0],"sauce-director")
    def test_rejects_private_urls_and_unsafe_actions(self):
        import os
        os.environ["SAUCE_ALLOWED_HOSTS"]="www.brimble.io"
        for url in ("http://www.brimble.io","https://localhost","file:///etc/passwd","https://x:pw@www.brimble.io"):
            with self.assertRaises(ValueError): tools._url(url)
        for actions in ([{"type":"script"}],[{"type":"click_link","selector":""}]):
            with self.assertRaises(ValueError): tools._check_actions(actions)
    def test_click_link_heading_is_preserved(self):
        actions = tools._check_actions([{
            "type": "click_link",
            "selector": "a[href='/dashboard']",
            "expected_visible_heading": " Dashboard "
        }])
        self.assertEqual(actions[0]["expected_visible_heading"], "Dashboard")
        self.assertNotIn("expected_visible_heading", tools._check_actions([{
            "type": "click_link", "selector": "a[href='/dashboard']"
        }])[0])

    def test_heading_only_valid_for_click_link(self):
        for action in (
            {"type": "wait", "expected_visible_heading": "Dashboard"},
            {"type": "hover", "selector": "a", "expected_visible_heading": "Dashboard"},
            {"type": "click_link", "selector": "a", "expected_visible_heading": ""},
            {"type": "click_link", "selector": "a", "expected_visible_heading": "   "},
            {"type": "click_link", "selector": "a", "expected_visible_heading": 4},
            {"type": "click_link", "selector": "a", "expected_visible_heading": "A"*161},
        ):
            with self.subTest(action=action):
                with self.assertRaises(ValueError):
                    tools._check_actions([action])

    def test_waits_for_exact_visible_heading(self):
        page = MagicMock()
        tools._wait_for_expected_heading(page, "Dashboard")
        page.get_by_role.assert_called_once_with("heading", name="Dashboard", exact=True)
        page.get_by_role.return_value.first.wait_for.assert_called_once_with(
            state="visible", timeout=15000
        )

    def test_capture_uses_playwright_locator_first_property(self):
        import contextlib
        import tempfile
        import types
        from unittest.mock import MagicMock, patch
        class Locator:
            @property
            def first(self):
                return self
            def evaluate(self, *a, **kw):
                return None
            def bounding_box(self):
                return {"x":200,"y":220,"width":300,"height":80}
        locator=Locator()
        page=MagicMock()
        page.url="https://example.com"
        page.locator.return_value=locator
        page.video.save_as.side_effect=lambda path:Path(path).write_bytes(b"webm")
        context=MagicMock()
        context.new_page.return_value=page
        browser=MagicMock()
        browser.new_context.return_value=context
        playwright=MagicMock()
        playwright.chromium.launch.return_value=browser
        module_sync=types.ModuleType("playwright.sync_api")
        module_sync.sync_playwright=lambda:contextlib.nullcontext(playwright)
        module_main=types.ModuleType("playwright")
        module_main.sync_api=module_sync
        with tempfile.TemporaryDirectory() as d:
            with (patch.dict(sys.modules,{"playwright":module_main,
                                          "playwright.sync_api":module_sync}),
                  patch.object(tools,"_url",return_value="example.com"),
                  patch.object(tools,"ROOT",Path(d))):
                result=json.loads(tools.capture({
                  "project":"demo","url":"https://example.com",
                  "actions":[{"type":"focus","selector":"h1",
                              "label":"Observed heading","seconds":0.1}]}))
            self.assertTrue(result["ok"],result)
            self.assertEqual(result["events"][1]["label"],"Observed heading")
            self.assertIn("start_time",result["events"][1])

    def test_tool_errors_are_json(self):
        self.assertFalse(json.loads(tools.capture({"project":"../secrets","url":"https://www.brimble.io"}))["ok"])
        self.assertFalse(json.loads(tools.render({"run_id":"../secrets"}))["ok"])
if __name__=="__main__":unittest.main()
