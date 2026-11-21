#!/usr/bin/env python3
"""Opt-in, bounded, *public-site-only* interaction discovery for Sauce.

No login, form filling, purchases, external navigations, exports or LLM action
execution. Probe one allowlisted display-only candidate in a fresh browser
context. Admission requires authentic Chromium before/after screenshot pixels
AND a corroborating browser UI state change. No creative/premium approval.
"""
from __future__ import annotations
import argparse,hashlib,json,re,time
from pathlib import Path
from urllib.parse import urlsplit
import cv2,numpy as np
from playwright.sync_api import sync_playwright
from capture_safety import guard_route,validate_public_url
from basic_tour_discovery import settle_page

CHROME="/opt/devmcp-browsers/chromium_headless_shell-1254/chrome-headless-shell-linux64/chrome-headless-shell"
SELECTOR='button,[role="switch"],[role="tab"],input[type="checkbox"]'
BAD=re.compile(r"sign|log.?in|register|buy|checkout|pay|price|purchase|upgrade|pro\b|delete|remove|reset|clear|send|submit|upload|export|download|share|publish|save|connect|install|feedback|cookie|consent|account|profile|billing|invite|subscribe",re.I)
GOOD=re.compile(r"theme|mode|dark|light|contrast|palette|color|appearance|preview|design|style|tab|typography|view|layout|scheme|format|variant",re.I)
JS=r'''() => [...document.querySelectorAll('button,[role="switch"],[role="tab"],input[type="checkbox"]')]
 .map((e,i)=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);
 const label=(e.getAttribute("aria-label")||e.getAttribute("title")||
  e.innerText||e.getAttribute("value")||"").replace(/\s+/g," ").trim().slice(0,90);
 return {domIndex:i,tag:e.tagName,role:e.getAttribute("role")||"",
 label,x:r.x,y:r.y,w:r.width,h:r.height,
 disabled:e.disabled||e.getAttribute("aria-disabled")==="true",
 hidden:s.display==="none"||s.visibility==="hidden"||+s.opacity<.5,
 outer:e.outerHTML.slice(0,300)};})
 .filter(x=>x.label&&x.w>=18&&x.h>=18&&x.x>=0&&x.y>=0&&
  x.x+x.w<=innerWidth&&x.y+x.h<=innerHeight&&!x.disabled&&!x.hidden)'''
STATE=r'''() => ({
 url:location.href,
 theme:document.documentElement.className.slice(0,220),
 body:document.body.className.slice(0,220),
 text:document.body.innerText.slice(0,2500),
 dark:matchMedia("(prefers-color-scheme: dark)").matches,
 controls:[...document.querySelectorAll('button,[role="switch"],[role="tab"]')].slice(0,75).map(e=>e.getAttribute('aria-label')||e.getAttribute('title')||e.innerText||''),
 active:[...document.querySelectorAll('[aria-selected="true"],[aria-checked="true"]')]
     .slice(0,24).map(e=>(e.getAttribute("aria-label")||e.innerText||"").trim().slice(0,80))
})'''


def sha(raw):return hashlib.sha256(raw).hexdigest()

def safe_action(c):
    label=c["label"]
    if BAD.search(label+" "+c["outer"]):return False
    if not GOOD.search(label):return False
    if c["w"]>600 or c["h"]>180:return False
    # Read-only controls. Never click submit, links, form-associated inputs,
    # or anything an author has explicitly marked destructive.
    if "href=" in c["outer"] or "type=submit" in c["outer"]:
        return False
    return True


def diff_score(before:bytes,after:bytes):
    b=cv2.imdecode(np.frombuffer(before,np.uint8),cv2.IMREAD_COLOR)
    a=cv2.imdecode(np.frombuffer(after,np.uint8),cv2.IMREAD_COLOR)
    if b is None or a is None or a.shape!=b.shape:raise ValueError("Unmatched real screenshots")
    b=cv2.resize(b,(640,400),interpolation=cv2.INTER_AREA)
    a=cv2.resize(a,(640,400),interpolation=cv2.INTER_AREA)
    d=np.max(cv2.absdiff(a,b),axis=2)
    return {"changedFraction":round(float(np.mean(d>24)),5),
            "meanChannelDelta":round(float(np.mean(d)),3)}

def select_story_actions(report):
    """Two complementary, real before/after admitted UI states or REFUSE.

    Pure generic UI taxonomy and visible-pixel evidence. Never infer a
    product feature that was not seen on the original public page.
    """
    if report.get("schema")!="sauce-public-ui-scout-v1":
        raise ValueError("Verified public browser scout receipt required")
    choices=report.get("accepted",[])
    if not isinstance(choices,list):raise ValueError("No source UI candidates")
    def category(label):
        label=label.lower()
        if any(x in label for x in ("theme","dark","light","appearance","mode")):
            return "appearance"
        if any(x in label for x in ("contrast","matrix","analysis","info","details","preview")):
            return "inspection"
        if any(x in label for x in ("palette","color","typography","style","layout","design")):
            return "composition"
        return "other"
    ranked=[]
    for c in choices:
        if not isinstance(c,dict) or c.get("status")!="verified_display_change":
            continue
        if not safe_action({**c,"outer":"","w":c["originalRect"]["w"],
                           "h":c["originalRect"]["h"]}):
            continue
        changed=c["pixel"]["changedFraction"]
        if type(changed) not in (int,float) or changed<.025:continue
        role=category(c["label"])
        utility=.075 if any(word in c["label"].lower()
              for word in ("contrast","matrix","analysis")) else (
              .025 if role=="inspection" else 0.)
        ranked.append((round(changed+utility,5),role,c))
    ranked.sort(key=lambda entry:entry[0],reverse=True)
    if not ranked:raise ValueError("No evidence-admitted visual action")
    first=ranked[0]
    others=[x for x in ranked[1:] if x[1]!=first[1] and
            x[2]["label"]!=first[2]["label"]]
    if not others:
        raise ValueError("No second distinct verified public product state")
    selected=[first,others[0]]
    return {"schema":"sauce-autoselected-source-actions-v1",
            "origin":report["observedLandingUrl"],
            "premiumApproved":False,
            "selectionMethod":"two-distinct-semantic-roles-from-original-browser-pixel-evidence",
            "actions":[{"label":x[2]["label"],"role":x[1],
                        "score":x[0],"originalBeforeSha256":x[2]["beforeSha256"],
                        "originalAfterSha256":x[2]["afterSha256"]}
                       for x in selected]}


def page_visit(browser,url,allowed_host):
    context=browser.new_context(viewport={"width":1280,"height":800},
        device_scale_factor=2,accept_downloads=False,service_workers="block",
        permissions=[],reduced_motion="reduce")
    context.route("**/*",guard_route)
    page=context.new_page()
    response=page.goto(url,wait_until="domcontentloaded",timeout=25000)
    if not response or response.status>=400 or (urlsplit(page.url).hostname or "").lower()!=allowed_host:
        context.close()
        raise ValueError("Denied navigation / failed original public site")
    settle_page(page)
    return context,page

def discover(url,allowed_host,*,max_probes=8,out:Path|None=None):
    host=(urlsplit(validate_public_url(url)).hostname or "").lower()
    if host!=allowed_host.lower():
        raise ValueError("Site must be explicitly allowlisted for this private experiment")
    if not 1<=max_probes<=12:raise ValueError("Candidate budget exceeded")
    out=Path(out) if out else None
    if out:out.mkdir(parents=True,exist_ok=True)
    results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=CHROME,headless=True,
            args=["--disable-dev-shm-usage","--no-sandbox"])
        ctx,page=page_visit(browser,url,host)
        try:
            canonical=page.url
            candidates=[c for c in page.evaluate(JS) if safe_action(c)]
            if out: (out/"observed-candidates.json").write_text(json.dumps(candidates,indent=2)+"\n")
        finally:ctx.close()
        for c in candidates[:max_probes]:
            probe_ctx=None
            try:
                probe_ctx,probe=page_visit(browser,canonical,host)
                available=probe.evaluate(JS)
                controls=[x for x in available if x["label"]==c["label"] and
                          x["tag"]==c["tag"] and safe_action(x)]
                if len(controls)!=1:
                    results.append({"label":c["label"],"status":"ambiguous_or_missing"})
                    continue
                actual=controls[0]
                prior=probe.evaluate(STATE)
                visible=probe.screenshot(type="png",animations="disabled")
                probe.wait_for_timeout(220)
                stationary=probe.screenshot(type="png",animations="disabled")
                source_drift=diff_score(visible,stationary)
                visible=stationary
                cx=actual["x"]+actual["w"]/2
                cy=actual["y"]+actual["h"]/2
                probe.mouse.move(cx,cy,steps=8)
                probe.mouse.click(cx,cy,delay=85)
                probe.wait_for_timeout(450)
                if ((urlsplit(probe.url).hostname or "").lower()!=host or
                    urlsplit(probe.url).path!=urlsplit(canonical).path):
                    results.append({"label":c["label"],"status":"navigation_rejected"})
                    continue
                after=probe.screenshot(type="png",animations="disabled")
                latter=probe.evaluate(STATE)
                score=diff_score(visible,after)
                changed=prior["theme"]!=latter["theme"] or prior["body"]!=latter["body"] or prior["text"]!=latter["text"] or prior["active"]!=latter["active"] or prior["controls"]!=latter["controls"]
                admitted=(score["changedFraction"]>=max(.025,
                           3*source_drift["changedFraction"]) and changed)
                item={"label":c["label"],"tag":c["tag"],"role":c["role"],
                    "status":"verified_display_change" if admitted else "weak_or_unconfirmed",
                    "origin":canonical,"pixel":score,"domChanged":changed,
                    "baselineDriftFraction":source_drift["changedFraction"],
                    "originalRect":{k:round(actual[k],2) for k in ("x","y","w","h")},
                    "beforeSha256":sha(visible),"afterSha256":sha(after)}
                results.append(item)
                if admitted and out:
                    stem=f"probe-{len(results):02d}"
                    (out/(stem+"-before.png")).write_bytes(visible)
                    (out/(stem+"-after.png")).write_bytes(after)
            except Exception as ex:
                results.append({"label":c["label"],"status":"failed_closed",
                                "error":type(ex).__name__})
            finally:
                if probe_ctx:probe_ctx.close()
        browser.close()
    accepted=[x for x in results if x["status"]=="verified_display_change"]
    accepted.sort(key=lambda x:(x["pixel"]["changedFraction"],x["pixel"]["meanChannelDelta"]),reverse=True)
    report={"schema":"sauce-public-ui-scout-v1","origin":url,
        "observedLandingUrl":canonical,"approvedPremiumFilm":False,
        "maxProbes":max_probes,"probed":len(results),"accepted":accepted,"allResults":results}
    try:
        report["autoActionPlan"]=select_story_actions(report)
    except ValueError:
        report["autoActionPlan"]=None
    if out:(out/"scout-evidence.json").write_text(json.dumps(report,indent=2)+"\n")
    return report

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--url",required=True)
    ap.add_argument("--allow-host",required=True)
    ap.add_argument("--out",required=True,type=Path)
    ap.add_argument("--max-probes",type=int,default=8)
    a=ap.parse_args()
    print(json.dumps(discover(a.url,a.allow_host,max_probes=a.max_probes,out=a.out),indent=2))
