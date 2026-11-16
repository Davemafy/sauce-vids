"""Seekable motion primitives for the flagship's optional cursor label.

The actual screen cursor uses its own click-locked track. A floating label,
when editorially justified, uses this independent 120/18/1 spring and may lag
without ever affecting the recorded click. All coordinates are per output frame.
"""
from __future__ import annotations
import math
from collections.abc import Sequence
from spring_motion import Spring2D


def badge_spring_track(cursor:Sequence[tuple[float,float]],fps:int=60,
                       offset:tuple[float,float]=(38.,-54.),
                       stiffness:float=120.,damping:float=18.,mass:float=1.
                      )->list[tuple[float,float]]:
    if fps!=60 or mass<=0 or stiffness<=0 or damping<0 or not cursor:
        raise ValueError('Badge physics requires a bounded 60fps cursor track')
    if not all(math.isfinite(v) for xy in cursor for v in xy):
        raise ValueError('Invalid tracked source coordinates')
    spring=Spring2D(cursor[0][0]+offset[0],cursor[0][1]+offset[1],
                    stiffness=stiffness/mass,damping=damping/mass)
    out=[]
    for x,y in cursor:
        out.append(tuple(round(v,6) for v in spring.step(
                       x+offset[0],y+offset[1],1/60)))
    return out


def shutter_velocity(cursor:Sequence[tuple[float,float]],fps:int=60,
                     shutter_angle:float=180.)->list[tuple[float,float]]:
    """Motion vector over a half-frame shutter, not a duplicated pointer.

    Vectors are metadata. The film compositor may use these for directional
    stroke convolution, but never to smear static source typography.
    """
    if fps!=60 or not 0<shutter_angle<=360:raise ValueError('Invalid shutter')
    exposure=shutter_angle/360/fps
    return [(0.,0.)] + [((b[0]-a[0])*fps*exposure,
                         (b[1]-a[1])*fps*exposure)
                        for a,b in zip(cursor,cursor[1:])]


def cursor_shutter_art(art,shutter_vector:tuple[float,float],
                       contact_locked:bool=False):
    """Real centered exposure integration on pointer pixels ONLY.

    No frame blending, no UI filtering and no offset of the cursor hotspot.
    Five premultiplied-alpha taps create a single lightly stretched silhouette
    instead of separate opaque trails or a doubled oval. A capped exposure of
    2.4px protects the approved vector's antialiasing and click visibility.
    """
    import cv2,numpy as np
    if (not isinstance(art,np.ndarray) or art.ndim!=3 or
        art.shape[2]!=4 or art.dtype!=np.uint8):
        raise ValueError('Shutter requires an RGBA pointer')
    dx,dy=shutter_vector
    if not math.isfinite(dx) or not math.isfinite(dy):
        raise ValueError('Invalid cursor motion vector')
    magnitude=math.hypot(dx,dy)
    if contact_locked or magnitude<1.15:return art
    scale=min(1.,2.4/magnitude)
    dx*=scale;dy*=scale
    alpha=art[:,:,3:4].astype(np.float32)/255.
    premul=art[:,:,:3].astype(np.float32)*alpha
    a_acc=np.zeros_like(alpha);rgb_acc=np.zeros_like(premul)
    for t in (-.50,-.25,0.,.25,.50):
        matrix=np.float32([[1,0,dx*t],[0,1,dy*t]])
        shifted_a=cv2.warpAffine(alpha[:,:,0],matrix,(art.shape[1],art.shape[0]),
                                flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
        shifted_rgb=cv2.warpAffine(premul,matrix,(art.shape[1],art.shape[0]),
                                  flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
        a_acc[:,:,0]+=shifted_a*.2
        rgb_acc+=shifted_rgb*.2
    out=np.empty_like(art)
    out[:,:,:3]=np.uint8(np.clip(rgb_acc/np.maximum(a_acc,1.e-5),0,255))
    out[:,:,3]=np.uint8(np.clip(a_acc[:,:,0]*255,0,255))
    return out
