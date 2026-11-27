import json,pytest
from playwright.sync_api import sync_playwright
from backend.product_explorer import CHROME
from backend import customer_observed_workspace as c,customer_story as s
HTML='''<style>body{margin:0}main{margin:600px auto;width:1400px}.workspace{width:1350px;height:720px}.toolbar{height:65px;display:flex;align-items:center;gap:20px}button{padding:12px}svg{display:block;width:1000px;height:500px}</style><main><article class=workspace><div class=toolbar><span>Chart type</span><div><button type=button>Bar</button><button type=button>Line</button><button type=button>Pie</button><button type=button>Export</button></div></div><section><span>Live preview</span><p>Nothing leaves your browser</p><svg viewBox="0 0 1000 500"><rect id=plot width=1000 height=500 fill="#777"/></svg></section></article></main><script>document.querySelectorAll('button').forEach(b=>b.onclick=()=>plot.setAttribute('fill',b.innerText==='Line'?'#124578':'#ba8722'))</script>'''
@pytest.fixture
def page(monkeypatch):
    monkeypatch.setattr(c,'assert_local',lambda *a:None);monkeypatch.setattr(s,'assert_local',lambda *a:None)
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path=CHROME,headless=True,args=['--no-sandbox']);p=b.new_page(viewport={'width':s.W,'height':s.H});p.set_content(HTML);yield p;b.close()
def test_observed_workspace_real_replay_and_proof(page):
    setup=c.prepare(page,'https://example.com/editor');assert setup
    rows=c.catalog(page,setup);assert [r['label'] for r in rows]==['Bar','Line','Pie']
    actions=rows[1:];assert s.validated_selection(json.dumps({'ids':[r['id'] for r in actions],'story':'Compare sample charts','hero_action_id':actions[-1]['id']}),rows)
    for a in actions:
        old=s.action_panel(page,a);before=s.shot(page);s.apply(page,'https://example.com/editor',a,None,lambda e,_:e.click());assert s.verify(page,'https://example.com/editor',before,old,s.shot)[2]>.9
    page.set_content(HTML);assert c.prepare(page,'https://example.com/editor',setup)==setup
    assert c.catalog(page,setup)==rows

def test_requires_local_statement_and_no_forms(page):
    page.set_content(HTML.replace('Nothing leaves your browser','Your data'));assert not c.prepare(page,'https://example.com/editor')
    page.set_content(HTML.replace('<div class=toolbar>','<form class=toolbar>').replace('</div></div><section>','</div></form><section>'));assert not c.prepare(page,'https://example.com/editor')

def test_no_invented_target_or_ambiguous_identity(page):
    setup=c.prepare(page,'https://example.com/editor');a=c.catalog(page,setup)[1]
    with pytest.raises(ValueError):c.locate(page,{**a,'label':'Invented'})
    page.locator('button').nth(2).evaluate("e=>e.innerText='Line'")
    with pytest.raises(ValueError):c.locate(page,a)
