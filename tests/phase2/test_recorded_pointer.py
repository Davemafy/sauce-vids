import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from recorded_pointer import draw_pointer, pointer_track, project_pointer, _recorded_cursor_sprite


def test_pointer_requires_cursorless_source_and_projects_recorded_hotspot():
    samples = [{"t": 0, "x": 20, "y": 20}, {"t": 1, "x": 40, "y": 20}]
    assert pointer_track({"pointer_samples": samples}, 100, 100) is None
    assert pointer_track({"cursorless": True, "pointer_samples": samples[::-1]}, 100, 100) is None
    track = pointer_track({"cursorless": True, "pointer_samples": samples}, 100, 100)
    frame = np.full((1080, 1920, 3), 120, dtype=np.uint8)
    matrix = np.array([[2, 0, 30], [0, 2, 40]])
    out = project_pointer(frame, track, matrix, 0.5)
    assert np.any(out[80:124, 90:121] != 120)
    assert np.all(out[:77] == 120)


def test_recorded_cursor_uses_licensed_conventional_arrow_not_old_bent_polygon():
    """The formerly hand-coded 7-point glyph produced a crooked-looking arrow."""
    from cinematic_presentation_v13 import _blend
    from online_cursor_assets import icon, hotspot
    from PIL import Image

    stage=np.full((1080,1920,3),[32,34,39],dtype=np.uint8)
    actual=stage.copy()
    click_tip=(801.25,342.7)
    draw_pointer(actual,*click_tip,scale=.73)
    official=icon("outline")
    size=(round(official.shape[1]*.73),round(official.shape[0]*.73))
    art=np.asarray(Image.fromarray(official,"RGBA").resize(
        size,Image.Resampling.LANCZOS),dtype=np.uint8)
    hot_x,hot_y=hotspot("outline")
    expected=stage.copy()
    _blend(expected,art,round(click_tip[0]-hot_x*.73),
                      round(click_tip[1]-hot_y*.73))
    np.testing.assert_array_equal(actual,expected)
    # Anti-aliased conventional arrow has a filled, readily visible white body.
    roi=actual[335:389,794:850]
    assert np.count_nonzero(np.all(roi>220,axis=2))>=50
    # Preserve original pointer apex/click; do not paint a second fake cursor.
    np.testing.assert_array_equal(actual[:320],stage[:320])
    assert _recorded_cursor_sprite(.73)[0] is _recorded_cursor_sprite(.73)[0]


def test_projected_cursor_uses_real_source_hotspot_without_creating_early_pointer():
    track=np.float64([[.95,220,180],[1.1,270,220],[1.3,300,250]])
    stage=np.full((1080,1920,3),[45,48,52],dtype=np.uint8)
    matrix=np.float64([[1.4,0.,95],[0.,1.4,40]])
    out=project_pointer(stage.copy(),track,matrix,1.1,scale=.73)
    tip=matrix@[270.,220.,1.]
    expected=stage.copy()
    draw_pointer(expected,*tip,scale=.73)
    np.testing.assert_array_equal(out,expected)
