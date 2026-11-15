"""Outermost cinematic frame root for every Sauce production replay.

The actual renderer is offscreen Chromium -> OpenCV -> FFmpeg, not React.
CinematicStage is the single final-frame wrapper; CinematicCursor is its
last visual child. Styling the web player alone cannot change video pixels.
"""
from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
from typing import Callable
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

MASTER_WIDTH,MASTER_HEIGHT=1920,1080
STAGE_BACKGROUND=(9,10,15)   # #090a0f
WINDOW_WIDTH=1480
WINDOW_HEIGHT=832
WINDOW_X=(MASTER_WIDTH-WINDOW_WIDTH)//2
WINDOW_Y=(MASTER_HEIGHT-WINDOW_HEIGHT)//2
WINDOW_RADIUS=16
FRAME_RGB=(18,18,24)
FRAME_OPACITY=.90
BACKDROP_BLUR=24
GLOW_BLUR=140
FRAME_BORDER=(255,255,255,.12)
HIGHLIGHT=(255,255,255,.08)
# CSS-compatible tiers:
# 0 40px 80px -20px rgba(0,0,0,.7)
# 0 80px 160px -40px rgba(0,0,0,.5)
SHADOWS=((40,80,-20,.70),(80,160,-40,.50))


def _mix_color(base:Image.Image,mask:Image.Image,color:tuple[int,int,int])->None:
    base.paste(color,(0,0),mask)


@lru_cache(maxsize=1)
def _stage_base()->tuple[np.ndarray,np.ndarray]:
    """Build the stage once; every output frame shares identical typography-safe background."""
    image=Image.new('RGB',(MASTER_WIDTH,MASTER_HEIGHT),STAGE_BACKGROUND)
    # Two broad, blurred gradient blooms below the frame. No color is
    # projected over the website: only the canvas behind the window.
    for x,y,rx,ry,color,alpha in (
        (470,610,425,370,(74,88,171),173),
        (1535,405,395,345,(123,74,149),144),
        (980,910,430,260,(63,83,124),91),
    ):
        mask=Image.new('L',(MASTER_WIDTH,MASTER_HEIGHT),0)
        ImageDraw.Draw(mask).ellipse((x-rx,y-ry,x+rx,y+ry),fill=alpha)
        _mix_color(image,mask.filter(ImageFilter.GaussianBlur(GLOW_BLUR)),color)

    left,top=WINDOW_X,WINDOW_Y
    right,bottom=left+WINDOW_WIDTH,top+WINDOW_HEIGHT
    # Render wide-diffusion shadows before drawing the window surface.
    # Negative spread narrows the mask before blur, matching CSS shadow geometry.
    for dy,blur,spread,opacity in SHADOWS:
        mask=Image.new('L',(MASTER_WIDTH,MASTER_HEIGHT),0)
        bounds=(left-spread,top+dy-spread,right+spread,bottom+dy+spread)
        ImageDraw.Draw(mask).rounded_rectangle(
            bounds,radius=max(1,WINDOW_RADIUS+spread),fill=255)
        mask=mask.filter(ImageFilter.GaussianBlur(blur))
        mask=mask.point(lambda a,o=opacity:round(a*o))
        image.paste((0,0,0),(0,0),mask)

    # The translucent frame backing samples the actual stage beneath it,
    # equivalent to backdrop-filter:blur(24px) + rgba(18,18,24,.90).
    region=image.crop((left,top,right,bottom))
    blurred=region.filter(ImageFilter.GaussianBlur(BACKDROP_BLUR))
    overlay=Image.new('RGB',(WINDOW_WIDTH,WINDOW_HEIGHT),FRAME_RGB)
    surface=Image.blend(blurred,overlay,FRAME_OPACITY)
    shape=Image.new('L',(WINDOW_WIDTH,WINDOW_HEIGHT),0)
    ImageDraw.Draw(shape).rounded_rectangle(
        (0,0,WINDOW_WIDTH-1,WINDOW_HEIGHT-1),radius=WINDOW_RADIUS,fill=255)
    image.paste(surface,(left,top),shape)

    # One-pixel 12%-white border plus an 8%-white inner highlight.
    draw=ImageDraw.Draw(image)
    rim=tuple(round(v*.12+18*.88) for v in FRAME_BORDER[:3])
    draw.rounded_rectangle((left,top,right-1,bottom-1),
        radius=WINDOW_RADIUS,outline=rim,width=1)
    inner=tuple(round(18*(1-.08)+255*.08) for _ in range(3))
    draw.rounded_rectangle((left+1,top+1,right-2,bottom-2),
        radius=WINDOW_RADIUS-1,outline=inner,width=1)

    clip=Image.new('L',(WINDOW_WIDTH,WINDOW_HEIGHT),0)
    ImageDraw.Draw(clip).rounded_rectangle(
        (1,1,WINDOW_WIDTH-2,WINDOW_HEIGHT-2),
        radius=WINDOW_RADIUS-1,fill=255)
    bgr=np.asarray(image,dtype=np.uint8)[:,:,::-1].copy()
    alpha=np.asarray(clip,dtype=np.float32)[:,:,None]/255.
    return bgr,alpha


@dataclass(frozen=True)
class CinematicStage:
    """Absolute root video wrapper, never an optional nested UI decoration."""
    width:int=MASTER_WIDTH
    height:int=MASTER_HEIGHT
    window_x:int=WINDOW_X
    window_y:int=WINDOW_Y
    window_w:int=WINDOW_WIDTH
    window_h:int=WINDOW_HEIGHT
    background_hex:str='#090a0f'

    def __post_init__(self):
        if (self.width,self.height)!=(MASTER_WIDTH,MASTER_HEIGHT):
            raise ValueError('Production stage is fixed to 1920x1080')
        if (self.window_x,self.window_y,self.window_w,self.window_h)!=(
            WINDOW_X,WINDOW_Y,WINDOW_WIDTH,WINDOW_HEIGHT):
            raise ValueError('Window must be centered and 1480px wide')

    @property
    def window(self)->tuple[int,int,int,int]:
        return self.window_x,self.window_y,self.window_w,self.window_h

    def render(self,website_frame:np.ndarray,
               cinematic_cursor:Callable[[np.ndarray],None]|None=None)->np.ndarray:
        """Wrap the real site pixels, then draw the cursor in the TOPMOST layer."""
        if website_frame.shape!=(self.window_h,self.window_w,3):
            raise ValueError('Source must be resized to the root window before wrapping')
        base,alpha=_stage_base()
        output=base.copy()
        x,y,w,h=self.window
        region=output[y:y+h,x:x+w]
        region[:]=np.uint8(np.clip(
            region.astype(np.float32)*(1-alpha)+website_frame.astype(np.float32)*alpha,0,255))
        if cinematic_cursor is not None:
            cinematic_cursor(output)
        return output


class CinematicCursor:
    """Sole visible film pointer, linked to the verified Spring2D trace."""
    def __init__(self,stage:CinematicStage,events:list[dict],
                 start_ms:float,style:str='ink',scale:float=.56):
        if not .35<=scale<=1:raise ValueError('Cursor scale out of bounds')
        if style not in ('ink','outline'):raise ValueError('Unsupported cursor style')
        self.stage,self.events,self.start_ms,self.style,self.scale=(
            stage,events,start_ms,style,scale)

    def draw(self,output:np.ndarray,position:tuple[float,float]|None,
             t:float,source_factor:float,shift_x:float,shift_y:float)->None:
        from cinematic_presentation_v13 import _blend,click_ring_frames
        from reference_cursor_v15 import load_cursor,press_scale
        if position is None:return
        ox,oy=self.stage.window[:2]
        # Click ripple under pointer, tied to actual pointerdown timestamp.
        rings=click_ring_frames()
        for ev in self.events:
            if ev['type']!='pointerdown' or ev.get('x') is None:continue
            age=t-(ev['t']-self.start_ms)/1000.
            if not 0<=age<.33:continue
            px=round(ox+shift_x+ev['x']*source_factor)
            py=round(oy+shift_y+ev['y']*source_factor)
            k=min(len(rings)-1,int(age/.33*len(rings)))
            _blend(output,rings[k],px-36,py-36)

        # Supersampled original vector remains sized 32x39px (the user's
        # approved proportion), not the previous oversized 58x70px.
        age=min((t-(ev['t']-self.start_ms)/1000. for ev in self.events
                if ev['type']=='pointerdown' and ev.get('x') is not None
                and 0<=t-(ev['t']-self.start_ms)/1000.<.25),default=None)
        image=load_cursor(self.style)
        scale=self.scale*press_scale(age)
        art=image.rgba
        if scale<.999:
            from PIL import Image as PILImage
            width=max(2,round(art.shape[1]*scale))
            height=max(2,round(art.shape[0]*scale))
            art=np.asarray(PILImage.fromarray(art,'RGBA').resize(
                (width,height),PILImage.Resampling.LANCZOS),dtype=np.uint8)
        x=round(ox+shift_x+position[0]*source_factor)
        y=round(oy+shift_y+position[1]*source_factor)
        _blend(output,art,round(x-image.hotspot[0]*scale),
                  round(y-image.hotspot[1]*scale))
