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
from spatial_parallax import window_homography,map_pointer,projected_target_quad
from multi_plane_depth import (
    focus_background_plane,composite_elevated_modal,RIM_COLOR)
from PIL import Image, ImageDraw, ImageFilter
from procedural_backdrops import procedural_backdrop, STYLES, brand_bloom
from stage_optics import apply_stage_optics

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


def brand_light_parameters(primary:str|None,accent:str|None):
    """Bound edge dispersion / H60 exterior rim to actual captured hues."""
    if primary is None or accent is None:
        return RIM_COLOR,(2.,2.)
    p=tuple(int(primary[i:i+2],16) for i in (1,3,5))
    a=tuple(int(accent[i:i+2],16) for i in (1,3,5))
    bgr=(a[2],a[1],a[0])
    rim=tuple(round(.94*v+.06*c) for v,c in zip(RIM_COLOR,bgr))
    weights=(round(1.1+.9*p[0]/255.,3),
             round(1.1+.9*a[2]/255.,3))
    return rim,weights


@lru_cache(maxsize=4)
def _stage_base(backdrop_style:str='obsidian-grain',
                brand_primary:str|None=None,
                brand_accent:str|None=None)->tuple[np.ndarray,np.ndarray,np.ndarray]:
    """Key the full stage cache by material; never return a stale flat plate."""
    # Procedural material is static in the output clock and appears ONLY
    # behind the original H0/H60 browser/window, never above UI text.
    material=procedural_backdrop(backdrop_style,MASTER_WIDTH,MASTER_HEIGHT,
                                  primary=brand_primary,accent=brand_accent)
    image=Image.fromarray(material[:,:,::-1].copy(),mode='RGB')
    ambient=material.copy()
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


@lru_cache(maxsize=4)
def _ambient_pulse_field(brand_primary:str|None=None,
                         brand_accent:str|None=None)->np.ndarray:
    # An inexpensive cached, blurred light map used only when RMS audio
    # is supplied; no audio means a static stage, never fake beats.
    field=Image.new('RGB',(MASTER_WIDTH,MASTER_HEIGHT),(0,0,0))
    for x,y,r,color in (
        (470,610,415,tuple(round(v) for v in reversed(brand_bloom(
            brand_primary,78,(78.,44.,36.))))),
        (1535,405,365,tuple(round(v) for v in reversed(brand_bloom(
            brand_accent,66,(66.,29.,65.)))))):
        mask=Image.new('L',(MASTER_WIDTH,MASTER_HEIGHT),0)
        ImageDraw.Draw(mask).ellipse((x-r,y-r,x+r,y+r),fill=205)
        mask=mask.filter(ImageFilter.GaussianBlur(GLOW_BLUR))
        field.paste(color,(0,0),mask)
    return np.asarray(field,dtype=np.uint8)[:,:,::-1].copy()




def _studio_floor(output:np.ndarray,source:np.ndarray,
                  tilt:tuple[float,float],intensity:float,
                  focal:float=1820.)->None:
    """Projection-grounded virtual floor: diffused reflection and two shadows.

    The floor is applied ONLY below the projected browser bottom. Roughened
    reflected pixels are actual website pixels, not a fabricated UI duplicate.
    """
    if intensity<=0:return
    matrix=window_homography(WINDOW_X,WINDOW_Y,WINDOW_WIDTH,WINDOW_HEIGHT,*tilt,focal=focal)
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


def apply_spotlight_focus(frame:np.ndarray,box:dict,
                          stage_window:tuple[int,int,int,int],
                          factor:float,dx:float,dy:float,
                          tilt:tuple[float,float],focal:float=1200.,
                          blur_px:float=6.,dim_opacity:float=.25)->np.ndarray:
    """Cinematic focus: sharp real UI region, projected 1px rim, contact shadow.

    The same homography maps the browser quad, cursor, and focus bounds.
    Inactive browser pixels are blurred/dimmed; outside-stage ambient remains
    unaffected. This never repaints the original UI or modifies source pixels.
    """
    if frame.ndim!=3 or frame.shape[2]!=3:raise ValueError('Expected BGR frame')
    if not 0<=blur_px<=6 or not 0<=dim_opacity<=.7:
        raise ValueError('Invalid spotlight parameters')
    x,y,w,h=stage_window
    H=window_homography(x,y,w,h,*tilt,focal=focal)
    window=np.float32([[x,y],[x+w,y],[x+w,y+h],[x,y+h]]).reshape(1,4,2)
    window_quad=cv2.perspectiveTransform(window,H)[0]
    target_quad=projected_target_quad(box,stage_window,factor,dx,dy,
                                      *tilt,perspective_px=focal)
    if not np.isfinite(target_quad).all():raise ValueError('Invalid target projection')
    out=frame.copy()
    # Focus effects are bounded to the projected browser window.
    left=max(0,int(np.floor(np.min(window_quad[:,0])))-6)
    right=min(frame.shape[1],int(np.ceil(np.max(window_quad[:,0])))+7)
    top=max(0,int(np.floor(np.min(window_quad[:,1])))-6)
    bottom=min(frame.shape[0],int(np.ceil(np.max(window_quad[:,1])))+7)
    if right<=left or bottom<=top:return out
    roi=out[top:bottom,left:right]
    original=roi.copy()
    window_poly=np.rint(window_quad-[left,top]).astype(np.int32)
    target_poly=np.rint(target_quad-[left,top]).astype(np.int32)
    window_mask=np.zeros(roi.shape[:2],dtype=np.uint8)
    target_mask=np.zeros_like(window_mask)
    cv2.fillConvexPoly(window_mask,window_poly,255,lineType=cv2.LINE_AA)
    cv2.fillConvexPoly(target_mask,target_poly,255,lineType=cv2.LINE_AA)
    target_mask=cv2.bitwise_and(target_mask,window_mask)
    if np.count_nonzero(target_mask)<20:return out
    # Compute visual context independently and restore the actual target.
    softened=(cv2.GaussianBlur(original,(0,0),max(.01,blur_px))
              if blur_px>0 else original)
    muted=np.uint8(np.clip(softened.astype(np.float32)*(1-dim_opacity),0,255))
    inactive=cv2.subtract(window_mask,target_mask).astype(np.float32)[:,:,None]/255.
    roi[:]=np.uint8(np.clip(original.astype(np.float32)*(1-inactive)
                  +muted.astype(np.float32)*inactive,0,255))
    # Contact elevation: a soft 7px-offset shadow outside the sharp target.
    shifted=np.float32(target_poly)+[0,7]
    shadow_mask=np.zeros_like(window_mask)
    cv2.fillConvexPoly(shadow_mask,shifted.astype(np.int32),255)
    shadow=cv2.GaussianBlur(shadow_mask,(0,0),11).astype(np.float32)/255.
    exclusion=(255-target_mask).astype(np.float32)/255.
    shadow=(shadow*exclusion*window_mask.astype(np.float32)/255.*.27)[:,:,None]
    roi[:]=np.uint8(np.clip(roi.astype(np.float32)*(1-shadow),0,255))
    # 1-pixel antialiased specular rim follows transformed target geometry.
    cv2.polylines(roi,[target_poly],True,(249,236,216),1,cv2.LINE_AA)
    return out


def cursor_glyph_clear_of_text(left:int,top:int,width:int,height:int,
                               label_quad:np.ndarray)->tuple[int,int]:
    """Keep the drawn pointer off actual DOM text, not the recorded click."""
    lx=float(np.min(label_quad[:,0]));rx=float(np.max(label_quad[:,0]))
    ty=float(np.min(label_quad[:,1]));by=float(np.max(label_quad[:,1]))
    if left+width<=lx-4 or left>=rx+4 or top+height<=ty-4 or top>=by+4:
        return left,top
    right=round(rx+5)
    # The pointer normally clears a short word by moving to its right.
    return (right,top) if right-left<=2*width else (left,round(by+5))


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
    backdrop_style:str='obsidian-grain'
    brand_primary:str|None=None
    brand_accent:str|None=None
    enable_stage_optics:bool=False
    optics_seed:int=20261116
    enable_studio_floor:bool=False
    floor_reflection_intensity:float=.25

    def __post_init__(self):
        if (self.width,self.height)!=(MASTER_WIDTH,MASTER_HEIGHT):
            raise ValueError('Production stage is fixed to 1920x1080')
        if self.backdrop_style not in STYLES:
            raise ValueError('Invalid procedural stage style')
        for color in (self.brand_primary,self.brand_accent):
            if color is not None and (not isinstance(color,str) or
                len(color)!=7 or not color.startswith('#') or
                any(c not in '0123456789abcdef' for c in color[1:])):
                raise ValueError('Studio brand colors must be canonical #rrggbb')
        if not isinstance(self.optics_seed,int) or not 0<=self.optics_seed<2**31:
            raise ValueError('Optical grain seed must be a bounded integer')
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
               tilt:tuple[float,float]=(0.,0.),glow:float=0.,
               perspective_px:float=1820.,
               spotlight:dict|None=None,
               diff_reveal:dict|None=None,
                foreground:dict|None=None,
               frame_index:int=0)->np.ndarray:
        """Outer composition: ambient -> 3D window -> final SVG pointer.

        tilt and glow are deterministic frame-indexed inputs. The source
        website array is never modified.
        """
        if website_frame.shape!=(self.window_h,self.window_w,3):
            raise ValueError('Source must be resized to the root window before wrapping')
        if not 0.<=glow<=1.:raise ValueError('RMS-driven glow must be normalized 0..1')
        base,alpha,ambient=_stage_base(
            self.backdrop_style,self.brand_primary,self.brand_accent)
        flat=base.copy()
        x,y,w,h=self.window
        region=flat[y:y+h,x:x+w]
        region[:]=np.uint8(np.clip(
            region.astype(np.float32)*(1-alpha)+website_frame.astype(np.float32)*alpha,0,255))
        if abs(tilt[0])+abs(tilt[1])>1e-5:
            homography=window_homography(x,y,w,h,*tilt,focal=perspective_px)
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
            extra=_ambient_pulse_field(self.brand_primary,self.brand_accent)
            # Glow must never overpower or re-color the content.
            # Modulate outside the transformed window only.
            area=cv2.warpPerspective(_tilt_mask()[:,:,0],
                     window_homography(x,y,w,h,*tilt,focal=perspective_px),
                     (self.width,self.height))[:,:,None] if (
                      abs(tilt[0])+abs(tilt[1])>1e-5) else _tilt_mask()
            output=np.uint8(np.clip(output.astype(np.float32)+
                  extra.astype(np.float32)*(glow*.68)*(1-area),0,255))
        if self.enable_studio_floor:
            _studio_floor(output,website_frame,tilt,self.floor_reflection_intensity,perspective_px)
        # Filled by the actual H60 composite; optics must not construct a
        # second, rectangular modal silhouette at sharp corners.
        rounded_modal_coverage=(np.zeros(output.shape[:2],dtype=np.uint8)
                                if self.enable_stage_optics else None)
        rim_color,spectral_weights=brand_light_parameters(
            self.brand_primary,self.brand_accent)
        if spotlight and spotlight.get('active') and spotlight.get('box'):
            if foreground is not None and foreground.get('source') is not None:
                output=focus_background_plane(output,self.window,tilt,perspective_px,
                    min(6.,float(spotlight.get('blurPx',6.))),
                    float(spotlight.get('dimOpacity',.25)))
                output=composite_elevated_modal(output,foreground['source'],
                    foreground['box'],self.window,
                    float(spotlight['factor']),float(spotlight['dx']),
                    float(spotlight['dy']),tilt,perspective_px,
                    radius_css=float(foreground.get('radiusCss',0.)),
                    coverage_out=rounded_modal_coverage,
                    rim_color=rim_color)
            else:
                # No verified modal-free plate: exact Phase 2 single-plane fallback.
                output=apply_spotlight_focus(
                    output,spotlight['box'],self.window,
                    float(spotlight['factor']),float(spotlight['dx']),
                    float(spotlight['dy']),tilt,perspective_px,
                    min(6.,float(spotlight.get('blurPx',6.))),
                    float(spotlight.get('dimOpacity',.25)))
        if self.enable_stage_optics:
            # Protect exact projected H0 and H60 rectangles; optical
            # sampling is applied only to the stage/shadow/floor and to
            # the exterior modal rim, never to genuine website pixels.
            src=np.float32([[[x,y],[x+w,y],[x+w,y+h],[x,y+h]]])
            H0=window_homography(x,y,w,h,*tilt,focal=perspective_px)
            window_quad=cv2.perspectiveTransform(src,H0)[0]
            # Only project chromatic dispersion when an authentic H60
            # layer has actually been composited, using its rounded alpha.
            modal_alpha=(rounded_modal_coverage if
                         rounded_modal_coverage is not None and
                         np.any(rounded_modal_coverage) else None)
            output=apply_stage_optics(output,window_quad,frame_index,
                     seed=self.optics_seed,modal_coverage=modal_alpha,
                     spectral_weights=spectral_weights)
        if cinematic_cursor is not None:
            cinematic_cursor(output)
        if diff_reveal and diff_reveal.get('progress',0)>0:
            from code_diff_reveal import peel_browser_frame
            group=_tilt_mask()[:,:,0]
            if abs(tilt[0])+abs(tilt[1])>1e-5:
                group=cv2.warpPerspective(group,
                    window_homography(x,y,w,h,*tilt,focal=perspective_px),
                    (self.width,self.height),flags=cv2.INTER_LINEAR)
            output=peel_browser_frame(output,ambient,diff_reveal['commit'],
                     float(diff_reveal['progress']),group)
        return output


class CinematicCursor:
    """Sole visible film pointer, linked to the verified Spring2D trace."""
    def __init__(self,stage:CinematicStage,events:list[dict],
                 start_ms:float,style:str='ink',scale:float=.56):
        if not .35<=scale<=1:raise ValueError('Cursor scale out of bounds')
        if style not in ('ink','outline'):raise ValueError('Unsupported cursor style')
        self.stage,self.events,self.start_ms,self.style,self.scale=(
            stage,events,start_ms,style,scale)
        from cursor_plane_motion import CursorPlaneGlide
        self._plane_glide=CursorPlaneGlide()

    def draw(self,output:np.ndarray,position:tuple[float,float]|None,
             t:float,source_factor:float,shift_x:float,shift_y:float,
              tilt:tuple[float,float]=(0.,0.),focal:float=1820.,
              foreground_box:dict|None=None,
              protected_text_box:dict|None=None)->None:
        from cinematic_presentation_v13 import _blend,click_ring_frames
        from reference_cursor_v15 import load_cursor,press_scale
        if position is None:return
        ox,oy=self.stage.window[:2]
        homography=(window_homography(*self.stage.window,*tilt,focal=focal)
                    if abs(tilt[0])+abs(tilt[1])>1e-5 else None)
        lifted_homography=(window_homography(*self.stage.window,*tilt,
                            focal=focal,z=60.) if foreground_box is not None else None)
        def on_foreground(px:float,py:float)->bool:
            b=foreground_box
            return bool(b and b['x']<=px<=b['x']+b['width']
                        and b['y']<=py<=b['y']+b['height'])
        def point(px:float,py:float,lifted:bool=False)->tuple[int,int]:
            H=lifted_homography if lifted and lifted_homography is not None else homography
            if H is not None: px,py=map_pointer(H,px,py)
            return round(px),round(py)
        # Click ripple under pointer, tied to actual pointerdown timestamp.
        rings=click_ring_frames()
        for ev in self.events:
            if ev['type']!='pointerdown' or ev.get('x') is None:continue
            age=t-(ev['t']-self.start_ms)/1000.
            if not 0<=age<.33:continue
            px,py=point(ox+shift_x+ev['x']*source_factor,
                        oy+shift_y+ev['y']*source_factor,
                        on_foreground(ev['x'],ev['y']))
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
        px=ox+shift_x+position[0]*source_factor
        py=oy+shift_y+position[1]*source_factor
        background_x,background_y=point(px,py)
        foreground_x,foreground_y=point(px,py,lifted=True)
        # Crossing the modal edge used to jump instantly between H0/H60,
        # moving the pointer ~17px in one frame in the Brimble proof.
        # Transition ONLY the rendered hotspot, never the real input event.
        lift=self._plane_glide.sample(
            t,on_foreground(position[0],position[1]))
        x=round(background_x+(foreground_x-background_x)*lift)
        y=round(background_y+(foreground_y-background_y)*lift)
        glyph_x=round(x-image.hotspot[0]*scale)
        glyph_y=round(y-image.hotspot[1]*scale)
        if protected_text_box is not None:
            b=protected_text_box
            lifted=on_foreground(b['x']+b['width']/2,b['y']+b['height']/2)
            quad=projected_target_quad(
                b,self.stage.window,source_factor,shift_x,shift_y,*tilt,
                perspective_px=focal,z=60. if lifted else 0.)
            # Only the cursor art can move; click ripple stays source-true.
            glyph_x,glyph_y=cursor_glyph_clear_of_text(
                glyph_x,glyph_y,art.shape[1],art.shape[0],quad)
        _blend(output,art,glyph_x,glyph_y)
