import pytest
from playwright.sync_api import sync_playwright
from backend.product_explorer import CHROME
from backend import customer_semantic_capabilities as c,customer_story as s
HTML='''<style>body{margin:0;font:24px sans-serif}table{width:1400px;border-collapse:collapse;margin:70px auto}td{height:95px}button{font:inherit;padding:15px}tr:nth-child(odd){background:#eee}</style><main><table aria-label="Inventory"><thead><tr><th aria-sort="none"><button type=button>Stock</button></th><th aria-sort="none"><button type=button>Quantity</button></th></tr></thead><tbody><tr style="background:#223366;color:white"><td>Widget A</td><td>30</td></tr><tr style="background:#884433;color:white"><td>Widget C</td><td>10</td></tr><tr style="background:#336644;color:white"><td>Widget B</td><td>20</td></tr><tr style="background:#777722;color:white"><td>Widget D</td><td>40</td></tr></tbody></table></main><script>document.querySelectorAll('th button').forEach((b,i)=>b.onclick=()=>{const h=b.parentElement,body=document.querySelector('tbody');document.querySelectorAll('th').forEach(x=>x.setAttribute('aria-sort','none'));h.setAttribute('aria-sort','ascending');const rows=[...body.rows];rows.sort((a,b)=>a.cells[i].innerText.localeCompare(b.cells[i].innerText,undefined,{numeric:true}));rows.forEach(r=>body.append(r))})</script>'''
@pytest.fixture
def page(monkeypatch):
    monkeypatch.setattr(c,'assert_local',lambda *a:None);monkeypatch.setattr(s,'assert_local',lambda *a:None)
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path=CHROME,headless=True,args=['--no-sandbox']);p=b.new_page(viewport={'width':1920,'height':1080});p.set_content(HTML);yield p;b.close()
def test_semantic_sort_is_real_row_reordering(page):
    actions=c.catalog(page);assert len(actions)==2
    for a in actions:
        old=s.action_panel(page,a);before=s.shot(page);s.apply(page,'https://example.com/demo',a,None,lambda e,_:e.click());assert s.verify(page,'https://example.com/demo',before,old,s.shot)[2]>.1

def test_sort_rejects_no_row_change_and_guessed_identity(page):
    a=c.catalog(page)[0]
    with pytest.raises(ValueError):c.locate(page,{**a,'label':'Invented'})
    page.evaluate("()=>document.querySelector('th button').onclick=()=>document.querySelector('th').setAttribute('aria-sort','ascending')")
    with pytest.raises(ValueError,match='row reordering'):c.apply(page,'https://example.com/demo',a,lambda e,_:e.click())

def test_bound_view_toggle_has_disjoint_result(page):
    page.set_content('''<main><button type=button aria-pressed=false aria-controls="chart" onclick="this.setAttribute('aria-pressed','true');chart.style.background='#345678'">Toggle detail view</button><section id=chart aria-label="Chart" style="margin:20px;width:1200px;height:500px;background:#ddd">Chart data</section></main>''')
    a=c.catalog(page)[0];old=s.action_panel(page,a);before=s.shot(page);s.apply(page,'https://example.com/demo',a,None,lambda e,_:e.click());assert s.verify(page,'https://example.com/demo',before,old,s.shot)[2]>.8
    page.locator('button').evaluate("e=>e.innerText='Delete account'");assert not c.catalog(page)
