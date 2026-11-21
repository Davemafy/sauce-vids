"""Offline guardrails for Sauce's opt-in multimodel experiment runner."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import experiment_model_shootout as shootout


def valid_plan():
    return {"schema":"sauce-film-plan-v1",
            "sourceSha256":"a"*64,"manifestSha256":"b"*64,
            "durationSeconds":4.9,"presentation":"fullscreen",
            "cursor":"recorded","audio":{"mode":"clean"},
            "camera":[{"at":0,"anchor":"wide","zoom":1,"easing":"quintic"},
                      {"at":2.533333,"anchor":"wide","zoom":1,"easing":"quintic"},
                      {"at":4.9,"anchor":"event:0:result","zoom":1.2,
                       "startAt":2.533333,"easing":"quintic"}]}


class MultimodelShootoutTests(unittest.TestCase):
    def test_registry_has_multiple_real_provider_candidates(self):
        self.assertIn(("vultr","deepseek-v4.1-flash-1017"),shootout.MODELS)
        self.assertIn(("vultr","glm-5.3"),shootout.MODELS)
        self.assertIn(("gemini","gemini-3.1-flash-lite"),shootout.MODELS)
        self.assertEqual(len(set(shootout.MODELS)),len(shootout.MODELS))
        self.assertNotIn(("vultr","inkling-2-mini"),shootout.MODELS)

    def test_json_response_accepts_plain_and_fenced_only(self):
        raw=json.dumps(valid_plan())
        self.assertEqual(shootout.json_response(raw),valid_plan())
        self.assertEqual(shootout.json_response(" ```json\n"+raw+"\n``` "),valid_plan())
        with self.assertRaises((ValueError,json.JSONDecodeError)):
            shootout.json_response("{\"camera\": [")

    def test_camera_cannot_modify_verified_source_or_audio(self):
        expected={"expected_source_sha":"a"*64,"expected_manifest_sha":"b"*64}
        self.assertEqual(shootout.check_camera_shape(valid_plan(),**expected),valid_plan())
        for patch_data in ({"sourceSha256":"x"*64},
                           {"manifestSha256":"y"*64},
                           {"audio":{"mode":"file","file":"fake.mp3"}},
                           {"presentation":"window"},
                           {"cursor":"none"},
                           {"schema":"sauce-film-v1"},
                           {"inventedOverlay":True},
                           {"durationSeconds":30}):
            with self.subTest(patch_data=patch_data):
                data={**valid_plan(),**patch_data}
                with self.assertRaises(ValueError):
                    shootout.check_camera_shape(data,**expected)

    def test_opening_is_verified_wide(self):
        plan=valid_plan()
        plan["camera"][0]={"at":0,"anchor":"event:0:result",
                            "zoom":2,"easing":"quintic"}
        with self.assertRaisesRegex(ValueError,"Opening camera"):
            shootout.check_camera_shape(plan,expected_source_sha="a"*64,
                                        expected_manifest_sha="b"*64)

    def test_invalid_unbounded_camera_key_rejected(self):
        plan=valid_plan()
        plan["camera"][1]["imageUrl"]="http://example.test/imaginary.png"
        with self.assertRaisesRegex(ValueError,"invented keys"):
            shootout.check_camera_shape(plan,expected_source_sha="a"*64,
                                        expected_manifest_sha="b"*64)

    def test_bounded_reasoning_routing_does_not_expose_credentials(self):
        off=shootout.build_vultr_payload("glm-5.2","hello",128,
                                      {"SAUCE_VULTR_REASONING_DISABLED":"1"})
        self.assertEqual(off["reasoning"],{"enabled":False})
        self.assertNotIn("api_key",json.dumps(off).lower())
        tuned=shootout.build_vultr_payload("glm-5.3","hello",1600,
                    {"SAUCE_VULTR_REASONING_EFFORT":"minimal",
                     "SAUCE_VULTR_REASONING_BUDGET":"256"})
        self.assertEqual(tuned["reasoning_effort"],"minimal")
        self.assertEqual(tuned["reasoning"]["max_tokens"],256)
        with self.assertRaisesRegex(ValueError,"Unsafe reasoning budget"):
            shootout.build_vultr_payload("glm-5.3","hello",1300,
                                         {"SAUCE_VULTR_REASONING_BUDGET":"999"})
        with self.assertRaisesRegex(ValueError,"4096 cap"):
            shootout.build_vultr_payload("glm-5.3","hello",10000,{})

    def test_unverified_model_never_becomes_published_film(self):
        with tempfile.TemporaryDirectory() as d:
            result=shootout.render_model(("vultr","no-approved-plan"),Path(d))
            self.assertEqual(result["status"],"NO_VALID_MODEL_FILM_PLAN")
            self.assertFalse(result["creativeApproved"])
            self.assertFalse((Path(d)/"films"/"vultr-no-approved-plan"/"master-1080p60.mp4").exists())

    def test_model_names_are_sanitized_for_private_paths(self):
        self.assertEqual(shootout.safe_name("vultr","GLM-5.3"),"vultr-glm-5-3")
        self.assertNotIn("/",shootout.safe_name("vultr","../../../escape"))
        self.assertNotIn("..",shootout.safe_name("vultr","../../../escape"))


if __name__=="__main__":
    unittest.main()
