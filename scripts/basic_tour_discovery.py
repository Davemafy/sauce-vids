"""EXPERIMENTAL browser-only Sauce Basic preflight.

No recording, public HTTP API, login, forms, clicks or writes to a website.
An isolated egress-filtered container is still required for untrusted users.
"""
from __future__ import annotations
import argparse
import json
from dataclasses import replace
import os
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

from basic_tour_planner import (
    Link, Page, Section, TourContract, canonical_url, create_preflight,
)
from capture_safety import validate_public_url, guard_route

USER_AGENT = "SauceBasicPreviewBot/0.1 (+https://github.com/Davemafy/sauce-vids)"
DOM_SNAPSHOT = r"""() => {
  const doc = document.documentElement;
  const vh = Math.max(240, Math.round(innerHeight));
  const links = [...document.querySelectorAll('a[href]')].slice(0, 250);
  function linkArea(a) {
    if (a.closest('header')) return 'header';
    if (a.closest('nav, [role="navigation"]')) return 'nav';
    if (a.closest('[role="menu"],[aria-haspopup]')) return 'dropdown';
    if (a.closest('footer')) return 'footer';
    return 'body';
  }
  const seen = new Set();
  let sections = [...document.querySelectorAll(
    'main section, [role="main"] section, main article, [role="main"] article, main [id], section[id]'
  )].filter(e => {
    const r=e.getBoundingClientRect();
    return r.width>150 && r.height>48;
  }).slice(0, 120);
  return {
    title: document.title,
    height: Math.max(vh, doc.scrollHeight, document.body?.scrollHeight||0),
    viewport_height: vh,
    anchor_ids: [...document.querySelectorAll("[id]")].slice(0,300)
      .map(e=>e.id).filter(Boolean),
    links: links.map(a => ({
      href:a.getAttribute('href')||'',
      label:(a.innerText||a.getAttribute('aria-label')||'').trim().slice(0,120),
      area:linkArea(a)
    })),
    sections: sections.map((e,i) => {
      const r=e.getBoundingClientRect();
      const t=(e.innerText||'').replace(/\s+/g,' ').trim();
      return {
        id:(e.id||('section-'+i)).slice(0,100),
        top:Math.max(0,Math.round(r.top+scrollY)),
        height:Math.max(0,Math.round(r.height)),
        words:Math.min(1000,t?t.split(' ').length:0),
        title:(e.querySelector('h1,h2,h3')?.innerText||'').trim().slice(0,120)
      }
    })
  };
}"""


def read_page(page, url: str) -> Page:
    """The only source of page facts is the real browser DOM."""
    facts = page.evaluate(DOM_SNAPSHOT)
    return Page(
        url, facts["title"] or urlsplit(url).path or "/",
        max(facts["height"], facts["viewport_height"]),
        facts["viewport_height"],
        tuple(Section(**s) for s in facts["sections"]),
        tuple(Link(**link) for link in facts["links"]),
        tuple(facts["anchor_ids"])
    )



def discover_hover_navigation(page, observed: Page, *, limit: int=16) -> Page:
    """Reveal safe hover-only nav children without clicking or submitting.

    Uses actual browser hover and DOM observations. It does not claim to
    discover click-only menus, authenticated routes or inaccessible content.
    """
    links={(link.href,link.area):link for link in observed.links}
    anchors=set(observed.anchor_ids)
    items=page.locator("header button, nav button, header [aria-haspopup], nav [aria-haspopup]")
    for i in range(min(items.count(),limit)):
        try:
            item=items.nth(i)
            if not item.is_visible():
                continue
            item.hover(timeout=800)
            page.wait_for_timeout(90)
            newer=read_page(page,observed.url)
            for link in newer.links:
                links.setdefault((link.href,link.area),link)
            anchors.update(newer.anchor_ids)
        except Exception:
            # Hover-specific discovery failure must not destroy homepage proof.
            continue
    page.evaluate("window.scrollTo(0,0)")
    return Page(observed.url,observed.title,observed.height,
                observed.viewport_height,observed.sections,
                tuple(links.values()),tuple(sorted(anchors)))


def settle_page(page) -> None:
    """Bounded readiness check; never rely on networkidle alone."""
    page.wait_for_function(
        "() => document.readyState==='interactive' || document.readyState==='complete'",
        timeout=6000
    )
    page.wait_for_timeout(450)
    page.evaluate("""async () => {
      const visible = [...document.images].filter(i=>{
        const r=i.getBoundingClientRect();
        return r.width>12 && r.height>12 && r.top<innerHeight*2;
      }).slice(0,36);
      await Promise.race([
        Promise.all(visible.map(i=>i.decode().catch(()=>{}))),
        new Promise(r=>setTimeout(r,1400))
      ]);
    }""")
    # The full recorder needs additional visual-stability/skeleton checks.
    # This prototype samples scroll geometry to inform the contract only.


def trigger_lazy_content(page, max_steps: int=12) -> dict:
    """Bounded REAL-wheel lazy trigger; report when coverage is incomplete."""
    initial=int(page.evaluate("document.documentElement.scrollHeight"))
    previous=-1
    steps=0
    for _ in range(max_steps):
        position=int(page.evaluate("window.scrollY"))
        height=int(page.evaluate("document.documentElement.scrollHeight"))
        viewport=int(page.evaluate("window.innerHeight"))
        if position >= height-viewport-1:
            break
        if position==previous:
            break
        previous=position
        page.mouse.wheel(0,min(630,height-position))
        steps+=1
        page.wait_for_timeout(170)
    final_height=int(page.evaluate("document.documentElement.scrollHeight"))
    at_bottom=bool(page.evaluate(
        "window.scrollY>=document.documentElement.scrollHeight-innerHeight-2"))
    capped=steps>=max_steps and not at_bottom
    # Reset page to the top; no fake content or state mutations.
    page.evaluate("window.scrollTo(0,0)")
    page.wait_for_timeout(150)
    return {"steps":steps,"max_steps":max_steps,"initial_height":initial,
            "final_height":final_height,"at_bottom":at_bottom,"capped":capped,
            "content_grew":final_height>initial+2}


def normalized_landing_route(requested: str, final: str) -> str | None:
    """Accept only safe canonical same-origin root redirects.

    Many sites redirect / to /welcome or /home. Do not turn a specific
    product page into a different page, login, query route, or new host.
    """
    original,_,error=canonical_url(requested,requested)
    reached,anchor,why=canonical_url(requested,final)
    if error or why or anchor:
        return None
    if reached==original:
        return reached
    root_path=urlsplit(requested).path
    if root_path not in ("","/"):
        return None
    return reached


def get_robots(page, root_url: str) -> RobotFileParser:
    url=urljoin(root_url,"/robots.txt")
    resp=page.goto(url,wait_until="domcontentloaded",timeout=9000)
    parser=RobotFileParser()
    parser.set_url(url)
    if resp and resp.status==404:
        parser.parse([])
        return parser
    if not resp or resp.status!=200:
        raise RuntimeError("robots_unavailable")
    text=page.locator("body").inner_text(timeout=3500)[:256_000]
    parser.parse(text.splitlines())
    return parser


def crawl_public_site(contract: TourContract, *, allowed_hosts: tuple[str,...]=(),
                      chromium_path: str | None=None) -> dict:
    """Bounded local preflight. Not ready for exposure to arbitrary customers.

    Existing public URL checks and guarded Playwright requests are reused.
    Production additionally requires network-level private-IP egress denial to
    address DNS rebinding / redirects and a separate hardened container.
    """
    root_host=(urlsplit(contract.root_url).hostname or "").lower()
    if not allowed_hosts or root_host not in {h.lower() for h in allowed_hosts}:
        raise ValueError("Experimental crawler requires an explicit test-host allowlist")
    if sync_playwright is None:
        raise RuntimeError("Playwright is required for browser discovery")
    validate_public_url(contract.root_url)
    observed=[]
    skipped=[]
    seed,_,why=canonical_url(contract.root_url,contract.root_url)
    if why:
        raise ValueError(why)
    requested_root=seed
    todo=[(seed,0)]
    seen=set()
    with sync_playwright() as pw:
        browser=pw.chromium.launch(
            executable_path=chromium_path or os.environ.get("SAUCE_CHROME_BIN") or
            "/opt/devmcp-browsers/chromium_headless_shell-1254/chrome-headless-shell-linux64/chrome-headless-shell",
            headless=True, args=["--disable-dev-shm-usage","--no-sandbox"]
        )
        context=browser.new_context(
            viewport={"width":contract.width,"height":contract.height},
            user_agent=USER_AGENT, accept_downloads=False,
            service_workers="block", permissions=[]
        )
        context.route("**/*",guard_route)
        page=context.new_page()
        try:
            robots=get_robots(page,contract.root_url)
            while todo and len(observed)<contract.max_pages:
                url,depth=todo.pop(0)
                if url in seen:
                    continue
                seen.add(url)
                if not robots.can_fetch(USER_AGENT,url):
                    skipped.append({"url":url,"reason":"robots_disallow"})
                    continue
                try:
                    validate_public_url(url)
                    response=page.goto(url,wait_until="domcontentloaded",timeout=18000)
                    if not response or response.status>=400:
                        raise RuntimeError("HTTP_"+str(response.status if response else "none"))
                    landing=normalized_landing_route(url,page.url)
                    if landing is None:
                        raise RuntimeError("cross_origin_or_query_redirect")
                    if landing!=url:
                        if url!=requested_root:
                            raise RuntimeError("nonroot_route_changed")
                        # Canonicalize / -> /welcome only on original home.
                        seed=landing
                        url=landing
                        seen.add(url)
                        contract=replace(contract,root_url=landing)
                    settle_page(page)
                    lazy_probe=trigger_lazy_content(page)
                    if lazy_probe["capped"]:
                        skipped.append({"url":url,"reason":"lazy_preflight_step_limit",
                                        "steps":lazy_probe["steps"]})
                    dom=read_page(page,url)
                    dom=discover_hover_navigation(page,dom)
                    observed.append(dom)
                    if contract.scope=="homepage" or depth>=contract.max_depth:
                        continue
                    for link in dom.links:
                        if (contract.scope=="navigation" and
                                link.area not in ("nav","header","dropdown")):
                            continue
                        dest,anchor,reason=canonical_url(contract.root_url,
                                                       urljoin(url,link.href))
                        if reason or anchor or not dest or dest==url:
                            continue
                        if dest not in seen and dest not in [x[0] for x in todo]:
                            todo.append((dest,depth+1))
                    page.wait_for_timeout(400) # modest crawl interval
                except Exception as exc:
                    skipped.append({"url":url,"reason":type(exc).__name__+":"+str(exc)[:100]})
            for url,depth in todo:
                if url not in seen:
                    skipped.append({"url":url,"reason":"page_limit"})
        finally:
            context.close()
            browser.close()
    if not observed or observed[0].url!=seed:
        return {"schema":"sauce.basic.tour.v1","status":"failed_preflight",
                "selected":[],"skipped":skipped}
    plan=create_preflight(contract,observed)
    if seed!=requested_root:
        plan["requested_root_url"]=requested_root
        plan["redirected_root_url"]=seed
    plan["skipped"].extend(skipped)
    from collections import Counter
    plan["skipped_by_reason"]=dict(sorted(
        Counter(row["reason"] for row in plan["skipped"]).items()))
    plan["skipped_unique_routes_by_reason"]={
        reason:len({row.get("url") or row.get("href") or row.get("source")
                    for row in plan["skipped"] if row["reason"]==reason})
        for reason in plan["skipped_by_reason"]
    }
    plan["status"]="preflight_only"
    return plan


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--url",required=True)
    parser.add_argument("--scope",choices=("homepage","navigation","all"),default="navigation")
    parser.add_argument("--max-pages",type=int,default=6)
    parser.add_argument("--out",required=True,type=Path)
    parser.add_argument("--allow-host",action="append",default=[],
                        help="Required explicit test-site host allowlist")
    parser.add_argument("--experimental",action="store_true",
                        help="A one-off local study only, not safe for a public endpoint")
    args=parser.parse_args()
    if not args.experimental:
        parser.error("Experimental preflight requires --experimental")
    contract=TourContract(args.url,scope=args.scope,max_pages=args.max_pages)
    result=crawl_public_site(contract,allowed_hosts=tuple(args.allow_host))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2))
    print(json.dumps({"status":result["status"],
        "pages":len(result["selected"]),
        "skipped":len(result["skipped"]),
        "estimated_seconds":result.get("estimated_seconds"),
        "output":str(args.out)},indent=2))


if __name__=="__main__":
    main()
