"""One-frame cursor repair: retain the preferred original pointer motion."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))

from cursor_plane_motion import CursorPlaneSeamRepair
from spatial_parallax import window_homography,map_pointer


def test_brimble_hit_crossing_repairs_only_one_frame():
    # Observed Brimble source pointer coordinates across H0/H60 dialog edge.
    source=[(1.550,380.0,404.1),(1.567,396.1,411.9),
            (1.583,412.7,419.2),(1.600,429.5,425.9),
            (1.617,446.9,432.0),(1.633,465.1,437.5),
            (1.650,484.4,442.4),(1.667,504.1,446.6),
            (1.683,523.6,450.1),(1.700,541.9,452.9)]
    h0=window_homography(220,124,1480,832,.3,-.4,focal=1200,z=0)
    h60=window_homography(220,124,1480,832,.3,-.4,focal=1200,z=60)
    seam=CursorPlaneSeamRepair()
    changed=[]
    previous=[]
    corrected=[]
    for i,(t,x,y) in enumerate(source):
        sx=220+740+(x-640)*1.31*1480/1280
        sy=124+416+(y-360)*1.31*832/720
        back=map_pointer(h0,sx,sy)
        front=map_pointer(h60,sx,sy)
        inside=x>=440
        original=front if inside else back
        strength=seam.sample(t,inside)
        newer=(back[0]+(front[0]-back[0])*strength,
               back[1]+(front[1]-back[1])*strength)
        if math.dist(original,newer)>1e-9:
            changed.append(i)
        previous.append(original)
        corrected.append(newer)

    # The previous rejected 140ms glide altered 8+ frames and lagged behind
    # the real cursor; this repair affects exactly ONE entry frame.
    assert changed==[4]
    assert math.dist(corrected[3],corrected[4])>math.dist(previous[3],previous[4])
    assert math.dist(corrected[4],corrected[5])<math.dist(previous[4],previous[5])
    assert corrected[:4]==previous[:4]
    assert corrected[5:]==previous[5:]


def test_departure_is_one_frame_only_and_no_lag():
    sample=CursorPlaneSeamRepair()
    result=[sample.sample(i/60,False) for i in range(3)]
    result.extend(sample.sample(i/60,True) for i in range(3,12))
    result.extend(sample.sample(i/60,False) for i in range(12,20))
    assert result==([0.]*3+[.5]+[1.]*8+[.5]+[0.]*7)


def test_true_click_uses_exact_target_even_on_crossing():
    sample=CursorPlaneSeamRepair()
    assert sample.sample(1.0,False)==0.
    assert sample.sample(1+1/60,True,force_exact=True)==1.
    assert sample.sample(1+2/60,True)==1.


def test_cut_reset_and_determinism():
    input_seq=[(i/60,8<=i<30) for i in range(40)]
    a,b=CursorPlaneSeamRepair(),CursorPlaneSeamRepair()
    assert [a.sample(*p) for p in input_seq]==[b.sample(*p) for p in input_seq]
    c=CursorPlaneSeamRepair()
    c.sample(.50,False)
    assert c.sample(.517,True)==.5
    assert c.sample(.97,True)==1.
    assert c.sample(1.25,False)==0.  # a distinct shot cut
    with pytest.raises(ValueError):
        c.sample(float('nan'),False)
    with pytest.raises(ValueError):
        c.sample(-1,True)
