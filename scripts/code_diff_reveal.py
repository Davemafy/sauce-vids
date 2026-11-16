"""Evidence-backed floating diff reveal, composited in the final 3D stage.

No model-written source: every highlighted line is a sanitized Git patch hunk.
The editor remains in the same 1920x1080 frame and source-time clock.
"""
from __future__ import annotations
from functools import lru_cache
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from git_evidence import validate_commit

W,H=600,632
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
UIFONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

@lru_cache(maxsize=24)
def _card(sha:str,file:str,title:str,lines:tuple[str,...])->np.ndarray:
    image=Image.new('RGBA',(W,H),(0,0,0,0));draw=ImageDraw.Draw(image)
    draw.rounded_rectangle((5,5,W-6,H-6),radius=18,
       fill=(13,17,25,252),outline=(97,111,127,200),width=2)
    font=ImageFont.truetype(FONT,18)
    fine=ImageFont.truetype(UIFONT,16)
    draw.rounded_rectangle((5,5,W-6,96),radius=18,fill=(25,30,39,255))
    draw.rectangle((5,76,W-6,96),fill=(25,30,39,255))
    draw.text((28,19),'COMMIT  '+sha[:10],fill=(159,178,195),font=fine)
    draw.text((28,50),title[:49],fill=(234,239,246),font=fine)
    draw.text((28,121),file[:43],fill=(142,173,221),font=font)
    y=176
    for line in lines[:16]:
        if y+25>H-18:break
        if line.startswith('+'):color=(117,218,159);bg=(19,54,42,148)
        elif line.startswith('-'):color=(244,141,144);bg=(67,27,36,148)
        elif line.startswith('@@'):color=(132,163,243);bg=(27,37,70,160)
        else:color=(181,192,209);bg=None
        if bg:draw.rounded_rectangle((16,y-2,W-18,y+24),radius=3,fill=bg)
        draw.text((27,y),line[:48].replace('\t','  '),fill=color,font=font)
        y+=28
    return cv2.cvtColor(np.asarray(image),cv2.COLOR_RGBA2BGRA)


def compose_diff(frame:np.ndarray,commit:dict,progress:float)->np.ndarray:
    if frame.shape!=(1080,1920,3):raise ValueError('Diff reveal requires 1080p stage')
    if not np.isfinite(progress) or progress<0 or progress>1:
        raise ValueError('Invalid frame-driven reveal progress')
    if progress<=0:return frame
    valid=validate_commit(commit)
    asset=_card(valid['sha'],valid['file'],valid['title'],tuple(valid['lines']))
    # The dark code panel is a physical floating card emerging from behind
    # the pivoting browser edge; it is never laid over source UI text in capture.
    x=1300+round((1-progress)*16)
    y=195+round((1-progress)*18)
    region=frame[y:y+H,x:x+W]
    if region.shape[:2]!=(H,W):return frame
    alpha=(asset[:,:,3:4].astype(np.float32)/255.)*(.98*progress)
    region[:]=np.uint8(np.clip(region.astype(np.float32)*(1-alpha)+
                 asset[:,:,:3].astype(np.float32)*alpha,0,255))
    # A tight shading line hints at the screen panel peeling across the reveal.
    shadow_x=max(0,x-11)
    cv2.line(frame,(shadow_x,y+16),(shadow_x,y+H-16),(8,10,14),5,cv2.LINE_AA)
    return frame



def peel_browser_frame(frame:np.ndarray,background:np.ndarray,commit:dict,
                       progress:float,window_mask:np.ndarray)->np.ndarray:
    """Lens-space peel: browser, cursor and callouts transform as one surface.

    The HTML/browser image is never regenerated. A perspective-tilted stage
    group shrinks and slides to reveal genuine code to the right. The same
    affine transform moves the actual overlaid pointer with the film.
    """
    if not 0<=progress<=1 or not np.isfinite(progress):
        raise ValueError('Invalid peel clock')
    if progress<=0:return frame
    if window_mask.shape!=(1080,1920) or frame.shape!=(1080,1920,3):
        raise ValueError('Invalid cinema mask')
    dst=background.copy()
    compose_diff(dst,commit,progress)
    scale=1.-.19*progress
    transform=np.float32([[scale,0,-61.*progress],
                          [0,scale,101.*progress]])
    moved=cv2.warpAffine(frame,transform,(1920,1080),
              flags=cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_CONSTANT)
    mask=cv2.dilate(window_mask,np.ones((18,18),np.uint8))
    mask=cv2.warpAffine(mask,transform,(1920,1080),
              flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
    norm=255. if float(np.max(mask))>1.01 else 1.
    alpha=cv2.GaussianBlur(mask.astype(np.float32)/norm,(0,0),2.4)[:,:,None]
    dst[:]=np.uint8(np.clip(dst.astype(np.float32)*(1-alpha)+
                            moved.astype(np.float32)*alpha,0,255))
    return dst
