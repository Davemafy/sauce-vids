import numpy as np
from backend.story_outcome_evidence import localized_color_proof,diverse_candidates

def test_real_distributed_chroma_not_incidental_change():
    a=np.full((1000,1600,3),240,np.uint8)
    b=a.copy()
    for x,y in ((100,100),(700,450),(1300,800)):
        a[y:y+45,x:x+240]=[25,25,25]
        b[y:y+45,x:x+240]=[235,75,25]
    proof=localized_color_proof(a,b,b)
    assert proof and proof["components"]==3 and proof["zones"]==3
    assert localized_color_proof(a,b,a) is None
    tiny=a.copy();tiny[10:15,10:15]=[220,0,0]
    assert localized_color_proof(a,tiny,tiny) is None
    grey=a.copy();grey[100:145,100:340]=[150,150,150]
    assert localized_color_proof(a,grey,grey) is None

def test_sample_is_bounded_and_diverse():
    rows=[{"id":f"{k}{i}","kind":"option","group":k} for k in ("a","b","c") for i in range(10)]
    sample=diverse_candidates(rows,8)
    assert len(sample)==len({x["id"] for x in sample})==8
    assert [x["group"] for x in sample[:3]]==["a","b","c"]
    assert sample[3]["id"]=="a5"

def test_empty_catalog():
    assert diverse_candidates([])==[]

def test_only_witnessed_ids_reach_story_director(tmp_path,monkeypatch):
    import json
    from contextlib import contextmanager
    from unittest.mock import Mock
    import backend.customer_story as s
    rows=[{"id":f"a{i}","kind":"option","label":str(i)} for i in range(4)]
    opened=[]
    @contextmanager
    def browser(url):
        p=Mock();p.url=url;opened.append(p);yield p
    monkeypatch.setattr(s,"browser",browser)
    monkeypatch.setattr(s,"shot",lambda p:b"source")
    monkeypatch.setattr(s,"arr",lambda b:np.zeros((8,8,3),np.uint8))
    monkeypatch.setattr(s,"media",lambda b:b)
    monkeypatch.setattr(s,"panel",lambda p:{"x":0,"y":0,"width":8,"height":8})
    monkeypatch.setattr(s,"apply",lambda *args:None)
    def verify(*args,**kw):
        if len(opened)==2:raise s.WeakVisualOutcome(.001,b"failed")
        return b"changed",{"x":0,"y":0,"width":8,"height":8},.20,1
    monkeypatch.setattr(s,"verify",verify)
    conv=Mock();conv.calls=2
    conv.ask.return_value='{"ids":["a0","a1","a3"],"story":"real","hero_action_id":"a3"}'
    raw,allowed=s.compare_outcomes(rows,{"url":"https://example.com/","picker":"Default"},b"opening",tmp_path,conv,"brief")
    records=json.loads((tmp_path/"outcomes/comparison.json").read_text())
    assert len(opened)==4 and len(allowed)==3
    assert all(r["status"]=="verified" for r in records if r["id"] in {a["id"] for a in allowed})
    failed=next(r for r in records if r["status"]=="weak")["id"]
    assert failed not in {a["id"] for a in allowed}
    assert len(conv.ask.call_args.kwargs["media"])==6
    assert s.validated_selection(json.dumps({"ids":[failed,allowed[0]["id"],allowed[1]["id"]],"story":"bad"}),allowed) is None

def test_model_cannot_spend_all_probes_on_one_of_many_capabilities():
    from backend.story_outcome_evidence import balance_hypotheses
    rows=[{"id":f"{k}{i}","kind":"option","group":k} for k in ("style","theme","radius","font") for i in range(8)]
    result=balance_hypotheses(rows,rows[:8])
    assert len(result)==8
    assert [r["group"] for r in result[:4]]==["style","theme","radius","font"]
    assert sum(r["group"]=="style" for r in result)==2
    assert balance_hypotheses(rows[:8],rows[4:8])==rows[4:8]

def test_provider_failure_is_not_a_source_rejection():
    import pytest
    from unittest.mock import Mock
    from backend.story_outcome_evidence import require_provider_reply
    c=Mock();c.data={"attempts":[{"status":"failed","http_status":503}]}
    with pytest.raises(RuntimeError,match="Gemini returned HTTP 503"):
        require_provider_reply(None,c)
    assert require_provider_reply("{}",c)=="{}"


def test_diverse_director_hypotheses_survive_catalog_order_and_probe_budget():
    from backend.story_outcome_evidence import balance_hypotheses
    # Shape of the 2026-11-25 shadcn Create discovery: 10 independent
    # control groups. The old first-round cap discarded three of six
    # diverse director selections, including later style alternatives.
    groups=["style","base","theme","chart","heading","font","icon","radius","menu","accent"]
    rows=[{"id":f"{k}{i}","kind":"option","group":k}
          for i in range(3) for k in groups]
    by_id={a["id"]:a for a in rows}
    ids=["style1","theme0","radius0","theme2","style2","menu0"]
    requested=[by_id[i] for i in ids]
    result=balance_hypotheses(rows,requested)
    assert len(result)==len({a["id"] for a in result})==8
    assert result[:6]==requested
    assert len({a["group"] for a in result})==6
    assert balance_hypotheses(list(reversed(rows)),requested)[:6]==requested
    full=requested+[by_id["base0"],by_id["chart0"]]
    assert balance_hypotheses(rows,full)==full
