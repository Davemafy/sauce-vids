"""Negative tests for bounded film-quality supervisor."""
import importlib.util
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location("quality_preview_supervisor",Path(__file__).resolve().parents[1]/"scripts/quality_preview_supervisor.py")
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)

def report(*codes):
    return {"findings":[{"code":x} for x in codes]}

def manifest(events=None):
    return {"events":events if events is not None else [{"t":3.5,"kind":"click"}],"lead_s":0}

def edl():
    return {"shots":[
        {"label":"open","startFrame":0,"endFrame":180,"camera":[{"f":0,"anchor":"wide","zoom":1.1}]},
        {"label":"second","startFrame":210,"endFrame":420,"camera":[{"f":0,"anchor":"wide","zoom":1.1}]},
        {"label":"third","startFrame":430,"endFrame":650,"camera":[{"f":0,"anchor":"wide","zoom":1.1}]}
    ]}

def test_only_static_opening_authorizes_adjustment():
    assert q.repair_edl(edl(),manifest(),report("LOW_VISUAL_DETAIL")) is None

def test_only_first_idle_source_region_changes():
    original=edl()
    updated=q.repair_edl(original,manifest(),report("STATIC_OPENING_2S"))
    assert updated["shots"][0]["startFrame"]==90
    assert updated["shots"][1:]==original["shots"][1:]
    assert original["shots"][0]["startFrame"]==0

@pytest.mark.parametrize("events",[
    [],[{"t":.5,"kind":"click"}],[{"kind":"click"}],
    [{"t":"one","kind":"click"}]
])
def test_cannot_trim_unobserved_or_real_actions(events):
    assert q.repair_edl(edl(),manifest(events),report("STATIC_OPENING_2S")) is None

def test_moving_camera_cannot_be_retimed():
    e=edl()
    e["shots"][0]["camera"].append({"f":40,"zoom":1.2,"anchor":"wide"})
    assert q.repair_edl(e,manifest(),report("STATIC_OPENING_2S")) is None

def test_short_first_shot_fails_closed():
    e=edl();e["shots"][0]["endFrame"]=42
    assert q.repair_edl(e,manifest(),report("STATIC_OPENING_2S")) is None

def test_missing_source_evidence_is_rejection(tmp_path,monkeypatch):
    import numpy as np
    monkeypatch.setattr(q,"probe",lambda _:{"streams":[{"codec_type":"video","width":1920,"height":1080}],"format":{"duration":"4"}})
    monkeypatch.setattr(q,"frames",lambda *args,**kwargs:np.zeros((40,90,160),dtype=np.int16))
    monkeypatch.setattr(q,"digest",lambda _: "test-hash")
    r=q.analyze(tmp_path/"missing.mp4")
    assert r["verdict"]=="REJECT"
    assert "UNVERIFIED_SOURCE_CLAIM" in {x["code"] for x in r["findings"]}

def test_repair_never_changes_source_or_events():
    m=manifest()
    e=edl()
    old=repr(m),repr(e)
    q.repair_edl(e,m,report("STATIC_OPENING_2S"))
    assert (repr(m),repr(e))==old

def test_fake_provenance_receipt_stops_before_render(tmp_path):
    import json
    video=tmp_path/"film.mp4"
    source=tmp_path/"source.mp4";source.write_bytes(b"genuine bytes unknown")
    man=tmp_path/"manifest.json";man.write_text(json.dumps(manifest()))
    edit=tmp_path/"edit.json";edit.write_text(json.dumps(edl()))
    rec=tmp_path/"receipt.json"
    rec.write_text(json.dumps({"source_path":str(source),"source_sha256":"0"*64,
                               "event_manifest_path":str(man),"event_manifest_sha256":"1"*64}))
    with pytest.raises(ValueError,match="mismatch"):
        q.supervise(video,man,edit,source,tmp_path/"out",rec,render=True)

def test_mismatched_provenance_path_stops(tmp_path):
    import json
    source=tmp_path/"source.mp4";source.write_bytes(b"x")
    man=tmp_path/"manifest.json";man.write_text(json.dumps(manifest()))
    edit=tmp_path/"edit.json";edit.write_text(json.dumps(edl()))
    rec=tmp_path/"receipt.json"
    rec.write_text(json.dumps({"source_path":str(tmp_path/"not-source.mp4"),"source_sha256":q.digest(source),
                               "event_manifest_path":str(man),"event_manifest_sha256":q.digest(man)}))
    with pytest.raises(ValueError,match="path"):
        q.supervise(tmp_path/"missing.mp4",man,edit,source,tmp_path/"out",rec,render=True)

