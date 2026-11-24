import hashlib,json,sys,wave
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from foley_mixer import render_foley_plan,_sample_asset,RATE
BANK=ROOT/'assets/foley/bencho'

def test_pinned_bencho_assets_and_exact_event_clock(tmp_path):
    catalog=json.loads((BANK/'catalog.json').read_text())
    assert len(catalog['sounds'])==24
    cues=[]
    for i,(alias,name) in enumerate(catalog['aliases'].items()):
        assert hashlib.sha256((BANK/(alias+'.flac')).read_bytes()).hexdigest()==catalog['sounds'][name]['sha256']
        sample=_sample_asset(alias,BANK)
        assert len(sample)==catalog['sounds'][name]['samples']
        assert np.max(np.abs(sample))>0.25
        at=(60+60*i)*800
        cues.append(dict(sound=alias,outputSample=at,outputMs=at/48,gain=.5))
    plan=dict(schema='sauce-foley-plan-v1',sampleRate=RATE,durationMs=4000,
              muted=False,masterGain=.5,musicGain=0.,duckIntervals=[],cues=cues)
    path=tmp_path/'bencho.wav'
    receipt=render_foley_plan(plan,path,asset_dir=BANK)
    assert receipt['asset_sources']=={c['sound']:'local' for c in cues}
    with wave.open(str(path),'rb') as f:
        assert f.getframerate()==48000 and f.getnframes()==192000
        pcm=np.frombuffer(f.readframes(f.getnframes()),'<i2').reshape(-1,2)/32767.
    for cue in cues:
        at=cue['outputSample'];reference=_sample_asset(cue['sound'],BANK)[:,0]*.25
        assert not np.any(pcm[at-100:at,0])
        scores=[np.dot(pcm[at+d:at+d+len(reference),0],reference) for d in range(-4,5)]
        assert np.argmax(scores)==4
    plan['muted']=True
    assert render_foley_plan(plan,path,asset_dir=BANK)['peak']==0
