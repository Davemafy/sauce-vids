"""Bounded repair decisions for Source-True Sauce URL films.

Never infer successful product functionality from a nav click, create new
application states, or repeat paid AI direction by default. This is a policy
plan for an adapter; browser recapture/render execution is a separate step.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from urllib.parse import urlsplit

from backend.url_film_quality import UrlFilmAssessment, _same_document_anchor

MAX_REPAIR_ATTEMPTS = 2


@dataclass(frozen=True)
class RepairStep:
    op: str
    source_ref: str | None = None
    evidence: str = ""


@dataclass(frozen=True)
class RepairDecision:
    schema: str
    status: str
    film_kind: str
    attempt: int
    max_attempts: int
    source_url: str
    steps: tuple[RepairStep, ...]
    draft_seconds: int
    requires_human_review: bool
    allow_paid_ai_retry: bool
    can_claim_verified_product_demo: bool
    reasons: tuple[str, ...]

    def as_receipt(self) -> dict:
        return asdict(self)


def _verified_anchor_destinations(report: dict, scenes: list[dict]) -> tuple[str, ...]:
    """Use only link fragments from controls actually clicked in the capture.

    Each destination is a locator to verify against live DOM later; this
    function must NOT pretend the destination's pixels have been captured.
    """
    url = report["url"]
    controls = {x.get("id"): x for x in report.get("controls", [])
                if isinstance(x, dict)}
    destinations: list[str] = []
    for scene in scenes:
        if not scene.get("transitionVerified") or scene.get("actualAction") != "click":
            continue
        control = controls.get(scene.get("actionId"))
        if control is None or control.get("kind") != "link":
            continue
        href = control.get("href", "")
        if _same_document_anchor(url, href):
            frag = urlsplit(href).fragment
            if frag and frag not in destinations:
                destinations.append(frag)
    return tuple(destinations)


def plan_repair(
    inspection: dict,
    scenes: list[dict],
    assessment: UrlFilmAssessment,
    *,
    attempt: int = 0,
    previous_failure_signatures: tuple[str, ...] = (),
) -> RepairDecision:
    """Choose a bounded next move after the source-evidence quality check.

    Repair steps are commands for an eventual authorized browser adapter, not
    claims that recapture/re-edit happened. No automatic paid inference.
    """
    if not isinstance(inspection, dict) or not isinstance(scenes, list):
        raise ValueError("Repair requires real inspection and recorded scene evidence")
    if not isinstance(assessment, UrlFilmAssessment):
        raise ValueError("Repair requires a typed source-evidence assessment")
    url = inspection.get("url", "")
    if not isinstance(url, str) or urlsplit(url).scheme not in ("https", "http"):
        raise ValueError("Repair cannot proceed without a validated source URL")
    if type(attempt) is not int or not 0 <= attempt <= MAX_REPAIR_ATTEMPTS:
        raise ValueError("Invalid bounded repair attempt")
    if not isinstance(previous_failure_signatures, tuple):
        raise ValueError("Previous failure signatures must be immutable")
    if assessment.eligible_product_demo and not assessment.reasons:
        return RepairDecision(
            "sauce-url-repair-v1", "needs_visual_review", "product-demo-candidate",
            attempt, MAX_REPAIR_ATTEMPTS, url, (), 3,
            True, False, True,
            ("Automated evidence checks are not creative approval",))
    if attempt >= MAX_REPAIR_ATTEMPTS:
        return RepairDecision(
            "sauce-url-repair-v1", "rejected", "unapproved",
            attempt, MAX_REPAIR_ATTEMPTS, url, (), 0,
            True, False, False, ("Repair budget exhausted; preserve original",))
    if assessment.navigation_only or assessment.actual_product_action_candidates == 0:
        kind = "public-website-showcase"
    else:
        kind = "product-demo-candidate"
    signature = "|".join((
        "navigation" if assessment.navigation_only else "nonavigation",
        "tiny" if assessment.bad_camera_targets else "notiny",
        "late" if assessment.opener_seconds > 4 else "ontime",
        "lowres" if not assessment.source_is_native_master else "native",
        "lowfps" if not assessment.source_is_native_fps else "nativefps",
    ))
    if signature in previous_failure_signatures:
        return RepairDecision(
            "sauce-url-repair-v1", "rejected", kind, attempt, MAX_REPAIR_ATTEMPTS,
            url, (), 0, True, False, False,
            ("No measured quality improvement after previous repair; do not loop",))
    steps: list[RepairStep] = []
    if kind == "public-website-showcase":
        steps.append(RepairStep(
            "reclassify_as_public_showcase", evidence=(
                "No verified in-app workflow; a landing-page film must not claim one"
            )))
    anchors = _verified_anchor_destinations(inspection, scenes)
    if assessment.bad_camera_targets:
        for fragment in anchors:
            steps.append(RepairStep(
                "resolve_destination_region_in_browser", fragment,
                "Re-find the actual target section after scrolling settles; "
                "verify section/headline geometry and genuine pixels before a camera move"
            ))
        if not anchors:
            steps.append(RepairStep(
                "capture_safe_source_regions",
                evidence="No destination anchor available; capture new genuine section geometry"
            ))
    if assessment.opener_seconds > 4:
        steps.append(RepairStep(
            "rewrite_opening_from_observed_source",
            evidence="Story must establish its subject/action within first three seconds; "
                     "do not invent a product result or time-warp real clicks"))
    if not assessment.source_is_native_master:
        steps.append(RepairStep(
            "capture_native_dpr2",
            evidence="Collect genuine native browser pixels at a source resolution "
                     "sufficient for a 1920×1080 master"))
    if not assessment.source_is_native_fps:
        steps.append(RepairStep(
            "record_true_source_fps",
            evidence="Do not claim 60 distinct source frames from 25fps Chromium video"))
    steps.append(RepairStep(
        "render_three_second_storyboard_only",
        evidence="Verify clip bounds, focus, cursor, meaning, and 390px readability; "
                 "full-duration render remains blocked pending visual review"))
    return RepairDecision(
        "sauce-url-repair-v1", "draft_required", kind, attempt+1,
        MAX_REPAIR_ATTEMPTS, url, tuple(steps), 3,
        True, False, False, tuple(assessment.reasons)
    )

def verify_visible_destination(page, fragment: str) -> dict:
    """Resolve a recorded same-page anchor to a REAL post-scroll section.

    Caller must supply a public/safely routed Playwright page; this helper
    never navigates, clicks a new link or changes application state.
    Raises if the section cannot be read without inventing pixels.
    """
    if (not isinstance(fragment, str) or not fragment
        or len(fragment) > 80 or not all(
            c.isalnum() or c in ("-", "_") for c in fragment
        )):
        raise ValueError("Unverified or unsafe anchor identifier")
    data = page.evaluate("""id => {
      const root=document.getElementById(id);
      if(!root)return null;
      const box=root.getBoundingClientRect();
      const visible=(r)=>r.width>0 && r.height>0 &&
        Math.min(innerWidth,r.right)>Math.max(0,r.left) &&
        Math.min(innerHeight,r.bottom)>Math.max(0,r.top);
      const heads=[...root.querySelectorAll('h1,h2,h3,h4')].map(h => {
        const r=h.getBoundingClientRect();
        return {text:(h.innerText||'').trim().slice(0,110),
          rect:{x:r.x,y:r.y,width:r.width,height:r.height},
          visible:visible(r)};
      }).filter(h=>h.visible && h.text.length>=8);
      return {anchor:id,viewport:{width:innerWidth,height:innerHeight},
        section:{x:box.x,y:box.y,width:box.width,height:box.height},
        headings:heads};
    }""", fragment)
    if not isinstance(data, dict):
        raise ValueError("No real DOM destination for observed anchor")
    section=data.get("section", {})
    viewport=data.get("viewport", {})
    if (not isinstance(section, dict) or not isinstance(viewport, dict)
        or section.get("width",0)<300 or section.get("height",0)<120
        or viewport.get("width",0)<600):
        raise ValueError("Real destination is too small for coherent composition")
    x=float(section["x"]); y=float(section["y"])
    width=float(section["width"]); height=float(section["height"])
    vw=float(viewport["width"]); vh=float(viewport["height"])
    # A tiny or offscreen sliver cannot be used as an approved camera focus.
    visible_w=max(0,min(x+width,vw)-max(x,0))
    visible_h=max(0,min(y+height,vh)-max(y,0))
    if visible_w<min(300,vw*.35) or visible_h<min(120,vh*.16):
        raise ValueError("Destination has not settled into visible source frame")
    if not data.get("headings"):
        raise ValueError("No legible source-authored headline in destination")
    return data
