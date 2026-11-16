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

if __name__=='__main__':unittest.main()
