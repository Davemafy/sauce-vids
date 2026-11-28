"""Public native Stagehand capture pilot. Never admits authenticated sessions.

The existing Sauce network guard owns permissions; Stagehand owns decisions.
Raw footage and observations survive downstream failures. This is a research
capture path, not a customer film endpoint or a verified film manifest.
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, re, signal, subprocess, tempfile, time
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from playwright.sync_api import sync_playwright, Error
from backend.customer_story import native_display, customer_browser_args, W, H, D, read_robots
from backend.native60_capture import FULL_CHROME
from backend.source_action_preflight import visible_authentication_barrier, standalone_authentication_barrier
from scripts.capture_safety import validate_public_url, guard_route
ROOT=Path(__file__).resolve().parents[1]
BLOCKED_PATH=re.compile(r"(?:^|/)(?:logout|signout|sign-out|login|log-in|signin|sign-in|signup|sign-up|register|checkout|billing|payment|delete|invite|oauth)(?:/|$)",re.I)
OBSERVE=r"""()=>{
  const privateSelector='input[type=password],input[autocomplete=one-time-code],[data-private],[data-secret],[data-sensitive]';
  for(const kind of ['pointermove','pointerdown','pointerup','wheel','input','change'])document.addEventListener(kind,e=>{
    if(!e.isTrusted||e.target?.closest?.(privateSelector))return;
    const target=e.target?.closest?.('button,[role=button],[role=tab],a,input,select,textarea,canvas,[contenteditable=true]')||e.target;
    const r=target?.getBoundingClientRect?.();if(!r)return;
    const event={kind,t:performance.timeOrigin+performance.now(),tag:String(target.tagName||'').slice(0,16),rect:{x:r.x,y:r.y,width:r.width,height:r.height}};
    if(typeof e.clientX==='number'){event.x=e.clientX;event.y=e.clientY;}
    // Never read values, selectors, keystrokes, clipboard or field text.
    window.__sauceNativeObserved?.(event);
  },true);
}"""

def private_json(path,data):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as f:json.dump(data,f,indent=2);f.write('\n')

def public_scope(url):
    validate_public_url(url)
    p=urlsplit(url)
    return p.scheme,p.hostname,p.port or (443 if p.scheme=='https' else 80)

def guard_for(url):
    approved=public_scope(url)
    def guard(route):
        req=route.request
        if req.is_navigation_request():
            try:
                p=urlsplit(req.url);candidate=urlunsplit((p.scheme,p.netloc,p.path,'',''))
                if public_scope(candidate)!=approved or p.query or p.fragment or BLOCKED_PATH.search(p.path):return route.abort('blockedbyclient')
            except (ValueError,TypeError):return route.abort('blockedbyclient')
        return guard_route(route)
    return guard

def clean_env(display=None,*,inference=False):
    env={k:os.environ[k] for k in ('PATH','HOME','LANG','LC_ALL','TZ','XDG_RUNTIME_DIR') if k in os.environ}
    if display:env['DISPLAY']=display
    if inference:
        for k in ('GEMINI_API_KEY','GOOGLE_GENERATIVE_AI_API_KEY'):
            if os.environ.get(k):env[k]=os.environ[k]
    return env

def capture(url,objective,out,*,max_steps=12,timeout_seconds=85):
    from backend.agentmail_auth import test_session_active
    if test_session_active():raise ValueError('Native public pilot refuses authenticated sessions')
    public_scope(url)
    if not isinstance(objective,str) or not 1<=len(objective)<=2400 or not 1<=max_steps<=24 or not 15<=timeout_seconds<=150:raise ValueError('Invalid bounded pilot objective')
    if not (os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_GENERATIVE_AI_API_KEY')):raise ValueError('Gemini not configured')
    node=os.getenv('SAUCE_STAGEHAND_NODE','node')
    out=Path(out).resolve();out.mkdir(mode=0o700,parents=True,exist_ok=False)
    raw=out/'source-native.mp4';events=[];navigation=[];stage='initializing';encoder=None;agent=None;clock=None
    with native_display(out) as display,tempfile.TemporaryDirectory(prefix='sauce-native-public-') as profile,sync_playwright() as pw:
        c=pw.chromium.launch_persistent_context(profile,headless=False,executable_path=str(FULL_CHROME),env=clean_env(display),args=customer_browser_args(display)+['--remote-debugging-port=0','--remote-debugging-address=127.0.0.1'],viewport={'width':W,'height':H},device_scale_factor=D,service_workers='block',accept_downloads=False,permissions=[])
        try:
            p=c.pages[0];c.route('**/*',guard_for(url));c.route_web_socket('**/*',lambda ws:ws.close())
            robots=read_robots(c,url)
            if not robots.can_fetch('SauceBasicPreviewBot/0.1',url):raise ValueError('Robots denied public route')
            c.on('page',lambda extra:extra.close() if extra!=p else None)
            def observed(source,event):
                if source['page']!=p or source['frame']!=p.main_frame or len(events)>=20000 or not isinstance(event,dict):return
                kind=event.get('kind');r=event.get('rect');t=event.get('t')
                def number(n):return type(n) in (float,int) and math.isfinite(n) and abs(n)<1e14
                if kind not in ('pointermove','pointerdown','pointerup','wheel','input','change') or not number(t) or not isinstance(r,dict) or not all(number(r.get(k)) for k in ('x','y','width','height')):return
                entry={'kind':kind,'t':t,'rect':{k:r[k] for k in ('x','y','width','height')}}
                if number(event.get('x')) and number(event.get('y')):entry.update(x=event['x'],y=event['y'])
                events.append(entry)
            c.expose_binding('__sauceNativeObserved',observed)
            c.add_init_script('('+OBSERVE+')()')
            p.on('framenavigated',lambda f:navigation.append({'epochMs':time.time()*1000,'path':urlsplit(f.url).path}) if f==p.main_frame else None)
            response=p.goto(url,wait_until='domcontentloaded',timeout=28000)
            if not response or response.status>=400 or public_scope(p.url)!=public_scope(url):raise ValueError('Public initial surface unavailable')
            p.wait_for_timeout(1800)
            session=c.new_cdp_session(p);window=session.send('Browser.getWindowForTarget')['windowId'];session.send('Browser.setWindowBounds',{'windowId':window,'bounds':{'windowState':'fullscreen'}});p.wait_for_timeout(1800)
            if p.evaluate('()=>[innerWidth,innerHeight,devicePixelRatio]')!=[W,H,D]:raise ValueError('Native viewport mismatch')
            def safe_surface():
                if public_scope(p.url)!=public_scope(url) or visible_authentication_barrier(p) or standalone_authentication_barrier(p) or p.locator('input[type=password]:visible,input[autocomplete=one-time-code]:visible,[data-private]:visible,[data-secret]:visible,[data-sensitive]:visible').count():raise ValueError('Sensitive or unauthorized surface')
            safe_surface();p.screenshot(path=out/'opening.png',scale='device')
            lines=(Path(profile)/'DevToolsActivePort').read_text().splitlines()
            if len(lines)!=2 or not lines[0].isdigit() or not re.fullmatch(r'/devtools/browser/[a-f0-9-]+',lines[1]):raise ValueError('Private local CDP unavailable')
            with tempfile.TemporaryDirectory(prefix='sauce-native-config-') as tmp:
                config=Path(tmp)/'task.json'
                private_json(config,{'cdpUrl':'ws://127.0.0.1:'+lines[0]+lines[1],'url':p.url,'model':'google/'+os.getenv('SAUCE_STAGEHAND_MODEL','gemini-3.1-flash-lite'),'instruction':objective+' Only use public, read-only interactions. Do not sign in, submit private data, or leave the site.','out':str(out/'agent-evidence'),'maxSteps':max_steps,'timeoutMs':timeout_seconds*1000})
                with (out/'capture.log').open('wb') as log:
                    clock=time.time()*1000
                    encoder=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','warning','-f','x11grab','-draw_mouse','0','-video_size',f'{W*D}x{H*D}','-framerate','60','-i',display,'-t',str(timeout_seconds+18),'-c:v','libx264','-preset','ultrafast','-crf','20','-pix_fmt','yuv420p','-threads','4','-an','-movflags','+faststart',str(raw)],stdin=subprocess.PIPE,stderr=log,env=clean_env(display))
                    p.wait_for_timeout(900)
                    stage='native_agent'
                    with (out/'agent.log').open('wb') as agent_log:
                        agent=subprocess.Popen([node,str(ROOT/'scripts/stagehand-native/attached.mjs'),str(config)],env=clean_env(inference=True),stdout=agent_log,stderr=subprocess.DEVNULL)
                        deadline=time.monotonic()+timeout_seconds+10
                        while agent.poll() is None and time.monotonic()<deadline:
                            p.wait_for_timeout(350);safe_surface()
                        if agent.poll() is None:agent.terminate();agent.wait(timeout=8)
                    safe_surface();p.wait_for_timeout(1200);safe_surface();p.screenshot(path=out/'closing.png',scale='device')
                    stage='captured' if agent.returncode==0 else 'agent_incomplete'
        except Exception as exc:
            stage='incomplete'
            private_json(out/'failure.json',{'type':type(exc).__name__})
        finally:
            if agent is not None and agent.poll() is None:
                agent.terminate()
                try:agent.wait(timeout=5)
                except subprocess.TimeoutExpired:agent.kill();agent.wait()
            if encoder is not None and encoder.poll() is None:
                try:encoder.stdin.write(b'q\n');encoder.stdin.flush();encoder.wait(timeout=12)
                except (OSError,subprocess.TimeoutExpired):
                    encoder.send_signal(signal.SIGINT);encoder.wait(timeout=8)
            c.close()
    info=None
    if raw.exists() and raw.stat().st_size:
        result=subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(raw)],capture_output=True,text=True,timeout=15)
        if result.returncode==0:info=json.loads(result.stdout)
    receipt={'schema':'sauce.stagehand.native-capture.v1','status':stage,'source':url,'captureStartEpochMs':clock,'clockAlignmentVerified':False,'eventsAdvisoryOnly':True,'events':events,'navigation':navigation,'stream':info,'filmEligible':False,'verifiedOutcome':False}
    if info:
        with raw.open('rb') as f:receipt['sha256']=hashlib.file_digest(f,'sha256').hexdigest()
    private_json(out/'capture-receipt.json',receipt)
    return {k:receipt[k] for k in ('status','filmEligible','verifiedOutcome')}|{'eventCount':len(events),'video':bool(info)}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--url',required=True);ap.add_argument('--objective',required=True);ap.add_argument('--out',required=True)
    ap.add_argument('--max-steps',type=int,default=12);ap.add_argument('--timeout',type=int,default=85)
    args=ap.parse_args()
    print(json.dumps(capture(args.url,args.objective,args.out,max_steps=args.max_steps,timeout_seconds=args.timeout)))
