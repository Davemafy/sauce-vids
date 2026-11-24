from backend.interactive_editorial import response,choose_candidate,run
from unittest.mock import Mock,patch
import json

def test_review_only_allows_bounded_choices():
    assert response('{"decision":"compact","observations":"Slow at 0:01"}',('keep','compact','reject'))['decision']=='compact'
    assert response('{"decision":"arbitrary","observations":"X"}',('keep','compact','reject')) is None
    assert response('{"decision":"keep","observations":""}',('keep','compact','reject')) is None

def test_no_rejected_film_promoted():
    base={'findings':[{'code':'STATIC_OPENING_2S','detail':{'p80_frame_delta':0}}]}
    new={'verdict':'HUMAN_REVIEW_REQUIRED','findings':[]}
    assert choose_candidate(base,new,{'decision':'candidate'})
    assert not choose_candidate(base,{**new,'verdict':'REJECT'},{'decision':'candidate'})
    assert not choose_candidate(base,new,{'decision':'reject'})

def test_recovery_does_not_repeat_calls(tmp_path):
    conv=Mock();conv.calls=1
    make=Mock()
    result=run(tmp_path,tmp_path,tmp_path/'review',make,conversation=conv)
    assert result['decision']=='interrupted-review'
    assert run(tmp_path,tmp_path,tmp_path/'review',make,conversation=conv)==result
    make.assert_not_called()
    conv.ask.assert_not_called()

def test_model_cannot_select_rejected_baseline(tmp_path):
    conv=Mock();conv.calls=0
    conv.ask.return_value='{"decision":"keep","observations":"Readable at 0:01"}'
    with patch('backend.interactive_editorial.evidence',return_value=(tmp_path/'film.mp4',{'verdict':'REJECT','film_sha256':'f'},{})), patch('backend.interactive_editorial._media',return_value={}):
        result=run(tmp_path,tmp_path,tmp_path/'review',Mock(),conversation=conv)
    assert result['model_reviewed']
    assert result['selected'] is None

def test_model_prefers_candidate_but_qa_rejects_both(tmp_path):
    conv=Mock();conv.calls=0
    conv.ask.side_effect=['{"decision":"compact","observations":"Slow opener"}','{"decision":"candidate","observations":"Faster"}']
    base=(tmp_path/'base.mp4',{'verdict':'REJECT','film_sha256':'b','findings':[]},{})
    candidate=(tmp_path/'candidate.mp4',{'verdict':'REJECT','film_sha256':'c','findings':[]},{})
    make=Mock(return_value=(tmp_path,tmp_path))
    with patch('backend.interactive_editorial.evidence',side_effect=[base,candidate]), patch('backend.interactive_editorial._media',return_value={}):
        result=run(tmp_path,tmp_path,tmp_path/'review',make,conversation=conv)
    assert result['revision_rendered']
    assert result['comparison']['decision']=='candidate'
    assert result['selected'] is None
    make.assert_called_once()
