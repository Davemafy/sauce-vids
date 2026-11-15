"""Sauce's presentation-only visual layers: stage, cursor, and click feedback.

Everything is composited OUTSIDE the source DOM. Recorded pixels, click
timestamps and target boxes remain authoritative. Glow never covers source UI.
No fake native/macOS browser titlebar is inserted.
"""
from __future__ import annotations
from functools import lru_cache
from presentation_contract import presentation_css_cursor,press_scale,modal_spring_scale
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

MASTER_W, MASTER_H = 1920, 1080
WINDOW_X, WINDOW_Y, WINDOW_W, WINDOW_H = 160, 50, 1600, 900
FRAME_RADIUS = 21


def _rounded_mask(bounds:tuple[int,int,int,int],radius:int,blur:float=0)->Image.Image:
    layer=Image.new('L',(MASTER_W,MASTER_H),0)
    ImageDraw.Draw(layer).rounded_rectangle(bounds,radius=radius,fill=255)
    return layer.filter(ImageFilter.GaussianBlur(blur)) if blur else layer


def _glow(background:Image.Image,point:tuple[int,int],
          hue:tuple[int,int,int],radius:int,alpha:int)->None:
    # Glow is deliberately located BEHIND the stage, not over web pixels.
    mask=Image.new('L',(MASTER_W,MASTER_H),0)
    x,y=point
    ImageDraw.Draw(mask).ellipse((x-radius,y-radius,x+radius,y+radius),fill=alpha)
    mask=mask.filter(ImageFilter.GaussianBlur(120))
    background.paste(hue,(0,0),mask)


@lru_cache(maxsize=1)
def draw_stage() -> tuple[np.ndarray,np.ndarray]:
    """Precompute the 1080p matte, atmospheric glow and layered shadows once."""
    bg=Image.new('RGB',(MASTER_W,MASTER_H),(236,236,232))
    _glow(bg,(385,650),(99,130,208),275,113)
    _glow(bg,(1575,375),(220,167,142),260,96)
    _glow(bg,(970,960),(160,178,172),250,64)

    x,y,w,h=WINDOW_X,WINDOW_Y,WINDOW_W,WINDOW_H
    # CSS-like multi-tier shadows: y-offset 50 with wide diffusion;
    # y-offset 25 at higher opacity; and a local contact shadow.
    tiers=(
      (48,98,-20,.30),
      (25,48,-12,.48),
      (7,19,-2,.18),
    )
    for y_offset,blur,spread,opacity in tiers:
        bounds=(x-spread,y+y_offset-spread,x+w+spread,y+h+y_offset+spread)
        shadow=_rounded_mask(bounds,FRAME_RADIUS,blur)
        alpha=shadow.point(lambda a,p=opacity:int(a*p))
        bg.paste((10,15,21),(0,0),alpha)

    d=ImageDraw.Draw(bg)
    # Crisp outline plus fine inner edge; site UI fills the transparent hole.
    d.rounded_rectangle((x-1,y-1,x+w,y+h),radius=FRAME_RADIUS+1,
                         fill=(245,245,243),outline=(88,94,97),width=2)
    d.rounded_rectangle((x+1,y+1,x+w-2,y+h-2),radius=FRAME_RADIUS,
                         outline=(255,255,255),width=2)
    clip=Image.new('L',(w,h),0)
    ImageDraw.Draw(clip).rounded_rectangle((0,0,w-1,h-1),radius=FRAME_RADIUS,
                                            fill=255)
    # Clip is independent of image content; no source pixel replacement.
    base=np.asarray(bg,dtype=np.uint8)[:,:,::-1].copy()
    alpha=np.asarray(clip,dtype=np.float32)[:,:,None]/255.
    return base,alpha


def compose_cursor(frame:np.ndarray,assets,css:str|None,
                   position:tuple[float,float]|None,
                   source_factor:float,shift_x:float,shift_y:float,
                   action_boxes:list[dict],time_s:float,start_ms:float,
                   events:list[dict])->tuple[float,float]|None:
    if position is None:return None
    cursor_type=presentation_css_cursor(css,position,action_boxes)
    asset=assets[cursor_type]
    image=asset.rgba
    scale=press_scale(events,time_s,start_ms)
    if scale!=1.:
        from PIL import Image as PImage
        width=max(2,round(image.width*scale))
        height=max(2,round(image.height*scale))
        image=image.resize((width,height),PImage.Resampling.LANCZOS)
    rgba=np.asarray(image,dtype=np.uint8)
    rgb=rgba[:,:,:3][:,:,[2,1,0]]
    a=rgba[:,:,3:4].astype(np.float32)/255.
    # Hotspot is kept fixed during press scaling.
    hot_x=round(asset.hotspot_x*scale)
    hot_y=round(asset.hotspot_y*scale)
    center_x=WINDOW_X+shift_x+position[0]*source_factor
    center_y=WINDOW_Y+shift_y+position[1]*source_factor
    x=round(center_x)-hot_x
    y=round(center_y)-hot_y
    h,w=rgba.shape[:2]
    left=max(WINDOW_X,x);top=max(WINDOW_Y,y)
    right=min(WINDOW_X+WINDOW_W,x+w)
    bottom=min(WINDOW_Y+WINDOW_H,y+h)
    if left<right and top<bottom:
        dest=frame[top:bottom,left:right]
        src=rgb[top-y:bottom-y,left-x:right-x]
        alpha=a[top-y:bottom-y,left-x:right-x]
        dest[:]=np.uint8(dest*(1-alpha)+src*alpha)
    return (center_x,center_y)


def click_feedback(frame:np.ndarray,events:list[dict],start_ms:float,
                   time_s:float,source_factor:float,dx:float,dy:float):
    """Anti-aliased click confirmation timed to actual pointerdown, not animation."""
    for e in events:
        if e['type']!='pointerdown' or e.get('x') is None:continue
        elapsed=time_s-(e['t']-start_ms)/1000.
        if not 0<=elapsed<=.31:continue
        p=elapsed/.31
        eased=1-(1-p)**3
        radius=8+23*eased
        x=round(WINDOW_X+dx+e['x']*source_factor)
        y=round(WINDOW_Y+dy+e['y']*source_factor)
        size=round(radius+8)
        x0=max(WINDOW_X,x-size);y0=max(WINDOW_Y,y-size)
        x1=min(WINDOW_X+WINDOW_W,x+size+1)
        y1=min(WINDOW_Y+WINDOW_H,y+size+1)
        if x1<=x0 or y1<=y0:continue
        roi=frame[y0:y1,x0:x1]
        # Ring is on the video frame, behind the cursor; no circular
        # spotlight or large indicator obscuring the target.
        opacity=.46*(1-p)**1.5
        ring=np.zeros_like(roi)
        mask=np.zeros(roi.shape[:2],np.uint8)
        cv2.circle(mask,(x-x0,y-y0),round(radius),255,2,cv2.LINE_AA)
        a=(mask.astype(np.float32)/255*opacity)[:,:,None]
        roi[:]=np.uint8(roi.astype(np.float32)*(1-a)+
                        np.array([35.,46.,45.],dtype=np.float32)*a)


