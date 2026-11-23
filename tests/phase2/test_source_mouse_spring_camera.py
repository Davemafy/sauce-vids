"""Reference-measured, hash-bound camera follow and physical dolly regressions."""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from source_mouse_spring_camera import (build_follow,reference_ease_out,
                                         _critically_damped_step)


def sample_capture():
    return {
        "capture_rect":{"width":320,"height":180},
        "pointer_samples":[
            {"t":0.10,"x":160,"y":90},
            {"t":0.40,"x":160,"y":90},
            {"t":0.52,"x":174,"y":82},
            {"t":0.64,"x":207,"y":52},
            {"t":0.76,"x":264,"y":28},
            {"t":0.82,"x":278,"y":22},
            {"t":1.09,"x":274,"y":22},
            {"t":1.53,"x":270,"y":24},
            {"t":2.0,"x":160,"y":90},
        ],
        "events":[{"kind":"click","start":.90,"end":1.01,"t":1.30,
                   "evidence":"Recorded click and verified source pixel change"}],
    }


def opts():
    return {"mode":"source-cursor-spring","eventIndices":[0],
            "responseSeconds":.37,"strength":.22,"deadzone":.09,
            "maxOffset":.055,"beforeSeconds":.65,"afterSeconds":.60}


def test_reference_exponential_zoom_arrives_fast_and_settles_quietly():
    values=[reference_ease_out(i/100) for i in range(101)]
    assert values[0]==0. and values[-1]==1.
    assert all(a<=b for a,b in zip(values,values[1:]))
    assert reference_ease_out(.3)>.55
    assert reference_ease_out(.75)>.97
    assert reference_ease_out(-1)==0.
    assert reference_ease_out(5)==1.


def test_exact_critically_damped_follow_has_no_idle_wiggle_or_overshoot():
    x=np.zeros(2);v=np.zeros(2);target=np.array([.055,-.05])
    history=[]
    for _ in range(120):
        x,v=_critically_damped_step(x,v,target,12.,1/60)
        history.append(x.copy())
    assert np.max(np.abs(np.stack(history)),axis=0)[0]<=.055001
    assert all(row[0]>=0 and row[1]<=0 for row in history)
    np.testing.assert_allclose(history[-1],target,rtol=0,atol=1e-7)
    # Same physical motion at 30fps and 60fps for an unchanging target.
    a=np.zeros(2);b=np.zeros(2);av=np.zeros(2);bv=np.zeros(2)
    for _ in range(30):a,av=_critically_damped_step(a,av,target,12.,1/30)
    for _ in range(60):b,bv=_critically_damped_step(b,bv,target,12.,1/60)
    np.testing.assert_allclose(a,b,rtol=0,atol=1e-12)


def test_mouse_follow_is_causal_event_gated_and_source_pinned():
    m=sample_capture();settings=opts()
    a=build_follow(m,(320,180),3.,60,settings)
    b=build_follow(m,(320,180),3.,60,settings)
    assert a.points==b.points
    assert a.source_sample_count==9
    assert a.offset(0)==(0.,0.)
    assert a.offset(.20)==(0.,0.)
    x,y=a.offset(1.2)
    assert -.055<=x<-.012 and .005<y<=.055,(x,y)
    assert a.offset(2.5)[0]==pytest.approx(0.,abs=.003)
    for t in np.linspace(0,3,181):
        x,y=a.offset(float(t))
        assert math.isfinite(x) and math.isfinite(y)
        assert max(abs(x),abs(y))<=.05500001
    # Smoothly inertial response without a jump when cursor direction changes.
    diffs=np.abs(np.diff(np.array(a.points),axis=0))
    assert float(diffs.max())<.012


@pytest.mark.parametrize("corruption",[
    lambda m:m.update(pointer_samples=[]),
    lambda m:m["pointer_samples"][4].update(x=321),
    lambda m:m["pointer_samples"][4].update(t=.21),
    lambda m:m["events"][0].update(evidence=""),
    lambda m:m["capture_rect"].update(width=999),
    lambda m:m["events"][0].update(t=.6),
])
def test_invalid_recorded_evidence_never_generates_fake_follow(corruption):
    m=sample_capture();corruption(m)
    with pytest.raises(ValueError):
        build_follow(m,(320,180),3,60,opts())


@pytest.mark.parametrize("patch",[
    {"mode":"generated-motion"},
    {"eventIndices":[4]},
    {"eventIndices":[0,0]},
    {"strength":9.},
    {"maxOffset":.5},
    {"responseSeconds":0.},
    {"deadzone":-.1},
    {"randomWallpaper":"neon"},
])
def test_untrusted_plan_cannot_override_source_timing_or_camera_bounds(patch):
    settings={**opts(),**patch}
    with pytest.raises(ValueError):
        build_follow(sample_capture(),(320,180),3.,60,settings)


def test_director_advertises_reference_follow_only_with_real_pointer_provenance():
    from film_director_capabilities import source_pointer_capabilities
    full=source_pointer_capabilities(sample_capture(),(320,180))
    assert full['recordedPointerTrackAvailable']
    assert full['sourceCursorSpringAvailable']
    short=sample_capture()
    short['pointer_samples']=short['pointer_samples'][:2]
    limited=source_pointer_capabilities(short,(320,180))
    assert limited['recordedPointerTrackAvailable']
    assert not limited['sourceCursorSpringAvailable']


def test_versioned_film_plan_schema_supports_bounded_source_mouse_camera():
    spec=json.loads((Path(__file__).resolve().parents[2]
                    / 'schemas/sauce-film-plan-v1.schema.json').read_text())
    studio=spec['properties']['studioStage']['properties']
    assert studio['camera']['items']['properties']['viewScale']['maximum']==1.8
    assert studio['motion']['properties']['profile']['enum']==[
        'classic','cinematic','reference-spring']
    follow=studio['motion']['properties']['follow']
    assert follow['additionalProperties'] is False
    assert follow['properties']['mode']['const']=='source-cursor-spring'
    assert follow['properties']['eventIndices']['uniqueItems'] is True
    assert follow['properties']['maxOffset']['maximum']<=.075
