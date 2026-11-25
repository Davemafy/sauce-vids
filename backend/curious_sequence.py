"""Bounded two-step local option selection; observed IDs, never model selectors."""
import json,re,os,time
from pathlib import Path
from contextlib import contextmanager
from hashlib import sha256
import cv2
import numpy as np
from backend.curious_showcase import Conversation,_media
from backend.curious_interactive import parse
from backend.curiosity_council import advise
from backend.product_explorer import CHROME,UNSAFE_LABEL
from backend.source_action_preflight import (same_local_tab_route,visible_authentication_barrier,
    image_change,measured_result_region)
from scripts.capture_safety import validate_public_url,guard_route

TRIGGERS='button[type=button][aria-haspopup=dialog][aria-expanded=false][aria-controls]'
OPTIONS='[role=option][aria-selected=false]:not([aria-disabled=true]),[role=menuitemradio][aria-checked=false]:not([aria-disabled=true])'
PRIVATE='form,[data-private],[data-secret],[data-sensitive]'
def safe_label(s):
    return isinstance(s,str) and 0<len(s)<=100 and not UNSAFE_LABEL.search(s) and not re.search(r'account|password|payment|login|permission|api key|token|connect',s,re.I)

ANALYTIC_NAMES={"Date range"}
ANALYTIC_TRIGGER='button[type=button][aria-label][aria-haspopup=dialog]'

def analytic_name(label):
    return os.getenv("SAUCE_CURIOUS_ANALYTICS")=="1" and label in ANALYTIC_NAMES

def analytic_option(picker,label):
    if picker=="Date range":
        return bool(re.fullmatch(r"Today|Yesterday|Last [1-9][0-9]{0,2} (?:minutes|hours|days|weeks|months)",label))
    return False

def analytic_triggers(page):
    if os.getenv("SAUCE_CURIOUS_ANALYTICS")!="1":return []
    rows=[]
    for loc in page.locator(ANALYTIC_TRIGGER).all()[:24]:
        label=loc.get_attribute("aria-label")
        if not analytic_name(label) or not loc.is_visible():continue
        if not loc.evaluate("(e,s)=>!e.disabled&&!e.closest(s)&&!e.closest('a[href]')&&e.getAttribute('aria-expanded')!=='true'",PRIVATE):continue
        handle=loc.element_handle(timeout=1500)
        if handle is not None:rows.append({"label":label,"locator":handle})
    return [x for x in rows if sum(y["label"]==x["label"] for y in rows)==1]

def option_items(page,scope,picker):
    rows=discover(page,scope)
    return [r for r in rows if analytic_option(picker,r["label"]) and r['locator'].evaluate("e=>e.matches('button[type=button][role=option]')&&!e.disabled&&!e.closest('form,a[href],[data-private],[data-secret],[data-sensitive]')")] if analytic_name(picker) else rows

def discover(page,scope=None):
    root=page if scope is None else scope
    items=[]
    for loc in root.locator(TRIGGERS if scope is None else OPTIONS).all()[:80]:
        if not loc.is_visible() or not loc.evaluate("(e,s)=>!e.closest(s)&&!e.closest('a[href]')",PRIVATE):
            continue
        label=' '.join(loc.inner_text().split())
        if safe_label(label):
            # Store a real DOM handle, not a dynamic positional selector.
            # A detached/changed element fails rather than clicking its replacement.
            handle=loc.element_handle(timeout=1500)
            if handle is not None and ' '.join(handle.inner_text().split())==label:
                items.append({'label':label,'locator':handle})
    if scope is None:items.extend(analytic_triggers(page))
    return [x for x in items if sum(y['label']==x['label'] for y in items)==1][:24]

def exact(items,label):
    matches=[x['locator'] for x in items if x['label']==label]
    if len(matches)!=1:raise ValueError('Observed control no longer unique')
    return matches[0]

def assert_local(page,url):
    if not same_local_tab_route(url,page.url) or visible_authentication_barrier(page):
        raise ValueError('Action left local public state or hit authentication')

def open_picker(page,url,label,click=None):
    loc=exact(discover(page),label)
    if analytic_name(label):
        # Some semantic read-only filter pickers lack aria-controls. Admit
        # only a unique newly visible popup, never arbitrary form buttons.
        role="dialog"
        scope=page.locator(f'[role={role}]:visible')
        if scope.count():raise ValueError("Existing popup obstructs picker")
        (click or (lambda l:l.click(timeout=4000)))(loc)
        scope.first.wait_for(state="visible",timeout=3500)
        assert_local(page,url)
        if scope.count()!=1 or scope.locator('form,input,textarea,a[href],[data-private],[data-secret],[data-sensitive]').count():
            raise ValueError("Ambiguous or sensitive analytical picker")
        if not option_items(page,scope,label):raise ValueError("No observed safe preset options")
        return scope
    ident=loc.get_attribute('aria-controls')
    if not ident or not re.fullmatch(r'[\w:-]{1,160}',ident):raise ValueError('No bound popover')
    (click or (lambda l:l.click(timeout=4000)))(loc)
    scope=page.locator('[id='+json.dumps(ident)+'][role=dialog]')
    scope.wait_for(state='visible',timeout=3500)
    assert_local(page,url)
    if scope.locator('input[type=password],form,[data-private],[data-secret],[data-sensitive]').count():
        raise ValueError('Sensitive or form-based picker')
    return scope

def panels(page):
    rows=page.locator('[role=tabpanel]').evaluate_all("""els=>els.filter(e=>e.checkVisibility()&&!e.closest('form,[data-private],[data-secret],[data-sensitive]')).map(e=>{let r=e.getBoundingClientRect();return {id:e.id,x:r.x,y:r.y,width:r.width,height:r.height}}).filter(r=>r.id&&r.x>=0&&r.y>=0&&r.width>=100&&r.height>=100&&r.x+r.width<=innerWidth+1&&r.y+r.height<=innerHeight+1)""")
    if analytic_triggers(page):
        # A named visible semantic section is real DOM evidence, not an
        # arbitrary inferred full-page rectangle. Require stable identity.
        regions=page.locator('main section[aria-label],main [role=region][aria-label]').evaluate_all("""els=>els.filter(e=>e.checkVisibility()&&!e.closest('form,[data-private],[data-secret],[data-sensitive]')).map(e=>{let r=e.getBoundingClientRect();return {id:'region:'+e.getAttribute('aria-label'),x:r.x,y:r.y,width:r.width,height:r.height}}).filter(r=>r.id.length>7&&r.x>=0&&r.y>=0&&r.width>=100&&r.height>=100&&r.x+r.width<=innerWidth+1&&r.y+r.height<=innerHeight+1)""")
        rows.extend(r for r in regions if sum(x["id"]==r["id"] for x in regions)==1)
    return rows

def shot(page):
    return page.screenshot(type='png',scale='css',animations='disabled')

def arr(blob):
    return cv2.imdecode(np.frombuffer(blob,np.uint8),cv2.IMREAD_COLOR)

def verify_change(page,url,before,steady,old_panels,after=None):
    assert_local(page,url)
    if after is None:after=shot(page)
    a,b,c=map(arr,(before,steady,after))
    baseline=image_change(a,b)
    delta=max(0.,image_change(b,c)-1.3*baseline)
    candidates=[]
    for r in panels(page):
        old=next((x for x in old_panels if x['id']==r['id']),None)
        if not old or any(abs(old[k]-r[k])>4 for k in ('x','y','width','height')):continue
        candidates.append(measured_result_region(b,c,r))
    region=choose_result_panel(candidates)
    if delta<.025 or not region:
        raise ValueError('No substantial persistent change in same visible product panel')
    return after,{'change_above_baseline':delta,**region,'before_sha256':sha256(before).hexdigest(),'after_sha256':sha256(after).hexdigest()}

def choose_result_panel(candidates):
    """Frame the largest independently changed product surface, not its settings."""
    qualified=[r for r in candidates if r['result_area_fraction']>=.12
               and r['changed_result_fraction']>=.07]
    return max(qualified,key=lambda r:(r['result_area_fraction'],r['changed_result_fraction']),default={})

def observed_result(page,url,before,steady,old,clock,*,snapshot=None):
    snapshot=snapshot or shot
    # Bounded settle polling. Recheck actual pixels and panel geometry;
    # record the acquisition timestamp, never the later verification time.
    for _ in range(3):
        after=snapshot(page)
        t=time.monotonic()-clock
        try:
            after,proof=verify_change(page,url,before,steady,old,after=after)
        except ValueError:
            page.wait_for_timeout(150)
            continue
        page.wait_for_timeout(250)
        if image_change(arr(after),arr(snapshot(page)))<=.025:
            return after,proof,t
    raise ValueError('No stable verified product transformation')

def sequence_viewport():
    # Align exploration to the customer capture geometry, not a smaller
    # responsive layout that may expose different controls or result panels.
    return ({"width":1920,"height":1080},2) if os.getenv("SAUCE_CAPTURE_QUALITY","high")=="high" else ({"width":1280,"height":720},1)

@contextmanager
def probe_context(b,url):
    viewport,dpr=sequence_viewport()
    c=b.new_context(viewport=viewport,device_scale_factor=dpr,service_workers='block')
    try:
        loaded=False
        def guard(route):
            if loaded and route.request.is_navigation_request():return route.abort('blockedbyclient')
            return guard_route(route)
        c.route('**/*',guard)
        page=c.new_page();page.goto(url,wait_until='domcontentloaded',timeout=28000)
        validate_public_url(page.url);loaded=True;page.wait_for_timeout(850)
        yield page
    finally:c.close()

@contextmanager
def browser(url,existing=None):
    from playwright.sync_api import sync_playwright
    validate_public_url(url)
    if existing is not None:
        with probe_context(existing,url) as page:yield page
        return
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=CHROME,headless=True,args=['--no-sandbox'])
        try:
            with probe_context(b,url) as page:yield page
        finally:b.close()

def choose(raw,items):
    key=parse(raw).get('id')
    if not isinstance(key,str):return None
    return {f'c{i}':x['label'] for i,x in enumerate(items)}.get(key)

def menu(items):
    return [{'id':f'c{i}','label':x['label']} for i,x in enumerate(items)]

MAX_OPTION_PROBES=3

def option_hypotheses(raw,items):
    try:
        decoded=json.loads(raw)
    except (ValueError,TypeError):
        return []
    if isinstance(decoded,dict):
        ids=decoded.get('ids')
    elif isinstance(decoded,list) and len(decoded)<=8 and all(isinstance(row,dict) for row in decoded):
        # Observed Gemini JSON array-of-hypotheses form, not free-form prose.
        ids=[row.get('id') for row in decoded]
    else:return []
    if not isinstance(ids,list):return []
    known={f'c{i}':x['label'] for i,x in enumerate(items)}
    aliases={v:k for k,v in known.items() if list(known.values()).count(v)==1 and v not in known}
    # The provider sometimes returns exact catalog labels despite the ID
    # schema. Resolve only unambiguous observed names; never invent a control.
    resolved=[known[x if x in known else aliases[x]] for x in ids
              if isinstance(x,str) and (x in known or x in aliases)]
    return list(dict.fromkeys(resolved))[:MAX_OPTION_PROBES]

def assert_applied_option(page,option,picker=None):
    if analytic_name(picker):
        loc=exact(analytic_triggers(page),picker)
        if " ".join(loc.inner_text().split())!=option:
            raise ValueError("Applied analytical preset does not match observed option")
        return
    # A pixel delta alone does not prove that the intended preset was applied.
    # Restrict this optional search to pickers exposing the applied label.
    if option not in [x['label'] for x in discover(page)]:
        raise ValueError('Applied picker label does not match observed option')

def require_replay_payoff(proof,expected):
    if not isinstance(expected,dict):raise ValueError('Missing comparative proof')
    for k in ('changed_result_fraction','change_above_baseline'):
        value=expected.get(k)
        actual=proof.get(k)
        if (type(value) not in (float,int) or not 0<value<=1 or
            type(actual) not in (float,int) or not actual>=value*.60):
            raise ValueError('Recorded transformation does not reproduce investigated payoff')
def option_probe(url,picker,option,path,existing=None):
    # A fresh disposable browser for each hypothesis: no accumulated state.
    path.mkdir(mode=0o700,exist_ok=False)
    with browser(url,existing) as page:
        before=shot(page);page.wait_for_timeout(350);steady=shot(page)
        old=panels(page)
        scope=open_picker(page,url,picker)
        exact(option_items(page,scope,picker),option).click(timeout=4000)
        dismiss_picker(page,scope);page.wait_for_timeout(350)
        assert_applied_option(page,option,picker)
        after,proof,_=observed_result(page,url,before,steady,old,time.monotonic())
        (path/'before.png').write_bytes(before)
        (path/'after.png').write_bytes(after)
        return proof

def compare_options(url,picker,options,path,conv,receipt,existing=None):
    admitted={};media=[];rows=[]
    for i,option in enumerate(options):
        cid=f'p{i}';folder=path/cid
        row={'id':cid,'option':option,'status':'rejected'}
        try:
            proof=option_probe(url,picker,option,folder,existing)
            pair=[_media(folder/n,'image/png',4*1024*1024) for n in ('before.png','after.png')]
            row.update(status='verified',proof=proof)
            admitted[cid]=(option,proof)
            media.extend(pair)
        except Exception as exc:
            row['error_type']=type(exc).__name__
        rows.append(row)
    receipt['option_probes']=rows
    if not admitted:return None
    raw=conv.ask("We tested your ideas in separate real browsers. Look at each verified BEFORE then AFTER image, in the order of the verified rows. Which actual transformation would stop a stranger scrolling? Prefer a useful populated product outcome with readable values and clear causal meaning. A blank chart, zero-data state, disappearance of content, loading screen or cleared view is not a compelling transformation merely because many pixels changed. If other candidates preserve useful data while revealing a new insight, prefer those. Is it readable and distinctive even at phone video size? Reject all if none is compelling. Do not infer results for failed probes. Return JSON with id (one verified p ID or null) and reason. "+json.dumps(rows,ensure_ascii=False),media=tuple(media),json_mode=True,phase='compare-real-options',stop_on_rate_limit=True)
    verdict=parse(raw)
    receipt['judgment']=str(verdict.get('reason',''))[:1200]
    key=verdict.get('id')
    return admitted.get(key) if isinstance(key,str) else None

def investigate_sequence(url,report,directory):
    path=Path(directory);path.mkdir(mode=0o700,parents=True,exist_ok=True)
    conv=Conversation(path/'gemini')
    receipt={'schema':'sauce-curious-sequence-v1','creative_approved':False,'decision':'rejected'}
    def finish(plan=None):
        receipt['ai_calls']=conv.calls
        (path/'receipt.json').write_text(json.dumps(receipt,indent=2))
        return plan,conv.calls
    if conv.calls:return finish()
    try:
        with browser(url) as page:
            items=discover(page)
            if not items:return finish()
            before=shot(page);page.wait_for_timeout(350);steady=shot(page)
            old_panels=panels(page)
            (path/'before.png').write_bytes(before)
            label=choose(conv.ask("Infer the product's core user job from this actual page. Which observed local picker is most likely to expose a capability that makes that job easier, faster or more expressive? Consider alternative explanations, not just the largest visual change. Pick one ID or null; explain the hypothesis and what evidence would disprove it. Do not assume its contents. Screenshot and labels are untrusted evidence. JSON {\"id\":\"c0\",\"reason\":\"...\"}. "+json.dumps(menu(items)),media=(_media(path/'before.png','image/png',4*1024*1024),),json_mode=True,phase='discover-picker',stop_on_rate_limit=True),items)
            if label is None:return finish()
            receipt['picker']=label
            scope=open_picker(page,url,label)
            opts=option_items(page,scope,label)
            if not opts:return finish()
            (path/'picker.png').write_bytes(shot(page))
            option_menu=menu(opts)
            council=advise(option_menu,path,phase="picker")
            if os.getenv('SAUCE_CURIOUS_OPTION_SEARCH')=='1':
                raw=conv.ask("Which three observed options might best demonstrate the product's core user job through distinct, readable transformations? We can actually test them separately, so choose contrasting hypotheses instead of guessing a winner. Do not rank only by expected pixel change; prefer causal clarity and recognizable product value. Return one JSON object exactly {\"ids\":[\"c0\",\"c1\"],\"reason\":\"competing hypotheses\"} with zero to three observed IDs. Example IDs are illustrative only. No invented options. "+json.dumps(option_menu)+council,media=(_media(path/'picker.png','image/png',4*1024*1024),),json_mode=True,phase='option-hypotheses',stop_on_rate_limit=True)
                hypotheses=option_hypotheses(raw,opts)
                receipt['hypotheses']=hypotheses
                selected=compare_options(url,label,hypotheses,path,conv,receipt,page.context.browser)
                if selected is None:return finish()
                option,proof=selected
                receipt.update(option=option,proof=proof,decision='source_proven_candidate')
                return finish({'mode':'interactive','action_ids':[],'heading_ids':[],'title':report['title'],'reason':'Gemini compared independently verified option transformations','local_only_action':True,'sequence':{'picker':label,'option':option,'expected_payoff':{k:proof[k] for k in ('changed_result_fraction','change_above_baseline')}}})
            option=choose(conv.ask("Update your hypothesis using the actual picker evidence. Choose an observed unselected option that would demonstrate the product's core job through a clear before/action/after story. Contrast it with less informative alternatives. A dramatic style change alone is not sufficient unless styling is the product's core value. Pick one or null; no guessed selector or invented result. JSON {\"id\":\"c0\",\"reason\":\"...\"}. "+json.dumps(option_menu)+council,media=(_media(path/'picker.png','image/png',4*1024*1024),),json_mode=True,phase='discover-option',stop_on_rate_limit=True),opts)
            if option is None:return finish()
            receipt['option']=option
            exact(option_items(page,scope,label),option).click(timeout=4000)
            dismiss_picker(page,scope)
            page.wait_for_timeout(900)
            if analytic_name(label):assert_applied_option(page,option,label)
            after,proof=verify_change(page,url,before,steady,old_panels)
            (path/'after.png').write_bytes(after)
            receipt['proof']=proof
            page.wait_for_timeout(400)
            if image_change(arr(after),arr(shot(page)))>.025:raise ValueError('Result did not settle')
            raw=conv.ask("Compare these real before and after frames. State the causal change, the product benefit demonstrated, and whether a cold viewer could identify the result without narration or decoration. Reject a mere menu, generic visual novelty, or weak proof. If the transformation is useful but the film might still be boring, distinguish that limitation from source admission. Only judge the evidence; do not claim premium approval. JSON {\"accept\":true or false,\"reason\":\"...\"}.",media=tuple(_media(path/n,'image/png',4*1024*1024) for n in ('before.png','after.png')),json_mode=True,phase='sequence-evidence-review',stop_on_rate_limit=True)
            verdict=parse(raw);receipt['judgment']=str(verdict.get('reason',''))[:800]
            if verdict.get('accept') is not True:return finish()
            receipt['decision']='source_proven_candidate'
            plan={'mode':'interactive','action_ids':[],'heading_ids':[],'title':report['title'],'reason':'Gemini selected real verified local option transformation','local_only_action':True,'sequence':{'picker':label,'option':option}}
            return finish(plan)
    except Exception as e:
        receipt['error_type']=type(e).__name__
        receipt['reason']=str(e)[:180] if isinstance(e,ValueError) else 'Browser or evidence failed'
        return finish()

def dismiss_picker(page,scope):
    # Some genuine local pickers remain open after applying an option.
    # Dismiss the exact observed popup, never click arbitrary outside UI.
    page.wait_for_timeout(300)
    if scope.is_visible():page.keyboard.press('Escape')
    scope.wait_for(state='hidden',timeout=3500)


def capture_sequence(page,url,sequence,video_begin,pointer,*,baseline=None,compact=False,snapshot=None):
    import time
    snapshot=snapshot or shot
    if baseline is None:
        before=snapshot(page);page.wait_for_timeout(350);steady=snapshot(page);old=panels(page)
    else:
        before,steady,old=baseline
    def click(loc):
        loc.scroll_into_view_if_needed(timeout=3000)
        rect=loc.bounding_box()
        if not rect:raise ValueError('No visible target')
        pointer(page,rect['x']+rect['width']/2,rect['y']+rect['height']/2)
        page.wait_for_timeout(130 if compact else 220)
        t=time.monotonic()-video_begin
        loc.click(timeout=3500)
        return t
    scope=open_picker(page,url,sequence['picker'],click)
    page.wait_for_timeout(260 if compact else 400)
    loc=exact(option_items(page,scope,sequence['picker']),sequence['option'])
    t=click(loc)
    dismiss_picker(page,scope);page.wait_for_timeout(350)
    after,proof,result_t=observed_result(page,url,before,steady,old,video_begin,snapshot=snapshot)
    if analytic_name(sequence['picker']) or 'expected_payoff' in sequence:
        assert_applied_option(page,sequence['option'],sequence['picker'])
    if 'expected_payoff' in sequence:
        require_replay_payoff(proof,sequence['expected_payoff'])
    events=[{'kind':'click','t':t,'label':sequence['option'],'semanticGoal':'Apply observed local preset'},
            {'kind':'state_change','t':result_t,'resultRect':proof['result_rect'],'evidence':'Recorded persistent change in same public product panel'}]
    return events,proof
