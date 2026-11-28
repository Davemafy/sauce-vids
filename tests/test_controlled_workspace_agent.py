import json
import pytest
from backend.controlled_workspace_agent import run,BASE
from scripts.benchmark_browser_executor import ScriptedPlanner

def test_only_supplied_synthetic_documents(tmp_path):
    with pytest.raises(ValueError):run({'https://example.com/':'hello'},'test',None,tmp_path/'x')

def test_forms_and_external_targets_not_exposed(tmp_path):
    class Planner:
        calls=0
        def ask(self,prompt,**kwargs):
            self.calls+=1
            obs=json.loads(prompt.split(' Current public DOM observation: ',1)[1])
            assert not obs['elements']
            return '{"operation":"finish"}'
    html='<form><input aria-label="Sample title"><button type="submit">Send</button></form><a href="https://outside.example/">Visit</a><section>Unchanged</section>'
    receipt=run({BASE:html},'Inspect controls',Planner(),tmp_path/'x')
    assert receipt['final_state']=='Unchanged'

def test_sensitive_surface_stops_before_planner(tmp_path):
    class Planner:
        def ask(self,*a,**k):raise AssertionError('No model call permitted')
    with pytest.raises(Exception,match='Sensitive surface'):
        run({BASE:'<input type="password"><section>Private</section>'},'Inspect',Planner(),tmp_path/'x')

def test_unknown_selection_not_executed(tmp_path):
    html='<label>Chart style<select onchange="document.querySelector(\'section\').textContent=this.value"><option>Table</option></select></label><section>Table</section>'
    receipt=run({BASE:html},'Change view',ScriptedPlanner([('select','Chart style')]),tmp_path/'x')
    assert receipt['final_state']=='Table'
    assert receipt['events'][0]['status']=='no-result-or-denied'
