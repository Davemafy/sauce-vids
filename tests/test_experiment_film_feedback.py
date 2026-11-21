"""Offline regression checks: model creativity cannot mutate source evidence."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from experiment_film_feedback import (
    constrained_plan, film_bytes, validate_pre_action_camera,
)

BASE = {
    "schema":"sauce-film-plan-v1",
    "sourceSha256":"a"*64,
    "manifestSha256":"b"*64,
    "durationSeconds":8.5,
    "presentation":"fullscreen",
    "cursor":"recorded",
    "audio":{"mode":"file","file":"licensed-voice.wav"},
    "camera":[{"at":0,"anchor":"wide","zoom":1,"easing":"quintic"},
              {"at":1.5,"anchor":"wide","zoom":1,"easing":"quintic"},
              {"at":3.2,"anchor":"event:0:result","zoom":1.5,"easing":"quintic"}]
}
EVENTS = {"events":[{"t":1.5,"start":1.333,
                     "evidence":"Actual recorded result appeared"}]}


class FilmFeedbackTests(unittest.TestCase):
    def test_identical_base_plan_survives(self):
        self.assertEqual(constrained_plan(BASE,BASE),BASE)
        validate_pre_action_camera(BASE,EVENTS)

    def test_model_can_supply_camera_only(self):
        proposed={"camera":[{"at":0,"anchor":"wide","zoom":1},
                            {"at":1.5,"anchor":"wide","zoom":1},
                            {"at":3.5,"anchor":"event:0:component","zoom":1.6}]}
        actual=constrained_plan(BASE,proposed)
        self.assertEqual(actual["sourceSha256"],BASE["sourceSha256"])
        self.assertEqual(actual["manifestSha256"],BASE["manifestSha256"])
        self.assertEqual(actual["audio"],BASE["audio"])
        validate_pre_action_camera(actual,EVENTS)

    def test_harmless_camera_array_envelope_is_recovered(self):
        data=[{"at":0,"anchor":"wide","zoom":1},
              {"at":1.5,"anchor":"wide","zoom":1},
              {"at":3.2,"anchor":"event:0:result","zoom":1.5}]
        self.assertEqual(constrained_plan(BASE,data)["camera"],data)
        self.assertEqual(constrained_plan(BASE,[{"camera":data}])["camera"],data)

    def test_changed_hash_and_audio_must_fail(self):
        for change in ({"sourceSha256":"c"*64}, {"manifestSha256":"d"*64},
                       {"audio":{"mode":"clean"}},{"durationSeconds":24},
                       {"presentation":"window"},{"cursor":"none"}):
            with self.subTest(change=change), self.assertRaisesRegex(ValueError,"immutable"):
                constrained_plan(BASE,{**BASE,**change})

    def test_unsupported_ui_control_rejected(self):
        for change in ({"inventNewUI":True},
                       {"camera":[{"at":0,"anchor":"wide","zoom":1},
                                  {"at":2.5,"anchor":"event:99:result","zoom":1.4}]},
                       {"camera":[{"at":0,"anchor":"wide","zoom":1},
                                  {"at":1.5,"anchor":"wide","zoom":1,"cssSelector":"#fake"}]}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                constrained_plan(BASE,{**BASE,**change})

    def test_no_pre_result_zoom_or_focus(self):
        for bad in ({"at":1.5,"anchor":"wide","zoom":1.1},
                    {"at":1.5,"anchor":"event:0:result","zoom":1.3},
                    {"at":1.0,"anchor":"event:0:component","zoom":1.3}):
            plan={**BASE,"camera":[BASE["camera"][0],bad,BASE["camera"][2]]}
            with self.subTest(bad=bad), self.assertRaisesRegex(ValueError,"Pre-action zoom"):
                validate_pre_action_camera(plan,EVENTS)

    def test_rejects_unsupported_video_input(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"not-video.txt";p.write_bytes(b"x"*35000)
            with self.assertRaisesRegex(ValueError,"MP4"):
                film_bytes(p)
            p=Path(t)/"empty.mp4";p.write_bytes(b"bad")
            with self.assertRaisesRegex(ValueError,"size or is empty"):
                film_bytes(p)
            p=Path(t)/"too-large.mp4"
            with p.open("wb") as fp:
                fp.truncate(12*1024*1024+1)
            with self.assertRaisesRegex(ValueError,"size or is empty"):
                film_bytes(p)


if __name__=="__main__":
    unittest.main()
