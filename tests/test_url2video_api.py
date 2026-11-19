"""No third-party test framework needed; must run in unittest CI."""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.capture_safety import validate_public_url
from backend.url2video import validate_direction,workflow_for,direct_once,NeedsKey
from backend.product_explorer import allowed, normalize, workflow
from backend.url_engine import direction

class UrlToVideoTests(unittest.TestCase):
    def test_reject_local_and_sensitive_urls(self):
        for url in ('http://127.0.0.1/', 'http://localhost/', 'http://10.1.2.3/',
                    'http://169.254.169.254/latest/meta-data',
                    'file:///etc/passwd','https://example.com:1234/',
                    'https://bob:secret@example.com/',
                    'https://example.com/private?token=secret'):
            with self.subTest(url=url):
                with self.assertRaises(ValueError): validate_public_url(url)

    def test_reject_private_dns_rebinding(self):
        with patch('scripts.capture_safety.socket.getaddrinfo',return_value=[
          (2,1,6,'',('93.184.215.14',443)),
          (2,1,6,'',('192.168.1.1',443))]):
            with self.assertRaises(ValueError):
                validate_public_url('https://some-public-looking-host.example.org/')

    def test_director_cannot_make_up_section(self):
        source={"heading":[{"id":0,"text":"Workflow","tag":"h2","y":900}]}
        with self.assertRaises(ValueError):
            validate_direction({"decision":"render","heading_ids":[999],
                 "reason":"test","title":"a","story":"b"},source)

    def test_director_can_decline_auth_gated_site(self):
        source={"heading":[{"id":0,"text":"Marketing","tag":"h1","y":0}]}
        plan=validate_direction({"decision":"needs_access","heading_ids":[],
            "reason":"Only sign in shown","title":"a","story":"b"},source)
        self.assertEqual(plan["decision"],"needs_access")

    def test_workflow_uses_no_mutating_interactions(self):
        source={"heading":[{"id":0,"text":"Product demo","tag":"h2","y":900}]}
        plan={"decision":"render","heading_ids":[0],"reason":"public",
              "title":"Test","story":"Product interactive"}
        steps=workflow_for(plan,source)
        self.assertTrue(steps)
        self.assertTrue({a["action"] for a in steps}.issubset({"scroll","hover"}))
        self.assertTrue(all(a.get("expect_selector")==a.get("selector")
                            for a in steps if a["action"]=="hover"))

    def test_public_slider_uses_one_recorded_drag_path(self):
        url = 'https://resend.com/pricing'
        slider = {'id': 'a0', 'text': 'Value Selector', 'kind': 'slider',
                  'selector': 'input[type=range]'}
        button = {'id': 'a1', 'text': 'Show example', 'kind': 'button',
                  'selector': 'button', 'controlled_panel': True}
        self.assertFalse(allowed({**slider, 'text': 'Pay with calculator'}, url))
        self.assertTrue(allowed(slider, url))
        report = {'title': 'Pricing', 'url': url, 'headings': [],
                  'controls': [button, slider]}
        with patch.dict(os.environ, {'GEMINI_API_KEY': ''}):
            plan, calls, _ = direction(report)
        self.assertEqual(calls, 0)
        self.assertEqual(plan['action_ids'], ['a0'])
        self.assertEqual([step['action'] for step in workflow(plan, report)], ['hover'])
        self.assertEqual(normalize({'mode': 'interactive', 'action_ids': ['a1', 'a0']},
                                   report)['action_ids'], ['a0'])

    def test_missing_key_does_not_generate_fake_direction(self):
        with patch.dict(os.environ,{"GEMINI_API_KEY":""}):
            with self.assertRaises(NeedsKey):
                direct_once({"screenshot":"/nonexistent"})

if __name__=="__main__":unittest.main()
