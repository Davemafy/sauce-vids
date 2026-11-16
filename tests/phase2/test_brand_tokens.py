"""Brand-token ingestion: source authenticity, brightness and pixel isolation."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/"scripts"))

from brand_extractor import (extract_brand_tokens, normalize_brand_tokens,
                             validate_brand_tokens, stage_brand_colors)
from cinematic_stage import (CinematicStage, _stage_base,
                             brand_light_parameters, _ambient_pulse_field)
from procedural_backdrops import procedural_backdrop
from session_contract import verify_package


def _tokens(primary: str | None, accent: str | None,
            meta: bool = False) -> dict:
    return normalize_brand_tokens({
        "colors": {"primary": primary, "accent": accent,
                   "background": "#ffffff"},
        "provenance": {
            "primary": "meta:theme-color" if meta else "css:--primary",
            "accent": "css:--accent",
            "background": "css:--background"},
        "typography": {
            "body": {"family": "Inter, sans-serif", "sizePx": 16,
                     "weight": "400"},
            "heading": {"family": "Georgia, serif", "sizePx": 32,
                        "weight": "700"}}
    })


def test_validated_tokens_are_small_safe_and_stable():
    blue = _tokens("#2872d7", "#24a896")
    orange = _tokens("#eb6c18", "#b52c69")
    assert blue["colors"] != orange["colors"]
    assert blue["typography"]["heading"]["family"] == "Georgia, serif"
    assert validate_brand_tokens(blue) == blue
    assert validate_brand_tokens(orange) == orange
    assert stage_brand_colors(blue) == ("#2872d7", "#24a896")
    assert stage_brand_colors(normalize_brand_tokens({})) == (None, None)
    assert normalize_brand_tokens({
        "colors": {"primary": "url(https://example.com/private)",
                   "accent": "<secret>", "background": "not a color"},
        "typography": {"body": {"family": "url(https://bad.example/font)",
                                 "sizePx": 100000}}})["confidence"] == "fallback"
    invalid = dict(blue)
    invalid["colors"] = {"primary": "rgba(255,0,0,1)",
                         "accent": "#24a896", "background": "#ffffff"}
    with pytest.raises(ValueError, match="canonical"):
        validate_brand_tokens(invalid)
    no_accent = normalize_brand_tokens({
        "colors": {"primary": "#bc401e"},
        "provenance": {"primary": "css:--primary"}})
    assert no_accent["provenance"]["accent"] == "derived:primary"
    assert validate_brand_tokens(no_accent) == no_accent
    assert stage_brand_colors(no_accent) == ("#bc401e", "#bc401e")


def test_distinct_site_tokens_parameterize_light_without_clobbering_ui():
    _stage_base.cache_clear()
    from_blue = _tokens("#2872d7", "#24a896")
    from_orange = _tokens("#eb6c18", "#b52c69")
    blue = CinematicStage(backdrop_style="fluted-glass",
                          brand_primary=from_blue["colors"]["primary"],
                          brand_accent=from_blue["colors"]["accent"])
    orange = CinematicStage(backdrop_style="fluted-glass",
                            brand_primary=from_orange["colors"]["primary"],
                            brand_accent=from_orange["colors"]["accent"])
    source = np.full((832,1480,3), (230, 242, 249), np.uint8)
    old = CinematicStage(backdrop_style="fluted-glass")
    a = blue.render(source)
    b = orange.render(source)
    c = old.render(source)
    assert not np.array_equal(a[:112],b[:112])
    assert not np.array_equal(a[:112],c[:112])
    # The same original browser pixels are composited regardless of brand.
    original_rect = (slice(300,830),slice(450,1490))
    assert np.array_equal(a[original_rect],b[original_rect])
    assert np.array_equal(a[original_rect],c[original_rect])
    assert np.array_equal(source,np.full_like(source,(230,242,249)))
    assert np.array_equal(blue.render(source),a)
    # Source hue controls actual channel lighting, but the stage stays dark.
    for arr in (a,b):
        assert np.percentile(arr[:110],99) < 80
    rim_a,weights_a=brand_light_parameters("#2872d7","#24a896")
    rim_b,weights_b=brand_light_parameters("#eb6c18","#b52c69")
    assert (rim_a,weights_a)!=(rim_b,weights_b)
    assert all(.5<=v<=2. for v in weights_a+weights_b)
    assert all(195<=v<=255 for v in rim_a+rim_b)
    assert _stage_base.cache_info().currsize == 3


def test_all_backdrop_variants_use_brand_and_default_pixel_identity():
    primary,accent="#1ea5c9","#f08a27"
    for style in ("fluted-glass","chromatic-bloom","obsidian-grain"):
        a=procedural_backdrop(style,320,180,primary,accent)
        b=procedural_backdrop(style,320,180,primary,accent)
        neutral=procedural_backdrop(style,320,180)
        assert np.array_equal(a,b)
        assert not np.array_equal(a,neutral)
        assert int(a.max())<=66


@pytest.mark.skipif(os.environ.get("SAUCE_BROWSER_TEST")!="1",
                    reason="Requires a real headless Chromium browser")
def test_two_web_origins_yield_distinct_observed_tokens_and_typography():
    from playwright.sync_api import sync_playwright
    chrome="/opt/devmcp-browsers/chromium_headless_shell-1254/chrome-headless-shell-linux64/chrome-headless-shell"
    websites={
        "https://cobalt.test/": """<!doctype html><html><head>
          <style>:root{--primary:#2872d7;--accent:#24a896;--background:#f9fbff}
            body{font-family:Arial,sans-serif;font-size:16px}
            h1{font-family:Georgia,serif;font-weight:700;font-size:36px}
            button{background:#2872d7;color:white}</style></head>
            <body><h1>Cobalt</h1><button>Continue</button></body></html>""",
        "https://copper.test/": """<!doctype html><html><head>
          <meta name="theme-color" content="#eb6c18">
          <style>:root{--accent:#b52c69;--background:#fffafa}
          body{font-family:Tahoma,sans-serif;font-size:15px}
          h1{font-family:Georgia,serif;font-size:30px}
          button{background:#eb6c18;color:white}</style></head>
          <body><h1>Copper</h1><button>Get started</button></body></html>""",
    }
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=chrome,
                                   args=["--no-sandbox","--disable-dev-shm-usage"])
        try:
            context=browser.new_context(viewport={"width":1280,"height":720})
            context.route("**/*",lambda route: route.fulfill(
                status=200,content_type="text/html",
                body=websites[route.request.url]))
            seen=[]
            for url in websites:
                page=context.new_page()
                page.goto(url,wait_until="domcontentloaded")
                result=extract_brand_tokens(page)
                assert validate_brand_tokens(result)==result
                seen.append(result)
                page.close()
            assert seen[0]["colors"]["primary"]=="#2872d7"
            assert seen[1]["colors"]["primary"]=="#eb6c18"
            assert seen[0]["colors"]["accent"]=="#24a896"
            assert seen[1]["colors"]["accent"]=="#b52c69"
            assert seen[0]["typography"]["heading"]["sizePx"]==36.
            assert seen[1]["typography"]["body"]["sizePx"]==15.
            assert seen[0]["provenance"]["primary"]=="css:--primary"
            assert seen[1]["provenance"]["primary"]=="meta:theme-color"
            assert seen[0]["colors"]!=seen[1]["colors"]
            browser.close()
        finally:
            if browser.is_connected():browser.close()


@pytest.mark.skipif(os.environ.get("SAUCE_BROWSER_TEST")!="1",
                    reason="Requires local-browser capture")
def test_capture_persists_brand_snapshot_in_real_session(tmp_path):
    from session_capture import record
    page_file=tmp_path/"product.html"
    page_file.write_text("""<!doctype html><html><head>
        <style>:root{--primary:#1674c5;--accent:#d56735}
        body{font-family:Arial;font-size:16px}</style></head>
        <body><button>Start</button></body></html>""")
    folder=tmp_path/"capture"
    session=record(page_file.as_uri(),[{"action":"wait","ms":2,
                       "settle_ms":2}],folder,1280,720,2)
    stored=json.loads((folder/"session.json").read_text())
    assert session["brand_tokens"]==stored["brand_tokens"]
    assert stored["brand_tokens"]["colors"]["primary"]=="#1674c5"
    assert stored["brand_tokens"]["colors"]["accent"]=="#d56735"
    assert stored["brand_tokens"]["confidence"]=="observed"
    verify_package(stored,folder)


@pytest.mark.skipif(os.environ.get("SAUCE_BROWSER_TEST")!="1",
                    reason="Requires pinned Chromium color conversion")
def test_modern_oklch_and_hsl_custom_properties_resolve_to_srgb():
    from playwright.sync_api import sync_playwright
    chrome="/opt/devmcp-browsers/chromium_headless_shell-1254/chrome-headless-shell-linux64/chrome-headless-shell"
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=chrome,
                                   args=["--no-sandbox","--disable-dev-shm-usage"])
        try:
            page=browser.new_page()
            page.set_content("""<!doctype html><style>
               :root {--primary: oklch(62% 0.21 250);
                      --accent: 33 90% 53%; --background: #ffffff}
               body {font-family: Arial}</style><button>Action</button>""")
            tokens=extract_brand_tokens(page)
            assert tokens["confidence"]=="observed"
            assert tokens["provenance"]["primary"]=="css:--primary"
            assert tokens["provenance"]["accent"]=="css:--accent"
            p=[int(tokens["colors"]["primary"][i:i+2],16) for i in (1,3,5)]
            a=[int(tokens["colors"]["accent"][i:i+2],16) for i in (1,3,5)]
            assert p[2]>p[0] and p[2]>p[1],tokens
            assert a[0]>a[2] and a[0]>a[1],tokens
        finally:
            browser.close()
