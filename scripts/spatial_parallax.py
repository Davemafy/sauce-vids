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
                      focal:float=FOCAL_LENGTH,max_degrees:float=6.,z:float=0.)->np.ndarray:
    if not math.isfinite(focal) or focal<=600 or focal>3000:
        raise ValueError('Invalid 3D perspective focal distance')
    if (not math.isfinite(max_degrees) or max_degrees<0 or max_degrees>6 or
        not math.isfinite(rotate_x) or not math.isfinite(rotate_y) or
        max(abs(rotate_x),abs(rotate_y))>max_degrees+1e-8):
        raise ValueError('3D window tilt exceeds permitted preset bounds')
    if not math.isfinite(z) or z<0 or z>60:
        raise ValueError('Invalid depth plane; expected 0..60px')
    ax,ay=math.radians(rotate_x),math.radians(rotate_y)
    cx,cy=x+w/2.,y+h/2.
    src=np.float32([[x,y],[x+w,y],[x+w,y+h],[x,y+h]])
    dst=[]
    for px,py in src:
        X,Y=px-cx,py-cy
        # Y-axis followed by X-axis rotations.
        X1=X*math.cos(ay)+z*math.sin(ay)
        Z1=-X*math.sin(ay)+z*math.cos(ay)
        Y2=Y*math.cos(ax)-Z1*math.sin(ax)
        Z2=Y*math.sin(ax)+Z1*math.cos(ax)
        scale=focal/(focal-Z2)
        dst.append((cx+X1*scale,cy+Y2*scale))
    return cv2.getPerspectiveTransform(src,np.float32(dst))


def map_pointer(matrix:np.ndarray,x:float,y:float)->tuple[float,float]:
    point=np.array([[[x,y]]],dtype=np.float32)
    transformed=cv2.perspectiveTransform(point,matrix)[0,0]
    return float(transformed[0]),float(transformed[1])


def projected_target_quad(box:dict,window:tuple[int,int,int,int],
                          source_factor:float,offset_x:float,offset_y:float,
                          rotate_x:float,rotate_y:float,
                          perspective_px:float=FOCAL_LENGTH,z:float=0.)->np.ndarray:
    """Use the SAME window homography for screenshot, rim, and cursor.

    Input box is evidence-backed CSS viewport coordinates; source_factor
    includes deviceScaleFactor and the per-frame CameraPose scale.
    Returns four corners in 1920x1080 final-compositor pixel coordinates.
    """
    values=[box.get(k) for k in ('x','y','width','height')]
    if (any(not isinstance(v,(int,float)) or not math.isfinite(v) for v in values)
        or values[2]<=1 or values[3]<=1 or
        not all(math.isfinite(v) for v in (source_factor,offset_x,offset_y))
        or source_factor<=0):
        raise ValueError('Invalid evidence-backed spotlight box')
    ox,oy,_,_=window
    x,y,w,h=values
    coords=np.float32([[
      [ox+offset_x+x*source_factor,oy+offset_y+y*source_factor],
      [ox+offset_x+(x+w)*source_factor,oy+offset_y+y*source_factor],
      [ox+offset_x+(x+w)*source_factor,oy+offset_y+(y+h)*source_factor],
      [ox+offset_x+x*source_factor,oy+offset_y+(y+h)*source_factor]]])
    matrix=window_homography(*window,rotate_x,rotate_y,focal=perspective_px,z=z)
    return cv2.perspectiveTransform(coords,matrix)[0]


def evidence_attention_events(session_dir,session:dict)->list[dict]:
    """Offline visual saliency + Farneback flow from SHA-verified capture states.

    Returns only source-clock CSS gaze coordinates, confidence and normalized
    motion: no screenshot pixels or page text enter the TypeScript director.
    """
    from pathlib import Path
    import hashlib
    folder=Path(session_dir)/'states'
    width,height=session['page']['viewport']
    observations=[]
    previous=None
    for state in session['states'][:80]:
        file=folder/state['file']
        raw=file.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=state['sha256']:
            raise ValueError('Saliency requires verified state image hash')
        img=cv2.imdecode(np.frombuffer(raw,dtype=np.uint8),cv2.IMREAD_GRAYSCALE)
        if img is None:raise ValueError('Invalid visual evidence image')
        small=cv2.resize(img,(256,144),interpolation=cv2.INTER_AREA)
        if previous is not None:
            flow=cv2.calcOpticalFlowFarneback(previous,small,None,
                .5,3,15,3,5,1.2,0)
            movement=cv2.magnitude(flow[:,:,0],flow[:,:,1]);
            change=cv2.absdiff(previous,small).astype(np.float32)/255.
            gx=cv2.Sobel(small,cv2.CV_32F,1,0,ksize=3)
            gy=cv2.Sobel(small,cv2.CV_32F,0,1,ksize=3)
            contours=cv2.magnitude(gx,gy)
            contours=contours/(np.percentile(contours,95)+1e-6)
            # Important dynamic content beats high-contrast unchanged text.
            salience=(np.minimum(change*3,1)*(.6+.4*np.minimum(contours,1)) +
                .24*np.minimum(movement/6.,1))
            salience=cv2.GaussianBlur(salience,(0,0),5.)
            _,peak,_,location=cv2.minMaxLoc(salience)
            # Do not pretend an unchanging screenshot provides gaze evidence.
            if peak>.085 and float(np.mean(change))>.006:
                x=float((location[0]+.5)*width/256)
                y=float((location[1]+.5)*height/144)
                flow_strength=min(1.,float(movement[location[1],location[0]])/6.)
                confidence=min(1.,max(0.,peak))
                observations.append({'type':'visual-attention',
                    't':float(state['at_ms']),'x':round(x,3),'y':round(y,3),
                    'attention':{'score':round(confidence,4),
                                 'flow':round(flow_strength,4)}})
        previous=small
    return observations
