from scripts.reference_shot_fit import match_landscape_component, scale_end_for_frames

def test_verified_heroui_chart_pair_fits_arcade_posting_card_without_stretching():
    rect={"x":521,"y":348.5,"width":1118,"height":316}
    fit=match_landscape_component(rect,(1920,1080))
    assert fit.eligible_geometry
    assert fit.padding_px in (25,26,27,28)
    assert fit.aspect_error_fraction<.002
    assert fit.padded_bounds[0]>=0 and fit.padded_bounds[2]<=1920

def test_verified_resend_tall_price_card_must_not_be_forced_into_wide_posting_shape():
    rect={"x":655,"y":368.796875,"width":299,"height":658.3125}
    fit=match_landscape_component(rect,(1920,1080))
    assert not fit.eligible_geometry
    assert "too tall" in fit.reason

def test_near_edge_panel_rejected_instead_of_inventing_missing_border_pixels():
    rect={"x":0,"y":10,"width":1118,"height":316}
    fit=match_landscape_component(rect,(1920,1080))
    assert not fit.eligible_geometry
    assert "clip" in fit.reason

def test_exact_46_frame_arcade_width_growth_compensates_terminal_sample_clock():
    scale=scale_end_for_frames(1520,1550,46)
    widths=[round(1520*(1+(scale-1)*i/46)) for i in range(46)]
    assert widths[0]==1520
    assert widths[-1]==1550
    assert widths[15]==1530
    assert widths[30]==1540

def test_ref_motion_rejects_excessive_scale():
    import pytest
    with pytest.raises(ValueError):
        scale_end_for_frames(100,200,46)
