"""Original editable SVG cursor artwork traced from the user's references.

User-specified silhouette and angle; not a generic cursor icon. Rendered
as the sole pointer in the final film, with screenshot-native cursor hidden.
The alpha shadow is equivalent to a CSS drop-shadow(0 12px 24px #0006).
"""
from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from math import exp
import numpy as np
from PIL import Image, ImageFilter

from cinematic_presentation_v13 import (
    _blend, _click_age, raster_svg, WINDOW_X, WINDOW_Y,
)

ROOT=Path(__file__).resolve().parents[1]/'assets'/'cursors'/'reference-v15'
PADDING=64
SHADOW_OFFSET=(0,12)
SHADOW_BLUR=24
SHADOW_OPACITY=.35
STYLES={
    # The source artwork's actual upper-left tip is the interaction hotspot.
    'ink': {'file':'black-rounded.svg','view':(70.,86.),'size':(58,70),
            'tip':(6.,4.3)},
    'outline': {'file':'white-outline.svg','view':(86.,87.),'size':(62,64),
                'tip':(5.,3.2)},
}


@dataclass(frozen=True)
class PointerSprite:
    rgba: np.ndarray
    hotspot: tuple[float,float]
    geometry: tuple[int,int]


def press_scale(age:float|None)->float:
    """0.88 peak at 75 ms followed by a critically damped release."""
    if age is None or not 0<=age<.25:return 1.
    if age<=.075:
        u=age/.075
        return 1.-.12*u*u*(3-2*u)
    q=(age-.075)/.175
    omega=8.
    return 1.-.12*(1+omega*q)*exp(-omega*q)


@lru_cache(maxsize=2)
def load_cursor(style:str)->PointerSprite:
    if style not in STYLES:raise ValueError('Cursor style must be ink or outline')
    spec=STYLES[style]
    src=(ROOT/spec['file']).read_text(encoding='utf-8')
    px=raster_svg(src,spec['size'],supersample=4)
    image=Image.fromarray(px,'RGBA')
    w,h=spec['size']
    W=w+PADDING*2
    H=h+PADDING*2
    alpha=Image.new('L',(W,H),0)
    alpha.paste(image.getchannel('A'),
                (PADDING+SHADOW_OFFSET[0],PADDING+SHADOW_OFFSET[1]))
    shadow=alpha.filter(ImageFilter.GaussianBlur(SHADOW_BLUR))
    shadow=shadow.point(lambda a:int(a*SHADOW_OPACITY))
    surface=Image.new('RGBA',(W,H),(0,0,0,0))
    black=Image.new('RGBA',(W,H),(0,0,0,255))
    black.putalpha(shadow)
    surface.alpha_composite(black)
    surface.alpha_composite(image,(PADDING,PADDING))
    sx=w/spec['view'][0]
    sy=h/spec['view'][1]
    tip=(PADDING+spec['tip'][0]*sx,PADDING+spec['tip'][1]*sy)
    return PointerSprite(np.asarray(surface,dtype=np.uint8).copy(),tip,(w,h))


def paint_cursor(frame:np.ndarray,position:tuple[float,float],
                 events:list[dict],start_ms:float,elapsed_s:float,
                 factor:float,dx:float,dy:float,style:str)->tuple[int,int]:
    sprite=load_cursor(style)
    art=sprite.rgba
    age=_click_age(elapsed_s,events,start_ms,.25)
    scale=press_scale(age)
    if scale<.999:
        image=Image.fromarray(art,'RGBA')
        w=max(2,round(art.shape[1]*scale))
        h=max(2,round(art.shape[0]*scale))
        art=np.asarray(image.resize((w,h),Image.Resampling.LANCZOS),dtype=np.uint8)
    x=round(WINDOW_X+dx+position[0]*factor)
    y=round(WINDOW_Y+dy+position[1]*factor)
    _blend(frame,art,round(x-sprite.hotspot[0]*scale),
                     round(y-sprite.hotspot[1]*scale))
    return (x,y)
