"""Browser-recorded cursor sprites sourced from Sauce's own or CC0 SVG assets.

The source website sees one pointer-events:none overlay driven only by actual
Chromium pointer events. Its CSS cursor class comes from getComputedStyle, not
from guessed DOM targets or fabricated interaction paths.
"""
from __future__ import annotations

from base64 import b64encode
from pathlib import Path
import json

# Legacy settings stay available to reproduce completed captures, but are
# not presented as founder-grade cursor styles.
CURSOR_STYLES = (
    "founder-reference", "studio-rounded", "gloss-carbon",
    "aero-prism", "mint-studio"
)


def build_cursor_script(style: str) -> str:
    """Return an isolated, DOM-aware SVG pointer script with exact hotspots."""
    if style not in CURSOR_STYLES:
        raise ValueError("Unknown registered cursor style")
    root = Path(__file__).resolve().parents[1] / "assets" / "cursors"
    roles = ("arrow", "hand", "text")
    files = {}
    for role in roles:
        if style in ("studio-rounded", "gloss-carbon", "aero-prism") and role == "arrow":
            path = root / "sauce-styles" / (style + ".svg")
        elif style == "mint-studio":
            path = root / "mint-studio" / (role + ".svg")
        else:
            path = root / "founder-reference" / (role + ".svg")
        data = path.read_bytes()
        if len(data) > 8192 or not data.startswith(b"<svg"):
            raise ValueError("Cursor SVG asset is unexpectedly large or malformed")
        files[role] = "data:image/svg+xml;base64," + b64encode(data).decode("ascii")
    # arrow (48x56 with tip 4,4); hand (32x32, tip 10,2);
    # text (32x32, tip 16,16).
    sizes = {
        "arrow": ({"w": 24, "h": 24, "hotX": 0, "hotY": 0}
                  if style == "mint-studio" else
                  {"w": 24, "h": 28, "hotX": 2, "hotY": 2}),
        "hand": {"w": 31, "h": 31, "hotX": 31 * 10 / 32, "hotY": 31 * 2 / 32},
        "text": {"w": 30, "h": 30, "hotX": 15, "hotY": 15},
    }
    # These are unchanged original source SVG assets; the browser simply
    # changes the visible glyph when its native computed cursor changes.
    js = r"""(() => {
  if (window.__saucePointerInstalled) return;
  window.__saucePointerInstalled = true;
  const images = __IMAGES__, geometry = __GEOMETRY__;
  const marker = document.createElement('div');
  marker.id = 'sauce-motion-pointer';
  marker.setAttribute('aria-hidden','true');
  marker.style.cssText = 'position:fixed;left:0;top:0;pointer-events:none;'
    + 'z-index:2147483646;transform:translate3d(-999px,-999px,0);'
    + 'background-size:100% 100%;background-repeat:no-repeat;will-change:transform;';
  const install = () => {
    if (!marker.isConnected) (document.body||document.documentElement).appendChild(marker);
  };
  install();
  if (document.readyState === 'loading')
    document.addEventListener('DOMContentLoaded', install, {once:true});
  let point = {x:-35,y:-35}, currentRole = null;
  const cssRole = event => {
    const el = event && event.target;
    if (!(el instanceof Element)) return 'arrow';
    const css = getComputedStyle(el).cursor;
    if (css === 'pointer') return 'hand';
    if (css === 'text' || css === 'vertical-text') return 'text';
    return 'arrow';
  };
  const reposition = event => {
    if (typeof event.clientX !== 'number' || typeof event.clientY !== 'number') return;
    point = {x:event.clientX,y:event.clientY};
    const role=cssRole(event), dims=geometry[role];
    if (role !== currentRole) {
      currentRole=role;
      marker.style.width=dims.w+'px';
      marker.style.height=dims.h+'px';
      marker.style.backgroundImage='url("'+images[role]+'")';
    }
    marker.style.transform='translate3d('+(point.x-dims.hotX)+'px,'
      +(point.y-dims.hotY)+'px,0)';
  };
  for (const eventName of ['pointermove','pointerover','pointerdown','pointerup'])
    window.addEventListener(eventName,reposition,true);
  window.__sauceGetPointer=()=>point;
})();"""
    return (js.replace("__IMAGES__", json.dumps(files, separators=(",", ":")))
              .replace("__GEOMETRY__", json.dumps(sizes, separators=(",", ":"))))
