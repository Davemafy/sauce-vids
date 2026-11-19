"""Visual-source admission cannot be tricked by mere click metadata."""
import sys
from pathlib import Path
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from story_viability_preflight import measure


def evidence(rect=None, rights='verified_internal_qa'):
    return {
      "source_url":"http://localhost:3000/",
      "rights":rights,
      "action":{"kind":"click","t":1.0,"semanticGoal":"Choose the actual editor transformation",
                "targetRect":{"x":50,"y":80,"width":80,"height":36}},
      "result":{"kind":"state_change","t":1.4,"evidence":"Editor output visibly changed",
                "resultRect":rect or {"x":250,"y":110,"width":900,"height":620}},
    }


def film():
    before=np.full((900,1600,3),230,dtype=np.uint8)
    after=before.copy()
    # High-contrast genuine result area transformed, no fabricated UI by the evaluator.
    after[115:725,255:1145,:]=(24,54,205)
    return before,after


def test_admits_only_to_three_second_creative_review_not_premium():
    before,after=film()
    r=measure(before,after,evidence())
    assert r['decision']=='candidate_first_three_seconds_only'
    assert r['issues']==[]
    assert r['premium_film_approved'] is False
    assert r['changed_fraction_of_frame']>.28
    assert r['result_fraction_of_frame']>.3
    assert r['human_critic_required'] is True


def test_tiny_real_result_is_rejected_even_with_real_click():
    before,after=film()
    rect={"x":1200,"y":750,"width":135,"height":75}
    r=measure(before,after,evidence(rect))
    assert r['decision']=='reject_source_before_video'
    assert 'RESULT_TOO_SMALL_FOR_SHORT_SILENT_FILM' in r['issues']
    assert 'WEAK_VISIBLE_TRANSFORMATION' in r['issues']


def test_large_but_static_result_is_rejected():
    before,_=film()
    after=before.copy()
    after[240:290,490:540,:]=(20,40,200)
    r=measure(before,after,evidence())
    assert r['decision']=='reject_source_before_video'
    assert 'WEAK_VISIBLE_TRANSFORMATION' in r['issues']


def test_rights_fails_even_for_beautiful_pictures():
    before,after=film()
    r=measure(before,after,evidence(rights='unknown'))
    assert 'SOURCE_RIGHTS_NOT_VERIFIED' in r['issues']
    assert r['premium_film_approved'] is False


@pytest.mark.parametrize('change',[
    lambda d:d['action'].update({'t':2.5}),
    lambda d:d['result'].update({'t':float('nan')}),
    lambda d:d['result'].update({'evidence':''}),
    lambda d:d['result'].update({'resultRect':{'x':1,'y':1,'width':-2,'height':55}}),
    lambda d:d.update({'source_url':'file:///private/render'}),
    lambda d:d['action'].update({'kind':'invented_click'}),
])
def test_bad_evidence_fails_closed(change):
    before,after=film();p=evidence();change(p)
    with pytest.raises(ValueError):measure(before,after,p)


def test_no_before_after_same_source_dimensions_fails():
    before,after=film()
    with pytest.raises(ValueError):measure(before,after[:500],evidence())
    with pytest.raises(ValueError):measure(before,after.astype(np.float32),evidence())


def admitted_receipt():
    from story_viability_preflight import validate_preview_admission
    before,after=film()
    p=evidence()
    report=measure(before,after,p)
    report.update(before_sha256='a'*64,after_sha256='b'*64)
    m={'source_url':p['source_url'],'events':[p['action'],p['result']]}
    return report,m,validate_preview_admission


def test_source_bound_preview_allowed_but_not_full_film():
    report,manifest,validator=admitted_receipt()
    validator(report,manifest,180,True)
    for frames in (None,0,181,720):
        with pytest.raises(ValueError,match='three-second'):
            validator(report,manifest,frames,True)
    with pytest.raises(ValueError,match='three-second'):
        validator(report,manifest,180,False)


def test_forged_or_stale_preview_is_rejected():
    report,manifest,validator=admitted_receipt()
    bad={**manifest,'source_url':'https://other.example/'}
    with pytest.raises(ValueError,match='source'):
        validator(report,bad,180,True)
    bad={'source_url':manifest['source_url'],'events':[]}
    with pytest.raises(ValueError,match='source clock'):
        validator(report,bad,180,True)
    bad={**report,'result_rect':[]}
    with pytest.raises(ValueError,match='geometry'):
        validator(bad,manifest,180,True)
    bad={**report,'result_rect':[1,2,3,4]}
    with pytest.raises(ValueError,match='geometry'):
        validator(bad,manifest,180,True)
    bad={**report,'before_sha256':'INVALID'}
    with pytest.raises(ValueError,match='provenance'):
        validator(bad,manifest,180,True)
    bad={**report,'premium_film_approved':True}
    with pytest.raises(ValueError,match='did not permit'):
        validator(bad,manifest,180,True)
