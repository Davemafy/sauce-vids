"""Autonomous shot coverage: source truth, per-event pointer and bounded selection."""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path

import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))

from autonomous_shot_coverage import (
    PANEL_PROFILES,PROFILES,choose_diverse,geometry_score,make_plan,
    run,select_profiles,sha,_pointer_start,
)


def dummy(tmp_path,*,moving=True):
    file=tmp_path/"original.mp4"
    file.write_bytes(b"source-locked synthetic TEST-only bytes")
    events=[]
    for t in (2.,5.,8.):
        events.append({"kind":"click","start":t,"end":t+.12,"t":t+.4,
         "evidence":"Verified real DOM changed TEST fixture",
         "targetRect":{"x":800.,"y":200.,"width":450.,"height":80.},
         "resultRect":{"x":1100.,"y":460.,"width":650.,"height":430.}})
    pointer=[]
    if moving:
        for i,start in enumerate((1.2,4.25,7.2)):
            pointer.extend({"t":round(start+j*.03,4),
                            "x":810.+j*10,"y":250.} for j in range(20))
    else:
        pointer=[{"t":.1+i*.09,"x":810.,"y":250.} for i in range(95)]
    manifest=tmp_path/"manifest.json"
    manifest.write_text(json.dumps({
      "source":"https://real.example/","cursorless":True,
      "duration":11.5,"capture_rect":{"width":2880,"height":1800},
      "events":events,"pointer_samples":pointer}))
    packet={"actualCapture":{
      "nativeFps":60.0,"durationSeconds":11.5,
      "resolution":[2880,1800],
      "verifiedEvents":[{"index":i} for i in range(3)],
      "pointerProvenance":{"recordedPointerTrackAvailable":True}}}
    return file,manifest,packet


def test_source_measured_panel_vs_card_profile_not_hostname():
    same_url="https://example.com/anything"
    small={"source":same_url,"events":[{"resultRect":
        {"x":50,"y":30,"width":498,"height":122}}]}
    big={"source":same_url,"events":[{"resultRect":
        {"x":750,"y":340,"width":1900,"height":1400}}]}
    assert select_profiles(small,(2880,1800)) is PROFILES
    assert select_profiles(big,(2880,1800)) is PANEL_PROFILES
    bad={"events":[{"resultRect":{
        "x":1400,"y":20,"width":1900,"height":800}}]}
    with pytest.raises(ValueError,match="outside"):
        select_profiles(bad,(2880,1800))


def test_each_action_result_comes_from_actual_timestamps_and_has_real_pointer(tmp_path):
    source,manifest,packet=dummy(tmp_path)
    p,_=make_plan(source,manifest,packet,PROFILES[1])
    assert p["schema"]=="sauce-film-plan-v1"
    assert p["sourceSha256"]==sha(source)
    assert p["manifestSha256"]==sha(manifest)
    assert p["cursor"]=="recorded"
    assert p["audio"]["eventIndices"]==[0,1,2]
    keys=p["studioStage"]["camera"]
    assert keys[0]["scale"]<1
    source_events=json.loads(manifest.read_text())["events"]
    for i,event in enumerate(source_events):
        result=[k for k in keys if k.get("focus")==f"event:{i}:result"]
        assert result
        assert result[0]["startAt"]>=event["t"]
    assert all(b["at"]>a["at"] for a,b in zip(keys,keys[1:]))
    assert not p["studioStage"]["payoff"]["mode"]=="overview"


def test_missing_individual_pointer_motion_never_fakes_action_zoom(tmp_path):
    source,manifest,packet=dummy(tmp_path,moving=False)
    p,_=make_plan(source,manifest,packet,PROFILES[1])
    keys=p["studioStage"]["camera"]
    # At event zero, no artificial cursor-approach shot is created.
    assert not any(k.get("focus")=="event:0:target" for k in keys)
    # After an earlier result, release to genuine whole-browser context
    # before the next action instead of staying incorrectly cropped.
    assert len([k for k in keys[1:-1] if k.get("center")==[.5,.5]])>=2
    assert _pointer_start([{"t":i*.04,"x":10,"y":11} for i in range(40)],2.) is None


def test_choose_distinct_motion_grasps_not_three_near_duplicates():
    ranked=[{"name":"smooth","status":"source_verified_plan",
              "score":110,"hardCuts":0},
            {"name":"smooth2","status":"source_verified_plan",
              "score":109,"hardCuts":0},
            {"name":"eventcut","status":"source_verified_plan",
              "score":98,"hardCuts":3}]
    chosen=choose_diverse(ranked,2)
    assert [r["name"] for r in chosen]==["smooth","eventcut"]
    assert choose_diverse([],2)==[]


def test_sha_guard_refuses_tampered_capture_before_building_output(tmp_path):
    source,manifest,_=dummy(tmp_path)
    out=tmp_path/"films"
    with pytest.raises(ValueError,match="SHA256 changed"):
        run(source,manifest,out,expected_source_sha256="f"*64,render=False)
    assert not out.exists()
    with pytest.raises(ValueError,match="SHA256 changed"):
        run(source,manifest,out,expected_manifest_sha256="0"*64,render=False)
    assert not out.exists()
    out.mkdir();(out/"receipt.txt").write_text("existing")
    with pytest.raises(ValueError,match="overwrite"):
        run(source,manifest,out,render=False)


def test_proposed_result_shots_never_precede_verified_onset(tmp_path):
    source,manifest,packet=dummy(tmp_path)
    p,_=make_plan(source,manifest,packet,PROFILES[2])
    events=json.loads(manifest.read_text())["events"]
    result_keys=[k for k in p["studioStage"]["camera"]
                 if k.get("focus","").endswith(":result")]
    for i,e in enumerate(events):
        match=next(k for k in result_keys if k.get("focus")==f"event:{i}:result")
        assert match["cut"] is True
        assert match["at"]>=e["t"]
        assert abs(match["at"]*60-round(match["at"]*60))<1e-5



def test_public_url_pipeline_uses_coverage_without_model_key(tmp_path,monkeypatch):
    import auto_public_ui_film
    import autonomous_shot_coverage
    monkeypatch.setattr(auto_public_ui_film,"validate_public_url",lambda url:url)
    capture=tmp_path/"authentic"
    capture.mkdir()
    for name in ("source-real-dpr2-60.mp4","source-events.json"):
        (capture/name).write_bytes(b"test-only")
    (capture/"discovery.json").write_text(json.dumps({
        "url":"https://example.com/editor",
        "host":"example.com"}))
    monkeypatch.setattr(auto_public_ui_film,"normalize",lambda *a:{
        "source":"https://example.com/editor",
        "events":[{"kind":"tab_switch","start":1,"end":2,
                   "t":2,"evidence":"Verified in source TEST fixture"}]})
    monkeypatch.setattr(auto_public_ui_film,"build_contract",lambda *a:{
        "actualCapture":{
            "sourceSha256":"source-hash-test",
            "manifestSha256":"manifest-hash-test",
            "verifiedEvents":[{"index":0,"sourceTime":{
                "start":1,"confirmedResultAt":2}}]}})
    called=[]
    def fake_run(source,manifest,out,**kwargs):
        called.append(kwargs)
        return {"status":"requires_human_creative_review",
                "rendered":[{"profile":"proof",
                    "status":"rendered_needs_human_review",
                    "film":str(tmp_path/"fake-test-only.mp4"),
                    "filmSha256":"test-placeholder-not-a-real-video"}]}
    monkeypatch.setattr(autonomous_shot_coverage,"run",fake_run)
    receipt=auto_public_ui_film.run(
        "https://example.com/editor","example.com",tmp_path/"out",
        from_capture=capture,director_mode="coverage",key=None)
    assert len(called)==1
    assert called[0]["expected_source_sha256"]=="source-hash-test"
    assert called[0]["expected_manifest_sha256"]=="manifest-hash-test"
    assert receipt["providerAttemptCount"]==0
    assert receipt["directorMode"]=="deterministic_source_coverage"
    assert receipt["status"]=="film_requires_human_review"
    assert receipt["creativeApproved"] is False
    assert receipt["noAutoPublication"] is True
    assert receipt["productionReady"] is False

def test_cinematic_ablation_reuses_exact_existing_keyframes(tmp_path):
    src,man,packet=dummy(tmp_path)
    a,_=make_plan(src,man,packet,next(x for x in PROFILES if x[0]=="restrained"))
    b,_=make_plan(src,man,packet,next(x for x in PROFILES if x[0]=="cinematic"))
    assert a["studioStage"]["camera"]==b["studioStage"]["camera"]
    assert a["sourceSha256"]==b["sourceSha256"]
    assert a["manifestSha256"]==b["manifestSha256"]
    assert a["audio"]==b["audio"]
    assert "motion" not in a["studioStage"]
    assert b["studioStage"]["motion"]=={"profile":"cinematic","shutter":.58}
    ranked=[
       {"name":"restrained","status":"source_verified_plan","score":102,"hardCuts":0},
       {"name":"cinematic","status":"source_verified_plan","score":102,"hardCuts":0},
       {"name":"punchy","status":"source_verified_plan","score":100,"hardCuts":3}]
    assert [x["name"] for x in choose_diverse(ranked,2)]==["cinematic","restrained"]


def test_cinematic_camera_does_not_override_better_source_geometry():
    ranked=[
       {"name":"proof","status":"source_verified_plan","score":130,"hardCuts":0},
       {"name":"cinematic","status":"source_verified_plan","score":90,"hardCuts":0},
       {"name":"punchy","status":"source_verified_plan","score":106,"hardCuts":3}]
    assert [x["name"] for x in choose_diverse(ranked,2)]==["proof","punchy"]

def test_reference_paced_motion_has_readable_release_before_next_real_result(tmp_path):
    source,manifest,packet=dummy(tmp_path)
    paced=next(x for x in PROFILES if x[0]=="cinematic_paced")
    plan,rows=make_plan(source,manifest,packet,paced)
    real=json.loads(manifest.read_text())["events"]
    camera=plan["studioStage"]["camera"]
    assert plan["studioStage"]["motion"]["profile"]=="cinematic"
    for i,e in enumerate(real[:-1]):
        result=next(k for k in camera if k.get("focus")==f"event:{i}:result")
        release=next(k for k in camera if k.get("center")==[.5,.5]
                     and k["at"]>result["at"]+.1)
        assert .8<=result["at"]-result["startAt"]<=.9
        assert release["startAt"]>=result["at"]+.1
        # On fast workflows the release must end *before* the next
        # recorded press; on longer drags it may finish during the action.
        assert release["at"]<=min(real[i+1]["start"]+.32,
                                 real[i+1]["t"]-.70)+1/60+1e-7
        assert release["at"]<real[i+1]["t"]
    assert plan["sourceSha256"]==sha(source)
    assert plan["manifestSha256"]==sha(manifest)
