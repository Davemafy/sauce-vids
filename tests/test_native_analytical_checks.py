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

@pytest.mark.parametrize("unexpected",[False,True])
def test_exact_popup_close_animation_not_confused_with_new_dialog(monkeypatch,unexpected):
    monkeypatch.setenv("SAUCE_CURIOUS_ANALYTICS","1")
    monkeypatch.setattr("backend.native_analytical_checks.assert_local",lambda p,u:None)
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path=CHROME,headless=True,args=["--no-sandbox"])
        try:
            p=b.new_page()
            p.set_content("""<button type=button aria-label="Date range" aria-haspopup=dialog onclick="document.getElementById('popup').hidden=false">Last 30 days</button>
            <div role=dialog id=popup hidden><button type=button role=option aria-selected=false>Today</button></div>
            <div role=dialog id=other hidden>Unrelated dialog</div>""")
            p.evaluate("""unexpected=>{
              document.querySelector('[role=option]').onclick=()=>{
                document.querySelector('button[aria-label]').innerText='Today';
                if(unexpected)document.getElementById('other').hidden=false;
                setTimeout(()=>document.getElementById('popup').hidden=true,100);
              };
            }""",unexpected)
            if unexpected:
                with pytest.raises(ValueError,match="Unexpected dialog"):
                    apply_preset(p,"https://example.com","Date range","Today",lambda loc,label:loc.click())
                assert p.locator('#other').is_visible()
            else:
                assert apply_preset(p,"https://example.com","Date range","Today",lambda loc,label:loc.click())=="Date range"
        finally:b.close()
