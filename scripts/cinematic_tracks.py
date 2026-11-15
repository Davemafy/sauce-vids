"""Action-led camera planner for verified Sauce session replay.

The cursor arrives before zooming; when the real modal becomes visible the
camera moves focus from the source button to its actual DOM box. No invented
modal animation, pre-click zoom or uncontrolled camera wandering.
"""
from __future__ import annotations

import math
from bisect import bisect_right
from typing import Sequence
from spring_motion import Spring1D,Spring2D


def _css_center(rect:dict)->tuple[float,float]:
    return rect['x']+rect['width']/2., rect['y']+rect['height']/2.


def _progress(current:tuple[float,float],origin:tuple[float,float],
              target:tuple[float,float])->float:
    dx,dy=target[0]-origin[0],target[1]-origin[1]
    dist=dx*dx+dy*dy
    if dist<1:return 1.
    p=((current[0]-origin[0])*dx+(current[1]-origin[1])*dy)/dist
    return max(0.,min(1.,p))


def cinematic_camera(events:Sequence[dict],start_ms:float,
                     duration:float,fps:int,
                     viewport:tuple[int,int]=(1280,720)
                    )->tuple[list[tuple[float,float,float]],dict]:
    if fps<=0 or duration<=0:raise ValueError('Need a fixed positive fps and duration')
    if not events:raise ValueError('Auto-camera requires recorded browser events')
    w,h=viewport
    center=(w/2.,h/2.)
    downs=[e for e in events if e['type']=='pointerdown' and e.get('box')]
    if not downs:
        return [(1.,*center) for _ in range(round(fps*duration))],{
            'policy':'no-click-no-zoom','first_zoom':None}
    downs=sorted(downs,key=lambda e:e['t'])
    first=downs[0]
    origin=(first['x'],first['y'])
    # Use the first real pointer sample near the start of the *recorded*
    # approach, never a guessed offscreen point.
    motions=[e for e in events if e['type']=='pointermove' and
             e.get('x') is not None and e['t']>=start_ms]
    if not motions:raise ValueError('No pointer trajectory; no automatic zoom')
    samples=[e for e in motions if e['t']<=first['t']]
    if len(samples)<3:
        # Pre-v11 traces may contain only Playwright's teleport-to-click
        # event. Keep those sessions replayable, but NEVER manufacture
        # a cinematic approach or move the camera without supporting data.
        return [(1.,*center) for _ in range(round(fps*duration))],{
            'policy':'legacy-sparse-cursor-no-automatic-zoom',
            'first_zoom':None,'first_click_ms':round(first['t'],2)}
    first_position=(samples[0]['x'],samples[0]['y'])
    target=_css_center(first['box'])
    distance=math.dist(first_position,target)
    if distance<20:raise ValueError('Approach distance too short to infer camera movement')
    first_motion=None
    for item in samples[1:]:
        displacement=math.dist((item['x'],item['y']),first_position)
        if displacement>=max(8.,distance*.025):
            first_motion=float(item['t'])
            break
    if first_motion is None:raise ValueError('Pointer did not approach first click')
    dialogs=[e for e in events if e['type']=='dialog-visible' and
             e.get('box') and e['t']>=first['t']]
    modal=dialogs[0] if dialogs else None
    modal_center=_css_center(modal['box']) if modal else center
    second=downs[1] if len(downs)>1 else None
    # Restrict zoom to keep the ENTIRE verified dialog in frame.
    if modal:
        r=modal['box']
        max_safe=min(1.44,(w-140)/r['width'],(h-122)/r['height'])
    else:max_safe=1.30
    modal_zoom=min(1.34,max_safe)
    detail_zoom=min(1.40,max_safe)
    cursor_times=[float(e['t']) for e in motions]
    pointer_samples=[(float(e['x']),float(e['y'])) for e in motions]

    def pointer_at(ms:float)->tuple[float,float]:
        j=max(0,bisect_right(cursor_times,ms)-1)
        if j>=len(cursor_times)-1:return pointer_samples[-1]
        a,b=cursor_times[j],cursor_times[j+1]
        q=max(0.,min(1.,(ms-a)/(b-a))) if b>a else 1.
        pt1,pt2=pointer_samples[j],pointer_samples[j+1]
        return (pt1[0]+(pt2[0]-pt1[0])*q,pt1[1]+(pt2[1]-pt1[1])*q)

    scale=Spring1D(1.,stiffness=96.,damping=2*math.sqrt(96.))
    pan=Spring2D(*center,stiffness=126.,damping=2*math.sqrt(126.))
    out=[]
    first_zoom_frame=None
    for frame in range(round(fps*duration)):
        elapsed=frame/fps
        absolute_ms=start_ms+1000*elapsed
        if absolute_ms<first_motion:
            desired=(1.,*center)
        elif absolute_ms<first['t']:
            progress=_progress(pointer_at(absolute_ms),first_position,target)
            # The camera responds only once the pointer has visibly started
            # its approach. It follows the button while retaining context.
            p=max(0.,min(1.,(progress-.025)/.975))
            desired=(1+.16*p,
                     center[0]+(target[0]-center[0])*.48*p,
                     center[1]+(target[1]-center[1])*.28*p)
        elif not modal or absolute_ms<modal['t']:
            desired=(1.16,
                     center[0]+(target[0]-center[0])*.48,
                     center[1]+(target[1]-center[1])*.28)
        elif second and absolute_ms>=second['t']:
            desired=(modal_zoom,*modal_center)
        elif second and absolute_ms<second['t']:
            point=pointer_at(absolute_ms)
            second_target=_css_center(second['box'])
            # Once the pointer actually approaches the modal control,
            # gently tighten the framing. There is no unrelated zoom.
            if abs(second_target[1]-modal_center[1])>1:
                detail=max(0.,min(1.,
                    (point[1]-modal_center[1])/(second_target[1]-modal_center[1])))
            else:
                detail=0.
            desired=(modal_zoom+(detail_zoom-modal_zoom)*detail,
                     modal_center[0]+(second_target[0]-modal_center[0])*.12*detail,
                     modal_center[1]+(second_target[1]-modal_center[1])*.16*detail)
        else:
            desired=(modal_zoom,*modal_center)
        if frame:
            scale.step(desired[0],1/fps)
            pan.step(desired[1],desired[2],1/fps)
        if first_zoom_frame is None and abs(scale.position-1.)>0.0001:
            first_zoom_frame=frame
        out.append((scale.position,pan.x.position,pan.y.position))
    metadata={
        'policy':'cursor approach -> real click -> visible dialog -> verified result',
        'first_pointer_motion_ms':round(first_motion,2),
        'first_click_ms':round(first['t'],2),
        'modal_visible_ms':round(modal['t'],2) if modal else None,
        'second_click_ms':round(second['t'],2) if second else None,
        'first_zoom_frame':first_zoom_frame,
        'max_zoom':round(max(v[0] for v in out),4),
        'dialog_css_center':[round(v,2) for v in modal_center],
    }
    return out,metadata
