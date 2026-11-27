import json
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pytest
from backend.customer_detail import select_component,observed_components
from scripts.customer_craft_contract import detail_region

def rect(x,y,w,h):return dict(x=x,y=y,width=w,height=h)

def test_component_is_complete_named_and_changed():
    box=rect(0,0,900,600)
    good={"label":"Chart","rect":rect(100,100,250,200)}
    before=np.zeros((600,900,3),np.uint8)
    after=before.copy();after[100:300,100:350]=180
    d=select_component(before,after,[good],[good],box)
    assert d["label"]=="Chart" and d["changedFraction"]==1
    assert select_component(before,before,[good],[good],box) is None
    assert select_component(before,after,[good],[{**good,"label":"Another"}],box) is None
    assert select_component(before,after,[good],[{**good,"rect":rect(650,100,400,200)}],box) is None
    assert select_component(before,after,[good],[{**good,"rect":rect(400,300,250,200)}],box) is None

def test_dom_excludes_clipped_sensitive_and_occluded_components():
    from playwright.sync_api import sync_playwright
    from backend.product_explorer import CHROME
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path=CHROME,headless=True,args=["--no-sandbox"])
        page=b.new_page(viewport={"width":900,"height":600})
        page.set_content("""
        <style>article{position:absolute;width:240px;height:180px;background:#ddd;border-radius:14px}h2{font-size:16px;margin:20px}</style>
        <article style="left:40px;top:40px"><h2>Chart</h2></article>
        <article style="left:620px;top:510px"><h2>Clipped</h2></article>
        <article data-private style="left:330px;top:40px"><h2>Private</h2></article>
        <article style="left:40px;top:260px"><h2>Covered</h2></article>
        <div style="position:absolute;left:40px;top:260px;width:240px;height:180px;background:white"></div>
        """)
        rows=observed_components(page,rect(0,0,900,600))
        assert [r["label"] for r in rows]==["Chart"]
        b.close()

def test_component_detail_preserves_initial_complete_result(tmp_path,monkeypatch):
    import sys
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]/"scripts"))
    from source_event_director import direction
    from spatial_studio_stage import load_studio_stage
    from customer_craft_contract import verify_plan
    proof={"schema":"sauce-decoded-component-v1","changedFraction":.25,"retainedFraction":.96,"settledDifference":.01}
    broad=rect(544,140,3248,1972);component=rect(700,300,1000,850)
    events=[{"kind":"click","start":t,"end":t+.1,"t":t+1.2,"evidence":"fixture",
        "targetRect":rect(850,600,100,60),"resultRect":broad,
        "componentRect":component,"componentProof":proof} for t in (2.,10.,20.)]
    m={"cursorless":True,"duration":30.,"events":events,"pointer_samples":[{"t":i*.1,"x":900,"y":630} for i in range(300)]}
    assert detail_region(events[0],(3840,2160))==(component,.6)
    assert detail_region({**events[0],"componentProof":{}},(3840,2160))==(broad,0.)
    source=tmp_path/"source.mp4";source.write_bytes(b"fixture")
    manifest=tmp_path/"manifest.json";manifest.write_text(json.dumps(m))
    packet={"actualCapture":{"durationSeconds":30.,"resolution":[3840,2160],"nativeFps":60,
        "pointerProvenance":{"recordedPointerTrackAvailable":True}}}
    with patch("film_director_capabilities.build_contract",return_value=packet):
        plan=direction(source,manifest,1)
    stage=load_studio_stage(plan["studioStage"],m,source,(3840,2160),(1920,1080),30.,60)
    ptr=np.asarray([[p["t"],p["x"],p["y"]] for p in m["pointer_samples"]])
    q=verify_plan(plan,m,stage,ptr,60,1800)
    assert q["minimumResultVisible"]==1 and q["heroMinimumResultVisible"]==1
    assert max(k.view_scale for k in stage.camera)>=1.2
    assert stage.detail_shots[0][1]>=events[1]["t"]+.6-1e-7
    # A real component cannot authorize a pre-result crop.
    bad=json.loads(json.dumps(plan["studioStage"]))
    next(k for k in bad["camera"] if k["viewScale"]>1.075)["startAt"]=events[1]["t"]
    with pytest.raises(ValueError):load_studio_stage(bad,m,source,(3840,2160),(1920,1080),30.,60)

def test_wide_hero_and_supporting_component_get_native_time(tmp_path,monkeypatch):
    """Regression fixture uses Nov 27 measured geometry/latency, not real footage."""
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]/"scripts"))
    from source_event_director import direction
    from spatial_studio_stage import load_studio_stage
    from customer_craft_contract import verify_plan
    from scripts.customer_editorial import fit_duration,schedule
    ids=["hero","support"]
    requested={"backdrop":"muted","duration_seconds":13,"beats":[
        {"action_id":"hero","framing":"wide","pace":"quick","purpose":"Establish complete result"},
        {"action_id":"support","framing":"detail","pace":"readable","purpose":"Read actual changed chart"}]}
    compiled=fit_duration(requested,ids,"hero")
    assert compiled["duration_seconds"]==16
    starts=schedule(compiled,ids,"hero")
    proof={"schema":"sauce-decoded-component-v1","changedFraction":.06799,"retainedFraction":1.,"settledDifference":0.}
    broad=rect(544,140,3248,1972)
    events=[{"kind":"click","start":t+2.2,"end":t+2.3,"t":t+3.93,"evidence":"fixture",
        "targetRect":rect(850,600,100,60),"resultRect":broad} for t in starts]
    events[1].update(componentRect=rect(632,228,748,1220),componentProof=proof)
    duration=compiled["duration_seconds"]
    m={"cursorless":True,"duration":float(duration),"events":events,
       "pointer_samples":[{"t":i*.1,"x":900,"y":630} for i in range(duration*10)]}
    source=tmp_path/"source.mp4";source.write_bytes(b"fixture")
    manifest=tmp_path/"manifest.json";manifest.write_text(json.dumps(m))
    packet={"actualCapture":{"durationSeconds":float(duration),"resolution":[3840,2160],"nativeFps":60,
        "pointerProvenance":{"recordedPointerTrackAvailable":True}}}
    with patch("film_director_capabilities.build_contract",return_value=packet):
        plan=direction(source,manifest,0,{"ids":ids,"hero":"hero","editorial":compiled})
    stage=load_studio_stage(plan["studioStage"],m,source,(3840,2160),(1920,1080),float(duration),60)
    ptr=np.asarray([[p["t"],p["x"],p["y"]] for p in m["pointer_samples"]])
    metrics=verify_plan(plan,m,stage,ptr,60,duration*60)
    assert metrics["detailEventIndices"]==[1] and metrics["heroDetailFrames"]>0
    assert metrics["minimumResultVisible"]==metrics["heroMinimumResultVisible"]==1.
    assert max(k.view_scale for k in stage.camera)>=1.2
    assert stage.detail_shots[0][1]>=events[1]["t"]+.6-1e-7
