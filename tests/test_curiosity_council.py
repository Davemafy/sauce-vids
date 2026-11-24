import json
from unittest.mock import Mock
from urllib.error import HTTPError
from backend.curiosity_council import advise, MODELS, checked
from backend.curious_interactive import investigate
import pytest

ITEMS=[{"id":"a0","label":"Preview","kind":"tab","selector":"#private"},
       {"id":"a1","label":"Theme","kind":"button","session":"secret-session"}]
def response(ids):
    return json.dumps(dict(ids=ids,hypothesis="Show a useful result",
                           falsifier="No result in source",challenge="Does it matter?"))

def test_disabled_and_missing_key_do_not_call(tmp_path,monkeypatch):
    transport=Mock()
    monkeypatch.delenv("SAUCE_DAHL_COUNCIL",raising=False)
    assert advise(ITEMS,tmp_path,phase="interactive",transport=transport)==""
    monkeypatch.setenv("SAUCE_DAHL_COUNCIL","1")
    monkeypatch.delenv("DAHL_API_KEY",raising=False)
    assert advise(ITEMS,tmp_path,phase="interactive",transport=transport)==""
    transport.assert_not_called()

def test_independent_ideas_then_challenge_and_resume(tmp_path,monkeypatch):
    monkeypatch.setenv("SAUCE_DAHL_COUNCIL","1")
    monkeypatch.setenv("DAHL_API_KEY","test-secret-credential")
    calls=[]
    def transport(model,prompt,key):
        assert key=="test-secret-credential"
        assert "#private" not in prompt and "secret-session" not in prompt and key not in prompt
        calls.append((model,prompt))
        return response(["a0" if model==MODELS[0] else "a1"]),{"total_tokens":31}
    suffix=advise(ITEMS,tmp_path,phase="interactive",transport=transport)
    assert [m for m,p in calls]==list(MODELS)
    assert "Show a useful result" not in calls[1][1]
    assert "Show a useful result" in calls[2][1]
    assert "Independently inspect" in suffix
    saved=(tmp_path/"dahl-council.json").read_text()
    assert "test-secret-credential" not in saved
    assert json.loads(saved)["visual_evidence_seen"] is False
    assert advise(ITEMS,tmp_path,phase="interactive",transport=transport)==""
    assert len(calls)==3

def test_invented_id_and_rate_limit_stop(tmp_path,monkeypatch):
    monkeypatch.setenv("SAUCE_DAHL_COUNCIL","1")
    monkeypatch.setenv("DAHL_API_KEY","fake-key")
    with pytest.raises(ValueError):checked(response(["fake"]),{"a0"})
    t=Mock(side_effect=HTTPError("https://example.com",429,"rate",None,None))
    assert advise(ITEMS,tmp_path,phase="picker",transport=t)==""
    assert t.call_count==1
    assert json.loads((tmp_path/"dahl-council.json").read_text())["attempts"][0]["http_status"]==429

def test_gemini_can_reject_every_council_idea(tmp_path,monkeypatch):
    monkeypatch.setenv("SAUCE_DAHL_COUNCIL","1")
    monkeypatch.setenv("DAHL_API_KEY","fake-key")
    monkeypatch.setattr("backend.curiosity_council.request",lambda *args:(response(["a0"]),{}))
    shot=tmp_path/"scan.jpg";shot.write_bytes(b"fixture")
    report={"url":"https://example.com/demo","title":"Demo","screenshot":str(shot),
            "controls":[{"id":"a0","kind":"tab","text":"Preview","selector":"#preview","in_form":False}]}
    conv=Mock();conv.calls=0
    conv.ask.return_value='{"action_ids":[],"reason":"Not meaningful"}'
    probe=Mock()
    result,_=investigate(report["url"],report,tmp_path/"job",Mock(),conversation=conv,probe=probe)
    assert result is None
    probe.assert_not_called()
    assert "TEXT-ONLY challenger" in conv.ask.call_args.args[0]
    assert conv.ask.call_count==1
