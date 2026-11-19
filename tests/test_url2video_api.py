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
from backend.shot_scorer import crop_for_subject, select_beats

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

    def test_public_brimble_setup_is_scoped_to_the_homepage_and_non_form_button(self):
        url = 'https://www.brimble.io/'
        button = {'id': 'a0', 'text': 'Connect your agent', 'kind': 'button',
                  'tag': 'button', 'button_type': 'submit', 'in_form': False,
                  'selector': 'button'}
        self.assertTrue(allowed(button, url))
        self.assertFalse(allowed(button, 'https://example.com/'))
        self.assertFalse(allowed(button, url + 'account'))
        self.assertFalse(allowed({**button, 'in_form': True}, url))
        plan, calls, source = direction({'url': url, 'headings': [], 'controls': [button]})
        self.assertEqual((plan['action_ids'], calls, source), (['a0'], 0, 'verified-public-dialog'))

    def test_public_tabs_use_local_direction_across_origins(self):
        tab = {'id': 'a0', 'kind': 'tab', 'text': 'Profile',
               'selector': '#profile-tab', 'in_form': False}
        for url in ('https://getbootstrap.com/', 'https://www.w3.org/'):
            with self.subTest(url=url), patch.dict(os.environ, {'GEMINI_API_KEY': ''}):
                self.assertTrue(allowed(tab, url))
                self.assertFalse(allowed({**tab, 'in_form': True}, url))
                self.assertFalse(allowed({**tab, 'text': 'Sign in'}, url))
                report = {'url': url, 'headings': [], 'controls': [tab]}
                plan, calls, source = direction(report)
                self.assertEqual((plan['action_ids'], calls, source), (['a0'], 0, 'local-tab'))

    def test_subject_reel_needs_a_real_hook_and_three_distinct_regions(self):
        def candidate(selector, kind, y):
            return {'selector':selector, 'label':selector, 'kind':kind,
                    'rect':{'x':90, 'y':y, 'width':700, 'height':240},
                    'viewport':[1280,720], 'contrast':9, 'font_px':18,
                    'controls':0, 'times':0, 'word_count':12}
        hook = candidate('#calendar', 'widget', 220)
        overlap = candidate('#calendar-copy', 'value', 228)
        proof = candidate('#proof', 'value', 1480)
        detail = candidate('#command', 'code', 990)
        self.assertEqual(select_beats([hook, overlap, proof]), [])
        self.assertEqual(select_beats([proof, overlap, {**proof, 'kind':'media'}]), [])
        beats = select_beats([proof, overlap, detail, hook])
        self.assertEqual([b['selector'] for b in beats], ['#calendar', '#command', '#proof'])
        self.assertEqual([b['purpose'] for b in beats], ['hook', 'detail', 'payoff'])
        report = {'url':'https://example.com/', 'controls':[], 'headings':[], 'beats':beats}
        with patch.dict(os.environ, {'GEMINI_API_KEY':''}):
            plan, calls, source = direction(report)
        self.assertEqual((plan['beats'], calls, source), (beats, 0, 'local-subjects'))

    def test_subject_crop_fits_and_rejects_offscreen_regions(self):
        rect = {'x':690, 'y':420, 'width':330, 'height':210}
        x,y,w,h = crop_for_subject(rect,1280,720)
        self.assertEqual(w*9,h*16)
        self.assertLessEqual(x,rect['x'])
        self.assertGreaterEqual(y+h,rect['y']+rect['height'])
        with self.assertRaises(ValueError):
            crop_for_subject({**rect,'y':-1},1280,720)

    def test_missing_key_does_not_generate_fake_direction(self):
        with patch.dict(os.environ,{"GEMINI_API_KEY":""}):
            with self.assertRaises(NeedsKey):
                direct_once({"screenshot":"/nonexistent"})

if __name__=="__main__":unittest.main()
