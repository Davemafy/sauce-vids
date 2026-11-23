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
import re
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
            "sourceCursorSpringAvailable":bool(ordered and len(samples)>=3),
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
            # Present director-safe SOURCE FRAME INDICES, not guessed times.
            # Reuse the same strict appearance detector as the real renderer.
            onset=e["t"]
            method="verified-event-time"
            if "result" in fields:
                try:
                    from spatial_studio_stage import detect_appearance_onset
                    evidence=detect_appearance_onset(source,tuple(size),e,fps)
                    onset=float(evidence["time"])
                    method=evidence["method"]
                except (ValueError,KeyError,RuntimeError,ImportError):
                    # Source-proof analysis is optional, never an invitation to
                    # claim a speculative earlier result or publish credentials.
                    onset=e["t"]
            action_frame=int(math.ceil(e["start"]*fps-1e-8))
            result_frame=int(math.ceil(onset*fps-1e-8))
            candidate_cuts={
               "action":{"nativeFrame":action_frame,"atSeconds":round(action_frame/fps,6),
                         "notBeforeActualPress":True},
               "result":{"nativeFrame":result_frame,"atSeconds":round(result_frame/fps,6),
                         "onsetMethod":method,"notBeforeActualResult":True}}
            summary={"index":i,"kind":str(e.get("kind","event"))[:40],
                "sourceTime":{"start":e["start"],"end":e["end"],"confirmedResultAt":e["t"]},
                "verifiedGeometry":fields,"candidateCuts":candidate_cuts}
            observed=e.get("observedPublicPrice")
            if isinstance(observed,str) and re.fullmatch(
                    r"\$[0-9][0-9,]*(?:\.[0-9]{2})? / mo",observed):
                summary["verifiedObservedPublicPrice"]=observed
            # A public, source-authenticated reversible ARIA-tab action can
            # be named to the creative director only after the original
            # browser capture + native result-pixel adapter admitted it.
            action=e.get("observedPublicAction")
            if (e.get("kind")=="tab_switch" and isinstance(action,str) and
                    re.fullmatch(r"[A-Za-z][A-Za-z0-9 \-_]{0,41}",action)):
                summary["verifiedObservedPublicAction"]=action
            events.append(summary)
    if not events:raise ValueError("No verified target and product result for director")
    schema=json.loads(SCHEMA_PATH.read_text())
    # Advertise only genuinely captured, hash-pinned, independently decodable
    # live DOM plates. Without those bytes no model may request this feature.
    verified_layers=[]
    for candidate in raw.get("domPlanes",[])[:5]:
        if not isinstance(candidate,dict):
            continue
        paired_frame=candidate.get("firstPairedFrame")
        if type(paired_frame) is not int or paired_frame<0:
            continue
        relevant=next((event for event in events
            if event["sourceTime"]["confirmedResultAt"]+.12<=paired_frame/fps),None)
        if relevant is None or paired_frame/fps>duration-1.6:
            continue
        first=math.ceil(max(paired_frame/fps,
                 relevant["sourceTime"]["confirmedResultAt"]+.12)*fps-1e-9)/fps
        if first+.35+.9>duration:
            continue
        # Reuse the strict renderer's source/plate audits, not a descriptive
        # manifest's self-reported 'verified' boolean.
        from live_dom_depth_plane import load_live_dom_plane
        config={"id":candidate.get("id"),"eventIndex":relevant["index"],
                "startAt":first,
                "peakAt":math.ceil((first+.48)*fps)/fps,
                "endAt":math.floor((duration-.04)*fps)/fps,
                "liftPx":0,"scale":1}
        try:
            validated=load_live_dom_plane(config,raw,source,manifest,
                source_size=tuple(size),fps=int(fps),duration=duration)
        except (ValueError,KeyError,RuntimeError,subprocess.SubprocessError):
            continue
        verified_layers.append({
            "id":validated.id,"nativeSourceRect":list(validated.rect),
            "firstPairedNativeFrame":validated.first_frame,
            "availableAtSeconds":validated.start_at,
            "evidenceEventIndex":validated.event_index,
            "cleanPlateSha256":validated.plate_sha256,
            "captureMethod":"same-browser-clock DOM-hidden verified clean plate",
            "opaqueSurface":True,
            "boundedMotion":{"liftPx":[0,160],"scale":[1,1.18],
                             "shadowStrength":[0,.6]},
            "requiresRealSource":True})
    # Multi-layer mode requires a single, source-frame-synchronous actual
    # Chromium clean plate with every independently moving original UI
    # element removed. Never advertise group syntax from a descriptive
    # sidecar without reconstructing and passing renderer provenance gates.
    verified_group=None
    candidate_group=raw.get("domPlanes")
    if (isinstance(candidate_group,list) and 2<=len(candidate_group)<=3 and
        all(isinstance(p,dict) and p.get("captureMethod")==
            "playwright-visible-then-multiple-DOM-elements-hidden-and-restored"
            for p in candidate_group)):
        paired=candidate_group[0].get("firstPairedFrame")
        for ev in events:
            if (type(paired) is not int or paired<0 or
                paired/fps>duration-1.60 or
                ev["sourceTime"]["confirmedResultAt"]+.12>paired/fps):
                continue
            first=math.ceil(max(paired/fps,
                         ev["sourceTime"]["confirmedResultAt"]+.12)*fps-1e-8)/fps
            end=math.floor((duration-.01)*fps)/fps
            peak=math.ceil((first+.55)*fps-1e-8)/fps
            if peak-first<.35 or end-peak<.9:continue
            configs=[{"id":rec.get("id"),"eventIndex":ev["index"],
                      "startAt":first,"peakAt":peak,"endAt":end,
                      "liftPx":0,"scale":1} for rec in candidate_group]
            try:
                from live_dom_multi_plane import load_live_dom_planes
                group=load_live_dom_planes(
                    configs,raw,source,manifest,
                    source_size=tuple(size),fps=int(fps),duration=duration)
            except (ValueError,KeyError,RuntimeError,subprocess.SubprocessError):
                continue
            verified_group={
                "ids":[m.id for m in group.members],
                "measuredNativeSourceRects":[list(m.rect) for m in group.members],
                "verifiedEventIndex":ev["index"],
                "firstPairedNativeFrame":group.first_frame,
                "earliestMotionAtSeconds":first,
                "latestMotionEndSeconds":end,
                "cleanPlateSha256":group.plate_sha256,
                "sourceSha256":group.source_sha256,
                "mustSelectAllIds":True,
                "nativeFps":fps,
                "boundedMotion":{"liftPx":[0,160],
                    "driftXPx":[-120,120],
                    "scale":[1,1.18],"scaleWithSourceTrueHeroCenter":[1,1.55],
                    "heroCenterNormalized":[.14,.86],
                    "shadowStrength":[0,.6]},
                "sourceTrueScreenAnchoredHeroAvailable":True,
                "independentStartPeakEndTimes":True,
                "realOpaqueElementSurfaces":True,
                "verifiedSynchronizedSameBrowserFrames":True
            }
            break
    pointer=source_pointer_capabilities(raw,size)
    return {
        "schema":"sauce-director-available-capabilities-v1",
        "brief":brief.strip(),
        "actualCapture":{"sourceSha256":_hash(source),"manifestSha256":_hash(manifest),
           "resolution":size,"nativeFps":fps,"durationSeconds":duration,
           "sourceCursorless":True,"verifiedEvents":events,
           "pointerProvenance":pointer,
           "verifiedLiveDomPlanes":verified_layers,
           "verifiedLiveDomPlaneGroup":verified_group},
        "creativeInstruction":"Direct a compelling, source-true cinematic UI film. "
           "You may choose any exposed effect and design original camera/keyframe timings. "
           "Prior references are stylistic only; never copy old product states. "
           "The final encoded movie, not syntax, will be evaluated visually.",
        "availableEffects":{
            "regularCamera":"camera keys with wide/verified event targets; no source repainting",
            "studioStage":"opt-in source-derived perspective stage with source-only UI "
              "pixels, material grain, true recorded pointer, bounded depth, perspective camera, "
              "verified event lighting or sustained source-pixel appearance trigger, source-derived "
              "shadow/reflection, native-frame source-true editorial camera hard cuts (camera cut=true, "
              "startAt=at, at aligned to source FPS, maximum 3, >=0.35s apart), "
              "overview/detail payoff clipping guard",
            **({"sourceCursorSpringCamera":
                 "OPTIONAL: studioStage.motion.profile=reference-spring plus "
                 "motion.follow={mode:source-cursor-spring,eventIndices:[verified source indices],"
                 "responseSeconds:.39,strength:.22,deadzone:.10,maxOffset:.055}; "
                 "spring drives the view from actual time-stamped browser cursor samples "
                 "ONLY near verified actions, never fakes a cursor path. "
                 "motion.immersive=true is available only with cloud_shadow_v1 "
                 "and permits source-safe physical camera viewScale 1..1.8 "
                 "on studioStage.camera keys. Increase viewScale after a real "
                 "recorded mouse approach or verified result, use sufficient "
                 "transition time to pass the 45px/frame source-motion gate, "
                 "then return to viewScale=1 with at least a brief wide hold. "
                 "The source UI is reprojected from native capture; verified "
                 "clicks and majority of resultRect MUST stay on-screen. "
                 "Prefer a moderate close-up rather than clipping the product."}
               if pointer["sourceCursorSpringAvailable"] else {}),
            "glassLoupe":"optional event-driven optical magnifier; do not use merely for decoration",
            "composition":"optional frozen genuine-UI pixel isolation, not live DOM layering",
            **({"domPlane":"OPTIONAL: independently animate one REAL DOM foreground from genuine "
                          "native-frame source/clean-plate browser screenshots with strict "
                          "hash+pixel-mismatch provenance. Only IDs in actualCapture."
                          "verifiedLiveDomPlanes exist; activate strictly after the proven "
                          "result and first paired frame, lift 0..160px, scale<=1.18 and "
                          "return to the original interface without fake pixels."}
               if verified_layers else {}),
            **({"domPlanes":"OPTIONAL: jointly animate exactly two or three independently "
                    "captured genuine UI elements, all source-natively tied to one "
                    "simultaneously DOM-hidden actual Chromium background plate. "
                    "Only IDs in actualCapture.verifiedLiveDomPlaneGroup are valid. "
                    "Use studioStage and independent native-frame-aligned startAt, "
                    "peakAt and endAt per element. Optionally add normalized "
                    "heroCenter=[x,y] to each REAL layer for genuine screen-anchored "
                    "foreground features: their original video pixels stay sharp "
                    "and independent while the application camera recedes; "
                    "when two screen-anchored hero cards hold together, "
                    "the whole browser source must recede to <=62% of the "
                    "1920x1080 canvas area, or the editorial preflight will "
                    "reject a flat composition. Do not substitute fake UI. "
                    "heroCenter accepts only [.14,.86], and only then does "
                    "source-backed scale allow up to 1.55x. The foreground must "
                    "always remain fully in frame and distinct from other cards. "
                    "The film MUST preserve real "
                    "result colors, original type and context. No fabricated "
                    "UI, recycled clean plate from another frame, or fake transitions."}
                if verified_group is not None else {})
        },
        "modelOutputInstructions":{
            "return":"One JSON object conforming exactly to included JSON Schema",
            "sourceSha256":"Use exact actualCapture.sourceSha256",
            "manifestSha256":"Use exact actualCapture.manifestSha256",
            "durationSeconds":"Do not exceed actualCapture.durationSeconds",
            "camera":"Omit when studioStage.camera takes over. Otherwise supply validated 2D keys.",
            "studioStage":"Choose only if the creative direction benefits. "
                "IMPORTANT CAMERA COORDINATE SEMANTICS: center=[x,y] means the "
                "normalized OUTPUT PLACEMENT OF THE ENTIRE SOURCE WINDOW, NOT "
                "the place in the source UI the camera should look at. For "
                "source-verified interactions, use focus='event:N:target' for "
                "the click and focus='event:N:result' for the payoff; the "
                "engine computes projection from the exact measured bounds. "
                "Never use center=[.2,.3] to mean 'look at top left of app'. "
                "Use studioStage.lighting.eventIndex and an appropriate verified payoff. "
                "Set trigger='appearance' only for a plausible visual color change. "
                "For decisive action-to-result shot transitions, camera keys may use cut=true "
                "ONLY at native frame aligned times with startAt=at. Candidate click/result "
                "native-frame cut timestamps are supplied per genuine verified event. "
                "Protect action target, preserve legible final payoff and do not require "
                "hard cuts where an authentic slow hold is more cinematic. "
                "When actualCapture.pointerProvenance.sourceCursorSpringAvailable is true, "
                "you may opt in to studioStage.motion.profile=reference-spring "
                "and motion.follow for causal critically-damped mouse following; "
                "to move INTO the physical floating window use the original "
                "cloud_shadow_v1 stage plus motion.immersive=true and per-key "
                "viewScale 1..1.8, maintaining source-verified geometry. "
                "Never fake cursor movement, paint substitute UI or use a large "
                "zoom where the resulting modal/label becomes illegible.",
            "domPlanes":"Only when actualCapture.verifiedLiveDomPlaneGroup exists; "
                "SOURCE-TRUE HERO GRAMMAR: After verified result, optionally "
                "detach each genuine DOM card and hold it at heroCenter [x,y] "
                "while its browser source recedes in studioStage.camera. "
                "Each card must stay fully readable, with original text, "
                "charts and source palette unchanged. Lift different cards "
                "on separate beats, then return them to native positions. "
                "must select ALL IDs, with source-FPS-aligned times. Choose independent "
                "rhythm with separately staggered readable lifts if it improves "
                "real product comprehension. Keep dominant UI legible and avoid "
                "turning meaningful actions into miniature screen shots.",
            "domPlane":"Only if a verified source-paired DOM plane exists and "
                "your film benefits from a genuine independent element. "
                "Set id from actualCapture.verifiedLiveDomPlanes, eventIndex "
                "from evidence, frame-aligned startAt/peakAt/endAt. "
                "Requires studioStage; never invent a plate, card, content or "
                "fake underlay. A readable 0.5s hold and late return work well.",
            "audio":"For an audible multi-action story, choose "
                "audio.mode=eventFoley and eventIndices=[all genuine narrated "
                "source event indices] in chronological order. Single-event "
                "films retain eventIndex. These synths are tied to ORIGINAL "
                "recorded press/result times, not invented new interactions. "
                "Use source-backed eventFoley on a genuine verified click "
                "when the requested product demo is audible. mode=clean means "
                "the FINAL VIDEO HAS NO AUDIO, not a quietly polished soundtrack; "
                "the encoded film supervisor will reject a missing audio stream. "
                "Never invent sounds for unrecorded interactions or add music.",
            "cursor":"For studioStage and flat camera choose ONLY the modes listed "
                     "in actualCapture.pointerProvenance.allowedCursorModesForStudio; "
                     "never invent cursor motion. The legacy glassLoupe may use "
                     "separate verified event-local pointer samples when present.",
            "sourceTruth":"Never add fabricated buttons, text, results, future-state motion, "
                "unverified click targets, or invented pointer samples.",
            "narrative":"For a genuine multi-action capture and a client brief "
                "requiring its complete workflow, show each observed result "
                "clearly and in order, with original recorded cursor approach "
                "and readable result holds. Source camera anchors event:i:result "
                "are available for each VERIFIED event; do not manufacture an "
                "extra action, price or missing result.",
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
