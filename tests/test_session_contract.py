"""No external dependencies: trace safety and replay preconditions."""
from __future__ import annotations
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from session_contract import safe_url,validate_actions,verify_package,cursor_class


class SessionContractTests(unittest.TestCase):
    def test_safe_url_strips_credentials_tokens_and_fragment(self):
        self.assertEqual(safe_url('https://user:pass@example.com/path?access_token=abc#secret'),
                         'https://example.com/path')

    def test_safe_url_keeps_local_fixture(self):
        self.assertEqual(safe_url('file:///home/test/demo.html'),
                         'file:///home/test/demo.html')

    def test_unsupported_protocol_rejected(self):
        with self.assertRaises(ValueError):
            safe_url('javascript:alert(1)')

    def test_password_workflow_requires_separate_channel(self):
        with self.assertRaisesRegex(ValueError,'Sensitive'):
            validate_actions([{'action':'fill','selector':'#password',
                               'value':'redacted','secret':True}])

    def test_missing_target_rejected(self):
        with self.assertRaises(ValueError):
            validate_actions([{'action':'click'}])

    def test_unsupported_workflow_rejected(self):
        with self.assertRaises(ValueError):
            validate_actions([{'action':'run_shell','value':'whoami'}])

    def test_approach_requires_real_target(self):
        validate_actions([{'action':'approach','selector':'#start',
                           'duration_ms':650}])
        with self.assertRaisesRegex(ValueError,'Missing'):
            validate_actions([{'action':'approach'}])

    def test_visual_expectation_is_allowed(self):
        validate_actions([{'action':'click','selector':'#open',
                           'expect_selector':'[role=dialog]'}])

    def test_cursor_categories(self):
        self.assertEqual(cursor_class('pointer'),'pointer')
        self.assertEqual(cursor_class('text'),'text')
        self.assertEqual(cursor_class('vertical-text'),'text')
        self.assertEqual(cursor_class('none'),'none')
        self.assertEqual(cursor_class('auto'),'default')
        self.assertEqual(cursor_class(None),'default')

    def example(self,folder):
        d=Path(folder)
        (d/'states').mkdir()
        image=b'FAKE PNG BYTES FOR HASH CHECK'
        (d/'states'/'000-start.png').write_bytes(image)
        return {
            'schema':'sauce.session.v1','source_url':'file:///fixture.html',
            'page':{'viewport':[1280,720],'dpr':2},
            'states':[{'name':'start','file':'000-start.png',
                       'sha256':hashlib.sha256(image).hexdigest()}],
            'workflow':[{'action':'click','selector':'#launch'}],
            'events':[{'t':1,'type':'pointermove'},
                      {'t':2,'type':'pointerdown'}],
        }

    def test_valid_source_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=self.example(tmp)
            self.assertEqual(verify_package(source,Path(tmp))['dpr'],2)

    def test_tampered_screenshot_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=self.example(tmp)
            (Path(tmp)/'states'/'000-start.png').write_bytes(b'TAMPERED')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):
                verify_package(source,Path(tmp))

    def test_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=self.example(tmp)
            source['states'][0]['file']='../../private.png'
            with self.assertRaises(ValueError):
                verify_package(source,Path(tmp))

    def test_nonmonotone_events_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=self.example(tmp)
            source['events'][1]['t']=0
            with self.assertRaisesRegex(ValueError,'Nonmonotone'):
                verify_package(source,Path(tmp))

    def test_input_values_cannot_be_serialized_into_trace(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=self.example(tmp)
            source['workflow'][0]['value']='secret'
            with self.assertRaisesRegex(ValueError,'Sensitive'):
                verify_package(source,Path(tmp))

if __name__=='__main__':
    unittest.main()
