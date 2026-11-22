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


def test_recorded_cursor_matches_original_cc0_svg_geometry_and_hotspot():
    """Full-frame pixels must match the real Mint vector, never a UI icon."""
    from io import BytesIO
    import cairosvg
    from PIL import Image
    from cinematic_presentation_v13 import _blend

    stage=np.full((1080,1920,3),[32,34,39],dtype=np.uint8)
    actual=stage.copy()
    recorded_tip=(801.25,342.7)
    draw_pointer(actual,*recorded_tip,scale=.73)

    source=(Path(__file__).resolve().parents[2]
            /"assets/cursors/mint-studio/arrow.svg").read_text()
    assert 'hotspot 0,0' in source
    assert source.count('stroke="#66757f"')==1
    # Independently rasterize original CC0 path with only a white-rim recolor.
    size=round(55*.73)
    white_rim=source.replace('stroke="#66757f"','stroke="#f5f7fb"')
    png=cairosvg.svg2png(bytestring=white_rim.encode(),
                         output_width=size*4,output_height=size*4)
    art=np.asarray(Image.open(BytesIO(png)).convert("RGBA").resize(
        (size,size),Image.Resampling.LANCZOS),dtype=np.uint8)
    expected=stage.copy()
    _blend(expected,art,round(recorded_tip[0]),round(recorded_tip[1]))
    np.testing.assert_array_equal(actual,expected)
    roi=actual[342:386,801:846]
    assert np.count_nonzero(np.all(roi>220,axis=2))>=30
    np.testing.assert_array_equal(actual[:320],stage[:320])
    assert _recorded_cursor_sprite(.73)[0] is _recorded_cursor_sprite(.73)[0]


def test_mint_svg_cursor_pack_roles_have_verified_native_hotspots():
    from recorded_pointer import _mint_svg_sprite
    for role,tip in (("arrow",(0,0)),("hand",(10,2)),("text",(16,16))):
        art,hot=_mint_svg_sprite(role,48)
        assert art.shape==(48,48,4)
        assert hot==(tip[0]*1.5,tip[1]*1.5)
        assert art[:,:,3].max()==255
    import pytest
    with pytest.raises(ValueError):
        _mint_svg_sprite("nonexistent",48)
    with pytest.raises(ValueError):
        _mint_svg_sprite("arrow",300)


def test_legacy_cursor_pack_available_only_when_explicitly_requested():
    from online_cursor_assets import icon,hotspot
    from cinematic_presentation_v13 import _blend
    from PIL import Image
    scale=.73;tip=(801.25,342.7)
    src=np.full((1080,1920,3),[32,34,39],dtype=np.uint8)
    actual=src.copy()
    draw_pointer(actual,*tip,scale=scale,theme="tabler-legacy")
    art=icon("outline")
    resized=np.asarray(Image.fromarray(art,"RGBA").resize(
        (round(art.shape[1]*scale),round(art.shape[0]*scale)),
        Image.Resampling.LANCZOS),dtype=np.uint8)
    h=hotspot("outline")
    expected=src.copy()
    _blend(expected,resized,round(tip[0]-h[0]*scale),
                          round(tip[1]-h[1]*scale))
    np.testing.assert_array_equal(actual,expected)
    assert not np.array_equal(actual,src)


def test_projected_cursor_uses_real_source_hotspot_without_creating_early_pointer():
    track=np.float64([[.95,220,180],[1.1,270,220],[1.3,300,250]])
    stage=np.full((1080,1920,3),[45,48,52],dtype=np.uint8)
    matrix=np.float64([[1.4,0.,95],[0.,1.4,40]])
    out=project_pointer(stage.copy(),track,matrix,1.1,scale=.73)
    tip=matrix@[270.,220.,1.]
    expected=stage.copy()
    draw_pointer(expected,*tip,scale=.73)
    np.testing.assert_array_equal(out,expected)


def test_all_three_original_cursor_styles_are_distinct_but_hotspot_precise():
    """Studio, glossy and playful are real SVG presets, never stacked cursors."""
    from recorded_pointer import SAUCE_ORIGINAL_STYLE_PACKS, _sauce_style_sprite
    from io import BytesIO
    from PIL import Image
    import cairosvg
    import xml.etree.ElementTree as ET

    assert SAUCE_ORIGINAL_STYLE_PACKS == (
        "studio-rounded", "gloss-carbon", "aero-prism")
    frames=[]
    for theme in SAUCE_ORIGINAL_STYLE_PACKS:
        p=(Path(__file__).resolve().parents[2]
           / "assets" / "cursors" / "sauce-styles" / f"{theme}.svg")
        original=p.read_text()
        element=ET.fromstring(original)
        assert element.get("viewBox")=="0 0 48 56"
        title=element.find("{http://www.w3.org/2000/svg}title")
        assert title is not None and "hotspot 4,4" in (title.text or "")
        native=Image.open(BytesIO(cairosvg.svg2png(
            bytestring=original.encode(), output_width=160,
            output_height=188))).convert("RGBA")
        native=np.asarray(native.resize((40,47),Image.Resampling.LANCZOS))
        art,hot=_sauce_style_sprite(theme,40)
        np.testing.assert_array_equal(art,native)
        assert hot == (4*40/48,4*47/56)
        assert art.shape==(47,40,4)
        assert np.count_nonzero(art[:,:,3]>30)>140
        assert art[:,:,3].max()==255
        assert _sauce_style_sprite(theme,40)[0] is art  # cached once per style
        frames.append(art)
    assert np.mean(np.abs(frames[0].astype(np.int16)-frames[1].astype(np.int16)))>12
    assert np.mean(np.abs(frames[0].astype(np.int16)-frames[2].astype(np.int16)))>12
    assert np.mean(np.abs(frames[1].astype(np.int16)-frames[2].astype(np.int16)))>12


def test_style_selection_modifies_sprite_not_recorded_cursor_coordinates():
    """The visual treatments may change pixels but never the observed click tip."""
    from recorded_pointer import CURSOR_PACKS,_recorded_cursor_sprite
    import pytest
    assert all(p in CURSOR_PACKS for p in ("studio-rounded","gloss-carbon","aero-prism"))
    tip=(801.5,343.25)
    base=np.full((1080,1920,3),39,dtype=np.uint8)
    views=[]
    for style in ("studio-rounded","gloss-carbon","aero-prism"):
        # One source-timed click location; only the painted sprite changes.
        result=base.copy()
        draw_pointer(result,*tip,scale=.73,theme=style)
        assert np.array_equal(result[:330],base[:330])
        assert np.any(result[343:394,801:854]!=base[343:394,801:854])
        views.append(result)
    assert not np.array_equal(views[0],views[1])
    assert not np.array_equal(views[1],views[2])
    with pytest.raises(ValueError,match="Unknown cursor theme"):
        _recorded_cursor_sprite(.73, "copied-proprietary-package")
