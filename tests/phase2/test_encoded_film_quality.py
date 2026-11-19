"""Source-honest encoded film rejection and bounded repair QA."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from encoded_film_quality import inspect_frames,bounded_review,_content_signature


def plate(value:int=26)->np.ndarray:
    return np.full((180,320,3),value,dtype=np.uint8)


def test_static_opening_rejected_without_any_verified_action():
    movie=[plate(29) for _ in range(155)]
    actual=inspect_frames(movie,60,[])
    assert 'INERT_OPENING' in [r.code for r in actual]
    assert any(r.remedy.startswith('Rebuild opening') for r in actual)


def test_interaction_present_prevents_false_static_opening_rejection():
    movie=[plate(29) for _ in range(155)]
    actual=inspect_frames(movie,60,[44])
    assert 'INERT_OPENING' not in [r.code for r in actual]


def test_smooth_real_motion_not_static_opening():
    frames=[]
    for k in range(155):
        image=plate(12)
        x=min(180,k*2)
        image[:,x:x+105,:]=220
        frames.append(image)
    actual=inspect_frames(frames,60,[])
    assert 'INERT_OPENING' not in [r.code for r in actual]


def test_relative_white_flash_rejected_in_dark_theme():
    frames=[plate(26) for _ in range(180)]
    for k in range(48,57):frames[k]=plate(248)
    defects=inspect_frames(frames,60,[])
    assert 'SOURCE_WASHOUT' in [d.code for d in defects]
    bad=next(d for d in defects if d.code=='SOURCE_WASHOUT')
    assert bad.window[0]>.7 and bad.window[1]<1.0


def test_consistently_white_theme_not_false_washout():
    frames=[plate(247) for _ in range(180)]
    defects=inspect_frames(frames,60,[50])
    assert 'SOURCE_WASHOUT' not in [d.code for d in defects]


def test_abrupt_cut_reported_as_warning_not_false_fabrication():
    frames=[plate(20) for _ in range(90)]+[plate(150) for _ in range(90)]
    defects=inspect_frames(frames,60,[50])
    assert 'ABRUPT_IMAGE_CHANGE' in [d.code for d in defects]


@pytest.mark.parametrize('attempts',[2,3,5])
def test_stop_loss_after_two_attempts(attempts):
    out=bounded_review([],[],used_attempts=attempts)
    assert out=={'status':'stop_human_review','retries_remaining':0,'accepted':False}


def test_reject_unimproved_candidate_preserve_best():
    previous=[{'level':'reject','code':'INERT_OPENING'}]
    current=[{'level':'reject','code':'SOURCE_WASHOUT'}]
    decision=bounded_review(previous,current,used_attempts=0)
    assert decision['status']=='reject_no_verified_improvement'
    assert decision['accepted'] is False


def test_only_objective_clear_video_is_referred_for_human_review():
    prior=[{'level':'reject','code':'INERT_OPENING'}]
    decision=bounded_review(prior,[],used_attempts=1)
    assert decision['status']=='request_human_visual_review'
    assert decision['accepted'] is False


def test_negative_bad_frames_and_bad_history_fail_closed():
    with pytest.raises(ValueError):inspect_frames([],60)
    with pytest.raises(ValueError):inspect_frames([plate() for _ in range(20)],0)
    with pytest.raises(ValueError):inspect_frames([plate() for _ in range(20)]+[np.zeros((40,40,3),np.uint8)])
    with pytest.raises(ValueError):bounded_review([],[],used_attempts=-1)


def test_frame_signature_is_deterministic():
    orig=plate(39)
    a,white=_content_signature(orig)
    b,white2=_content_signature(orig.copy())
    assert np.array_equal(a,b)
    assert white==white2==0
