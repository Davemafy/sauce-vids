from unittest.mock import Mock
import pytest
import backend.customer_story as s

def test_analytical_replay_retains_observed_picker_identity(monkeypatch):
    monkeypatch.setenv("SAUCE_CURIOUS_ANALYTICS","1")
    page,scope,trigger,option=Mock(),Mock(),Mock(),Mock()
    def open_(p,url,picker,click):
        assert picker=="Date range"
        click(trigger)
        return scope
    monkeypatch.setattr(s,"native_analytic_picker",open_)
    resolve=Mock(return_value=option)
    monkeypatch.setattr(s,"native_analytic_handle",resolve)
    monkeypatch.setattr(s,"dismiss_picker",Mock())
    monkeypatch.setattr(s,"assert_local",Mock())
    applied=Mock();monkeypatch.setattr(s,"assert_applied_option",applied)
    click=Mock()
    for label in ("Today","Last 7 days"):
        assert s.apply(page,"https://example.com/demo",{"kind":"option","label":label},"Date range",click)=="Date range"
        resolve.assert_called_with(scope,label,option=True)
        applied.assert_called_with(page,label,"Date range")
    assert click.call_count==4

def test_analytical_replay_rejects_custom_or_unobserved_unsafe_options(monkeypatch):
    monkeypatch.setenv("SAUCE_CURIOUS_ANALYTICS","1")
    open_=Mock();monkeypatch.setattr(s,"native_analytic_picker",open_)
    for label in ("Custom range","Delete","Last 1000 days"):
        with pytest.raises(s.StoryRejected,match="Unrecognized"):
            s.apply(Mock(),"https://example.com/demo",{"kind":"option","label":label},"Date range",Mock())
    open_.assert_not_called()

def test_tabs_are_in_viewport_and_hit_tested():
    from playwright.sync_api import sync_playwright
    from backend.product_explorer import CHROME
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path=CHROME,headless=True,args=["--no-sandbox"])
        try:
            p=b.new_page(viewport={"width":800,"height":600})
            p.set_content("""<div role="tablist">
              <button role="tab" aria-selected="false" aria-controls="p1">Campaigns</button>
              <button role="tab" aria-selected="false" aria-controls="p2" style="position:absolute;top:900px">Regions</button>
              <button role="tab" aria-selected="false" aria-controls="p3" style="position:absolute;left:250px;top:10px">Covered</button>
              <div style="position:absolute;left:245px;top:0;width:150px;height:60px;background:white"></div>
              </div>""")
            assert [name for name,_ in s.tabs(p)]==["Campaigns"]
            assert p.evaluate("scrollY")==0
        finally:b.close()
