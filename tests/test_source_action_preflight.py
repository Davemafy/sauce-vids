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
