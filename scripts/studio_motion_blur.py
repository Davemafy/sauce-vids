"""Small directional Gaussian shutter in 2D source-frame coordinates.

This runs ONLY when the trace time map accelerates and there is camera
or scroll displacement. No synthetic blur over static UI text.
"""
from __future__ import annotations
import numpy as np,cv2
from math import hypot


def directional_blur(frame:np.ndarray,vx:float,vy:float,speed:float)->np.ndarray:
    if frame.ndim!=3 or frame.shape[2]!=3:raise ValueError('Expected BGR frame')
    amount=max(0.,min(1.,(speed-1.5)/2.5))
    length=hypot(vx,vy)
    if amount<=0 or length<.75:return frame
    radius=min(6.,amount*3.6+min(2.4,length*.20))
    # Source-frame displacement is expressed per output frame. Increase
    # blur-shutter displacement with the accelerated playback multiplier
    # while preserving the direction measured from actual camera/scroll.
    multiplier=max(0.,speed-1.)
    dx=vx/length*min(6.,radius*multiplier)
    dy=vy/length*min(6.,radius*multiplier)
    h,w=frame.shape[:2]
    xs=np.arange(w,dtype=np.float32)[None,:]
    ys=np.arange(h,dtype=np.float32)[:,None]
    accum=np.zeros_like(frame,dtype=np.float32)
    # Symmetric 5-tap temporal shutter aligned with actual movement vector.
    weights=(.08,.24,.36,.24,.08)
    for offset,weight in zip((-2,-1,0,1,2),weights):
        if offset==0:
            layer=frame
        else:
            matrix=np.float32([[1,0,dx*offset/2],[0,1,dy*offset/2]])
            layer=cv2.warpAffine(frame,matrix,(w,h),flags=cv2.INTER_LINEAR,
                                borderMode=cv2.BORDER_REPLICATE)
        accum+=layer.astype(np.float32)*weight
    return np.uint8(np.clip(accum,0,255))
