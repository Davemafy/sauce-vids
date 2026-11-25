import json
from pathlib import Path
from unittest.mock import Mock
import pytest
import backend.customer_story as s

def catalog():
    return [{"id":f"a{i}","kind":"option","group":"Theme","label":str(i)} for i in range(6)]

def response(ids):
    return json.dumps({"ids":ids,"story":"Observed product transformation"})

def test_replan_keeps_safety_and_editorial_call_budget(tmp_path,monkeypatch):
    conv=Mock();conv.calls=2
    conv.ask.side_effect=[response(["a0","a2","a3","a4"]),'{"accept":true}']
    seen=[]
    def probe(plan,out):
        ids=[a["id"] for a in plan["actions"]];seen.append(ids)
        if len(seen)==1:
            (out/"failed-before.png").write_bytes(b"before")
            (out/"failed-after.png").write_bytes(b"after")
            return [],[],{"id":"a1","observedDelta":.01}
        return [{"id":i} for i in ids],[],None
    monkeypatch.setattr(s,"probe_story",probe)
    monkeypatch.setattr(s,"media",lambda b:b)
    result=s.investigate_story(response(["a0","a1","a2","a3"]),catalog(),{},b"opening",tmp_path,conv,"brief")
    assert seen==[["a0","a1","a2","a3"],["a0","a2","a3","a4"]]
    assert conv.ask.call_args_list[0].kwargs["media"]==(b"opening",b"before",b"after")
    assert [c.kwargs["phase"] for c in conv.ask.call_args_list]==["story-replan","story-editorial"]
    assert json.loads((tmp_path/"direction.json").read_text())==result[0]
    assert (tmp_path/"attempt-1/direction.json").is_file()

@pytest.mark.parametrize("reason",["Authentication barrier","Sensitive menu","Unsettled starting state"])
def test_nonvisual_failure_never_replans(tmp_path,monkeypatch,reason):
    conv=Mock();conv.calls=1
    monkeypatch.setattr(s,"probe_story",Mock(side_effect=s.StoryRejected(reason)))
    with pytest.raises(s.StoryRejected,match=reason):
        s.investigate_story(response(["a0","a1","a2","a3"]),catalog(),{},b"",tmp_path,conv,"brief")
    conv.ask.assert_not_called()
    assert not (tmp_path/"direction.json").exists()

def test_budget_preserves_editorial_slot(tmp_path,monkeypatch):
    conv=Mock();conv.calls=3
    monkeypatch.setattr(s,"probe_story",Mock(return_value=([],[],{"id":"a1"})))
    with pytest.raises(s.StoryRejected,match="budget"):
        s.investigate_story(response(["a0","a1","a2","a3"]),catalog(),{},b"",tmp_path,conv,"brief")
    conv.ask.assert_not_called()

def test_excluded_action_is_not_replayed(tmp_path,monkeypatch):
    conv=Mock();conv.calls=1;conv.ask.return_value=response(["a0","a1","a2","a4"])
    def probe(plan,out):
        (out/"failed-before.png").write_bytes(b"before")
        (out/"failed-after.png").write_bytes(b"after")
        return [],[],{"id":"a1"}
    m=Mock(side_effect=probe)
    monkeypatch.setattr(s,"probe_story",m);monkeypatch.setattr(s,"media",lambda b:b)
    with pytest.raises(s.StoryRejected,match="No valid"):
        s.investigate_story(response(["a0","a1","a2","a3"]),catalog(),{},b"",tmp_path,conv,"brief")
    assert m.call_count==1

def test_actual_low_delta_is_distinguished_from_unstable_source(monkeypatch):
    import cv2
    import numpy as np
    box={"x":0,"y":0,"width":s.W,"height":s.H}
    def png(color):
        im=np.full((s.H,s.W,3),color,np.uint8)
        ok,data=cv2.imencode(".png",im)
        assert ok
        return data.tobytes()
    before=png(50);weak=png(54);different=png(200)
    p=Mock()
    monkeypatch.setattr(s,"assert_local",lambda *args:None)
    monkeypatch.setattr(s,"panel",lambda p:box)
    with pytest.raises(s.WeakVisualOutcome) as error:
        s.verify(p,"https://example.com/",before,box,lambda p:weak)
    assert error.value.delta==0 and error.value.after==weak
    after,_,delta,_=s.verify(p,"https://example.com/",before,box,lambda p:different)
    assert delta==1 and after==different
    images=iter([weak,different]*3)
    with pytest.raises(s.StoryRejected,match="did not settle") as error:
        s.verify(p,"https://example.com/",before,box,lambda p:next(images))
    assert not isinstance(error.value,s.WeakVisualOutcome)
