"""No-human-per-video verification for Sauce Basic's automatic film gate."""
from __future__ import annotations
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from basic_tour_autodirect import (
    critique,motion_probe,repair_once,run,MAX_ATTEMPTS,
)


def make_video(root:Path,kind:str,duration:float=5)->Path:
    target=root/f"{kind}.mp4"
    input_spec=("color=c=white:s=320x180:r=30"
                if kind=="static" else
                "testsrc2=size=320x180:rate=30")
    subprocess.run(["ffmpeg","-v","error","-y",
        "-f","lavfi","-i",input_spec,"-t",str(duration),"-c:v",
        "libx264","-preset","ultrafast","-pix_fmt","yuv420p",str(target)],
        check=True,timeout=35)
    return target


class AutomaticBasicCriticTests(unittest.TestCase):
    def test_static_yet_decodable_film_is_rejected(self):
        with TemporaryDirectory() as tmp:
            video=make_video(Path(tmp),"static")
            scene={"receipt":{"url":"https://source.example/","issues":[]}}
            result=critique(video,[scene],{"shots":[{"scene":0}]})
            self.assertEqual(result["technicalQuality"],"reject")
            self.assertIn("opening_lacks_visible_motion",result["failures"])
            self.assertIn("excessive_static_frames",result["failures"])
            self.assertEqual(result["creativeQuality"],"unverified")

    def test_genuine_dynamic_video_passes_motion_floor_not_creative(self):
        with TemporaryDirectory() as tmp:
            video=make_video(Path(tmp),"dynamic")
            scene={"receipt":{"url":"https://source.example/","issues":[]}}
            result=critique(video,[scene],{"shots":[{"scene":0}]})
            self.assertEqual(result["technicalQuality"],"bounded_checks_pass")
            self.assertEqual(result["creativeQuality"],"unverified")
            self.assertGreater(result["filmChecks"]["openingMotionRatio"],.8)

    def test_source_warning_survives_dynamic_video(self):
        with TemporaryDirectory() as tmp:
            video=make_video(Path(tmp),"dynamic")
            scene={"receipt":{"url":"https://source.example/",
                              "issues":["visible_skeleton"]}}
            result=critique(video,[scene],{"shots":[{"scene":0}]})
            self.assertIn("source_low_confidence_scene_0",result["failures"])

    def test_bounded_repair_moves_real_motion_shot_first(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            dynamic=make_video(root,"dynamic")
            scenes=[
              {"receipt":{"url":"https://site.example/a","issues":[]},
               "video_path":dynamic},
              {"receipt":{"url":"https://site.example/b",
                          "issues":["visible_skeleton"]},
               "video_path":dynamic},
            ]
            edl={"budgetSeconds":18,
                 "shots":[
                  {"scene":0,"kind":"establish","sourceStartSeconds":.2,
                   "durationSeconds":2.6,"sourceCropZoom":1.18,
                   "sourceDynamicPush":False},
                  {"scene":0,"kind":"feature","sourceStartSeconds":1.,
                   "durationSeconds":3.5,"sourceCropZoom":1.13,
                   "sourceDynamicPush":False},
                  {"scene":1,"kind":"feature","sourceStartSeconds":1.,
                   "durationSeconds":3.5,"sourceCropZoom":1.13,
                   "sourceDynamicPush":False}
                 ]}
            repaired=repair_once(edl,scenes,{"failures":["opening_lacks_visible_motion"]})
            self.assertEqual(repaired["shots"][0]["kind"],"hook_motion")
            self.assertEqual(repaired["shots"][0]["scene"],0)
            self.assertFalse(repaired["shots"][0]["sourceDynamicPush"])
            self.assertEqual(repaired["excludedLowConfidenceSceneIds"],[1])
            self.assertLessEqual(repaired["durationSeconds"],edl["budgetSeconds"])
            self.assertEqual(MAX_ATTEMPTS,2)
            self.assertEqual(edl["shots"][0]["kind"],"establish")

    def test_all_low_confidence_sources_return_rejection_json_not_crash(self):
        # Existing 1080p fixture creates correctly hashed original receipts.
        sys.path.insert(0,str(Path(__file__).resolve().parent))
        from test_basic_tour_shortcut import fixture_scene
        with TemporaryDirectory() as tmp:
            folder=fixture_scene(Path(tmp)/"source","src",pattern="testsrc2")
            import json
            receipt_file=folder/"receipt.json"
            receipt=json.loads(receipt_file.read_text())
            receipt["issues"]=["incomplete_visible_images"]
            receipt_file.write_text(json.dumps(receipt))
            out=Path(tmp)/"automatic"
            result=run([folder],out,max_seconds=15)
            self.assertEqual(result["status"],"rejected_no_saleable_preview")
            self.assertFalse(result["acceptedByAutomaticChecks"])
            self.assertEqual(result["attempts"],[])
            self.assertEqual(result["rejectionReasons"],
                             ["all_recorded_pages_low_confidence"])
            self.assertTrue((out/"autodirect-result.json").exists())
            self.assertIsNone(result["selectedCandidate"])

    def test_too_little_source_footage_returns_readable_rejection(self):
        sys.path.insert(0,str(Path(__file__).resolve().parent))
        from test_basic_tour_shortcut import fixture_scene
        with TemporaryDirectory() as tmp:
            folder=fixture_scene(Path(tmp)/"source","src",pattern="testsrc2")
            import json
            receipt_file=folder/"receipt.json"
            receipt=json.loads(receipt_file.read_text())
            receipt["hold_samples"]=[{
                "scroll_y":0,"duration_ms":1300,"issues":[]
            }]
            receipt_file.write_text(json.dumps(receipt))
            out=Path(tmp)/"automatic"
            result=run([folder],out,max_seconds=15)
            self.assertEqual(result["status"],"rejected_no_saleable_preview")
            self.assertIn("cannot_plan_source_true_preview",
                          result["rejectionReasons"][0])
            self.assertTrue((out/"autodirect-result.json").exists())
            self.assertEqual(list(out.glob("**/*.mp4")),[])

    def test_repair_refuses_to_invent_motion_when_source_is_static(self):
        with TemporaryDirectory() as tmp:
            source=make_video(Path(tmp),"static")
            edl={"budgetSeconds":20,
                 "shots":[{"scene":0,"kind":"establish",
                           "sourceStartSeconds":0.2,"durationSeconds":2.6},
                          {"scene":0,"kind":"feature",
                           "sourceStartSeconds":1.,"durationSeconds":3.2}]}
            with self.assertRaisesRegex(ValueError,"No authentic browser-motion"):
                repair_once(edl,[{"video_path":source,"receipt":{"issues":[]}}],
                            {"failures":["opening_lacks_visible_motion"]})


if __name__=="__main__":
    unittest.main()
