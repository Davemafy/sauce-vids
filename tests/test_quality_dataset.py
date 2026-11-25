"""Ensure Sauce quality corpus is negative-only, source-pinned and private-safe."""
import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from build_quality_dataset import build,curated_workflow,qa_findings


def sample(tmp_path,*,verdict="REJECT",qa_binding=True):
    root=tmp_path/"private";job=root/"research"/"job"
    export=job/"export";export.mkdir(parents=True)
    binary=export/"master-1080p60.mp4"
    binary.write_bytes(b"fake bytes; do not create a valid film"+b"x"*2500)
    sha=hashlib.sha256(binary.read_bytes()).hexdigest()
    report={"verdict":verdict,"film_sha256":sha if qa_binding else "0"*64,
            "duration":15.0,"findings":[
                {"code":"STATIC_OPENING_2S","detail":{"p80_frame_delta":0.04,
                  "private_token":"SHOULD_NOT_EXPORT","source":"/private/secret"}},
                {"code":"NO_AUDIO_STREAM","detail":{"info":"SECRET"}}],
            "raw_prompt":"PRIVATE_AND_UNTRUSTED"}
    (export/"encoded-quality.json").write_text(json.dumps(report))
    (export/"release.json").write_text(json.dumps({
        "source_sha256":"1"*64,"film_sha256":sha,
        "plan_sha256":"2"*64,"observed_actions":3,
        "private_har": "RAW_HAR_SECRET","customer_email":"a@example.com"}))
    return root,sha,binary


def test_machine_and_human_labels_are_disjoint(tmp_path):
    root,sha,_=sample(tmp_path)
    manual=[{"film_sha256":sha,"label":"creative_reject",
             "evidence_document":"docs/SAUCE_HANDOFF.md",
             "defects":["STATIC_OPENING_2S"],
             "workflow":{"submitted_url":"https://tweakcn.com/",
                         "actions":["Cyberpunk"],"verified_result_seconds":[5.3],
                         "gemini_successful_calls":3}}]
    corpus,index=build({"research":root},manual)
    assert corpus["summary"]["machine_rejected"]==1
    assert corpus["summary"]["curated_creative_rejections"]==1
    assert corpus["summary"]["premium_approved"]==0
    c=corpus["cases"][0]
    assert c["quality"]["human_premium_label"]=="creative_reject"
    assert c["quality"]["premium_reference_eligible"] is False
    assert c["evidence"]["qa_binding"]=="sha_match"
    assert c["curated_public_workflow"]["actions"]==["Cyberpunk"]
    assert index[c["id"]][0]["root"]=="research"
    exported=json.dumps(corpus)
    for sensitive in ("RAW_HAR_SECRET","PRIVATE_AND_UNTRUSTED","SHOULD_NOT_EXPORT",
                      "a@example.com","/private/secret","research/job"):
        assert sensitive not in exported


def test_missing_or_stale_qa_never_claims_pass(tmp_path):
    root,sha,film=sample(tmp_path,qa_binding=False)
    d,_=build({"research":root},[])
    assert d["cases"][0]["quality"]["machine_verdict"] is None
    assert d["cases"][0]["evidence"]["qa_binding"]=="sha_mismatch"
    assert d["summary"]["machine_qa_missing_or_untrusted"]==1
    (film.parent/"encoded-quality.json").unlink()
    d,_=build({"research":root},[])
    assert d["cases"][0]["evidence"]["qa_binding"]=="missing"
    assert d["cases"][0]["quality"]["machine_verdict"] is None


def test_identical_binaries_deduplicate_but_locator_stays_private(tmp_path):
    root,sha,b=sample(tmp_path)
    other=root/"another"/"job"/"export";other.mkdir(parents=True)
    (other/"master-1080p60.mp4").write_bytes(b.read_bytes())
    corpus,index=build({"research":root},[])
    assert corpus["summary"]["inventoried_binary_files"]==2
    assert corpus["summary"]["unique_film_binaries"]==1
    assert corpus["summary"]["duplicate_files"]==1
    assert len(index[corpus["cases"][0]["id"]])==2
    assert not any("another/job" in json.dumps(c) for c in corpus["cases"])


def test_public_workflow_guard_and_no_fabricated_premium():
    assert curated_workflow({"submitted_url":"https://tweakcn.com/",
        "actions":["Modern Minimal"],"verified_result_seconds":[5.4]})["actions"]==["Modern Minimal"]
    for private in ("http://127.0.0.1/","https://tweakcn.com/?token=secret",
                    "https://example.com/me"):
        with pytest.raises(ValueError):
            curated_workflow({"submitted_url":private,"actions":[]})
    with pytest.raises(ValueError):
        curated_workflow({"actions":["user@example.com"]})
    with pytest.raises(ValueError):
        curated_workflow({"actions":["Demo"],"verified_result_seconds":[1.0,2.0]})
    assert qa_findings([{"code":"REPEATED_OR_STATIC_FRAMES",
      "detail":{"fraction":.75,"prompt":"credential"}}])[0]["numeric_evidence"]=={"fraction":.75}


def test_pre_film_failures_are_structured_and_never_export_raw_reasons(tmp_path):
    from build_quality_dataset import build_failed_attempts
    root=tmp_path/"research";folder=root/"job"/"private"/"customer-story"
    folder.mkdir(parents=True)
    first={"reason":"Insufficient final source hold","index":2,
           "observedDelta":0.071,"email":"private@client.example"}
    (folder/"rejection.json").write_text(json.dumps(first))
    second=folder/"attempt-1";second.mkdir()
    (second/"rejection.json").write_text(json.dumps({
        "reason":"private user response containing a secret bearer token",
        "index":"not-int","observedDelta":50,
        "debug_prompt":"PRIVATE_UNTRUSTED_PROMPT"}))
    result=build_failed_attempts({"research":root})
    assert result["summary"]=={"receipts":2,"unclassified_reasons":1}
    codes={x["reason_code"] for x in result["cases"]}
    assert codes=={"INSUFFICIENT_FINAL_HOLD","UNCLASSIFIED_REJECTION"}
    safe=json.dumps(result)
    assert "private@client.example" not in safe
    assert "secret bearer token" not in safe
    assert "PRIVATE_UNTRUSTED_PROMPT" not in safe
    assert all(c["premium_reference_eligible"] is False for c in result["cases"])
