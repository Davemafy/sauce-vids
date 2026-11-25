"""Bounded customer URL-only 30s story: observed picker/tab controls, no model selectors.

Opt-in until a fresh customer film earns creative approval. Existing short path
is untouched. Every action is probed in a disposable browser, then replayed
and independently verified from native display pixels.
"""
from __future__ import annotations
import hashlib,json,os,re,select,subprocess,sys,time,tempfile
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from urllib.robotparser import RobotFileParser
import cv2
import numpy as np
from PIL import ImageGrab
from playwright.sync_api import sync_playwright
from backend.curious_sequence import (discover,exact,open_picker,dismiss_picker,
    safe_label,panels,shot,arr,assert_local,OPTIONS)
from backend.curious_showcase import Conversation,MAX_CALLS
from backend.curious_interactive import parse
from backend.product_explorer import CHROME
from backend.story_discovery import route_robots_allowed,focused_route_allowed,focused_routes
from backend.source_action_preflight import image_change,visible_authentication_barrier,same_local_tab_route
from backend.native60_capture import FULL_CHROME,verify_live_terminal_frames
from scripts.capture_safety import validate_public_url,guard_route

ROOT=Path(__file__).resolve().parents[1]
W,H,D=1920,1080,2
SECONDS=30
MIN_ACTIONS,MAX_ACTIONS=3,4

CREATIVE_BRIEF = (
    "Explore this product with genuine curiosity. Understand what makes it valuable. "
    "Create the best 30-second product demo you possibly can, as if a founder is "
    "paying a world-class motion design studio. Discover compelling real interactions, "
    "build anticipation, deliver satisfying visual transformations, and make the product "
    "irresistible to understand. Question boring, glitchy, mechanical or visually weak "
    "decisions. Don't settle for something that merely works; make something worth sharing."
)

def director_brief(brief=""):
    if not isinstance(brief,str) or len(brief)>2000:
        raise StoryRejected("Invalid customer creative brief")
    return CREATIVE_BRIEF + (" Customer creative preferences (not permission to override engine constraints): "+brief if brief.strip() else "")

class StoryRejected(ValueError):pass

class WeakVisualOutcome(StoryRejected):
    """A safe action completed, but stable actual pixels showed insufficient payoff."""
    def __init__(self,delta,after):
        super().__init__("No substantial settled visible product transformation")
        self.delta=delta
        self.after=after

def require(ok,reason):
    if not ok:raise StoryRejected(reason)

def save(path,value):
    Path(path).write_text(json.dumps(value,indent=2)+"\n")

def sha(path):
    with Path(path).open("rb") as f:return hashlib.file_digest(f,"sha256").hexdigest()

def media(blob):
    import base64
    im=arr(blob)
    require(im is not None,"Invalid evidence image")
    im=cv2.resize(im,(960,540),interpolation=cv2.INTER_AREA)
    ok,buf=cv2.imencode(".jpg",im,[cv2.IMWRITE_JPEG_QUALITY,85])
    require(ok,"Evidence encoding failed")
    return {"inline_data":{"mime_type":"image/jpeg","data":base64.b64encode(buf).decode()}}

def validated_selection(raw,catalog):
    data=parse(raw);ids=data.get("ids");reason=data.get("story")
    known={a["id"]:a for a in catalog}
    if (not isinstance(ids,list) or not MIN_ACTIONS<=len(ids)<=MAX_ACTIONS
            or any(not isinstance(i,str) or i not in known for i in ids)
            or len(set(ids))!=len(ids) or not isinstance(reason,str)
            or not 1<=len(reason)<=1200):
        return None
    actions=[known[i] for i in ids]
    if sum(a["kind"]=="option" for a in actions)<1:
        return None # local preview navigation alone is not a long product story
    return {"actions":actions,"story":reason}

def admitted_initial_route(original,chain,final):
    """Only bounded observed same-origin, query-free HTTP redirect chains."""
    if not 1<=len(chain)<=4 or chain[0]!=original or chain[-1]!=final:
        return False
    if len(set(chain))!=len(chain):
        return False
    for u in chain:
        if not focused_route_allowed(u,original):
            return False
        try:validate_public_url(u)
        except ValueError:return False
    return True

def preview_frame_allowed(url,origin,robots):
    """Bounded same-origin, query-free, read-only product preview documents."""
    return (focused_route_allowed(url,origin)
            and bool(re.match(r"^/previews?(?:/|$)",urlsplit(url).path))
            and robots.can_fetch("SauceBasicPreviewBot/0.1",url))

def read_robots(context,url):
    target=urljoin(url,"/robots.txt")
    robot=context.new_page()
    try:
        response=robot.goto(target,wait_until="domcontentloaded",timeout=12000)
        parser=RobotFileParser()
        if response and response.status==404:parser.parse([])
        else:
            require(response and response.status==200 and robot.url==target,"Robots unavailable")
            parser.parse(robot.locator("body").inner_text(timeout=3000)[:160000].splitlines())
        return parser
    finally:robot.close()

def clear_welcome(page,url):
    """Dismiss a single nonsensitive local welcome/intro before recording."""
    dialogs=page.locator('[role=dialog]:visible')
    if not dialogs.count():return
    require(dialogs.count()==1,"Multiple opening dialogs")
    dialog=dialogs.first
    text=dialog.inner_text()[:2000]
    require(bool(re.search(r'\b(welcome|customiz[ea]|get started|introduction|tour)\b',text,re.I))
            and not re.search(r'\b(privacy|cookie|consent|terms|account|sign in|sign up|login|payment|purchase|subscribe|permission|personal data)\b',text,re.I)
            and dialog.locator('form,input,textarea,select,a[href],[data-private],[data-secret],[data-sensitive]').count()==0,
            "Opening dialog needs user decision")
    buttons=dialog.locator('button:visible')
    require(buttons.count()==1,"Ambiguous opening dialog")
    btn=buttons.first
    require(" ".join(btn.inner_text().split()).lower() in ("get started","continue","close","dismiss","skip","got it"),
            "Unsupported opening dialog action")
    btn.click(timeout=3500)
    dialog.wait_for(state="hidden",timeout=3500)
    assert_local(page,url)

def menu_triggers(page):
    rows=[]
    for loc in page.locator('button[type=button][aria-haspopup=menu][aria-expanded=false]:not(:disabled)').all()[:36]:
        if not loc.is_visible():continue
        if not loc.evaluate("e=>!e.closest('form,a[href],[data-private],[data-secret],[data-sensitive],[inert],[data-base-ui-inert]')"):continue
        lines=[x.strip() for x in loc.inner_text().splitlines() if x.strip()]
        if len(lines)<2 or not safe_label(lines[0]) or not safe_label(lines[1]):continue
        rows.append((lines[0],loc.element_handle(timeout=1500)))
    return [(k,v) for k,v in rows if v is not None and sum(x==k for x,_ in rows)==1][:12]

def open_radio_menu(page,url,group,click=None):
    hits=[h for k,h in menu_triggers(page) if k==group]
    require(len(hits)==1 and page.locator('[role=menu]:visible').count()==0,"Menu identity ambiguous")
    (click or (lambda l:l.click(timeout=3500)))(hits[0])
    scope=page.locator('[role=menu]:visible')
    scope.first.wait_for(state='visible',timeout=2500)
    require(scope.count()==1,"No unique observed menu")
    assert_local(page,url)
    require(scope.locator('form,input,textarea,a[href],[data-private],[data-secret],[data-sensitive]').count()==0,"Sensitive menu")
    return scope

def radio_options(scope):
    rows=[]
    for loc in scope.locator('[role=menuitemradio][aria-checked=false]:not([aria-disabled=true])').all()[:24]:
        if loc.is_visible():
            label=" ".join(loc.inner_text().split())
            if safe_label(label):rows.append((label,loc.element_handle(timeout=1500)))
    return [(k,v) for k,v in rows if v is not None and sum(x==k for x,_ in rows)==1]

def balanced_menu_catalog(groups,limit=60):
    # Round-robin keeps later customization groups visible to the model.
    # Stable IDs are assigned only after the complete observed catalog.
    rows=[]
    for i in range(max((len(options) for _,options in groups),default=0)):
        for group,options in groups:
            if i<len(options):
                rows.append({"id":f"m{len(rows)}","kind":"option","group":group,"label":options[i]})
                if len(rows)>=limit:return rows
    return rows

def scan_radio_menus(page,url):
    groups=[]
    for group,_ in menu_triggers(page):
        scope=open_radio_menu(page,url,group)
        opts=radio_options(scope)
        groups.append((group,[label for label,_ in opts]))
        dismiss_picker(page,scope)
    return balanced_menu_catalog(groups)

@contextmanager
def browser(url,*,display=None,include_robots=False):
    validate_public_url(url)
    with sync_playwright() as pw:
        b=pw.chromium.launch(headless=display is None,
            executable_path=str(FULL_CHROME if display else CHROME),
            env={**os.environ,"DISPLAY":display} if display else None,
            args=["--no-sandbox","--disable-dev-shm-usage",
                  "--window-position=0,0","--window-size=1920,1080",
                  "--force-device-scale-factor=2","--no-first-run"])
        c=b.new_context(viewport={"width":W,"height":H},device_scale_factor=D,
            service_workers="block",accept_downloads=False,permissions=[])
        try:
            loaded=False;robots=None
            def guard(route):
                req=route.request
                if req.is_navigation_request():
                    if robots is not None and req.frame.parent_frame is not None and preview_frame_allowed(req.url,url,robots):
                        return guard_route(route)
                    if loaded or req.url not in (url,urljoin(url,"/robots.txt")):
                        return route.abort("blockedbyclient")
                return guard_route(route)
            c.route("**/*",guard);c.route_web_socket("**/*",lambda ws:ws.close())
            robots=read_robots(c,url)
            require(robots.can_fetch("SauceBasicPreviewBot/0.1",url),"Robots denied public route")
            p=c.new_page();r=p.goto(url,wait_until="domcontentloaded",timeout=28000)
            require(r and r.status==200,"Unexpected initial public URL")
            chain=[];req=r.request
            while req and len(chain)<5:
                chain.append(req.url);req=req.redirected_from
            chain.reverse()
            require(req is None and admitted_initial_route(url,chain,p.url),"Unexpected initial public URL")
            loaded=True
            if p.url!=url:
                # The browser already received the server redirect. Admit the
                # destination only after public-route and robots checks.
                require(robots.can_fetch("SauceBasicPreviewBot/0.1",p.url),"Robots denied redirect destination")
            actual=p.url
            p.wait_for_timeout(1100)
            require(p.url==actual,"Unexpected post-load route change")
            if display:
                cdp=c.new_cdp_session(p);win=cdp.send("Browser.getWindowForTarget")["windowId"]
                cdp.send("Browser.setWindowBounds",{"windowId":win,"bounds":{"windowState":"fullscreen"}})
                p.wait_for_timeout(6000)
                require(p.evaluate("()=>[innerWidth,innerHeight,devicePixelRatio]")==[W,H,D],"Wrong native viewport")
            require(not visible_authentication_barrier(p),"Authentication barrier")
            clear_welcome(p,actual)
            yield (p,robots) if include_robots else p
        finally:
            c.close();b.close()

def observed_product_entry_links(page,origin,robots,*,limit=8):
    """Rank ONLY actually visible homepage anchors, never guessed destinations.

    Scan anchors independently of the bounded clickable-button inventory, as
    the latter omitted even the genuine 'Try It Now' links on tweakcn's home.
    The candidate cannot be a redirect, cross-origin route, query, fragment,
    auth route, download or robots-denied document.
    """
    rows=[]
    for loc in page.locator('a[href]').all()[:100]:
        if not loc.is_visible():continue
        if not loc.evaluate("e=>!e.closest('form,[data-private],[data-secret],[data-sensitive]')&& !e.hasAttribute('download')"):continue
        label=' '.join(loc.inner_text(timeout=1600).split())[:105]
        href=loc.get_attribute('href') or ''
        target=urljoin(page.url,href)
        u=urlsplit(target)
        if (not label or len(label)>105 or u.query or u.fragment
                or not focused_route_allowed(target,origin)
                or not robots.can_fetch('SauceBasicPreviewBot/0.1',target)):
            continue
        rows.append({'kind':'link','text':label,'href':target})
    ranked=focused_routes(rows,origin)[:limit]
    return [{'id':f'r{i}','url':u,
             'label':next(x['text'] for x in rows if x['href']==u)}
            for i,u in enumerate(ranked)]


def resolve_public_product_entry(url,out,conv,creative):
    """One separately observed public read-only navigation before any action.

    Gemini only selects a witnessed anchor ID; source URL is retained and
    target is reopened under the same independent browser/robots guards.
    """
    with browser(url,include_robots=True) as observed:
        page,robots=observed
        candidates=observed_product_entry_links(page,url,robots)
        receipt={'submitted_url':url,'entry_candidates':candidates,
                 'chosen_url':url,'model_selected':False}
        if not candidates:
            save(out/'entry-route.json',receipt)
            return url
        opening=shot(page)
        raw=conv.ask(creative+" The customer submitted a public homepage. Choose the single observed read-only entry link most likely to open the real functional product, not documentation, pricing or blog. You may choose null if none proves an app entry. We will validate and reopen the actual public route independently. Do not invent an ID or URL. Reply JSON {id:'r0' or null, reason:'...'}. "+json.dumps([{'id':c['id'],'label':c['label'],'path':urlsplit(c['url']).path} for c in candidates]),
                     media=(media(opening),),json_mode=True,phase='observed-product-entry',stop_on_rate_limit=True)
        verdict=parse(raw)
        choice=next((c for c in candidates if c['id']==verdict.get('id')),None)
        if choice:
            receipt.update(chosen_url=choice['url'],model_selected=True,
                           chosen_label=choice['label'])
        receipt['model_calls']=conv.calls
        save(out/'entry-route.json',receipt)
        return receipt['chosen_url']


def tabs(page):
    rows=[]
    for loc in page.locator('button[role="tab"][aria-selected="false"][aria-controls]:not(:disabled)').all()[:50]:
        if not loc.is_visible():continue
        if not loc.evaluate("""e=>!e.form&&!e.closest('form,[data-private],[data-secret],[data-sensitive],a')&&!!e.closest('[role=tablist]')&&e.getAttribute('aria-disabled')!=='true'"""):continue
        label=" ".join(loc.inner_text().split())
        if safe_label(label):
            handle=loc.element_handle(timeout=1500)
            if handle is not None and handle.get_attribute("aria-selected")=="false":
                rows.append((label,handle))
    return [(l,x) for l,x in rows if sum(y==l for y,_ in rows)==1]

def tab(page,label):
    matches=[x for l,x in tabs(page) if l==label]
    require(len(matches)==1,"Observed preview tab is no longer unique and inactive")
    return matches[0]

def panel(page):
    rows=panels(page)
    # An actual large named same-origin preview iframe is a product surface.
    # Read geometry only; inspect the actual visible pixels, never inject UI.
    for f in page.locator('iframe[title]:visible').all()[:8]:
        title=f.get_attribute('title') or ''
        frame=f.element_handle().content_frame()
        rect=f.bounding_box()
        declared=urljoin(page.url,f.get_attribute('src') or '')
        if (title.lower() in ('preview','product preview','live preview') and frame and rect
                and focused_route_allowed(declared,page.url.split('?')[0])
                and re.match(r'^/previews?(?:/|$)',urlsplit(declared).path)
                and same_local_tab_route(declared,frame.url)
                and 0<=rect['x'] and 0<=rect['y'] and rect['x']+rect['width']<=W+1 and rect['y']+rect['height']<=H+1):
            rows.append(rect)
    rows=sorted(rows,key=lambda r:r["width"]*r["height"],reverse=True)
    require(rows and rows[0]["width"]*rows[0]["height"]>=W*H*.18,
            "No large visible product panel")
    return rows[0]

def intersection(old,new):
    x=max(old["x"],new["x"]);y=max(old["y"],new["y"])
    r=min(old["x"]+old["width"],new["x"]+new["width"])
    b=min(old["y"]+old["height"],new["y"]+new["height"])
    box={"x":x,"y":y,"width":r-x,"height":b-y}
    require(box["width"]>0 and box["height"]>0 and
            box["width"]*box["height"]>=W*H*.18,"Product panel continuity missing")
    return box

def verify(page,url,before,old,snapshot,*,allow_localized=False,proof_metrics=None):
    assert_local(page,url)
    new=panel(page);box=intersection(old,new)
    x,y,w,h=(round(box[k]) for k in ("x","y","width","height"))
    weak=None
    for _ in range(3):
        page.wait_for_timeout(500);after=snapshot(page);t=time.monotonic()
        page.wait_for_timeout(250);settled=snapshot(page)
        assert_local(page,url)
        if image_change(pixels(after),pixels(settled))>.025:continue
        a=pixels(before)[y:y+h,x:x+w];b=pixels(after)[y:y+h,x:x+w]
        delta=float(np.mean(np.max(cv2.absdiff(a,b),axis=2)>25))
        if delta>=.07:return after,box,delta,t
        if allow_localized:
            from backend.story_outcome_evidence import localized_color_proof
            localized=localized_color_proof(a,b,pixels(settled)[y:y+h,x:x+w])
            if localized is not None:
                if proof_metrics is not None:proof_metrics.update(localized)
                return after,box,delta,t
        weak=(delta,after)
    if weak is not None:raise WeakVisualOutcome(*weak)
    raise StoryRejected("Product outcome did not settle")

def exact_observed_option(scope,label):
    """Resolve a previously observed safe label to one current DOM handle.

    Full option discovery remains authoritative for model selection. Replay
    needs only the chosen label, not dozens of remote locator round trips.
    Never use model selectors or positional identity; ambiguity fails closed.
    """
    require(safe_label(label),"Unsafe option label")
    handle=scope.evaluate_handle(r"""(root,args)=>{
        const normalize=e=>e.innerText.trim().replace(/\s+/g,' ');
        const eligible=[...root.querySelectorAll(args.selector)].slice(0,80).filter(e=>{
            const r=e.getBoundingClientRect(),style=getComputedStyle(e);
            return e.isConnected&&!e.disabled&&r.width>0&&r.height>0&&style.visibility==='visible'
                &&!e.closest('form,[data-private],[data-secret],[data-sensitive],a[href],[inert]')
                &&normalize(e)===args.label;
        });
        return eligible.length===1?eligible[0]:null;
    }""",{"selector":OPTIONS,"label":label}).as_element()
    require(handle is not None and handle.is_visible() and
            " ".join(handle.inner_text().split())==label,
            "Observed option no longer unique or visible")
    require(handle.evaluate("(e,selector)=>e.isConnected&&!e.disabled&&e.matches(selector)&&!e.closest('form,[data-private],[data-secret],[data-sensitive],a[href],[inert]')",OPTIONS),
            "Sensitive option")
    return handle

def apply(page,url,action,picker,click):
    label=action["label"]
    if action["kind"]=="option" and action.get("group"):
        group=action["group"]
        scope=open_radio_menu(page,url,group,lambda loc:click(loc,None))
        hits=[h for k,h in radio_options(scope) if k==label]
        require(len(hits)==1,"Observed radio option no longer unique")
        click(hits[0],label);dismiss_picker(page,scope)
        assert_local(page,url)
        rows=[h for k,h in menu_triggers(page) if k==group]
        require(len(rows)==1 and label in [x.strip() for x in rows[0].inner_text().splitlines()[1:]],
                "Applied radio value not observed")
        return picker
    if action["kind"]=="option":
        scope=open_picker(page,url,picker,lambda loc:click(loc,None))
        loc=exact_observed_option(scope,label)
        click(loc,label);dismiss_picker(page,scope)
        require(label in [q["label"] for q in discover(page)],"Applied option label not observed")
        return label
    loc=tab(page,label);controlled=loc.get_attribute("aria-controls")
    click(loc,label)
    selected=page.get_by_role("tab",name=label,exact=True)
    require(selected.count()==1 and selected.get_attribute("aria-selected")=="true"
            and selected.get_attribute("aria-controls")==controlled,"Tab not selected")
    require(any(r["id"]==controlled for r in panels(page)),"Selected tab has no visible result panel")
    return picker

def explore(url,out,progress,*,request=None,brief=""):
    creative=director_brief(brief)
    out.mkdir(mode=0o700,parents=True,exist_ok=False)
    conv=Conversation(out/"model",request=request)
    submitted_url=url
    url=resolve_public_product_entry(url,out,conv,creative)
    # A landing page cannot be silently replaced by a guessed deep route.
    # Its selected destination is reopened independently with all guards.
    with browser(url) as p:
        url=p.url
        title=p.title()[:140];opening=shot(p)
        (out/"opening.png").write_bytes(opening)
        radio_catalog=scan_radio_menus(p,url)
        if len(radio_catalog)>=MIN_ACTIONS:
            picker=None;catalog=radio_catalog;picker_image=opening
            save(out/"discovery.json",{"picker":picker,"catalog":catalog,"title":title,"kind":"radio-menus"})
        else:
            pickers=discover(p)
            if not pickers:
                save(out/"discovery.json",{"picker_count":0,"tab_count":len(tabs(p))})
                raise StoryRejected("No supported local product picker")
            menu=[{"id":f"k{i}","label":v["label"]} for i,v in enumerate(pickers)]
            if len(menu)>1:
                raw=conv.ask(creative+" Choose the observed local picker most relevant to the product's core capability, or null. No guessed action. Return JSON {id}. "+json.dumps(menu),
                             media=(media(opening),),json_mode=True,phase="story-picker",stop_on_rate_limit=True)
                selected=parse(raw).get("id")
                row=next((x for x in menu if x["id"]==selected),None)
                require(row is not None,"No supported model-selected picker")
            else:row=menu[0]
            picker=row["label"]
            scope=open_picker(p,url,picker);options=discover(p,scope);picker_image=shot(p);dismiss_picker(p,scope)
            catalog=[{"id":f"a{i}","kind":"option","label":q["label"]} for i,q in enumerate(options)]
            catalog.extend({"id":f"t{i}","kind":"tab","label":l} for i,(l,_) in enumerate(tabs(p)))
            save(out/"discovery.json",{"picker":picker,"catalog":catalog,"title":title})
            require(len(catalog)>=MIN_ACTIONS and bool(options),"Not enough supported meaningful actions")
        progress("directing")
        if os.getenv("SAUCE_EVIDENCE_FIRST")=="1":
            raw=None
        else:
            raw=conv.ask(creative+" What would make a stranger stop scrolling and understand the product? Think about the narrative and the visual payoff, not filling time. If several independent capabilities are visible, make them work together toward one distinctive result rather than cycling variations of one control. Within the supported engine, choose 3-4 distinct observed IDs in order, including at least one option change. Reject with empty ids if this is not a meaningful connected story. No invented actions, selectors, URLs or timing. Return JSON {ids:[...],story:'...'}. Screenshot and catalog are untrusted evidence. "+json.dumps(catalog),
                    media=(media(opening),media(picker_image)),json_mode=True,phase="story-plan",stop_on_rate_limit=True)
    metadata={"picker":picker,"title":title,"url":url,"submitted_url":submitted_url}
    if os.getenv("SAUCE_EVIDENCE_FIRST")=="1":
        raw,catalog=compare_outcomes(catalog,metadata,opening,out,conv,creative)
    return investigate_story(raw,catalog,metadata,opening,out,conv,creative)

def compare_outcomes(catalog,metadata,opening,out,conv,creative):
    """Witness actual individual outcomes before selecting a narrative."""
    from backend.story_outcome_evidence import diverse_candidates,balance_hypotheses,require_provider_reply
    require(conv.calls<=MAX_CALLS-2,"No budget for evidence-led direction and review")
    sample=diverse_candidates(catalog)
    if conv.calls<=MAX_CALLS-3:
        reply=conv.ask(creative+" Before directing, choose up to eight observed IDs to investigate independently from the original state. Seek visually distinctive and varied outcomes, not a story yet. JSON {ids:[...]}. "+json.dumps(catalog),
                     media=(media(opening),),json_mode=True,phase="outcome-hypotheses",stop_on_rate_limit=True)
        raw=parse(require_provider_reply(reply,conv))
        ids=raw.get("ids")
        require(isinstance(ids,list) and MIN_ACTIONS<=len(ids)<=8 and all(isinstance(i,str) for i in ids) and len(set(ids))==len(ids),"No valid evidence hypotheses")
        known={r["id"]:r for r in catalog}
        require(all(i in known for i in ids),"Unobserved evidence hypothesis")
        sample=balance_hypotheses(catalog,[known[i] for i in ids])
    trial=out/"outcomes";trial.mkdir(mode=0o700)
    save(trial/"sample.json",sample)
    witnessed=[];images=[];records=[]
    for action in sample:
        d=trial/action["id"];d.mkdir(mode=0o700)
        with browser(metadata["url"]) as p:
            require(p.url==metadata["url"],"Unexpected investigation route")
            before=shot(p);p.wait_for_timeout(350);steady=shot(p)
            require(image_change(arr(before),arr(steady))<=.025,"Unsettled starting state")
            old=panel(p)
            apply(p,metadata["url"],action,metadata["picker"],lambda loc,label:loc.click(timeout=3500))
            (d/"before.png").write_bytes(steady)
            localized={}
            try:
                after,box,delta,_=verify(p,metadata["url"],steady,old,shot,allow_localized=action["kind"]=="option",proof_metrics=localized)
            except WeakVisualOutcome as e:
                (d/"after.png").write_bytes(e.after)
                records.append({"id":action["id"],"status":"weak","delta":e.delta})
                save(trial/"comparison.json",records)
                continue
            (d/"after.png").write_bytes(after)
            records.append({"id":action["id"],"status":"verified","delta":delta,
                            "proof":"distributed-color" if delta<.07 else "panel-change",
                            "localized":localized or None,"result":box})
            witnessed.append(action);images.extend((media(steady),media(after)))
            save(trial/"comparison.json",records)
    require(len(witnessed)>=MIN_ACTIONS,"Insufficient witnessed outcomes for a connected film")
    # Paired screenshots are in the same order as the admitted catalog.
    raw=conv.ask(creative+" You now have actual independent before/after image pairs for each verified option below, in order. Direct a connected workflow using only 3-4 of these witnessed IDs. Prioritize a clear payoff and avoid redundant theme cycling. The images show independent tests, not an already verified sequence; Sauce will replay the entire sequence. Abstain if these do not support a compelling demo. JSON {ids:[...],story:'...'}. Observed outcomes: "+json.dumps([r for r in records if r["status"]=="verified"])+" Catalog: "+json.dumps(witnessed),
                 media=tuple(images),json_mode=True,phase="story-from-outcomes",stop_on_rate_limit=True)
    return require_provider_reply(raw,conv),witnessed

def probe_story(plan,out):
    """Probe a complete candidate in a fresh guarded browser, never a dirty prefix."""
    proofs=[];images=[]
    with browser(plan["url"]) as p:
        require(p.url==plan["url"],"Unexpected replay route")
        current=plan["picker"]
        for i,action in enumerate(plan["actions"]):
            before=shot(p);p.wait_for_timeout(350);steady=shot(p)
            require(image_change(arr(before),arr(steady))<=.025,"Unsettled starting state")
            old=panel(p)
            current=apply(p,plan["url"],action,current,lambda loc,label:loc.click(timeout=3500))
            try:
                after,box,delta,_=verify(p,plan["url"],steady,old,shot,allow_localized=os.getenv("SAUCE_EVIDENCE_FIRST")=="1" and action["kind"]=="option")
            except WeakVisualOutcome as e:
                # Only settled low-payoff outcomes are eligible for replan.
                # Auth, navigation, blocked controls, invalid geometry and
                # unstable source errors propagate without another model call.
                assert_local(p,plan["url"])
                (out/"failed-before.png").write_bytes(steady)
                (out/"failed-after.png").write_bytes(e.after)
                failure={"index":i,"id":action["id"],"observedDelta":round(e.delta,6),
                         "minimumDelta":.07,"priorVerified":proofs,
                         "reason":str(e)}
                save(out/"rejection.json",failure)
                save(out/"probe.json",proofs)
                return proofs,images,failure
            (out/f"{i}-before.png").write_bytes(steady);(out/f"{i}-after.png").write_bytes(after)
            proofs.append({"id":action["id"],"delta":delta,"result":box})
            images.extend((media(steady),media(after)))
    save(out/"probe.json",proofs)
    return proofs,images,None

def investigate_story(raw,catalog,metadata,opening,out,conv,creative):
    """At most one model-authored recovery; reserve a call for editorial admission."""
    allowed=list(catalog)
    for attempt in range(2):
        plan=validated_selection(raw,allowed)
        require(plan is not None,"No valid model-authored connected story")
        plan.update(metadata)
        trial=out/f"attempt-{attempt+1}";trial.mkdir(mode=0o700)
        save(trial/"direction.json",plan)
        proofs,images,failure=probe_story(plan,trial)
        if failure is None:
            verdict=parse(conv.ask(creative+" Challenge this connected workflow against all real before/after evidence. Reject repetitive, decorative or navigation-only outcomes. JSON {accept:true/false,reason:'...'}. "+json.dumps(proofs),
                                  media=tuple(images),json_mode=True,phase="story-editorial",stop_on_rate_limit=True))
            save(trial/"editorial.json",verdict)
            require(verdict.get("accept") is True,"Editorial story not admitted")
            save(out/"direction.json",plan);save(out/"probe.json",proofs);save(out/"editorial.json",verdict)
            return plan,conv.calls,proofs
        if attempt or conv.calls>MAX_CALLS-2:
            raise StoryRejected("No verified story within bounded recovery budget")
        # The same option may behave differently in another context; exclude
        # only the observed failed ID for this job, not an entire capability.
        allowed=[a for a in allowed if a["id"]!=failure["id"]]
        require(len(allowed)>=MIN_ACTIONS,"Insufficient remaining observed actions")
        raw=conv.ask(creative+" Your actual workflow was tested and one safe action had too little settled visual payoff. The paired images show that failed action before and after, with the original opening first. Rethink the entire story from the original state. Select 3-4 distinct remaining observed IDs, not the excluded ID. Do not invent actions or claims; abstain with empty ids if the workflow cannot be compelling. JSON {ids:[...],story:'...'}. Measured failure: "+json.dumps(failure)+" Remaining catalog: "+json.dumps(allowed),
                     media=(media(opening),media((trial/"failed-before.png").read_bytes()),media((trial/"failed-after.png").read_bytes())),
                     json_mode=True,phase="story-replan",stop_on_rate_limit=True)
    raise StoryRejected("No verified story after bounded recovery")

@contextmanager
def native_display(out):
    with (out/"xvfb.log").open("ab") as log:
        proc=subprocess.Popen(["Xvfb","-displayfd","1","-screen","0",f"{W*D}x{H*D}x24","-nolisten","tcp","-noreset"],
                              stdout=subprocess.PIPE,stderr=log)
    try:
        ready,_,_=select.select([proc.stdout],[],[],7)
        require(bool(ready),"Native display unavailable")
        n=proc.stdout.readline().decode().strip();require(n.isdigit(),"Invalid display number")
        yield ":"+n
    finally:
        if proc.poll() is None:proc.terminate();proc.wait(timeout=8)

def pixels(evidence):
    return evidence if isinstance(evidence,np.ndarray) else arr(evidence)

def screen(display):
    # Capture only once and keep proof as raw pixels until a stable result
    # needs to be persisted. Avoid PNG encode/decode in the live loop.
    im=ImageGrab.grab(xdisplay=display)
    require(im.size==(W*D,H*D),"Wrong physical source screen")
    rgb=cv2.resize(np.asarray(im),(W,H),interpolation=cv2.INTER_AREA)
    return cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR)

def persist_screen(path,image):
    ok,data=cv2.imencode(".png",image,[cv2.IMWRITE_PNG_COMPRESSION,1])
    require(ok,"Native evidence failed")
    Path(path).write_bytes(data.tobytes())

def first_action_anchor(page,plan):
    """Resolve a real, visible first-action control before filming.

    Never synthesize mouse destination coordinates: the recorded source
    pointer may approach only a control discovered from the current guarded
    browser DOM. Failure is a safe wide opening, not a guessed gesture.
    """
    first=plan["actions"][0]
    loc=None
    if first["kind"]=="option" and first.get("group"):
        hits=[h for name,h in menu_triggers(page) if name==first["group"]]
        if len(hits)==1:loc=hits[0]
    elif first["kind"]=="option":
        hits=[h for h in discover(page) if h["label"]==plan["picker"]]
        if len(hits)==1:loc=hits[0]["locator"] if isinstance(hits[0],dict) else None
    elif first["kind"]=="tab":
        hits=[h for name,h in tabs(page) if name==first["label"]]
        if len(hits)==1:loc=hits[0]
    if loc is None:return None
    try:
        if not loc.is_visible():return None
        rect=loc.bounding_box()
    except Exception:return None
    if (not isinstance(rect,dict) or
            any(not isinstance(rect.get(k),(int,float)) for k in ("x","y","width","height")) or
            not 0<=rect["x"]<rect["x"]+rect["width"]<=W or
            not 0<=rect["y"]<rect["y"]+rect["height"]<=H):
        return None
    return (rect["x"]+rect["width"]/2,rect["y"]+rect["height"]/2)


def opening_pointer_approach(move,wait,anchor,start=(W*.25,H*.2)):
    """Early real-pointer anticipation, no unobserved clicks or invented UI."""
    if anchor is None:return 0
    sx,sy=start;tx,ty=anchor
    # The actual press still happens later in click(); stop short first.
    tx=max(16,min(W-16,tx-26))
    ty=max(16,min(H-16,ty-12))
    for i in range(1,13):
        u=i/12;u=u*u*(3-2*u)
        wait(.12+.58*i/12)
        move(sx+(tx-sx)*u,sy+(ty-sy)*u)
    return 12


def action_start(index,count):
    """Leave time for an actual final result, including proof acquisition."""
    require(MIN_ACTIONS<=count<=MAX_ACTIONS and 0<=index<count,"Invalid action schedule")
    return .8+index*19.0/(count-1)

def capture(url,plan,proofs,out):
    out.mkdir(mode=0o700,parents=True,exist_ok=False)
    native=lambda r:{k:round(r[k]*D,4) for k in ("x","y","width","height")}
    with native_display(out) as display, browser(url,display=display) as p:
        # This is before FFmpeg starts. Never use Playwright screenshots during recording.
        p.mouse.move(W*.25,H*.2);browser_pixels=shot(p);p.wait_for_timeout(1800)
        opening=screen(display)
        require(image_change(arr(browser_pixels),opening)<.035,"Native viewport misaligned")
        # Observe only: the cursor moves toward this real DOM control once
        # the native source clock starts. No screenshots during recording.
        opening_anchor=first_action_anchor(p,plan)
        source=out/"source.mp4";pts=[];events=[];pos=[W*.25,H*.2];pending_proof=[];timings=[]
        with (out/"capture.log").open("ab") as log:
            enc=subprocess.Popen(["ffmpeg","-v","error","-nostdin","-f","x11grab","-draw_mouse","0",
                "-video_size",f"{W*D}x{H*D}","-framerate","60","-i",display,"-t",str(SECONDS),
                "-c:v","libx264","-preset","ultrafast","-crf","20","-pix_fmt","yuv420p","-threads","4",
                "-an","-movflags","+faststart",str(source)],stderr=log)
        clock=time.monotonic()
        def now():return round(time.monotonic()-clock,6)
        def wait(t):time.sleep(max(0,t-now()))
        def move(x,y):
            p.mouse.move(x,y);pos[:]=[x,y];t=now()
            if t<SECONDS and (not pts or t>pts[-1]["t"]):pts.append({"t":t,"x":x*D,"y":y*D})
        def click(loc,label):
            loc.scroll_into_view_if_needed(timeout=3000);p.wait_for_timeout(100);r=loc.bounding_box()
            require(r and 0<=r["x"]<r["x"]+r["width"]<=W and 0<=r["y"]<r["y"]+r["height"]<=H,
                    "Target clipped before click")
            # Preserve the real stationary interval before a new approach.
            move(*pos)
            sx,sy=pos;tx=r["x"]+r["width"]/2;ty=r["y"]+r["height"]/2;start=time.monotonic()
            for i in range(1,13):
                q=i/12;q=q*q*(3-2*q)
                move(sx+(tx-sx)*q,sy+(ty-sy)*q)
                time.sleep(max(0,start+.48*i/12-time.monotonic()))
            require(loc.evaluate("e=>{let r=e.getBoundingClientRect(),h=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return h&&(h===e||e.contains(h))&&!e.closest('form,[data-private],[data-secret],[data-sensitive]')}"),"Target obstructed")
            move(*pos);p.mouse.down();t=now();p.wait_for_timeout(65);p.mouse.up();end=now()
            if label:
                events.extend([{"kind":"pointerdown","actionKind":"click","label":label,"t":t,"targetRect":native(r)},
                               {"kind":"pointerup","label":label,"t":end}])
        current=plan["picker"]
        try:
            move(*pos)
            opening_pointer_approach(move,wait,opening_anchor)
            for i,(action,expected) in enumerate(zip(plan["actions"],proofs)):
                wait(action_start(i,len(proofs)));started=now();before=screen(display);old=panel(p)
                current=apply(p,url,action,current,click)
                applied=now()
                try:
                    after,box,delta,t=verify(p,url,before,old,lambda _:screen(display),allow_localized=os.getenv("SAUCE_EVIDENCE_FIRST")=="1" and action["kind"]=="option")
                except StoryRejected as exc:
                    persist_screen(out/f"{i}-rejected-before.png",before)
                    persist_screen(out/f"{i}-rejected-after.png",screen(display))
                    save(out/"replay-rejection.json",{"index":i,"action_id":action["id"],"reason":str(exc)})
                    raise
                require(delta>=expected["delta"]*.6,"Replay lost investigated payoff")
                confirmed=round(t-clock,6)
                timings.append({"index":i,"start":started,"applied":applied,"confirmed":confirmed,"proof_complete":now()})
                save(out/"action-timing.json",timings)
                if confirmed>=SECONDS-2:
                    save(out/"timing-rejection.json",{"index":i,"confirmed":confirmed,"action_id":action["id"],"source_duration":SECONDS})
                    raise StoryRejected("Insufficient final source hold")
                events.append({"kind":"verified_result","label":action["label"],"t":confirmed,
                    "resultRect":native(box),"evidence":"Verified live same-product panel change; fraction "+str(round(delta,4))})
                pending_proof.append((i,before,after))
            wait(29);enc.wait(timeout=20);require(enc.returncode==0,"Native recording failed")
        finally:
            if enc.poll() is None:enc.terminate();enc.wait(timeout=10)
        for i,before,after in pending_proof:
            persist_screen(out/f"{i}-before.png",before);persist_screen(out/f"{i}-after.png",after)
        verify_live_terminal_frames(source,1800)
        cap=cv2.VideoCapture(str(source));cap.set(cv2.CAP_PROP_POS_FRAMES,20)
        good,f=cap.read();cap.release()
        require(good and float(np.mean(np.abs(cv2.resize(f,(480,270)).astype(float)-
                   cv2.resize(opening,(480,270)).astype(float))))<5,"Original source viewport mismatch")
        receipt={"source":url,"capture":"Chromium X11 native DPR2 60fps","source_sha256":sha(source),
            "cursorless":True,"capture_rect":{"width":W*D,"height":H*D},"frameCount":1800,
            "events":events,"pointer_samples":pts}
        save(out/"receipt.json",receipt)
        from scripts.verified_capture_receipt_adapter import convert
        manifest=convert(source,out/"receipt.json");save(out/"manifest.json",manifest)
        from scripts.quality_preview_supervisor import probe,full_rate_temporal_frames,transient_frame_reversion_finding
        stream=next(s for s in probe(source)["streams"] if s["codec_type"]=="video")
        require(not transient_frame_reversion_finding(full_rate_temporal_frames(source,stream),fps=60),"Original source transient viewport jump")
        return source,out/"manifest.json"

def render(folder,source,manifest,plan,calls,progress,audio):
    export=folder/"export";export.mkdir(mode=0o700,exist_ok=False)
    private=folder/"private"/"customer-story";filmplan=private/"film-plan.json"
    master=export/"master-1080p60.mp4"
    def run(script,*args,timeout=400):
        with (folder/"render.log").open("ab") as log:
            subprocess.run([sys.executable,str(ROOT/"scripts"/script),*map(str,args)],
                           cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=timeout)
    progress("rendering")
    run("source_event_director.py","--source",source,"--manifest",manifest,"--out",filmplan)
    common=("--video",source,"--manifest",manifest,"--film-plan",filmplan,"--customer-craft-contract")
    run("render_event_video.py",*common,"--validate-only")
    run("render_event_video.py",*common,"--output",master)
    # Optional owner-provisioned CC0 catalog, using the existing verified
    # picture-locked mixer (preserves real event Foley, unlike music replacement).
    music_root=os.getenv("SAUCE_CUSTOMER_MUSIC_ROOT") if audio=="auto" else None
    if music_root:
        mixes=private/"music"
        run("soundtrack_catalog.py","--root",music_root,"--film",master,
            "--foley",export/"source-verified-event-foley.wav","--receipt",export/"source-verified-foley-receipt.json",
            "--role","transformation","--out",mixes,"--foley-gain",.7,timeout=120)
        chosen=json.loads((mixes/"catalog.json").read_text())["selection"]["chosen"]
        # The existing catalog already verifies compressed picture identity.
        import shutil
        shutil.copyfile(mixes/(chosen+".mp4"),master)
    else:
        from backend.licensed_music_bed import licensed_music_from_env,add_music_to_master
        track=licensed_music_from_env() if audio=="auto" else None
        chosen=track.id if track else None
        if track:add_music_to_master(master,track,SECONDS,preserve_foley=True)
    from scripts.quality_preview_supervisor import analyze
    q=analyze(master,{"source_path":str(source),"source_sha256":sha(source),
          "event_manifest_path":str(manifest),"event_manifest_sha256":sha(manifest)},seconds=SECONDS)
    from scripts.customer_craft_contract import split_findings
    q["responsibility"]=split_findings(q)
    save(export/"encoded-quality.json",q)
    if q["responsibility"]["technical"]:
        raise RuntimeError("Customer craft rejected encoded technical defects: "+",".join(q["responsibility"]["technical"]))
    subprocess.run(["ffmpeg","-v","error","-xerror","-i",str(master),"-f","null","-"],check=True,timeout=100)
    editorial=None
    if os.getenv("SAUCE_CUSTOMER_ENCODED_REVIEW")=="1":
        from backend.customer_story_review import review
        editorial=review(master,q,source,manifest,plan,private/"encoded-review")
        calls+=editorial["ai_calls"]

    subprocess.run(["ffmpeg","-v","error","-i",str(master),"-vf","scale=1280:720:flags=lanczos,fps=30",
        "-c:v","libx264","-preset","fast","-crf","18","-c:a","aac","-movflags","+faststart",str(export/"preview.mp4")],check=True,timeout=120)
    release={"continuous_motion":True,"source_verified":True,"source_sha256":sha(source),
        "film_mode":"interactive","observed_actions":len(plan["actions"]),"recorded_source_fps":"60/1","master_fps":60,
        "render_mode":"native-source-event-story","encoded_quality_verdict":q["verdict"],
        "encoded_quality_findings":[x["code"] for x in q["findings"]],"creative_approved":False,
        "source_duration_seconds":SECONDS,"film_sha256":sha(master),"plan_sha256":sha(filmplan),
        "craft_contract":json.loads((export/"camera-metrics.json").read_text())["customerCraft"],
        "soundtrack":chosen,"encoded_quality_responsibility":q["responsibility"],
        "encoded_editorial":editorial}
    save(export/"release.json",release)
    from backend.url_engine import customer_quality_summary
    progress("needs_review")
    return {"status":"needs_review","title":plan["title"],"ai_calls":calls,
        "direction_source":"gemini-observed-story+deterministic-film-json","capture_mode":"interactive",
        "render_mode":release["render_mode"],"preview":"preview.mp4","narrated":False,
        **customer_quality_summary(release)}

def execute_story(url,folder,progress,*,audio="auto",brief=""):
    from backend.url_engine import NoVerifiedProductAction
    if audio=="narrated":raise NoVerifiedProductAction("30s story currently supports clean/auto audio")
    private=folder/"private"/"customer-story"
    try:
        progress("inspecting")
        plan,calls,proofs=explore(url,private,progress,brief=brief)
        progress("capturing")
        source,manifest=capture(plan["url"],plan,proofs,private/"native")
        return render(folder,source,manifest,plan,calls,progress,audio)
    except StoryRejected as e:
        if private.is_dir():save(private/"rejection.json",{"reason":str(e),"creative_approved":False})
        raise NoVerifiedProductAction(str(e)) from e
