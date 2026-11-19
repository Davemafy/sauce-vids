"""Contract tests for site-independent Sauce creative JSON over real source media."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from film_plan import load_film_plan


@pytest.fixture
def source(tmp_path):
    movie=tmp_path/"real-source.mp4"
    movie.write_bytes(b"test-verified-browser-pixels")
    sha=hashlib.sha256(movie.read_bytes()).hexdigest()
    manifest={
        "cursorless":True,"capture_rect":{"width":1920,"height":1080},
        "pointer_samples":[
            {"t":1.25,"x":600,"y":450},
            {"t":2.00,"x":740,"y":450},
            {"t":3.20,"x":790,"y":450}],
        "events":[{"kind":"slider_change","t":2.8,
                   "evidence":"Verified displayed price changed after actual range input",
                   "targetRect":{"x":500,"y":400,"width":500,"height":60},
                   "resultRect":{"x":600,"y":600,"width":320,"height":120}}]}
    plan={"schema":"sauce-film-plan-v1","sourceSha256":sha,
          "durationSeconds":5.5,"presentation":"fullscreen","cursor":"recorded",
          "audio":{"mode":"clean"},
          "camera":[{"at":0,"anchor":"wide","zoom":1},
                    {"at":1.1,"anchor":"event:0:target","zoom":1.25},
                    {"at":3.6,"startAt":2.8,"anchor":"event:0:group","zoom":1.25},
                    {"at":5.1,"startAt":4.0,"anchor":"event:0:result","zoom":1.40}]}
    return movie,manifest,plan


def compile_plan(source):
    movie,m,p=source
    path=movie.with_name("manifest.json")
    path.write_text(json.dumps(m,sort_keys=True))
    p.setdefault("manifestSha256",hashlib.sha256(path.read_bytes()).hexdigest())
    return load_film_plan(p,m,movie,path,(1920,1080),7.0,movie.with_name("plan.json"))


def test_recorded_source_has_real_camera_keyframes(source):
    p=compile_plan(source)
    assert len(p.camera_keys)==4
    assert p.source_size==(1920,1080)
    assert p.audio_file is None
    first=p.at(0,(1920,1080)); middle=p.at(2.3,(1920,1080))
    assert first.shape==(2,3)
    assert np.isfinite(middle).all()
    assert middle[0,0]>first[0,0]
    assert middle[1,1]==middle[0,0]
    assert not np.array_equal(first,middle)


def test_sha_mismatch_rejected(source):
    movie,m,p=source
    movie.write_bytes(b"other pixels")
    with pytest.raises(ValueError,match="Source SHA256 mismatch"):
        compile_plan(source)


def test_bogus_result_time_rejected(source):
    movie,m,p=source
    p["camera"][2]["at"]=2.79
    p["camera"][2]["startAt"]=2.7
    with pytest.raises(ValueError,match="not-yet-observed"):
        compile_plan(source)


def test_source_cannot_claim_unverified_result(source):
    movie,m,p=source
    m["events"][0]["evidence"]=""
    with pytest.raises(ValueError,match="verified outcome"):
        compile_plan(source)


def test_cursorless_provenance_required(source):
    movie,m,p=source
    m["cursorless"]=False
    with pytest.raises(ValueError,match="double cursors"):
        compile_plan(source)


def test_missing_pointer_track_fails_closed(source):
    movie,m,p=source
    m["pointer_samples"]=[]
    with pytest.raises(ValueError,match="source-timed track"):
        compile_plan(source)


def test_invalid_origin_geometry_rejected(source):
    movie,m,p=source
    m["events"][0]["resultRect"]["x"]=1700
    with pytest.raises(ValueError,match="outside genuine source"):
        compile_plan(source)


def test_nonmonotonic_timeline_fails(source):
    movie,m,p=source
    p["camera"][2]["at"]=1.1
    with pytest.raises(ValueError,match="strictly increasing"):
        compile_plan(source)


def test_bad_unknown_field_fails(source):
    movie,m,p=source
    p["camera"][1]["unsupportedLens"]=1234
    with pytest.raises(ValueError,match="unexpected keys"):
        compile_plan(source)


def test_reject_fabricated_effects_in_schema(source):
    movie,m,p=source
    p["generativeUI"]={"approved":True}
    with pytest.raises(ValueError,match="unexpected keys"):
        compile_plan(source)


def test_audio_cannot_escape_plan_workspace(source):
    movie,m,p=source
    p["audio"]={"mode":"file","file":"../../secrets.mp3"}
    with pytest.raises(ValueError,match="local to the plan"):
        compile_plan(source)


def test_audio_from_local_file_is_accepted(source):
    movie,m,p=source
    audio=movie.parent/"narration.wav"
    audio.write_bytes(b"private-owner-authorized-audio")
    p["audio"]={"mode":"file","file":"narration.wav"}
    assert compile_plan(source).audio_file == audio.resolve()


def test_protected_result_cannot_be_clipped(source):
    movie,m,p=source
    m["events"][0]["resultRect"]={"x":0,"y":0,"width":550,"height":250}
    p["camera"][3]["zoom"]=2.5
    with pytest.raises(ValueError,match="would be clipped"):
        compile_plan(source)


def test_identical_plan_over_source_is_deterministic(source):
    p=compile_plan(source)
    assert np.array_equal(p.at(3.4,(1280,720)),p.at(3.4,(1280,720)))

def test_easing_cannot_anticipate_future_result(source):
    movie,m,p=source
    p["camera"][2].pop("startAt")
    with pytest.raises(ValueError,match="anticipate unobserved result"):
        compile_plan(source)


def test_future_result_camera_holds_until_observed_action(source):
    movie,m,p=source
    plan=compile_plan(source)
    a=plan.at(2.1,(1920,1080))
    b=plan.at(2.79,(1920,1080))
    assert np.array_equal(a,b), "Result push must wait until actual changed value"
    assert not np.array_equal(a,plan.at(3.2,(1920,1080)))


def test_no_instant_hold_teleport(source):
    movie,m,p=source
    p["camera"][1]["easing"]="hold"
    with pytest.raises(ValueError,match="Unsupported camera easing"):
        compile_plan(source)


def test_manifest_hash_must_match_actual_evidence(source):
    movie,m,p=source
    p["manifestSha256"]="0"*64
    with pytest.raises(ValueError,match="manifest SHA256 mismatch"):
        compile_plan(source)
