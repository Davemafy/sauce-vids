"""Controlled executor benchmark v1. Scripted choices, NOT model accuracy.
All documents are synthetic and fulfilled inside Chromium; no external traffic.
"""
from contextlib import contextmanager
import argparse,json,time
from pathlib import Path
from playwright.sync_api import sync_playwright
from backend.product_explorer import CHROME
from backend import customer_browser_agent as agent,customer_story as story

BASE="https://benchmark.example.com"
STYLE='<style>body{margin:0;font:22px sans-serif}header{height:90px}button{padding:18px}section{width:1200px;height:650px;background:#ddd}ol{display:flex;gap:30px;height:50px;list-style:none}</style>'
NORMAL='<main><header><button type=button onclick="change(1)">Show trends</button><button type=button onclick="change(2)">View breakdown</button></header><section aria-label="Results" id="result">Starting result</section></main><script>function change(n){result.style.background=n===1?"#245587":"#773355";result.textContent=n===1?"Trend result":"Breakdown result"}</script>'
STEP='<div><ol><li><button type=button aria-current=step>Choose sample</button></li><li><button type=button>Inspect schema</button></li><li><button type=button>Use the app</button></li></ol><article style="width:1200px;height:650px;background:#ddd">Sample table</article><p>The demo runs in your browser with sample data. Nothing is saved or sent.</p></div><script>document.querySelectorAll("button").forEach((b,i)=>b.onclick=()=>{document.querySelectorAll("button").forEach(n=>n.removeAttribute("aria-current"));b.setAttribute("aria-current","step");let r=document.querySelector("article");r.style.background=i===1?"#225588":"#773355";r.textContent=b.textContent})</script>'
# Fixed choices represent a perfect goal-directed planner, not an LLM.
# Unsupported operations remain in the denominator, with no real forms submitted.
CASES=[
 ("connected_views",NORMAL,[("click","Show trends"),("click","View breakdown")],["Show trends","View breakdown"],"Breakdown result"),
 ("observed_entry",'<main><a href="/demo">Interactive demo</a></main>',[("navigate","Interactive demo"),("click","Show trends"),("click","View breakdown")],["Show trends","View breakdown"],"Breakdown result"),
 ("scroll_to_workspace",'<div style="height:540px">Intro</div>'+NORMAL,[("scroll_down",None),("click","Show trends"),("click","View breakdown")],["Show trends","View breakdown"],"Breakdown result"),
 ("local_sample_steps",STEP,[("click","Inspect schema"),("click","Use the app")],["Inspect schema","Use the app"],"Use the app"),
 ("offscreen_sample_steps",'<div style="height:540px">Intro</div>'+STEP,[("scroll_down",None),("click","Inspect schema"),("click","Use the app")],["Inspect schema","Use the app"],"Use the app"),
 ("invalid_id_recovery",NORMAL,[("invalid",None),("click","Show trends"),("click","View breakdown")],["Show trends","View breakdown"],"Breakdown result"),
 ("no_op_recovery",NORMAL.replace("<header>",'<header><button type=button>Show summary</button>'),[("click","Show summary"),("click","Show trends"),("click","View breakdown")],["Show trends","View breakdown"],"Breakdown result"),
 ("native_select",'<main><label>Chart style <select onchange="result.textContent=this.value"><option>Table</option><option>Scatter</option></select></label><section id=result aria-label="Results">Table</section></main>',[("select","Chart style")],[],"Scatter"),
 ("sample_text_input",'<main><label>Sample title <input oninput="result.textContent=this.value"></label><section id=result aria-label="Results">Initial</section></main>',[("type","Sample title")],[],"Example project"),
 ("canvas_drag",'<main><canvas width=1200 height=650 aria-label="Drawing canvas"></canvas><section id=result aria-label="Results">No drawing</section></main><script>let start=null;const c=document.querySelector("canvas"),ctx=c.getContext("2d");c.onpointerdown=e=>{start=[e.offsetX,e.offsetY]};c.onpointerup=e=>{if(start&&Math.hypot(e.offsetX-start[0],e.offsetY-start[1])>20){ctx.beginPath();ctx.moveTo(...start);ctx.lineTo(e.offsetX,e.offsetY);ctx.stroke();result.textContent="Drawing created"}start=null}</script>',[("drag","Drawing canvas")],[],"Drawing created"),
]
class Robots:
    def can_fetch(self,agent,url):return url.startswith(BASE+"/")
class ScriptedPlanner:
    calls=0
    def __init__(self,choices):self.choices=choices
    def ask(self,prompt,**kw):
        obs=json.loads(prompt.split(" Current public DOM observation: ",1)[1]); i=self.calls;self.calls+=1
        if i>=len(self.choices):return json.dumps({"operation":"finish"})
        op,label=self.choices[i]
        if op=="invalid":return json.dumps({"operation":"click","target":"e999"})
        row=next((x for x in obs["elements"] if x["name"]==label),{})
        return json.dumps({"operation":op,"target":row.get("id"),"distance":360,
            "region":row.get("result_region") or next((r["id"] for r in obs["result_regions"]),None),
            "value":{"select":"Scatter","type":"Example project"}.get(op),
            "gesture":{"from":[100,100],"to":[300,300]} if op=="drag" else None})

def evaluate(out):
    results=[]
    for name,html,choices,expected,final in CASES:
        state={}; start=time.monotonic()
        @contextmanager
        def browser(url,include_robots=False):
            with sync_playwright() as pw:
                b=pw.chromium.launch(executable_path=CHROME,headless=True,args=["--no-sandbox"])
                p=b.new_page(viewport={"width":story.W,"height":story.H})
                p.route("**/*",lambda r:r.fulfill(status=200,content_type="text/html",body=STYLE+(NORMAL if r.request.url==BASE+"/demo" and name=="observed_entry" else html)) if r.request.url in (BASE+"/",BASE+"/demo") else r.abort())
                p.goto(url)
                try:yield p,Robots()
                finally:
                    state["final_text"]=p.locator("section,article").first.inner_text() if p.locator("section,article").count() else ""
                    b.close()
        planner=ScriptedPlanner(choices)
        row={"case":name,"planner":"scripted"}
        try:
            graph=agent.run(BASE+"/",out/name,planner,browser,story.shot,story.media,story.verify)
            got=[a["label"] for a in graph["actions"]]
            row.update(verified_actions=got,expected_actions=expected,final_state=state.get("final_text"),step_statuses=[s["status"] for s in graph["steps"]])
            row["goal_reached"]=state.get("final_text")==final
            row["pass"]=got==expected and row["goal_reached"]
        except Exception as exc:
            row.update(error=type(exc).__name__);row["pass"]=False;row["goal_reached"]=False
        row.update(decisions=planner.calls,elapsed_seconds=round(time.monotonic()-start,3))
        results.append(row)
        print(json.dumps(row),flush=True)
    receipt={"schema":"sauce-controlled-executor-benchmark-v1","model_calls":0,"planner":"scripted","completed":sum(r["pass"] for r in results),"total":len(results),"goal_reached":sum(r["goal_reached"] for r in results),"results":results}
    (out/"summary.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print("COMPLETE",receipt["completed"],"/",receipt["total"])
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True);a=p.parse_args()
    a.out.mkdir(mode=0o700,parents=True,exist_ok=False);evaluate(a.out)
