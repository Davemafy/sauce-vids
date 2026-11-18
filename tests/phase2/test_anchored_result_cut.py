import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from anchored_result_cut import plan_result_cut


def test_verified_result_cut_keeps_anchor_and_full_region_in_view():
    bounds = {"x": 1200, "y": 223, "width": 193, "height": 109}
    click = {"kind": "click", "t": 4.9, "semanticGoal": "format selected data"}
    result = {"kind": "state_change", "t": 5., "resultRect": bounds, "evidence": "value changed"}
    args = ((1600, 900), (1920, 1080), 60)
    shot = plan_result_cut([click, result], *args, 7.)
    assert shot.frame == 315
    center = np.array([1296.5, 277.5, 1.])
    np.testing.assert_allclose(shot.matrix @ center, center[:2] * 1.2)
    assert np.all(shot.matrix @ [1200., 223., 1.] > 0)
    assert np.all(shot.matrix @ [1393., 332., 1.] < [1920, 1080])
    assert plan_result_cut([result], *args, 7.) is None
    assert plan_result_cut([click, result], *args, 6.) is None
    assert plan_result_cut([click, dict(result, evidence=True)], *args, 7.) is None
    assert plan_result_cut([click, dict(result, resultRect=dict(bounds, x=float("nan")))], *args, 7.) is None
