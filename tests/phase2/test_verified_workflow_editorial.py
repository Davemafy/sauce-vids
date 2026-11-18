"""Second real-product directing contract: no guessed state or source UI."""
import sys
from pathlib import Path
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts"))
from verified_workflow_editorial import plan_verified_workflow

def events():
    return [
        {"kind":"range_select","t":3.7448,
         "resultRect":{"x":1200,"y":223,"width":193,"height":109}},
        {"kind":"cursor_dwell","t":4.4851,
         "targetRect":{"x":447,"y":48.5,"width":28,"height":28}},
        {"kind":"click","t":4.9487,"semanticGoal":"format actual selected cells",
         "targetRect":{"x":447,"y":49.5,"width":28,"height":28}},
        {"kind":"state_change","t":4.9755,"evidence":"verified cell value change",
         "resultRect":{"x":1200,"y":223,"width":193,"height":109}},
        {"kind":"interaction_complete","t":8.5008},
    ]

def shot(e=None,length=10.35):
    return plan_verified_workflow(events() if e is None else e,
                                  (1600,900),(1920,1080),length,.27)

def test_source_verified_action_and_no_predictive_push():
    p=shot()
    assert p is not None
    assert p.button_start>4.4851
    assert p.button_end<p.click_time
    assert p.result_start>p.result_time
    assert p.result_end<p.release_start
    assert p.sample(0)==p.opening
    assert p.sample(p.button_start-.01)==p.opening
    assert p.sample(p.result_end+.2)==p.outcome
    assert p.outcome.zoom>2.2
    assert p.receipt()['noSyntheticUI']
    assert p.receipt()['sourceTimelinePreserved']
    assert p.receipt()['resultCutSourceFrame']==319

def test_real_pixels_only_and_nonclipping_source_outcome():
    p=shot()
    x,y,w,h=p.result_bounds
    pts=np.array([[x,y,1],[x+w,y+h,1]],np.float64)
    dst=pts@p.matrix(6.2).T
    assert (dst[0]>24).all()
    assert dst[1,0]<1896 and dst[1,1]<1056
    assert (dst[1]-dst[0]).min()>240
    for t in np.linspace(0,10.35,270):
        m=p.matrix(float(t))
        assert np.isfinite(m).all()
        assert m[0,0]==pytest.approx(m[1,1],abs=1e-10)
        assert m[0,1]==m[1,0]==0

def test_missing_or_invalid_source_evidence_fails_closed():
    original=events()
    for miss in ('range_select','cursor_dwell','click','state_change',
                 'interaction_complete'):
        assert shot([e for e in original if e['kind']!=miss]) is None
    wrong=[dict(e) for e in original]
    wrong[3]['evidence']=''
    assert shot(wrong) is None
    wrong=[dict(e) for e in original]
    wrong[3]['resultRect']={"x":float('nan'),"y":223,"width":193,"height":109}
    assert shot(wrong) is None
    wrong=[dict(e) for e in original]
    wrong[2]['semanticGoal']=''
    assert shot(wrong) is None
    wrong=[dict(e) for e in original]
    wrong[2]['t']=4.0
    assert shot(wrong) is None
    assert plan_verified_workflow(original,(1600,900),(1080,1920),10.35,.27) is None
    assert plan_verified_workflow(original,(1600,900),(1920,1080),10.35,100) is None
    assert shot(length=7) is None

def test_no_frame_teleport_except_verified_result_boundary():
    p=shot()
    assert p is not None
    eps=1/60
    starts=[p.button_start,p.button_end,p.result_end,
            p.release_start,p.release_end]
    for t in starts:
        before=p.sample(t-eps/100)
        after=p.sample(t+eps/100)
        assert abs(before.zoom-after.zoom)<.002
        assert abs(before.x-after.x)<4
        assert abs(before.y-after.y)<4
    # One intentional edit decision: cut to the real result then push in.
    a=p.sample(p.result_start-eps/100)
    b=p.sample(p.result_start+eps/100)
    assert abs(a.x-b.x)>300
    assert abs(b.zoom-p.outcome.zoom)>.3
