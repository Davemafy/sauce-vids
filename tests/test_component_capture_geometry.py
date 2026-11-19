"""Isolated browser geometry tests for source-true UI component capture.

Does not reach any external website or use production browser contexts.
"""
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright

from backend.product_explorer import CHROME
from backend.live_capture import COMPONENT_RECT_JS,prepare_slider_component_view


@pytest.fixture
def page():
    if not Path(CHROME).is_file():
        pytest.skip("Existing Playwright Chromium is not installed")
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=CHROME,
                                    args=["--no-sandbox","--disable-dev-shm-usage"])
        try:
            p=browser.new_page(viewport={"width":1920,"height":1080})
            yield p
        finally:
            browser.close()


def _fixture_html(decorated=True):
    style=("border:1px solid #888;border-radius:16px;"
           if decorated else "border:0;border-radius:0;")
    return f"""<html><body style="margin:0;height:2200px;background:#111;color:white">
    <div style="position:absolute;top:360px;left:344px;width:1232px;height:850px">
      <div style="margin:6px auto 0;width:672px;height:52px">
        <div style="height:20px"><input type="range" aria-label="email volume" min="0" max="100"
                          value="20" style="width:672px;height:20px"></div>
      </div>
      <div style="display:flex;margin-top:48px;gap:12px">
        <div style="width:299px;height:658px"></div>
        <div id="card" style="{style}box-sizing:border-box;width:299px;height:658px;
             padding:20px">
          <strong>Pro</strong>
          <div style="margin-top:84px"><span id="price">$20 / mo</span></div>
          <div style="margin-top:220px">Features and CTA</div>
        </div>
      </div>
    </div></body></html>"""


def test_viewport_prepares_full_decorated_component(page):
    page.set_content(_fixture_html())
    original=page.evaluate("scrollY")
    delta=prepare_slider_component_view(page,page.locator('input[type=range]'))
    assert delta>0
    assert page.evaluate("scrollY")>original
    component=page.locator("#price").evaluate(COMPONENT_RECT_JS)
    assert component is not None
    assert 297<component["width"]<301
    assert 656<component["height"]<660
    assert component["y"]>=0 and component["y"]+component["height"]<=1080


def test_non_component_text_does_not_get_promoted(page):
    page.set_content(_fixture_html(decorated=False))
    # Absence of borders/background means no genuine isolated card boundary.
    page.evaluate("window.scrollTo(0,120)")
    assert page.locator("#price").evaluate(COMPONENT_RECT_JS) is None
