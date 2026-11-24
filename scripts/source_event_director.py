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


def direction(video:Path,manifest:Path):
    from film_director_capabilities import build_contract
    packet=build_contract(video,manifest,
        "Produce a readable 16:9 real-source two-or-more-step product film")
    evidence=json.loads(Path(manifest).read_text())
    duration=packet["actualCapture"]["durationSeconds"]
    events=evidence.get("events",[])
    if (not 1<=len(events)<=4 or not (6<=duration<=25 if len(events)==1 else 8<=duration<=25) or
        evidence.get("cursorless") is not True or
        not packet["actualCapture"]["pointerProvenance"].get("recordedPointerTrackAvailable")):
        raise ValueError("Need 1..4 source-verified visible UI actions and original recorded pointer")
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
    return plan


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():raise ValueError("Refuse to replace existing creative work")
    plan=direction(a.source.resolve(),a.manifest.resolve())
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(plan,indent=2)+"\n")
    print(json.dumps({"filmPlan":str(a.out),"verifiedEvents":len(plan["audio"]["eventIndices"]),
                      "sourceSha256":plan["sourceSha256"],
                      "creativeApproved":False}))
if __name__=="__main__":main()
