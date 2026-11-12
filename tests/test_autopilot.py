"""Test the fully automatic first-cut director without requiring live browser access."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("autotest_plugin",ROOT/"__init__.py",submodule_search_locations=[str(ROOT)])
mod=importlib.util.module_from_spec(spec);sys.modules["autotest_plugin"]=mod;spec.loader.exec_module(mod)
from autotest_plugin import autopilot, tools, director


class AutoTest(unittest.TestCase):
    def test_selects_actual_heading_selectors_and_skips_footer(self):
        observed={"document_height":3100,
                  "headings":[
                      {"tag":"H1","text":"Build a better product","selector":"#hero","document_y":80},
                      {"tag":"H2","text":"See product intelligence","selector":"#intel","document_y":900},
                      {"tag":"H2","text":"Automate your workflows","selector":"#flows","document_y":1610},
                      {"tag":"H2","text":"Meet the team","selector":"#team","document_y":2400},
                      {"tag":"H2","text":"Contact us","selector":"#contact","document_y":2999}],
                  "controls":[{"type":"click_tab","selector":"[role='tab']","label":"Examples"}]}
        actions=autopilot.select_actions(observed,20)
        self.assertEqual(actions[0]["type"],"wait")
        self.assertEqual([a.get("selector") for a in actions if a["type"]=="focus"],
                         ["#intel","#flows","#team"])
        self.assertFalse(any(a.get("selector")=="#contact" for a in actions))
        self.assertEqual(actions[-1]["type"],"click_tab")

    def test_prefers_illustrated_feature_sequence_to_generic_footer(self):
        observed={"document_height":3200,"controls":[],
                  "headings":[
                      {"tag":"H3","text":"Launch with one click","selector":"#f1","document_y":600},
                      {"tag":"H3","text":"Watch deployment logs","selector":"#f2","document_y":830},
                      {"tag":"H3","text":"Fix a pull request","selector":"#f3","document_y":1100},
                      {"tag":"H3","text":"Watch a website get built","selector":"#f4","document_y":1440},
                      {"tag":"H2","text":"You ask. It works. You stay in charge.",
                       "selector":"#generic","document_y":1950}]}
        actions=autopilot.select_actions(observed,20)
        self.assertEqual([a.get("selector") for a in actions if a["type"]=="focus"],
                         ["#f1","#f2","#f3","#f4"])
        self.assertGreater(actions[1]["seconds"],2.2)

    def test_fallback_scrolling_for_sparse_heading_pages(self):
        observed={"document_height":4200,"headings":[],"controls":[]}
        actions=autopilot.select_actions(observed,20)
        self.assertTrue(any(a["type"]=="scroll" for a in actions))
        self.assertLessEqual(len(actions),24)

    def test_rejects_invalid_or_fabricated_actions(self):
        bad={"document_height":9000,"headings":[
           {"tag":"H2","text":"Preview the product","selector":None,"document_y":1200}
        ]}
        actions=autopilot.select_actions(bad,20)
        self.assertFalse(any(a["type"]=="focus" for a in actions))
        with self.assertRaises(ValueError):
            autopilot.select_actions({"headings":"fake"},20)

    def test_uses_observed_event_timing_for_clips(self):
        events=[
          {"type":"page","time":1.0},
          {"type":"wait","start_time":1.0,"time":3.3},
          {"type":"focus","start_time":3.3,"time":6.2,"label":"Actual headline",
           "position":{"x":1000,"y":350}},
          {"type":"focus","start_time":6.2,"time":9.1,"label":"Another headline",
           "position":{"x":720,"y":450}},
        ]
        shots=autopilot.make_shots(events,10,20)
        self.assertEqual(len(shots),3)
        self.assertEqual(shots[1]["label"],"Actual headline")
        self.assertTrue(all(0<=s["start_s"]<s["end_s"]<=10 for s in shots))
        self.assertEqual(shots[0]["zoom"],1.0)
        self.assertGreater(shots[1]["focus_x"],0.5)

    def test_preserves_all_sections_under_length_limit(self):
        events=[{"type":"page","time":1},
                {"type":"wait","start_time":1,"time":3.5}]
        t=3.5
        for i in range(5):
            events.append({"type":"focus","start_time":t,"time":t+4.8,
                           "label":"Feature "+str(i),
                           "position":{"x":400 if i%2 else 1000,"y":450}})
            t+=4.8
        shots=autopilot.make_shots(events,t+1,20)
        self.assertEqual(len(shots),6)
        self.assertEqual(shots[-1]["label"],"Feature 4")
        self.assertLessEqual(sum(s["end_s"]-s["start_s"] for s in shots),20.01)

    def test_output_target_bounds(self):
        for value in (0,7,40,float("nan")):
            with self.subTest(value=value):
                with patch.object(tools,"_url",return_value="example.com"):
                    reply=json.loads(autopilot.run({"url":"https://example.com",
                        "duration_seconds":value}))
                self.assertFalse(reply["ok"])
                self.assertEqual(reply["stage"],"validate")

    def test_url_to_video_contract_with_tool_receipts(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)/"demo-fixture"
            folder.mkdir()
            original_root=tools.ROOT
            tools.ROOT=Path(d)
            try:
                scout={"ok":True,"scout_id":"demo-scout-abcd",
                       "document_height":1800,
                       "headings":[{"tag":"H2","text":"Meet the product",
                         "selector":"#feature","document_y":800}],"controls":[]}
                capture={"ok":True,"run_id":"demo-fixture",
                         "events":[{"type":"page","time":1},
                            {"type":"wait","start_time":1,"time":3.2},
                            {"type":"focus","start_time":3.2,"time":5.5,
                             "label":"Meet the product","position":{"x":720,"y":420}}]}
                planned={"ok":True,"edit_plan":str(folder/"edit-plan.json"),
                         "shots":[{"start_s":1.08,"end_s":3.12}]}
                rendered={"ok":True,"video":str(folder/"final.mp4")}
                review={"ok":True,"duration_s":8.5,"frames":[{"time_s":2,"file":"a.jpg"}],
                        "black_intervals":[]}
                inspect={"ok":True,"video_metadata":{"streams":[
                    {"codec_type":"video","width":1920,"height":1080}]}}
                with (patch.object(tools,"_url",return_value="example.com"),
                      patch.object(director,"scout",return_value=json.dumps(scout)),
                      patch.object(tools,"capture",return_value=json.dumps(capture)),
                      patch.object(director,"_duration",return_value=9),
                      patch.object(director,"plan",return_value=json.dumps(planned)),
                      patch.object(tools,"render",return_value=json.dumps(rendered)),
                      patch.object(director,"review",return_value=json.dumps(review)),
                      patch.object(tools,"inspect",return_value=json.dumps(inspect))):
                    reply=json.loads(autopilot.run({"url":"https://example.com",
                        "project":"demo","duration_seconds":10}))
                self.assertTrue(reply["ok"], reply)
                self.assertEqual(reply["video"], str(folder/"final.mp4"))
                self.assertEqual(reply["shots"],1)
                self.assertFalse(reply["visual_art_direction_verified"])
                self.assertTrue((folder/"auto-report.json").is_file())
            finally:
                tools.ROOT=original_root

if __name__=="__main__":unittest.main()
