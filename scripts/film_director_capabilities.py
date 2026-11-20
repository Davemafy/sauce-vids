#!/usr/bin/env python3
"""Create the SAME source-pinned renderer contract for any future film director.

No LLM network call, no source pixel upload, no manual per-site coordinates.
The model decides whether the 2.5D studio, loupe, or plain camera best serves
its REAL input, and must return validated sauce-film-plan-v1 JSON.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path
from fractions import Fraction


SCHEMA_PATH=Path(__file__).resolve().parents[1]/"schemas"/"sauce-film-plan-v1.schema.json"
RENDERER_PATH=Path(__file__).resolve().parent/"render_event_video.py"


def _hash(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def source_pointer_capabilities(raw,size):
    """Conservative pointer facts with no guessed or invented motion."""
    samples=raw.get("pointer_samples")
    ordered=False
    if isinstance(samples,list) and len(samples)>=2:
        try:
            seq=[(float(p["t"]),float(p["x"]),float(p["y"])) for p in samples]
            ordered=(all(math.isfinite(v) for p in seq for v in p) and
                     all(0<=p[1]<size[0] and 0<=p[2]<size[1] for p in seq) and
                     all(b[0]>a[0] for a,b in zip(seq,seq[1:])))
        except (KeyError,ValueError,TypeError):
            ordered=False
    event_samples=any(isinstance(e,dict) and
              isinstance(e.get("pointer_samples"),list) and len(e["pointer_samples"])>=2
              for e in raw.get("events",[]))
    return {"recordedPointerTrackAvailable":bool(ordered),
            "eventLocalPointerSamplesPresent":bool(event_samples),
            "allowedCursorModesForStudio":["none","recorded"] if ordered else ["none"]}


def build_contract(source,manifest,brief):
    source=Path(source);manifest=Path(manifest)
    if not source.is_file() or not manifest.is_file():
        raise ValueError("Existing real source and manifest files are mandatory")
    if type(brief) is not str or not 4 <= len(brief.strip()) <= 1200:
        raise ValueError("Film director requires a concise customer brief")
    info=json.loads(subprocess.check_output([
        "ffprobe","-v","error","-select_streams","v:0",
        "-show_entries","stream=width,height,avg_frame_rate:format=duration",
        "-of","json",str(source)],text=True))
    stream=info["streams"][0]
    fps=float(Fraction(stream["avg_frame_rate"]))
    size=[int(stream["width"]),int(stream["height"])]
    if fps not in (24,25,30,50,60) or size[0]<320 or size[1]<180:
        raise ValueError("Unsupported real source frame rate/resolution")
    raw=json.loads(manifest.read_text())
    if raw.get("cursorless") is not True:
        raise ValueError("Capture must declare cursorless provenance")
    rect=raw.get("capture_rect") or {}
    if (rect.get("width"),rect.get("height"))!=tuple(size):
        raise ValueError("Source size and captured pixel space disagree")
    duration=min(float(info["format"]["duration"]),float(raw["duration"]))
    if not math.isfinite(duration) or duration<.5:
        raise ValueError("Invalid source duration")
    events=[]
    for i,e in enumerate(raw.get("events",[])):
        if not isinstance(e,dict) or not isinstance(e.get("evidence"),str) or not e["evidence"].strip():
            continue
        if not all(type(e.get(k)) in (float,int) and math.isfinite(e[k]) and
                   0<=e[k]<=duration for k in ("start","end","t")):
            continue
        fields={}
        for kind,key in (("target","targetRect"),("result","resultRect"),("component","componentRect")):
            b=e.get(key)
            if not isinstance(b,dict) or any(type(b.get(k)) not in (int,float) for k in ("x","y","width","height")):
                continue
            x,y,w,h=[float(b[k]) for k in ("x","y","width","height")]
            if not all(math.isfinite(x) for x in (x,y,w,h)):
                continue
            if x<0 or y<0 or w<1 or h<1 or x+w>size[0] or y+h>size[1]:
                continue
            fields[kind]={key:b[key] for key in ("x","y","width","height")}
        if "target" in fields and ("result" in fields or "component" in fields):
            events.append({"index":i,"kind":str(e.get("kind","event"))[:40],
                "sourceTime":{"start":e["start"],"end":e["end"],"confirmedResultAt":e["t"]},
                "verifiedGeometry":fields})
    if not events:raise ValueError("No verified target and product result for director")
    schema=json.loads(SCHEMA_PATH.read_text())
    pointer=source_pointer_capabilities(raw,size)
    return {
        "schema":"sauce-director-available-capabilities-v1",
        "brief":brief.strip(),
        "actualCapture":{"sourceSha256":_hash(source),"manifestSha256":_hash(manifest),
           "resolution":size,"nativeFps":fps,"durationSeconds":duration,
           "sourceCursorless":True,"verifiedEvents":events,
           "pointerProvenance":pointer},
        "creativeInstruction":"Direct a compelling, source-true cinematic UI film. "
           "You may choose any exposed effect and design original camera/keyframe timings. "
           "Prior references are stylistic only; never copy old product states. "
           "The final encoded movie, not syntax, will be evaluated visually.",
        "availableEffects":{
            "regularCamera":"camera keys with wide/verified event targets; no source repainting",
            "studioStage":"opt-in source-derived perspective stage with source-only UI "
              "pixels, material grain, true recorded pointer, bounded depth, perspective camera, "
              "verified event lighting or sustained source-pixel appearance trigger, source-derived "
              "shadow/reflection, overview/detail payoff clipping guard",
            "glassLoupe":"optional event-driven optical magnifier; do not use merely for decoration",
            "composition":"optional frozen genuine-UI pixel isolation, not live DOM layering"
        },
        "modelOutputInstructions":{
            "return":"One JSON object conforming exactly to included JSON Schema",
            "sourceSha256":"Use exact actualCapture.sourceSha256",
            "manifestSha256":"Use exact actualCapture.manifestSha256",
            "durationSeconds":"Do not exceed actualCapture.durationSeconds",
            "camera":"Omit when studioStage.camera takes over. Otherwise supply validated 2D keys.",
            "studioStage":"Choose only if the creative direction benefits. "
                "Use studioStage.lighting.eventIndex and an appropriate verified payoff. "
                "Set trigger='appearance' only for a plausible visual color change; the engine "
                "detects actual source-frame evidence or falls back to recorded confirmation.",
            "cursor":"For studioStage and flat camera choose ONLY the modes listed "
                     "in actualCapture.pointerProvenance.allowedCursorModesForStudio; "
                     "never invent cursor motion. The legacy glassLoupe may use "
                     "separate verified event-local pointer samples when present.",
            "sourceTruth":"Never add fabricated buttons, text, results, future-state motion, "
                "unverified click targets, or invented pointer samples.",
            "narrative":"Show action, observed change and a legible final payoff."
        },
        "outputSchema":schema,
        "localGate":{"executable":str(RENDERER_PATH.name),
          "flags":["--video","--manifest","--film-plan","--validate-only"],
          "sourceTruth":"Render rejects changed hashes, invalid event/time/geometry, fast "
             "perspective motion, clipped payoff and unproven early lighting",
          "creativeApproval":False}
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--brief",required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=build_contract(a.source,a.manifest,a.brief)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"source":result["actualCapture"]["sourceSha256"],
        "verifiedEvents":len(result["actualCapture"]["verifiedEvents"]),
        "capabilities":list(result["availableEffects"]),
        "hasStudioStage":True,
        "promptSent":False,"creativeApproved":False}))


if __name__=="__main__":
    main()
