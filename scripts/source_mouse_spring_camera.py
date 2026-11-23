"""Source-true spring camera: a bounded, causal follow of the *recorded* mouse.

A camera move is not an invented pointer move. This sampler only repositions
the real video plane, using genuine pointer samples from a hash-bound manifest.
Its critical damping creates the quick, quiet settlement measured from the
owner's 2026-11-23 Google Sheets reference, without endless mouse chasing.
"""
from __future__ import annotations

from dataclasses import dataclass
import bisect
import math

import numpy as np


@dataclass(frozen=True)
class RecordedFollow:
    fps: float
    points: tuple[tuple[float, float], ...]
    max_displacement: float
    source_sample_count: int

    def offset(self, seconds: float) -> tuple[float, float]:
        if not math.isfinite(seconds):
            raise ValueError("Non-finite film time")
        frame=max(0.,min(float(seconds)*self.fps,len(self.points)-1))
        first=int(math.floor(frame));last=min(first+1,len(self.points)-1)
        f=frame-first
        x0,y0=self.points[first];x1,y1=self.points[last]
        return x0*(1-f)+x1*f,y0*(1-f)+y1*f


def _number(value, name, low, high) -> float:
    if type(value) not in (float,int) or not math.isfinite(value) or not low<=value<=high:
        raise ValueError(f"motion.follow.{name} outside [{low}, {high}]")
    return float(value)


def _fade(t: float, left: float, right: float, ramp: float) -> float:
    if t<left or t>right:
        return 0.
    enter=min(1.,max(0.,(t-left)/ramp))
    exit=min(1.,max(0.,(right-t)/ramp))
    # C2 smooth gate at each event boundary. Camera never anticipates a
    # future pointer position; the gate merely authorizes observed movement.
    def smooth(x):
        return x*x*x*(x*(x*6-15)+10)
    return smooth(enter)*smooth(exit)


def _critically_damped_step(position: np.ndarray, velocity: np.ndarray,
                             target: np.ndarray, omega: float, dt: float):
    """Exact constant-target solution for one sample of a 2nd-order spring."""
    delta=position-target
    decay=math.exp(-omega*dt)
    combined=velocity+omega*delta
    future_position=target+(delta+combined*dt)*decay
    future_velocity=(velocity-omega*combined*dt)*decay
    return future_position,future_velocity


def build_follow(manifest: dict, source_size: tuple[int,int], duration: float,
                 fps: float, cfg: dict) -> RecordedFollow:
    allowed={"mode","eventIndices","responseSeconds","strength",
             "deadzone","maxOffset","beforeSeconds","afterSeconds"}
    if not isinstance(cfg,dict) or set(cfg)-allowed:
        raise ValueError("Unknown recorded mouse follow controls")
    if cfg.get("mode")!="source-cursor-spring":
        raise ValueError("Follow must use real source-cursor-spring")
    strength=_number(cfg.get("strength",.22),"strength",.04,.45)
    deadzone=_number(cfg.get("deadzone",.10),"deadzone",.03,.23)
    max_offset=_number(cfg.get("maxOffset",.055),"maxOffset",.008,.075)
    response=_number(cfg.get("responseSeconds",.39),"responseSeconds",.18,.95)
    before=_number(cfg.get("beforeSeconds",.75),"beforeSeconds",.25,1.15)
    after=_number(cfg.get("afterSeconds",.7),"afterSeconds",.25,1.2)
    if not isinstance(manifest,dict):
        raise ValueError("Real source manifest is required")
    w,h=source_size
    if w<=0 or h<=0 or not (math.isfinite(duration) and duration>0
                            and math.isfinite(fps) and 15<=fps<=120):
        raise ValueError("Source size/frame clock invalid")
    capture=manifest.get("capture_rect",{})
    if not isinstance(capture,dict) or (
        capture.get("width")!=w or capture.get("height")!=h):
        raise ValueError("Mouse samples must share original browser pixel geometry")
    raw=manifest.get("pointer_samples")
    if not isinstance(raw,list) or len(raw)<3 or len(raw)>100000:
        raise ValueError("Cannot follow without a real sampled pointer track")
    seen=[];last=-1.
    for pt in raw:
        if not isinstance(pt,dict):
            raise ValueError("Nonobject observed pointer")
        t=_number(pt.get("t"),"source.time",0.,duration)
        x=_number(pt.get("x"),"source.x",0.,w)
        y=_number(pt.get("y"),"source.y",0.,h)
        if t<=last:
            raise ValueError("Original pointer timestamps must be strictly increasing")
        seen.append((t,x/w,y/h));last=t
    ids=cfg.get("eventIndices")
    events=manifest.get("events")
    if (not isinstance(ids,list) or not 1<=len(ids)<=12 or
        any(type(ix) is not int for ix in ids) or len(set(ids))!=len(ids) or
        not isinstance(events,list)):
        raise ValueError("Follow requires unique verified eventIndices")
    windows=[]
    for ix in ids:
        if ix<0 or ix>=len(events):
            raise ValueError("Follow event index is not in source manifest")
        e=events[ix]
        if (not isinstance(e,dict) or not isinstance(e.get("evidence"),str)
                or not e["evidence"].strip()):
            raise ValueError("Camera follow needs actual verified event")
        times=[]
        for name in ("start","end","t"):
            times.append(_number(e.get(name),f"event.{name}",0.,duration))
        start,end,confirmed=times
        if not (start<=end<=confirmed or
                (e.get("kind")=="slider_change" and start<=confirmed<=end)):
            raise ValueError("Camera follow needs source-clock-valid event")
        windows.append((max(0.,start-before),min(duration,confirmed+after)))
    windows.sort()
    # Critical damping with a finite response time. Exact per-step spring
    # integration is stable at 24/25/30/60/120 fps, independent of rendering
    # order, and cannot overshoot an idle target.
    times=[p[0] for p in seen]
    pos=np.zeros(2,dtype=np.float64);vel=np.zeros(2,dtype=np.float64)
    path=[(0.,0.)]
    delta=1./fps
    omega=4.74/response # approx 95% settle for a fixed target
    for frame in range(1,math.ceil(duration*fps)+1):
        t=min(duration,frame/fps)
        gate=max((_fade(t,a,b,.19) for a,b in windows),default=0.)
        cursor=np.zeros(2)
        if gate>0 and t>=times[0]:
            ix=bisect.bisect_right(times,t)-1
            ix=max(0,min(len(seen)-1,ix))
            px,py=seen[ix][1:]
            # Interpolate only observed adjacent samples; do NOT invent a
            # cursor trajectory across gaps in real browser observations.
            if ix+1<len(seen):
                next_t,nx,ny=seen[ix+1]
                gap=next_t-seen[ix][0]
                if gap<=.20 and next_t>t:
                    p=max(0.,min(1.,(t-seen[ix][0])/gap))
                    px=px+(nx-px)*p;py=py+(ny-py)*p
            cursor=np.array([px-.5,py-.5])
        magnitude=np.maximum(np.abs(cursor)-deadzone,0.)
        desire=-np.sign(cursor)*np.minimum(magnitude*strength,max_offset)*gate
        pos,vel=_critically_damped_step(pos,vel,desire,omega,delta)
        # Finite precision may cause tiny values beyond a bounded target.
        pos=np.clip(pos,-max_offset,max_offset)
        path.append((float(pos[0]),float(pos[1])))
    return RecordedFollow(float(fps),tuple(path),max_offset,len(seen))


def reference_ease_out(progress: float) -> float:
    """Quick zoom arrival with long quiet tail; exact normalized endpoints.

    An exponential, critically-damped distance response resembles the
    measured reference's 0.3-0.9s scale settlement. No overshoot and no
    arbitrary per-frame noise.
    """
    p=max(0.,min(1.,float(progress)))
    u=6.8*p
    decay=1.-(1.+u)*math.exp(-u)
    end=1.-7.8*math.exp(-6.8)
    return min(1.,max(0.,decay/end))
