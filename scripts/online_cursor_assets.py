"""Online-sourced premium arrow cursors for Sauce film compositor.

The source SVGs are verbatim MIT-licensed Tabler Icons assets. We theme
their paths at render time instead of drawing a bespoke cursor. No network
calls occur during rendering. Hotspots refer to the original SVG apex.
"""
from __future__ import annotations
from functools import lru_cache
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
from PIL import Image

from cinematic_presentation_v13 import _blend, raster_svg, cursor_press_scale

ROOT=Path(__file__).resolve().parents[1]/'assets'/'cursors'/'tabler'
CURSOR_SIZE=(46,52)
SVG_APEX={'ink':(3.039,4.277),'outline':(3.904,3.904)}
CURSOR_FILES={'ink':'pointer-filled.svg','outline':'pointer-outline.svg'}
# These colors are specifically chosen to match the user's two references:
# black body + white rim, and white body + bold graphite outline.
STYLE_COLORS={
    'ink':('#0B0D12','#FFFFFF','1.45'),
    'outline':('#FEFEFE','#0A0D11','1.85'),
}


def cursor_svg(style:str)->str:
    """Load official Tabler path geometry, applying film-only coloration."""
    if style not in CURSOR_FILES:
        raise ValueError(f'Unknown pointer style {style!r}; use ink or outline')
    svg=ET.fromstring((ROOT/CURSOR_FILES[style]).read_text(encoding='utf-8'))
    fill,stroke,width=STYLE_COLORS[style]
    svg.set('fill','none')
    svg.set('stroke','none')
    svg.set('width',str(CURSOR_SIZE[0]))
    svg.set('height',str(CURSOR_SIZE[1]))
    for child in svg:
        if child.tag.endswith('path'):
            child.set('fill',fill)
            child.set('stroke',stroke)
            child.set('stroke-width',width)
            child.set('stroke-linejoin','round')
            child.set('stroke-linecap','round')
    return ET.tostring(svg,encoding='unicode')


@lru_cache(maxsize=2)
def icon(style:str)->np.ndarray:
    # Cairo SVG 4x supersampling -> one Lanczos downscale.
    pixels=raster_svg(cursor_svg(style),CURSOR_SIZE,supersample=4)
    if pixels.shape!=(CURSOR_SIZE[1],CURSOR_SIZE[0],4):
        raise RuntimeError('Unexpected cursor raster shape')
    return pixels


def hotspot(style:str)->tuple[float,float]:
    if style not in SVG_APEX:raise ValueError(style)
    apex=SVG_APEX[style]
    return (CURSOR_SIZE[0]*apex[0]/24,CURSOR_SIZE[1]*apex[1]/24)


def render_cursor(frame:np.ndarray,
                  position:tuple[float,float],
                  events:list[dict],start_ms:float,elapsed_s:float,
                  factor:float,dx:float,dy:float,
                  style:str)->tuple[int,int]:
    """Put a single persistent Tabler arrow on the final composited frame."""
    from cinematic_presentation_v13 import WINDOW_X,WINDOW_Y
    art=icon(style)
    from cinematic_presentation_v13 import _click_age
    age=_click_age(elapsed_s,events,start_ms,.25)
    scale=cursor_press_scale(age) if age is not None else 1.
    if scale<.999:
        pic=Image.fromarray(art,'RGBA')
        dims=(max(2,round(art.shape[1]*scale)),max(2,round(art.shape[0]*scale)))
        art=np.asarray(pic.resize(dims,Image.Resampling.LANCZOS),dtype=np.uint8)
    h=hotspot(style)
    x=WINDOW_X+dx+position[0]*factor
    y=WINDOW_Y+dy+position[1]*factor
    _blend(frame,art,round(x-h[0]*scale),round(y-h[1]*scale))
    return round(x),round(y)
