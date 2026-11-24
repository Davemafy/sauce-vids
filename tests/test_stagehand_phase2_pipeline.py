"""Phase 2 agent director: source truth, causal camera and fail-closed orchestration."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.plan_stagehand_phase2 import actual_source,directed_plan


def fixture():
    e={"kind":"click","start":1.5,"end":1.6,"t":2.3,
       "evidence":"Original genuine browser click and source pixels",
       "targetRect":{"x":650,"y":900,"width":300,"height":60},
       "resultRect":{"x":1040,"y":540,"width":800,"height":720}}
    return {"cursorless":True,"capture_rect":{"width":2880,"height":1800},
        "duration":10.,"events":[e],
        "pointer_samples":[{"t":i*.05+.05,"x":700,"y":940} for i in range(40)],
        "provenance":{"capture":"Chromium X11 native DPR2 60fps"}}


class Phase2NativeDirectorTests(unittest.TestCase):
    def setup_temp(self,td):
        video=Path(td)/"real-source.mp4";video.write_bytes(b"test fixture only")
        manifest=Path(td)/"source-manifest.json"
        data=fixture()
        data["provenance"]["originalSourceSha256"]=hashlib.sha256(video.read_bytes()).hexdigest()
        manifest.write_text(json.dumps(data))
        return video,manifest

    def test_result_camera_starts_after_verified_real_outcome(self):
        with tempfile.TemporaryDirectory() as td:
            video,manifest=self.setup_temp(td)
            plan={"schema":"sauce-film-plan-v1","durationSeconds":10.,
                  "studioStage":{"camera":[],"payoff":{"mode":"detail"}}}
            with patch("scripts.plan_stagehand_phase2.direction",return_value=plan):
                changed,decision=directed_plan(video,manifest)
            keys=changed["studioStage"]["camera"]
            self.assertEqual(decision["strategy"],"source-native-causal-detail")
            self.assertLess(keys[1]["at"],2.3)
            self.assertEqual(keys[1]["center"],[.5,.5])
            self.assertEqual(keys[1]["viewScale"],1.)
            self.assertGreater(keys[2]["startAt"],2.3)
            self.assertEqual(keys[2]["focus"],"event:0:result")
            self.assertEqual(keys[-1]["viewScale"],1)
            self.assertTrue(changed["studioStage"]["motion"]["immersive"])
            self.assertEqual(changed["studioStage"]["motion"]["follow"]["eventIndices"],[0])

    def test_six_and_half_second_causal_edit_and_readable_hold(self):
        with tempfile.TemporaryDirectory() as td:
            video,manifest=self.setup_temp(td)
            info=json.loads(manifest.read_text())
            info["duration"]=6.5
            info["events"][0]["start"]=1.48
            info["events"][0]["end"]=1.67
            info["events"][0]["t"]=2.50
            manifest.write_text(json.dumps(info))
            baseline={"schema":"sauce-film-plan-v1","durationSeconds":6.5,
                      "studioStage":{"camera":[],"payoff":{"mode":"detail"}}}
            with patch("scripts.plan_stagehand_phase2.direction",return_value=baseline):
                plan,meta=directed_plan(video,manifest)
            keys=plan["studioStage"]["camera"]
            self.assertEqual(meta["strategy"],"source-native-causal-detail")
            self.assertGreater(keys[2]["startAt"],2.5)
            self.assertLess(keys[2]["at"],keys[3]["startAt"]-.7)
            self.assertEqual(keys[3]["at"],6.5)
            self.assertEqual(keys[1]["center"],[.5,.5])

    def test_short_one_action_source_valid_but_short_two_action_rejected(self):
        import source_event_director
        with tempfile.TemporaryDirectory() as td:
            video,manifest=self.setup_temp(td)
            record=json.loads(manifest.read_text())
            record["duration"]=6.5
            manifest.write_text(json.dumps(record))
            packet={"actualCapture":{"durationSeconds":6.5,"nativeFps":60,
                     "resolution":[2880,1800],
                     "pointerProvenance":{"recordedPointerTrackAvailable":True}}}
            with patch("film_director_capabilities.build_contract",return_value=packet):
                plan=source_event_director.direction(video,manifest)
            self.assertEqual(plan["durationSeconds"],6.5)
            self.assertEqual(plan["audio"]["eventIndices"],[0])
            self.assertEqual(plan["audio"]["clickGain"],0.)
            self.assertEqual(plan["studioStage"]["stagePreset"],"cloud_window_clearface_v1")
            record["events"].append(dict(record["events"][0],start=3.2,t=4.2))
            manifest.write_text(json.dumps(record))
            with patch("film_director_capabilities.build_contract",return_value=packet):
                with self.assertRaises(ValueError):
                    source_event_director.direction(video,manifest)

    def test_longer_film_requires_multiple_verified_outcomes(self):
        import source_event_director
        with tempfile.TemporaryDirectory() as td:
            video,manifest=self.setup_temp(td)
            record=json.loads(manifest.read_text())
            first=record["events"][0]
            record["duration"]=30.
            record["events"]=[dict(first,start=t,end=t+.1,t=t+1.) for t in (2.,8.,15.,22.)]
            packet={"actualCapture":{"durationSeconds":30.,"nativeFps":60,
                     "resolution":[2880,1800],
                     "pointerProvenance":{"recordedPointerTrackAvailable":True}}}
            with patch("film_director_capabilities.build_contract",return_value=packet):
                manifest.write_text(json.dumps(record))
                plan=source_event_director.direction(video,manifest)
                self.assertEqual(plan["durationSeconds"],30.)
                self.assertEqual(plan["audio"]["eventIndices"],[0,1,2,3])
                for n in (1,2):
                    manifest.write_text(json.dumps(dict(record,events=record["events"][:n])))
                    with self.assertRaises(ValueError):
                        source_event_director.direction(video,manifest)

    def test_no_fake_compact_camera_for_whole_viewport_change(self):
        with tempfile.TemporaryDirectory() as td:
            video,manifest=self.setup_temp(td)
            data=json.loads(manifest.read_text())
            data["events"][0]["resultRect"]={"x":0,"y":0,"width":2880,"height":1800}
            manifest.write_text(json.dumps(data))
            base={"durationSeconds":10.,"studioStage":{"camera":[{"at":0,"scale":.88}]}}
            with patch("scripts.plan_stagehand_phase2.direction",return_value=base):
                plan,decision=directed_plan(video,manifest)
            self.assertEqual(decision["strategy"],"source-true-overview")
            self.assertIs(plan,base)
            self.assertNotIn("motion",plan["studioStage"])

    def test_forged_hash_or_unverified_source_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            video,manifest=self.setup_temp(td)
            raw=json.loads(manifest.read_text())
            raw["provenance"]["originalSourceSha256"]="0"*64
            with self.assertRaises(ValueError):actual_source(raw,video)
            raw=json.loads(manifest.read_text())
            raw["events"][0]["evidence"]=""
            with self.assertRaises(ValueError):actual_source(raw,video)
            raw=json.loads(manifest.read_text())
            raw["pointer_samples"]=[]
            with self.assertRaises(ValueError):actual_source(raw,video)
            raw=json.loads(manifest.read_text())
            raw["events"].append(raw["events"][0])
            with self.assertRaises(ValueError):actual_source(raw,video)

    def test_result_must_leave_real_reading_hold(self):
        with tempfile.TemporaryDirectory() as td:
            video,manifest=self.setup_temp(td)
            raw=json.loads(manifest.read_text())
            raw["events"][0]["t"]=7.7
            manifest.write_text(json.dumps(raw))
            with patch("scripts.plan_stagehand_phase2.direction",return_value={
                "durationSeconds":10., "studioStage":{}}):
                with self.assertRaises(ValueError):directed_plan(video,manifest)


class Phase2PipelineSafetyTests(unittest.TestCase):
    def test_default_fails_without_existing_model_credential(self):
        from scripts.stagehand_phase2_pipeline import run
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"job"
            report={"url":"https://example.com/","source_url":"https://example.com/"}
            with patch("scripts.stagehand_phase2_pipeline.validate_public_url"),patch(
                 "scripts.stagehand_phase2_pipeline.inspect",return_value=report),patch.dict(
                 "os.environ",{"GEMINI_API_KEY":"","GOOGLE_GENERATIVE_AI_API_KEY":"",
                               "BROWSERBASE_API_KEY":"","SAUCE_STAGEHAND_BROWSER":"local"}):
                with self.assertRaises(RuntimeError):
                    run("https://example.com/",out)
            receipt=json.loads((out/"experiment-receipt.json").read_text())
            self.assertEqual(receipt["status"],"failed_closed")
            self.assertFalse(receipt["premiumApproved"])
            self.assertFalse((out/"private"/"native").exists())

    def test_existing_dir_never_overwritten(self):
        from scripts.stagehand_phase2_pipeline import run
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"existing"
            out.mkdir()
            (out/"owner-evidence.txt").write_text("preserve")
            with patch("scripts.stagehand_phase2_pipeline.validate_public_url"):
                with self.assertRaises(ValueError):run("https://example.com/",out)
            self.assertEqual((out/"owner-evidence.txt").read_text(),"preserve")


if __name__=="__main__":
    unittest.main()
