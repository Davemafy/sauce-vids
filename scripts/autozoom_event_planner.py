#!/usr/bin/env python3
"""Event-driven camera planning for Sauce recordings.

No hand-authored camera keyframes. A click that changes state may create one
focus shot on the resulting DOM region. Missing evidence -> locked wide shot.
All source coordinates are from capture sidecar, in the source viewport frame.
"""
from __future__ import annotations
import json,math
from dataclasses import dataclass
from pathlib import Path

def smooth5(x:float)->float:
    x=max(0.0,min(1.0,x))
    return x*x*x*(x*(x*6.0-15.0)+10.0)

def clamp(v:float,lo:float,hi:float)->float:
    return max(lo,min(hi,v))

@dataclass(frozen=True)
class Shot:
    action:str
    click:float
    start:float
    settle:float
    release:float
    end:float
    zoom:float
    focus_x:float
    focus_y:float
    evidence:str
    result_rect:dict
    def sample(self,t:float):
        if t<self.start:
            z=0.0
        elif t<self.settle:
            z=smooth5((t-self.start)/(self.settle-self.start))
        elif t<self.release:
            z=1.0
        elif t<self.end:
            z=1.0-smooth5((t-self.release)/(self.end-self.release))
        else:
            z=0.0
        return z
    def dictionary(self):
        return vars(self)

def plan(events:list, viewport:dict,duration:float)->list[Shot]:
    shots=[]
    w,h=viewport["width"],viewport["height"]
    meaningful=[e for e in events if e.get("kind")=="click" and e.get("semanticGoal")]
    for click in meaningful:
        ct=click["t"]
        # Only trust actual recorded DOM change, not a cursor dwell or guessed click.
        changed=next((e for e in events if e.get("kind")=="state_change"
                      and ct<=e.get("t",-1)<=ct+1.8
                      and e.get("resultRect")),None)
        if not changed:
            continue
        bounds=changed["resultRect"]
        if any(float(bounds[k])<=0 for k in ("width","height")):
            continue
        # When result region is very tall, the meaningful top portion is what
        # deserves to be read first (header + first changed lines), not all rows.
        rw=float(bounds["width"])
        rh=float(bounds["height"])
        fx=(bounds["x"]+rw*.53)/w
        fy=(bounds["y"]+rh*.38)/h
        if not (0.04<=fx<=.96 and 0.04<=fy<=.96):
            continue
        readable_w=rw*.80
        readable_h=rh*.56
        max_zoom=min(w/(readable_w+180),h/(readable_h+155))*.97
        zoom=clamp(max_zoom,1.16,1.36)
        end_evt=next((e for e in events if e.get("kind")=="interaction_complete"
                    and changed["t"]<e.get("t",-1)<duration),None)
        if end_evt is not None:
            release=min(duration-1.15,end_evt["t"]+.18)
        else:
            release=min(duration-1.15,changed["t"]+3.3)
        start=max(0.0,ct-.32)
        settle=min(release-.7,changed["t"]+1.20)
        end=min(duration-.14,release+2.05)
        if settle<=start or end<=release:continue
        shots.append(Shot(
            action=str(click.get("label","interaction")),click=float(ct),
            start=round(start,4),settle=round(settle,4),
            release=round(release,4),end=round(end,4),
            zoom=round(zoom,5),focus_x=round(fx,6),
            focus_y=round(fy,6),
            evidence=str(changed.get("evidence","documented state change")),
            result_rect=bounds,
        ))
    # A conservatively bounded planner should not stack competing camera paths.
    accepted=[]
    last_end=-1.0
    for shot in sorted(shots,key=lambda a:a.start):
        if shot.start>=last_end:
            accepted.append(shot)
            last_end=shot.end
    return accepted

def sample_camera(t:float,shots:list[Shot]):
    if not shots:return (1.0,.5,.5)
    z=1.0
    x,y=.5,.5
    for shot in shots:
        p=shot.sample(t)
        if p>0:
            z+=p*(shot.zoom-1)
            x+=p*(shot.focus_x-.5)
            y+=p*(shot.focus_y-.5)
    return z,x,y

if __name__=="__main__":
    import sys
    manifest=json.loads(Path(sys.argv[1]).read_text())
    viewport={"width":manifest["capture_rect"]["width"],
              "height":manifest["capture_rect"]["height"]}
    result=plan(manifest["events"],viewport,manifest["duration"])
    print(json.dumps([s.dictionary() for s in result],indent=2))
