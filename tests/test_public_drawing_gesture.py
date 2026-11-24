import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.public_drawing_gesture import select_drawing_route, run, render_admitted


class PublicDrawingGestureTests(unittest.TestCase):
    def setUp(self):
        self.url="https://example.com/"
        self.page={"url":self.url+"drawing","title":"Freehand SVG drawing tool",
                   "text":"Pick a brush and start drawing"}
        self.research={"requested_url":self.url,"pages":[self.page]}

    @patch("backend.public_drawing_gesture.validate_public_url")
    def test_observed_unique_route(self, validate):
        self.assertEqual(select_drawing_route(self.research),self.page)
        validate.assert_called_once_with(self.page["url"])
        for pages in ([],[self.page,self.page],
                      [{**self.page,"url":"https://other.test/drawing"}],
                      [{**self.page,"url":self.url+"auth/drawing"}],
                      [{**self.page,"text":"Marketing only"}]):
            with self.assertRaises(ValueError):
                select_drawing_route({**self.research,"pages":pages})

    def test_no_candidate_never_captures_or_calls_model(self):
        with tempfile.TemporaryDirectory() as tmp, \
             patch("backend.public_drawing_gesture.discover_public_product",
                   return_value={**self.research,"pages":[]}), \
             patch("backend.public_drawing_gesture.capture") as capture, \
             patch("backend.public_drawing_gesture.evaluate") as evaluate:
            out=Path(tmp)/"run"
            result=run(self.url,out,":210")
            self.assertEqual(result["decision"],"not_admitted")
            self.assertFalse(result["production_ready"])
            capture.assert_not_called()
            evaluate.assert_not_called()

    def test_unadmitted_checkpoint_never_renders(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);(out/"editorial").mkdir()
            review={"admitted_id":None,"decision":None}
            (out/"editorial/decision.json").write_text(json.dumps(review))
            (out/"receipt.json").write_text(json.dumps({
                "schema":"sauce-public-drawing-research-v1",
                "decision":"editorial_not_admitted","editorial":review}))
            with patch("backend.public_drawing_gesture.subprocess.run") as spawn:
                with self.assertRaisesRegex(ValueError,"No admitted"):
                    render_admitted(out)
                spawn.assert_not_called()


if __name__=="__main__":unittest.main()
