"""A safe public click cannot count as a product demo without visible evidence."""
import unittest
import numpy as np
from pathlib import Path
from backend.source_action_preflight import (
    image_change,classify_visible_outcome,probe_public_action)


def plate():
    return np.full((720,1280,3),38,dtype=np.uint8)


def state(text='same',dialog=0):
    return {'visible_content_hash':text,'aria_controls_hash':'same',
            'dialog_count':dialog,'url_path':'/'}


class VisualOutcomeProof(unittest.TestCase):
    def test_meaningful_dom_and_large_real_visual_change(self):
        before=plate();steady=before.copy();after=before.copy()
        after[100:600,230:1000,:]=(175,123,211)
        proof=classify_visible_outcome(before,steady,after,state('old'),state('new'))
        self.assertEqual(proof['decision'],'visible_outcome_candidate')
        self.assertFalse(proof['human_film_approval'])
        self.assertGreater(proof['change_above_baseline'],.2)

    def test_giant_canvas_visual_change_can_be_a_candidate_without_new_text(self):
        before=plate();after=before.copy()
        after[80:550,200:1050,:]=(219,161,60)
        proof=classify_visible_outcome(before,before.copy(),after,state(),state())
        self.assertEqual(proof['decision'],'visible_outcome_candidate')
        self.assertFalse(proof['human_film_approval'])

    def test_modal_text_change_but_no_significant_pixels_fails(self):
        before=plate();after=before.copy()
        after[120:135,240:260,:]=220
        proof=classify_visible_outcome(before,before.copy(),after,state('old'),state('new'))
        self.assertEqual(proof['decision'],'no_proven_visible_outcome')

    def test_animated_background_baseline_does_not_qualify(self):
        before=plate();steady=before.copy();after=before.copy()
        steady[100:600,200:1000,:]=(170,170,170)
        after[100:600,200:1000,:]=(170,170,170)
        proof=classify_visible_outcome(before,steady,after,state(),state())
        self.assertEqual(proof['decision'],'no_proven_visible_outcome')
        self.assertGreater(proof['baseline_change_fraction'],.2)

    def test_static_site_rejected_even_when_click_event_claimed(self):
        before=plate()
        proof=classify_visible_outcome(before,before.copy(),before.copy(),state(),state())
        self.assertEqual(proof['decision'],'no_proven_visible_outcome')

    def test_reject_invalid_frames_and_unsafe_selection_before_browser(self):
        with self.assertRaises(ValueError):
            image_change(plate(),plate()[:300])
        source={'url':'https://example.com','controls':[
            {'id':'a0','kind':'button','text':'Submit application',
             'button_type':'submit','selector':'#send','in_form':True}]}
        with self.assertRaises(ValueError):
            probe_public_action('https://example.com',source,'a0',Path('/tmp/test-sauce-unwanted'))
        with self.assertRaises(ValueError):
            probe_public_action('https://example.com',source,'a999',Path('/tmp/test-sauce-unwanted'))


if __name__=='__main__':
    unittest.main()


class RealPipelineDecision(unittest.TestCase):
    def test_actual_proof_keeps_only_verified_interaction(self):
        from backend.url_engine import apply_visible_action_verdict
        plan={'mode':'interactive','action_ids':['a0'],'heading_ids':['h0'],
              'title':'Sample','reason':'real visible action'}
        report={'title':'Sample','url':'https://example.com/',
            'controls':[{'id':'a0','kind':'button','text':'Show example',
                         'button_type':'button','selector':'#show','in_form':False}],
            'headings':[{'id':'h0','selector':'h1','text':'Sample'}]}
        accepted=apply_visible_action_verdict(
            plan,report,{'decision':'visible_outcome_candidate'},cinematic_only=True)
        self.assertEqual(accepted['mode'],'interactive')
        downgraded=apply_visible_action_verdict(
            plan,report,{'decision':'no_proven_visible_outcome'})
        self.assertEqual(downgraded['mode'],'showcase')
        self.assertEqual(downgraded['action_ids'],[])
        with self.assertRaisesRegex(RuntimeError,'stopped before recording'):
            apply_visible_action_verdict(plan,report,{'decision':'no_proven_visible_outcome'},
                                         cinematic_only=True)


class AuthenticationBarrierTests(unittest.TestCase):
    def test_observed_theme_picker_login_dialog(self):
        from backend.source_action_preflight import authentication_barrier
        self.assertTrue(authentication_barrier([{
            "text": "Welcome back\nSign in to your account to continue\nContinue with Google\nContinue with GitHub",
            "password": False}]))
        self.assertTrue(authentication_barrier([{"text": "Authentication is required"}]))
        self.assertTrue(authentication_barrier([{"text": "Sign in", "password": True}]))

    def test_ordinary_setup_and_preview_are_not_authentication_barriers(self):
        from backend.source_action_preflight import authentication_barrier
        self.assertFalse(authentication_barrier([]))
        self.assertFalse(authentication_barrier([{"text": "Connect your agent\nCopy configuration"}]))
        self.assertFalse(authentication_barrier([{"text": "Preview component\nSign in button"}]))
        self.assertFalse(authentication_barrier([{"text": "Welcome back\nYour dashboard"}]))

    def test_authentication_receipt_cannot_admit_interactive_film(self):
        from backend.url_engine import apply_visible_action_verdict
        plan={"mode":"interactive","action_ids":["a0"],"heading_ids":["h0"],"title":"Sample"}
        report={"title":"Sample","url":"https://example.com/","controls":[],
                "headings":[{"id":"h0","selector":"h1","text":"Sample"}]}
        proof={"decision":"authentication_required"}
        self.assertEqual(apply_visible_action_verdict(plan,report,proof)["mode"],"showcase")
        with self.assertRaisesRegex(RuntimeError,"stopped before recording"):
            apply_visible_action_verdict(plan,report,proof,cinematic_only=True)


class ReadOnlyAccessDiscoveryTests(unittest.TestCase):
    def test_direct_auth_route_requires_visible_form_evidence(self):
        from backend.source_action_preflight import standalone_authentication_barrier
        from unittest.mock import Mock
        p=Mock(url="https://example.com/login")
        p.evaluate.return_value=True
        self.assertTrue(standalone_authentication_barrier(p))
        p.evaluate.return_value=False
        self.assertFalse(standalone_authentication_barrier(p))
        p.url="https://example.com/components/login-preview"
        p.evaluate.reset_mock()
        self.assertFalse(standalone_authentication_barrier(p))
        p.evaluate.assert_not_called()

    def test_auth_link_evidence_is_not_an_action_or_proof_of_access(self):
        from backend.source_action_preflight import observed_auth_entry_links
        from urllib.robotparser import RobotFileParser
        from unittest.mock import Mock
        def link(label,href,visible=True,safe=True):
            a=Mock()
            a.is_visible.return_value=visible
            a.evaluate.return_value=safe
            a.inner_text.return_value=label
            a.get_attribute.return_value=href
            return a
        p=Mock(url="https://example.com/")
        p.locator.return_value.all.return_value=[
            link("Sign in","/login"),
            link("Sign in","/login"),
            link("Create an account","/signup"),
            link("Sign in","https://other.example.com/login"),
            link("Sign in","/login?token=secret"),
            link("Sign in","/login#fragment"),
            link("Sign in","/private/login"),
            link("Sign in","/hidden/login",False),
            link("Sign in","/sensitive/login",safe=False),
            link("Preview","/login"),
            link("Sign in","/editor"),
        ]
        robots=RobotFileParser()
        robots.parse(["User-agent: *","Disallow: /private/"])
        self.assertEqual(observed_auth_entry_links(p,p.url,robots),[
            {"url":"https://example.com/login","label":"Sign in","classification":"observed_account_entry"},
            {"url":"https://example.com/signup","label":"Create an account","classification":"observed_account_entry"},
        ])
        p.goto.assert_not_called()
        p.click.assert_not_called()

    def test_chromium_default_submit_type_is_detected_without_filling_form(self):
        from backend.source_action_preflight import standalone_authentication_barrier
        from backend.product_explorer import CHROME
        from playwright.sync_api import sync_playwright
        import pytest
        if not Path(CHROME).is_file():
            pytest.skip("Chromium not installed")
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=str(CHROME),headless=True,args=["--no-sandbox"])
            try:
                page=browser.new_page()
                page.route("https://fixture.example.com/**",lambda route:route.fulfill(
                    status=200,content_type="text/html",body='<form><input type="email"><input type="password"><button>Sign in</button></form>'))
                page.goto("https://fixture.example.com/login")
                self.assertTrue(standalone_authentication_barrier(page))
                page.locator("form").evaluate("f=>f.style.display='none'")
                self.assertFalse(standalone_authentication_barrier(page))
                page.goto("https://fixture.example.com/preview")
                self.assertFalse(standalone_authentication_barrier(page))
            finally:browser.close()
