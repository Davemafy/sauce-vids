"""One remote director call can return multiple source-verified candidates."""
import hashlib
import json
import sys
from pathlib import Path
from urllib.error import HTTPError

import cv2
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from one_call_edl_ablation import check_variants,run,SCHEMA


def _packet():
    return {"actualCapture":{"sourceSha256":"a"*64,"manifestSha256":"b"*64}}


def _variant(name):
    return {"id":name,"filmPlan":{"schema":"sauce-film-plan-v1",
       "sourceSha256":"a"*64,"manifestSha256":"b"*64}}


def test_exactly_two_or_three_variants_with_verified_hashes():
    valid={"schema":SCHEMA,"selected":"tight",
           "variants":[_variant("tight"),_variant("readable")]}
    assert len(check_variants(valid,_packet()))==2
    fake=json.loads(json.dumps(valid))
    fake["variants"][1]["filmPlan"]["sourceSha256"]="0"*64
    with pytest.raises(ValueError,match="forged"):
        check_variants(fake,_packet())
    fake=json.loads(json.dumps(valid))
    fake["variants"][1]["id"]="tight"
    with pytest.raises(ValueError,match="duplicate"):
        check_variants(fake,_packet())
    fake=json.loads(json.dumps(valid))
    fake["selected"]="missing"
    with pytest.raises(ValueError,match="Selected"):
        check_variants(fake,_packet())


@pytest.fixture
def sample(tmp_path):
    source=tmp_path/"source.mp4"
    writer=cv2.VideoWriter(str(source),cv2.VideoWriter_fourcc(*"mp4v"),
                           25,(320,180))
    assert writer.isOpened()
    for i in range(50):
        frame=np.full((180,320,3),185,np.uint8)
        if i>=25:frame[25:145,110:285]=(40,55,165)
        writer.write(frame)
    writer.release()
    manifest=tmp_path/"events.json"
    manifest.write_text(json.dumps({"source":"https://example.com",
        "duration":2.0,"cursorless":True,
        "capture_rect":{"width":320,"height":180},
        "events":[{"kind":"theme_change","start":.5,"t":1.1,"end":1.1,
          "evidence":"True original capture changed",
          "targetRect":{"x":10,"y":12,"width":80,"height":25},
          "resultRect":{"x":110,"y":25,"width":175,"height":120}}]}))
    return source,manifest


def _plan(source,manifest):
    dig=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    return {"schema":"sauce-film-plan-v1",
      "sourceSha256":dig(source),"manifestSha256":dig(manifest),
      "durationSeconds":2.0,"presentation":"fullscreen","cursor":"none",
      "audio":{"mode":"eventFoley","eventIndex":0},
      "camera":[{"at":0,"anchor":"wide","zoom":1},
                {"at":2.0,"anchor":"wide","zoom":1}]}


def test_one_api_response_two_locally_validated_candidates(sample,tmp_path):
    src,manifest=sample
    plan=_plan(src,manifest)
    invocations=[]
    def fake_model(*args):
        invocations.append(1)
        assert len(args)==4
        result={"schema":SCHEMA,"selected":"readable",
                "variants":[{"id":"tight","filmPlan":plan},
                            {"id":"readable","filmPlan":plan}]}
        return json.dumps(result),{"usageMetadata":{"totalTokenCount":149}}
    def fake_validator(*args):
        return True,"source locked"
    result=run(src,manifest,"Demonstrate real outcome",tmp_path/"run",
        model="gemini-3.7-flash",key="in-memory-test-key",
        model_call=fake_model,validator=fake_validator,render=False)
    assert len(invocations)==1
    assert result["apiCalls"]==1
    assert result["modelSelected"]=="readable"
    assert result["selected"]=="readable"
    assert result["status"]=="validated_not_rendered"
    assert result["creativeApproved"] is False
    assert all(row["status"]=="validated" for row in result["variants"])
    assert "in-memory-test-key" not in (
        tmp_path/"run"/"one-call-receipt.json").read_text()


def test_one_call_fails_closed_on_provider_503(sample,tmp_path):
    src,manifest=sample
    attempts=[]
    def unavailable(*args):
        attempts.append(1)
        raise HTTPError("https://example.invalid",503,"unavailable",{},None)
    result=run(src,manifest,"Actual source only",tmp_path/"503",
        model="gemini-3.7-flash",key="test-only",
        model_call=unavailable,render=False)
    assert attempts==[1]
    assert result["apiCalls"]==1
    assert result["providerHttpStatus"]==503
    assert result["status"]=="provider_unavailable"
    assert result["selected"] is None
    assert result["rendered"]==[]
