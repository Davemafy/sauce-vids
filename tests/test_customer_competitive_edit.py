import json,pytest
from backend.customer_competitive_edit import score_rows,WEIGHTS
from backend.customer_state_search import chain,enqueue

def test_ranking_is_weighted_and_requires_all_candidates():
    rows=[{'id':i,'rubric':{k:v for k in WEIGHTS}} for i,v in [('A',72),('B',90),('C',65)]]
    assert score_rows(json.dumps({'scores':rows}),['A','B','C'])=={'A':72.,'B':90.,'C':65.}
    rows[1]['rubric']['composition']=101
    with pytest.raises(ValueError):score_rows(json.dumps({'scores':rows}),['A','B','C'])
    with pytest.raises(ValueError):score_rows(json.dumps({'scores':rows[:2]}),['A','B','C'])

def test_third_order_discovery_requires_complete_observed_chain():
    meta={'setup':{'kind':'local-demo-views'}}
    root={'id':'a','group':'filter','label':'Services'};queue=[];witnessed=[root]
    child={'group':'detail','label':'Drill down'};grandchild={'group':'metric','label':'Breakdown'}
    enqueue(queue,[root],witnessed,None,meta,root,catalog_fn=lambda *a:[child]);witnessed.append(queue[0])
    enqueue(queue,[root],witnessed,None,meta,queue[0],catalog_fn=lambda *a:[grandchild])
    assert [x['id'] for x in chain(queue[1],witnessed)]==['a','state0']
    witnessed.append(queue[1]);enqueue(queue,[root],witnessed,None,meta,queue[1],catalog_fn=lambda *a:[{'group':'new','label':'New'}]);assert len(queue)==2
    with pytest.raises(ValueError):chain(queue[1],[root])


def test_three_independent_directions_select_actual_ranked_proxy(tmp_path):
    import cv2,numpy as np
    from pathlib import Path
    from backend.customer_competitive_edit import compete
    from backend.customer_story import sha
    def video(path,fps,shade):
        writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'mp4v'),fps,(160,90));assert writer.isOpened()
        for i in range(13*fps):writer.write(np.full((90,160,3),shade+i%5,np.uint8))
        writer.release()
    source=tmp_path/'source.mp4';video(source,60,10)
    manifest=tmp_path/'manifest.json';manifest.write_text(json.dumps({'events':[{'start':1.,'t':2.,'resultRect':{'x':10,'y':10,'width':80,'height':50}},{'start':6.,'t':7.,'resultRect':{'x':10,'y':10,'width':80,'height':50}}]}))
    base={'backdrop':'cobalt','duration_seconds':13,'beats':[{'action_id':i,'framing':'wide','pace':'readable','purpose':'Observed result'} for i in ['a','b']]}
    plan={'editorial':base,'actions':[{'id':'a'},{'id':'b'}],'hero_action_id':'b','story':'Real product'}
    created=[];calls=[];tones=['cobalt','muted','graphite']
    class Model:
        def __init__(self,d):self.d=d;self.calls=0;self.data={'attempts':[]};created.append(self)
        def ask(self,prompt,**kw):
            self.calls+=1;calls.append(kw);assert kw['max_attempts']==1
            if self.d.name=='critic':
                assert len(kw['media'])==48
                rows=[{'id':i,'rubric':{k:v for k in WEIGHTS}} for i,v in [('A',50),('B',92),('C',60)]]
                return json.dumps({'scores':rows})
            i=int(self.d.parent.name[-1])-1
            beats=[{**b,'framing':'accent'} if i==0 and b['action_id']=='b' else b for b in base['beats']]
            return json.dumps({'accept':True,'reason':'Observed',**base,'backdrop':tones[i],'beats':beats})
    def run(script,*args):
        if script=='source_event_director.py':Path(args[args.index('--out')+1]).write_text(Path(args[args.index('--editorial-intent')+1]).read_text())
        else:
            target=Path(args[args.index('--output')+1]);video(target,12,int(target.parent.name[-1])*40)
    d=tmp_path/'competitive';chosen,count=compete(source,manifest,plan,d,run,factory=Model)
    receipt=json.loads((d/'result.json').read_text());assert count==receipt['calls']==4
    assert receipt['status']=='ranked' and receipt['creative_approved'] is False
    assert chosen['backdrop']==tones[int(receipt['blind_mapping']['B'])-1]
    assert len({c['preview_sha256'] for c in receipt['candidates']})==3
    assert receipt['source_sha256']==sha(source)
    assert all(m.calls==1 for m in created)


def test_fixed_source_long_prose_cannot_reject_valid_camera():
    from backend.customer_competitive_edit import fixed_source_intent
    ids=['a','b'];base={'backdrop':'muted','duration_seconds':16,'beats':[{'action_id':i,'framing':'wide','pace':'readable','purpose':'Verified original'} for i in ids]}
    v={'accept':True,**base,'beats':[{**b,'purpose':'x'*400} for b in base['beats']]}
    assert fixed_source_intent(v,base,ids,'a')==base
    v['beats'][1]['action_id']='invented'
    with pytest.raises(ValueError):fixed_source_intent(v,base,ids,'a')


def test_last_all_wide_candidate_reserves_verified_hero_contrast():
    from backend.customer_competitive_edit import contrast_candidate
    ids=['a','b'];base={'backdrop':'graphite','duration_seconds':16,'beats':[
        {'action_id':i,'framing':'wide','pace':'readable','purpose':'Verified original'} for i in ids]}
    candidate=contrast_candidate(base,[base,base],ids,'b')
    assert candidate['beats'][0]==base['beats'][0]
    assert candidate['beats'][1]=={**base['beats'][1],'framing':'detail'}
    assert candidate['duration_seconds']==16 and candidate['backdrop']=='graphite'
    assert base['beats'][1]['framing']=='wide'
    assert contrast_candidate(base,[base],ids,'b')==base
    assert contrast_candidate(base,[base,candidate],ids,'b')==base
