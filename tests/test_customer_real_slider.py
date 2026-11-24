"""Customer URL-to-video: accessible real sliders, not AI-invented actions.

This local HTML fixture is a regression test only. Actual customer acceptance
also runs against a fresh external site via the normal one-URL API.
"""
from pathlib import Path
import sys
import time
import unittest

from backend.product_explorer import JS, allowed, CHROME
from backend.live_capture import capture_slider
from backend.url_engine import apply_visible_action_verdict

HTML=r"""
<!doctype html><html lang="en"><head><style>
body{font:16px system-ui;margin:0;background:#f9f8fc}
[data-slot=slider]{position:absolute;left:190px;top:200px;width:330px;height:55px}
label{position:absolute;left:0;top:0}
output{position:absolute;right:0;top:0}
[data-slot=slider-track]{position:absolute;top:28px;left:0;width:330px;height:22px;
 background:#abc6ee;border-radius:20px}
[data-slot=slider-thumb]{position:absolute;top:0;left:30%;width:22px;height:22px;
 transform:translateX(-50%);background:#153c9c;border-radius:50%;touch-action:none}
.clip{position:absolute;overflow:hidden;width:1px;height:1px;clip-path:inset(50%)}
.clip input{position:absolute;left:-20px;top:-9px;width:128px;height:16px}
</style></head><body><main><div role="group" data-slot="slider">
<label id="volume-label">Volume</label><output data-slot="slider-output" for="volume" id="volume-output">30</output>
<div data-slot="slider-track"><div data-slot="slider-thumb">
<div class="clip"><input id="volume" type="range" aria-labelledby="volume-label"
min="0" max="100" step="1" value="30"></div>
</div></div></div></main>
<script>
const track=document.querySelector('[data-slot=slider-track]');
const thumb=document.querySelector('[data-slot=slider-thumb]');
const input=document.querySelector('input');
const output=document.querySelector('output');
let held=false;
const update=e=>{
 const x=Math.min(1,Math.max(0,(e.clientX-track.getBoundingClientRect().left)/
                                     track.getBoundingClientRect().width));
 const next=Math.round(x*100);
 input.value=String(next);
 thumb.style.left=(next)+'%';
 if(!window.freezeDependentOutput)output.textContent=String(next);
};
thumb.addEventListener('pointerdown',e=>{held=true;thumb.setPointerCapture(e.pointerId)});
thumb.addEventListener('pointermove',e=>{if(held)update(e)});
thumb.addEventListener('pointerup',e=>{if(held)update(e);held=false});
</script></body></html>
"""


class RealSliderCaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.playwright=sync_playwright().start()
        cls.browser=cls.playwright.chromium.launch(
            headless=True,executable_path=CHROME,
            args=['--no-sandbox','--disable-dev-shm-usage'])

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.ctx=self.browser.new_context(viewport={'width':1280,'height':720})
        self.page=self.ctx.new_page()
        self.page.set_content(HTML)

    def tearDown(self):
        self.ctx.close()

    def test_unlabelled_input_uses_real_accessible_label_and_visible_track(self):
        report=self.page.evaluate(JS)
        sliders=[c for c in report['controls'] if c['kind']=='slider']
        self.assertEqual(len(sliders),1)
        c=sliders[0]
        self.assertIn('Volume',c['text'])
        self.assertTrue(allowed(c,'https://example.com'))
        loc=self.page.locator(c['selector'])
        self.assertEqual(loc.count(),1)
        actual=capture_slider(self.page,loc,time.monotonic())
        self.assertIsNotNone(actual)
        self.assertEqual(actual['kind'],'slider_change')
        self.assertEqual(actual['price_change'],None)
        self.assertGreaterEqual(len(actual['pointer_samples']),25)
        self.assertGreater(actual['resultRect']['width'],6)
        self.assertEqual(actual['resultRect']['y'],200)
        self.assertNotEqual(self.page.locator('output').inner_text(),'30')
        self.assertEqual(int(self.page.locator('input').input_value()),
                         int(self.page.locator('output').inner_text()))

    def test_moving_thumb_without_dependent_visible_result_is_not_proof(self):
        self.page.evaluate('window.freezeDependentOutput=true')
        loc=self.page.locator('input[type=range]')
        self.assertIsNone(capture_slider(self.page,loc,time.monotonic()))
        self.assertNotEqual(self.page.locator('input').input_value(),'30')
        self.assertEqual(self.page.locator('output').inner_text(),'30')

    def test_sliders_in_forms_never_auto_discovered(self):
        self.page.evaluate("""() => {
            const form=document.createElement('form');
            document.querySelector('main').appendChild(form);
            form.appendChild(document.querySelector('[role=group]'));
        }""")
        self.assertFalse([c for c in self.page.evaluate(JS)['controls']
                          if c['kind']=='slider'])


class NativeCaptureAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.plan={'mode':'interactive','action_ids':['a0'],
                   'heading_ids':[],'title':'Slider','reason':'observed'}
        self.report={'url':'https://example.com/','controls':[
            {'id':'a0','kind':'slider'}],'headings':[]}
        self.proof={'schema':'sauce-source-action-preflight-v1',
                    'decision':'requires_recorded_slider_outcome',
                    'source_control_id':'a0','control_kind':'slider',
                    'source_url':'https://example.com/',
                    'human_film_approval':False}

    def test_deferred_proof_is_not_premium_claim(self):
        self.assertIs(apply_visible_action_verdict(
            self.plan,self.report,self.proof,cinematic_only=False),self.plan)
        with self.assertRaises(RuntimeError):
            apply_visible_action_verdict(
                self.plan,self.report,self.proof,cinematic_only=True)

    def test_deferral_cannot_be_forged_for_an_unobserved_control(self):
        for change in ({'source_control_id':'a9'},
                       {'control_kind':'button'},
                       {'source_url':'https://other.com/'},
                       {'human_film_approval':True}):
            with self.subTest(change=change):
                proof={**self.proof,**change}
                self.assertEqual(
                    apply_visible_action_verdict(
                        self.plan,self.report,proof)['mode'],'showcase')


if __name__=='__main__':
    unittest.main()
