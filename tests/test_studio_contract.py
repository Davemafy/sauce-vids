"""Studio JSON is explicitly validated before any subprocess runs."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]/"studio"
spec=importlib.util.spec_from_file_location("studio_contract",ROOT/"render_project.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
EXAMPLE=json.loads((ROOT/"examples/brimble-first-scene.json").read_text())

class StudioContractTests(unittest.TestCase):
    def valid(self, project):
        with patch.object(module,"approved_file",return_value=Path("/tmp/sample.mp4")):
            with patch.object(module,"_duration",return_value=(19.8,1920,1080)):
                return module.validate(project,"ffprobe")

    def test_valid_scene(self):
        config=self.valid(EXAMPLE)
        self.assertEqual(config["window"]["width"],1490)
        self.assertEqual(config["window"]["x"],215)
        self.assertEqual(config["window"]["y"],180)
        self.assertEqual(config["window"]["height"],838)

    def test_rejects_traversal_and_remote_paths(self):
        for name in ("../bad.mp4","footage/../bad.mp4",
                     "footage/a/b.mp4","https://malicious.test/file.mp4"):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    module.approved_file("footage",name)

    def test_rejects_unavailable_features_and_unsafe_composition(self):
        def mutations():
            return [
                lambda x: x["canvas"].update(width=9999),
                lambda x: x["canvas"].update(duration_frames=1000),
                lambda x: x["scenes"][0]["browser"].update(x=1800),
                lambda x: x["scenes"][0]["browser"].update(aspect_ratio=1.6),
                lambda x: x["scenes"][0]["browser"].update(radius=60),
                lambda x: x["scenes"][0]["browser"].update(chrome="unknown"),
                lambda x: x["scenes"][0]["camera"].append(
                  {"frame":45,"scale":1.3,"focus_x":0.5,"focus_y":0.5}),
                lambda x: x["scenes"].append(copy.deepcopy(x["scenes"][0])),
                lambda x: x["background"].update(preset="not-real"),
                lambda x: x["audio"].update(volume=2),
            ]
        for mutation in mutations():
            data=copy.deepcopy(EXAMPLE)
            mutation(data["project"])
            with self.subTest(mutation=repr(mutation)):
                with self.assertRaises(ValueError):
                    self.valid(data)

    def test_rejects_tiny_browser_even_when_agent_requests_it(self):
        data=copy.deepcopy(EXAMPLE)
        data["project"]["scenes"][0]["browser"]["width"]=850
        with self.assertRaisesRegex(ValueError,"framing is invalid"):
            self.valid(data)

    def test_refuses_to_enlarge_source_pixels(self):
        with patch.object(module,"approved_file",return_value=Path("/tmp/sample.mp4")):
            with patch.object(module,"_duration",return_value=(20,1440,810)):
                with self.assertRaisesRegex(ValueError,"smaller than the displayed"):
                    module.validate(EXAMPLE,"ffprobe")

    def test_real_media_ratio_must_match_scene(self):
        with patch.object(module,"approved_file",return_value=Path("/tmp/sample.mp4")):
            with patch.object(module,"_duration",return_value=(20,1440,900)):
                with self.assertRaisesRegex(ValueError,"aspect ratio differs"):
                    module.validate(EXAMPLE,"ffprobe")
if __name__ == "__main__": unittest.main()
