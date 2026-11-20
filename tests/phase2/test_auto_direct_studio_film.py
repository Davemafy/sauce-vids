"""Unattended Gemini film-direction orchestration: fail-closed, no paid API in tests."""
import hashlib
import json
import sys
from pathlib import Path
import cv2
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from auto_direct_studio_film import run_unattended,safe_model_name


@pytest.fixture()
def source_pair(tmp_path):
    src=tmp_path/"real.mp4"
    writer=cv2.VideoWriter(str(src),cv2.VideoWriter_fourcc(*"mp4v"),25,(320,180))
    assert writer.isOpened()
    for i in range(50):
        frame=np.full((180,320,3),205,np.uint8)
        if i>25:frame[20:160,120:300]=(30,40,240)
        writer.write(frame)
    writer.release()
    assert src.stat().st_size>100
    manifest=tmp_path/"capture.json"
    manifest.write_text(json.dumps({
        "cursorless":True,"duration":2.,
        "capture_rect":{"width":320,"height":180},
        "events":[{"kind":"theme_change","start":.6,"end":.8,"t":1.30,
        "evidence":"verified changed theme with source pixels",
        "targetRect":{"x":10,"y":12,"width":90,"height":24},
        "resultRect":{"x":120,"y":20,"width":180,"height":140}}]}))
    return src,manifest


def valid_plan(src,manifest):
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    return {"schema":"sauce-film-plan-v1",
      "sourceSha256":digest(src),"manifestSha256":digest(manifest),
      "durationSeconds":2.0,"presentation":"fullscreen","cursor":"none",
      "audio":{"mode":"clean"},
      "camera":[{"at":0,"anchor":"wide","zoom":1},
                {"at":2,"anchor":"wide","zoom":1}]}


def run(src,manifest,out,call,validator,*,max_attempts=2,key="secret-used-only-in-memory"):
    return run_unattended(src,manifest,"A fantastic genuine source-true film",out,
        model="gemini-3-flash-preview",key=key,max_attempts=max_attempts,
        model_call=call,validator=validator,render=False)


def test_success_produces_source_locked_plan_without_human_edit(source_pair,tmp_path):
    src,manifest=source_pair;original=valid_plan(src,manifest)
    calls=[]
    def fake_call(s,packet,model,key,feedback):
        assert feedback is None
        assert packet["actualCapture"]["sourceSha256"]==original["sourceSha256"]
        assert key=="secret-used-only-in-memory"
        calls.append(1)
        return json.dumps(original),{"usageMetadata":{"totalTokenCount":201}}
    def check(s,m,p,out):
        assert json.loads(p.read_text())==original
        return True,"source-verified renderer accepted"
    out=tmp_path/"job"
    receipt=run(src,manifest,out,fake_call,check,max_attempts=1)
    assert receipt["outcome"]=="validated_not_rendered"
    assert receipt["winningAttempt"]==1
    assert len(calls)==1
    assert receipt["creativeApproved"] is False
    assert len(receipt["attempts"])==1
    assert "secret-used-only-in-memory" not in (out/"unattended-receipt.json").read_text()


def test_model_writes_incompatible_window_and_sauce_mechanically_corrects(source_pair,tmp_path):
    src,manifest=source_pair;plan=valid_plan(src,manifest)
    plan["presentation"]="window"
    plan["studioStage"]={"camera":[{"at":0,"scale":.8},{"at":2.,"scale":.8}],
       "lighting":{"eventIndex":0}}
    plan.pop("camera")
    def call(*args):
        return json.dumps(plan),{"usageMetadata":{"totalTokenCount":100}}
    def valid(_,__,p,___):
        data=json.loads(p.read_text())
        assert data["presentation"]=="fullscreen"
        assert data["studioStage"]==plan["studioStage"]
        return True,"source/manifest verified"
    receipt=run(src,manifest,tmp_path/"job",call,valid,max_attempts=1)
    assert receipt["outcome"]=="validated_not_rendered"
    assert receipt["attempts"][0]["mechanicalChanges"]==[
      {"field":"presentation","from":"window","to":"fullscreen",
       "reason":"studioStage already owns the projected physical screen"}]


def test_source_hash_mismatch_never_reaches_render(source_pair,tmp_path):
    src,manifest=source_pair;plan=valid_plan(src,manifest)
    plan["sourceSha256"]="0"*64
    seen=[]
    def call(*args):return json.dumps(plan),{}
    def validator(*args):seen.append(1);return True,"should not happen"
    receipt=run(src,manifest,tmp_path/"job",call,validator,max_attempts=1)
    assert receipt["outcome"]=="failed"
    assert receipt["rendered"] is False
    assert not seen
    assert receipt["attempts"][0]["status"]=="error"


def test_first_plan_is_preserved_when_second_repairs(source_pair,tmp_path):
    src,manifest=source_pair;plan=valid_plan(src,manifest)
    seen=[]
    def call(_,packet,model,key,feedback):
        seen.append(feedback)
        return json.dumps(plan),{"usageMetadata":{}}
    def validate(_,__,___,____):
        return (len(seen)>1,"verified failure: camera hides true interaction" if len(seen)==1
              else "corrected")
    out=tmp_path/"job";receipt=run(src,manifest,out,call,validate)
    assert receipt["outcome"]=="validated_not_rendered"
    assert receipt["winningAttempt"]==2
    assert len(seen)==2
    assert seen[0] is None
    assert "camera hides" in seen[1]
    assert (out/"model-1-original.json").is_file()
    assert (out/"model-2-original.json").is_file()


def test_two_failed_attempts_do_not_create_film(source_pair,tmp_path):
    src,manifest=source_pair
    def call(*args):return json.dumps(valid_plan(src,manifest)),{}
    def reject(*args):return False,"genuine source click hidden"
    result=run(src,manifest,tmp_path/"job",call,reject)
    assert result["outcome"]=="failed"
    assert len(result["attempts"])==2
    assert result["rendered"] is False
    assert not (tmp_path/"job"/"film.mp4").exists()


def test_no_key_means_no_calls_or_fake_fallback(source_pair,tmp_path):
    src,manifest=source_pair
    def call(*args):raise AssertionError("model should not be invoked")
    def validate(*args):raise AssertionError("validator should not be invoked")
    with pytest.raises(RuntimeError,match="credential unavailable"):
        run(src,manifest,tmp_path/"job",call,validate,key=None)
    assert not (tmp_path/"job").exists()


@pytest.mark.parametrize("value",["","../evil","gemini/model","some model","a"*80])
def test_model_id_cannot_inject_network_destination(value):
    with pytest.raises(ValueError,match="model identifier"):
        safe_model_name(value)


def test_model_contract_does_not_offer_unrecorded_studio_cursor(source_pair):
    from film_director_capabilities import build_contract,source_pointer_capabilities
    source,manifest=source_pair
    packet=build_contract(source,manifest,"Film real product interaction")
    status=packet["actualCapture"]["pointerProvenance"]
    assert status["allowedCursorModesForStudio"]==["none"]
    assert status["recordedPointerTrackAvailable"] is False
    m=json.loads(manifest.read_text())
    m["events"][0]["pointer_samples"]=[{"t":.6,"x":11,"y":20},{"t":.8,"x":18,"y":20}]
    status=source_pointer_capabilities(m,(320,180))
    assert status["eventLocalPointerSamplesPresent"] is True
    assert status["allowedCursorModesForStudio"]==["none"]


def test_stage_cursor_is_only_removed_with_verified_missing_source_track(source_pair):
    from studio_plan_bounded_repair import normalize_generated_studio_plan
    src,manifest=source_pair;m=json.loads(manifest.read_text())
    p={**valid_plan(src,manifest),"cursor":"recorded",
       "studioStage":{"camera":[{"at":0,"scale":.8},{"at":2,"scale":.8}],
                      "lighting":{"eventIndex":0}}}
    result,receipt=normalize_generated_studio_plan(p,manifest=m)
    assert p["cursor"]=="recorded"
    assert result["cursor"]=="none"
    assert len(receipt["changes"])==1
    assert receipt["changes"][0]["field"]=="cursor"
    # A legacy glass lens can validly use separate local pointer samples.
    with_loupe={**p,"glassLoupe":{}}
    same,unused=normalize_generated_studio_plan(with_loupe,manifest=m)
    assert same["cursor"]=="recorded"
    # Explicit global pointer evidence retains the requested real cursor.
    m["pointer_samples"]=[
       {"t":.55,"x":35,"y":30},{"t":.85,"x":40,"y":42}]
    retained,unused=normalize_generated_studio_plan(p,manifest=m)
    assert retained["cursor"]=="recorded"
    assert not unused["changes"]


def test_model_packet_contains_frame_exact_research_provenance(source_pair):
    from film_director_capabilities import build_contract
    src,manifest=source_pair
    packet=build_contract(src,manifest,"Direct a real feature film")
    event=packet["actualCapture"]["verifiedEvents"][0]
    assert event["candidateCuts"]["action"]=={
        "nativeFrame":15,"atSeconds":.6,"notBeforeActualPress":True}
    assert event["candidateCuts"]["result"]["nativeFrame"]==26
    assert event["candidateCuts"]["result"]["atSeconds"]==1.04
    assert event["candidateCuts"]["result"]["onsetMethod"]=="sustained-pixel-evidence"
    assert packet["actualCapture"]["nativeFps"]==25
    assert "cut" in packet["outputSchema"]["properties"]["studioStage"]["properties"]["camera"]["items"]["properties"]
    assert "Future mock UI" not in json.dumps(packet)


def test_reference_paths_and_provenance_checked_before_model_use(source_pair,tmp_path):
    src,manifest=source_pair
    plan=valid_plan(src,manifest)
    oversized=tmp_path/"not-mp4.txt"
    oversized.write_text("not reference")
    def model(*args,**kwargs):
        raise AssertionError("No model/network call with invalid reference")
    def validator(*args):raise AssertionError("No validation needed")
    with pytest.raises(ValueError,match="Invalid private research reference"):
        run_unattended(src,manifest,"Beautiful source true product film",tmp_path/"new",
            model="gemini-3-flash-preview",key="dummy",max_attempts=1,
            model_call=model,validator=validator,render=False,
            reference_paths=[oversized])
    assert not (tmp_path/"new").exists()


def test_overview_scale_fit_preserves_every_non_final_creative_camera_key(source_pair,tmp_path):
    from studio_plan_bounded_repair import normalize_generated_studio_plan
    from spatial_studio_stage import load_studio_stage
    src,manifest=source_pair
    m=json.loads(manifest.read_text())
    plan={
        "schema":"sauce-film-plan-v1",
        "sourceSha256":hashlib.sha256(src.read_bytes()).hexdigest(),
        "manifestSha256":hashlib.sha256(manifest.read_bytes()).hexdigest(),
        "durationSeconds":2.0,"presentation":"fullscreen","cursor":"none",
        "studioStage":{
           "camera":[
               {"at":0,"scale":.73,"center":[.5,.5]},
               {"at":.85,"scale":.95,"focus":"event:0:target"},
               {"at":1.3,"startAt":1.3,"scale":.85,"focus":"event:0:result"},
               {"at":2.0,"scale":1.12,"center":[.5,.5]}],
           "lighting":{"eventIndex":0,"trigger":"verified"},
           "payoff":{"region":"event:0:result","mode":"overview",
                     "minVisible":.70,"minContextVisible":.85}
        }}
    original=json.loads(json.dumps(plan))
    corrected,receipt=normalize_generated_studio_plan(
        plan,manifest=m,source_path=src,source_size=(320,180),
        fps=25,output_size=(640,360))
    changed=[item for item in receipt["changes"] if item["field"].endswith(".scale")]
    assert len(changed)<=1
    assert corrected["studioStage"]["camera"][:-1]==original["studioStage"]["camera"][:-1]
    assert corrected["studioStage"]["camera"][-1]["at"]==2.0
    assert corrected["sourceSha256"]==original["sourceSha256"]
    assert corrected["manifestSha256"]==original["manifestSha256"]
    assert corrected["studioStage"]["camera"][-1]["scale"]<=original["studioStage"]["camera"][-1]["scale"]
    assert corrected["studioStage"]["camera"][-1]["scale"]>=original["studioStage"]["camera"][-1]["scale"]-.22-.0001
    assert plan==original


def test_redundant_default_center_and_default_quintic_only_are_mechanical(source_pair):
    from studio_plan_bounded_repair import normalize_generated_studio_plan
    src,manifest=source_pair
    p={"presentation":"window","studioStage":{"camera":[
        {"at":0,"scale":.8,"center":[.5,.5]},
        {"at":2.0,"scale":.85,"center":[.5,.5],
         "focus":"event:0:result","easing":"quintic"}],
        "lighting":{"eventIndex":0}}}
    old=json.loads(json.dumps(p))
    fixed,receipt=normalize_generated_studio_plan(p)
    assert old==p
    assert fixed["presentation"]=="fullscreen"
    assert fixed["studioStage"]["camera"][1].get("center") is None
    assert fixed["studioStage"]["camera"][1].get("easing") is None
    assert len(receipt["changes"])==3
    # Unsupported easing must stay in JSON and be rejected by strict validator.
    odd=json.loads(json.dumps(p))
    odd["studioStage"]["camera"][1]["easing"]="linear"
    unchanged,r=normalize_generated_studio_plan(odd)
    assert unchanged["studioStage"]["camera"][1]["easing"]=="linear"
