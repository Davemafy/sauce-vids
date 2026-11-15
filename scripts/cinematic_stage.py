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
import cv2
from spatial_parallax import window_homography,map_pointer
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
def _stage_base()->tuple[np.ndarray,np.ndarray,np.ndarray]:
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

    ambient=np.asarray(image,dtype=np.uint8)[:,:,::-1].copy()
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
    return bgr,alpha,ambient


@lru_cache(maxsize=1)
def _tilt_mask()->np.ndarray:
    # Preserve window and broad shadow while moving the entire group
    # (not just the product screenshot) in projected 3D.
    mask=Image.new('L',(MASTER_WIDTH,MASTER_HEIGHT),0)
    x,y=WINDOW_X,WINDOW_Y
    d=ImageDraw.Draw(mask)
    d.rounded_rectangle((x,y,x+WINDOW_WIDTH,y+WINDOW_HEIGHT),
                        radius=WINDOW_RADIUS,fill=255)
    for offset,blur,spread,opacity in SHADOWS:
        layer=Image.new('L',(MASTER_WIDTH,MASTER_HEIGHT),0)
        ImageDraw.Draw(layer).rounded_rectangle(
            (x-spread,y+offset-spread,x+WINDOW_WIDTH+spread,
             y+WINDOW_HEIGHT+offset+spread),
            radius=max(1,WINDOW_RADIUS+spread),fill=255)
        layer=layer.filter(ImageFilter.GaussianBlur(blur))
        blend=Image.fromarray(np.maximum(
            np.asarray(mask,dtype=np.uint8),
            np.uint8(np.asarray(layer,dtype=np.float32)*opacity*.75)))
        mask=blend
    return np.asarray(mask,dtype=np.float32)[:,:,None]/255.


@lru_cache(maxsize=1)
def _ambient_pulse_field()->np.ndarray:
    # An inexpensive cached, blurred light map used only when RMS audio
    # is supplied; no audio means a static stage, never fake beats.
    field=Image.new('RGB',(MASTER_WIDTH,MASTER_HEIGHT),(0,0,0))
    for x,y,r,color in (
        (470,610,415,(36,44,78)),
        (1535,405,365,(65,29,66))):
        mask=Image.new('L',(MASTER_WIDTH,MASTER_HEIGHT),0)
        ImageDraw.Draw(mask).ellipse((x-r,y-r,x+r,y+r),fill=205)
        mask=mask.filter(ImageFilter.GaussianBlur(GLOW_BLUR))
        field.paste(color,(0,0),mask)
    return np.asarray(field,dtype=np.uint8)[:,:,::-1].copy()




def _studio_floor(output:np.ndarray,source:np.ndarray,
                  tilt:tuple[float,float],intensity:float)->None:
    """Projection-grounded virtual floor: diffused reflection and two shadows.

    The floor is applied ONLY below the projected browser bottom. Roughened
    reflected pixels are actual website pixels, not a fabricated UI duplicate.
    """
    if intensity<=0:return
    matrix=window_homography(WINDOW_X,WINDOW_Y,WINDOW_WIDTH,WINDOW_HEIGHT,*tilt)
    corners=[map_pointer(matrix,float(x),float(y)) for x,y in (
        (WINDOW_X,WINDOW_Y+WINDOW_HEIGHT),
        (WINDOW_X+WINDOW_WIDTH,WINDOW_Y+WINDOW_HEIGHT))]
    floor_y=max(0,min(MASTER_HEIGHT-6,int(np.ceil(max(q[1] for q in corners)))+1))
    floor_h=MASTER_HEIGHT-floor_y
    if floor_h<8:return
    floor=output[floor_y:,:,:]
    x_center=(corners[0][0]+corners[1][0])*.5
    # Stage floor is intentionally near-black, with an increasingly
    # invisible horizon; never a second neon/gradient visual gimmick.
    ys=np.arange(floor_h,dtype=np.float32)[:,None]
    xs=np.arange(MASTER_WIDTH,dtype=np.float32)[None,:]
    taper=np.clip(1-ys/max(18.,float(floor_h)),0,1)
    lateral=np.exp(-((xs-x_center)/730.)**2)
    plane=(taper*lateral).astype(np.float32)
    floor[:]=np.uint8(np.clip(
        floor.astype(np.float32)*(1-plane[:,:,None]*.13),0,255))

    # Two independent directional floor shadows: dark contact under base,
    # broader cast shifted slightly away from a 35-degree virtual key light.
    contact=np.zeros((floor_h,MASTER_WIDTH),np.float32)
    ambient=np.zeros_like(contact)
    lean=float(tilt[1])*8.
    cv2.ellipse(contact,(round(x_center+lean),9),
                (max(1,round(WINDOW_WIDTH*.37)),15),0,0,360,.56,-1,cv2.LINE_AA)
    cv2.ellipse(ambient,(round(x_center+45+lean),30),
                (max(1,round(WINDOW_WIDTH*.54)),65),0,0,360,.24,-1,cv2.LINE_AA)
    contact=cv2.GaussianBlur(contact,(0,0),9)
    ambient=cv2.GaussianBlur(ambient,(0,0),26)
    dark=np.clip(contact+ambient,0,.72)*plane
    floor[:]=np.uint8(np.clip(floor.astype(np.float32)*(1-dark[:,:,None]),0,255))

    # True reflective pixels from the window base. Horizontal plane
    # contracts with depth; Gaussian convolution simulates roughness .35.
    ref_h=min(110,source.shape[0])
    sample=cv2.flip(source[-ref_h:].copy(),0)
    src=np.float32([[0,0],[WINDOW_WIDTH-1,0],
                    [WINDOW_WIDTH-1,ref_h-1],[0,ref_h-1]])
    near_l,near_r=corners[0][0],corners[1][0]
    far_l=near_l+160
    far_r=near_r-160
    dst=np.float32([[near_l,0],[near_r,0],
                    [far_r,floor_h-1],[far_l,floor_h-1]])
    homography=cv2.getPerspectiveTransform(src,dst)
    reflected=cv2.warpPerspective(sample,homography,(MASTER_WIDTH,floor_h),
                flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
    reflected=cv2.GaussianBlur(reflected,(0,0),4.5)
    fade=(np.clip(1-ys/max(1,floor_h),0,1)**2
          *np.exp(-((xs-x_center)/690.)**2)).astype(np.float32)
    strength=np.clip(fade*intensity,0,.5)[:,:,None]
    floor[:]=np.uint8(np.clip(
        floor.astype(np.float32)*(1-strength)
        +reflected.astype(np.float32)*strength,0,255))


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
    enable_studio_floor:bool=False
    floor_reflection_intensity:float=.25

    def __post_init__(self):
        if (self.width,self.height)!=(MASTER_WIDTH,MASTER_HEIGHT):
            raise ValueError('Production stage is fixed to 1920x1080')
        if not 0<=self.floor_reflection_intensity<=.5:
            raise ValueError('Floor intensity must be between 0 and .5')
        if (self.window_x,self.window_y,self.window_w,self.window_h)!=(
            WINDOW_X,WINDOW_Y,WINDOW_WIDTH,WINDOW_HEIGHT):
            raise ValueError('Window must be centered and 1480px wide')

    @property
    def window(self)->tuple[int,int,int,int]:
        return self.window_x,self.window_y,self.window_w,self.window_h

    def render(self,website_frame:np.ndarray,
               cinematic_cursor:Callable[[np.ndarray],None]|None=None,
               tilt:tuple[float,float]=(0.,0.),glow:float=0.)->np.ndarray:
        """Outer composition: ambient -> 3D window -> final SVG pointer.

        tilt and glow are deterministic frame-indexed inputs. The source
        website array is never modified.
        """
        if website_frame.shape!=(self.window_h,self.window_w,3):
            raise ValueError('Source must be resized to the root window before wrapping')
        if not 0.<=glow<=1.:raise ValueError('RMS-driven glow must be normalized 0..1')
        base,alpha,ambient=_stage_base()
        flat=base.copy()
        x,y,w,h=self.window
        region=flat[y:y+h,x:x+w]
        region[:]=np.uint8(np.clip(
            region.astype(np.float32)*(1-alpha)+website_frame.astype(np.float32)*alpha,0,255))
        if abs(tilt[0])+abs(tilt[1])>1e-5:
            homography=window_homography(x,y,w,h,*tilt)
            warped=cv2.warpPerspective(flat,homography,(self.width,self.height),
                     flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,
                     borderValue=(0,0,0))
            mask=cv2.warpPerspective(_tilt_mask()[:,:,0],homography,
                      (self.width,self.height),flags=cv2.INTER_LINEAR,
                      borderMode=cv2.BORDER_CONSTANT)[:,:,None]
            output=np.uint8(np.clip(
                ambient.astype(np.float32)*(1-mask)+warped.astype(np.float32)*mask,
                0,255))
        else:
            output=flat
        if glow>0:
            extra=_ambient_pulse_field()
            # Glow must never overpower or re-color the content.
            # Modulate outside the transformed window only.
            area=cv2.warpPerspective(_tilt_mask()[:,:,0],
                     window_homography(x,y,w,h,*tilt),
                     (self.width,self.height))[:,:,None] if (
                      abs(tilt[0])+abs(tilt[1])>1e-5) else _tilt_mask()
            output=np.uint8(np.clip(output.astype(np.float32)+
                  extra.astype(np.float32)*(glow*.68)*(1-area),0,255))
        if self.enable_studio_floor:
            _studio_floor(output,website_frame,tilt,self.floor_reflection_intensity)
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
             t:float,source_factor:float,shift_x:float,shift_y:float,
             tilt:tuple[float,float]=(0.,0.))->None:
        from cinematic_presentation_v13 import _blend,click_ring_frames
        from reference_cursor_v15 import load_cursor,press_scale
        if position is None:return
        ox,oy=self.stage.window[:2]
        homography=(window_homography(*self.stage.window,*tilt)
                    if abs(tilt[0])+abs(tilt[1])>1e-5 else None)
        def point(px:float,py:float)->tuple[int,int]:
            if homography is not None:
                px,py=map_pointer(homography,px,py)
            return round(px),round(py)
        # Click ripple under pointer, tied to actual pointerdown timestamp.
        rings=click_ring_frames()
        for ev in self.events:
            if ev['type']!='pointerdown' or ev.get('x') is None:continue
            age=t-(ev['t']-self.start_ms)/1000.
            if not 0<=age<.33:continue
            px,py=point(ox+shift_x+ev['x']*source_factor,
                        oy+shift_y+ev['y']*source_factor)
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
        x,y=point(ox+shift_x+position[0]*source_factor,
                  oy+shift_y+position[1]*source_factor)
        _blend(output,art,round(x-image.hotspot[0]*scale),
                  round(y-image.hotspot[1]*scale))
