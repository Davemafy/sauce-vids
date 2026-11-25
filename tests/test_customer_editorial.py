import copy,json
from pathlib import Path
from unittest.mock import Mock,patch
import numpy as np
import pytest
from scripts import customer_editorial as editorial
from backend import customer_story as story

IDS=["a0","a1","a2"]
def intent():
    return {"backdrop":"graphite","duration_seconds":30,"beats":[
        {"action_id":"a0","framing":"wide","pace":"quick","purpose":"Establish original result"},
        {"action_id":"a1","framing":"accent","pace":"readable","purpose":"Prove change"},
        {"action_id":"a2","framing":"detail","pace":"linger","purpose":"Read the payoff"}]}

def test_model_semantics_change_capture_schedule_and_preserve_budget():
    a=intent();b=copy.deepcopy(a)
    b["beats"][0]["pace"]="linger";b["beats"][2]["pace"]="quick"
    x=editorial.schedule(a,IDS,"a2");y=editorial.schedule(b,IDS,"a2")
    assert x[0]==y[0]==.8 and x[1]<y[1]
    for times in (x,y):
        assert min(np.diff(times))>=5 and times[-1]<=20.8

@pytest.mark.parametrize("mutate",[
    lambda a:a["beats"].reverse(),
    lambda a:a["beats"][0].update(action_id="unknown"),
    lambda a:[b.update(framing="detail") for b in a["beats"]],
    lambda a:a["beats"][0].update(pace="unbounded"),
    lambda a:a["beats"][0].update(x=500),
    lambda a:a.update(backdrop="arbitrary"),
    lambda a:a.update(duration_seconds=15),
])
def test_unverified_editorial_control_rejected(mutate):
    a=intent();mutate(a)
    with pytest.raises(ValueError):editorial.validate(a,IDS,"a2")

def test_claude_editorial_admission_persists_exact_model_decision(tmp_path,monkeypatch):
    catalog=[{"id":i,"kind":"option","label":i} for i in IDS]
    raw=json.dumps({"ids":IDS,"story":"Observed product benefit","hero_action_id":"a2"})
    c=Mock();c.provider_name="Claude";c.calls=3;c.data={"model":"claude-sonnet-5-5"}
    c.ask.return_value=json.dumps({"accept":True,"reason":"Observed benefit",**intent()})
    monkeypatch.setattr(story,"probe_story",lambda p,o:([{"id":i} for i in IDS],[],None))
    plan,_,_=story.investigate_story(raw,catalog,{},b"",tmp_path,c,"brief")
    assert plan["editorial"]==intent()
    assert c.ask.call_args.kwargs["response_schema"]["properties"]["beats"]["items"]["properties"]["action_id"]["enum"]==IDS
    assert json.loads((tmp_path/"direction.json").read_text())["editorial"]==intent()

def test_model_camera_authority_is_executed_and_independently_verified(tmp_path,monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]/"scripts"))
    from source_event_director import direction
    from spatial_studio_stage import load_studio_stage
    from customer_craft_contract import verify_plan
    ev=[{"start":t,"end":t+.1,"t":t+1.5,"evidence":"verified","kind":"click",
         "targetRect":{"x":1260,"y":725,"width":80,"height":50},
         "resultRect":{"x":1000,"y":500,"width":1400,"height":800}} for t in (2.,9.,20.)]
    m={"cursorless":True,"events":ev,"duration":30.,
       "pointer_samples":[{"t":i*.1,"x":1300,"y":750} for i in range(300)]}
    source=tmp_path/"source.mp4";source.write_bytes(b"fixture")
    manifest=tmp_path/"manifest.json";manifest.write_text(json.dumps(m))
    packet={"actualCapture":{"durationSeconds":30.,"resolution":[3840,2160],
        "nativeFps":60,"pointerProvenance":{"recordedPointerTrackAvailable":True}}}
    with patch("film_director_capabilities.build_contract",return_value=packet):
        baseline=direction(source,manifest,2)
        plan=direction(source,manifest,2,{"ids":IDS,"hero":"a2","editorial":intent()})
        wrong=copy.deepcopy(intent());wrong["beats"][2]["framing"]="wide"
        no_detail=direction(source,manifest,2,{"ids":IDS,"hero":"a2","editorial":wrong})
    stage=load_studio_stage(plan["studioStage"],m,source,(3840,2160),(1920,1080),30.,60)
    plain=load_studio_stage(baseline["studioStage"],m,source,(3840,2160),(1920,1080),30.,60)
    assert stage.backdrop_tone=="graphite"
    assert stage.view_scale(4.)==1. and plain.view_scale(4.)>1.
    assert max(k.view_scale for k in stage.camera)>=1.2
    assert "heroEventIndex" not in no_detail["studioStage"]["motion"]
    assert len(plan["studioStage"]["camera"])<len(baseline["studioStage"]["camera"])
    ptr=np.asarray([[p["t"],p["x"],p["y"]] for p in m["pointer_samples"]])
    assert verify_plan(plan,m,stage,ptr,60,1800)["minimumResultVisible"]==1.

def test_compact_story_uses_actual_shorter_verified_source(tmp_path,monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]/"scripts"))
    from source_event_director import direction
    from spatial_studio_stage import load_studio_stage
    from customer_craft_contract import verify_plan
    a=intent();a["duration_seconds"]=22
    starts=editorial.schedule(a,IDS,"a2")
    assert starts[-1]<=12.8
    ev=[{"start":t,"end":t+.1,"t":t+1.2,"evidence":"verified","kind":"click",
         "targetRect":{"x":1260,"y":725,"width":80,"height":50},
         "resultRect":{"x":1000,"y":500,"width":1400,"height":800}} for t in (2.,8.,14.)]
    m={"cursorless":True,"events":ev,"duration":22.,
       "pointer_samples":[{"t":i*.1,"x":1300,"y":750} for i in range(220)]}
    source=tmp_path/"source.mp4";source.write_bytes(b"fixture")
    manifest=tmp_path/"manifest.json";manifest.write_text(json.dumps(m))
    packet={"actualCapture":{"durationSeconds":22.,"resolution":[3840,2160],
        "nativeFps":60,"pointerProvenance":{"recordedPointerTrackAvailable":True}}}
    with patch("film_director_capabilities.build_contract",return_value=packet):
        plan=direction(source,manifest,2,{"ids":IDS,"hero":"a2","editorial":a})
        with pytest.raises(ValueError,match="duration"):
            direction(source,manifest,2,{"ids":IDS,"hero":"a2","editorial":intent()})
    stage=load_studio_stage(plan["studioStage"],m,source,(3840,2160),(1920,1080),22.,60)
    ptr=np.asarray([[p["t"],p["x"],p["y"]] for p in m["pointer_samples"]])
    assert plan["durationSeconds"]==22 and verify_plan(plan,m,stage,ptr,60,1320)["checkedFrames"]==1320

def test_two_detail_beats_preserve_both_real_results(tmp_path,monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]/"scripts"))
    from source_event_director import direction
    from spatial_studio_stage import load_studio_stage
    from customer_craft_contract import verify_plan
    ev=[{"start":t,"end":t+.1,"t":t+1.2,"evidence":"verified","kind":"click",
         "targetRect":{"x":1260,"y":725,"width":80,"height":50},
         "resultRect":{"x":1000,"y":500,"width":1400,"height":800}} for t in (2.,10.,20.)]
    m={"cursorless":True,"events":ev,"duration":30.,
       "pointer_samples":[{"t":i*.1,"x":1300,"y":750} for i in range(300)]}
    source=tmp_path/"source.mp4";source.write_bytes(b"fixture")
    manifest=tmp_path/"manifest.json";manifest.write_text(json.dumps(m))
    packet={"actualCapture":{"durationSeconds":30.,"resolution":[3840,2160],
        "nativeFps":60,"pointerProvenance":{"recordedPointerTrackAvailable":True}}}
    a=intent();a["beats"][0]["framing"]="detail"
    with patch("film_director_capabilities.build_contract",return_value=packet):
        plan=direction(source,manifest,2,{"ids":IDS,"hero":"a2","editorial":a})
    assert plan["studioStage"]["motion"]["detailEventIndices"]==[0,2]
    stage=load_studio_stage(plan["studioStage"],m,source,(3840,2160),(1920,1080),30.,60)
    ptr=np.asarray([[p["t"],p["x"],p["y"]] for p in m["pointer_samples"]])
    metrics=verify_plan(plan,m,stage,ptr,60,1800)
    assert metrics["detailEventIndices"]==[0,2] and metrics["minimumResultVisible"]==1.
    assert metrics["heroMinimumResultVisible"]==1.
    assert metrics["maximumQuadSpeedPx"]<=8 and metrics["maximumQuadAccelerationPx"]<=1.5
    for i in (0,2):
        assert stage.hero_backdrop_strength(ev[i]["t"]-.1)==0.
    wrong=copy.deepcopy(plan["studioStage"]);wrong["motion"]["detailEventIndices"]=[0,1]
    with pytest.raises(ValueError):load_studio_stage(wrong,m,source,(3840,2160),(1920,1080),30.,60)
    wrong=copy.deepcopy(plan["studioStage"]);wrong["motion"]["detailEventIndices"]=[0,0]
    with pytest.raises(ValueError):load_studio_stage(wrong,m,source,(3840,2160),(1920,1080),30.,60)

def test_opt_in_gemini_can_direct_real_editorial_beats(tmp_path,monkeypatch):
    monkeypatch.setenv("SAUCE_CUSTOMER_EDITORIAL_DIRECTION","1")
    catalog=[{"id":i,"kind":"option","label":i} for i in IDS]
    raw=json.dumps({"ids":IDS,"story":"Observed benefit","hero_action_id":"a2"})
    c=Mock();c.provider_name="Gemini";c.calls=3;c.data={"model":"gemini-3.1-flash-lite"}
    a=intent();a["beats"][0]["framing"]="detail"
    c.ask.return_value=json.dumps({"accept":True,"reason":"Observed benefit",**a})
    monkeypatch.setattr(story,"probe_story",lambda p,o:([{"id":i} for i in IDS],[],None))
    plan,_,_=story.investigate_story(raw,catalog,{},b"",tmp_path,c,"brief")
    assert plan["editorial"]==a and plan["director_provider"]=="gemini"
    assert c.ask.call_args.kwargs["response_schema"]["properties"]["beats"]["items"]["properties"]["action_id"]["enum"]==IDS
