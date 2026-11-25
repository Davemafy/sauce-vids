import pytest
from playwright.sync_api import sync_playwright
from backend.product_explorer import CHROME
from backend.native_analytical_checks import batch_panels,apply_preset

def test_batched_analytical_checks_preserve_real_dom_identity(monkeypatch):
    monkeypatch.setenv("SAUCE_CURIOUS_ANALYTICS","1")
    monkeypatch.setattr("backend.native_analytical_checks.assert_local",lambda p,u:None)
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path=CHROME,headless=True,args=["--no-sandbox"])
        try:
            p=b.new_page(viewport={"width":1000,"height":800})
            p.set_content("""<button type=button aria-label="Date range" aria-haspopup=dialog aria-expanded=false onclick="document.querySelector('#popup').style.display='block'">Last 30 days</button>
            <div id=popup role=dialog style="display:none"><button type=button role=option aria-selected=false onclick="document.querySelector('[aria-label=\'Date range\']')">Today</button></div>
            <main><section aria-label=Traffic style="width:600px;height:250px"></section></main>""")
            p.evaluate("""()=>{let opt=document.querySelector('[role=option]');opt.onclick=()=>{document.querySelector('button[aria-label]').innerText='Today';document.querySelector('#popup').style.display='none';}}""")
            assert batch_panels(p)[0]["id"]=="region:Traffic"
            assert apply_preset(p,"https://example.com","Date range","Today",lambda loc,label:loc.click())=="Date range"
            with pytest.raises(ValueError,match="Unrecognized"):
                apply_preset(p,"https://example.com","Date range","Custom range",lambda loc,label:loc.click())
            p.evaluate("""()=>{document.querySelector('#popup').insertAdjacentHTML('beforeend','<input type=password>')}""")
            with pytest.raises(ValueError,match="sensitive"):
                apply_preset(p,"https://example.com","Date range","Today",lambda loc,label:loc.click())
        finally:b.close()
