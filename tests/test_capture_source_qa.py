import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import pytest
from capture_source_qa import Geometry, clock_report, outcome_report, parse_framemd5


def test_calibrated_pointer_hotspot_dpr2_and_crop():
    g = Geometry(1440, 900, 2, crop_x=105, crop_y=180, crop_width=2640,
                 crop_height=1440, hotspot_x=2, hotspot_y=3)
    assert g.source_hotspot(400, 200) == (695, 220)
    assert g.cursor_sprite_origin(400, 200) == (693, 217)


@pytest.mark.parametrize("css_x,css_y", [(-1, 10), (1440, 10), (5, 901)])
def test_out_of_viewport_pointer_is_rejected(css_x, css_y):
    with pytest.raises(ValueError):
        Geometry(1440, 900, 2).source_hotspot(css_x, css_y)


def test_impossible_crop_is_rejected():
    with pytest.raises(ValueError, match="exceeds"):
        Geometry(400, 300, 2, crop_width=1000).validate()


def test_framemd5_timestamp_parsing_and_duplicate_detection(tmp_path):
    p = tmp_path / "frames.md5"
    p.write_text("#tb 0: 1/60\n0, 0, 0, 1, 3, abc\n0, 1, 1, 1, 3, abc\n0, 2, 2, 1, 3, def\n")
    frames = parse_framemd5(p)
    assert frames[1][0] == pytest.approx(1/60)
    report = clock_report(frames, 60)
    assert report["adjacent_exact_duplicates"] == 1
    assert not report["qa_pass"]
    assert report["nominal_unique_fps_unproven"]


def test_source_timestamp_gap_negative():
    report = clock_report([(0, "a"), (1/60, "b"), (4/60, "c")], 60)
    assert report["pts_gaps"] == 1
    assert not report["qa_pass"]


def test_repeated_or_unsorted_pts_negative(tmp_path):
    p = tmp_path / "bad.md5"
    p.write_text("#tb 0: 1/60\n0, 0, 0, 1, 3, a\n0, 1, 0, 1, 3, b\n")
    with pytest.raises(ValueError, match="timestamp"):
        parse_framemd5(p)


def test_dom_click_to_real_result_and_pointer_alignment():
    rect = {"x": 100, "y": 200, "width": 60, "height": 40}
    events = [{"t": 1.0, "kind": "click", "targetRect": rect},
              {"t": 1.2, "kind": "state_change", "evidence": "Visible DOM panel"}]
    pointer = [{"t": 0.99, "x": 120, "y": 210}]
    assert outcome_report(events, pointer)["qa_pass"]
    assert not outcome_report(events[:1], pointer)["qa_pass"]
    assert not outcome_report(events, [{"t": 1, "x": 500, "y": 600}])["qa_pass"]
    assert not outcome_report([events[0], {"t": 1.2, "kind": "state_change"}], pointer)["qa_pass"]


def test_invalid_event_clock_negative():
    with pytest.raises(ValueError, match="monotonic"):
        outcome_report([{"t": 2, "kind": "click"}, {"t": 1, "kind": "state_change"}], [])


def test_empty_clicks_do_not_pass():
    assert not outcome_report([{"t": 0, "kind": "state_change"}], [])["qa_pass"]
