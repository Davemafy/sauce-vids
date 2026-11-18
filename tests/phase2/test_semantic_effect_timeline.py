"""Effect timing, provenance and compatibility regression tests."""
from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from semantic_effect_timeline import (
    SemanticEffectTimeline, VerifiedEffectEvidence, PASS_ORDER
)
from semantic_spatial_handoff import eased

OK=VerifiedEffectEvidence(True,True,True,True)

def sample(t, f, target="dialog", evidence=OK):
    return t.sample(family="semantic-layer-separation",
                    target_id=target,frame=f,evidence=evidence)

def test_exact_old_60fps_curve_and_compositor_order():
    t=SemanticEffectTimeline()
    for frame in range(48,85):
        result=sample(t,frame)
        assert result.progress==eased((frame-48)/18)
        assert result.depth_fraction==result.background_focus_fraction
        assert result.passes==PASS_ORDER
    assert sample(t,90).progress==1

def test_missing_verification_releases_track_and_restores_from_zero():
    t=SemanticEffectTimeline()
    sample(t,20)
    incomplete=VerifiedEffectEvidence(True,True,False,True)
    assert sample(t,25,evidence=incomplete) is None
    result=sample(t,30)
    assert result.progress==0 and result.start_frame==30

def test_unimplemented_families_fail_closed():
    t=SemanticEffectTimeline()
    for family in ("state-metamorphosis","optical-field","velocity-deformation",
                   "kinetic-type","spatial-continuity","xray",""):
        with pytest.raises(ValueError,match="Unimplemented"):
            t.sample(family=family,target_id="dialog",frame=3,evidence=OK)

def test_invalid_identity_mask_evidence_clock():
    t=SemanticEffectTimeline()
    with pytest.raises(ValueError,match="identity"):
        sample(t,1,target="")
    with pytest.raises(ValueError,match="mask"):
        t.sample(family="semantic-layer-separation",target_id="dialog",
                 frame=1,evidence=OK,mask="full-frame")
    with pytest.raises(ValueError,match="verified evidence"):
        sample(t,1,evidence=None)
    sample(t,30)
    with pytest.raises(ValueError,match="backwards"):
        sample(t,29)

def test_30fps_and_explicit_release_are_exact():
    t=SemanticEffectTimeline(30)
    sample(t,5)
    assert sample(t,14).progress==1
    t.release("dialog")
    assert sample(t,15).progress==0

def test_independent_regions_have_independent_clocks():
    t=SemanticEffectTimeline()
    sample(t,0,target="a")
    sample(t,7,target="b")
    a=sample(t,8,target="a")
    b=sample(t,8,target="b")
    assert a.start_frame==0 and b.start_frame==7
    assert a.progress>b.progress

def test_effect_duration_is_fixed_and_bounded():
    t=SemanticEffectTimeline()
    with pytest.raises(ValueError,match="duration"):
        t.sample(family="semantic-layer-separation",target_id="dialog",
                 frame=1,evidence=OK,duration_ms=2000)
    t.sample(family="semantic-layer-separation",target_id="dialog",
             frame=1,evidence=OK,duration_ms=300)
    with pytest.raises(ValueError,match="retime"):
        t.sample(family="semantic-layer-separation",target_id="dialog",
                 frame=2,evidence=OK,duration_ms=600)
