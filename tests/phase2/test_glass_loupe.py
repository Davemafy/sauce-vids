"""Evidence, fallback, and deterministic pixels for the event-video loupe."""
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from glass_loupe import apply_loupe, plan_loupe


def event():
    return {
        "kind":"slider_change", "start":.5, "t":.8, "end":1.2,
        "evidence":"Observed result text change",
        "targetRect":{"x":30,"y":45,"width":120,"height":12},
        "resultRect":{"x":70,"y":90,"width":85,"height":20},
        "pointer_samples":[{"t":.5,"x":55,"y":50},{"t":1.2,"x":110,"y":50}],
    }


def test_requires_verified_change_and_cursorless_footage():
    valid = event()
    for patch in ({"evidence":""}, {"resultRect":None}, {"t":.3},
                  {"pointer_samples":[{"t":.5,"x":0,"y":50}]*2}):
        assert not plan_loupe({"cursorless":True,"events":[valid|patch]},320,180,4)
    assert not plan_loupe({"events":[valid]},320,180,4)
    shot, = plan_loupe({"cursorless":True,"events":[valid]},320,180,4)
    assert np.allclose(shot.pointer(.85),(82.5,50))
    assert shot.pointer(3) == (110,50)


def test_uses_same_frame_source_and_changes_only_lens_area():
    shot, = plan_loupe({"cursorless":True,"events":[event()]},320,180,4)
    original = np.full((180,320,3),150,dtype=np.uint8)
    frame = np.full_like(original,40)
    transform = np.float32([[1,0,0],[0,1,0]])
    result = apply_loupe(frame.copy(),original,transform,shot,2)
    assert np.array_equal(result,apply_loupe(frame.copy(),original,transform,shot,2))
    assert np.array_equal(result[:,300:],frame[:,300:])
    assert np.array_equal(result[75,111],original[75,111])
    assert not np.array_equal(result,apply_loupe(frame.copy(),255-original,transform,shot,2))


def test_short_tail_keeps_lens_and_cursor_visible_until_clip_end():
    shot, = plan_loupe({"cursorless":True,"events":[event()]},320,180,4.25)
    assert shot.end == 4.25 and not shot.dissolve
    source = np.full((180,320,3),40,dtype=np.uint8)
    transform = np.float64([[1,0,0],[0,1,0]])
    held = apply_loupe(source.copy(),source,transform,shot,3.)
    final = apply_loupe(source.copy(),source,transform,shot,4.24)
    assert np.array_equal(held,final)
    assert np.max(final) > 220


def test_interpolation_preserves_sample_and_does_not_overshoot_reversal():
    observed = event()
    observed["pointer_samples"] = [
        {"t":.5,"x":55,"y":50},
        {"t":.8,"x":110,"y":50},
        {"t":1.2,"x":70,"y":50},
    ]
    shot, = plan_loupe({"cursorless":True,"events":[observed]},320,180,5)
    assert shot.pointer(.8) == (110,50)
    assert max(shot.pointer(i/1000)[0] for i in range(500,1201)) == 110
    assert abs(shot.pointer(.801)[0]-shot.pointer(.799)[0]) < .01
