"""Hero selection, shared QA and real DOM-scoped result regressions."""
import json
from pathlib import Path
from unittest.mock import patch
import pytest
from backend import customer_story as story
from scripts.customer_craft_contract import encoded_verdict,split_findings

def test_editorial_only_is_reviewable_and_unknown_fails_closed():
    codes=["STATIC_OPENING_2S","REPEATED_OR_STATIC_FRAMES","SMALL_FOCAL_CONTENT"]
    report={"findings":[{"code":c} for c in codes]}
    assert encoded_verdict(report)=="HUMAN_REVIEW_REQUIRED"
    assert split_findings(report)=={"technical":[],"editorial":codes,"creativeApproved":False}
    for code in ("TRANSIENT_FRAME_REVERSION","TERMINAL_BROWSER_BLACKOUT",
                 "UNVERIFIED_SOURCE_CLAIM","UNREADABLE_CRITICAL_TEXT_AT_390PX",
                 "WASHED_OUT_FRAMES","LOW_VISUAL_DETAIL","UNKNOWN"):
        assert encoded_verdict({"findings":report["findings"]+[{"code":code}]})=="REJECT"

def test_schema_and_strict_hero_membership():
    catalog=[{"id":f"a{i}","kind":"option","label":str(i)} for i in range(4)]
    raw={"ids":["a0","a1","a2"],"story":"actual story","hero_action_id":"a1"}
    assert story.validated_selection(json.dumps(raw),catalog)["hero_action_id"]=="a1"
    for hero in (None,"","a3","unknown",["a1"],True):
        assert story.validated_selection(json.dumps({**raw,"hero_action_id":hero}),catalog) is None
    schema=story.story_response_schema(catalog)
    assert "hero_action_id" in schema["required"]
    assert schema["properties"]["ids"]["items"]["enum"]==["a0","a1","a2","a3"]
    assert schema["properties"]["hero_action_id"]["enum"]==["a0","a1","a2","a3",""]

def test_hero_hold_is_larger_than_setup_and_cannot_precede_proof(tmp_path,monkeypatch):
    import sys
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]/"scripts"))
    from source_event_director import direction
    ev=[{"start":t,"end":t+.1,"t":t+1.5,"evidence":"verified",
         "kind":"click","targetRect":{"x":300,"y":400,"width":120,"height":60},
         "resultRect":{"x":500,"y":400,"width":2500,"height":1200}} for t in (2.,10.,20.)]
    source=tmp_path/"source.mp4";source.write_bytes(b"fixture")
    manifest=tmp_path/"manifest.json";manifest.write_text(json.dumps({"cursorless":True,"events":ev}))
    packet={"actualCapture":{"durationSeconds":30.,"resolution":[3840,2160],
            "nativeFps":60,"pointerProvenance":{"recordedPointerTrackAvailable":True}}}
    with patch("film_director_capabilities.build_contract",return_value=packet):
        plan=direction(source,manifest,1)
        with pytest.raises(ValueError):direction(source,manifest,3)
    keys=plan["studioStage"]["camera"]
    peaks=[(k,keys[i+1]) for i,k in enumerate(keys) if k["viewScale"]>1]
    assert len(peaks)==3
    assert peaks[0][0]["viewScale"]==peaks[2][0]["viewScale"]==1.035
    assert 1.20<=peaks[1][0]["viewScale"]<=1.62
    assert plan["studioStage"]["motion"]["heroEventIndex"]==1
    holds=[n["startAt"]-k["at"] for k,n in peaks]
    assert holds[1]>=1.0 and holds[1]>max(holds[0],holds[2])
    for i,(k,n) in enumerate(peaks):
        assert k["startAt"]>=ev[i]["t"]
        assert n["at"]<(ev[i+1]["start"] if i+1<len(ev) else 30)

def test_tab_result_uses_selected_sibling_not_largest_unrelated_panel(monkeypatch):
    from playwright.sync_api import sync_playwright
    from backend.product_explorer import CHROME
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=CHROME,headless=True,args=["--no-sandbox"])
        page=browser.new_page(viewport={"width":story.W,"height":story.H})
        page.set_content("""
        <div role="tablist"><button role="tab" aria-selected="true" aria-controls="old">Referrers</button>
        <button role="tab" aria-selected="false" aria-controls="new" onclick="
        this.previousElementSibling.setAttribute('aria-selected','false');this.setAttribute('aria-selected','true');
        document.getElementById('old').hidden=true;document.getElementById('new').hidden=false;">Campaigns</button></div>
        <div role="tabpanel" id="old" style="width:600px;height:400px;background:#eee">Referrers</div>
        <div role="tabpanel" id="new" hidden style="width:600px;height:400px;background:#333;color:white">Campaigns</div>
        <div role="tabpanel" id="unrelated" style="width:1000px;height:500px;background:#aaa">Other chart</div>
        """)
        action={"kind":"tab","label":"Campaigns"}
        old=story.action_panel(page,action)
        assert old["id"]=="old" and old["tab_result_id"]=="new"
        page.get_by_role("tab",name="Campaigns").click()
        assert story.result_panel(page,old)["id"]=="new"
        assert story.intersection(old,story.result_panel(page,old),minimum_fraction=.04)["width"]==600
        page.get_by_role("tab",name="Campaigns").evaluate("e=>e.setAttribute('aria-controls','unrelated')")
        with pytest.raises(story.StoryRejected):story.result_panel(page,old)
        browser.close()

def _hero_manifest(result, pointer=(1300,750), duration=30.):
    # Fixture only: verify all projected frames against independent geometry.
    ev=[{"start":t,"end":t+.1,"t":t+1.5,"evidence":"fixture verified",
         "kind":"click","targetRect":{"x":pointer[0]-40,"y":pointer[1]-25,"width":80,"height":50},
         "resultRect":dict(result)} for t in (2.,10.,22.)]
    return {"cursorless":True,"events":ev,"duration":duration,
            "pointer_samples":[{"t":i*.1,"x":pointer[0],"y":pointer[1]} for i in range(300)]}

@pytest.mark.parametrize("rect,pointer,expected",[
    ({"x":1000,"y":500,"width":1400,"height":800},(1300,750),1.62),
    ({"x":560,"y":392,"width":3202,"height":851},(1100,650),1.289),
    ({"x":0,"y":0,"width":3840,"height":2160},(1100,650),1.065),
    ({"x":40,"y":1100,"width":1050,"height":700},(500,1400),None),
])
def test_localized_geometry_and_all_frame_contract(rect,pointer,expected,tmp_path,monkeypatch):
    import numpy as np
    import sys
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]/"scripts"))
    from source_event_director import direction
    from spatial_studio_stage import load_studio_stage
    from customer_craft_contract import verify_plan
    m=_hero_manifest(rect,pointer)
    source=tmp_path/"fixture.mp4";source.write_bytes(b"fixture")
    manifest=tmp_path/"manifest.json";manifest.write_text(json.dumps(m))
    packet={"actualCapture":{"durationSeconds":30.,"resolution":[3840,2160],
            "nativeFps":60,"pointerProvenance":{"recordedPointerTrackAvailable":True}}}
    with patch("film_director_capabilities.build_contract",return_value=packet):
        plan=direction(source,manifest,1)
    stage=load_studio_stage(plan["studioStage"],m,source,(3840,2160),(1920,1080),30.,60)
    peak=max(k.view_scale for k in stage.camera)
    if expected is not None:assert peak==pytest.approx(expected,abs=.002)
    else:assert 1.20<=peak<=1.62
    ptr=np.asarray([[p["t"],p["x"],p["y"]] for p in m["pointer_samples"]])
    metrics=verify_plan(plan,m,stage,ptr,60,1800)
    assert metrics["minimumResultVisible"]==1.
    assert metrics["maximumQuadSpeedPx"]<=8
    assert metrics["maximumQuadAccelerationPx"]<=1.5
    if peak>1.075:
        assert metrics["heroDetailFrames"]>0 and metrics["heroMinimumResultVisible"]==1.
        assert metrics["heroMinimumPaddingPx"]>=35
        hero_key=next(k for k in stage.camera if k.view_scale>1.075)
        assert stage.hero_backdrop_strength(hero_key.at)==pytest.approx(1.)
        assert stage.hero_backdrop_strength(m["events"][1]["t"]-.1)==0.
        assert stage.hero_backdrop_strength(stage.hero_interval[1]+.1)==0.
        # Same result cannot be framed using an unrelated selected event or
        # before the source clock admits it.
        import copy
        wrong=copy.deepcopy(plan["studioStage"]);wrong["motion"]["heroEventIndex"]=2
        with pytest.raises(ValueError):load_studio_stage(wrong,m,source,(3840,2160),(1920,1080),30.,60)
        wrong=copy.deepcopy(plan["studioStage"])
        next(k for k in wrong["camera"] if k["viewScale"]>1.075)["startAt"]=10.5
        with pytest.raises(ValueError):load_studio_stage(wrong,m,source,(3840,2160),(1920,1080),30.,60)
    else:
        assert metrics["heroDetailFrames"]==0 and stage.hero_detail_index is None
