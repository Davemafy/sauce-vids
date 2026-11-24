"""Customer URL ingestion: real demo is not a marketing preview.

These tests exercise customer intent against observed public source controls.
No model-generated UI, selectors, user submissions or website fixtures are
used as rendered footage.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
import os

from backend.url_engine import execute, NoVerifiedProductAction


REPORT={
    "url":"https://demo.example/",
    "controls":[],
    "headings":[{"id":"h0","text":"Why it works","y":500}],
}
SHOWCASE={
    "mode":"showcase",
    "action_ids":[],
    "heading_ids":["h0"],
    "title":"Public product website",
    "reason":"No verified action"
}


class StopBeforeRecord(Exception):
    pass


class CustomerFilmIntentTests(unittest.TestCase):
    def test_default_customer_demo_denies_unsupported_showcase_before_capture(self):
        with TemporaryDirectory(prefix="sauce-customer-demo-") as tmp:
            with (patch.dict(os.environ,{"SAUCE_CINEMATIC_ONLY":"0"}),
                  patch("backend.url_engine.validate_public_url"),
                  patch("backend.url_engine.inspect",return_value=REPORT),
                  patch("backend.url_engine.direction",
                        return_value=(SHOWCASE,1,"provider-unavailable-fallback")),
                  patch("backend.url2video.previous_feedback",return_value=[]),
                  patch("backend.url_engine.subprocess.run") as runner):
                with self.assertRaises(NoVerifiedProductAction):
                    execute(REPORT["url"],Path(tmp),intent="product_demo")
                runner.assert_not_called()
                self.assertTrue((Path(tmp)/"direction.json").is_file())

    def test_marketing_preview_requires_explicit_intent(self):
        with TemporaryDirectory(prefix="sauce-customer-preview-") as tmp:
            with (patch.dict(os.environ,{"SAUCE_CINEMATIC_ONLY":"1"}),
                  patch("backend.url_engine.validate_public_url"),
                  patch("backend.url_engine.inspect",return_value=REPORT),
                  patch("backend.url_engine.direction",
                        return_value=(SHOWCASE,0,"no-key-fallback")),
                  patch("backend.url_engine.workflow",return_value=[]),
                  patch("backend.url2video.previous_feedback",return_value=[]),
                  patch("backend.url_engine.subprocess.run",
                        side_effect=StopBeforeRecord) as runner):
                with self.assertRaises(StopBeforeRecord):
                    execute(REPORT["url"],Path(tmp),intent="website_preview")
                runner.assert_called_once()
                self.assertEqual(
                    __import__("json").loads((Path(tmp)/"direction.json").read_text())["mode"],
                    "showcase")

    def test_unknown_intent_refused_before_network(self):
        with TemporaryDirectory(prefix="sauce-customer-invalid-") as tmp:
            with patch("backend.url_engine.validate_public_url") as validate:
                with self.assertRaisesRegex(ValueError,"Unknown customer film intent"):
                    execute("https://demo.example/",Path(tmp),intent="auto_publish")
                validate.assert_not_called()
                self.assertFalse((Path(tmp)/"direction.json").exists())


if __name__=="__main__":
    unittest.main()
