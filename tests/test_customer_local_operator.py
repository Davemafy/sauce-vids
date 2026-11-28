from contextlib import contextmanager
import json
import pytest
from playwright.sync_api import sync_playwright
from backend import customer_browser_agent as agent,customer_story as story,customer_local_operator as op
from backend.product_explorer import CHROME

HTML="""<style>body{margin:0;font:22px sans-serif}button{padding:20px}article{width:1250px;height:650px;background:#ddd}</style><main><p>Interactive demo runs entirely in your browser with sample data.</p><button id=a>Forecast</button><button id=b hidden>Segment</button><button id=c>Send report</button><button id=d>Nothing</button><article id=result>Baseline</article></main><script>a.onclick=()=>{result.textContent='Forecast result';result.style.background='#245587';b.hidden=false;fetch('https://example.com/blocked').catch(()=>{})};b.onclick=()=>{result.style.background='#773355';result.textContent='Segment result'}</script>"""
class Robots:
    def can_fetch(self,*a):return True
@pytest.fixture
def browser():
    @contextmanager
    def run(url,include_robots=False):
        with sync_playwright() as pw:
            b=pw.chromium.launch(executable_path=CHROME,headless=True,args=['--no-sandbox'])
            p=b.new_page(viewport={'width':story.W,'height':story.H})
            p.route('**/*',lambda r:r.fulfill(status=200,content_type='text/html',body=HTML))
            p.goto(url)
            try:yield p,Robots()
            finally:b.close()
    return run

def test_connected_general_primitives_replay_and_guard(browser,tmp_path):
    class Model:
        calls=0
        def ask(self,prompt,**kw):
            self.calls+=1
            obs=json.loads(prompt.split(' Current public DOM observation: ',1)[1])
            if self.calls>2:return json.dumps({'selection':'finish','region':'none','reason':'done'})
            wanted=['Forecast','Segment'][self.calls-1]
            row=next(r for r in obs['trusted_actions'] if r['name']==wanted and r['capability']=='local-primitive')
            assert not any(r['name']=='Send report' for r in obs['trusted_actions'])
            return json.dumps({'selection':'investigate:'+row['id'],'region':'none','objective':'Explain forecast segmentation','expected':wanted+' result','reason':'advance'})
    url='https://example.com/demo'
    result=agent.run(url,tmp_path/'scout',Model(),browser,story.shot,story.media,story.verify)
    assert len(result['actions'])==2
    assert result['actions'][1]['requires']==result['actions'][0]['id']
    assert all(x['delta']>.85 for x in result['proofs'])
    assert result['steps'][0]['observed_result_text']=={
        'appeared':['Forecast result'],'disappeared':['Baseline']}
    assert result['steps'][1]['observed_result_text']=={
        'appeared':['Segment result'],'disappeared':['Forecast result']}
    assert story.validated_selection(json.dumps({'ids':[a['id'] for a in result['actions']],'story':'Forecast segmentation','hero_action_id':result['actions'][-1]['id']}),result['actions'])
    with browser(url) as (p,_):
        op.isolate(p)
        assert not p.evaluate('navigator.onLine')
        for action in result['actions']:
            old=story.action_panel(p,action);before=story.shot(p)
            story.apply(p,url,action,None,lambda h,l:h.click())
            assert story.verify(p,url,before,old,story.shot)[2]>.85
        assert p.locator('article').inner_text()=='Segment result'

def test_sensitive_and_noop_not_accepted(browser):
    url='https://example.com/demo'
    with browser(url) as (p,_):
        choices=op.primitives(p)
        assert 'Send report' not in [x['label'] for x in choices]
        a=next(x for x in choices if x['label']=='Nothing')
        op.isolate(p)
        old=story.action_panel(p,a);before=story.shot(p)
        story.apply(p,url,a,None,lambda h,l:h.click())
        with pytest.raises(story.WeakVisualOutcome):
            story.verify(p,url,before,old,story.shot)
        p.locator('main').evaluate("e=>e.insertAdjacentHTML('beforeend','<input type=password>')")
        assert op.primitives(p)==[]


def test_operator_restores_verified_prefix_after_weak_action(browser,tmp_path):
    class Model:
        calls=0

        def ask(self,prompt,**kwargs):
            observation=json.loads(prompt.split(' Current public DOM observation: ',1)[1])
            choices={row['name']:row['id'] for row in observation['trusted_actions']}
            self.calls+=1
            if self.calls==4:
                return json.dumps({'selection':'finish','region':'none'})
            if self.calls==3:
                assert 'Nothing' not in choices
            wanted=('Forecast','Nothing','Segment')[self.calls-1]
            return json.dumps({'selection':'investigate:'+choices[wanted],'region':'none'})

    url='https://example.com/demo'
    result=agent.run(url,tmp_path/'scout',Model(),browser,story.shot,story.media,story.verify)
    assert [a['label'] for a in result['actions']]==['Forecast','Segment']
    assert result['steps'][1]['status']=='weak-result-recovered'
    assert result['steps'][1]['restored_actions']==1
    assert result['actions'][1]['requires']==result['actions'][0]['id']



def test_delayed_result_is_verified_after_loading_state(browser):
    url='https://example.com/demo'
    with browser(url) as (page,_):
        page.locator('#a').evaluate("""button => {
            button.onclick=() => {
                result.textContent='Parsing';
                result.style.background='#cc5555';
                result.setAttribute('aria-busy','true');
                setTimeout(() => {
                    result.textContent='Completed report';
                    result.style.background='#245587';
                    result.removeAttribute('aria-busy');
                }, 1050);
            };
        }""")
        action=next(a for a in op.primitives(page) if a['label']=='Forecast')
        op.isolate(page)
        old=story.action_panel(page,action)
        before=story.shot(page)
        story.apply(page,url,action,None,lambda h,_:h.click())
        after,_,_,_=story.verify(page,url,before,old,story.shot)
        assert page.locator('#result').inner_text()=='Completed report'
        assert story.image_change(story.arr(after),story.arr(story.shot(page)))<.01
