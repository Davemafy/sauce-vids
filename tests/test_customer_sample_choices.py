import pytest,json
from playwright.sync_api import sync_playwright
from backend.product_explorer import CHROME
from backend import customer_sample_choices as c,customer_story as s
HTML='''<style>body{margin:0}main{margin:1000px auto;width:1300px}section{height:720px}article{display:flex;width:1250px;height:560px}aside{width:250px}button{display:block;padding:14px}#result{flex:1;background:#ddd}</style><main><section><h2>Insights comparison</h2><p>Interactive sample data only</p><article><aside><button type=button aria-pressed=true>Overview</button><button type=button aria-pressed=false>Retention</button><button type=button aria-pressed=false>Acquisition</button></aside><div id=result>Sample results</div></article></section></main><script>document.addEventListener('click',e=>{if(!e.target.matches('button'))return;for(const b of document.querySelectorAll('button'))b.setAttribute('aria-pressed',String(b===e.target));result.style.background=e.target.innerText==='Retention'?'#225588':'#aa6622'})</script>'''
@pytest.fixture
def page(monkeypatch):
    monkeypatch.setattr(c,'assert_local',lambda *a:None);monkeypatch.setattr(s,'assert_local',lambda *a:None)
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path=CHROME,headless=True,args=['--no-sandbox']);p=b.new_page(viewport={'width':1920,'height':1080});p.set_content(HTML);yield p;b.close()
def test_observed_sample_comparison_and_result(page):
    setup=c.prepare(page,'https://example.com/demo');assert setup
    rows=c.catalog(page,setup);assert len(rows)==2
    for a in rows:
        before=s.shot(page);old=s.action_panel(page,a);s.apply(page,'https://example.com/demo',a,None,lambda e,_:e.click());assert s.verify(page,'https://example.com/demo',before,old,s.shot)[2]>.8
    assert s.validated_selection(json.dumps({'ids':[x['id'] for x in rows],'story':'Compare sample data','hero_action_id':rows[-1]['id']}),rows)
def test_no_sample_marker_or_form_no_admission(page):
    page.set_content(HTML.replace('Interactive sample data only','Interactive data'));assert not c.prepare(page,'https://example.com/demo')
    page.set_content(HTML.replace('<aside>','<form><aside>').replace('</aside>','</aside></form>'));assert not c.prepare(page,'https://example.com/demo')
def test_unsafe_and_invented_choices_not_clicked(page):
    setup=c.prepare(page,'https://example.com/demo');a=c.catalog(page,setup)[0]
    with pytest.raises(ValueError):c.locate(page,{**a,'label':'Delete account'})
    with pytest.raises(ValueError):c.locate(page,{**a,'label':'Invented'})
