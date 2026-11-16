"""Source-grounded, privacy-bounded brand tokens for captured websites.

Read only presentation CSS and public theme meta tags, never text content,
forms, credentials, image URLs, cookies or arbitrary page variables.
Persist a small normalized snapshot with the exact captured session.
"""
from __future__ import annotations

import re
from typing import Any

SCHEMA = "sauce.brand.v1"
HEX = re.compile(r"^#[0-9a-f]{6}$")
FONT = re.compile(r"^[A-Za-z0-9 ,.'\"_-]{1,96}$")
DEFAULT_COLORS = {"primary": "#6878a5", "accent": "#95759e",
                  "background": "#090a0f"}

# The DOM is observed at capture start, after stylesheet/font hydration,
# and never queried again during frame-stepped rendering. The temporary
# color resolver element does not load resources or read user data.
EXTRACT_BRAND_JS = r"""() => {
  const root=document.documentElement;
  const body=document.body || root;
  const rs=getComputedStyle(root),bs=getComputedStyle(body);
  const scratch=document.createElement("span");
  scratch.setAttribute("aria-hidden","true");
  scratch.style.cssText="position:fixed;pointer-events:none;opacity:0;";
  root.appendChild(scratch);
  const resolve=(raw)=>{
    if(typeof raw!=="string"||raw.length>90)return null;
    let text=raw.trim();
    if(!text||/url\(|var\(|attr\(|expression\(|[<>;{}]/i.test(text))
      return null;
    // shadcn/Tailwind commonly stores a triplet: "221 83% 53%".
    if(/^\d{1,3}(?:\.\d+)?\s+\d{1,3}(?:\.\d+)?%\s+\d{1,3}(?:\.\d+)?%(?:\s*\/\s*[\d.]+%?)?$/.test(text))
      text="hsl("+text+")";
    try{
      scratch.style.color="";
      scratch.style.setProperty("color",text,"important");
      if(!scratch.style.color)return null;
      const v=getComputedStyle(scratch).color;
      const m=v.match(/^rgba?\(\s*(\d+(?:\.\d+)?)\s*[, ]\s*(\d+(?:\.\d+)?)\s*[, ]\s*(\d+(?:\.\d+)?)/i);
      let nums;
      if(m)nums=m.slice(1,4).map(Number);
      else{
        // Chromium may preserve modern oklch(), oklab() and display-p3
        // in computed style. Canvas converts these into captured sRGB.
        const canvas=document.createElement("canvas");
        canvas.width=canvas.height=1;
        const ctx=canvas.getContext("2d",{willReadFrequently:true});
        if(!ctx)return null;
        ctx.fillStyle="#000";
        ctx.fillStyle=v;
        ctx.fillRect(0,0,1,1);
        nums=[...ctx.getImageData(0,0,1,1).data].slice(0,3);
      }
      if(nums.some(n=>!Number.isFinite(n)||n<0||n>255))return null;
      return "#"+nums.map(n=>Math.round(n).toString(16).padStart(2,"0")).join("");
    }catch{return null;}
  };
  const chromatic=(hex)=>{
    if(!hex)return false;
    const c=[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16));
    return Math.max(...c)-Math.min(...c)>=19&&Math.max(...c)>=24;
  };
  const css=(names,allowNeutral=false)=>{
    for(const name of names){
      for(const sty of [rs,bs]){
        const raw=sty.getPropertyValue(name);
        const color=resolve(raw);
        if(color&&(allowNeutral||chromatic(color)))
          return {value:color,source:"css:"+name};
      }
    }
    return null;
  };
  const meta=(selectors)=>{
    for(const selector of selectors){
      const m=document.querySelector(selector);
      const color=resolve(m?.getAttribute("content")||"");
      if(color)return {value:color,source:"meta:theme-color"};
    }
    return null;
  };
  const visible=(el)=>{
    if(!el)return false;
    const s=getComputedStyle(el),r=el.getBoundingClientRect();
    return s.display!=="none"&&s.visibility!=="hidden"&&
      r.width>=36&&r.height>=16;
  };
  const computed=(selectors,property)=>{
    for(const selector of selectors){
      const nodes=[...document.querySelectorAll(selector)].slice(0,10);
      for(const el of nodes){
        if(!visible(el)||el.closest(
           ".woot-widget-bubble,.crisp-client,#intercom-container,"+
           "#hubspot-messages-iframe-container"))continue;
        const color=resolve(getComputedStyle(el)[property]);
        if(chromatic(color))return {value:color,source:"computed:"+property};
      }
    }
    return null;
  };
  // Named brand tokens take precedence over UI element colors. A neutral
  // button cannot override a source-declared --primary.
  const primary=css(["--brand-primary","--color-primary","--primary",
                     "--theme-primary","--brand-color","--color-brand"])||
       meta(['meta[name="theme-color"]','meta[name="msapplication-TileColor"]'])||
       computed(['button[type="submit"]','[data-variant="primary"]',
                 '.btn-primary','.button-primary','a[role="button"]',
                 'button'],'backgroundColor');
  const accent=css(["--brand-accent","--color-accent","--accent",
                    "--theme-accent","--secondary","--color-secondary"])||
       computed(['[data-variant="accent"]','.btn-accent',
                 '[class*="accent"]'],'stroke')||
       computed(['[data-variant="accent"]','.btn-accent',
                 '[class*="accent"]'],'color')||
       computed(['[data-variant="accent"]','.btn-accent','.accent',
                 'a[role="button"]'],'backgroundColor');
  const background=css(["--color-background","--background",
                        "--surface","--page-background"],true)||
       {value:resolve(bs.backgroundColor)||resolve(rs.backgroundColor),
        source:"computed:backgroundColor"};
  const h=document.querySelector('h1,h2,[role="heading"]');
  const hs=h?getComputedStyle(h):bs;
  const safeFont=(v)=>typeof v==="string"&&v.length<97&&
      /^[A-Za-z0-9 ,.'"_-]+$/.test(v)?v:null;
  const size=(v)=>{
    const n=parseFloat(v);return Number.isFinite(n)&&n>=8&&n<=120
      ?Math.round(n*100)/100:null;
  };
  const font=(v)=>({
    family:safeFont(v.fontFamily),
    weight:/^(normal|bold|[1-9]00)$/.test(v.fontWeight)
      ?v.fontWeight:"normal",
    sizePx:size(v.fontSize)
  });
  scratch.remove();
  return {schema:"sauce.brand.v1",
    colors:{primary:primary?.value??null,accent:accent?.value??null,
            background:background.value??null},
    provenance:{primary:primary?.source??null,accent:accent?.source??null,
                background:background.source??null},
    typography:{body:font(bs),heading:font(hs)}};
}"""


def _hex(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.lower()
    return value if HEX.fullmatch(value) else None


def _neutral(value: str | None) -> bool:
    if value is None:
        return True
    ch = [int(value[i:i + 2], 16) for i in (1, 3, 5)]
    return max(ch) - min(ch) < 19 or max(ch) < 24


def _font(obj: Any) -> dict:
    data = obj if isinstance(obj, dict) else {}
    family = data.get("family")
    family = family if isinstance(family, str) and FONT.fullmatch(family) else None
    weight = data.get("weight")
    if weight not in {"normal", "bold", "100", "200", "300", "400",
                      "500", "600", "700", "800", "900"}:
        weight = "normal"
    size = data.get("sizePx")
    size = round(float(size), 2) if type(size) in (float, int) and 8 <= size <= 120 else None
    return {"family": family, "weight": weight, "sizePx": size}


def normalize_brand_tokens(raw: Any) -> dict:
    """Accept only literal colors/known provenance and bounded typography.

    This prevents a remote page from writing arbitrary CSS/HTML into the
    renderer or from leaking secret-looking CSS variables into a trace.
    """
    payload = raw if isinstance(raw, dict) else {}
    colors = payload.get("colors") if isinstance(payload.get("colors"), dict) else {}
    provenance = (payload.get("provenance") if isinstance(payload.get("provenance"), dict)
                  else {})
    primary, accent, background = (_hex(colors.get(k)) for k in
                                   ("primary", "accent", "background"))
    # A white/black button is not reliable evidence of the product's brand.
    # Do not infer a palette from a domain name or synthesize unrelated hues.
    if _neutral(primary):
        primary = None
    if _neutral(accent):
        accent = None
    source_names = {"primary", "accent", "background"}
    sanitized_sources = {}
    for key in source_names:
        v = provenance.get(key)
        allowed = (isinstance(v, str) and
                   (v.startswith("css:--") or v in {
                       "meta:theme-color", "computed:backgroundColor",
                       "computed:stroke", "computed:color",
                       "derived:primary", "derived:accent",
                       "fallback:neutral"}))
        if allowed and len(v) <= 50 and re.fullmatch(r"[\w:-]+", v):
            sanitized_sources[key] = v
        else:
            sanitized_sources[key] = None
    # If a page exposes only one genuine brand color, use it for both subtle
    # lights rather than inventing a competing hue. Provenance remains clear.
    if primary is None and accent is not None:
        primary = accent
        sanitized_sources["primary"] = "derived:accent"
    if accent is None and primary is not None:
        accent = primary
        sanitized_sources["accent"] = "derived:primary"
    # Re-validating a stored neutral snapshot must not reinterpret its
    # intentionally conservative fallback colors as observed brand evidence.
    inherited_fallback=(sanitized_sources["primary"]=="fallback:neutral"
                        and sanitized_sources["accent"]=="fallback:neutral")
    has_brand = primary is not None and accent is not None and not inherited_fallback
    if not has_brand:
        primary, accent = DEFAULT_COLORS["primary"], DEFAULT_COLORS["accent"]
        sanitized_sources["primary"] = "fallback:neutral"
        sanitized_sources["accent"] = "fallback:neutral"
    typ = payload.get("typography") if isinstance(payload.get("typography"), dict) else {}
    return {"schema": SCHEMA,
            "colors": {"primary": primary, "accent": accent,
                       "background": background or DEFAULT_COLORS["background"]},
            "provenance": sanitized_sources,
            "typography": {"body": _font(typ.get("body")),
                           "heading": _font(typ.get("heading"))},
            "confidence": "observed" if has_brand else "fallback"}


def validate_brand_tokens(data: Any) -> dict:
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ValueError("Invalid brand token schema")
    for key in ("colors", "typography", "provenance"):
        if not isinstance(data.get(key), dict):
            raise ValueError("Malformed captured brand tokens")
    sanitized = normalize_brand_tokens(data)
    if sanitized != data:
        raise ValueError("Captured brand tokens are not canonical")
    return sanitized


def extract_brand_tokens(page) -> dict:
    return normalize_brand_tokens(page.evaluate(EXTRACT_BRAND_JS))


def stage_brand_colors(tokens: dict | None) -> tuple[str | None, str | None]:
    """Legacy and neutral-fallback sessions preserve the exact old stage."""
    if tokens is None:
        return None, None
    safe = validate_brand_tokens(tokens)
    if safe["confidence"] == "fallback":
        return None, None
    return safe["colors"]["primary"], safe["colors"]["accent"]
