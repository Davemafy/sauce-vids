"""High-density public URL source is opt-in and proven, not merely upscaled."""
import os
from unittest.mock import patch
import pytest
from backend.live_capture import capture_quality,capture_cursor_style,ARROW_CURSOR_JS
from backend.live_render import source_video_profile


def test_legacy_pilot_capture_remains_720p_and_dpr1():
    with patch.dict(os.environ, {}, clear=True):
        p=capture_quality()
    assert p == {'quality':'standard','dpr':1,
                 'viewport':{'width':1280,'height':720},
                 'video_size':{'width':1280,'height':720}}


def test_opt_in_capture_uses_hidpi_chromium_at_real_1080p():
    with patch.dict(os.environ, {'SAUCE_CAPTURE_QUALITY':'high'}, clear=True):
        p=capture_quality()
    assert p == {'quality':'high','dpr':2,
                 'viewport':{'width':1920,'height':1080},
                 'video_size':{'width':1920,'height':1080}}


@pytest.mark.parametrize('quality',['low','native','4k','HIGH',''])
def test_invalid_quality_is_not_silently_promoted(quality):
    with patch.dict(os.environ, {'SAUCE_CAPTURE_QUALITY':quality}, clear=True):
        with pytest.raises(ValueError):
            capture_quality()


def test_native_source_preserved_without_spatial_upscale():
    receipt={'capture_quality':'high','source_dpr':2,
             'viewport_css_size':{'width':1920,'height':1080},
             'requested_video_size':{'width':1920,'height':1080}}
    profile=source_video_profile(
        {'width':1920,'height':1080,'r_frame_rate':'30/1'},receipt)
    assert profile['native_1080p']
    assert profile['dimensions']==[1920,1080]
    assert profile['source_dpr']==2
    assert 'scale=1920' not in profile['filter']
    assert profile['source_fps']=='30/1'


def test_legacy_720p_is_still_truthfully_labeled_as_upscaled():
    p=source_video_profile(
        {'width':1280,'height':720,'r_frame_rate':'25/1'}, {})
    assert not p['native_1080p']
    assert p['source_dpr']==1
    assert p['filter'].startswith('scale=1920:1080')


def test_high_quality_claim_rejected_for_720p_video():
    with pytest.raises(RuntimeError,match='differs'):
        source_video_profile({'width':1280,'height':720},{
            'capture_quality':'high','source_dpr':2,
            'requested_video_size':{'width':1920,'height':1080}})


def test_high_quality_claim_rejected_when_dpr_is_wrong():
    with pytest.raises(RuntimeError,match='proof mismatch'):
        source_video_profile({'width':1920,'height':1080},{
            'capture_quality':'high','source_dpr':1,
            'requested_video_size':{'width':1920,'height':1080}})


def test_unsupported_recordings_cannot_be_mislabeled():
    with pytest.raises(RuntimeError,match='dimensions'):
        source_video_profile({'width':640,'height':360},{})


def test_default_cursor_is_unchanged_for_existing_pilot():
    with patch.dict(os.environ, {}, clear=True):
        assert capture_cursor_style()=='circle'


def test_real_arrow_requires_explicit_opt_in():
    with patch.dict(os.environ, {'SAUCE_CAPTURE_CURSOR':'arrow'}, clear=True):
        assert capture_cursor_style()=='arrow'
    assert "point.x-2.5" in ARROW_CURSOR_JS
    assert "point.y-2" in ARROW_CURSOR_JS
    assert "aria-hidden" in ARROW_CURSOR_JS
    assert "window.__sauceGetPointer" in ARROW_CURSOR_JS
    assert 'path d=' in ARROW_CURSOR_JS


def test_unrecognized_cursor_is_rejected():
    with patch.dict(os.environ, {'SAUCE_CAPTURE_CURSOR':'giant-glass-dot'}, clear=True):
        with pytest.raises(ValueError):
            capture_cursor_style()

def test_padded_1080_container_is_not_native_source():
    # This actually happened during the first real Chromium high-DPR
    # experiment. The video probed 1920x1080 but the UI occupied only
    # 1280x720 CSS pixels with blank padding to the right and bottom.
    with pytest.raises(RuntimeError,match='CSS viewport'):
        source_video_profile({'width':1920,'height':1080},{
            'capture_quality':'high','source_dpr':2,
            'requested_video_size':{'width':1920,'height':1080},
            'viewport_css_size':{'width':1280,'height':720}})


def test_high_density_requires_source_viewport_evidence():
    with pytest.raises(RuntimeError,match='CSS viewport'):
        source_video_profile({'width':1920,'height':1080},{
            'capture_quality':'high','source_dpr':2,
            'requested_video_size':{'width':1920,'height':1080}})
