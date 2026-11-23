"""Browser scrollbars vanish in fresh source footage; real scrolling remains."""
from pathlib import Path
import sys
import copy
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts"))
from session_capture import MOCKUP_SCROLLBAR_STYLE
from cloud_shadow_stage import window_geometry
from spatial_studio_stage import load_studio_stage


def test_public_scout_and_recorders_reuse_existing_scrollbar_cleanup():
    for name in ("public_interaction_scout.py",
                 "record_scouted_interactions.py",
                 "source_truth_tab_capture.py"):
        src=(ROOT/"scripts"/name).read_text()
        assert "from session_capture import MOCKUP_SCROLLBAR_STYLE,install_presentation_cleanup" in src
        assert "install_presentation_cleanup(" in src
        assert "page.add_style_tag(content=MOCKUP_SCROLLBAR_STYLE)" in src
    assert "scrollbar-width: none" in MOCKUP_SCROLLBAR_STYLE
    assert "display: none !important" in MOCKUP_SCROLLBAR_STYLE
    # This CSS does not set overflow:hidden or disable pointer/wheel actions.
    assert "overflow" not in MOCKUP_SCROLLBAR_STYLE
    assert "pointer-events" not in MOCKUP_SCROLLBAR_STYLE


@pytest.mark.skipif(not Path("/opt/devmcp-browsers/chromium_headless_shell-1255/chrome-headless-shell-linux64/chrome-headless-shell").exists(),
                    reason="Dedicated Chromium headless browser unavailable")
def test_original_document_and_nested_scroll_still_work_under_cleanup():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b=pw.chromium.launch(headless=True, executable_path=
          "/opt/devmcp-browsers/chromium_headless_shell-1255/chrome-headless-shell-linux64/chrome-headless-shell",
          args=["--no-sandbox"])
        page=b.new_page(viewport={"width":960,"height":540})
        page.set_content('''<body style="margin:0">
          <div id="inner" style="height:130px;width:340px;overflow:auto">
          <div style="height:700px">Real product content</div></div>
          <div style="height:2300px">More real content</div></body>''')
        before=page.evaluate("""() => ({
           document:document.scrollingElement.scrollHeight,
           nested:document.querySelector('#inner').scrollHeight})""")
        page.add_style_tag(content=MOCKUP_SCROLLBAR_STYLE)
        after=page.evaluate("""() => ({
           document:document.scrollingElement.scrollHeight,
           nested:document.querySelector('#inner').scrollHeight,
           hidden:getComputedStyle(document.querySelector('#inner'),'::-webkit-scrollbar').display})""")
        assert after["document"]==before["document"]
        assert after["nested"]==before["nested"]
        assert after["hidden"]=="none"
        page.evaluate("() => {scrollTo(0,400);document.querySelector('#inner').scrollTop=250}")
        movement=page.evaluate("() => ({main:scrollY,inner:document.querySelector('#inner').scrollTop})")
        assert movement=={"main":400,"inner":250}
        b.close()


def test_larger_browser_stays_inside_stage_with_genuine_margins():
    a=window_geometry((2880,1800),(1920,1080))
    left,top,right,bottom,radius=a
    assert right-left>1500 and bottom-top>930
    assert left>=185 and right<=1735
    assert 60<=top<=75 and 60<=1080-bottom<=75
    assert 15<=radius<=26


def test_output_encoder_uses_loss_aware_60fps_preset():
    real=(ROOT/"scripts/render_event_video.py").read_text()
    temporal=(ROOT/"scripts/source_true_film_recut.py").read_text()
    assert '"-preset","medium","-crf","15"' in real
    assert '"-preset","medium","-crf","15"' in temporal
