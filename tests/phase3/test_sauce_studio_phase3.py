"""Sauce Studio Phase 3: cursor fidelity, presentation polish and safety."""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts"))
from click_anchor import align_click_positions
from session_capture import MOCKUP_SCROLLBAR_STYLE,PRESENTATION_CLEANUP_STYLE
from studio_motion_callouts import KineticCalloutRenderer


def test_scrollbars_are_visually_hidden_not_disabled():
    assert "::-webkit-scrollbar" in MOCKUP_SCROLLBAR_STYLE
    assert "display: none !important" in MOCKUP_SCROLLBAR_STYLE
    assert "scrollbar-width: none" in MOCKUP_SCROLLBAR_STYLE
    source=(ROOT/"scripts/session_replay.py").read_text()
    assert "page.add_style_tag(content=PRESENTATION_CLEANUP_STYLE)" in source


def test_click_anchor_exact_recorded_position():
    pts=[(0.,0.) for _ in range(90)]
    event={"type":"pointerdown","t":1000,"x":120.,"y":150.}
    result=align_click_positions(pts,[event],0,60)
    assert result[60] == (120.,150.)
    assert result[45] == pts[45]
    assert result[60] != pts[60]
    assert result[61][0] < 120.
    assert len(result)==len(pts)


def test_small_click_deviation_does_not_change_track():
    pts=[(100.25,150.5) for _ in range(100)]
    click={"type":"pointerdown","t":1000,"x":100.4,"y":150.4}
    assert align_click_positions(pts,[click],0,60)==pts


def test_kinetic_callout_has_glass_rim_and_180ms_slide():
    import numpy as np
    frame=np.full((1080,1920,3),38,dtype=np.uint8)
    cues=[{"text":"Connect Agent",
           "outputStartMs":0,"outputEndMs":1200,
           "box":{"x":390,"y":210,"width":200,"height":45}}]
    renderer=KineticCalloutRenderer(cues,fps=60)
    first=frame.copy()
    renderer.draw(first,0,1,0,0,(0,0),(220,124,1480,832),1200)
    assert np.array_equal(first,frame)
    middle=frame.copy()
    renderer.draw(middle,5,1,0,0,(0,0),(220,124,1480,832),1200)
    assert np.count_nonzero(middle!=frame)>100
    visible=frame.copy()
    renderer.draw(visible,11,1,0,0,(0,0),(220,124,1480,832),1200)
    assert np.count_nonzero(visible!=frame)>1000
    code=(ROOT/"scripts/studio_motion_callouts.py").read_text()
    assert "progress*progress*(3-2*progress)" in code
    assert "216,236,249" in code


@pytest.mark.skipif(os.getenv("SAUCE_BROWSER_TEST")!="1",
                    reason="Enable the real Chromium integration on Vultr")
def test_scrollbar_css_in_real_chromium():
    from playwright.sync_api import sync_playwright
    binary="/opt/devmcp-browsers/chromium_headless_shell-1254/chrome-headless-shell-linux64/chrome-headless-shell"
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=binary,
                                   args=["--no-sandbox","--disable-dev-shm-usage"])
        page=browser.new_page(viewport={"width":400,"height":500})
        page.set_content("""<div id="scroller"
          style="width:200px;height:100px;overflow:auto">
          <div style="height:700px">Scrollable content</div></div>""")
        page.add_style_tag(content=MOCKUP_SCROLLBAR_STYLE)
        assert page.locator("#scroller").evaluate(
          "e=>getComputedStyle(e,'::-webkit-scrollbar').display")=="none"
        assert page.locator("#scroller").evaluate("e=>e.scrollHeight>e.clientHeight")
        page.locator("#scroller").evaluate("e=>e.scrollTop=150")
        assert page.locator("#scroller").evaluate("e=>e.scrollTop")==150
        browser.close()


def test_connect_agent_pill_has_one_rim_but_no_extra_oval_at_native_pixels():
    """Regression for the white horseshoe observed at 100% in Phase 2 frame 75."""
    import numpy as np
    cue={"text":"Connect Agent","outputStartMs":0,"outputEndMs":1200,
         "box":{"x":390,"y":210,"width":200,"height":45}}
    frame=np.full((1080,1920,3),38,dtype=np.uint8)
    KineticCalloutRenderer([cue],fps=60).draw(
        frame,11,1.,0.,0.,(0.,0.),(220,124,1480,832),1200.)
    # Pill top is y=244 with a retained 1px luminous border. The interior
    # y=245..251 must remain dark; the old 180-342° specular arc polluted it.
    assert np.mean(frame[244,620:800]) > 100
    assert not np.any(frame[245:252,620:800].mean(axis=2)>75)
    assert np.max(frame[260:290,620:800])>180  # Label remains legible.
