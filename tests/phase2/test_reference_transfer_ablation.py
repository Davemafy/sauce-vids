import json
from pathlib import Path
import pytest
from scripts.reference_transfer_ablation import generate_ablation_plans

@pytest.fixture
def track(tmp_path):
    """Synthetic numeric track; proprietary real-reference measurements stay private."""
    trace=tmp_path/"synthetic-reference.research.json"
    data={"schema":"sauce-reference-raster-panel-track-research-v1",
          "sourceSha256":"a"*64,
          "sourceFrameRate":[30,1],
          "fidelityTier":"research_only",
          "approvedForGemini":False,
          "method":"Synthetic box growth fixture, not extracted proprietary reference data.",
          "measurements":[]}
    for i in range(46):
        w=1520+round(30*i/45)
        h=480+round(9*i/45)
        x=(1920-w)//2
        y=(1080-h)//2
        data["measurements"].append({"referenceFrame":1392+i,"box":[x,y,w,h]})
    trace.write_text(json.dumps(data))
    return trace

def evidence(tmp_path,*,rect,t=1.9,valid=True):
    src=tmp_path/"source.mp4"
    src.write_bytes(b"synthetic-test-media-marker")
    manifest=tmp_path/"events.json"
    manifest.write_text(json.dumps({"cursorless":True,"capture_rect":{"width":1920,"height":1080},
        "duration":4.1,"events":[{"kind":"theme_change","t":t,
            "evidence":"Genuine visible browser outcome" if valid else "",
            "targetRect":{"x":300,"y":700,"width":100,"height":20},
            "resultRect":rect,"componentRect":rect,"pointer_samples":[]}]}))
    return src,manifest

def test_research_trace_clock_complete_without_real_reference_pixels(track):
    data=json.loads(track.read_text())
    assert data["fidelityTier"]=="research_only"
    assert data["approvedForGemini"] is False
    assert len(data["measurements"])==46
    assert data["measurements"][0]["box"][2]==1520
    assert data["measurements"][-1]["box"][2]==1550

def test_compatible_full_source_component_gets_three_research_only_plans(tmp_path,track):
    s,m=evidence(tmp_path,rect={"x":521,"y":348.5,"width":1118,"height":316})
    out=tmp_path/"plans"
    result=generate_ablation_plans(s,m,track,out,duration_seconds=4.0)
    assert result["geometryCompatible"]
    assert not result["productionGeminiEligible"] and not result["geminiCalled"]
    assert not result["semanticTransferApproved"]
    assert len(result["armPlans"])==3
    plan=json.loads((out/"measured_reference.json").read_text())
    layer=plan["composition"]["layers"][0]
    assert layer["paddingPx"]==26 and layer["enterSeconds"]==0
    assert layer["widthFraction"]==1520/1920
    assert layer["startAt"]==(120-46)/30

def test_incompatible_tall_source_refuses_wide_reference(tmp_path,track):
    s,m=evidence(tmp_path,rect={"x":655,"y":368.796875,"width":299,"height":658.3125},t=2.38)
    result=generate_ablation_plans(s,m,track,tmp_path/"plans")
    assert not result["geometryCompatible"]
    assert len(result["armPlans"])==2
    assert not (tmp_path/"plans/measured_reference.json").exists()

def test_no_fabricated_outcome_is_admitted(tmp_path,track):
    s,m=evidence(tmp_path,rect={"x":521,"y":348.5,"width":1118,"height":316},valid=False)
    with pytest.raises(ValueError,match="outcome evidence"):
        generate_ablation_plans(s,m,track,tmp_path/"plans")

def test_result_must_exist_before_measured_46_frame_hold(tmp_path,track):
    s,m=evidence(tmp_path,rect={"x":521,"y":348.5,"width":1118,"height":316},t=2.9)
    with pytest.raises(ValueError,match="too late"):
        generate_ablation_plans(s,m,track,tmp_path/"plans")

def test_false_gemini_eligibility_is_refused(tmp_path,track):
    d=json.loads(track.read_text());d["approvedForGemini"]=True;track.write_text(json.dumps(d))
    s,m=evidence(tmp_path,rect={"x":521,"y":348.5,"width":1118,"height":316})
    with pytest.raises(ValueError,match="research-only"):
        generate_ablation_plans(s,m,track,tmp_path/"plans")
