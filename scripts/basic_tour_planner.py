"""Pure deterministic planning contract for Sauce Basic website tours.

No model inference, filesystem side effects, network access, or renderer changes.
The same plan drives preflight duration estimates and future wheel playback.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from hashlib import sha256
import json
import math
from collections import Counter
import re
from urllib.parse import urljoin, urlsplit, urlunsplit, unquote

SCHEMA = "sauce.basic.tour.v1"
SAFE_METHOD = "GET"
DANGEROUS = re.compile(
    r"(^|[-_/])(logout|log-out|signout|sign-out|delete|remove|destroy|"
    r"unsubscribe|deactivate|reset-password|checkout|purchase|pay|payment|"
    r"download|billing|admin|invite|revoke)([-_/]|$)", re.I)
WHEEL_HZ = 30
MAX_SCROLL_SPEED = 800.0        # CSS pixels/second, including ease peak
MAX_SCROLL_ACCEL = 1200.0       # CSS pixels/second²
MAX_PAGE_HEIGHT = 100_000       # do not auto-tour infinite documents


def canonical_url(base: str, href: str) -> tuple[str | None, str | None, str]:
    """Return (same-origin URL, optional anchor, skip reason).

    Avoid query-driven infinite page discovery, side-effect GET routes and
    external links. This is *not* an SSRF protection boundary: the browser
    still requires egress firewall + redirect / DNS checks.
    """
    if not isinstance(base, str) or not isinstance(href, str):
        return None, None, "invalid_link"
    if len(href) > 2048 or not href.strip():
        return None, None, "invalid_link"
    try:
        raw = urlsplit(href.strip())
        if raw.scheme and raw.scheme.lower() not in ("https", "http"):
            return None, None, "non_http"
        page = urlsplit(base)
        link = urlsplit(urljoin(base, href))
        if page.scheme not in ("https", "http") or not page.hostname:
            raise ValueError("Base must be HTTP(S) URL")
        if (link.scheme != page.scheme or link.hostname != page.hostname or
                link.port != page.port or link.username or link.password):
            return None, None, "external_or_unsafe"
        if link.query or page.query:
            return None, None, "query_route"
        path = re.sub(r"/{2,}", "/", link.path or "/")
        if DANGEROUS.search(unquote(path)):
            return None, None, "possibly_destructive"
        if re.search(r"\.(?:pdf|zip|tar|gz|exe|dmg|mp4|mp3|jpg|png|webp|svg)$", path, re.I):
            return None, None, "download_or_asset"
        if path != "/" and path.endswith("/"):
            path = path[:-1]
        route = urlunsplit((link.scheme, link.netloc.lower(), path, "", ""))
        anchor = unquote(link.fragment)[:150] if link.fragment else None
        return route, anchor, ""
    except (ValueError, UnicodeError):
        return None, None, "invalid_url"


@dataclass(frozen=True)
class Link:
    href: str
    label: str = ""
    area: str = "body"     # header, nav, dropdown, body, footer


@dataclass(frozen=True)
class Section:
    id: str
    top: int
    height: int
    words: int = 0
    title: str = ""

    def __post_init__(self):
        if self.top < 0 or self.height < 0 or self.words < 0:
            raise ValueError("Negative section measurements")


@dataclass(frozen=True)
class Page:
    url: str
    title: str
    height: int
    viewport_height: int
    sections: tuple[Section, ...] = ()
    links: tuple[Link, ...] = ()
    anchor_ids: tuple[str, ...] = ()

    def __post_init__(self):
        if self.height < self.viewport_height or self.viewport_height < 240:
            raise ValueError("Invalid page height / viewport")


@dataclass(frozen=True)
class TourContract:
    root_url: str
    scope: str = "navigation"  # homepage | navigation | all
    max_pages: int = 12
    max_depth: int = 2
    max_minutes: int = 10
    profile: str = "balanced"  # relaxed | balanced | quick
    fps: int = 60
    width: int = 1280
    height: int = 720
    audio: str = "silent"
    transitions: str = "hard_cut"
    chapters: str = "metadata"
    retention_days: int = 7

    def __post_init__(self):
        from urllib.parse import urlsplit
        p = urlsplit(self.root_url)
        if p.scheme not in ("https", "http") or not p.hostname or p.username or p.password or p.query or p.fragment:
            raise ValueError("Root must be a query-free public HTTP(S) URL")
        if self.scope not in ("homepage", "navigation", "all"):
            raise ValueError("Unsupported coverage scope")
        if not (1 <= self.max_pages <= 50 and 0 <= self.max_depth <= 5 and 1 <= self.max_minutes <= 60):
            raise ValueError("Unbounded page/depth/duration limits")
        if self.profile not in ("relaxed", "balanced", "quick"):
            raise ValueError("Unsupported pacing profile")
        if ((self.width, self.height) not in ((1280, 720), (1920, 1080))
                or (self.fps, self.audio, self.transitions,
                    self.chapters, self.retention_days) != (
                    60, "silent", "hard_cut", "metadata", 7)):
            raise ValueError("V1 contract must preserve landscape film/retention defaults")
        route, anchor, reason = canonical_url(self.root_url, self.root_url)
        if reason or anchor:
            raise ValueError("Invalid root URL")

    def manifest(self) -> dict:
        return {"schema": SCHEMA, **asdict(self)}


def discover_routes(pages: list[Page], contract: TourContract) -> dict:
    """Stable breadth-first discovery using supplied observed DOM facts.

    The caller must obtain Page facts from real browser visits (not guessed
    routes); this function cannot independently prove a URL is reachable.
    """
    if not pages:
        raise ValueError("Missing observed home page")
    index = {}
    for p in pages:
        url, _, reason = canonical_url(contract.root_url, p.url)
        if not reason and url not in index:
            index[url] = p
    root, _, reason = canonical_url(contract.root_url, contract.root_url)
    if reason or root not in index:
        raise ValueError("Root page has no real DOM observation")
    selected = []
    skipped = []
    anchors: dict[str, list[dict]] = {}
    queue = [(root, 0)]
    seen = set()
    while queue:
        url, depth = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        if len(selected) >= contract.max_pages:
            skipped.append({"url":url,"reason":"page_limit"})
            continue
        page = index.get(url)
        if page is None:
            skipped.append({"url":url,"reason":"not_observed_or_unreachable"})
            continue
        selected.append({"url":url,"title":page.title,"depth":depth})
        anchor_list = []
        for link in page.links:
            route, anchor, why = canonical_url(contract.root_url, urljoin(url, link.href))
            if why:
                skipped.append({"source":url,"href":link.href[:200],"reason":why})
                continue
            if route == url and anchor:
                if anchor not in page.anchor_ids:
                    skipped.append({"source":url,"href":link.href[:200],
                                    "reason":"unresolved_anchor"})
                elif anchor not in [a["id"] for a in anchor_list]:
                    anchor_list.append({"id":anchor,"label":link.label[:120]})
                continue
            if contract.scope == "homepage":
                continue
            if contract.scope == "navigation" and link.area not in ("header","nav","dropdown"):
                continue
            if link.area not in ("header","nav","dropdown","body","footer"):
                continue
            if depth < contract.max_depth and route not in seen and (route,depth+1) not in queue:
                queue.append((route,depth+1))
            elif depth >= contract.max_depth:
                skipped.append({"source":url,"url":route,"reason":"depth_limit"})
        anchors[url] = anchor_list
    return {"pages":selected,"anchors":anchors,"skipped":skipped,
            "total_observed":len(index), "scope":contract.scope}


def ease(u: float) -> float:
    """Quintic smootherstep, derivatives are 0 at section endpoints."""
    x = min(1.0,max(0.0,float(u)))
    return x*x*x*(x*(x*6.0-15.0)+10.0)


def scroll_duration(distance: float, profile: str="balanced") -> float:
    """Speed and acceleration bounds of an exact quintic trajectory."""
    if distance < 0:
        raise ValueError("Negative scroll")
    speed_multiplier = {"relaxed":.68,"balanced":1.0,"quick":1.2}[profile]
    max_v = MAX_SCROLL_SPEED * speed_multiplier
    max_a = MAX_SCROLL_ACCEL * speed_multiplier
    # quintic max velocity = 1.875 D/T; acceleration <= 5.774 D/T².
    return max(0.0,1.875*distance/max_v,
               math.sqrt(5.774*distance/max_a) if distance else 0.0)


def wheel_steps(start: int, end: int, profile: str="balanced") -> list[dict]:
    """Timed signed wheel deltas. Execute with real Playwright mouse.wheel.

    Timestamps are derived from this plan, rather than recomputed in the
    recorder. This exact function MUST also run during preflight estimates.
    """
    distance=end-start
    if distance < 0:
        raise ValueError("The Basic tour scrolls downward")
    if distance == 0:
        return []
    seconds=scroll_duration(distance,profile)
    n=max(1,math.ceil(seconds*WHEEL_HZ))
    past=0.0
    steps=[]
    for i in range(1,n+1):
        current=distance*ease(i/n)
        dy=current-past
        steps.append({"at_ms":round(i*seconds*1000/n,3),
                      "dy":round(dy,4)})
        past=current
    # Fix the tiny rounding error in the final wheel step.
    steps[-1]["dy"]=round(steps[-1]["dy"]+(distance-sum(s["dy"] for s in steps)),4)
    return steps


def hold_seconds(words: int, profile: str="balanced") -> float:
    """Bounded reading opportunity, not a claim viewers read every word."""
    baseline=max(.6,min(4.0,.65+.032*min(words,120)))
    return round(baseline*{"relaxed":1.35,"balanced":1.0,"quick":.8}[profile],3)


def plan_page(page: Page, contract: TourContract) -> dict:
    """Dry-run timeline used unchanged by the future recorder."""
    max_scroll=min(page.height,MAX_PAGE_HEIGHT)-page.viewport_height
    if page.height>MAX_PAGE_HEIGHT:
        cap_reason="height_limit"
    else:
        cap_reason=None
    # One hold per screenful; do not add a second hold for every nearby
    # nested section or anchor. The previous grid+all-section union silently
    # doubled the stops on complex landing pages.
    step=max(240,page.viewport_height-90)
    positions=sorted({0, max(0,max_scroll),*range(step,max_scroll,step)})
    def visible_words(pos:int) -> tuple[int,list[str]]:
        visible=[]
        for section in page.sections:
            area=max(0, min(pos+page.viewport_height,section.top+section.height)
                       - max(pos,section.top))
            if area <= 0:
                continue
            word_fraction=round(section.words*area/max(1,section.height))
            visible.append((word_fraction,section.id))
        # Nested DOM sections often count the same words repeatedly.
        # Use the largest visible estimate, not their unbounded sum.
        words=max((n for n,_ in visible),default=8)
        return words,[ident for _,ident in visible]
    duration_ms=0.0
    steps=[]
    for i,pos in enumerate(positions):
        previous=positions[i-1] if i else 0
        wheels=wheel_steps(previous,pos,contract.profile)
        if wheels:
            duration_ms+=wheels[-1]["at_ms"]
            steps.append({"kind":"wheel","start":previous,"end":pos,
                          "duration_ms":wheels[-1]["at_ms"],"steps":wheels})
        words,section_ids=visible_words(pos)
        hold=int(round(hold_seconds(words,contract.profile)*1000))
        duration_ms+=hold
        steps.append({"kind":"hold","scroll_y":pos,"duration_ms":hold,
                      "section_ids":section_ids[:24],"visible_words":words})
    wheel_ms=sum(step["duration_ms"] for step in steps if step["kind"]=="wheel")
    hold_ms=sum(step["duration_ms"] for step in steps if step["kind"]=="hold")
    return {"wheel_ms":round(wheel_ms,3),"hold_ms":round(hold_ms,3),
            "holds":len(positions),
            "url":page.url,"title":page.title,"source_height":page.height,
            "viewport_height":page.viewport_height,
            "steps":steps,"duration_ms":round(duration_ms,3),
            "capped":cap_reason}


def create_preflight(contract: TourContract, observed_pages: list[Page]) -> dict:
    routes=discover_routes(observed_pages,contract)
    by_url={}
    for p in observed_pages:
        url,_,error=canonical_url(contract.root_url,p.url)
        if not error:
            by_url[url]=p
    chapters=[]
    timeline=[]
    t=0.0
    for row in routes["pages"]:
        p=by_url[row["url"]]
        plan=plan_page(p,contract)
        if chapters:
            t+=350  # clean, safe hard-cut transition; no invented click
        chapters.append({"title":p.title,"url":row["url"],"start_ms":round(t,3)})
        timeline.append(plan)
        t+=plan["duration_ms"]
    estimate=round(t/1000,3)
    # Explicit input fingerprint: preflight must be revalidated before recording.
    observed=[{"url":p.url,"title":p.title,"height":p.height,
               "sections":[asdict(s) for s in p.sections],
               "links":[asdict(l) for l in p.links],
               "anchor_ids":p.anchor_ids} for p in observed_pages]
    digest=sha256(json.dumps(observed,sort_keys=True).encode()).hexdigest()
    skip_counts=dict(sorted(Counter(x["reason"] for x in routes["skipped"]).items()))
    page_breakdown=[{"url":p["url"],"total_ms":p["duration_ms"],
                     "wheel_ms":p["wheel_ms"],"hold_ms":p["hold_ms"],
                     "holds":p["holds"],"source_height":p["source_height"]}
                    for p in timeline]
    return {"schema":SCHEMA,"contract":contract.manifest(),"chapters":chapters,
            "skipped_by_reason":skip_counts,"page_breakdown":page_breakdown,
            "selected":routes["pages"],"anchors":routes["anchors"],
            "skipped":routes["skipped"],"source_fingerprint":digest,
            "timeline":timeline,"estimated_seconds":estimate,
            "estimate_range_seconds":[round(estimate*.85,1),round(estimate*1.35+2,1)],
            "limit_exceeded":estimate>contract.max_minutes*60,
            "status":"preflight_only"}
