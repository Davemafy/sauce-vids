"""Evidence-driven glass loupe for cursorless browser captures."""
from dataclasses import dataclass, fields
from numbers import Real
import math
from bisect import bisect_right

from recorded_pointer import draw_loupe_pointer

import cv2
import numpy as np

from autozoom_event_planner import smooth5


@dataclass(frozen=True)
class LoupeStyle:
    entry_delay: float = .10
    entry_duration: float = .31
    expand_duration: float = .34
    expand_delay: float = .12
    exit_delay: float = .24
    exit_duration: float = .47
    small_radius: float = .40
    expanded_radius: float = .71
    expanded_center_x: float = .50
    expanded_center_y: float = .72
    payoff_y: float = .65

    @classmethod
    def from_plan(cls, data):
        if not isinstance(data, dict) or set(data) - {f.name for f in fields(cls)}:
            raise ValueError("Unknown glass loupe control")
        for name, value in data.items():
            low, high = ((.20, .85) if "radius" in name else
                         (.15, .85) if "center" in name or name == "payoff_y" else
                         (.08, 1.5) if name.endswith("duration") else (0., 1.))
            if isinstance(value, bool) or not isinstance(value, Real) or not low <= value <= high:
                raise ValueError(f"Invalid glass loupe {name}")
        style = cls(**data)
        if style.small_radius > style.expanded_radius:
            raise ValueError("Expanded loupe radius must be at least the entry radius")
        return style


@dataclass(frozen=True)
class LoupeShot:
    start: float
    changed: float
    released: float
    end: float
    points: tuple
    result: tuple
    dissolve: bool = True
    reframe: float | None = None

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
                any(not (start <= t <= duration and 0 <= px < width and 0 <= py < height)
                    for t,px,py in points) or
                any(not (x-2 <= px <= x+w+2 and y-2 <= py <= y+h+2)
                    for t,px,py in points if t <= released) or
                sum(t <= released for t,_,_ in points)<2 or
                any(a[0]>=b[0] for a,b in zip(points,points[1:]))):
                continue
        except (KeyError,TypeError,ValueError,OverflowError):
            continue
        dissolve = event.get("fade_at_end") is True or duration-end >= .45
        # A sustained drag can become the reframing cue before the final
        # result, but only when the DOM later verifies that same interaction.
        first_x = points[0][1]
        reframe = next((t for t,px,_ in points
                        if .75<=t-start and t<=released and abs(px-first_x)>=w*.06),changed)
        shots.append(LoupeShot(start,changed,released,end if dissolve else duration,
                               points,result,dissolve,min(reframe,changed)))
    return shots


def _edge_bend(radius_fraction):
    skirt = np.clip((radius_fraction-.57)/.43,0.,1.)
    # A rolling lip steepens the warp into the glass, then widens
    # the last few source pixels as they approach the polished edge.
    lip = np.clip((radius_fraction-.88)/.12,0.,1.)
    return 1.+.075*skirt**2+.46*skirt**5-.23*lip**2


def apply_loupe(stage, source, transform, shot, time, style=LoupeStyle()):
    """Sample original capture pixels directly. Color separation stays at the rim."""
    height,width = stage.shape[:2]
    entry_phase = (time-shot.start-style.entry_delay)/style.entry_duration
    entry = smooth5(entry_phase)
    exit_strength = smooth5((shot.end-time-style.exit_delay)/style.exit_duration) if shot.dissolve else 1.
    strength = min(entry,exit_strength)
    pointer_x,pointer_y = shot.pointer(time)
    anchor_x,anchor_y = shot.pointer(min(time,shot.released))
    x,y,w,h = shot.result
    reframe = shot.reframe if shot.reframe is not None else shot.changed
    reframe_phase = (time-reframe)/style.expand_duration
    if reframe < shot.changed:
        reframe_phase -= style.expand_delay/style.expand_duration
    reveal = smooth5(reframe_phase)
    # Keep the live control as the anchor, then include the entire changed value group.
    left,right = min(anchor_x,x),max(anchor_x,x+w)
    top,bottom = min(anchor_y,y),max(anchor_y,y+h)
    focus_x = anchor_x+((left+right)/2-anchor_x)*reveal
    focus_y = anchor_y+((top+bottom)/2-anchor_y)*reveal
    sx,sy = float(transform[0,0]),float(transform[1,1])
    center_x = focus_x*sx+transform[0,2]
    center_y = focus_y*sy+transform[1,2]
    center_x += width*.03*(1.-reveal)
    center_x += (width*style.expanded_center_x-center_x)*reveal*.82
    center_y += (height*style.expanded_center_y-center_y)*reveal*.82
    settled_radius = height*(style.small_radius+(style.expanded_radius-style.small_radius)*reveal)
    radius = settled_radius*(.36+.64*strength)
    center_x = float(np.clip(center_x,radius*.72,width-radius*.72))
    center_y = float(np.clip(center_y,radius*.66,height-radius*.66))
    center_y += reveal*max(0.,radius-center_y)
    result_half_span = math.hypot((right-left)*sx,(bottom-top)*sy)/2
    fitted_zoom = min(1.76, .76*settled_radius/max(1.,result_half_span))
    magnification = 1.98+reveal*(fitted_zoom-1.98)
    magnification = max(1.05,magnification)
    magnification = 1.+(magnification-1.)*strength
    # Lead the resulting value slightly left of the optical center so
    # the neighboring plan remains in context, with space beneath the price.
    focus_x += (1.-reveal)*radius*.30/(sx*magnification)
    focus_x += reveal*(x+w/2+(center_x-width*.37)/(sx*magnification)-focus_x)
    focus_y += reveal*(y+h/2+(center_y-height*style.payoff_y)/(sy*magnification)-focus_y)
    if strength > 0:
        x0,y0=max(0,math.floor(center_x-radius-18)),max(0,math.floor(center_y-radius-18))
        x1,y1=min(width,math.ceil(center_x+radius+18)),min(height,math.ceil(center_y+radius+18))
        yy,xx=np.mgrid[y0:y1,x0:x1].astype(np.float32)
        dx,dy=xx-center_x,yy-center_y
        radial=np.hypot(dx,dy)/radius
        optical=np.clip((radial-.70)/.30,0,1)
        bend=_edge_bend(radial)
        mx=focus_x+dx*bend/(sx*magnification)
        my=focus_y+dy*bend/(sy*magnification)
        inside=(mx>=0)&(my>=0)&(mx<source.shape[1]-1)&(my<source.shape[0]-1)
        alpha=np.clip((1.-radial)*radius/3.4,0,1)*strength
        # Source pixels stay sharp in the center. Outside that page, extend
        # the refraction into the captured composition so the bezel and
        # scenery bend through the same glass instead of ending at a clip.
        screen_x = mx*sx+transform[0,2]
        screen_y = my*sy+transform[1,2]
        sample=cv2.remap(source,mx,my,cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
        # The two color channels split in opposite directions at the outer edge.
        fringe = optical**3 * (radius*.020)/sx
        for channel,sign in ((0,1),(2,-1)):
            sample[:,:,channel]=cv2.remap(source[:,:,channel],mx+sign*dx/radius*fringe,
                                          my+sign*dy/radius*fringe,cv2.INTER_LINEAR,
                                          borderMode=cv2.BORDER_REPLICATE)
        # Short radial shutter streaks appear during the optical movement.
        # Stable frames use only the original sharp sample.
        phase = max(0.,1.-abs(2.*entry_phase-1.),1.-abs(2.*reframe_phase-1.))
        if shot.dissolve:
            exit_phase = (shot.end-time-style.exit_delay)/style.exit_duration
            phase = max(phase,1.-abs(2.*exit_phase-1.))
        if phase > .03:
            spread = .034*phase**2
            mx0,my0 = mx-focus_x,my-focus_y
            early = cv2.remap(source,mx-mx0*spread,my-my0*spread,cv2.INTER_LINEAR,
                              borderMode=cv2.BORDER_REPLICATE)
            late = cv2.remap(source,mx+mx0*spread,my+my0*spread,cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_REPLICATE)
            sample = cv2.addWeighted(sample,.56,cv2.addWeighted(early,.5,late,.5,0),.44,0)
        if np.any(~inside & (radial < 1.)):
            surround = cv2.remap(stage,screen_x.astype(np.float32),screen_y.astype(np.float32),
                                  cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
            for channel, direction in ((0,1),(2,-1)):
                offset = fringe * direction
                surround[:,:,channel] = cv2.remap(
                    stage[:,:,channel],(screen_x+dx/radius*offset*sx).astype(np.float32),
                    (screen_y+dy/radius*offset*sy).astype(np.float32),
                    cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
            sample = np.where(inside[:,:,None],sample,surround)
        roi=stage[y0:y1,x0:x1]
        shadow=np.clip(1.-np.abs(radial-1.)*radius/15.,0,1)*.32*strength
        out=roi*(1.-shadow[:,:,None])*(1.-alpha[:,:,None])+sample*alpha[:,:,None]
        upper_light = np.clip((-dy-.24*dx)/radius,0,1)
        rim = np.clip(1.-np.abs(radial-.997)*radius/4.,0,1)*strength
        rim *= .12+.68*upper_light**1.7
        # The broader, dim inner reflection rolls off into the glass.
        sheen = np.exp(-((radial-.979)*radius/11.)**2)*upper_light**3*.13*strength
        lower_reflection = np.clip((dy+.45*dx)/radius,0,1)**2
        lower_reflection *= np.clip(1.-radial,0,1)**.42 * alpha
        out = out+np.float32([17,24,32])*lower_reflection[:,:,None]
        out = out+(255.-out)*sheen[:,:,None]
        roi[:]=np.uint8(np.clip(np.rint(out*(1.-rim[:,:,None])+np.float32([211,226,229])*rim[:,:,None]),0,255))
    # Match the tip to the same inverse radial map used for the footage.
    # During the optical blend we favor the visible magnified interaction.
    dx = (pointer_x-focus_x)*sx*magnification
    dy = (pointer_y-focus_y)*sy*magnification
    distance = math.hypot(dx,dy)
    lo,hi = 0.,distance
    for _ in range(14):
        r = (lo+hi)/2
        if r*_edge_bend(r/radius) < distance:
            lo = r
        else:
            hi = r
    radial_scale = (lo+hi)/(2*distance) if distance else 1.
    base_x = pointer_x*sx+transform[0,2]
    base_y = pointer_y*sy+transform[1,2]
    tip_x = base_x+(center_x+dx*radial_scale-base_x)*strength
    tip_y = base_y+(center_y+dy*radial_scale-base_y)*strength
    draw_loupe_pointer(stage,tip_x,tip_y,scale=1.+strength*(.28-.14*reveal))
    return stage
