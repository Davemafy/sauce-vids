from contextlib import contextmanager
import json
import pytest
from playwright.sync_api import sync_playwright
from backend.product_explorer import CHROME
from backend import customer_browser_agent as agent,customer_story as story

HTML='''<style>body{margin:0;font:22px sans-serif}header{height:90px}button{padding:18px}section{width:1200px;height:650px;background:#ddd}</style><main><header><button type=button onclick="result.style.background='#245587'">Show trends</button><button type=button onclick="result.style.background='#773355'">View breakdown</button><button type=button>Open room session</button><a href="/demo">Interactive demo</a><a href="/auth/login">Log in</a><a href="https://elsewhere.example/demo">External demo</a></header><section aria-label="Results" id=result>Observed product result</section><p>Use the product</p></main>'''
class Robots:
    def can_fetch(self,agent,url):return '/blocked' not in url
@pytest.fixture
def page():
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path=CHROME,headless=True,args=['--no-sandbox']);p=b.new_page(viewport={'width':story.W,'height':story.H});p.route('https://example.com/**',lambda r:r.fulfill(status=200,content_type='text/html',body=HTML));p.goto('https://example.com/');yield p;b.close()

def test_broad_observation_separate_policy(page):
    public,targets,regions,image=agent.observation(page,Robots());assert image
    names={r['name']:r for r in public['elements']}
    assert names['Open room session']['allowed'] is None
    assert names['Log in']['allowed'] is None
    assert names['External demo']['allowed'] is None
    assert names['Interactive demo']['allowed']=='navigate'
    assert names['Show trends']['allowed']=='click'
    assert 'button' in names['Show trends']['computed_ax_roles']
    assert 'Use the product' in names and regions
    assert all('key' not in r and 'href' not in r for r in public['elements'])

def test_private_fields_and_sensitive_surfaces(page):
    page.locator('main').evaluate("e=>e.insertAdjacentHTML('beforeend','<input value=DO_NOT_SEND>')")
    public,_,_,image=agent.observation(page,Robots());assert 'DO_NOT_SEND' not in json.dumps(public);assert not image
    page.locator('main').evaluate("e=>e.insertAdjacentHTML('afterbegin','<div data-secret>SECRET</div>')")
    with pytest.raises(ValueError,match='Private'):agent.observation(page,Robots())

def test_agent_connected_actual_outcomes_and_replay(page,tmp_path):
    @contextmanager
    def browser(url,include_robots=False):yield page,Robots()
    class Gemini:
        calls=0
        def ask(self,prompt,**kw):
            obs=json.loads(prompt.split(' Current public DOM observation: ',1)[1]);self.calls+=1
            if self.calls>2:return json.dumps({'operation':'finish'})
            label=['Show trends','View breakdown'][self.calls-1]
            return json.dumps({'operation':'click','target':next(r['id'] for r in obs['elements'] if r['name']==label),'region':obs['result_regions'][0]['id']})
    r=agent.run(page.url,tmp_path/'scout',Gemini(),browser,story.shot,story.media,story.verify)
    assert len(r['actions'])==2 and r['actions'][1]['requires']==r['actions'][0]['id']
    assert all(p['delta']>.8 for p in r['proofs'])
    a=r['actions'];raw=json.dumps({'ids':[x['id'] for x in a],'story':'Inspect two real results','hero_action_id':a[-1]['id']});assert story.validated_selection(raw,a)
    page.reload()
    for action in a:
        before=story.shot(page);old=story.action_panel(page,action);story.apply(page,page.url,action,None,lambda h,l:h.click());assert story.verify(page,page.url,before,old,story.shot)[2]>.8
    with pytest.raises(ValueError):agent.locate(page,{**a[0],'label':'Invented'})

def test_invalid_target_cannot_execute(page,tmp_path):
    @contextmanager
    def browser(url,include_robots=False):yield page,Robots()
    class Gemini:
        calls=0
        def ask(self,prompt,**kw):
            self.calls+=1
            return json.dumps({'operation':'click','target':'e999'})
    r=agent.run(page.url,tmp_path/'scout',Gemini(),browser,story.shot,story.media,story.verify)
    assert r['calls']==4 and not r['actions'] and all(x['status']=='invalid-or-denied-target' for x in r['steps'])


def test_navigation_reobserves_destination_without_guessed_url(page,tmp_path):
    @contextmanager
    def browser(url,include_robots=False):
        page.goto(url);yield page,Robots()
    class Gemini:
        calls=0
        def ask(self,prompt,**kw):
            obs=json.loads(prompt.split(' Current public DOM observation: ',1)[1]);self.calls+=1
            if self.calls==1:
                assert obs['path']=='/'
                return json.dumps({'operation':'navigate','target':next(r['id'] for r in obs['elements'] if r['name']=='Interactive demo'),'url':'https://elsewhere.example/evil'})
            assert obs['path']=='/demo'
            return json.dumps({'operation':'finish'})
    r=agent.run(page.url,tmp_path/'scout',Gemini(),browser,story.shot,story.media,story.verify)
    assert r['url']=='https://example.com/demo' and r['calls']==2
    assert r['steps'][0]['status']=='navigated'


def test_navigation_closes_actual_sync_browser_before_opening_next(tmp_path):
    events=[]
    @contextmanager
    def fresh(url,include_robots=False):
        with sync_playwright() as pw:
            b=pw.chromium.launch(executable_path=CHROME,headless=True,args=['--no-sandbox'])
            p=b.new_page(viewport={'width':story.W,'height':story.H})
            p.route('https://example.com/**',lambda r:r.fulfill(status=200,content_type='text/html',body=HTML))
            p.goto(url);events.append(('open',url))
            try:yield p,Robots()
            finally:b.close();events.append(('close',url))
    class Model:
        calls=0
        def ask(self,prompt,**kw):
            self.calls+=1
            obs=json.loads(prompt.split(' Current public DOM observation: ',1)[1])
            if self.calls==1:return json.dumps({'operation':'navigate','target':next(r['id'] for r in obs['elements'] if r['name']=='Interactive demo')})
            assert obs['path']=='/demo'
            return json.dumps({'operation':'finish'})
    r=agent.run('https://example.com/',tmp_path/'scout',Model(),fresh,story.shot,story.media,story.verify)
    assert r['url']=='https://example.com/demo'
    assert events==[('open','https://example.com/'),('close','https://example.com/'),('open','https://example.com/demo'),('close','https://example.com/demo')]


def test_inspection_scroll_before_actions_is_replayable_opening(page,tmp_path):
    page.locator('main').evaluate("e=>e.insertAdjacentHTML('afterbegin','<div style=\"height:720px\">Intro</div>')")
    @contextmanager
    def browser(url,include_robots=False):yield page,Robots()
    class Model:
        calls=0
        def ask(self,prompt,**kw):
            self.calls+=1
            obs=json.loads(prompt.split(' Current public DOM observation: ',1)[1])
            if self.calls==1:return json.dumps({'operation':'scroll_down'})
            if self.calls==4:return json.dumps({'operation':'finish'})
            label=['Show trends','View breakdown'][self.calls-2]
            return json.dumps({'operation':'click','target':next(r['id'] for r in obs['elements'] if r['name']==label),'region':obs['result_regions'][0]['id']})
    r=agent.run(page.url,tmp_path/'scout',Model(),browser,story.shot,story.media,story.verify)
    assert r['setup']['kind']=='browser-agent-scroll' and r['setup']['y']>0
    assert len(r['actions'])==2
    page.evaluate('()=>window.scrollTo(0,0)')
    story.replay_setup(page,{'url':page.url,'setup':r['setup']})
    for a in r['actions']:
        before=story.shot(page);old=story.action_panel(page,a)
        story.apply(page,page.url,a,None,lambda h,l:h.click())
        assert story.verify(page,page.url,before,old,story.shot)[2]>.8
