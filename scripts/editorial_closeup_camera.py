"""Editorial camera test: an actual browser action fills the frame.

This is a separately selectable four-second filmmaking benchmark, not a
replacement for Sauce's established evidence-driven default planner.
"""
from __future__ import annotations
import math
from spring_motion import Spring1D,Spring2D
from cinematic_tracks import cinematic_camera


def closeup_camera(events:list[dict],start_ms:float,
                   duration:float,fps:int,
                   viewport:tuple[int,int]=(1280,720),
                   window:tuple[int,int]=(1480,832),
                   expanded_rect:dict|None=None):
    original,meta=cinematic_camera(events,start_ms,duration,fps,viewport)
    buttons=[e for e in events if e['type']=='pointerdown' and e.get('box')]
    dialogs=[e for e in events if e['type']=='dialog-visible' and e.get('box')]
    if len(buttons)<2 or not dialogs:
        raise ValueError('Editorial proof requires two recorded clicks and a real dialog')
    first,second=buttons[:2]
    dialog=dialogs[0]
    if not first['t']<dialog['t']<second['t']:
        raise ValueError('Unexpected recorded action/dialog ordering')
    w,h=viewport;ww,wh=window
    box=dialog['box']
    safe=min((ww-118)/(box['width']*ww/w),
             (wh-100)/(box['height']*wh/h),1.72)
    if safe<1.5:raise ValueError('Dialog cannot fit safely into editorial closeup')
    target_zoom=min(1.67,safe)
    if expanded_rect is None:
        raise ValueError('Expanded modal geometry must be measured after the real second click')
    if not all(key in expanded_rect for key in ('x','y','width','height')):
        raise ValueError('Incomplete expanded modal rectangle')
    if not 0<expanded_rect['height']<=h or not 0<expanded_rect['width']<=w:
        raise ValueError('Expanded modal geometry out of bounds')
    reveal_safe=min((ww-120)/(expanded_rect['width']*ww/w),
                    (wh-106)/(expanded_rect['height']*wh/h),1.72)
    if reveal_safe<1.05:raise ValueError('Expanded modal cannot fit the stage')
    detail_zoom=min(1.30,reveal_safe-.005)
    center=(w*.5,h*.5)
    dialog_center=(box['x']+box['width']*.5,box['y']+box['height']*.5)
    expanded_center=(expanded_rect['x']+expanded_rect['width']*.5,
                     expanded_rect['y']+expanded_rect['height']*.5)
    target=(first['x'],first['y'])
    first_motion=meta['first_pointer_motion_ms']
    scale=Spring1D(1.,stiffness=160.,damping=2*math.sqrt(160.))
    pan=Spring2D(*center,stiffness=168.,damping=2*math.sqrt(168.))
    output=[]
    for i in range(round(duration*fps)):
        now=start_ms+1000*i/fps
        if now<first_motion:
            desired_z=1.
            dest=center
        elif now<first['t']:
            # Zoom follows the *actual approach*, never precedes it.
            progress=min(1.,(now-first_motion)/max(1.,first['t']-first_motion))
            eased=progress*progress*(3-2*progress)
            desired_z=1.+.27*eased
            dest=(center[0]+(target[0]-center[0])*.30*eased,
                  center[1]+(target[1]-center[1])*.15*eased)
        elif now<dialog['t']:
            desired_z=1.27
            dest=(center[0]+(target[0]-center[0])*.30,
                  center[1]+(target[1]-center[1])*.15)
        elif now<second['t']-560:
            desired_z=target_zoom
            dest=dialog_center
        elif now<second['t']:
            # Recorded cursor starts approaching the second control:
            # deliberate pullback PREPARES for the real expanding panel.
            desired_z=detail_zoom
            dest=expanded_center
        else:
            desired_z=detail_zoom
            dest=expanded_center
        if i:
            scale.step(desired_z,1/fps)
            pan.step(*dest,1/fps)
        output.append((scale.position,pan.x.position,pan.y.position))
    meta={**meta,
          'policy':'editorial: action -> real modal -> command, two narrated beats',
          'max_zoom':round(max(z for z,_,_ in output),4),
          'safe_modal_zoom':round(safe,4),
          'requested_modal_zoom':target_zoom,
          'expanded_modal_zoom':detail_zoom,
          'expanded_dialog_css_rect':expanded_rect,
          'dialog_css_rect':box,
          'editorial_closeup':True}
    return output,meta
