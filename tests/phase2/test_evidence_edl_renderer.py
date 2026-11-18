"""Evidence-backed Sauce shot maps, independent of the private source capture."""
import sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from evidence_edl_renderer import build,pose,camera,quintic

def evidence():
    rect=lambda x,y,w,h: {'x':x,'y':y,'width':w,'height':h}
    ev=[{'kind':'session_start','t':0,'heroRect':rect(300,200,300,100)}]
    for i in range(3):
        ev.append({'kind':'click','t':3+i*5,'semanticGoal':'real action',
                   'targetRect':rect(40,100+i*30,70,30)})
        ev.append({'kind':'state_change','t':3.5+i*5,'evidence':'real UI changed',
                   'resultRect':rect(500,100,600,500),
                   'detailRect':rect(550,250,300,220)})
    return {'cursorless':True,'source_kind':'real open source editor',
            'events':ev,'lead_s':.25,'capture_rect':rect(0,0,1600,900)}

def edl():
    return {'unstableRanges':[[170,180]],
      'shots':[
       {'label':'real result teaser','startFrame':740,'endFrame':830,
        'camera':[{'f':0,'zoom':1.7,'anchor':'detail:2'},
                  {'f':89,'zoom':1.3,'anchor':'result:2'}]},
       {'label':'first action','startFrame':10,'endFrame':160,
        'camera':[{'f':0,'zoom':1.16,'anchor':'wide'}]},
       {'label':'first result','startFrame':190,'endFrame':380,
        'camera':[{'f':0,'zoom':1.2,'anchor':'wide'},
                  {'f':45,'zoom':2.,'anchor':'result:0'}]},
       {'label':'second result','startFrame':400,'endFrame':590,
        'camera':[{'f':0,'zoom':1.2,'anchor':'wide'},
                  {'f':40,'zoom':1.5,'anchor':'result:1'}]}
      ]}

def test_evidence_anchored_shots_keep_original_source_frame_ranges():
    shots,total=build(evidence(),edl(),(1600,900),950)
    assert total==620
    assert [s.out_start for s in shots]==[0,90,240,430]
    assert [(s.start,s.end) for s in shots]==[(740,830),(10,160),(190,380),(400,590)]
    for s in shots:
        for frame in range(0,s.length(),3):
            m=camera(evidence(),s,frame,(1600,900),(1920,1080))
            assert m.shape==(2,3) and np.isfinite(m).all()
            assert m[0,0]==pytest.approx(m[1,1])
            assert m[0,1]==m[1,0]==0

def test_invalid_or_unverified_result_is_rejected():
    manifest=evidence()
    manifest['events'][-1]['evidence']=''
    with pytest.raises(ValueError):
        build(manifest,edl(),(1600,900),950)
    manifest=evidence()
    manifest['cursorless']=False
    with pytest.raises(ValueError):
        build(manifest,edl(),(1600,900),950)
    manifest=evidence()
    manifest['events'][-1]['detailRect']['x']=float('nan')
    with pytest.raises(ValueError):
        build(manifest,edl(),(1600,900),950)

def test_unstable_source_frames_never_enter_an_editorial_shot():
    x=edl()
    x['shots'][1]['endFrame']=175
    with pytest.raises(ValueError,match='corrupt'):
        build(evidence(),x,(1600,900),950)
    x=edl()
    x['shots'][2]['startFrame']=-1
    with pytest.raises(ValueError):
        build(evidence(),x,(1600,900),950)

def test_viewport_intersection_preserves_visible_pixels_and_fails_closed():
    x=evidence()
    first=next(e for e in x['events'] if e.get('kind')=='state_change')
    first['resultRect']={'x':500,'y':430,'width':600,'height':500}
    assert pose(x,'result:0',(1600,900)) == (800,665)
    first['resultRect']={'x':500,'y':700,'width':600,'height':500}
    with pytest.raises(ValueError):
        pose(x,'result:0',(1600,900))

def test_quintic_camera_is_bounded_and_quiet_at_endpoints():
    assert quintic(-50)==0
    assert quintic(0)==0
    assert quintic(1)==1
    assert quintic(50)==1
    assert 0<quintic(.25)<.25
    assert quintic(.5)==pytest.approx(.5)
