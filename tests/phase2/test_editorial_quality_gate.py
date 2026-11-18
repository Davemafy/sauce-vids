"""Automated editorial rejection and bounded source-true recovery tests."""
import json,sys
from pathlib import Path
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from editorial_quality_gate import inspect_editorial,bounded_repair
from evidence_edl_renderer import build

def scenario():
    box=lambda x,y,w,h:dict(x=x,y=y,width=w,height=h)
    events=[]
    for i,(click_t,result_t) in enumerate([(2.0,4.0),(6.5,8.8),(9.4,13.0)]):
        events.append(dict(kind='click',t=click_t,
                           semanticGoal=f'authentic product interaction {i+1}',
                           targetRect=box(20,300,180,50)))
        events.append(dict(kind='state_change',t=result_t,
                           evidence=f'verified DOM outcome {i+1}',
                           resultRect=box(500,150,850,550),
                           detailRect=box(650,240,300,220)))
    m=dict(cursorless=True,source_kind='real Chromium public app',lead_s=.25,
           capture_rect=box(0,0,1600,900),events=events)
    wide=lambda f,z:dict(f=f,zoom=z,anchor='wide')
    result=lambda f,z,i:dict(f=f,zoom=z,anchor=f'result:{i}')
    shots=[
      dict(label='real action 1',startFrame=40,endFrame=184,
           camera=[wide(0,1.1),wide(143,1.1)]),
      dict(label='outcome 1 and action 2',startFrame=259,endFrame=484,
           camera=[wide(0,1.1),result(60,1.7,0),result(147,1.7,0),
                   wide(194,1.12),wide(224,1.12)]),
      dict(label='outcome 2 and action 3',startFrame=534,endFrame=733,
           camera=[wide(0,1.1),result(45,1.40,1),result(150,1.40,1),
                   wide(175,1.1),wide(198,1.1)]),
      dict(label='actual outcome 3',startFrame=780,endFrame=1050,
           camera=[wide(0,1.1),result(55,1.3,2),result(269,1.3,2)])
    ]
    return m,dict(shots=shots,unstableRanges=[[185,258],[484,533],[733,778]])

def test_good_action_first_edit_passes_without_repair():
    m,e=scenario()
    assert inspect_editorial(m,e)==[]
    fixed,rep,issues=bounded_repair(m,e)
    assert fixed==e and not rep and not issues
    shots,frames=build(m,e,(1600,900),1110)
    assert frames==838 and len(shots)==4

def test_unsafe_future_teaser_is_rejected_then_dropped_without_invention():
    m,e=scenario()
    preview={'label':'future outcome teaser','startFrame':846,'endFrame':925,
             'camera':[{'f':0,'zoom':2.55,'anchor':'detail:2'},
                       {'f':78,'zoom':2.55,'anchor':'detail:2'}]}
    e['shots'].insert(0,preview)
    codes={f['code'] for f in inspect_editorial(m,e) if f['level']=='reject'}
    assert codes=={'NONCHRONOLOGICAL_OPENER','NO_ESTABLISHING_SHOT'}
    fixed,rep,issues=bounded_repair(m,e)
    assert [s['startFrame'] for s in fixed['shots']]==[40,259,534,780]
    assert rep[0]['removedSourceFrames']==[846,925]
    assert issues==[]
    assert build(m,fixed,(1600,900),1110)[1]==838
    assert e['shots'][0]==preview # no input mutation

def test_no_repair_if_remaining_cut_too_short_or_not_verified():
    m,e=scenario()
    e['shots']=[dict(label='teaser',startFrame=980,endFrame=1050,
                     camera=[{'f':0,'zoom':2.9,'anchor':'result:2'}])] + e['shots'][:2]
    fixed,rep,issues=bounded_repair(m,e)
    assert not rep and fixed==e
    assert any(f['code']=='NONCHRONOLOGICAL_OPENER' for f in issues)

def test_falsely_anticipated_result_camera_rejected():
    m,e=scenario()
    e['shots'][1]['camera'][0]['anchor']='result:2'
    codes={x['code'] for x in inspect_editorial(m,e)}
    assert 'UNOBSERVED_CAMERA_TARGET' in codes

def test_short_final_hold_warns_but_truthful_data_not_rejected():
    m,e=scenario()
    e['shots'][-1]['camera']=[{'f':0,'zoom':1.1,'anchor':'wide'},
                             {'f':249,'zoom':1.3,'anchor':'result:2'},
                             {'f':269,'zoom':1.3,'anchor':'result:2'}]
    findings=inspect_editorial(m,e)
    assert any(f['code']=='NO_FINAL_READING_HOLD' and f['level']=='warn' for f in findings)

def test_genuine_clicks_required():
    m,e=scenario()
    m['events']=[v for v in m['events'] if v['kind']!='click']
    assert any(x['code']=='NO_DEMONSTRATED_WORKFLOW' for x in inspect_editorial(m,e))

def test_no_auto_repair_when_output_contains_one_invalid_future_anchor():
    m,e=scenario()
    e['shots'][-1]['camera'][0]['anchor']='result:2'
    fixed,_,issues=bounded_repair(m,e)
    assert fixed==e
    assert any(f['code']=='UNOBSERVED_CAMERA_TARGET' for f in issues)

def test_engine_cli_uses_preflight_only_as_opt_in():
    s=(Path(__file__).resolve().parents[2]/'scripts/evidence_edl_renderer.py').read_text()
    assert '--quality-gate' in s and '--bounded-repair' in s
    assert 'if quality_gate or bounded_repair' in s
    assert 'creativeApproval' in s

def test_overview_group_rejects_crop_that_hides_real_metric_cards():
    m,e=scenario()
    state=[v for v in m['events'] if v['kind']=='state_change'][-1]
    state['summaryRects']=[
        dict(x=300.,y=300.,width=260.,height=100.),
        dict(x=620.,y=300.,width=260.,height=100.),
        dict(x=940.,y=300.,width=260.,height=100.)]
    e['shots'][-1]['camera']=[dict(f=0,zoom=1.1,anchor='wide'),
                            dict(f=52,zoom=1.15,anchor='overview:2'),
                            dict(f=269,zoom=1.15,anchor='overview:2')]
    assert inspect_editorial(m,e)==[]
    e['shots'][-1]['camera'][-2]['zoom']=2.8
    e['shots'][-1]['camera'][-1]['zoom']=2.8
    assert any(x['code']=='CLIPPED_VERIFIED_SUMMARY_GROUP'
               for x in inspect_editorial(m,e))

def test_missing_evidence_does_not_shift_receipt_anchor_indices():
    m,e=scenario()
    changes=[v for v in m['events'] if v.get('kind')=='state_change']
    changes[1]['evidence']=''
    assert any(x['code']=='UNOBSERVED_CAMERA_TARGET'
               for x in inspect_editorial(m,e))
