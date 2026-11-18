"""Evidence-locked source-true editorial camera for real screen recordings.

Reuses Sauce's existing event-video renderer and source pixels; never creates UI,
actions, cursors, results, or a second browser recording.
"""
from dataclasses import dataclass
import math
import numpy as np

def ease(t):
    u=max(0.,min(1.,t))
    return u*u*u*(u*(u*6-15)+10)

def bounds(e,key,sw,sh):
    d=e.get(key) if isinstance(e,dict) else None
    if not isinstance(d,dict):return None
    try: x,y,w,h=(float(d[k]) for k in ('x','y','width','height'))
    except (KeyError,TypeError,ValueError):return None
    if (not all(map(math.isfinite,(x,y,w,h))) or w<6 or h<6 or x<0 or y<0
        or x+w>sw or y+h>sh):return None
    return x,y,w,h

def moment(e):
    t=e.get('t') if isinstance(e,dict) else None
    return float(t) if type(t) in (int,float) and math.isfinite(t) else None

@dataclass(frozen=True)
class Pose:
    zoom:float
    x:float
    y:float

@dataclass(frozen=True)
class Workflow:
    opening:Pose
    button:Pose
    outcome:Pose
    button_start:float
    button_end:float
    result_start:float
    result_end:float
    release_start:float
    release_end:float
    result_bounds:tuple
    click_time:float
    result_time:float
    source_size:tuple
    output_size:tuple

    def sample(self,t):
        if not math.isfinite(t):raise ValueError('Nonfinite film time')
        def mix(a,b,ratio):
            u=ease(ratio)
            return Pose(a.zoom+(b.zoom-a.zoom)*u,
                        a.x+(b.x-a.x)*u,a.y+(b.y-a.y)*u)
        if t<self.button_start:return self.opening
        if t<self.button_end:return mix(self.opening,self.button,(t-self.button_start)/(self.button_end-self.button_start))
        if t<self.result_start:return self.button
        if t<self.result_end:
            # One source-event-locked cut reframes the genuinely changed UI
            # from the distant toolbar to its result. A bounded push then
            # enlarges the original pixels. Never whip 2000px across a page.
            context=Pose(min(1.60,self.outcome.zoom),self.outcome.x,self.outcome.y)
            return mix(context,self.outcome,(t-self.result_start)/(self.result_end-self.result_start))
        if t<self.release_start:return self.outcome
        if t<self.release_end:return mix(self.outcome,self.opening,(t-self.release_start)/(self.release_end-self.release_start))
        return self.opening

    def matrix(self,t):
        sw,sh=self.source_size
        ow,oh=self.output_size
        p=self.sample(t)
        sx=(ow/sw)*p.zoom
        hw=sw/(2*p.zoom);hh=sh/(2*p.zoom)
        cx=min(sw-hw,max(hw,p.x))
        cy=min(sh-hh,max(hh,p.y))
        return np.float64([[sx,0.,ow/2-cx*sx],[0.,sx,oh/2-cy*sx]])

    def receipt(self):
        return {'schema':'source-true-workflow-camera-v1',
                'opening':vars(self.opening),'button':vars(self.button),
                'result':vars(self.outcome),
                'buttonStart':self.button_start,'buttonEnd':self.button_end,
                'resultStart':self.result_start,'resultEnd':self.result_end,
                'releaseStart':self.release_start,'releaseEnd':self.release_end,
                'resultBounds':self.result_bounds,
                'resultCutSourceFrame':math.ceil(self.result_start*60),
                'sourceTimelinePreserved':True,'noSyntheticUI':True}

def plan_verified_workflow(events,source_size,output_size,duration,lead_s=0):
    sw,sh=source_size;ow,oh=output_size
    if (not isinstance(events,list) or sw<640 or sh<360 or sw*oh!=sh*ow
        or not math.isfinite(duration) or duration<7
        or type(lead_s) not in (int,float) or not math.isfinite(lead_s)
        or not 0<=lead_s<=.75):return None
    for i,result in enumerate(events):
        if not isinstance(result,dict) or result.get('kind')!='state_change':continue
        if not isinstance(result.get('evidence'),str) or not result['evidence'].strip():continue
        rt=moment(result);rb=bounds(result,'resultRect',sw,sh)
        if rt is None or rb is None:continue
        clicks=[e for e in events[:i] if isinstance(e,dict)
                and e.get('kind')=='click' and isinstance(e.get('semanticGoal'),str)
                and e['semanticGoal'].strip() and moment(e) is not None
                and 0<=rt-moment(e)<=1.8 and bounds(e,'targetRect',sw,sh)]
        if not clicks:continue
        clicked=clicks[-1];ct=moment(clicked);cb=bounds(clicked,'targetRect',sw,sh)
        selections=[e for e in events[:i] if isinstance(e,dict)
                    and e.get('kind')=='range_select' and moment(e) is not None
                    and .5<=ct-moment(e)<=4 and bounds(e,'resultRect',sw,sh)]
        if not selections:continue
        sel=bounds(selections[-1],'resultRect',sw,sh)
        approach=[e for e in events[:i] if isinstance(e,dict)
                  and e.get('kind')=='cursor_dwell' and moment(e) is not None
                  and 0<ct-moment(e)<1 and bounds(e,'targetRect',sw,sh)
                  and abs(bounds(e,'targetRect',sw,sh)[0]-cb[0])<20]
        if not approach:continue
        completion=next((e for e in events[i+1:] if isinstance(e,dict)
                         and e.get('kind')=='interaction_complete' and moment(e)
                         and moment(e)>rt),None)
        if completion is None:continue
        bs=moment(approach[-1])+lead_s
        be=ct+lead_s-.05
        rs=rt+lead_s+.07
        re=rs+.72
        ls=moment(completion)+lead_s+.25
        le=ls+1.22
        if not(.5<bs<be<rs<re<ls<le<duration-.02):continue
        rx,ry,rw,rh=rb;bx,by,bw,bh=cb
        left=min(bx,sel[0],rx)
        right=max(bx+bw,sel[0]+sel[2],rx+rw)
        wide=min(1.36,max(1.,(sw*.91)/(right-left+sw*.13)))
        intro=Pose(wide,(left+right)/2,sh*.40)
        toolbar=Pose(min(1.64,wide+.28),bx+bw/2,by+bh/2)
        zoom=min(2.30,sw/(rw+sw*.23),sh/(rh+sh*.19))
        if zoom<1.65:continue
        shot=Workflow(intro,toolbar,Pose(zoom,rx+rw/2,ry+rh/2),
                      round(bs,5),round(be,5),round(rs,5),round(re,5),
                      round(ls,5),round(le,5),rb,ct+lead_s,rt+lead_s,
                      source_size,output_size)
        projected=np.array([[rx,ry,1.],[rx+rw,ry+rh,1.]])@shot.matrix(re).T
        if projected[0,0]<24 or projected[0,1]<24 or projected[1,0]>ow-24 or projected[1,1]>oh-24:continue
        return shot
    return None
