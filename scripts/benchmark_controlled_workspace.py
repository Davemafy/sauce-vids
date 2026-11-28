"""Same ten synthetic goals as v1, but a separate offline action executor.
Scores are scripted goal completion only, not public-film or LLM acceptance.
"""
import argparse,json
from pathlib import Path
from backend.controlled_workspace_agent import run,BASE
from scripts.benchmark_browser_executor import CASES,STYLE,NORMAL,ScriptedPlanner

def evaluate(out):
    rows=[]
    for name,html,choices,_,final in CASES:
        docs={BASE:STYLE+html}
        if name=='observed_entry':docs[BASE+'demo']=STYLE+NORMAL
        try:
            receipt=run(docs,'Achieve '+final,ScriptedPlanner(choices),out/name)
            row={'case':name,'goal_reached':receipt['final_state']==final,
                 'state':receipt['final_state'],'decisions':receipt['decisions'],
                 'events':[e['status'] for e in receipt['events']],'seconds':receipt['elapsed_seconds']}
        except Exception as e:row={'case':name,'goal_reached':False,'error':type(e).__name__}
        rows.append(row);print(json.dumps(row),flush=True)
    summary={'planner':'scripted','model_calls':0,'goal_reached':sum(r['goal_reached'] for r in rows),'total':len(rows),'results':rows}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('GOAL',summary['goal_reached'],'/',summary['total'])
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    a.out.mkdir(mode=0o700,parents=True,exist_ok=False);evaluate(a.out)
