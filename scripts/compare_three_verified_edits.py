"""Three controlled Sauce edits of ONE verified real browser capture.

Research-only creative experiment. Preserves exact source/video, source event
manifest and Foley indices. Only film-plan camera and physical presentation
grammar differ; never authors product pixels, outcomes or pointer data.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, math
from pathlib import Path


PROFILES={
    "living": "Continuous editorial camera with one stable detail focus per verified price",
    "editorial": "Native-frame-locked cuts following proven results, long stable reads",
    "optical": "Physical glass-window dolly and bounded original pointer spring",
}


def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def validate_capture(source, manifest_path, base_plan):
    source=Path(source);manifest_path=Path(manifest_path)
    base=json.loads(Path(base_plan).read_text())
    data=json.loads(manifest_path.read_text())
    if base.get("schema")!="sauce-film-plan-v1" or not isinstance(data,dict):
        raise ValueError("Original verified Sauce film plan required")
    if base["sourceSha256"]!=sha(source) or base["manifestSha256"]!=sha(manifest_path):
        raise ValueError("Original real source/manifest hash mismatch")
    if not data.get("cursorless") or len(data.get("pointer_samples",[]))<20:
        raise ValueError("Original source must have real pointer evidence")
    events=data.get("events",[])
    duration=float(base["durationSeconds"])
    if len(events)!=3 or duration<9.0 or duration>18.0:
        raise ValueError("This bounded comparison expects three real result events")
    if abs(float(data.get("duration",0))-duration)>.02:
        raise ValueError("Source manifest film duration drift")
    for i,event in enumerate(events):
        if event.get("kind") not in ("slider_change","click","switch_tab") or not event.get("evidence"):
            raise ValueError("One or more source actions lack independent verification")
        for k in ("start","t","end"):
            if not isinstance(event.get(k),(float,int)) or not math.isfinite(event[k]):
                raise ValueError("Missing measured source action time")
        if not (0<=event["start"]<=event["end"]<=event["t"]+.02<duration-1):
            raise ValueError("Source event chronology untrusted")
        if i and event["start"]<=events[i-1]["t"]+.65:
            raise ValueError("No credible reading time between authentic outcomes")
        for key in ("targetRect","resultRect"):
            box=event.get(key,{})
            if not all(isinstance(box.get(k),(int,float)) and box[k]>=0 for k in ("x","y","width","height")):
                raise ValueError("Missing original source DOM rect")
            if min(box["width"],box["height"])<=1:
                raise ValueError("Empty original source DOM rect")
    if base.get("cursor")!="recorded" or base.get("audio",{}).get("eventIndices")!=[0,1,2]:
        raise ValueError("Music/Foley/cursor comparability requires identical source evidence")
    return base,data


def key(at,scale,*,start=None,focus=None,view=None,cut=False):
    k={"at":float(at),"scale":round(float(scale),4)}
    if start is not None:k["startAt"]=float(start)
    if focus:k["focus"]=focus
    else:k["center"]=[.5,.5]
    if view is not None:k["viewScale"]=round(float(view),4)
    if cut:k["cut"]=True
    return k


def derive(profile,source,manifest,base):
    if profile not in PROFILES:raise ValueError("Unknown creative comparison")
    film,proof=validate_capture(source,manifest,base)
    e=proof["events"];end=float(film["durationSeconds"])
    output=copy.deepcopy(film)
    stage=output["studioStage"]
    # Identical appearance, fixed source and recorded audio across the trio.
    # Bright cobalt clouds are in the environment, and the real full-sized
    # browser is the ONLY floating glass. No fake overlays or frame content.
    stage["stagePreset"]="cloud_window_fullglass_v1"
    stage["payoff"]={"region":"event:2:result","mode":"detail",
                     "minVisible":.94,"minContextVisible":.66}
    stage["lighting"]={"eventIndex":2,"trigger":"verified",
                        "intensity":.36,"transitionSeconds":.28}
    stage["reflection"]=.035
    stage["depthPx"]=8
    stage["material"]={"color":[30,32,38],"grain":.1}
    timing=[(float(x["start"]),float(x["t"])) for x in e]
    if profile=="living":
        # Maintain visual continuity. No gratuitous pull-back between the
        # related slider changes, and always focus on true displayed results.
        cams=[key(0,.885)]
        for i,(start,t) in enumerate(timing):
            at=t+.48
            transition=t+.06
            cams.append(key(at,[1.045,1.075,1.105][i],
                            start=transition,focus=f"event:{i}:result"))
        cams.append(key(end,1.105,start=end-.55,focus="event:2:result"))
        stage["motion"]={"profile":"cinematic","shutter":.13}
    elif profile=="editorial":
        # Temporal jump is CAMERA ONLY; recorded source timestamps continue
        # straight through the entire 10.2s clip. Cuts only after real
        # outcome evidence at exact original native60 frame boundaries.
        cams=[key(0,.88)]
        for i,(_,t) in enumerate(timing):
            cut_time=math.ceil((t+.045)*60)/60
            cams.append(key(cut_time,[1.26,1.31,1.36][i],
                            start=cut_time,focus=f"event:{i}:result",cut=True))
            # Cut makes the observed price legible, then release to the
            # full slider BEFORE the next real gesture. No cropped action.
            if i<2:
                next_start=timing[i+1][0]
                bridge=next_start-.25
                transition=max(cut_time+.45,bridge-.56)
                if bridge-transition<.2:
                    raise ValueError("No pre-next-action source context")
                cams.append(key(bridge,.885,start=transition))
        cams.append(key(end,1.23,start=end-.64,focus="event:2:result"))
        stage["motion"]={"profile":"cinematic","shutter":0.}
    else:
        # Dolly the WHOLE glass/browser after source-verified price changes.
        # Do not pan a price card to frame center: that moved the real page
        # heading out of frame in the rejected optical study. Keep the
        # original UI, context and recorded cursor source-true.
        cams=[key(0,.885,view=1.)]
        first_pre=max(.24,timing[0][0]-.18)
        cams.append(key(first_pre,.89,start=.12,
                        focus="event:0:target",view=1.015))
        for i,(start,t) in enumerate(timing):
            cams.append(key(t+.58,.89,start=t+.065,
                            view=[1.085,1.135,1.16][i]))
            if i<2:
                next_start=timing[i+1][0]
                end_bridge=next_start-.24
                begin=max(t+.58,end_bridge-.42)
                if end_bridge-begin<.22:
                    raise ValueError("No context shot possible between proven events")
                cams.append(key(end_bridge,.88,start=begin,view=1.01))
        cams.append(key(end,.88,start=end-.95,view=1.))
        stage["motion"]={"profile":"reference-spring","immersive":True,
                         "shutter":.16,
                         "follow":{"mode":"source-cursor-spring","eventIndices":[0,1,2],
                                   "responseSeconds":.38,"strength":.075,
                                   "deadzone":.14,"maxOffset":.012,
                                   "beforeSeconds":.42,"afterSeconds":.42}}
    stage["camera"]=cams
    return output


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",required=True,type=Path)
    p.add_argument("--manifest",required=True,type=Path)
    p.add_argument("--base-plan",required=True,type=Path)
    p.add_argument("--output-dir",required=True,type=Path)
    a=p.parse_args()
    if a.output_dir.exists():
        raise ValueError("Preserve existing research films: output directory exists")
    plans={name:derive(name,a.source,a.manifest,a.base_plan) for name in PROFILES}
    a.output_dir.mkdir(mode=0o700,parents=True)
    manifest={
        "schema":"sauce-three-verified-edits-v1",
        "sourceSha256":sha(a.source),"manifestSha256":sha(a.manifest),
        "source":str(a.source),"sourceEventCount":3,
        "sourceTimelineUnchanged":True,
        "creativeApproval":False,
        "profiles":{}
    }
    for name,plan in plans.items():
        folder=a.output_dir/name
        folder.mkdir(mode=0o700)
        path=folder/"plan.json"
        path.write_text(json.dumps(plan,indent=2)+"\n")
        manifest["profiles"][name]={"intent":PROFILES[name],
                                    "cameraKeys":len(plan["studioStage"]["camera"]),
                                    "planSha256":sha(path)}
    (a.output_dir/"experiment.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps(manifest,indent=2))


if __name__=="__main__":main()
