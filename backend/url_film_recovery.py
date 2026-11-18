"""Bounded repair decisions for Source-True Sauce URL films.

Never infer successful product functionality from a nav click, create new
application states, or repeat paid AI direction by default. This is a policy
plan for an adapter; browser recapture/render execution is a separate step.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import struct
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
            True, False, False,
            ("A changed control is not proof of the promised product outcome; "
             "human evidence and film review are still required",))
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


def _same_destination_geometry(before: dict, after: dict) -> bool:
    """Require both the section and its actual heading positions to settle."""
    if before.get("viewport") != after.get("viewport"):
        return False
    try:
        if any(abs(float(before["section"][key]) -
                   float(after["section"][key])) > 2
               for key in ("x", "y", "width", "height")):
            return False
        old_heads, new_heads = before["headings"], after["headings"]
        if len(old_heads) != len(new_heads):
            return False
        for old, new in zip(old_heads, new_heads):
            if old["text"] != new["text"]:
                return False
            if any(abs(float(old["rect"][key]) -
                       float(new["rect"][key])) > 2
                   for key in ("x", "y", "width", "height")):
                return False
    except (KeyError, TypeError, ValueError):
        return False
    return True


def capture_verified_destination(page, fragment: str) -> tuple[dict, bytes]:
    """Capture actual source pixels and verify the DOM didn't shift mid-shot.

    This must only be called with the existing safe public Playwright context.
    A source SHA alone is not proof of pixels; caller gets the exact PNG bytes
    to keep private alongside the returned receipt. No video is rendered.
    """
    # Browser smooth scroll/entrance animations may still be moving at the
    # nominal click timestamp. Wait for two consecutive stable samples;
    # a capture during movement cannot authorize the next camera move.
    waiter = getattr(page, "wait_for_timeout", None)
    before = None if callable(waiter) else verify_visible_destination(page, fragment)
    settled = not callable(waiter)
    checks = 0
    if callable(waiter):
        for _ in range(12):  # Bounded 1.8s maximum, no infinite waits.
            waiter(150)
            try:
                after_wait = verify_visible_destination(page, fragment)
            except ValueError:
                before = None
                checks = 0
                continue
            if before is not None and _same_destination_geometry(before, after_wait):
                checks += 1
            else:
                checks = 0
            before = after_wait
            if checks >= 2:
                settled = True
                break
    if not settled:
        raise ValueError("Source section never settled before capture")
    raw = page.screenshot(type="png", animations="disabled", caret="hide")
    after = verify_visible_destination(page, fragment)
    if not isinstance(raw, bytes) or not raw.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Missing authentic Chromium PNG source bytes")
    if len(raw) < 33 or len(raw) > 16 * 1024 * 1024:
        raise ValueError("Source PNG size outside bounded capture")
    image_w, image_h = struct.unpack(">II", raw[16:24])
    viewport = after["viewport"]
    css_w, css_h = float(viewport["width"]), float(viewport["height"])
    if (not 1 <= image_w / css_w <= 3
            or not 1 <= image_h / css_h <= 3
            or abs(image_w / css_w - image_h / css_h) > .02):
        raise ValueError("Captured source PNG does not match DOM viewport")
    if not _same_destination_geometry(before, after):
        raise ValueError("Source section or headline moved during capture")
    receipt = {
        "schema": "sauce-verified-anchor-capture-v1",
        "anchor": fragment,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "source_dimensions": [image_w, image_h],
        "viewport": after["viewport"],
        "section": after["section"],
        "headings": after["headings"],
        "approved_for_premium_film": False,
    }
    return receipt, raw
