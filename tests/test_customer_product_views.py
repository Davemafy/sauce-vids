"""Real Chromium fixtures for independent in-product view discovery."""
import json
import pytest
from playwright.sync_api import sync_playwright
from backend.product_explorer import CHROME
from backend import customer_story as s

HTML="""
<style>
body {margin:0;font:20px sans-serif}
section {position:absolute;top:80px;width:860px;height:920px;}
section:first-of-type {left:50px} section:nth-of-type(2) {left:990px}
[role=tabpanel] {width:850px;height:740px;padding:8px;box-sizing:border-box}
button {padding:14px}
#traffic0,#devices0 {background:#ececec}
#traffic1 {background:#4683ad} #devices1 {background:#a7c874}
[hidden] {display:none!important}
</style>
<main>
<section>
<h2 id="traffic-title">Acquisition analysis</h2>
<div role="tablist" aria-labelledby="traffic-title">
<button role="tab" aria-selected="true" aria-controls="traffic0">Overview</button>
<button role="tab" aria-selected="false" aria-controls="traffic1">Campaigns</button>
</div>
<div role="tabpanel" id="traffic0">Visitors by channel</div>
<div role="tabpanel" id="traffic1" hidden>Campaign conversion results</div>
</section>
<section>
<div role="tablist" aria-label="Audience analysis">
<button role="tab" aria-selected="true" aria-controls="devices0">Overview</button>
<button role="tab" aria-selected="false" aria-controls="devices1">Devices</button>
</div>
<div role="tabpanel" id="devices0">Audience summary</div>
<div role="tabpanel" id="devices1" hidden>Mobile and desktop audience</div>
</section>
</main>
<nav><div role="tablist" aria-label="Navigation">
<button role="tab" aria-selected="false" aria-controls="other">Marketing</button>
</div></nav>
<script>
document.addEventListener('click',e=>{
 if(e.target.getAttribute('role')!=='tab')return;
 const group=e.target.closest('[role=tablist]');
 for(const t of group.querySelectorAll('[role=tab]')){
  t.setAttribute('aria-selected',String(t===e.target));
  const panel=document.getElementById(t.getAttribute('aria-controls'));
  if(panel)panel.hidden=t!==e.target;
 }
});
</script>
"""

@pytest.fixture
def page(monkeypatch):
    monkeypatch.setattr(s,"assert_local",lambda *args:None)
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path=CHROME,headless=True,args=["--no-sandbox"])
        p=b.new_page(viewport={"width":s.W,"height":s.H})
        p.set_content(HTML)
        yield p
        b.close()

def test_independent_views_verified_in_connected_sequence(page):
    catalog=s.product_tab_catalog(page)
    assert [(a["group"],a["label"]) for a in catalog]==[
        ("View: Acquisition analysis","Campaigns"),("View: Audience analysis","Devices")]
    raw=json.dumps({"ids":[a["id"] for a in catalog],"hero_action_id":catalog[0]["id"],"story":"Compare acquisition and audience"})
    plan=s.validated_selection(raw,catalog)
    assert plan and plan["actions"]==catalog
    for a in catalog:
        before=s.shot(page);old=s.action_panel(page,a)
        s.apply(page,"https://example.com/demo",a,None,lambda loc,_:loc.click())
        after,box,delta,t=s.verify(page,"https://example.com/demo",before,old,s.shot)
        assert delta>.9 and box["width"]>=800
    assert page.locator("#traffic1").is_visible() and page.locator("#devices1").is_visible()

def test_group_identity_and_nonoverlap_are_required(page):
    catalog=s.product_tab_catalog(page)
    a=catalog[0]
    page.locator('[role=tablist]').first.evaluate("e=>{e.removeAttribute('aria-labelledby');e.setAttribute('aria-label','Different')}")
    with pytest.raises(s.StoryRejected,match="group changed"):
        s.action_panel(page,a)
    page.locator('section').nth(1).evaluate("e=>e.style.left='600px'")
    assert s.product_tab_catalog(page)==[]

def test_same_group_and_unbound_tabs_cannot_replace_product_action(page):
    rows=s.product_tab_catalog(page)
    raw=json.dumps({"ids":[a["id"] for a in rows],"hero_action_id":rows[0]["id"],"story":"A navigation tour"})
    assert s.validated_selection(raw,[rows[0],{**rows[1],"group":rows[0]["group"]}]) is None
    assert s.validated_selection(raw,[{k:v for k,v in a.items() if k!="control"} for a in rows]) is None
    page.locator('[aria-label="Audience analysis"]').evaluate("e=>e.setAttribute('aria-label','Account')")
    assert len(s.product_tab_catalog(page))==1

def test_discovery_does_not_require_picker_for_independent_views(page,tmp_path,monkeypatch):
    from contextlib import contextmanager
    from unittest.mock import Mock
    @contextmanager
    def browser(url,**kwargs):
        yield page
    url="https://example.com/demo"
    monkeypatch.setenv("SAUCE_CUSTOMER_DIRECTOR_PROVIDER","claude")
    monkeypatch.setattr(s,"resolve_public_product_entry",lambda *a:url)
    monkeypatch.setattr(s,"browser",browser)
    monkeypatch.setattr(s,"analytic_triggers",lambda *a:[])
    monkeypatch.setattr(s,"scan_radio_menus",lambda *a:[])
    monkeypatch.setattr(s,"discover",lambda *a:[])
    monkeypatch.setattr("backend.customer_combobox.prepare",lambda *a:None)
    conv=Mock();conv.calls=0
    monkeypatch.setattr("backend.claude_customer_director.ClaudeConversation",lambda *a,**k:conv)
    def compare(catalog,metadata,opening,out,conversation,creative):
        assert len(catalog)==2 and metadata["picker"] is None
        return "test model fixture",catalog
    monkeypatch.setattr(s,"compare_outcomes",compare)
    monkeypatch.setattr(s,"investigate_story",lambda raw,catalog,metadata,*a:(catalog,0,[]))
    result,calls,proofs=s.explore(url,tmp_path/"job",lambda _:None,request=Mock())
    assert len(result)==2 and calls==0 and proofs==[]
    assert json.loads((tmp_path/"job"/"discovery.json").read_text())["kind"]=="named-product-views"



def test_icon_only_accessible_view_names_are_replayable(page):
    page.locator('[aria-controls="traffic1"]').evaluate("e=>{e.innerText='';e.setAttribute('aria-label','Campaigns');e.style.minWidth='60px'}")
    page.locator('[aria-controls="devices1"]').evaluate("e=>{const n=document.createElement('span');n.id='device-label';n.hidden=true;n.textContent='Devices';document.body.append(n);e.innerText='';e.setAttribute('aria-labelledby',n.id);e.style.minWidth='60px'}")
    rows=s.product_tab_catalog(page)
    assert [a["label"] for a in rows]==["Campaigns","Devices"]
    for a in rows:
        old=s.action_panel(page,a);before=s.shot(page)
        s.apply(page,"https://example.com/demo",a,None,lambda loc,_:loc.click())
        assert s.verify(page,"https://example.com/demo",before,old,s.shot)[2]>.9


def test_accessible_name_cannot_disguise_unsafe_tab(page):
    page.locator('[aria-controls="traffic1"]').evaluate("e=>e.setAttribute('aria-label','Delete account')")
    assert [a["label"] for a in s.product_tab_catalog(page)]==["Devices"]
