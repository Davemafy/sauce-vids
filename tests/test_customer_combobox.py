import pytest
from playwright.sync_api import sync_playwright
from backend.product_explorer import CHROME
from backend import customer_combobox as c
from backend import customer_story as story

@pytest.fixture
def page(monkeypatch):
    monkeypatch.setattr(c,"assert_local",lambda *args:None)
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path=CHROME,headless=True,args=["--no-sandbox"])
        p=b.new_page(viewport={"width":1920,"height":1080})
        p.set_content("""
        <style>
        body{margin:0}button{padding:12px}
        [role=tabpanel]{position:absolute;top:90px;left:30px;width:1300px;height:900px;background:#ddd}
        [role=dialog]{position:fixed;right:0;top:0;width:450px;height:1080px;background:white;padding:20px;box-sizing:border-box}
        [role=listbox]{position:fixed;right:40px;top:350px;width:350px;background:#ddd;z-index:5}
        [role=option]{padding:20px}
        </style>
        <button type=button aria-label="Theme customizer" aria-haspopup=dialog aria-expanded=false aria-controls=drawer onclick="this.setAttribute('aria-expanded','true');drawer.hidden=false">Customize</button>
        <div role=tabpanel id=product>Actual product</div>
        <div role=dialog id=drawer hidden>
          <div><label>Style</label><button type=button role=combobox aria-expanded=false aria-controls=choices onclick="openList(this)">Vega</button></div>
          <div><label>Theme</label><button type=button role=combobox aria-expanded=false aria-controls=choices onclick="openList(this)">Neutral</button></div>
          <div><label>Account</label><button type=button role=combobox aria-expanded=false aria-controls=choices>Private</button></div>
          <div inert><label>Font</label><button type=button role=combobox aria-expanded=false aria-controls=choices>Secret</button></div>
        </div>
        <div role=listbox id=choices hidden>
          <div role=option aria-selected=false onclick="pick(this)">Blue</div>
          <div role=option aria-selected=false onclick="pick(this)">Emerald</div>
          <div role=option aria-selected=false aria-disabled=true>Disabled</div>
          <div role=option aria-selected=false>Delete account</div>
        </div>
        <script>
        let active;
        function openList(e){active=e;e.setAttribute('aria-expanded','true');choices.hidden=false}
        function closeList(){if(active)active.setAttribute('aria-expanded','false');choices.hidden=true}
        function pick(e){active.innerText=e.innerText;product.style.background='green';closeList()}
        document.addEventListener('keydown',e=>{if(e.key==='Escape')closeList()})
        </script>
        """)
        yield p
        b.close()

def test_observed_controls_and_exact_replay(page):
    setup=c.prepare(page,"https://example.com/editor")
    assert setup=={"kind":"presentation-combobox-drawer","opener":"Theme customizer"}
    rows=c.catalog(page,"https://example.com/editor")
    assert {(a["group"],a["label"]) for a in rows}=={("Style","Blue"),("Style","Emerald"),("Theme","Blue"),("Theme","Emerald")}
    before=story.action_panel(page,rows[0])
    assert before["combo_result_id"]=="product" and before["width"]>=1200
    story.apply(page,"https://example.com/editor",rows[0],None,lambda e,_:e.click())
    assert c.handle(page,rows[0]["group"]).inner_text()==rows[0]["label"]
    assert story.result_panel(page,before)==before

def test_arbitrary_opener_and_unobserved_value_fail_closed(page):
    page.locator('button[aria-label]').evaluate("e=>e.setAttribute('aria-label','Purchase')")
    assert c.prepare(page,"https://example.com/editor") is None
    page.locator('button[aria-label]').evaluate("e=>e.setAttribute('aria-label','Theme customizer')")
    c.prepare(page,"https://example.com/editor")
    with pytest.raises(ValueError,match="no longer unique"):
        c.apply(page,"https://example.com/editor",{"group":"Theme","label":"Invented"},lambda e,_:e.click())

def test_setup_reproduced_not_invented(monkeypatch):
    setup={"kind":"presentation-combobox-drawer","opener":"Theme customizer"}
    monkeypatch.setattr(c,"prepare",lambda *args:None)
    with pytest.raises(story.StoryRejected,match="not reproduced"):
        story.replay_setup(None,{"setup":setup,"url":"https://example.com/editor"})
