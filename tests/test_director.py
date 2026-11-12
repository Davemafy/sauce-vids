"""Focused tests for Hermes's v0.2 scout/plan/render/review contracts."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sauce_test",ROOT/"__init__.py",submodule_search_locations=[str(ROOT)])
pkg = importlib.util.module_from_spec(spec)
sys.modules["sauce_test"] = pkg
spec.loader.exec_module(pkg)
from sauce_test import director, tools, schemas, autopilot


class DirectorTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original_root = tools.ROOT
        tools.ROOT = Path(self.temp.name)

    def tearDown(self):
        tools.ROOT = self.original_root
        self.temp.cleanup()

    def _recording(self):
        folder = tools._dir("brimble-test")
        (folder/"recording.webm").write_bytes(b"fake test fixture")
        return folder

    def test_registers_seven_declared_tools(self):
        declared = [schemas.CAPTURE, schemas.RENDER, schemas.INSPECT,
                    schemas.SCOUT, schemas.PLAN, schemas.REVIEW, schemas.AUTO]
        class Context:
            def __init__(self):
                self.tools = []
            def register_tool(self, **kwargs):
                self.tools.append(kwargs)
            def register_skill(self, *args):
                pass
        ctx=Context()
        pkg.register(ctx)
        self.assertEqual([x["name"] for x in ctx.tools],
                         [x["name"] for x in declared])
        self.assertEqual(len(ctx.tools),7)

    def test_tab_action_and_heading(self):
        parsed=tools._check_actions([{"type":"click_tab","selector":"[role=tab]",
            "expected_visible_heading":"Preview"}])
        self.assertEqual(parsed[0]["expected_visible_heading"],"Preview")
        with self.assertRaises(ValueError):
            tools._check_actions([{"type":"click_tab","selector":"", "seconds":1}])

    def test_edit_plan_persists_chronological_validated_shots(self):
        folder=self._recording()
        shots=[{"start_s":0,"end_s":2,"zoom":1.2,"focus_x":0.65,"focus_y":0.45,"label":"Opening"},
               {"start_s":3,"end_s":6,"zoom":1.0,"label":"Demo"}]
        with patch.object(director,"_duration",return_value=9):
            reply=json.loads(director.plan({"run_id":"brimble-test","shots":shots}))
        self.assertTrue(reply["ok"])
        self.assertEqual(reply["output_duration_s"],5)
        edl=json.loads((folder/"edit-plan.json").read_text())
        self.assertEqual(edl["shots"][0]["focus_x"],0.65)
        self.assertEqual(len(edl["shots"]),2)

    def test_rejects_overlapping_or_out_of_bounds_shots(self):
        self._recording()
        for shots in (
            [{"start_s":1,"end_s":2},{"start_s":1.8,"end_s":3}],
            [{"start_s":1,"end_s":80}],
            [{"start_s":0,"end_s":1,"zoom":10}],
            [{"start_s":0,"end_s":1,"focus_x":-1}],
            [{"start_s":0,"end_s":1,"label":"x"*121}]
        ):
            with self.subTest(shots=shots),patch.object(director,"_duration",return_value=9):
                self.assertFalse(json.loads(director.plan({"run_id":"brimble-test","shots":shots}))["ok"])

    def test_missing_plan_fails_without_rendering(self):
        self._recording()
        result=json.loads(tools.render({"run_id":"brimble-test","use_edit_plan":True}))
        self.assertFalse(result["ok"])
        self.assertIn("sauce_plan",result["error"])

    def test_asset_cannot_escape_directory(self):
        directory=Path(self.temp.name)/"licensed"
        directory.mkdir()
        (directory/"music.mp3").write_bytes(b"fake")
        with patch.dict(os.environ,{"SAUCE_ASSET_DIR":str(directory)}):
            self.assertEqual(director._asset("music.mp3",{".mp3"}), directory/"music.mp3")
            with self.assertRaises(ValueError):
                director._asset("../private.mp3",{".mp3"})
            with self.assertRaises(ValueError):
                director._asset("missing.mp3",{".mp3"})
            with self.assertRaises(ValueError):
                director._asset("music.mp3",{".wav"})

if __name__=="__main__":
    unittest.main()
