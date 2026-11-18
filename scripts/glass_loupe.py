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
    dissolve: bool = True

    def pointer(self, time):
        index = bisect_right(self.points, time, key=lambda point: point[0])
        if index == 0:
            return self.points[0][1:]
        if index == len(self.points):
            return self.points[-1][1:]
        t0, x0, y0 = self.points[index-1]
        t1, x1, y1 = self.points[index]
        u = (time-t0)/(t1-t0)
        # Monotone Hermite interpolation preserves samples and removes velocity
        # jumps without overshooting a slider that stops or reverses.
        def tangent(i, axis):
            if i == 0 or i == len(self.points)-1:
                return 0.
            a,b,c = self.points[i-1:i+2]
            left = (b[axis]-a[axis])/(b[0]-a[0])
            right = (c[axis]-b[axis])/(c[0]-b[0])
            return 2*left*right/(left+right) if left*right>0 else 0.

        blend = u*u*(3-2*u)
        outgoing = u*(1-u)**2*(t1-t0)
        incoming = -u*u*(1-u)*(t1-t0)
        return tuple(a+(b-a)*blend+outgoing*tangent(index-1,axis)+incoming*tangent(index,axis)
                     for axis,a,b in ((1,x0,x1),(2,y0,y1)))


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
        dissolve = duration-end >= .45
        shots.append(LoupeShot(start,changed,released,end if dissolve else duration,
                               points,result,dissolve))
    return shots


def apply_loupe(stage, source, transform, shot, time):
    """Sample original capture pixels directly. Color separation stays at the rim."""
    height,width = stage.shape[:2]
    entry = smooth5((time-shot.start)/.34)
    exit_strength = smooth5((shot.end-time)/.48) if shot.dissolve else 1.
    strength = min(entry,exit_strength)
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
    center_x += (width*.50-center_x)*reveal*.82
    center_y += (height*.72-center_y)*reveal*.65
    settled_radius = height*(.39+.29*reveal)
    radius = settled_radius*(.30+.70*strength)
    center_x = float(np.clip(center_x,radius*.72,width-radius*.72))
    center_y = float(np.clip(center_y,radius*.66,height-radius*.66))
    result_half_span = math.hypot((right-left)*sx,(bottom-top)*sy)/2
    fitted_zoom = min(1.78, .76*settled_radius/max(1.,result_half_span))
    magnification = 1.78+reveal*(fitted_zoom-1.78)
    magnification = max(1.05,magnification)
    magnification = 1.+(magnification-1.)*strength
    # Lead the resulting value slightly left of the optical center so
    # the neighboring plan remains in context, with space beneath the price.
    focus_x += reveal*(x+w/2+(center_x-width*.37)/(sx*magnification)-focus_x)
    focus_y += reveal*(y+h/2+(center_y-height*.65)/(sy*magnification)-focus_y)
    if strength > 0:
        x0,y0=max(0,math.floor(center_x-radius-18)),max(0,math.floor(center_y-radius-18))
        x1,y1=min(width,math.ceil(center_x+radius+18)),min(height,math.ceil(center_y+radius+18))
        yy,xx=np.mgrid[y0:y1,x0:x1].astype(np.float32)
        dx,dy=xx-center_x,yy-center_y
        radial=np.hypot(dx,dy)/radius
        optical=np.clip((radial-.72)/.28,0,1)
        bend=1.+.17*optical**3
        mx=focus_x+dx*bend/(sx*magnification)
        my=focus_y+dy*bend/(sy*magnification)
        inside=(mx>=0)&(my>=0)&(mx<source.shape[1]-1)&(my<source.shape[0]-1)
        alpha=np.clip((1.-radial)*radius/3.,0,1)*strength*inside
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
    # Match the tip to the same inverse radial map used for the footage.
    # During the optical blend we favor the visible magnified interaction.
    dx = (pointer_x-focus_x)*sx*magnification
    dy = (pointer_y-focus_y)*sy*magnification
    distance = math.hypot(dx,dy)
    lo,hi = 0.,distance
    for _ in range(14):
        r = (lo+hi)/2
        edge = max(0.,min(1.,(r/radius-.72)/.28))
        if r*(1.+.17*edge**3) < distance:
            lo = r
        else:
            hi = r
    radial_scale = (lo+hi)/(2*distance) if distance else 1.
    base_x = pointer_x*sx+transform[0,2]
    base_y = pointer_y*sy+transform[1,2]
    tip_x = base_x+(center_x+dx*radial_scale-base_x)*strength
    tip_y = base_y+(center_y+dy*radial_scale-base_y)*strength
    # High contrast white body and black keyline survive a phone-size downscale.
    # Subpixel coordinates keep the cursor from snapping to integer positions.
    glyph = np.float32([[0,0],[0,36],[10,27],[18,44],[25,40],[17,24],[33,24]])
    glyph *= .86*height/1080
    glyph += (tip_x,tip_y)
    polygon = np.int32(np.rint(glyph*16))
    cv2.polylines(stage,[polygon],True,(8,9,10),max(2,round(height/270)),cv2.LINE_AA,shift=4)
    cv2.fillPoly(stage,[polygon],(248,248,248),cv2.LINE_AA,shift=4)
    return stage
