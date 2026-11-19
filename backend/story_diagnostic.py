"""Inspect a public URL and save its editorial plan and static review sheet."""
from __future__ import annotations

import argparse
import json
import math
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image, ImageChops, ImageStat

from scripts.capture_safety import guard_route, validate_public_url

from .beat_selector import story_hook, select_story
from .contact_sheet import render_contact_sheet
from .preflight import check_page
from .product_explorer import CHROME
from .shot_scorer import discover_candidates, score_candidates

# Prefer explicitly semantic controls. A plain booking button can submit a
# reservation, so only a standalone time choice or an exposed state control
# is eligible. All network traffic is blocked while this probe runs.
SAFE_TARGET = r"""(el) => {
  if (!el.matches('button,[role=tab],[role=switch],[role=radio]') ||
      el.closest('a,form,nav,header,footer,[data-private],[data-secret],[data-sensitive]') ||
      el.form || el.disabled || el.getAttribute('type') === 'submit' ||
      el.getAttribute('aria-disabled') === 'true') return null;
  const label = (el.innerText || el.getAttribute('aria-label') || '').trim();
  if (/book|reserv|submit|publish|subscribe|buy|pay|delete|sign|log in|confirm|rickroll|authorize|send/i.test(label))
    return null;
  if (!el.matches('[aria-selected=false],[aria-pressed],[aria-checked],[aria-expanded=false]') &&
      !/^\d{1,2}:\d{2}\s*(?:[ap]m)?$/i.test(label)) return null;
  return label;
}"""
SNAPSHOT = r"""(el) => {
  const region = document.getElementById(el.getAttribute('aria-controls') || '');
  return { attributes: Object.fromEntries(['aria-selected','aria-pressed','aria-checked','aria-expanded','data-state']
                     .map(name => [name, el.getAttribute(name)])),
           target: (el.innerText || '').trim().slice(0,120),
           panel: region && region.checkVisibility({checkOpacity:true,checkVisibilityCSS:true}) ?
                    (region.innerText || '').trim().slice(0,1000) : '' };
}"""
SOURCE_TEXT = "(el) => (el.innerText || '').replace(/\\s+/g, ' ').trim().slice(0,2500)"


def _change(before: dict, after: dict, original: str, changed: str) -> str | None:
    for key, value in before["attributes"].items():
        updated = after["attributes"][key]
        if value != updated and updated in ("true", "false", "active", "inactive",
                                            "open", "closed", "checked", "unchecked", "selected"):
            return f"{key} changed {value or 'unset'} → {updated}"
    if after["panel"] and before["panel"] != after["panel"]:
        return "Controlled panel displayed different visible content"
    if after["target"] and before["target"] != after["target"]:
        return "Control label changed after click"
    if changed and original != changed:
        return "Visible content inside the product region changed after click"
    return None


def _crop_box(rect):
    left, top = math.floor(rect["x"]), math.floor(rect["y"])
    return (left, top, math.ceil(rect["x"] + rect["width"]),
            math.ceil(rect["y"] + rect["height"]))


def _captures_region(page, rect):
    left, top, right, bottom = _crop_box(rect)
    return Image.open(BytesIO(page.screenshot(full_page=True, scale="css", timeout=7000, clip={
        "x": left, "y": top, "width": right - left, "height": bottom - top,
    }))).convert("RGB")


def _probe(context, url, hook):
    from playwright.sync_api import Error as PlaywrightError

    targets = hook.get("targets", [])
    if not targets:
        return None, None
    # The original document stays untouched for the before screenshot. Each
    # failed action ends its own page and the next candidate gets fresh state.
    for target in targets[:3]:
        page = context.new_page()
        try:
            response = page.goto(url, wait_until="domcontentloaded", timeout=10000)
            if response is None or response.status >= 400:
                continue
            page.wait_for_timeout(700)
            anchor = page.locator(hook["selector"])
            control = page.locator(target["selector"])
            if anchor.count() != 1 or control.count() != 1 or not control.is_visible():
                continue
            if not control.evaluate(SAFE_TARGET):
                continue
            if not control.evaluate("(el, anchor) => document.querySelector(anchor)?.contains(el)", hook["selector"]):
                continue
            control.scroll_into_view_if_needed(timeout=1500)
            target_rect = control.evaluate("""el => {
              const r = el.getBoundingClientRect();
              return {x:r.x+scrollX,y:r.y+scrollY,width:r.width,height:r.height};
            }""")
            expected = target["rect"]
            if any(abs(target_rect[k] - expected[k]) > 12 for k in expected):
                continue
            before = control.evaluate(SNAPSHOT)
            original = anchor.evaluate(SOURCE_TEXT)
            # Scoped to this disposable page. Stops requests, popups and
            # top-level navigation initiated by the interaction.
            page.route("**/*", lambda route: route.abort())
            page.route_web_socket("**/*", lambda socket: socket.close())
            page.on("popup", lambda popup: popup.close())
            initial = page.url
            image_before = _captures_region(page, hook["rect"])
            page.wait_for_timeout(220)
            if before != control.evaluate(SNAPSHOT) or original != anchor.evaluate(SOURCE_TEXT):
                continue
            control.click(timeout=1800)
            page.wait_for_timeout(350)
            if page.url != initial:
                continue
            mutation = _change(before, control.evaluate(SNAPSHOT), original, anchor.evaluate(SOURCE_TEXT))
            if mutation:
                after = _captures_region(page, hook["rect"])
                if ImageStat.Stat(ImageChops.difference(image_before, after)).mean == [0, 0, 0]:
                    continue
                return {"type": "click", "target_rect": expected,
                        "verified_mutation": mutation}, after
        except PlaywrightError:
            continue
        finally:
            page.close()
    return None, None


def _decline_optional_cookies(page):
    # Use the site's accessible decline control on consent chrome only.
    # The browser context is disposable and the site's pixels remain intact.
    from playwright.sync_api import Error as PlaywrightError

    controls = page.locator(
        'button[data-tid="banner-decline"], [role="dialog"] button,'
        '[id*="cookie" i] button, [class*="cookie-banner" i] button'
    )
    for control in controls.all()[:20]:
        try:
            if (control.is_visible() and not control.evaluate("el => !!el.form") and
                    control.inner_text().strip().casefold() in
                    {"decline", "reject all", "decline all", "reject optional", "essential only"}):
                if not control.evaluate("""el => {
                    for (let n = el.parentElement, i = 0; n && i < 5; n = n.parentElement, i++) {
                        if (n.innerText.length < 1200 && /cookie/i.test(n.innerText)) return true;
                    }
                    return false;
                }"""):
                    continue
                control.click(timeout=1200)
                return
        except PlaywrightError:
            continue


def _warm_media(page):
    # Trigger source lazy loading without replacing page styles or content.
    for y in range(0, min(page.evaluate("document.documentElement.scrollHeight"), 21600), 650):
        page.evaluate("(y) => window.scrollTo({top: y, behavior: 'instant'})", y)
        page.wait_for_timeout(70)
    page.evaluate("window.scrollTo({top: 0, behavior: 'instant'})")
    page.wait_for_timeout(500)


def diagnose(url: str, output: Path, browser_executable: str = CHROME) -> dict:
    from playwright.sync_api import Error as PlaywrightError, sync_playwright

    validate_public_url(url)
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    domain = urlsplit(url).hostname.removeprefix("www.")
    source = action_crop = rejected = None
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=browser_executable,
                                    args=["--no-sandbox", "--disable-dev-shm-usage"])
        try:
            context = browser.new_context(viewport={"width": 1280, "height": 720},
                                          service_workers="block", accept_downloads=False)
            context.route("**/*", guard_route)
            context.route_web_socket("**/*", lambda socket: socket.close())
            page = context.new_page()
            try:
                response = page.goto(url, wait_until="domcontentloaded", timeout=16000)
                plan = check_page(page, response, url)
            except PlaywrightError as error:
                plan = {"url": url, "status": "source_unavailable", "reason": type(error).__name__}
            if plan["status"] == "ready":
                _decline_optional_cookies(page)
                _warm_media(page)
                measured = discover_candidates(page)
                candidates = score_candidates(measured)
                hook = story_hook(candidates)
                interaction = None
                if hook:
                    interaction, action_crop = _probe(context, page.url, hook)
                plan = select_story(url, candidates, interaction)
                if hook is None:
                    rejected = next((c for c in score_candidates(measured, include_unreadable=True)
                                     if c["readability"] == "below_floor" and c["kind"] == "widget"
                                     and (c["calendar"] or c["times"] >= 3) and not c["distractions"]), None)
                source = Image.open(BytesIO(page.screenshot(full_page=True, scale="css", timeout=12000))).convert("RGB")
                (output / f"candidates_{domain}.json").write_text(json.dumps(candidates[:25], indent=2) + "\n")
        finally:
            browser.close()
    sheet_plan = plan
    if rejected:
        sheet_plan = {**plan, "beats": [{
            "beat_index": 1, "role": "rejected_preview", "score": rejected["score"],
            "source_rect": rejected["rect"], "reason": rejected["reason"],
        }]}
    render_contact_sheet(sheet_plan, output / f"contact_sheet_{domain}.png", source, action_crop)
    (output / f"beat_plan_{domain}.json").write_text(json.dumps(plan, indent=2) + "\n")
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", nargs="+")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--browser-executable", default=CHROME)
    args = parser.parse_args()
    for url in args.url:
        print(json.dumps(diagnose(url, args.out, args.browser_executable), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
