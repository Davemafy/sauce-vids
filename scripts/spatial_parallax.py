"""Cursor-velocity-driven 3D inertial parallax for Sauce's window.

All motion derives from the saved Spring2D cursor samples. Perspective
is a true projected 3D rotation via a 3x3 homography. Pointer hotspots
are transformed by the same matrix as the window.
"""
from __future__ import annotations
import math
from typing import Sequence
import cv2
import numpy as np
from spring_motion import Spring2D

MAX_DEGREES=2.5
DEFAULT_GAIN=1.35
FOCAL_LENGTH=1820.

def inertial_tilt_track(cursor:Sequence[tuple[float,float]]|None,
                        fps:int=60,gain:float=DEFAULT_GAIN
                       )->list[tuple[float,float]]:
    if cursor is None:return []
    if fps<=0 or gain<0 or gain>MAX_DEGREES:raise ValueError('Invalid tilt track arguments')
    spring=Spring2D(0.,0.,stiffness=88.,damping=19.)
    out=[]
    for i,pos in enumerate(cursor):
        if i:
            before=cursor[i-1]
            vx=(pos[0]-before[0])*fps
            vy=(pos[1]-before[1])*fps
            # Saturated optical response to real pointer momentum.
            target_x=-gain*math.tanh(vy/1300.)
            target_y= gain*math.tanh(vx/1300.)
            rx,ry=spring.step(target_x,target_y,1./fps)
        else:rx,ry=0.,0.
        out.append((max(-MAX_DEGREES,min(MAX_DEGREES,rx)),
                    max(-MAX_DEGREES,min(MAX_DEGREES,ry))))
    return out


def window_homography(x:int,y:int,w:int,h:int,
                      rotate_x:float,rotate_y:float,
                      focal:float=FOCAL_LENGTH)->np.ndarray:
    if max(abs(rotate_x),abs(rotate_y))>MAX_DEGREES+1e-8:
        raise ValueError('3D window tilt exceeds 2.5 degrees')
    ax,ay=math.radians(rotate_x),math.radians(rotate_y)
    cx,cy=x+w/2.,y+h/2.
    src=np.float32([[x,y],[x+w,y],[x+w,y+h],[x,y+h]])
    dst=[]
    for px,py in src:
        X,Y=px-cx,py-cy
        # Y-axis followed by X-axis rotations.
        X1=X*math.cos(ay)
        Z1=-X*math.sin(ay)
        Y2=Y*math.cos(ax)-Z1*math.sin(ax)
        Z2=Y*math.sin(ax)+Z1*math.cos(ax)
        scale=focal/(focal-Z2)
        dst.append((cx+X1*scale,cy+Y2*scale))
    return cv2.getPerspectiveTransform(src,np.float32(dst))


def map_pointer(matrix:np.ndarray,x:float,y:float)->tuple[float,float]:
    point=np.array([[[x,y]]],dtype=np.float32)
    transformed=cv2.perspectiveTransform(point,matrix)[0,0]
    return float(transformed[0]),float(transformed[1])
