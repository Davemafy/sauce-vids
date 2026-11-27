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


def test_claude_review_uses_timestamped_master_frames(tmp_path,monkeypatch):
    import cv2
    import numpy as np
    f=tmp_path/'master.mp4';s=tmp_path/'source.mp4';m=tmp_path/'manifest.json'
    writer=cv2.VideoWriter(str(f),cv2.VideoWriter_fourcc(*'mp4v'),10.,(160,90))
    assert writer.isOpened()
    for i in range(40):writer.write(np.full((90,160,3),i,dtype=np.uint8))
    writer.release()
    s.write_bytes(b'source')
    m.write_text(json.dumps({'events':[{'start':.5,'t':1.5}]}))
    c=Mock();c.provider_name='Claude';c.calls=0
    c.ask.return_value=json.dumps({'decision':'keep','observations':'Visible result at 1.5s'})
    q={'film_sha256':sha(f),'duration':4,'findings':[],'verdict':'HUMAN_REVIEW_REQUIRED'}
    a=r.review(f,q,s,m,{'director_provider':'claude'},tmp_path/'review',conversation=c)
    assert a['review_mode']=='timestamped-master-frames'
    assert 0.5 in a['review_frame_times'] and 1.5 in a['review_frame_times']
    assert a['model_reviewed'] and not a['creative_approved']
    args,kwargs=c.ask.call_args
    assert 'cannot hear audio' in args[0]
    assert kwargs['response_schema']['properties']['decision']['enum']==['keep','reject']
    assert all(x['inline_data']['mime_type']=='image/jpeg' for x in kwargs['media'] if 'inline_data' in x)
    assert not (tmp_path/'review'/'review.mp4').exists()


def test_review_sampling_preserves_contact_and_result_with_bounded_coverage():
    events=[{'start':s,'t':s+2.8} for s in (1.,8.,15.,22.)]
    times=r.review_sample_times(30.,{'events':events})
    assert len(times)<=40 and times==sorted(set(times))
    assert times[0]==0 and times[-1]==29.9
    for e in events:
        for t in (e['start']-.2,e['start'],e['t']-.15,e['t'],e['t']+.4,e['t']+1.2):
            assert round(t,3) in times
    assert max(b-a for a,b in zip(times,times[1:]))<=2


def test_review_sampling_rejects_nonfinite_evidence():
    with pytest.raises(ValueError):r.review_sample_times(13.,{'events':[{'start':float('nan'),'t':2}]})
    with pytest.raises(ValueError):r.review_sample_times(float('inf'),{})
