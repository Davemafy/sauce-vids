"""Flagship film composition: restrained product photography, not decorative optics.

The verified UI remains untouched. Only outside-window stage pixels and an
accurate, thin browser frame are generated. Same homography transforms cursor.
"""
from __future__ import annotations
from functools import lru_cache
from typing import Callable
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageFont
from spatial_parallax import window_homography

W,H=1920,1080
# 1644px capture on 1920px stage preserves more of the native 2x source.
WINDOW=(138,78,1644,924)

@lru_cache(maxsize=1)
def _matte():
    x,y,w,h=WINDOW
    image=Image.new('RGB',(W,H),(22,24,25))
    # Very restrained studio illumination: near-neutral, not colored bloom.
    # Soft physically oriented contact shadow beneath the same source window.
    shadow=Image.new('L',(W,H),0)
    d=ImageDraw.Draw(shadow)
    d.rounded_rectangle((x-10,y-3,x+w+10,y+h+28),radius=21,fill=178)
    image.paste((0,0,0),(0,0),shadow.filter(ImageFilter.GaussianBlur(42)))
    frame=ImageDraw.Draw(image)
    frame.rounded_rectangle((x-3,y-3,x+w+2,y+h+2),radius=18,
                            fill=(12,14,15),outline=(67,70,71),width=2)
    # Small chrome-edge highlights, not a fake browser toolbar.
    frame.line((x+16,y-3,x+w-16,y-3),fill=(92,95,95),width=1)
    mask=Image.new('L',(w,h),0)
    ImageDraw.Draw(mask).rounded_rectangle((0,0,w-1,h-1),radius=15,fill=255)
    # Non-UI stage labelling avoids competing with the actual product.
    label=ImageDraw.Draw(image)
    from PIL import ImageFont
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
    label.text((x,28),'BRIMBLE  /  CONNECT YOUR AGENT',font=font,fill=(152,155,152))
    label.text((x+w-178,H-39),'MADE WITH SAUCE',font=font,fill=(143,147,145))
    return np.asarray(image,dtype=np.uint8)[:,:,::-1].copy(),np.asarray(mask,dtype=np.float32)[:,:,None]/255.

class FlagshipStage:
    width=W;height=H
    window=WINDOW
    background_hex='#161819'
    enable_studio_floor=False
    floor_reflection_intensity=0.

    def render(self,website_frame:np.ndarray,
               cinematic_cursor:Callable[[np.ndarray],None]|None=None,
               tilt:tuple[float,float]=(0.,0.),glow:float=0.,
               perspective_px:float=2400.,spotlight:dict|None=None,
               diff_reveal:dict|None=None,
               editorial_caption:str|None=None)->np.ndarray:
        x,y,w,h=self.window
        if website_frame.shape!=(h,w,3):raise ValueError('Wrong source dimensions for flagship')
        if not np.isfinite(tilt).all() or max(abs(a) for a in tilt)>2.5:
            raise ValueError('Flagship tilt outside editorial bounds')
        base,mask=_matte()
        out=base.copy()
        roi=out[y:y+h,x:x+w]
        roi[:]=np.uint8(np.clip(roi.astype(np.float32)*(1-mask)+
                   website_frame.astype(np.float32)*mask,0,255))
        if abs(tilt[0])+abs(tilt[1])>1.e-4:
            # Transform only the photographed browser; do not warp the room.
            Hm=window_homography(x,y,w,h,*tilt,focal=perspective_px)
            group=np.zeros_like(out)
            group[y:y+h,x:x+w]=out[y:y+h,x:x+w]
            moved=cv2.warpPerspective(group,Hm,(W,H),flags=cv2.INTER_LANCZOS4)
            bounds=np.zeros((H,W),np.uint8)
            bounds[y:y+h,x:x+w]=np.uint8(mask[:,:,0]*255)
            bounds=cv2.warpPerspective(bounds,Hm,(W,H),flags=cv2.INTER_LINEAR)
            amt=bounds.astype(np.float32)[:,:,None]/255
            out=np.uint8(np.clip(base.astype(np.float32)*(1-amt)+moved.astype(np.float32)*amt,0,255))
        # No vignette, spotlight, floor caustics, RGB splitting or gradients.
        if editorial_caption:
            if editorial_caption not in ('01  OPEN CONNECTOR','02  CHOOSE CODEX',
                                         '03  COMMAND COPIED'):
                raise ValueError('Only source-verified editorial chapters are permitted')
            from functools import lru_cache
            out[1025:1055,138:620]=_caption(out[1025:1055,138:620],editorial_caption)
        if cinematic_cursor is not None:cinematic_cursor(out)
        return out


@lru_cache(maxsize=3)
def _caption_overlay(label:str)->np.ndarray:
    p=Image.new('RGBA',(482,30),(0,0,0,0))
    f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',18)
    ImageDraw.Draw(p).text((0,2),label,fill=(177,181,178,255),font=f)
    return np.asarray(p,dtype=np.uint8).copy()

def _caption(roi:np.ndarray,label:str)->np.ndarray:
    rgba=_caption_overlay(label)
    a=rgba[:,:,3:4].astype(np.float32)/255.
    return np.uint8(np.clip(roi.astype(np.float32)*(1-a)+
                   rgba[:,:,:3][:,:,::-1].astype(np.float32)*a,0,255))
