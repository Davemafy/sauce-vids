import pytest
from playwright.sync_api import sync_playwright
from backend.product_explorer import CHROME
from backend import customer_local_views as local
from backend import customer_story as story

HTML="""
<style>
body{margin:0;font:20px sans-serif;min-height:2000px}
[role=region]{margin:500px auto 0;width:1200px;height:760px;background:#eee;padding:20px;box-sizing:border-box}
[role=group],[role=tablist]{height:55px}button{padding:12px}
#result{height:550px;background:#cddddd}
</style>
<div role=region aria-label="Analytics interactive demo">
<div role=group aria-label="Business unit">
<button type=button aria-pressed=true>All</button>
<button type=button aria-pressed=false>Services</button>
</div>
<div role=tablist>
<button type=button role=tab aria-selected=true>Summary</button>
<button type=button role=tab aria-selected=false>Details</button>
</div>
<div id=result>Sample analytics</div>
</div>
<script>
document.addEventListener('click',e=>{
 const g=e.target.closest('[role=group],[role=tablist]');
 if(!g)return;const state=g.getAttribute('role')==='group'?'aria-pressed':'aria-selected';
 for(const b of g.querySelectorAll('button['+state+']'))b.setAttribute(state,String(b===e.target));
 if(e.target.innerText==='Services')result.style.background='#226699';
 if(e.target.innerText==='Details')result.style.background='#aa7722';
});
</script>
"""
@pytest.fixture
def page(monkeypatch):
    monkeypatch.setattr(local,"assert_local",lambda *a:None)
    monkeypatch.setattr(story,"assert_local",lambda *a:None)
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path=CHROME,headless=True,args=["--no-sandbox"])
        p=b.new_page(viewport={"width":story.W,"height":story.H});p.set_content(HTML)
        yield p
        b.close()

def test_real_local_filter_then_view_result(page):
    setup=local.prepare(page,"https://example.com/demo")
    assert setup=={"kind":"local-demo-views","region":"Analytics interactive demo"}
    rows=local.catalog(page,setup)
    assert {a["label"] for a in rows}=={"Services","Details"}
    assert page.evaluate("scrollY")>0
    for a in rows:
        before=story.shot(page);old=story.action_panel(page,a)
        story.apply(page,"https://example.com/demo",a,None,lambda e,_:e.click())
        after,box,d,t=story.verify(page,"https://example.com/demo",before,old,story.shot)
        assert d>.8 and box["height"]>=500
    assert page.get_by_role("button",name="Services").get_attribute("aria-pressed")=="true"
    assert page.get_by_role("tab",name="Details").get_attribute("aria-selected")=="true"

def test_control_only_change_is_not_product_evidence(page):
    page.evaluate("""()=>document.addEventListener('click',e=>{if(e.target.innerText==='Services')result.style.background='#cddddd'})""")
    setup=local.prepare(page,"https://example.com/demo")
    a=local.catalog(page,setup)[0];before=story.shot(page);old=story.action_panel(page,a)
    story.apply(page,"https://example.com/demo",a,None,lambda e,_:e.click())
    with pytest.raises(story.WeakVisualOutcome):
        story.verify(page,"https://example.com/demo",before,old,story.shot)

def test_unsafe_or_ambiguous_groups_fail_closed(page):
    page.locator('[role=group]').evaluate("e=>e.setAttribute('aria-label','Account')")
    assert local.candidate(page) is None
    page.locator('[role=group]').evaluate("e=>e.setAttribute('aria-label','Business unit')")
    page.get_by_role("button",name="Services").evaluate("e=>e.setAttribute('aria-pressed','true')")
    assert local.candidate(page) is None

def test_invented_or_replayed_selected_action_rejected(page):
    setup=local.prepare(page,"https://example.com/demo");a=local.catalog(page,setup)[0]
    with pytest.raises(ValueError):
        local.locate(page,{**a,"label":"Invented"})
    local.apply(page,"https://example.com/demo",a,lambda e,_:e.click())
    with pytest.raises(ValueError):
        local.locate(page,a)

def test_setup_replays_in_real_browser(page):
    setup=local.prepare(page,"https://example.com/demo")
    page.evaluate("()=>window.scrollTo(0,0)")
    story.replay_setup(page,{"url":"https://example.com/demo","setup":setup})
    assert local.catalog(page,setup)
