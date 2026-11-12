"""Tool bridge tests: Hermes decisions are validated, not inferred."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sauce_studio_test", ROOT/"__init__.py",
  submodule_search_locations=[str(ROOT)])
plugin = importlib.util.module_from_spec(spec)
sys.modules["sauce_studio_test"] = plugin
spec.loader.exec_module(plugin)
from sauce_studio_test import studio_tools, tools

EXAMPLE=json.loads((ROOT/"studio/examples/brimble-first-scene.json").read_text())["project"]

class StudioBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.folder=Path(self.tmp.name)
        self.runs=self.folder/"runs"
        self.stage=self.folder/"studio-public"
        self.runs.mkdir()
        self.stage.mkdir()
        self.patches=[
            patch.object(tools,"ROOT",self.runs),
            patch.object(studio_tools.engine,"STATIC",self.stage),
            patch.object(studio_tools.engine,"validate",return_value={"ok":True}),
        ]
        for p in self.patches:p.start()

    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.tmp.cleanup()

    def _captured(self):
        p=self.runs/"demo-123"
        p.mkdir(exist_ok=True)
        (p/"capture.json").write_text(json.dumps({"url":"https://www.example.com/app"}))
        (p/"final.mp4").write_bytes(b"authentic-recording-fixture")
        return p

    def test_compose_stages_only_actual_recorded_footage(self):
        self._captured()
        project=copy.deepcopy(EXAMPLE)
        project["scenes"][0]["browser"]["url"]="example.com/app"
        project["scenes"][0]["footage"]="../../fake.mp4"
        project.pop("audio",None)
        result=json.loads(studio_tools.compose({"run_id":"demo-123","project":project}))
        self.assertTrue(result["ok"],result)
        saved=json.loads((self.runs/"demo-123/studio-project.json").read_text())["project"]
        self.assertEqual(saved["scenes"][0]["footage"],"footage/demo-123.mp4")
        self.assertEqual(saved["provenance"]["source_url"],"https://www.example.com/app")
        self.assertEqual((self.stage/"footage/demo-123.mp4").read_bytes(),b"authentic-recording-fixture")

    def test_compose_prefers_unprocessed_webm_over_legacy_mp4(self):
        folder=self._captured()
        (folder/"recording.webm").write_bytes(b"native-1080p-webm")
        project=copy.deepcopy(EXAMPLE)
        project["scenes"][0]["browser"]["url"]="example.com/app"
        project.pop("audio",None)
        result=json.loads(studio_tools.compose({"run_id":"demo-123","project":project}))
        self.assertTrue(result["ok"],result)
        saved=json.loads((folder/"studio-project.json").read_text())["project"]
        self.assertEqual(saved["scenes"][0]["footage"],"footage/demo-123.webm")
        self.assertEqual((self.stage/"footage/demo-123.webm").read_bytes(),b"native-1080p-webm")

    def test_compose_rejects_spoofed_url(self):
        self._captured()
        project=copy.deepcopy(EXAMPLE)
        project.pop("audio",None)
        result=json.loads(studio_tools.compose({"run_id":"demo-123","project":project}))
        self.assertFalse(result["ok"])
        self.assertIn("must match",result["error"])

    def test_compose_requires_real_capture(self):
        result=json.loads(studio_tools.compose({"run_id":"unknown-1","project":EXAMPLE}))
        self.assertFalse(result["ok"])
        self.assertIn("capture receipt",result["error"])

    def test_preview_requires_saved_project(self):
        result=json.loads(studio_tools.preview({"run_id":"unknown-1","time_s":1}))
        self.assertFalse(result["ok"])
        self.assertIn("sauce_compose",result["error"])

    def test_tool_reports_finished_artifact(self):
        p=self._captured()
        (p/"studio-project.json").write_text(json.dumps({"project":EXAMPLE}))
        stage=self.folder/"studio"
        (stage/"node_modules/.bin").mkdir(parents=True)
        (stage/"node_modules/.bin/remotion").write_text("installed")
        with patch.object(studio_tools.engine,"STUDIO",stage):
            with patch.object(studio_tools.engine,"render",return_value={
                "ok":True,"file":str(p/"studio-final.mp4"),"width":1920,
                "height":1080,"bytes":27}):
                result=json.loads(studio_tools.render_project({"run_id":"demo-123"}))
        self.assertTrue(result["ok"],result)
        self.assertEqual(result["run_id"],"demo-123")
        self.assertEqual(result["width"],1920)

if __name__=="__main__":
    unittest.main()
