"""Action-led auto-zoom: move the cursor, then move the camera.

This planner turns recorded cursor telemetry, verified click targets and real
UI-state timestamps into a deterministic 60fps camera track. No action means
no zoom. Modal framing is tied to the observed DOM appearance, not anticipation
of a state that the viewer cannot see.

The spring integrator is the exact solver in spring_motion.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from bisect import bisect_right
from math import hypot
from typing import Sequence

from spring_motion import Spring1D, Spring2D


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    width: float
    height: float

    @property
    def center(self) -> tuple[float, float]:
        return (self.x + self.width/2., self.y + self.height/2.)


def first_intentional_motion(
    samples: Sequence[Sequence[float]],
    *,
    click_time: float,
    window: float = 2.0,
    min_speed: float = 100.0,
    target: tuple[float,float] | None = None,
) -> float:
    """First sustained motion heading toward the known click.

    We ignore idle/timestamp gaps; samples must precede the actual click.
    Do not start a zoom just because a click will happen later.
    """
    if len(samples) < 2:
        raise ValueError("Cursor telemetry is required for auto-zoom")
    eligible = [
        (a,b) for a,b in zip(samples,samples[1:])
        if b[0] <= click_time and b[0] >= click_time-window
           and b[0] > a[0]
    ]
    for a,b in eligible:
        speed = hypot(b[1]-a[1],b[2]-a[2])/(b[0]-a[0])
        # Idle movement or travel away from a click must not trigger a zoom.
        closes_on_click=(target is None or
           hypot(b[1]-target[0],b[2]-target[1])<
           hypot(a[1]-target[0],a[2]-target[1])-1.0)
        if speed >= min_speed and closes_on_click:
            return float(b[0])
    raise ValueError("No intentional cursor movement before click; use manual zoom")


def build_action_camera(
    *, fps: int,
    duration: float,
    pointer_samples: Sequence[Sequence[float]],
    click_time: float,
    click_rect: Rect,
    modal_open_time: float,
    picker_rect: Rect,
    copied_time: float,
    result_rect: Rect,
    viewport: tuple[int,int] = (1600,900),
    zoom_action: float = 1.32,
    zoom_picker: float = 1.62,
    zoom_result: float = 1.66,
    stiffness_zoom: float = 125.0,
    stiffness_pan: float = 160.0,
) -> tuple[list[tuple[float,float,float]], dict]:
    """Compute motion from recorded cursor movement and actual UI state changes.

    Approach zoom is coupled to distance travelled toward a *real* click.
    After a modal opens, the actual element bounds take over the framing.
    Pointer tracking inside a dialog uses a dead zone to prevent twitching.
    """
    if fps <= 0 or duration <= 0:
        raise ValueError("fps and duration must be positive")
    if not (0 < click_time < modal_open_time < copied_time < duration):
        raise ValueError("UI state timestamps must follow the recorded action")
    if len(pointer_samples)<2:
        raise ValueError("recorded pointer samples are required")
    if any(pointer_samples[i+1][0] <= pointer_samples[i][0]
           for i in range(len(pointer_samples)-1)):
        raise ValueError("Pointer timestamps must be strictly increasing")
    if min(zoom_action,zoom_picker,zoom_result)<1:
        raise ValueError("Auto-zoom factors must be >= 1")

    vwidth,vheight = viewport
    center=(vwidth/2.,vheight/2.)
    move_start=first_intentional_motion(
        pointer_samples,click_time=click_time,target=click_rect.center)
    times=[float(x[0]) for x in pointer_samples]
    begin_x=float(pointer_samples[0][1])
    begin_y=float(pointer_samples[0][2])
    # If cursor has an idle record at time zero, it is the real start point.
    # Prefer the sample immediately before first intentional motion.
    j=max(0,bisect_right(times,move_start)-2)
    begin_x=float(pointer_samples[j][1])
    begin_y=float(pointer_samples[j][2])
    target_x,target_y=click_rect.center
    dx,dy=target_x-begin_x,target_y-begin_y
    distance_squared=dx*dx+dy*dy
    if distance_squared<1:
        raise ValueError("Cursor did not travel meaningfully to the target")

    max_picker_zoom = min(zoom_picker,
       vwidth/(picker_rect.width+130.),
       vheight/(picker_rect.height+90.))
    max_result_zoom = min(zoom_result,
       vwidth/(result_rect.width+110.),
       vheight/(result_rect.height+65.))
    # Framing safety is more important than making everything huge.
    # At current source/output aspect this yields 1.62 and ~1.66.
    if min(max_picker_zoom,max_result_zoom)<=1:
        raise ValueError("Dialog too large for a safe auto-zoom")
    scale=Spring1D(1.0,stiffness=stiffness_zoom,
                   damping=2*(stiffness_zoom**0.5))
    pan=Spring2D(*center,stiffness=stiffness_pan,
                 damping=2*(stiffness_pan**0.5))
    dt=1/fps
    out=[]
    cue_times={}
    max_progress=0.0

    def sample_cursor(t:float)->tuple[float,float]:
        k=max(0,bisect_right(times,t)-1)
        if k>=len(pointer_samples)-1:
            return float(pointer_samples[-1][1]),float(pointer_samples[-1][2])
        a,b=pointer_samples[k],pointer_samples[k+1]
        u=max(0.,min(1.,(t-a[0])/(b[0]-a[0])))
        return float(a[1]+u*(b[1]-a[1])),float(a[2]+u*(b[2]-a[2]))

    for index in range(round(duration*fps)):
        t=index/fps
        if t<move_start:
            wanted=(1.0,*center)
        elif t<modal_open_time:
            x,y=sample_cursor(t)
            projection=((x-begin_x)*dx+(y-begin_y)*dy)/distance_squared
            max_progress=max(max_progress,max(0.,min(1.,projection)))
            # No zoom until the cursor is measurably on its way.
            p=max(0.,min(1.,(max_progress-.08)/.92))
            # Reserve context around the clicked button. Avoid placing it
            # dead center and cropping the surrounding workflow.
            biased_x=center[0]+.40*(target_x-center[0])
            biased_y=center[1]+.18*(target_y-center[1])
            wanted=(1+(zoom_action-1)*p,center[0]+(biased_x-center[0])*p,
                    center[1]+(biased_y-center[1])*p)
        elif t<copied_time:
            focusx,focusy=picker_rect.center
            # Only follow the cursor once it actually enters the dialog.
            # Dead zone lets small cursor adjustments happen without
            # making the whole screen chase the pointer.
            px,py=sample_cursor(t)
            if picker_rect.x-12<=px<=picker_rect.x+picker_rect.width+12 and (
                picker_rect.y-12<=py<=picker_rect.y+picker_rect.height+12):
                delta=px-focusx
                if abs(delta)>145:
                    focusx+=max(-24.,min(24.,(abs(delta)-145)*.15*(1 if delta>0 else -1)))
            wanted=(max_picker_zoom,focusx,focusy)
        else:
            focusx,focusy=result_rect.center
            wanted=(max_result_zoom,focusx,focusy)
        if index:
            scale.step(wanted[0],dt)
            pan.step(wanted[1],wanted[2],dt)
        out.append((scale.position,pan.x.position,pan.y.position))

    cue_times={
      "first_pointer_motion":move_start,
      "first_click":click_time,
      "modal_visible":modal_open_time,
      "copied_state_visible":copied_time,
      "focus_policy":"cursor-led approach → verified modal region → verified result region",
      "zoom_targets":[zoom_action,round(max_picker_zoom,4),round(max_result_zoom,4)],
      "recorded_click_center":[round(target_x,2),round(target_y,2)],
    }
    # For very unusual aspect ratios, a proposed zoom that cuts out
    # the verified result rectangle must be rejected by the visual gate.
    return out,cue_times
