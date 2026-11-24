import sys
from pathlib import Path
import json
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from soundtrack_taste import rank_candidates
from soundtrack_catalog import cue_times

def row(id,mood,score=1.2,license='CC0-1.0'):
    return dict(id=id,mood=mood,license=license,status='candidate',pictureExcerptCandidates=[{'rhythmScore':score}])

def test_preference_role_rotation_and_exploration():
    rows=[row('slipshod','underground house'),row('pantheon','dark phonk'),
          row('electron','atmospheric chillstep'),row('garden','minimal house'),
          row('mc808','ambient progressive house'),row('bad','minimal house',8,'CC-BY-NC')]
    assert rank_candidates(rows,'interaction')[0]['id']=='slipshod'
    assert rank_candidates(rows,'transformation')[0]['id']=='pantheon'
    assert rank_candidates(rows,'showcase')[0]['id']=='electron'
    assert rank_candidates(rows,'interaction',recent=['slipshod'])[0]['id']=='garden'
    assert rank_candidates(rows,'interaction',explore=True)[0]['id']=='garden'
    assert rank_candidates(rows,'transformation',recent=['pantheon'])==[]
    assert rank_candidates(rows,'showcase',explore=True)[0]['id']=='mc808'

def test_showcase_cues_are_not_invented(tmp_path):
    receipt={'samples':48000,'cue_count':1}
    plan={'schema':'sauce-foley-plan-v1','sampleRate':48000,'durationMs':1000,
          'musicGain':0,'cues':[{'sound':'whoosh_soft','outputSample':4800,'outputMs':100}]}
    p=tmp_path/'plan.json';p.write_text(json.dumps(plan))
    assert cue_times(receipt,p)==([.1],[.1])
    with pytest.raises(ValueError):cue_times(receipt)
    plan['cues'][0]['sound']='click_crisp';p.write_text(json.dumps(plan))
    with pytest.raises(ValueError):cue_times(receipt,p)
