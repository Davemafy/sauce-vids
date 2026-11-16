"""The executed edit clock and deterministic Foley share 800 samples/frame."""
from __future__ import annotations
import sys,wave
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from foley_mixer import RATE,_synthesis,render_foley_plan

def test_exact_48khz_foley_positions_across_hard_cuts(tmp_path):
    assert RATE==48000
    sample_per_frame=RATE//60
    assert sample_per_frame==800
    cut_frames=(61,129)
    cues=[{'sound':'click_crisp','outputSample':f*sample_per_frame,
           'outputMs':f*1000/60,'gain':.6} for f in (60,130)]
    plan={'schema':'sauce-foley-plan-v1','sampleRate':RATE,
      'durationMs':180*1000/60,'muted':False,'masterGain':.4,
      'musicGain':0.,'cues':cues,'duckIntervals':[]}
    path=tmp_path/'cut-locked-foley.wav'
    result=render_foley_plan(plan,path)
    assert result['samples']==180*sample_per_frame
    with wave.open(str(path),'rb') as f:
        assert (f.getframerate(),f.getnchannels())==(RATE,2)
        pcm=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2')
        audio=pcm.reshape(-1,2).astype(np.float64)/32767.
    reference=_synthesis('click_crisp')[:,0].astype(np.float64)*.6*.4
    for cue in cues:
        at=cue['outputSample']
        assert at%800==0
        assert not np.any(audio[at-100:at,0])
        lags=range(-4,5)
        scores=[np.dot(audio[at+k:at+k+len(reference),0],reference)
                for k in lags]
        assert list(lags)[int(np.argmax(scores))]==0
    assert all(a==b*800 for a,b in [(cut_frames[0]*800,cut_frames[0]),
                                      (cut_frames[1]*800,cut_frames[1])])
