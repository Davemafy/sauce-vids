"""Capture/replay cleanup and keyed procedural stage material regressions."""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from procedural_backdrops import procedural_backdrop, STYLES
from cinematic_stage import CinematicStage, _stage_base, MASTER_HEIGHT, MASTER_WIDTH
from session_capture import (MOCKUP_SCROLLBAR_STYLE, PRESENTATION_CLEANUP_STYLE,
                             PRESENTATION_WIDGET_STYLE, install_presentation_cleanup)


def test_three_materials_are_distinct_deterministic_and_style_cached():
    _stage_base.cache_clear()
    a, clip, ambient = _stage_base("fluted-glass")
    b, _, ambient_b = _stage_base("obsidian-grain")
    c, _, ambient_c = _stage_base("chromatic-bloom")
    assert a.shape == (1080, 1920, 3)
    assert ambient.shape == a.shape
    assert clip.shape == (832, 1480, 1)
    assert len({v.tobytes()[:700_000] for v in (ambient, ambient_b, ambient_c)}) == 3
    assert np.array_equal(_stage_base("fluted-glass")[0], a)
    assert _stage_base.cache_info().currsize == 3
    assert _stage_base.cache_info().hits >= 1
    assert float(ambient[:, :195].std()) > float(ambient_b[:, :195].std())
    assert float(ambient[:, :195].mean()) > float(ambient_b[:, :195].mean()) + 5
    assert int(ambient.max()) <= 66
    with pytest.raises(ValueError):
        procedural_backdrop("undefined")
    with pytest.raises(ValueError):
        CinematicStage(backdrop_style="undefined")


def test_procedural_stage_never_recolors_browser_pixels():
    browser = np.full((832, 1480, 3), (240, 234, 222), np.uint8)
    original = browser.copy()
    quiet = CinematicStage(backdrop_style="obsidian-grain").render(browser)
    textured = CinematicStage(backdrop_style="fluted-glass").render(browser)
    chromatic = CinematicStage(backdrop_style="chromatic-bloom").render(browser)
    assert np.array_equal(browser, original)
    # Within the H0 content rectangle the original UI remains pixel-identical.
    for frame in (quiet, textured, chromatic):
        assert np.array_equal(frame[390:740, 420:1450], original[266:616, 200:1230])
    assert np.any(quiet[:110] != textured[:110])
    assert np.any(textured[:110] != chromatic[:110])


def test_presentation_cleanup_includes_observed_chatwoot_not_just_aria_chat():
    assert "::-webkit-scrollbar" in MOCKUP_SCROLLBAR_STYLE
    assert '.woot-widget-bubble' in PRESENTATION_WIDGET_STYLE
    assert '#intercom-container' in PRESENTATION_CLEANUP_STYLE
    assert '.crisp-client' in PRESENTATION_CLEANUP_STYLE
    assert '#hubspot-messages-iframe-container' in PRESENTATION_CLEANUP_STYLE
    assert '[aria-label*="chat" i]' in PRESENTATION_CLEANUP_STYLE
    replay = (ROOT / "scripts/session_replay.py").read_text()
    capture = (ROOT / "scripts/session_capture.py").read_text()
    assert "install_presentation_cleanup(context)" in replay
    assert "install_presentation_cleanup(context)" in capture
    assert "page.add_style_tag(content=PRESENTATION_CLEANUP_STYLE)" in replay


@pytest.mark.skipif(os.environ.get("SAUCE_BROWSER_TEST") != "1",
                    reason="Enable actual HAR-backed Chromium on Vultr")
def test_chatwoot_cleanup_survives_brimble_hydration_and_frame_zero():
    from playwright.sync_api import sync_playwright
    source = ROOT / "studio/.tmp/brimble-reference-v16-ink"
    if not (source / "network.har").is_file():
        pytest.skip("Private verified Brimble HAR unavailable")
    session = json.loads((source / "session.json").read_text())
    executable = "/opt/devmcp-browsers/chromium_headless_shell-1254/chrome-headless-shell-linux64/chrome-headless-shell"
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=executable,
                                     args=["--no-sandbox", "--disable-dev-shm-usage"])
        try:
            context = browser.new_context(viewport={"width": 1280, "height": 720},
                                          device_scale_factor=2, service_workers="block")
            context.route_from_har(str(source / "network.har"),
                                   not_found="abort", update=False)
            install_presentation_cleanup(context)
            page = context.new_page()
            page.goto(session["source_url"], wait_until="domcontentloaded",
                      timeout=30000)
            page.wait_for_timeout(1250)  # Real Brimble widget mounts asynchronously.
            result = page.evaluate("""() => {
                const bubble = document.querySelector("button.woot-widget-bubble");
                return {mounted: !!bubble,
                  hidden: !!bubble && getComputedStyle(bubble).display === "none",
                  stylePresent: !!document.getElementById("sauce-presentation-cleanup"),
                  top: document.elementFromPoint(1240,674)?.className ?? ""};
            }""")
            assert result["mounted"], "Fixture must genuinely contain Chatwoot"
            assert result["stylePresent"] and result["hidden"], result
            assert "woot-widget-bubble" not in str(result["top"])
            # Explicitly verify React hydration did not discard the CSS rule.
            page.add_style_tag(content=PRESENTATION_CLEANUP_STYLE)
            assert page.locator("button.woot-widget-bubble").first.evaluate(
                "e=>getComputedStyle(e).display") == "none"
        finally:
            browser.close()


def test_obsidian_rms_ambient_glow_changes_stage_only():
    source=np.full((832,1480,3),(245,242,236),np.uint8)
    stage=CinematicStage(backdrop_style="obsidian-grain")
    cold=stage.render(source,glow=0.)
    hot=stage.render(source,glow=.9)
    assert np.any(hot[:100,:] > cold[:100,:]), "RMS must drive the ambient stage"
    assert np.array_equal(cold[390:740,420:1450],hot[390:740,420:1450])
