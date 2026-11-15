"""Deterministic continuous-position spring motion for Sauce's 60fps compositor.

The state transition is the exact solution of the mass-spring-damper ODE for
a held target over one fixed frame. It avoids explicit Euler instability and
preserves velocity across target changes. Use critical damping for cameras;
cursor may use slight underdamping where the actual click position is safe.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import cos, exp, isfinite, sin, sqrt
from bisect import bisect_right
from typing import Sequence


@dataclass
class Spring1D:
    position: float
    velocity: float = 0.0
    stiffness: float = 144.0
    damping: float = 24.0

    def __post_init__(self) -> None:
        if not all(isfinite(x) for x in
                   (self.position,self.velocity,self.stiffness,self.damping)):
            raise ValueError("Spring parameters must be finite")
        if self.stiffness <= 0 or self.damping < 0:
            raise ValueError("Require stiffness > 0 and damping >= 0")

    def step(self, target: float, dt: float) -> float:
        """Exact damped oscillator step with target constant across dt."""
        if not isfinite(target) or not isfinite(dt) or dt < 0:
            raise ValueError("Invalid spring target or timestep")
        if dt == 0:
            return self.position
        w = sqrt(self.stiffness)
        zeta = self.damping / (2.0 * w)
        y = self.position-target
        v = self.velocity
        if abs(zeta-1.0) < 1e-8:
            decay = exp(-w*dt)
            c = v+w*y
            next_y = (y+c*dt)*decay
            next_v = (v-w*c*dt)*decay
        elif zeta < 1.0:
            a = zeta*w
            wd = w*sqrt(1.0-zeta*zeta)
            decay = exp(-a*dt)
            ct,st = cos(wd*dt), sin(wd*dt)
            next_y = decay*(y*ct+(v+a*y)/wd*st)
            next_v = decay*(v*ct-(a*v+w*w*y)/wd*st)
        else:
            root = sqrt(zeta*zeta-1.0)
            r1,r2 = -w*(zeta-root),-w*(zeta+root)
            coeff1 = (v-r2*y)/(r1-r2)
            coeff2 = y-coeff1
            e1,e2=exp(r1*dt),exp(r2*dt)
            next_y = coeff1*e1+coeff2*e2
            next_v = r1*coeff1*e1+r2*coeff2*e2
        self.position=target+next_y
        self.velocity=next_v
        return self.position


class Spring2D:
    def __init__(self,x:float,y:float,stiffness:float=576.,damping:float=48.):
        self.x=Spring1D(x,stiffness=stiffness,damping=damping)
        self.y=Spring1D(y,stiffness=stiffness,damping=damping)

    def step(self, target_x:float,target_y:float,dt:float)->tuple[float,float]:
        return self.x.step(target_x,dt),self.y.step(target_y,dt)


def camera_track(
    *, fps:int, duration:float,
    anchors:Sequence[tuple[float,float,float,float]],
    stiffness_zoom:float=100., damping_zoom:float=20.,
    stiffness_pan:float=144., damping_pan:float=24.,
) -> list[tuple[float,float,float]]:
    """Return frame-indexed (scale, focus_x, focus_y), never seek-integrate.

    Anchors are (time, scale, focus_x, focus_y) and encode *targets*.
    The output is precomputed once and can be accessed in arbitrary order.
    """
    if fps<=0 or duration<=0 or not anchors or anchors[0][0]!=0:
        raise ValueError("Need positive fps/duration and initial anchor at t=0")
    if any(t1>=t2 for t1,t2 in
           zip((a[0] for a in anchors), (a[0] for a in anchors[1:]))):
        raise ValueError("Anchor times must increase strictly")
    if any(a[1]<=0 for a in anchors):
        raise ValueError("Camera scale must be positive")
    scale=Spring1D(anchors[0][1],stiffness=stiffness_zoom,damping=damping_zoom)
    pan=Spring2D(anchors[0][2],anchors[0][3],stiffness_pan,damping_pan)
    times=[a[0] for a in anchors]
    out=[]
    dt=1.0/fps
    for i in range(round(duration*fps)):
        t=i/fps
        target=anchors[max(0,bisect_right(times,t)-1)]
        # Frame zero remains the exact chosen starting composition.
        if i:
            scale.step(target[1],dt)
            pan.step(target[2],target[3],dt)
        out.append((scale.position,pan.x.position,pan.y.position))
    return out


def cursor_track(
    *, samples:Sequence[Sequence[float]],fps:int,duration:float,
    stiffness:float=784., damping:float=56.,
) -> list[tuple[float,float]]:
    """Filter the REAL, time-stamped cursor path without inventing actions.

    Samples must remain in original recorded time. Never smooth the recorded
    click event timestamps or move them. Verify endpoint accuracy separately.
    """
    if fps<=0 or duration<=0 or len(samples)<2:
        raise ValueError("Cursor requires at least two recorded samples")
    if any(len(v)<3 for v in samples):
        raise ValueError("Samples must contain (timestamp,x,y)")
    if any(samples[i+1][0]<=samples[i][0] for i in range(len(samples)-1)):
        # Duplicate timings can be emitted by telemetry. Do not silently
        # corrupt click alignment; deduplicate explicitly upstream.
        raise ValueError("Sample timestamps must be strictly increasing")
    timestamps=[float(row[0]) for row in samples]
    spring=Spring2D(float(samples[0][1]),float(samples[0][2]),stiffness,damping)
    out=[]
    dt=1.0/fps
    for i in range(round(duration*fps)):
        t=i/fps
        j=max(0,bisect_right(timestamps,t)-1)
        if j>=len(samples)-1:
            x,y=float(samples[-1][1]),float(samples[-1][2])
        else:
            a,b=samples[j],samples[j+1]
            q=max(0.,min(1.,(t-a[0])/(b[0]-a[0])))
            x=a[1]+q*(b[1]-a[1])
            y=a[2]+q*(b[2]-a[2])
        if i:spring.step(float(x),float(y),dt)
        out.append((spring.x.position,spring.y.position))
    return out
