"""Opt-in compact drawing edit. Preserve the actual stroke and verified payoff.

Reuse existing source event director, camera validation and native compositor.
A clean neutral studio is selected for a pale, high-contrast drawing surface.
No global warp, glass treatment, added graphics or fabricated source states.
"""
import argparse
import json
import math
from pathlib import Path
if __package__:
    from .source_event_director import direction
else:
    from source_event_director import direction

def compact_drawing(plan,manifest):
    events=manifest.get('events',[])
    if len(events)!=1 or events[0].get('kind')!='draw_stroke':
        raise ValueError('Requires a single independently verified drawing stroke')
    e=events[0]
    start,end,result=(float(e[k]) for k in ('start','end','t'))
    if not e.get('evidence') or not .6<=start<end<=result:
        raise ValueError('Unverified drawing chronology')
    duration=math.ceil((result+1.80)*60)/60
    if duration>plan['durationSeconds'] or duration<4.5:
        raise ValueError('Insufficient genuine result hold')
    sw,sh=(manifest['capture_rect'][k] for k in ('width','height'))
    fit=min(.86,(1080-96)*sw/(1920*sh))
    box=e['targetRect']
    # The verified canvas must fit inside the output throughout the push.
    detail=min(1.55,(1920-32)*sw/(1920*box['width']),
               (1080-32)*sw/(1920*box['height']))
    if detail<fit*1.12:raise ValueError('No useful detail composition')
    contact=math.ceil(start*60)/60
    after=math.ceil(result*60)/60
    # Approach is observed; push after contact, hold during the last stroke,
    # then return after independently verified completion. No hard cuts.
    peak=math.floor((end-.18)*60)/60
    release=math.ceil((result+.1)*60)/60
    returned=math.ceil((result+1.15)*60)/60
    if not contact+.9<peak<after<release<returned<duration-.5:
        raise ValueError('No readable continuous detail timeline')
    def key(at,scale,focus='wide',begin=None):
        k={'at':at,'scale':scale,'yaw':0,'pitch':0}
        if focus=='wide':k['center']=[.5,.5]
        else:k['focus']=focus
        if begin is not None:k['startAt']=begin
        return k
    plan['durationSeconds']=duration
    plan['cursorMotion']='reference-v1'
    s=plan['studioStage']
    s.update(stagePreset='classic',material={'color':[36,37,39],'grain':.08},
             depthPx=0,reflection=0,lighting={'eventIndex':0,'trigger':'verified','intensity':0,'transitionSeconds':.32},
             motion={'profile':'cinematic','shutter':0})
    s['camera']=[key(0,fit),key(peak,detail,'event:0:target',contact),
                 key(after,detail,'event:0:target',peak),
                 key(returned,fit,'wide',release),key(duration,fit,'wide',returned)]
    s['payoff']={'region':'event:0:result','mode':'overview','minVisible':.99,'minContextVisible':.99}
    return plan

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',required=True,type=Path);p.add_argument('--manifest',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    a=p.parse_args()
    if a.out.exists():raise ValueError('Refuse overwrite')
    plan=compact_drawing(direction(a.source,a.manifest),json.loads(a.manifest.read_text()))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(plan,indent=2)+'\n')
if __name__=='__main__':main()
