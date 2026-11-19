"""Verified click/audio EDL map stays locked to video frames at 48k/60."""
import copy
import hashlib
import sys
import wave
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from verified_edit_audio import actual_cues,synthesize,SAMPLES_PER_FRAME

SOURCE_HASH='ab'*32

def source_manifest():
    return {
        'cursorless':True,'source_sha256':SOURCE_HASH,'lead_s':.25,
        'events':[
            {'kind':'click','t':1.0,'semanticGoal':'inspect code review'},
            {'kind':'state_change','t':1.2,'evidence':'Source code diff visible'},
        ]
    }

def edit():
    return {'shots':[
        {'startFrame':20,'endFrame':125,'camera':[
            {'f':0,'zoom':1.,'anchor':'wide'},
            {'f':34,'zoom':1.5,'anchor':'result:0'}]},
        {'startFrame':125,'endFrame':260,'camera':[
            {'f':0,'zoom':1.,'anchor':'wide'}]}
    ]}

def test_real_click_falls_on_exact_output_frame():
    cues=actual_cues(source_manifest(),edit())
    cue=next(item for item in cues if item['kind']=='click')
    assert cue['source_frame']==75
    assert cue['frame']==55
    assert next(item for item in cues if item['kind']=='state_change')['frame']==67
    assert next(item for item in cues if item['kind']=='edit_boundary')['frame']==105
    assert next(item for item in cues if item['kind']=='camera_transition')['frame']==0

def test_wav_sample_clock_and_sha_are_deterministic(tmp_path):
    m,e=source_manifest(),edit()
    out=tmp_path/'foo.wav'
    report=synthesize(m,e,240,out)
    assert report['source_sha256']==SOURCE_HASH
    assert report['sample_rate']==48000 and report['audio_samples']==192000
    assert report['samples_per_frame']==800
    assert report['pcm_sha256']==hashlib.sha256(out.read_bytes()).hexdigest()
    with wave.open(str(out),'rb') as f:
        assert f.getframerate()==48000
        assert f.getnchannels()==2 and f.getnframes()==192000
        wave_data=np.frombuffer(f.readframes(f.getnframes()),dtype=np.int16).reshape(-1,2)
    at=55*SAMPLES_PER_FRAME
    assert np.max(np.abs(wave_data[at:at+300]))>1000
    second=tmp_path/'again.wav'
    assert synthesize(m,e,240,second)['pcm_sha256']==report['pcm_sha256']

@pytest.mark.parametrize('mutator',[
    lambda m: m.update({'cursorless':False}),
    lambda m: m.update({'source_sha256':''}),
    lambda m: m.update({'lead_s':float('nan')}),
    lambda m: m['events'][0].update({'semanticGoal':''}),
    lambda m: m['events'][0].update({'t':-0.5}),
    lambda m: m['events'][1].update({'evidence':''}),
])
def test_missing_real_capture_or_event_proof_fails_closed(mutator):
    m=source_manifest()
    mutator(m)
    with pytest.raises((ValueError,KeyError)):
        actual_cues(m,edit())

def test_audio_requires_an_actual_captured_click(tmp_path):
    m=source_manifest()
    m['events']=m['events'][1:]
    with pytest.raises(ValueError,match='No real click'):
        synthesize(m,edit(),240,tmp_path/'none.wav')

def test_source_ranges_and_duration_are_bounded(tmp_path):
    e=edit()
    e['shots'][0]['startFrame']=-2
    with pytest.raises(ValueError):actual_cues(source_manifest(),e)
    with pytest.raises(ValueError):synthesize(source_manifest(),edit(),29,tmp_path/'short.wav')
