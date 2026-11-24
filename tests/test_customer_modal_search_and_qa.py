"""Customer URL -> public interaction research -> encoded-quality contract.

No fixed site selectors, no fake UI, and no premium auto-approval.
"""
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

from backend.public_modal_search import investigate_modal_candidates
from backend.product_explorer import safe_public_modal_opener,allowed
from backend.source_action_preflight import authentication_barrier
from backend.live_render import evaluate_encoded_customer_film


def report():
    return {
        "url":"https://example.com/components/modal",
        "title":"Modal examples",
        "headings":[{"id":"h0","selector":"h1","text":"Modal"}],
        "controls":[
            {"id":f"a{i}","text":"Open modal","tag":"button","kind":"button",
             "button_type":"button","in_form":False,"selector":f"#example-{i}",
             "controlled_panel":False} for i in range(5)]
    }


class PublicModalSearchTests(unittest.TestCase):
    def test_three_distinct_fresh_probes_and_first_substantial_result(self):
        r=report()
        attempted=[]
        def fake_probe(url,source,cid,path):
            attempted.append((url,cid,str(path)))
            d={"schema":"sauce-source-action-preflight-v1",
               "decision":"authentication_required" if cid=="a0" else "visible_outcome_candidate",
               "result_area_fraction":.04 if cid=="a1" else .11,
               "changed_result_fraction":.3,
               "human_film_approval":False}
            return d
        def admit(plan,source,proof):
            if proof["decision"]!="visible_outcome_candidate" or proof["result_area_fraction"]<.055:
                raise RuntimeError("Not a substantial verified public result")
            return plan
        with tempfile.TemporaryDirectory() as tmp:
            with patch("backend.public_modal_search.probe_public_action",
                       side_effect=fake_probe):
                result=investigate_modal_candidates(
                    "https://example.com/components/modal",r,Path(tmp),
                    {"title":"Demo","heading_ids":["h0"]},admit,limit=3)
            self.assertEqual(result[0]["action_ids"],["a2"])
            self.assertEqual([x[1] for x in attempted],["a0","a1","a2"])
            evidence=json.loads((Path(tmp)/"receipt.json").read_text())
            self.assertEqual([x["status"] for x in evidence["attempts"]],
                             ["rejected","rejected","source_proven_candidate"])
            self.assertFalse(evidence["creative_approved"])
            self.assertEqual(evidence["max_candidates"],3)

    def test_all_failed_never_admit_and_no_fourth_probe(self):
        r=report()
        attempts=[]
        with tempfile.TemporaryDirectory() as tmp:
            with patch("backend.public_modal_search.probe_public_action",
                       side_effect=lambda url,source,cid,path:attempts.append(cid) or
                           {"decision":"authentication_required"}):
                outcome=investigate_modal_candidates(
                    "https://example.com/components/modal",r,tmp,
                    {"title":"Test"},lambda *args: (_ for _ in ()).throw(ValueError("Denied")))
            self.assertIsNone(outcome)
            self.assertEqual(attempts,["a0","a1","a2"])

    def test_login_button_forms_and_submitting_modals_are_never_proposed(self):
        base=report()["controls"][0]
        self.assertTrue(safe_public_modal_opener(base))
        self.assertTrue(allowed(base,"https://example.com"))
        for mutation in ({"text":"Open account"},{"in_form":True},
                         {"button_type":"submit"},{"text":"Open modal and pay"},
                         {"kind":"link"},{"tag":"a"}):
            self.assertFalse(safe_public_modal_opener({**base,**mutation}))
        self.assertTrue(authentication_barrier([
            {"text":"Example authentication","password":True}]))
        self.assertFalse(authentication_barrier([
            {"text":"Public example modal content","password":False}]))


class CustomerEncodedQualityContractTests(unittest.TestCase):
    def test_all_interactive_film_receipts_must_be_scored(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)
            source=path/"continuous-source.webm"
            source.write_bytes(b"original genuine source test bytes")
            manifest=path/"continuous-capture.json"
            manifest.write_text(json.dumps({"continuous_recording":True,
               "actions":[{"kind":"button"}],"source_url":"https://example.com/"}))
            film=path/"master.mp4"
            film.write_bytes(b"test output")
            from backend.live_render import file_digest
            captured={"continuous_recording":True,"sha256":file_digest(source)}
            assessment={"verdict":"REJECT","findings":[
                {"code":"REPEATED_OR_STATIC_FRAMES"},{"code":"NO_AUDIO_STREAM"}]}
            with patch("scripts.quality_preview_supervisor.analyze",
                       return_value=assessment) as evaluate:
                fields=evaluate_encoded_customer_film(film,path,captured,5.84,path)
            self.assertEqual(fields["encoded_quality_verdict"],"REJECT")
            self.assertEqual(fields["encoded_quality_findings"],
                             ["REPEATED_OR_STATIC_FRAMES","NO_AUDIO_STREAM"])
            self.assertFalse(fields["creative_approved"])
            params=evaluate.call_args
            self.assertEqual(params.args[0],film)
            self.assertEqual(params.kwargs["seconds"],5.84)
            self.assertEqual(params.kwargs["evidence"]["source_sha256"],
                             captured["sha256"])
            self.assertEqual(json.loads((path/"encoded-quality.json").read_text()),
                             assessment)

    def test_forged_or_missing_original_is_denied_before_scoring(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)
            (path/"continuous-source.webm").write_bytes(b"real original")
            (path/"continuous-capture.json").write_text("{}")
            with patch("scripts.quality_preview_supervisor.analyze") as evaluate:
                with self.assertRaises(ValueError):
                    evaluate_encoded_customer_film(path/"film.mp4",path,
                        {"continuous_recording":True,"sha256":"0"*64},5.8,path)
                evaluate.assert_not_called()
            self.assertFalse((path/"encoded-quality.json").exists())


if __name__=="__main__":
    unittest.main()
