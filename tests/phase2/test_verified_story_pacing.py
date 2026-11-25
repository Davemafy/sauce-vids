import sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from verified_story_pacing import plan_ranges,remap,stable_runs

def test_stable_runs_preserve_genuine_change():
    a=np.zeros((120,4,4,3),np.uint8);a[60:]=100
    assert stable_runs(a,0,120)==[(0,60),(60,120)]

def test_story_pacing_retains_all_verified_actions():
    a=np.zeros((1800,4,4,3),np.uint8)
    es=[]
    for i,t in enumerate((3.,11.,20.)):
        a[int((t+1)*60):]=50*(i+1)
        es.append({'start':t,'end':t+.1,'t':t+1,'evidence':'observed'})
    points=[{'t':0.,'x':0.,'y':0.},{'t':1.7,'x':20.,'y':0.},{'t':10.,'x':40.,'y':0.},{'t':19.,'x':60.,'y':0.}]
    ranges=plan_ranges(a,es,points)
    assert sum(b-a for a,b in ranges)<1800
    for e in es:assert remap(e['t'],ranges)-remap(e['start'],ranges)==pytest.approx(1.)
    with pytest.raises(ValueError):remap(0.,ranges)

def test_ready_frame_cannot_remove_recorded_approach():
    a=np.zeros((1800,4,4,3),np.uint8)
    a[60:]=40
    es=[{'start':t,'end':t+.1,'t':t+1,'evidence':'real'} for t in (3.,11.,20.)]
    points=[{'t':0.,'x':0.,'y':0.},{'t':1.7,'x':20.,'y':0.},{'t':10.,'x':40.,'y':0.},{'t':19.,'x':60.,'y':0.}]
    assert plan_ranges(a,es,points,ready_frame=78)[0][0]==78
    with pytest.raises(ValueError):plan_ranges(a,es,points,ready_frame=105)


def test_stationary_approach_gap_requires_real_stationary_pointer_and_pixels():
    from verified_story_pacing import stationary_approach_gaps
    a=np.zeros((600,4,4,3),np.uint8)
    events=[{'start':3.}]
    p=[{'t':.5,'x':10.,'y':10.},{'t':1.5,'x':10.,'y':10.}]
    assert stationary_approach_gaps(a,events,p,a)==[(38,82)]
    source=a.copy();source[60:]=100
    assert stationary_approach_gaps(a,events,p,source)==[]
    p[-1]['x']=40.
    assert stationary_approach_gaps(a,events,p,a)==[]
