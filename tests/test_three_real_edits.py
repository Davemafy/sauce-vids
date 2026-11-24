"""Three original-source film-edit research contract; no fictional outcomes."""
from __future__ import annotations
import hashlib
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from scripts.compare_three_verified_edits import derive, validate_capture, PROFILES


class ThreeRealEditsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        self.source=root/"test-original-browser.mp4"
        self.source.write_bytes(b"unit fixture only; not an authorized film")
        self.manifest=root/"source-events.json"
        self.base=root/"original-film-plan.json"
        self.events=[]
        for ix, (start, t) in enumerate(((.7557,1.989),(3.6385,4.815),(6.639,7.808))):
            self.events.append({
                "kind":"slider_change", "start":start, "t":t, "end":t,
                "targetRect":{"x":758,"y":731,"width":1344,"height":40},
                "resultRect":{"x":870+ix*100,"y":1157,"width":498,"height":123},
                "evidence":"Original Chromium recorded a visible price change",
            })
        self.data={"source":"https://example.com/pricing",
                   "duration":10.216666666666667, "cursorless":True,
                   "events":self.events,
                   "pointer_samples":[{"t":i*.05,"x":900,"y":900}
                                      for i in range(160)]}
        self.manifest.write_text(json.dumps(self.data))
        self.original={"schema":"sauce-film-plan-v1",
                       "sourceSha256":hashlib.sha256(self.source.read_bytes()).hexdigest(),
                       "manifestSha256":hashlib.sha256(self.manifest.read_bytes()).hexdigest(),
                       "durationSeconds":self.data["duration"],"cursor":"recorded",
                       "audio":{"mode":"eventFoley","eventIndices":[0,1,2],
                                "clickGain":.34,"motionGain":.17,"masterGain":.45},
                       "studioStage":{"stagePreset":"cloud_window_fullglass_v1",
                                      "camera":[{"at":0,"scale":.88},
                                                {"at":self.data["duration"],"scale":.88}],
                                      "lighting":{"eventIndex":2,"trigger":"verified"}}}
        self.base.write_text(json.dumps(self.original))

    def test_all_edits_retain_exact_source_provenance_audio_and_timeline(self):
        output=[derive(name,self.source,self.manifest,self.base) for name in PROFILES]
        self.assertEqual(len(output),3)
        for plan in output:
            self.assertEqual(plan["sourceSha256"],self.original["sourceSha256"])
            self.assertEqual(plan["manifestSha256"],self.original["manifestSha256"])
            self.assertEqual(plan["durationSeconds"],self.data["duration"])
            self.assertEqual(plan["cursor"],"recorded")
            self.assertEqual(plan["audio"],self.original["audio"])
            self.assertEqual(plan["studioStage"]["stagePreset"],
                             "cloud_window_fullglass_v1")
            camera=plan["studioStage"]["camera"]
            self.assertEqual(camera[0]["at"],0)
            self.assertEqual(camera[-1]["at"],self.data["duration"])
            self.assertTrue(all(camera[i]["at"]<camera[i+1]["at"]
                                for i in range(len(camera)-1)))
            self.assertEqual(plan["studioStage"]["payoff"]["region"],
                             "event:2:result")

    def test_result_zooms_and_cuts_not_before_observed_source(self):
        for profile in PROFILES:
            keys=derive(profile,self.source,self.manifest,self.base)["studioStage"]["camera"]
            for key in keys:
                if key.get("focus","wide").endswith(":result"):
                    ix=int(key["focus"].split(":")[1])
                    self.assertGreaterEqual(key.get("startAt",0),
                                            self.events[ix]["t"])
            if profile=="editorial":
                cuts=[k for k in keys if k.get("cut")]
                self.assertEqual(len(cuts),3)
                for i,cut in enumerate(cuts):
                    self.assertGreater(cut["at"],self.events[i]["t"])
                    self.assertLess(cut["at"]-self.events[i]["t"],.1)
                    self.assertAlmostEqual(cut["at"]*60,round(cut["at"]*60))
            else:
                self.assertFalse(any(k.get("cut") for k in keys))

    def test_forged_or_incomplete_evidence_is_denied(self):
        altered=deepcopy(self.data)
        altered["events"][1]["evidence"]=""
        self.manifest.write_text(json.dumps(altered))
        with self.assertRaises(ValueError):
            derive("living",self.source,self.manifest,self.base)
        self.manifest.write_text(json.dumps(self.data))
        self.source.write_bytes(b"forged replacement")
        with self.assertRaises(ValueError):
            derive("editorial",self.source,self.manifest,self.base)

    def test_denies_timestamps_that_cannot_support_real_result_holds(self):
        altered=deepcopy(self.data)
        altered["events"][1]["start"]=2.05
        self.manifest.write_text(json.dumps(altered))
        self.original["manifestSha256"]=hashlib.sha256(self.manifest.read_bytes()).hexdigest()
        self.base.write_text(json.dumps(self.original))
        with self.assertRaises(ValueError):
            validate_capture(self.source,self.manifest,self.base)


if __name__=="__main__":
    unittest.main()
