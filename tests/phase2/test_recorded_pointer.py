import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from recorded_pointer import pointer_track, project_pointer


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
