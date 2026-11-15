"""Sauce v13 production presentation compositor.

SVG-authored pointer and ripple; never a native X11 hand or a DOM screenshot
of a cursor. Both are rasterized from the editable vector assets at 4x and
composited after the real browser frame. Every motion sample is produced by
Spring2D in spring_motion.cursor_track().
"""
from __future__ import annotations
from functools import lru_cache
from io import BytesIO
from pathlib import Path
import math
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import cairosvg

MASTER_W,MASTER_H=1920,1080
WINDOW_X,WINDOW_Y,WINDOW_W,WINDOW_H=160,50,1600,900
RADIUS=20
SOURCE=Path(__file__).resolve().parents[1]/'assets'/'cursors'
POINTER_HOTSPOT=(2.8,2.4)
POINTER_SIZE=(28,38)


def _blurred_ellipse(im:Image.Image,cx:int,cy:int,rx:int,ry:int,
                     color:tuple[int,int,int],strength:int)->None:
    a=Image.new('L',(MASTER_W,MASTER_H),0)
    ImageDraw.Draw(a).ellipse((cx-rx,cy-ry,cx+rx,cy+ry),fill=strength)
    a=a.filter(ImageFilter.GaussianBlur(120))
    im.paste(color,(0,0),a)


@lru_cache(maxsize=1)
def make_dark_stage()->tuple[np.ndarray,np.ndarray]:
    """Dark gradient, ambient blob, and CSS-equivalent multilayer shadows."""
    xx=np.linspace(0.,1.,MASTER_W,dtype=np.float32)[None,:,None]
    yy=np.linspace(0.,1.,MASTER_H,dtype=np.float32)[:,None,None]
    top=np.array([15.,17.,26.],dtype=np.float32)
    bottom=np.array([24.,27.,39.],dtype=np.float32)
    # Dark even behind pale product footage, avoiding bright flat margins.
    rgb=np.broadcast_to(top*(1-yy)+bottom*yy,(MASTER_H,MASTER_W,3)).copy()
    # slight studio-like illumination toward the center of the background
    rgb+=np.array([5.,4.,5.],dtype=np.float32)*(1-np.abs(xx-.50)*1.25)
    canvas=Image.fromarray(np.uint8(np.clip(rgb,0,255)),'RGB')
    _blurred_ellipse(canvas,365,555,300,320,(83,108,186),185)
    _blurred_ellipse(canvas,1580,415,275,265,(152,95,157),145)
    _blurred_ellipse(canvas,960,945,355,180,(66,94,151),106)
    x,y,w,h=WINDOW_X,WINDOW_Y,WINDOW_W,WINDOW_H
    # Wide-diffusion CSS tiers, plus a short contact shadow.
    for offset,blur,spread,opacity in (
        (50,100,-20,.30),
        (25,50,-12,.50),
        (8,17,0,.28),
    ):
        mask=Image.new('L',(MASTER_W,MASTER_H),0)
        b=(x-spread,y+offset-spread,x+w+spread,y+h+offset+spread)
        ImageDraw.Draw(mask).rounded_rectangle(b,radius=RADIUS+3,fill=255)
        mask=mask.filter(ImageFilter.GaussianBlur(blur))
        mask=mask.point(lambda alpha,a=opacity:round(alpha*a))
        canvas.paste((0,0,4),(0,0),mask)

    d=ImageDraw.Draw(canvas)
    d.rounded_rectangle((x-2,y-2,x+w+1,y+h+1),radius=RADIUS+2,
                        fill=(19,22,30),outline=(104,110,127),width=1)
    # Inner highlight edge (equivalent to white 8%-opacity rim).
    d.rounded_rectangle((x,y,x+w-1,y+h-1),radius=RADIUS+1,
                        outline=(59,64,77),width=2)
    clip=Image.new('L',(w,h),0)
    ImageDraw.Draw(clip).rounded_rectangle((0,0,w-1,h-1),radius=RADIUS,fill=255)
    arr=np.asarray(canvas)[:,:,::-1].copy()
    alpha=np.asarray(clip,dtype=np.float32)[:,:,None]/255.
    return arr,alpha


def raster_svg(svg_text:str,size:tuple[int,int],supersample:int=4)->np.ndarray:
    w,h=size
    raw=cairosvg.svg2png(bytestring=svg_text.encode('utf-8'),
                         output_width=w*supersample,output_height=h*supersample)
    pic=Image.open(BytesIO(raw)).convert('RGBA')
    pic=pic.resize((w,h),Image.Resampling.LANCZOS)
    return np.asarray(pic,dtype=np.uint8)


@lru_cache(maxsize=1)
def pointer_image()->np.ndarray:
    return raster_svg((SOURCE/'sauce-pointer.svg').read_text(),POINTER_SIZE)


def cursor_press_scale(elapsed:float)->float:
    """Contract to 85% on real mouse down, then settle without cartoon bounce."""
    if elapsed<0 or elapsed>=.25:return 1.
    if elapsed<=.075:
        q=elapsed/.075
        return 1-.15*(q*q*(3-2*q))
    t=(elapsed-.075)/.175
    omega=7.8
    return 1-.15*(1+omega*t)*math.exp(-omega*t)


def _blend(dst:np.ndarray,src_rgba:np.ndarray,hot_x:int,hot_y:int)->None:
    """Premultiplied-style correct subframe alpha blend, bounded by frame."""
    h,w=src_rgba.shape[:2]
    x0=max(0,hot_x);y0=max(0,hot_y)
    x1=min(dst.shape[1],hot_x+w);y1=min(dst.shape[0],hot_y+h)
    if x0>=x1 or y0>=y1:return
    patch=dst[y0:y1,x0:x1]
    src=src_rgba[y0-hot_y:y1-hot_y,x0-hot_x:x1-hot_x]
    a=src[:,:,3:4].astype(np.float32)/255
    bgr=src[:,:,:3][:,:,[2,1,0]]
    patch[:]=np.uint8(np.clip(patch*(1-a)+bgr*a,0,255))


@lru_cache(maxsize=1)
def click_ring_frames()->tuple[np.ndarray,...]:
    template=(SOURCE/'sauce-click-ripple.svg').read_text()
    out=[]
    for i in range(22):
        progress=i/21
        radius=7+21*(1-(1-progress)**2.5)
        opacity=.48*(1-progress)**1.4
        width=1.7-.6*progress
        svg=(template.replace('{{RADIUS}}',f'{radius:.3f}')
                     .replace('{{WIDTH}}',f'{width:.3f}')
                     .replace('{{OPACITY}}',f'{opacity:.4f}'))
        out.append(raster_svg(svg,(72,72)))
    return tuple(out)


def _click_age(elapsed_s:float,events:list[dict],start_ms:float,
               window_s:float=.33)->float|None:
    ages=[elapsed_s-(e['t']-start_ms)/1000
          for e in events if e['type']=='pointerdown' and e.get('x') is not None]
    alive=[x for x in ages if 0<=x<window_s]
    return min(alive) if alive else None


def paint_click_ripple(frame:np.ndarray,events:list[dict],start_ms:float,
                       elapsed_s:float,factor:float,dx:float,dy:float)->None:
    rings=click_ring_frames()
    for event in events:
        if event['type']!='pointerdown' or event.get('x') is None:continue
        age=elapsed_s-(event['t']-start_ms)/1000
        if not 0<=age<.33:continue
        x=WINDOW_X+dx+event['x']*factor
        y=WINDOW_Y+dy+event['y']*factor
        index=min(len(rings)-1,int(age/.33*len(rings)))
        _blend(frame,rings[index],round(x)-36,round(y)-36)


def paint_svg_pointer(frame:np.ndarray,position:tuple[float,float],
                      events:list[dict],start_ms:float,elapsed_s:float,
                      factor:float,dx:float,dy:float)->tuple[int,int]:
    # Position is Spring2D-integrated and remains the real recorded pointer,
    # including through the click; never switch to an X11 hand.
    svg=pointer_image()
    age=_click_age(elapsed_s,events,start_ms,.25)
    scale=cursor_press_scale(age) if age is not None else 1.
    if scale<.999:
        im=Image.fromarray(svg,'RGBA')
        nw=max(2,round(svg.shape[1]*scale))
        nh=max(2,round(svg.shape[0]*scale))
        svg=np.asarray(im.resize((nw,nh),Image.Resampling.LANCZOS),dtype=np.uint8)
    mx=WINDOW_X+dx+position[0]*factor
    my=WINDOW_Y+dy+position[1]*factor
    offx=round(POINTER_HOTSPOT[0]*scale)
    offy=round(POINTER_HOTSPOT[1]*scale)
    _blend(frame,svg,round(mx)-offx,round(my)-offy)
    return round(mx),round(my)
