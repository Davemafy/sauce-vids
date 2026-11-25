import json
from unittest.mock import Mock
import pytest
from backend import customer_story_review as r
from backend.customer_story import sha

def setup(tmp,monkeypatch,verdict):
    f=tmp/'master.mp4';s=tmp/'source.mp4';m=tmp/'manifest.json'
    for p in (f,s,m):p.write_bytes(p.name.encode())
    monkeypatch.setattr(r.subprocess,'run',lambda args,**kw: __import__('pathlib').Path(args[-1]).write_bytes(b'video'))
    monkeypatch.setattr('scripts.quality_preview_supervisor.probe',lambda p:{'format':{'duration':'30.0'}})
    conv=Mock();conv.calls=0;conv.ask.return_value=json.dumps({'decision':verdict,'observations':'00:02 static opening'})
    return f,s,m,conv

def test_model_keep_does_not_override_rejection(tmp_path,monkeypatch):
    f,s,m,c=setup(tmp_path,monkeypatch,'keep')
    q={'film_sha256':sha(f),'duration':30,'findings':[{'code':'STATIC_OPENING_2S'}],'verdict':'REJECT'}
    out=tmp_path/'review'
    a=r.review(f,q,s,m,{},out,conversation=c)
    assert a['model_reviewed'] and not a['creative_approved'] and not a['retained_for_human_review']
    assert r.review(f,q,s,m,{},out,conversation=c)==a
    assert c.ask.call_count==1
    f.write_bytes(b'different')
    with pytest.raises(ValueError):r.review(f,q,s,m,{},out,conversation=c)

def test_interrupted_review_never_recharges(tmp_path,monkeypatch):
    f,s,m,c=setup(tmp_path,monkeypatch,'reject');c.calls=1
    q={'film_sha256':sha(f),'duration':30,'findings':[],'verdict':'HUMAN_REVIEW_REQUIRED'}
    a=r.review(f,q,s,m,{},tmp_path/'review',conversation=c)
    assert a['decision']=='interrupted-review'
    c.ask.assert_not_called()

def test_exact_option_handle_fails_closed():
    from backend.customer_story import exact_observed_option,StoryRejected
    scope=Mock();handle=Mock();handle.is_visible.return_value=True
    handle.inner_text.return_value='Observed';handle.evaluate.return_value=True
    scope.evaluate_handle.return_value.as_element.return_value=handle
    assert exact_observed_option(scope,'Observed') is handle
    scope.evaluate_handle.return_value.as_element.return_value=None
    with pytest.raises(StoryRejected):exact_observed_option(scope,'Observed')
    scope.evaluate_handle.return_value.as_element.return_value=handle
    handle.inner_text.return_value='Changed'
    with pytest.raises(StoryRejected):exact_observed_option(scope,'Observed')
    with pytest.raises(StoryRejected):exact_observed_option(scope,'Payment')
