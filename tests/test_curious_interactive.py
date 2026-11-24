import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock
from backend.curious_interactive import investigate

def test_bounded_evidence_review_rejects_unknown_and_failed_ids():
    with TemporaryDirectory() as tmp:
        p=Path(tmp);shot=p/'scan.jpg';shot.write_bytes(b'fixture')
        report={'url':'https://example.com/demo','title':'Demo','headings':[],'screenshot':str(shot),
                'controls':[{'id':f'a{i}','kind':'tab','text':f'Tab {i}','selector':f'#t{i}','in_form':False} for i in range(5)]}
        conv=Mock();conv.calls=0
        conv.ask.side_effect=['{"action_ids":["fake","a0","a1","a2","a3"]}','{"action_id":"a0","reason":"bad"}']
        tried=[]
        def probe(url,report,cid,path,**kwargs):
            assert kwargs['local_only']
            tried.append(cid);path.mkdir()
            for n in ('before.png','after.png'):(path/n).write_bytes(b'fixture')
            return {'decision':'no_proven_visible_outcome' if cid=='a0' else 'visible_outcome_candidate'}
        def admit(plan,report,proof):
            if proof['decision']!='visible_outcome_candidate':raise ValueError('Rejected')
        result,_=investigate(report['url'],report,p/'loop',admit,conversation=conv,probe=probe)
        assert result is None
        assert tried==['a0','a1','a2']
        assert conv.ask.call_count==2
        assert json.loads((p/'loop/receipt.json').read_text())['selected'] is None

def test_real_admitted_candidate_only():
    with TemporaryDirectory() as tmp:
        p=Path(tmp);shot=p/'scan.jpg';shot.write_bytes(b'fixture')
        r={'url':'https://example.com/demo','headings':[],'screenshot':str(shot),'controls':[
          {'id':'a1','kind':'tab','text':'Preview','selector':'#preview','in_form':False}]}
        conv=Mock();conv.calls=0;conv.ask.side_effect=['{"action_ids":["a1"]}','{"action_id":"a1","reason":"verified"}']
        def probe(url,report,cid,path,**kwargs):
            path.mkdir()
            for n in ('before.png','after.png'):(path/n).write_bytes(b'fixture')
            return {'decision':'visible_outcome_candidate'}
        result,_=investigate(r['url'],r,p/'loop',lambda *args:None,conversation=conv,probe=probe)
        assert result[0]['action_ids']==['a1']
        assert result[1]['decision']=='visible_outcome_candidate'

def test_tab_history_state_is_not_a_new_destination():
    from backend.source_action_preflight import same_local_tab_route
    u='https://example.com/editor'
    assert same_local_tab_route(u,u+'?p=dashboard')
    for bad in ('https://other.com/editor','https://example.com/other',u+'?token=abc',u+'#other','http://example.com/editor'):
        assert not same_local_tab_route(u,bad)

def test_model_array_is_normalized_not_rejected():
    from backend.curious_interactive import hypothesis_ids
    assert hypothesis_ids('[{"action_ids":["a2"]},{"action_ids":["a4","a5"]}]')==['a2','a4','a5']
    assert hypothesis_ids('Here is my answer')==[]
    assert hypothesis_ids('{"action_ids":[null,12,"a1"]}')==['a1']
