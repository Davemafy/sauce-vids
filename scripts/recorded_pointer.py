"""Project one source-timed cursor onto cursorless recorded footage."""
from functools import lru_cache

import cv2
import numpy as np


def pointer_track(manifest, width, height):
    if manifest.get("cursorless") is not True:
        return None
    try:
        track = np.asarray([(p["t"], p["x"], p["y"])
                            for p in manifest["pointer_samples"]], dtype=np.float64)
    except (KeyError, TypeError, ValueError):
        return None
    if (track.ndim != 2 or len(track) < 2 or not np.isfinite(track).all()
            or np.any(np.diff(track[:, 0]) <= 0)
            or np.any(track[:, 1:] < 0) or np.any(track[:, 1] >= width)
            or np.any(track[:, 2] >= height)):
        return None
    return track


# Colorosse Mint Cursors: original CC0 vector pack, not a UI icon or a
# hand-drawn compositor polygon. The source SVGs remain verbatim under assets.
# Explicit legacy mode retains reproducibility of prior rejected comparisons.
CURSOR_PACKS = ("founder-reference", "mint-studio", "studio-rounded", "gloss-carbon", "aero-prism", "tabler-legacy")
SAUCE_ORIGINAL_STYLE_PACKS = ("studio-rounded", "gloss-carbon", "aero-prism")


@lru_cache(maxsize=64)
def _mint_svg_sprite(role: str, pixel_size: int):
    """Rasterize a genuine CC0 cursor SVG at 4x, preserving its native hotspot.

    Render-time white rim improves contrast on dark product UIs; the source
    path, viewBox, original asset bytes and original tip metadata are unchanged.
    """
    if role not in ("arrow", "hand", "text"):
        raise ValueError("Unsupported cursor role")
    if not 2 <= pixel_size <= 256:
        raise ValueError("Unsupported cursor display size")
    from io import BytesIO
    from pathlib import Path
    import cairosvg
    from PIL import Image
    import xml.etree.ElementTree as ET

    filename = (Path(__file__).resolve().parents[1]
                / "assets" / "cursors" / "mint-studio" / f"{role}.svg")
    original = filename.read_text(encoding="utf-8")
    root = ET.fromstring(original)
    if root.tag != "{http://www.w3.org/2000/svg}svg":
        raise ValueError("Mint theme must be an SVG")
    title = root.find("{http://www.w3.org/2000/svg}title")
    hotspots={"arrow": (0.,0.), "hand": (10.,2.), "text": (16.,16.)}
    original_hotspot=hotspots[role]
    expected=f"hotspot {int(original_hotspot[0])},{int(original_hotspot[1])}"
    if title is None or expected not in (title.text or ""):
        raise ValueError("CC0 cursor hotspot metadata does not match")
    if original.count('stroke="#66757f"') < 1:
        raise ValueError("Mint pack outline palette changed unexpectedly")
    rendered = original.replace('stroke="#66757f"', 'stroke="#f5f7fb"')
    png = cairosvg.svg2png(bytestring=rendered.encode("utf-8"),
                           output_width=pixel_size*4,
                           output_height=pixel_size*4)
    pic = Image.open(BytesIO(png)).convert("RGBA")
    pic = pic.resize((pixel_size,pixel_size),Image.Resampling.LANCZOS)
    art = np.asarray(pic,dtype=np.uint8).copy()
    # The native asset's hotspot is in the 32-unit SVG canvas, not the
    # resized image. Preserve it when scaling to any 1080p/4K output.
    return art, tuple(v*pixel_size/32. for v in original_hotspot)


def pointer_role_at(manifest: dict, time: float) -> str:
    """Only an observed CSS cursor may change the arrow to a hand or I-beam.

    The browser recorder already stores computed CSS cursor strings on its
    pointermove events. An event-aligned capture adapter may carry that string
    into the hashed pointer_samples. No nearest-target guesses are allowed.
    Critically, role changes are stepwise AFTER the recorded timestamp, never
    anticipated from a future mouse position or nearby button.
    """
    points = manifest.get("pointer_samples", [])
    if not isinstance(points, list) or not np.isfinite(time):
        return "arrow"
    role = "arrow"
    previous_time = -float("inf")
    for sample in points:
        if not isinstance(sample, dict):
            return "arrow"
        stamp = sample.get("t")
        if type(stamp) not in (float,int) or not np.isfinite(stamp) or stamp <= previous_time:
            return "arrow"
        previous_time = stamp
        if stamp > time:
            break
        observed = sample.get("cursor")
        # No role metadata means prior arrow/hand should not persist across
        # newly observed geometry that has not been semantically classified.
        if observed == "pointer":
            role = "hand"
        elif observed in ("text", "vertical-text"):
            role = "text"
        else:
            role = "arrow"
    return role


@lru_cache(maxsize=96)
def _founder_reference_sprite(role: str, pixel_width: int):
    """Reference-inspired cursor artwork with exact source-declared hotspots.

    Uses a new Sauce arrow drawing and CC0-derived hand/I-beam paths. No
    copyrighted screenshot images or UI icon glyphs become product assets.
    """
    if role not in ("arrow","hand","text"):
        raise ValueError("Unknown observed cursor role")
    if type(pixel_width) is not int or not 2 <= pixel_width <= 256:
        raise ValueError("Cursor tile width outside supported bounds")
    from io import BytesIO
    from pathlib import Path
    import xml.etree.ElementTree as ET
    import cairosvg
    from PIL import Image

    expected = {"arrow":(48,56,4,4),"hand":(32,32,10,2),"text":(32,32,16,16)}
    base_w,base_h,tip_x,tip_y=expected[role]
    filename=(Path(__file__).resolve().parents[1]/"assets"/"cursors"
              /"founder-reference"/f"{role}.svg")
    source=filename.read_text(encoding="utf-8")
    tree=ET.fromstring(source)
    if tree.tag!="{http://www.w3.org/2000/svg}svg" or tree.get("viewBox")!=f"0 0 {base_w} {base_h}":
        raise ValueError("Source cursor geometry changed")
    title=tree.find("{http://www.w3.org/2000/svg}title")
    if title is None or f"hotspot {tip_x},{tip_y}" not in (title.text or ""):
        raise ValueError("Source cursor hotspot changed")
    height=round(pixel_width*base_h/base_w)
    raw=cairosvg.svg2png(bytestring=source.encode(),
                          output_width=pixel_width*4,output_height=height*4)
    sprite=Image.open(BytesIO(raw)).convert("RGBA").resize(
        (pixel_width,height),Image.Resampling.LANCZOS)
    return np.asarray(sprite,dtype=np.uint8).copy(),(
        tip_x*pixel_width/base_w,tip_y*height/base_h)


@lru_cache(maxsize=96)
def _sauce_style_sprite(theme: str, pixel_width: int):
    """Rasterize an original Sauce cursor design, preserving its SVG click tip.

    Each preset is deliberately a *cursor*, not a floating annotation icon.
    Its 4,4 SVG hotspot is scaled with the untouched original silhouette.
    Shadows, highlights, and gradients are authored inside each SVG; no
    synthetic movement or state change is introduced by this aesthetic pass.
    """
    if theme not in SAUCE_ORIGINAL_STYLE_PACKS:
        raise ValueError("Unknown Sauce cursor design")
    if type(pixel_width) is not int or not 2 <= pixel_width <= 256:
        raise ValueError("Cursor tile width outside supported renderer bounds")
    from io import BytesIO
    from pathlib import Path
    import xml.etree.ElementTree as ET
    import cairosvg
    from PIL import Image

    source = (Path(__file__).resolve().parents[1]
              / "assets" / "cursors" / "sauce-styles" / f"{theme}.svg")
    svg = source.read_text(encoding="utf-8")
    tree = ET.fromstring(svg)
    if (tree.tag != "{http://www.w3.org/2000/svg}svg"
            or tree.get("viewBox") != "0 0 48 56"):
        raise ValueError("Sauce cursor silhouette coordinate system changed")
    title = tree.find("{http://www.w3.org/2000/svg}title")
    if title is None or "hotspot 4,4" not in (title.text or ""):
        raise ValueError("Sauce cursor's original click hotspot missing")
    pixel_height = round(pixel_width * 56 / 48)
    png = cairosvg.svg2png(bytestring=svg.encode("utf-8"),
                           output_width=pixel_width * 4,
                           output_height=pixel_height * 4)
    art = Image.open(BytesIO(png)).convert("RGBA")
    art = art.resize((pixel_width, pixel_height), Image.Resampling.LANCZOS)
    return (np.asarray(art, dtype=np.uint8).copy(),
            (4.0 * pixel_width / 48.0, 4.0 * pixel_height / 56.0))


@lru_cache(maxsize=96)
def _recorded_cursor_sprite(scale, theme="founder-reference", role="arrow"):
    """Load a precise cursor asset and hotspot for the selected source pack."""
    if theme not in CURSOR_PACKS:
        raise ValueError("Unknown cursor theme")
    if not np.isfinite(scale) or scale<=0:
        raise ValueError("Invalid cursor scale")
    if theme == "founder-reference" or role in ("hand", "text"):
        return _founder_reference_sprite(role,max(2,round(55*scale)))
    if theme in SAUCE_ORIGINAL_STYLE_PACKS:
        return _sauce_style_sprite(theme, max(2, round(55 * scale)))
    if theme == "mint-studio":
        # A 55px logical tile at 1080p with ~0.73 film scale produces a
        # natural ~23x31px painted silhouette; not a giant screen ornament.
        size = max(2,round(55*scale))
        return _mint_svg_sprite("arrow",size)

    # Retained only for explicit before/after and reproducibility. Never
    # silently fall back to it if the source SVG is missing or malformed.
    from PIL import Image
    from online_cursor_assets import icon, hotspot
    artwork = icon("outline")
    apex_x,apex_y=hotspot("outline")
    if scale != 1.:
        dims=(max(2,round(artwork.shape[1]*scale)),
              max(2,round(artwork.shape[0]*scale)))
        artwork=np.asarray(Image.fromarray(artwork,"RGBA").resize(
            dims,Image.Resampling.LANCZOS),dtype=np.uint8)
    return artwork,(apex_x*scale,apex_y*scale)


def draw_pointer(stage, tip_x, tip_y, scale=1., theme="founder-reference", role="arrow"):
    """Render the one real source-timed pointer, not a synthetic cursor path."""
    if not np.isfinite((tip_x,tip_y,scale)).all() or scale<=0:
        raise ValueError("Non-finite source cursor coordinates or scale")
    from cinematic_presentation_v13 import _blend
    effective=round(scale*stage.shape[0]/1080.,4)
    art,(hot_x,hot_y)=_recorded_cursor_sprite(effective,theme,role)
    _blend(stage,art,round(tip_x-hot_x),round(tip_y-hot_y))


@lru_cache(maxsize=2)
def _loupe_cursor_asset(clean=False):
    # Render a conventional arrow on a transparent, supersampled tile.
    # The forward tip sits at (4, 4); rounded joins keep the stem clean.
    from cairosvg import svg2png
    svg = b'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 50">
      <path d="M4 4 L32 29 Q33.5 30.5 31 31 L21 31 L27 43
               Q28 45 26 46 L23 47 Q21 48 20 46 L14 34 L7 40
               Q5 41 5 38 Z" fill="#151618" stroke="#f6f6f6"
        stroke-width="2.05" stroke-linejoin="round"/>
    </svg>'''
    if clean:
        # A straight, constant-width shaft with parallel edges.
        svg = b'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 50">
          <path d="M4 4 L4 35 L12.5 27 L20 43 L25.4 40.5 L17.9 24.5 L29 24.5 Z"
                fill="#121316" stroke="#ffffff" stroke-width="1.65" stroke-linejoin="round"/>
        </svg>'''
    png=svg2png(bytestring=svg,output_width=160,output_height=200)
    rgba=cv2.imdecode(np.frombuffer(png,np.uint8),cv2.IMREAD_UNCHANGED).astype(np.float32)/255.
    rgba[:,:,:3] *= rgba[:,:,3:4]
    return rgba


def draw_loupe_pointer(stage, tip_x, tip_y, *, scale=1., clean=False):
    asset = _loupe_cursor_asset(clean)
    size = scale*stage.shape[0]/1080
    left,top = tip_x-4*size,tip_y-4*size
    x0,y0 = max(0,int(np.floor(left))),max(0,int(np.floor(top)))
    x1,y1 = min(stage.shape[1],int(np.ceil(left+40*size))),min(stage.shape[0],int(np.ceil(top+50*size)))
    if x1<=x0 or y1<=y0:
        return
    matrix = np.float32([[size/4,0,left-x0],[0,size/4,top-y0]])
    cursor = cv2.warpAffine(asset,matrix,(x1-x0,y1-y0),flags=cv2.INTER_LINEAR)
    roi = stage[y0:y1,x0:x1]
    roi[:] = np.rint(roi*(1.-cursor[:,:,3:4])+255.*cursor[:,:,:3])


def project_pointer(stage, track, matrix, time, scale=1., theme="founder-reference", role="arrow"):
    x, y = (np.interp(time, track[:, 0], track[:, col]) for col in (1, 2))
    draw_pointer(stage, *(matrix @ [x, y, 1.]), scale=scale, theme=theme, role=role)
    return stage
