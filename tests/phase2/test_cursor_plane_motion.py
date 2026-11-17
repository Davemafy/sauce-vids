"""H0/H60 cursor continuity independent of cosmetic stage shaders."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))

from cursor_plane_motion import CursorPlaneGlide
from spatial_parallax import window_homography,map_pointer


def _mix(a,b,u):
    return (a[0]+(b[0]-a[0])*u,a[1]+(b[1]-a[1])*u)


def test_brimble_modal_entry_has_no_discontinuous_depth_snap():
    """The observed approach crosses x=440 at ~1.617s; old H60 jumped 16px."""
    window=(220,124,1480,832)
    h0=window_homography(*window,.3,-.4,focal=1200,z=0)
    h60=window_homography(*window,.3,-.4,focal=1200,z=60)
    # Verified recorded-source CSS values sampled around the H60 boundary.
    points=[(1.550,380.0,404.1),(1.567,396.1,411.9),
            (1.583,412.7,419.2),(1.600,429.5,425.9),
            (1.617,446.9,432.0),(1.633,465.1,437.5),
            (1.650,484.4,442.4),(1.667,504.1,446.6),
            (1.683,523.6,450.1),(1.700,541.9,452.9),
            (1.717,558.3,455.1),(1.733,572.3,456.8),
            (1.750,583.7,458.1),(1.767,592.6,459.0)]
    glide=CursorPlaneGlide()
    plain=[]
    new=[]
    mixes=[]
    for t,x,y in points:
        # x=640 and y=360 is the unchanged modal camera focus.
        px=220+740+(x-640)*1.31*1480/1280
        py=124+416+(y-360)*1.31*832/720
        back=map_pointer(h0,px,py)
        front=map_pointer(h60,px,py)
        foreground=x>=440
        mix=glide.sample(t,foreground)
        plain.append(front if foreground else back)
        new.append(_mix(back,front,mix))
        mixes.append(mix)
    # No instantaneous 0 -> 1 weight when the pointer enters the modal.
    assert mixes[:4]==[0.]*4
    assert mixes[4]==0.
    assert 0<mixes[5]<mixes[7]<mixes[10]<1.
    assert mixes[-1]==pytest.approx(1.,abs=.02)
    old_entry=math.dist(plain[3],plain[4])
    new_entry=math.dist(new[3],new[4])
    old_before=math.dist(plain[2],plain[3])
    new_before=math.dist(new[2],new[3])
    # The hard plane cut made the pointer decelerate abruptly at the edge.
    assert abs(new_entry-new_before)<abs(old_entry-old_before)*.55, (
        old_before,old_entry,new_before,new_entry)
    assert new_entry>old_entry
    assert new[-1]==pytest.approx(plain[-1],abs=.5)


def test_reverse_transition_interpolates_and_returns_to_background():
    sample=CursorPlaneGlide()
    out=[sample.sample(i/60.,False) for i in range(3)]
    out.extend(sample.sample(i/60.,True) for i in range(3,17))
    out.extend(sample.sample(i/60.,False) for i in range(17,32))
    assert out[:4]==[0.,0.,0.,0.]
    assert all(a<=b+1e-10 for a,b in zip(out[3:17],out[4:17]))
    assert out[16]==pytest.approx(1.)
    assert out[17]==pytest.approx(1.)
    assert out[-1]==pytest.approx(0.)
    assert all(0<=v<=1 for v in out)
    assert out==[v for v in out]


def test_beat_cut_resets_depth_without_false_teleport_animation():
    sample=CursorPlaneGlide()
    sample.sample(.50,False)
    sample.sample(.517,True)
    assert sample.sample(.55,True)<1.
    # A 420ms skipped source span is a deliberate editorial shot cut.
    assert sample.sample(.97,True)==1.
    assert sample.sample(.987,False)==1.
    assert sample.sample(1.2,False)==0.
    with pytest.raises(ValueError):
        sample.sample(float("nan"),True)
    with pytest.raises(ValueError):
        sample.sample(-.1,False)


def test_fixed_input_and_clock_are_reproducible():
    sequence=[(i/60.,(8<=i<29)) for i in range(42)]
    one=CursorPlaneGlide()
    two=CursorPlaneGlide()
    assert [one.sample(*p) for p in sequence]==[
           two.sample(*p) for p in sequence]
