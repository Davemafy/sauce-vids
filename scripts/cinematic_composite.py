"""Subtle editorial depth separation outside a REAL captured modal.

The recorded app owns the UI and its transition. We do not redraw, scale
or fabricate the dialog. This effect affects only pixels behind its verified
bounding rectangle and can be disabled per export.
"""
from __future__ import annotations
import cv2
import numpy as np


def background_focus(frame:np.ndarray,box:dict|None,dpr:int,
                     mix:float=.35)->np.ndarray:
    if box is None or mix<=0:return frame
    if not 0<=mix<=.7:raise ValueError('Backdrop blur mix out of range')
    h,w=frame.shape[:2]
    px=lambda n:int(round(n*dpr))
    x0=max(0,px(box['x']-15))
    y0=max(0,px(box['y']-15))
    x1=min(w,px(box['x']+box['width']+15))
    y1=min(h,px(box['y']+box['height']+15))
    if x1<=x0 or y1<=y0:return frame
    sigma=max(2.,3.5*dpr)
    blurred=cv2.GaussianBlur(frame,(0,0),sigmaX=sigma)
    backdrop=cv2.addWeighted(frame,1-mix,blurred,mix,0)
    # A softly feathered protection mask retains the actual dialog,
    # border, text and shadow. The interior rectangle stays pixel-identical.
    padding=max(3,px(12))
    cx0=min(w,max(0,x0+padding))
    cy0=min(h,max(0,y0+padding))
    cx1=min(w,max(cx0,x1-padding))
    cy1=min(h,max(cy0,y1-padding))
    protection=np.zeros((h,w),dtype=np.uint8)
    cv2.rectangle(protection,(cx0,cy0),(cx1,cy1),255,-1)
    feather=cv2.GaussianBlur(protection,(0,0),sigmaX=5*dpr)
    alpha=feather.astype(np.float32)[:,:,None]/255.
    out=np.uint8(np.clip(backdrop.astype(np.float32)*(1-alpha)+
        frame.astype(np.float32)*alpha,0,255))
    # Hard-inside protection guarantees legibility even on small modals.
    out[cy0+padding:cy1-padding,cx0+padding:cx1-padding]=frame[cy0+padding:cy1-padding,cx0+padding:cx1-padding]
    return out
