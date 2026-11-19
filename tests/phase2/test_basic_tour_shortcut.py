"""Sauce Basic Short Cut contract tests; no customer footage in CI."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import subprocess
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from basic_tour_shortcut import (
    SCHEMA,load_scene,hold_beats,choose_shots,compile_cut,digest,
)


def fixture_scene(root:Path,name:str,*,pattern:str)->Path:
    root.mkdir(parents=True,exist_ok=True)
    video=root/"segment-1080p60.mp4"
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error",
      "-nostdin","-y","-f","lavfi","-i",
      f"{pattern}=size=1920x1080:rate=30",
      "-t","6","-c:v","libx264","-preset","ultrafast",
      "-pix_fmt","yuv420p",str(video)],
      check=True,timeout=55)
    manifest={
        "schema":"sauce-basic-capture-v1","source_url":f"https://test.example/{name}",
        "observed_scroll":[{"t":2.8,"type":"wheel","end":700}],
    }
    manifest_file=root/"capture-manifest.json"
    manifest_file.write_text(json.dumps(manifest))
    film={
      "schema":"sauce-film-plan-v1",
      "sourceSha256":digest(video),"manifestSha256":digest(manifest_file),
      "cursor":"none","presentation":"fullscreen"
    }
    (root/"film-plan.json").write_text(json.dumps(film))
    receipt={
      "url":manifest["source_url"],"encoded_sha256":digest(video),
      "encoded_seconds":6,
      "hold_samples":[
         {"scroll_y":0,"duration_ms":1800,"issues":[]},
         {"scroll_y":700,"duration_ms":2400,"issues":[]}],
      "issues":[],
    }
    (root/"receipt.json").write_text(json.dumps(receipt))
    return root


class BasicShortCutTests(unittest.TestCase):
    def test_verified_sources_compile_readable_original_clip_times(self):
        with TemporaryDirectory() as tmp:
            a=fixture_scene(Path(tmp)/"a","a",pattern="testsrc2")
            b=fixture_scene(Path(tmp)/"b","b",pattern="testsrc2")
            scenes=[load_scene(a),load_scene(b)]
            edl=choose_shots(scenes,duration_limit=18)
            self.assertEqual(edl["schema"],SCHEMA)
            self.assertGreaterEqual(edl["durationSeconds"],8)
            self.assertTrue(any(x["kind"]=="feature" for x in edl["shots"]))
            self.assertTrue(all(x["sourceStartSeconds"]>=0 and
                x["sourceStartSeconds"]+x["durationSeconds"]<=6.01
                for x in edl["shots"]))
            out=compile_cut(edl,scenes,Path(tmp)/"output")
            self.assertEqual(out["status"],"technical_pass_creative_review_required")
            self.assertEqual(out["frames"],round(out["durationSeconds"]*30))

    def test_stronger_source_hero_can_open_without_fabrication(self):
        with TemporaryDirectory() as tmp:
            darker=fixture_scene(Path(tmp)/"a","a",pattern="color")
            richer=fixture_scene(Path(tmp)/"b","b",pattern="testsrc2")
            edl=choose_shots([load_scene(darker),load_scene(richer)],
                             duration_limit=18,hook_strategy="strongest_hero")
            self.assertEqual(edl["shots"][0]["kind"],"hero_hook")
            self.assertEqual(edl["shots"][0]["scene"],1)
            self.assertTrue(edl["shots"][0]["sourceDynamicPush"])
            self.assertGreater(edl["heroSalienceScores"][1],
                               edl["heroSalienceScores"][0])

    def test_modified_source_is_rejected_by_existing_hash_binding(self):
        with TemporaryDirectory() as tmp:
            a=fixture_scene(Path(tmp)/"a","a",pattern="testsrc2")
            self.assertEqual(len(load_scene(a)["film"]["sourceSha256"]),64)
            with (a/"segment-1080p60.mp4").open("ab") as f:f.write(b"tamper")
            with self.assertRaisesRegex(ValueError,"unverified source"):
                load_scene(a)

    def test_no_unreadably_short_budget_and_no_fake_sources(self):
        with TemporaryDirectory() as tmp:
            a=fixture_scene(Path(tmp)/"a","a",pattern="testsrc2")
            with self.assertRaises(ValueError):
                choose_shots([load_scene(a)],duration_limit=6)
            with self.assertRaises(ValueError):
                choose_shots([],duration_limit=20)
            with self.assertRaisesRegex(ValueError,"Invalid hook"):
                choose_shots([load_scene(a)],duration_limit=20,hook_strategy="AI")
