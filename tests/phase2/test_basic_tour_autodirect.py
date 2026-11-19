"""No-human-per-video verification for Sauce Basic's automatic film gate."""
from __future__ import annotations
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from basic_tour_autodirect import (
    critique,motion_probe,repair_once,MAX_ATTEMPTS,
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
