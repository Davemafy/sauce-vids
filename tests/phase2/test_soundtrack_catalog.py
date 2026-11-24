from pathlib import Path
import sys
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from soundtrack_catalog import admit, sha, excerpts

def test_rights_evidence_and_bytes_are_both_pinned(tmp_path):
    evidence=tmp_path/'source.html'
    evidence.write_text('CC0 1.0 Universal License https://creativecommons.org/publicdomain/zero/1.0/')
    track=tmp_path/'track.mp3'
    track.write_bytes(b'test media fixture')
    row=dict(license='CC0-1.0',file='track.mp3',sha256=sha(track),
             license_evidence='source.html',license_evidence_sha256=sha(evidence))
    assert admit(tmp_path,row)==track
    with pytest.raises(ValueError):
        admit(tmp_path,dict(row,license='CC-BY-NC'))
    track.write_bytes(b'tampered')
    with pytest.raises(ValueError):
        admit(tmp_path,row)

def test_excerpt_suggestions_are_bounded_and_seek_rhythm():
    t=np.arange(0,30,.016)
    power=np.full_like(t,.05)
    power[(t>=10)&(t<20)]=1.
    flux=np.zeros_like(t)
    flux[(t>=10)&(t<20)]=.8
    candidates=excerpts(t,flux,power,30,10,[1,4,7])
    assert 9<=candidates[0]['start']<=11
    assert all(0<=r['start']<=20 for r in candidates)
    with pytest.raises(ValueError):
        excerpts(t,flux,power,30,31)
