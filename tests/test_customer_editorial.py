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

def test_compact_story_two_distinct_capabilities_only(monkeypatch):
    catalog=[{"id":"a","kind":"option","group":"Style"},{"id":"b","kind":"option","group":"Theme"},{"id":"c","kind":"option","group":"Style"}]
    def pick(ids):
        return story.validated_selection(json.dumps({"ids":ids,"story":"Complete transformation","hero_action_id":ids[-1]}),catalog)
    assert pick(["a","b"]) is not None
    assert pick(["a","c"]) is None
    monkeypatch.setenv("SAUCE_EVIDENCE_FIRST","0")
    assert pick(["a","b"]) is None

@pytest.mark.parametrize("duration",[16,18,20])
def test_compact_verified_camera_and_foley(tmp_path,monkeypatch,duration):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]/"scripts"))
    from source_event_director import direction
    from spatial_studio_stage import load_studio_stage
    from customer_craft_contract import verify_plan
    ids=["a0","a1"]
    a=intent();a["duration_seconds"]=duration;a["beats"]=a["beats"][:2]
    a["beats"][1]["framing"]="detail"
    ev=[{"start":t,"end":t+.1,"t":t+1.2,"evidence":"verified","kind":"click",
         "targetRect":{"x":1260,"y":725,"width":80,"height":50},
         "resultRect":{"x":1000,"y":500,"width":1400,"height":800}} for t in (2.,8.)]
    m={"cursorless":True,"events":ev,"duration":float(duration),
       "pointer_samples":[{"t":i*.1,"x":1300,"y":750} for i in range(duration*10)]}
    source=tmp_path/"source.mp4";source.write_bytes(b"fixture")
    manifest=tmp_path/"manifest.json";manifest.write_text(json.dumps(m))
    packet={"actualCapture":{"durationSeconds":float(duration),"resolution":[3840,2160],
        "nativeFps":60,"pointerProvenance":{"recordedPointerTrackAvailable":True}}}
    with patch("film_director_capabilities.build_contract",return_value=packet):
        plan=direction(source,manifest,1,{"ids":ids,"hero":"a1","editorial":a})
    stage=load_studio_stage(plan["studioStage"],m,source,(3840,2160),(1920,1080),float(duration),60)
    ptr=np.asarray([[p["t"],p["x"],p["y"]] for p in m["pointer_samples"]])
    metrics=verify_plan(plan,m,stage,ptr,60,duration*60)
    assert metrics["checkedActions"]==2 and metrics["checkedFrames"]==duration*60
    assert metrics["minimumResultVisible"]==1. and metrics["detailEventIndices"]==[1]
    assert plan["audio"]["eventIndices"]==[0,1]
    assert editorial.schema(ids)["properties"]["duration_seconds"]["enum"]==[12,13,16,18,20]
    assert editorial.schedule(a,ids,"a1")[-1]<=duration-9.2+1e-6
    for bad in (15,22,30):
        with pytest.raises(ValueError):editorial.validate({**a,"duration_seconds":bad},ids,"a1")

@pytest.mark.parametrize("count,duration",[(2,13),(3,18)])
def test_shortest_native_story_preserves_real_action_time_and_reading_hold(tmp_path,monkeypatch,count,duration):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]/"scripts"))
    from source_event_director import direction
    from spatial_studio_stage import load_studio_stage
    from customer_craft_contract import verify_plan
    ids=IDS[:count]
    a=intent()
    a["duration_seconds"]=duration
    a["beats"]=a["beats"][:count]
    a["beats"][-1]["framing"]="accent"
    starts=editorial.schedule(a,ids,ids[-1])
    assert starts==[.8+5*i for i in range(count)]
    assert duration-starts[-1]==pytest.approx(7.2)
    # Fixture timings modeled on the observed shadcn v2 capture (3.3-3.53s
    # from scheduled start to confirmation), not fabricated customer footage.
    ev=[{"start":t+2.1,"end":t+2.3,"t":t+3.5,"evidence":"fixture",
         "kind":"click","targetRect":{"x":1260,"y":725,"width":80,"height":50},
         "resultRect":{"x":544,"y":140,"width":3248,"height":1972}} for t in starts]
    m={"cursorless":True,"events":ev,"duration":float(duration),
       "pointer_samples":[{"t":i*.1,"x":1300,"y":750} for i in range(duration*10)]}
    source=tmp_path/"source.mp4";source.write_bytes(b"fixture")
    manifest=tmp_path/"manifest.json";manifest.write_text(json.dumps(m))
    packet={"actualCapture":{"durationSeconds":float(duration),"resolution":[3840,2160],
            "nativeFps":60,"pointerProvenance":{"recordedPointerTrackAvailable":True}}}
    with patch("film_director_capabilities.build_contract",return_value=packet):
        plan=direction(source,manifest,count-1,{"ids":ids,"hero":ids[-1],"editorial":a})
    stage=load_studio_stage(plan["studioStage"],m,source,(3840,2160),(1920,1080),float(duration),60)
    ptr=np.asarray([[p["t"],p["x"],p["y"]] for p in m["pointer_samples"]])
    metrics=verify_plan(plan,m,stage,ptr,60,duration*60)
    assert metrics["checkedActions"]==count and metrics["minimumResultVisible"]==1.
    assert duration-ev[-1]["t"]==pytest.approx(3.7)
    assert plan["audio"]["eventIndices"]==list(range(count))
    assert editorial.schema(ids)["properties"]["duration_seconds"]["enum"][0]==(12 if count==2 else duration)
    with pytest.raises(ValueError):
        editorial.validate({**a,"duration_seconds":11 if count==2 else duration-1},ids,ids[-1])


def test_supporting_detail_compiles_short_model_request_into_native_budget():
    ids=IDS[:2]
    a=intent();a["duration_seconds"]=13;a["beats"]=a["beats"][:2]
    a["beats"][1]["framing"]="detail"
    a["duration_seconds"]=12
    with pytest.raises(ValueError,match="detail travel"):
        editorial.validate(a,ids,"a0")
    compiled=editorial.fit_duration(a,ids,"a0")
    assert a["duration_seconds"]==12 and compiled["duration_seconds"]==16
    starts=editorial.schedule(compiled,ids,"a0")
    assert compiled["duration_seconds"]-starts[-1]>=9.7-1e-6
    assert compiled["beats"]==a["beats"]

def test_nonfinal_detail_earns_time_even_with_quick_pace():
    a=intent();a["duration_seconds"]=18
    a["beats"][0]["framing"]="detail"
    a["beats"][2]["framing"]="wide"
    compiled=editorial.fit_duration(a,IDS,"a1")
    assert compiled["duration_seconds"]==26
    starts=editorial.schedule(compiled,IDS,"a1")
    assert starts[1]-starts[0]>=9.
    assert starts[2]-starts[1]>=5.


def test_small_verified_local_result_earns_detail_and_native_budget():
    ids=["lv2","lv3"]
    actions=[{"id":i,"control":"local-demo-view"} for i in ids]
    proofs=[{"id":i,"result":{"x":408,"y":418,"width":1104,"height":483}} for i in ids]
    a={"backdrop":"cobalt","duration_seconds":13,"beats":[
        {"action_id":ids[0],"framing":"wide","pace":"readable","purpose":"Filter"},
        {"action_id":ids[1],"framing":"accent","pace":"linger","purpose":"Table"}]}
    amended,receipt=editorial.protect_local_readability(a,actions,ids[0],proofs,(1920,1080))
    assert amended["beats"][0]["framing"]=="detail" and amended["duration_seconds"]>=18
    assert amended["beats"][1]==a["beats"][1] and a["beats"][0]["framing"]=="wide"
    assert receipt["action_id"]==ids[0]
    assert editorial.protect_local_readability(amended,actions,ids[0],proofs,(1920,1080))==(amended,None)
    assert editorial.protect_local_readability(a,[{"id":i} for i in ids],ids[0],proofs,(1920,1080))==(a,None)
    broad=[{"id":i,"result":{"x":0,"y":0,"width":1920,"height":1080}} for i in ids]
    assert editorial.protect_local_readability(a,actions,ids[0],broad,(1920,1080))==(a,None)


def test_fast_local_pacing_shortens_only_witnessed_fast_workflows():
    ids=['a','b'];actions=[{'id':i,'control':'local-demo-view'} for i in ids];proofs=[{'id':i,'probe_seconds':1.2} for i in ids]
    a={'backdrop':'muted','duration_seconds':16,'beats':[{'action_id':i,'framing':'wide','pace':'readable','purpose':'Proof'} for i in ids]}
    short,receipt=editorial.compact_fast_local(a,actions,'a',proofs)
    assert short['duration_seconds']==12 and receipt['previous_duration']==16
    a['beats'][1]['framing']='detail';short,_=editorial.compact_fast_local(a,actions,'a',proofs)
    assert short['duration_seconds']==13
    proofs[0]['probe_seconds']=2.5
    assert editorial.compact_fast_local(a,actions,'a',proofs)==(a,None)


def test_measured_combobox_latency_preserves_native_reading_time():
    ids=['a','b'];actions=[{'id':i,'kind':'option','control':'presentation-combobox'} for i in ids]
    a={'backdrop':'muted','duration_seconds':12,'beats':[{'action_id':i,'framing':'wide','pace':pace,'purpose':'Verified'} for i,pace in zip(ids,['readable','linger'])]}
    proofs=[{'id':'a','probe_seconds':3.811481},{'id':'b','probe_seconds':4.07615}]
    amended,starts,receipt=editorial.measured_schedule(a,actions,'b',proofs)
    assert amended['duration_seconds']==16 and a['duration_seconds']==12
    assert starts[0]==.8 and starts[1]-starts[0]>=3.811481+1.10+.9-1e-6
    assert amended['duration_seconds']-starts[1]>=4.07615+1.10+2.15-1e-6
    assert editorial.measured_schedule(amended,actions,'b',proofs)[:2]==(amended,starts)
    assert receipt['probe_seconds']==[3.811481,4.07615]
    fast=[{'id':i,'probe_seconds':1.2} for i in ids]
    assert editorial.measured_schedule(a,actions,'b',fast)[0]==a
    with pytest.raises(ValueError,match='timing budget'):
        editorial.measured_schedule(a,actions,'b',[{'id':i,'probe_seconds':12.} for i in ids])
