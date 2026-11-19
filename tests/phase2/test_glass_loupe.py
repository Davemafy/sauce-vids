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


def test_sustained_drag_can_reframe_before_verified_price_and_exit_to_wide():
    observed = event()
    observed.update(t=2.4, end=3.7, fade_at_end=True, pointer_samples=[
        {"t":.5,"x":55,"y":50},
        {"t":1.45,"x":70,"y":50},
        {"t":2.4,"x":110,"y":50},
        {"t":3.7,"x":70,"y":50},
    ])
    shot, = plan_loupe({"cursorless":True,"events":[observed]},320,180,4.65)
    assert (shot.reframe, shot.changed, shot.end, shot.dissolve) == (1.45,2.4,4.65,True)
    source = np.full((180,320,3),40,dtype=np.uint8)
    transform = np.float64([[1,0,0],[0,1,0]])
    peaked = apply_loupe(source.copy(),source,transform,shot,3.)
    returned = apply_loupe(source.copy(),source,transform,shot,4.6)
    assert np.count_nonzero(peaked != source) > 1000
    assert np.count_nonzero(returned != source) < 250
    assert returned.max() > 220


def test_cursor_can_leave_control_after_release_without_reframing_glass():
    event_with_tail = event()
    event_with_tail["pointer_samples"].extend([
        {"t":1.4,"x":65,"y":70}, {"t":1.8,"x":55,"y":80},
    ])
    shot, = plan_loupe({"cursorless":True,"events":[event_with_tail]},320,180,4)
    assert shot.pointer(1.8) == (55,80)
    assert shot.pointer(shot.released) == (110,50)
    event_with_tail["pointer_samples"][-1]["x"] = 360
    assert not plan_loupe({"cursorless":True,"events":[event_with_tail]},320,180,4)


def test_liquid_edge_changes_slope_without_distorting_center():
    from glass_loupe import _edge_bend
    radii = np.linspace(0,1,100)
    mapped = radii*_edge_bend(radii)
    assert np.all(np.diff(mapped)>0)
    assert _edge_bend(.55) == 1.
    assert _edge_bend(1.) > 1.3


def test_plan_loupe_style_changes_pixels_and_rejects_invalid_controls():
    import pytest
    from glass_loupe import LoupeStyle

    shot, = plan_loupe({"cursorless": True, "events": [event()]}, 320, 180, 4)
    source = np.full((180, 320, 3), 100, dtype=np.uint8)
    stage = np.full_like(source, 20)
    matrix = np.float64([[1, 0, 0], [0, 1, 0]])
    style = LoupeStyle.from_plan({"entry_delay": .5, "expanded_radius": .75})
    baseline = apply_loupe(stage.copy(), source, matrix, shot, .85)
    revised = apply_loupe(stage.copy(), source, matrix, shot, .85, style)
    assert np.count_nonzero(baseline != stage) > np.count_nonzero(revised != stage)
    for item in ({"entry_delay": True}, {"small_radius": .86},
                 {"expanded_radius": .3}, {"payoff_y": float("nan")}, {"script": "path"}):
        with pytest.raises(ValueError):
            LoupeStyle.from_plan(item)


def test_plan_selects_cursor_silhouette_without_changing_the_lens():
    import pytest
    from glass_loupe import LoupeStyle

    shot, = plan_loupe({"cursorless": True, "events": [event()]}, 320, 180, 4)
    source = np.full((180, 320, 3), 120, dtype=np.uint8)
    stage = np.full_like(source, 20)
    matrix = np.float64([[1, 0, 0], [0, 1, 0]])
    outlined = LoupeStyle.from_plan({"cursor_style": "outlined"})
    baseline = apply_loupe(stage.copy(), source, matrix, shot, 2)
    revised = apply_loupe(stage.copy(), source, matrix, shot, 2, outlined)
    delta = np.any(baseline != revised, axis=2)
    assert 0 < np.count_nonzero(delta) < 100
    with pytest.raises(ValueError, match="cursor_style"):
        LoupeStyle.from_plan({"cursor_style": "unknown"})
