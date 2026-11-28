"""Bounded native Browser Use on a caller-owned, public, guarded Chromium."""
import asyncio,json,os,sys,time
from pathlib import Path
from urllib.parse import urlsplit
from browser_use import Agent,Browser,ChatGoogle,Tools

async def main(path):
    c=json.loads(Path(path).read_text())
    endpoint=urlsplit(c['cdpUrl']);source=urlsplit(c['url'])
    if endpoint.scheme!='ws' or endpoint.hostname!='127.0.0.1' or source.scheme not in ('https','http'):
        raise ValueError('Expected private browser and public source')
    if c['model']!='google/gemini-3.1-flash-lite':raise ValueError('Gemini only')
    os.environ['ANONYMIZED_TELEMETRY']='false'
    b=Browser(cdp_url=c['cdpUrl'],keep_alive=True,viewport={'width':1920,'height':1080},device_scale_factor=2,
        allowed_domains=[source.hostname],captcha_solver=False,enable_default_extensions=False,highlight_elements=False,dom_highlight_elements=False,accept_downloads=False)
    llm=ChatGoogle(model='gemini-3.1-flash-lite',api_key=os.environ['GEMINI_API_KEY'],max_retries=1,max_output_tokens=3072,thinking_level='minimal')
    tools=Tools(exclude_actions=['search','upload_file','write_file','read_file','replace_file','save_as_pdf','evaluate','navigate','go_back','switch','close'])
    a=Agent(task=c['instruction'],llm=llm,browser=b,tools=tools,use_judge=False,max_actions_per_step=1,max_failures=2,step_timeout=35,llm_timeout=30,directly_open_url=False,enable_planning=False,calculate_cost=True,enable_signal_handler=False,final_response_after_failure=False, llm_screenshot_size=(1280,720))
    start=time.monotonic();out=Path(c['out']);out.mkdir(mode=0o700,exist_ok=False)
    async def step_end(agent):
        # Persist only operation names and clocks, not model reasoning, arguments, DOM or secrets.
        with (out/'steps.jsonl').open('a') as f:
            f.write(json.dumps({'epochMs':time.time()*1000,'step':agent.history.number_of_steps(),'actions':agent.history.action_names()[-1:]})+'\n')
    try:
        h=await asyncio.wait_for(a.run(max_steps=c['maxSteps'],on_step_end=step_end),timeout=c['timeoutMs']/1000)
        result={'reportedSuccess':h.is_successful(),'steps':h.number_of_steps(),'actions':h.action_names()}
    except Exception as e:result={'errorType':type(e).__name__}
    finally:
        result['elapsedSeconds']=time.monotonic()-start
        try:result['usage']=(await a.token_cost_service.get_usage_summary()).model_dump()
        except Exception:pass
        (out/'receipt.json').write_text(json.dumps(result,indent=2))
        await b.stop()
if __name__=='__main__':asyncio.run(main(sys.argv[1]))
