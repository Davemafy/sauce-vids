import os,unittest
from unittest.mock import patch
from backend.product_explorer import allowed,normalize,workflow
from backend.url_engine import direction

class ExplorerContracts(unittest.TestCase):
    def setUp(self):
        self.source={
          'title':'Court Notice Checker','url':'https://sample.example.com/',
          'headings':[{'id':'h0','text':'Verify a notice','selector':'body > main:nth-of-type(1) > h1:nth-of-type(1)','y':90}],
          'controls':[
            {'id':'a0','text':'Paste text instead','selector':'body > button:nth-of-type(1)','kind':'button','tag':'button'},
            {'id':'a1','text':'Learn more','selector':'body > a:nth-of-type(1)','kind':'link','href':'https://sample.example.com/features'},
          ],
          'screenshot':'/nonexistent.jpg'
        }

    def test_allow_public_educational_actions(self):
        self.assertTrue(allowed(self.source['controls'][0],self.source['url']))
        self.assertTrue(allowed(self.source['controls'][1],self.source['url']))

    def test_reject_unsafe_and_cross_domain_actions(self):
        for text in ('Delete account','Submit application','Purchase plan','Log in','Upload ID'):
            with self.subTest(text=text):
                self.assertFalse(allowed({'kind':'button','text':text},self.source['url']))
        self.assertFalse(allowed({'kind':'link','text':'Docs',
            'href':'https://attacker.example.com/move'},self.source['url']))
        self.assertFalse(allowed({'kind':'link','text':'Account',
            'href':'https://sample.example.com/account'},self.source['url']))

    def test_untrusted_model_ids_cannot_inject_css(self):
        plan=normalize({'mode':'interactive','action_ids':['a0','a0','fake',
            'body > button:nth-of-type(1)'],'heading_ids':['h0','bad'],
            'title':'Observed demo','reason':'Safe'},self.source)
        self.assertEqual(plan['action_ids'],['a0'])
        self.assertEqual(plan['heading_ids'],['h0'])
        actions=workflow(plan,self.source)
        self.assertEqual([x['action'] for x in actions],['hover','click'])
        self.assertEqual(actions[0]['selector'],self.source['controls'][0]['selector'])

    def test_empty_model_output_yields_honest_showcase(self):
        plan=normalize({'mode':'interactive','action_ids':['nonexistent']},self.source)
        self.assertEqual(plan['mode'],'showcase')
        self.assertEqual(workflow(plan,self.source)[0]['action'],'hover')

    def test_missing_model_credentials_still_produces_evidence_only_plan(self):
        with patch.dict(os.environ,{'GEMINI_API_KEY':''}):
            plan,calls,source=direction(self.source)
        self.assertEqual((calls,plan['mode'],source),(0,'showcase','no-key-fallback'))

class ExplorerSafetyTests(unittest.TestCase):
    def control(self,**extra):
        return {'id':'a5','text':'Paste text instead','kind':'button',
                'button_type':'button','selector':'#check > button:nth-of-type(1)',
                **extra}

    def test_reversible_public_control_is_eligible(self):
        c=self.control()
        self.assertTrue(allowed(c,'https://seal-verify.vercel.app/'))
        self.assertFalse(allowed(dict(c,button_type='submit'), 'https://seal-verify.vercel.app/'))
        self.assertFalse(allowed(dict(c,text='Delete account'), 'https://seal-verify.vercel.app/'))
        self.assertFalse(allowed(dict(c,text='Upload document'), 'https://seal-verify.vercel.app/'))

    def test_restrict_to_first_party_non_sensitive_get_links(self):
        base={'kind':'link','text':'Try the demo','href':'https://example.com/demo'}
        self.assertTrue(allowed(base,'https://example.com'))
        self.assertFalse(allowed(dict(base,href='https://other.example.com/demo'),'https://example.com'))
        self.assertFalse(allowed(dict(base,href='https://example.com/login'),'https://example.com'))
        self.assertFalse(allowed(dict(base,href='https://example.com/demo?token=abc'),'https://example.com'))

    def test_model_can_select_only_observed_ids(self):
        report={'title':'SEAL','controls':[self.control()],
                'headings':[{'id':'h0','text':'Check a court message',
                             'selector':'body > h1:nth-of-type(1)','y':180}]}
        planned=normalize({'mode':'interactive','action_ids':['a5','a999'],
                          'heading_ids':['h0','fake'],'title':'Recorded demo'},report)
        self.assertEqual(planned['action_ids'],['a5'])
        self.assertEqual(planned['heading_ids'],['h0'])
        actions=workflow(planned,report)
        self.assertEqual([x['action'] for x in actions],['hover','click'])
        self.assertEqual(actions[0]['expect_selector'],report['controls'][0]['selector'])
        self.assertFalse(any(x['action'] in ('fill','submit','upload') for x in actions))
        unknown=normalize({'mode':'interactive','action_ids':['invented']},report)
        self.assertEqual(unknown['mode'],'showcase')


if __name__=='__main__':unittest.main()
