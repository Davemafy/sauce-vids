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


def test_encoded_video_reject_feedback_preserves_original_film_and_retries(source_pair,tmp_path,monkeypatch):
    """Real rejection is retained and supplied to the next director attempt."""
    import auto_direct_studio_film as director
    import quality_preview_supervisor as supervisor
    src,manifest=source_pair
    plan=valid_plan(src,manifest)
    attempts=[]
    feedbacks=[]
    def model(s,packet,model,key,feedback):
        feedbacks.append(feedback)
        return json.dumps(plan),{"usageMetadata":{"totalTokenCount":111}}
    def validator(s,m,p,dir):
        assert json.loads(p.read_text())==plan
        return True,"Actual source hash and native timing approved"
    real_run=director.subprocess.run
    def render(cmd,**kwargs):
        if "--output" not in cmd:
            return real_run(cmd,**kwargs)
        path=Path(cmd[cmd.index("--output")+1])
        path.write_bytes(b"actual-encoded-film-stub-"+str(len(attempts)).encode())
        attempts.append(str(path))
        from subprocess import CompletedProcess
        return CompletedProcess(cmd,0,stdout="verified film")
    def qa(path,*,evidence,seconds):
        if len(attempts)==1:
            return {"verdict":"REJECT","findings":[
                {"code":"WASHED_OUT_FRAMES","detail":{"fraction":.8}}]}
        return {"verdict":"HUMAN_REVIEW_REQUIRED","findings":[]}
    monkeypatch.setattr(director.subprocess,"run",render)
    monkeypatch.setattr(supervisor,"analyze",qa)
    out=tmp_path/"private"
    result=run_unattended(
        src,manifest,"A great real 2s cinematic film",out,
        model="gemini-3-flash-preview",key="test-key",max_attempts=3,
        model_call=model,validator=validator,render=True,
        editorial_preflight=False)
    assert len(attempts)==2
    assert result["winningAttempt"]==2
    assert result["outcome"]=="needs_review"
    assert result["creativeApproved"] is False
    assert result["attempts"][0]["status"]=="rendered_objective_reject_retry"
    assert (out/"film-attempt-1-rejected.mp4").read_bytes()==b"actual-encoded-film-stub-0"
    assert (out/"film.mp4").read_bytes()==b"actual-encoded-film-stub-1"
    assert (out/"encoded-visual-qa-attempt-1.json").exists()
    assert (out/"encoded-visual-qa.json").exists()
    assert "WASHED_OUT_FRAMES" in feedbacks[1]
    assert feedbacks[0] is None
    assert len(feedbacks)==2
    assert "test-key" not in (out/"unattended-receipt.json").read_text()


def test_bounded_three_calls_never_auto_approves_failed_creative_film(source_pair,tmp_path):
    src,manifest=source_pair
    def model(*args):return json.dumps(valid_plan(src,manifest)),{}
    def reject(*args):return False,"Source camera leaves real action frame"
    result=run(src,manifest,tmp_path/"private",model,reject,max_attempts=3)
    assert len(result["attempts"])==3
    assert result["outcome"]=="failed"
    assert result["creativeApproved"] is False
    assert not (tmp_path/"private"/"film.mp4").exists()
    with pytest.raises(ValueError,match="bounded"):
        run(src,manifest,tmp_path/"never",model,reject,max_attempts=4)


def test_grouped_live_dom_time_repairs_are_native_and_bounded_only():
    from studio_plan_bounded_repair import normalize_generated_studio_plan
    p={"presentation":"fullscreen",
       "studioStage":{},
       "domPlanes":[
         {"id":"a","startAt":1.5,"peakAt":2.5,"endAt":3.4},
         {"id":"b","startAt":1.733,"peakAt":2.55,"endAt":3.4}
       ]}
    old=json.loads(json.dumps(p))
    fixed,receipt=normalize_generated_studio_plan(p,fps=60)
    assert p==old
    assert fixed["domPlanes"][0]==old["domPlanes"][0]
    assert fixed["domPlanes"][1]["startAt"]==pytest.approx(104/60,abs=1e-8)
    assert fixed["domPlanes"][1]["peakAt"]==pytest.approx(150/60,abs=1e-8)
    assert fixed["domPlanes"][1]["endAt"]==3.4
    assert all(entry["field"].startswith("domPlanes[1].")
               for entry in receipt["changes"])
    assert len(receipt["changes"])==2
    unsafe=json.loads(json.dumps(p))
    unsafe["domPlanes"][1]["peakAt"]=2.73
    not_fixed,unsafe_receipt=normalize_generated_studio_plan(unsafe,fps=60)
    # Too late to return the genuine DOM plane: must fail strict renderer.
    assert not_fixed["domPlanes"][1]["peakAt"]==2.733333333
    assert not any(q["field"]=="domPlanes[1].peakAt" and q.get("reason","").startswith("Bounded")
                   for q in unsafe_receipt["changes"])


def test_source_director_preflight_rejects_cropped_and_silent_real_action(source_pair):
    from source_director_preflight import preflight_source_edit
    src,manifest=source_pair
    m=json.loads(manifest.read_text())
    plan=valid_plan(src,manifest)
    del plan["camera"]
    plan["studioStage"]={
      "camera":[{"at":0,"scale":1.45,"focus":"event:0:target"},
                {"at":2.0,"scale":.78,"center":[.5,.5]}],
      "lighting":{"eventIndex":0,"trigger":"verified"},
      "payoff":{"region":"event:0:result","mode":"overview",
                "minVisible":.75,"minContextVisible":.80}
    }
    report=preflight_source_edit(plan,m,src,(320,180),25,output_size=(640,360))
    assert report["verdict"]=="REJECT"
    assert report["creativeApproved"] is False
    codes=[f["code"] for f in report["findings"]]
    assert "UNRECOGNIZABLE_OPENING_CROP" in codes
    assert "ACTION_FILM_WITHOUT_VERIFIED_AUDIO" in codes
    plan["studioStage"]["camera"][0]={"at":0,"scale":.78,"center":[.5,.5]}
    plan["audio"]={"mode":"eventFoley","eventIndex":0,
                   "clickGain":.4,"motionGain":.15,"masterGain":.35}
    fixed=preflight_source_edit(plan,m,src,(320,180),25,output_size=(640,360))
    assert fixed["verdict"]=="GEOMETRY_AND_AUDIO_PREFLIGHT_PASS"
    assert not fixed["findings"]
    assert fixed["creativeApproved"] is False


def test_explicit_customer_mute_skips_audio_veto_but_not_source_crop(source_pair):
    from source_director_preflight import preflight_source_edit
    src,manifest=source_pair
    m=json.loads(manifest.read_text())
    plan=valid_plan(src,manifest)
    plan["studioStage"]={
      "camera":[{"at":0,"scale":1.45,"focus":"event:0:target"},
                {"at":2.0,"scale":.78,"center":[.5,.5]}],
      "lighting":{"eventIndex":0},
      "payoff":{"region":"event:0:result","minVisible":.75}
    }
    r=preflight_source_edit(plan,m,src,(320,180),25,
                            output_size=(640,360),audio_required=False)
    assert [f["code"] for f in r["findings"]]==["UNRECOGNIZABLE_OPENING_CROP"]


def test_unattended_director_retries_real_source_editorial_failures(
        source_pair,tmp_path,monkeypatch):
    import auto_direct_studio_film as director
    import quality_preview_supervisor as supervisor
    src,manifest=source_pair
    base=valid_plan(src,manifest)
    del base["camera"]
    base["studioStage"]={
      "camera":[{"at":0,"scale":.78,"center":[.5,.5]},
                {"at":2.0,"scale":.78,"center":[.5,.5]}],
      "lighting":{"eventIndex":0},
      "payoff":{"region":"event:0:result","mode":"overview"}
    }
    base["audio"]={"mode":"eventFoley","eventIndex":0,
                   "clickGain":.4,"motionGain":.2,"masterGain":.5}
    broken=json.loads(json.dumps(base))
    broken["studioStage"]["camera"][0]={
      "at":0,"scale":1.45,"focus":"event:0:target"}
    broken["audio"]={"mode":"clean"}
    seen=[]
    def model(s,packet,model,key,feedback):
        seen.append(feedback)
        plan=broken if len(seen)==1 else base
        return json.dumps(plan),{"usageMetadata":{"totalTokenCount":99}}
    def validate(*args):return True,"real renderer source verified"
    subprocess_run=director.subprocess.run
    def render(cmd,**kwargs):
        if "--output" not in cmd:return subprocess_run(cmd,**kwargs)
        Path(cmd[cmd.index("--output")+1]).write_bytes(b"mock-encoded-output")
        from subprocess import CompletedProcess
        return CompletedProcess(cmd,0,stdout="rendered")
    monkeypatch.setattr(director.subprocess,"run",render)
    monkeypatch.setattr(supervisor,"analyze",
                        lambda *args,**kwargs:{"verdict":"HUMAN_REVIEW_REQUIRED","findings":[]})
    out=tmp_path/"private"
    result=run_unattended(src,manifest,"Real software film",out,
         model="gemini-3-flash-preview",key="test-secret",
         model_call=model,validator=validate,max_attempts=3,render=True)
    assert len(seen)==2
    assert "UNRECOGNIZABLE_OPENING_CROP" in seen[1]
    assert "ACTION_FILM_WITHOUT_VERIFIED_AUDIO" in seen[1]
    assert result["attempts"][0]["status"]=="editorial_preflight_reject"
    assert result["outcome"]=="needs_review"
    assert result["creativeApproved"] is False
    assert (out/"editorial-preflight-1.json").exists()
    assert (out/"editorial-preflight-2.json").exists()
    assert not (out/"film-attempt-1-rejected.mp4").exists()
    assert (out/"film.mp4").exists()


def test_provider_429_stops_before_unbounded_retry_or_fake_film(source_pair,tmp_path):
    from urllib.error import HTTPError
    src,manifest=source_pair
    seen=[]
    def blocked(*args):
        seen.append(1)
        raise HTTPError("https://example.invalid/",429,"Quota",{},None)
    def forbidden_validator(*args):
        raise AssertionError("No plan/renderer call after provider rejected")
    out=tmp_path/"quota-blocked"
    result=run(src,manifest,out,blocked,forbidden_validator,max_attempts=3)
    assert seen==[1]
    assert result["outcome"]=="provider_unavailable"
    assert result["attempts"][0]["httpStatus"]==429
    assert result["attempts"][0]["status"]=="provider_http_blocked"
    assert result["rendered"] is False
    assert result["creativeApproved"] is False
    assert not (out/"film.mp4").exists()
    assert "secret-used-only-in-memory" not in (out/"unattended-receipt.json").read_text()



def test_refit_story_is_aspirational_and_never_changes_real_capture(source_pair,tmp_path):
    src,manifest=source_pair
    m=json.loads(manifest.read_text())
    m["source"]="https://refit.davemafy.xyz/"
    manifest.write_text(json.dumps(m))
    brief={
        "schema":"sauce-creative-brief-v1",
        "sourceUrl":"https://refit.davemafy.xyz",
        "output":{"orientation":"landscape","targetDurationSeconds":80},
        "story":{"payoff":"Bring your agent. Change the model. Keep the behavior."},
        "scenes":[
            {"id":"hook","role":"hook","targetSeconds":9,
             "recordedEvidence":{"original":"24/24","replacement":"13/24"},
             "actions":[{"type":"navigate","target":"/"}]},
            {"id":"run","role":"demonstration","targetSeconds":12,
             "actions":[{"type":"click","target":"Run refund agent"}]}
        ]}
    creative=tmp_path/"client-story.json";creative.write_text(json.dumps(brief))
    plan=valid_plan(src,manifest)
    calls=[]
    def fake_model(s,packet,model,key,feedback):
        assert packet["actualCapture"]["durationSeconds"]==2.0
        assert len(packet["actualCapture"]["verifiedEvents"])==1
        assert "24/24" not in json.dumps(packet["actualCapture"])
        assert packet["unverifiedClientStoryIntent"]["requestedDurationSeconds"]==80
        assert packet["unverifiedClientStoryIntent"]["clientBrief"]["scenes"][0]["recordedEvidence"]["original"]=="24/24"
        calls.append(1)
        return json.dumps(plan),{"usageMetadata":{}}
    result=run_unattended(src,manifest,"Demonstrate product with source-true evidence",
         tmp_path/"with-story",model="gemini-3-flash-preview",key="fake",
         model_call=fake_model,validator=lambda *args:(True,"source verified"),
         max_attempts=1,render=False,creative_brief_path=creative)
    assert calls==[1]
    assert result["outcome"]=="validated_not_rendered"
    assert result["creativeApproved"] is False

    creative_wrong=tmp_path/"wrong-product-story.json"
    brief["sourceUrl"]="https://other.example"
    creative_wrong.write_text(json.dumps(brief))
    with pytest.raises(ValueError,match="hostname"):
        run_unattended(src,manifest,"Demonstrate product with source-true evidence",
             tmp_path/"wrong-story",model="gemini-3-flash-preview",key="fake",
             model_call=fake_model,validator=lambda *args:(True,"source verified"),
             max_attempts=1,render=False,creative_brief_path=creative_wrong)
    assert not (tmp_path/"wrong-story").exists()
