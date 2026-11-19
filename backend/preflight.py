"""Bounded public-page preflight for source-first story discovery."""
from __future__ import annotations

import re

_BLOCKED_HTTP = {403, 429, 503}
_CHALLENGE_TEXT = re.compile(
    r"just a moment|verify (?:that )?you are human|access denied|"
    r"enable javascript and cookies|checking your browser|attention required|"
    r"performing security verification",
    re.IGNORECASE,
)

_PAGE_SIGNAL_JS = r"""() => {
 const visible = node => {
   const rect = node.getBoundingClientRect();
   return rect.width >= 24 && rect.height >= 14 &&
     node.checkVisibility({opacityProperty: true, visibilityProperty: true});
 };
 const chrome = 'nav,footer,header,[role="navigation"],[role="banner"],[role="contentinfo"]';
 const blocks = [...document.querySelectorAll(
   'h1,h2,h3,p,li,button,input,[role="grid"],table,pre,video,img,iframe,canvas'
 )].slice(0, 180).filter(node => {
   if (!visible(node) || node.closest(chrome)) return false;
   if (node.matches('img,video,iframe,canvas')) {
     const {width,height} = node.getBoundingClientRect();
     return width * height >= 40000;
   }
   return node.matches('input,table,[role="grid"]') ||
     (node.innerText || node.getAttribute('aria-label') || '').trim().length >= 4;
 });
 const marked = [...document.querySelectorAll(
   '#challenge-stage,#challenge-form,#cf-challenge-running,iframe[src*="challenges.cloudflare.com"]'
 )].some(visible);
 return {
   title: document.title.slice(0, 160),
   topText: (document.body?.innerText || '').trim().slice(0, 700),
   meaningfulBlocks: blocks.length,
   marked,
 };
}"""


def check_page(page, response, url: str) -> dict:
    """Check a normally navigated page once, without retrying or solving a block."""
    def blocked(signal):
        return {
            "status": "blocked",
            "reason": "waf_challenge",
            "signal": signal,
            "url": url,
        }

    status = response.status if response is not None else None
    if status in _BLOCKED_HTTP:
        return blocked(f"http_{status}")
    if status is not None and status >= 400:
        return {"status": "unavailable", "reason": f"http_{status}", "url": url}

    initial = page.evaluate(_PAGE_SIGNAL_JS)
    if _CHALLENGE_TEXT.search(initial["title"]):
        return blocked("challenge_title")

    try:
        page.wait_for_load_state("networkidle", timeout=3000)
    except Exception as error:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

        if not isinstance(error, PlaywrightTimeoutError):
            raise
        # Analytics and live previews may keep requests in flight indefinitely.
    page.wait_for_timeout(1500)
    observed = page.evaluate(_PAGE_SIGNAL_JS)
    if (_CHALLENGE_TEXT.search(observed["title"]) or observed["marked"] or
            _CHALLENGE_TEXT.search(observed["topText"]) and observed["meaningfulBlocks"] < 12):
        return blocked("challenge_markup_or_text")
    if observed["meaningfulBlocks"] < 3:
        return blocked("fewer_than_three_visible_content_blocks")
    return {"status": "ready", "url": url}
