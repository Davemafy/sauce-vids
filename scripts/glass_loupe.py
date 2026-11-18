"""Evidence-driven glass loupe for cursorless browser captures."""
from dataclasses import dataclass
import math
from bisect import bisect_right

import cv2
import numpy as np

from autozoom_event_planner import smooth5


@dataclass(frozen=True)
class LoupeShot:
    start: float
    changed: float
    released: float
    end: float
    points: tuple
    result: tuple

    def pointer(self, time):
        index = bisect_right(self.points, time, key=lambda point: point[0])
        if index == 0:
            return self.points[0][1:]
        if index == len(self.points):
            return self.points[-1][1:]
        t0, x0, y0 = self.points[index-1]
        t1, x1, y1 = self.points[index]
        u = (time-t0)/(t1-t0)
        return x0+(x1-x0)*u, y0+(y1-y0)*u


def _rect(raw, width, height):
    x,y,w,h = (float(raw[k]) for k in ("x","y","width","height"))
    if not (0 <= x < x+w <= width and 0 <= y < y+h <= height and
            all(math.isfinite(v) for v in (x,y,w,h))):
        raise ValueError("Invalid visible rectangle")
    return x,y,w,h


def plan_loupe(manifest, width, height, duration):
    if manifest.get("cursorless") is not True:
        return []
    shots = []
    for event in manifest.get("events", []):
        evidence = event.get("evidence")
        if event.get("kind") != "slider_change" or not isinstance(evidence,str) or not evidence.strip():
            continue
        try:
            start, changed, released = (float(event[k]) for k in ("start","t","end"))
            if not (0 <= start <= changed <= released < duration and released-start <= 5):
                continue
            end = min(duration,released+2.85)
            if end-released < .65 or (shots and start < shots[-1].end):
                continue
            x,y,w,h = _rect(event["targetRect"],width,height)
            result = _rect(event["resultRect"],width,height)
            points = tuple(tuple(float(p[k]) for k in ("t","x","y")) for p in event["pointer_samples"])
            if (len(points)<2 or
                any(not (start <= t <= released and x-2 <= px <= x+w+2 and y-2 <= py <= y+h+2)
                    for t,px,py in points) or
                any(a[0]>=b[0] for a,b in zip(points,points[1:]))):
                continue
        except (KeyError,TypeError,ValueError,OverflowError):
            continue
        shots.append(LoupeShot(start,changed,released,end,points,result))
    return shots


def apply_loupe(stage, source, transform, shot, time):
    """Sample original capture pixels directly. Color separation stays at the rim."""
    height,width = stage.shape[:2]
    strength = min(smooth5((time-shot.start)/.34),smooth5((shot.end-time)/.32))
    pointer_x,pointer_y = shot.pointer(time)
    x,y,w,h = shot.result
    reveal = smooth5((time-shot.changed)/.38)
    # Keep the live control as the anchor, then include the entire changed value group.
    left,right = min(pointer_x,x),max(pointer_x,x+w)
    top,bottom = min(pointer_y,y),max(pointer_y,y+h)
    focus_x = pointer_x+((left+right)/2-pointer_x)*reveal
    focus_y = pointer_y+((top+bottom)/2-pointer_y)*reveal
    sx,sy = float(transform[0,0]),float(transform[1,1])
    center_x = focus_x*sx+transform[0,2]
    center_y = focus_y*sy+transform[1,2]
    radius = height*(.39+.17*reveal)*(.15+.85*strength)
    center_x = float(np.clip(center_x,radius*.72,width-radius*.72))
    center_y = float(np.clip(center_y,radius*.66,height-radius*.66))
    magnification = 1.78+reveal*(min(1.88, .78*radius/max(1.,math.hypot((right-left)*sx,(bottom-top)*sy)/2))-1.78)
    magnification = max(1.05,magnification)
    magnification = 1.+(magnification-1.)*strength
    if strength > 0:
        x0,y0=max(0,math.floor(center_x-radius-18)),max(0,math.floor(center_y-radius-18))
        x1,y1=min(width,math.ceil(center_x+radius+18)),min(height,math.ceil(center_y+radius+18))
        yy,xx=np.mgrid[y0:y1,x0:x1].astype(np.float32)
        dx,dy=xx-center_x,yy-center_y
        radial=np.hypot(dx,dy)/radius
        optical=np.clip((radial-.72)/.28,0,1)
        bend=1.+.24*optical**3
        mx=focus_x+dx*bend/(sx*magnification)
        my=focus_y+dy*bend/(sy*magnification)
        inside=(mx>=0)&(my>=0)&(mx<source.shape[1]-1)&(my<source.shape[0]-1)
        alpha=np.clip((1.-radial)*radius/2.,0,1)*strength*inside
        sample=cv2.remap(source,mx,my,cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
        # The two color channels split in opposite directions at the outer edge.
        fringe=optical**4 * 4.0
        for channel,sign in ((0,1),(2,-1)):
            sample[:,:,channel]=cv2.remap(source[:,:,channel],mx+sign*dx/radius*fringe,
                                          my+sign*dy/radius*fringe,cv2.INTER_LINEAR,
                                          borderMode=cv2.BORDER_REPLICATE)
        roi=stage[y0:y1,x0:x1]
        shadow=np.clip(1.-np.abs(radial-1.)*radius/15.,0,1)*.32*strength
        out=roi*(1.-shadow[:,:,None])*(1.-alpha[:,:,None])+sample*alpha[:,:,None]
        rim=np.clip(1.-np.abs(radial-.996)*radius/3.,0,1)*strength
        rim*=.22+.57*np.clip(-dy/radius,0,1)
        roi[:]=np.rint(out*(1.-rim[:,:,None])+np.float32([216,220,227])*rim[:,:,None])
    # Cursorless sources get one sharp cursor projected with the loupe center.
    if time <= shot.released+.22:
        base_x=pointer_x*sx+transform[0,2]
        base_y=pointer_y*sy+transform[1,2]
        tip_x=base_x+(center_x+(pointer_x-focus_x)*sx*magnification-base_x)*strength
        tip_y=base_y+(center_y+(pointer_y-focus_y)*sy*magnification-base_y)*strength
        pointer=np.int32([[0,0],[2,25],[9,18],[15,28],[20,25],[14,15],[24,14]])
        pointer+=np.int32([round(tip_x),round(tip_y)])
        cv2.fillPoly(stage,[pointer],(16,17,19),cv2.LINE_AA)
        cv2.polylines(stage,[pointer],True,(250,250,250),2,cv2.LINE_AA)
    return stage
