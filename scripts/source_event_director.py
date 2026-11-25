#!/usr/bin/env python3
"""Deterministic source-event story edit when no external director is available.

NOT a simulated LLM decision or premium creative approval. Uses only
source-video hashes, verified event times, real geometry, original recorded
pointer and prior Sauce studio primitives. For bounded public demos; no
fabricated event, content, site coordinates or timestamp.
"""
from __future__ import annotations
import argparse,hashlib,json,math
from pathlib import Path


def sha(file):
    dig=hashlib.sha256()
    with Path(file).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):dig.update(b)
    return dig.hexdigest()


def direction(video:Path,manifest:Path,hero_event_index=None):
    from film_director_capabilities import build_contract
    packet=build_contract(video,manifest,
        "Produce a readable 16:9 real-source two-or-more-step product film")
    evidence=json.loads(Path(manifest).read_text())
    duration=packet["actualCapture"]["durationSeconds"]
    events=evidence.get("events",[])
    long_story=25<duration<=30 and 3<=len(events)<=6
    short_story=1<=len(events)<=4 and (6<=duration<=25 if len(events)==1 else 8<=duration<=25)
    if (not (long_story or short_story) or
        evidence.get("cursorless") is not True or
        not packet["actualCapture"]["pointerProvenance"].get("recordedPointerTrackAvailable")):
        raise ValueError("Need 1..4 short or 3..6 long source-verified visible UI actions and original recorded pointer")
    if hero_event_index is not None and (not long_story or type(hero_event_index) is not int
            or not 0<=hero_event_index<len(events)):
        raise ValueError("Hero must reference a verified long-story event")
    for i,e in enumerate(events):
        if (not e.get("evidence") or e["start"]<.7 or
            e["t"]-e["start"]>3.5 or e["t"]>=duration-.9 or
            (i>0 and e["start"]-events[i-1]["t"]<.7)):
            raise ValueError("Recorded actions lack independent readable timing")
    frame_rate=packet["actualCapture"]["nativeFps"]
    def native(t):
        return round(round(t*frame_rate)/frame_rate,9)
    def after_visible(t):
        return round(math.ceil(t*frame_rate-1e-9)/frame_rate,9)
    def bounded(v,l,h):return max(l,min(h,v))
    source_w,source_h=packet["actualCapture"]["resolution"]
    # On the approved floating window, the real webpage already has a
    # larger physical frame. Start with its entire UI, not an artistic crop.
    keys=[{"at":0,"scale":.88,"center":[.5,.5],"yaw":0,"pitch":0}]
    for ix,e in enumerate(events):
        area=e["targetRect"]
        target_x=(area["x"]+area["width"]*.5)/source_w
        target_y=(area["y"]+area["height"]*.5)/source_h
        start=native(e["start"]-.18)
        if start-keys[-1]["at"]<.4:
            raise ValueError("Actions too close for readable framing")
        precenter=[round(bounded(.5+(.5-target_x)*.016,.493,.507),4),
                   round(bounded(.5+(.5-target_y)*.014,.493,.507),4)]
        keys.append({"at":start,
                     "startAt":native(max(keys[-1]["at"],start-.92)),
                     "scale":.885,"center":precenter,"yaw":0,"pitch":0})
        outcome=native(e["t"]+.33)
        if outcome<=start+.4 or outcome>=duration-.2:
            raise ValueError("Result cannot be held meaningfully")
        # Native result anchoring never starts before its confirmed source
        # evidence. The browser itself determines the result's geometry.
        result=e["resultRect"]
        result_fraction=result["width"]*result["height"]/(source_w*source_h)
        # A source-spanning theme change is an overview; an actually
        # observed compact dialog is a deliberate detail beat.
        zoom=.895 if result_fraction>=.74 else .955
        keys.append({"at":outcome,"startAt":after_visible(e["t"]),
                     "scale":zoom,"focus":f"event:{ix}:result",
                     "yaw":0,"pitch":0})
    if keys[-1]["at"]>duration-1.8:
        raise ValueError("No source-verified final payoff hold")
    keys.append({"at":duration,"startAt":native(max(keys[-1]["at"],duration-1.12)),
                 "scale":.88,"center":[.5,.5],"yaw":0,"pitch":0})
    plan={
      "schema":"sauce-film-plan-v1",
      "sourceSha256":sha(video),"manifestSha256":sha(manifest),
      "durationSeconds":duration,"presentation":"fullscreen",
      "cursor":"recorded",
      "audio":{"mode":"eventFoley",
               "eventIndices":list(range(len(events))),
               "clickGain":0.,"motionGain":.10,"masterGain":.46},
      "studioStage":{
        "stagePreset":"cloud_window_clearface_v1",
         "camera":keys,
         "material":{"color":[32,35,43],"grain":.16},
         "lighting":{"eventIndex":len(events)-1,"trigger":"verified",
                     "intensity":.42,"transitionSeconds":.32},
         "depthPx":9,"reflection":.05,
         "payoff":{"region":f"event:{len(events)-1}:result",
                   "mode":("detail" if result_fraction<.74 else "overview"),
                   "minVisible":.90,"minContextVisible":.68}
       }
    }
    if long_story:
        # Audible, restrained defaults for the long customer edit. Source
        # event times are unchanged; a quiet soundtrack is mixed separately.
        plan["audio"].update(clickGain=.44,motionGain=.22,masterGain=.78)
        # Preserve product context across a continuous long workflow. A
        # large result in one panel is not permission to crop the editor.
        def whole(at,view,start=None):
            k={"at":at,"scale":.88,"viewScale":view,"center":[.5,.5],"yaw":0,"pitch":0}
            if start is not None:k["startAt"]=start
            return k
        camera=[whole(0,1.)]
        for i,e in enumerate(events):
            begin=after_visible(e["t"])
            peak=native(begin+.45)
            next_press=events[i+1]["start"] if i+1<len(events) else duration
            is_hero=i==hero_event_index
            # Hold the hero at peak rather than spending its whole beat in motion.
            # Setup beats get a smaller, shorter push. Never extend a source beat
            # across the next genuine press or change the original source clock.
            zoom=1.065 if is_hero else (1.035 if hero_event_index is not None else 1.065)
            hold=2.35 if is_hero else (.25 if hero_event_index is not None else .4)
            release=native(min(next_press-.25,peak+hold+.85))
            if release<=peak+.2:
                continue
            camera.extend([whole(peak,zoom,begin),
                           whole(release,1.,native(max(peak,release-.85)))])
        camera.append(whole(duration,1.))
        plan["studioStage"]["camera"]=camera
        plan["studioStage"]["motion"]={"profile":"cinematic","immersive":True,"shutter":0}
        plan["studioStage"]["payoff"].update(mode="overview",minVisible=.99,minContextVisible=.99)
    if len(events)==1 and events[0]["kind"]=="draw_stroke":
        e=events[0]
        # Preserve the complete drawing surface during the actual stroke.
        rise_start=after_visible(max(.18,e["start"]-.55))
        rise_end=native(min(e["end"],e["start"]+.8))
        release_start=after_visible(e["t"]+.35)
        if rise_end>rise_start+.4 and release_start<duration-1.0:
            def wide(at,view,start=None):
                k={"at":at,"scale":.88,"viewScale":view,
                   "center":[.5,.5],"yaw":0,"pitch":0}
                if start is not None:k["startAt"]=start
                return k
            plan["studioStage"]["camera"]=[
                wide(0,1.),wide(rise_end,1.035,rise_start),
                wide(native(duration-.35),1.,release_start),
                wide(duration,1.)]
            plan["studioStage"]["motion"]={"profile":"cinematic","immersive":True,"shutter":0}
            plan["studioStage"]["payoff"].update(mode="overview",minVisible=.99,minContextVisible=.99)
    return plan


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--hero-event-index",type=int)
    a=p.parse_args()
    if a.out.exists():raise ValueError("Refuse to replace existing creative work")
    plan=direction(a.source.resolve(),a.manifest.resolve(),a.hero_event_index)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(plan,indent=2)+"\n")
    print(json.dumps({"filmPlan":str(a.out),"verifiedEvents":len(plan["audio"]["eventIndices"]),
                      "sourceSha256":plan["sourceSha256"],
                      "creativeApproved":False}))
if __name__=="__main__":main()
