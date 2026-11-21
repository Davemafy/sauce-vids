"""Compile a validated conversational plan into Sauce's existing session workflow.

Only independently observed, read-only links can generate clicks. Browser
resolves DOM selectors; model strings cannot become executable selectors.
This experiment never runs costly or destructive actions.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from backend.product_explorer import CHROME, JS
from backend.story_discovery import public_same_origin
from scripts.capture_safety import guard_route,validate_public_url
from scripts.session_contract import validate_actions
from scripts.conversation_director_experiment import validate_compilation


def normalize_route(url):
    p=urlsplit(url)
    return p.scheme,p.netloc.lower(),p.path.rstrip("/") or "/"


def resolve_readonly_link(plan_step,report,page):
    pages={p["id"]:p for p in report["pages"]}
    data=pages[plan_step["page_id"]]
    control=next((c for c in data["controls"] if c["id"]==plan_step["control_id"]),None)
    if not control or control["policy"]["class"]!="read_only_navigation":
        raise ValueError("Non-navigation or unauthorized action cannot be compiled")
    if not public_same_origin(control.get("href"),report["requested_url"]):
        raise ValueError("Cross-origin or unsafe navigation prevented")
    if normalize_route(page.url)!=normalize_route(data["url"]):
        raise ValueError("Observed source page not active")
    fresh=page.evaluate(JS)
    matches=[c for c in fresh["controls"]
             if c["kind"]=="link" and c["text"]==control["text"]
             and c.get("href")==control["href"]]
    if len(matches)!=1:
        raise ValueError("Observed source control changed or became ambiguous")
    actual=matches[0]
    selector=actual["selector"]
    target=page.locator(selector)
    if target.count()!=1 or not target.is_visible():
        raise ValueError("Observed control is missing or not visible")
    if target.evaluate("(e)=>e.href")!=control["href"]:
        raise ValueError("Live target points somewhere else")
    return selector,control


def compiled_readonly_workflow(report,plan,private_dir):
    from playwright.sync_api import sync_playwright
    # Validate the complete input before any action is allowed.
    candidate=validate_compilation(plan,report)
    private_dir=Path(private_dir);private_dir.mkdir(parents=True,exist_ok=True)
    source=report["requested_url"]
    validate_public_url(source)
    actions=[{"action":"wait","ms":350,"settle_ms":220}]
    evidence=[]
    with sync_playwright() as p:
        b=p.chromium.launch(headless=True,executable_path=CHROME,
                             args=["--no-sandbox","--disable-dev-shm-usage"])
        try:
            context=b.new_context(viewport={"width":1280,"height":720},
                                  device_scale_factor=2,service_workers="block")
            context.route("**/*",guard_route)
            page=context.new_page()
            response=page.goto(source,wait_until="domcontentloaded",timeout=28000)
            if response and response.status>=400:
                raise RuntimeError("Public site inaccessible")
            page.wait_for_timeout(950)
            for step in candidate["steps"]:
                if step["type"]=="propose_action":
                    evidence.append({"id":step["control_id"],"status":"not_authorized_not_executed"})
                    continue
                if step["type"]=="inspect":
                    if step["quote"] not in " ".join(page.locator("body").inner_text().split()):
                        raise RuntimeError("Planned source quote no longer found in current page")
                    actions.append({"action":"wait","ms":min(1700,max(550,len(step["quote"])*16)),
                                    "settle_ms":150})
                    evidence.append({"quote":step["quote"],"status":"source_text_observed_not_claim_verified"})
                    continue
                selector,control=resolve_readonly_link(step,report,page)
                actions.extend([
                    {"action":"hover","selector":selector,"settle_ms":400},
                    {"action":"click","selector":selector,"settle_ms":1200}
                ])
                page.locator(selector).click()
                page.wait_for_timeout(1050)
                if not public_same_origin(page.url,source):
                    raise RuntimeError("Navigation escaped originally verified origin")
                if normalize_route(page.url)!=normalize_route(control["href"]):
                    raise RuntimeError("Navigation did not reach observed destination")
                fragment=urlsplit(control["href"]).fragment
                if fragment:
                    section=page.locator("#"+fragment)
                    if section.count()!=1 or not section.is_visible():
                        raise RuntimeError("Observed anchor destination not visible")
                    # Respect native anchor scroll; don't invent a zoom target.
                evidence.append({"id":step["control_id"],"status":"read_only_navigation_observed",
                                 "destination":page.url})
            actions.append({"action":"wait","ms":1400,"settle_ms":150})
            page.screenshot(path=str(private_dir/"verified-final-source.png"),
                            animations="disabled")
        finally:
            b.close()
    if not any(x["action"]=="click" for x in actions):
        raise ValueError("No independently verified read-only action to film")
    validate_actions(actions)
    (private_dir/"capture-workflow.json").write_text(json.dumps(actions,indent=2)+"\n")
    (private_dir/"execution-preflight.json").write_text(json.dumps({
        "origin":source,"schema":"sauce-capture-preflight-receipt-v1",
        "resolved_actions":evidence,"executed":True,
        "expensive_actions_executed":0,"human_film_approved":False,
        "action_verification":"navigation_only_not_live_application_outcome"
    },indent=2)+"\n")
    return actions


def main():
    a=argparse.ArgumentParser()
    a.add_argument("--research",type=Path,required=True)
    a.add_argument("--plan",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    args=a.parse_args()
    report=json.loads(args.research.read_text())
    raw=json.loads(args.plan.read_text())
    actions=compiled_readonly_workflow(report,raw,args.out)
    print(json.dumps({"actions":actions,
                      "workflow":str(args.out/"capture-workflow.json"),
                      "expensive_actions_executed":0},indent=2))

if __name__=="__main__":
    main()
