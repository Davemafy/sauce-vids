#!/usr/bin/env python3
"""Audited, *mechanical-only* normalization for generated Sauce film JSON.

Never invent creative direction, source hashes, browser events, geometry or
timing. Only remove unambiguous redundant defaults and fit the FINAL camera
scale to the model's own requested overview if backed by genuine source.
All changes are audited, optional and must pass the unchanged real validator.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import math
from fractions import Fraction


def _digest(data):
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(",",":")).encode()).hexdigest()


def normalize_generated_studio_plan(raw, *, manifest=None, source_path=None,
                                    source_size=None, fps=None,
                                    output_size=(1920,1080),manifest_path=None,
                                    enforce_cloud_stage=False):
    if not isinstance(raw,dict):
        raise ValueError("Film plan must be an object")
    source=copy.deepcopy(raw)
    corrected=copy.deepcopy(raw)
    repairs=[]
    if (enforce_cloud_stage and "studioStage" in corrected and
            "domPlanes" not in corrected and "domPlane" not in corrected):
        # Stage look is a controlled renderer preset, NOT generated art direction.
        # The already-verified independently lifted DOM-plane mode is an
        # incompatible special capture. Keep its proven compositor behavior
        # until it has its own fixed-stage physical-window integration.
        stage=corrected["studioStage"]
        if not isinstance(stage,dict):
            raise ValueError("Cannot enforce a fixed stage over invalid JSON")
        previous=stage.get("stagePreset")
        # Keep an explicitly source-safe cloud environment. Do not
        # force the owner's new sky-behind-window preset back to ink-blue.
        if previous not in ("cloud_shadow_v1","cloud_window_sky_v1","cloud_window_fullglass_v1"):
            stage["stagePreset"]="cloud_shadow_v1"
            repairs.append({"field":"studioStage.stagePreset",
                  "from":previous,"to":"cloud_shadow_v1",
                  "reason":"Owner-locked sky, fixed rounded floating window and depth"})
    if "studioStage" not in corrected:
        return corrected,{"schema":"sauce-bounded-studio-repair-v1","sourcePlanSha256":_digest(source),
                          "repairedPlanSha256":_digest(corrected),"changes":repairs,
                          "creativeApproval":False}
    # Only one unambiguous compatibility correction: a physical in-frame
    # studio uses the fullscreen OUTPUT stream, not the old decorated
    # browser-window presentation. Do not discard a configured window.
    if (corrected.get("presentation")=="window" and "window" not in corrected
            and "glassLoupe" not in corrected and "composition" not in corrected):
        corrected["presentation"]="fullscreen"
        repairs.append({"field":"presentation","from":"window","to":"fullscreen",
                        "reason":"studioStage already owns the projected physical screen"})
    for i,key in enumerate(corrected.get("studioStage",{}).get("camera",[])):
        if isinstance(key,dict) and key.get("easing")=="quintic":
            # Studio camera has exactly one interpolation algorithm: quintic.
            # Removing a redundant explicit selection changes zero pixels.
            del key["easing"]
            repairs.append({"field":f"studioStage.camera[{i}].easing",
                            "from":"quintic","to":None,
                            "reason":"Renderer already uses quintic easing exclusively"})
        if (isinstance(key,dict) and key.get("focus","wide")!="wide"
                and key.get("center")==[.5,.5]):
            # A redundant default window placement conflicts with the more
            # explicit verified event-focus contract; remove only the default.
            del key["center"]
            repairs.append({"field":f"studioStage.camera[{i}].center",
                            "from":[.5,.5],"to":None,
                            "reason":"Verified event focus supersedes default whole-window center"})

    if manifest is not None and "studioStage" in corrected and (
        corrected.get("cursor")=="recorded" and "glassLoupe" not in corrected):
        from film_director_capabilities import source_pointer_capabilities
        size=manifest.get("capture_rect") or {}
        try:dimensions=(int(size["width"]),int(size["height"]))
        except (KeyError,TypeError,ValueError):
            raise ValueError("Cannot verify source pointer provenance")
        if not source_pointer_capabilities(manifest,dimensions)["recordedPointerTrackAvailable"]:
            # We can safely REMOVE an unsupported drawn cursor; never synthesize
            # a track, guess its position, or alter any filmed interaction.
            corrected["cursor"]="none"
            repairs.append({"field":"cursor","from":"recorded","to":"none",
                 "reason":"No genuine global pointer track; cannot render fictional cursor"})
    # A complete 3-action genuine cursor recording may induce Gemini to
    # request target AND verified-result hard cuts (six total). The existing
    # source-verified 3-cut studio limit is non-negotiable. Only a complete
    # one-to-one native-frame 3x ACTION→RESULT pattern may mechanically drop
    # redundant action target keys, preserving original RESULT cuts exactly.
    if (manifest is not None and source_path is not None and fps is not None
            and isinstance(corrected.get("studioStage"),dict)):
        from source_action_cut_budget import fit_verified_result_cut_budget
        corrected,compiled=fit_verified_result_cut_budget(corrected,manifest,fps,source_size=source_size)
        repairs.extend(compiled)
    # For a smooth camera transition toward a VERIFIED real result,
    # Gemini may leave startAt implicit (= prior key), one original source
    # frame BEFORE that result is visibly present. The unchanged renderer
    # correctly rejects anticipatory framing. Only if decoded SOURCE PIXELS
    # prove the real result appears within two native frames of that onset
    # can we delay a transition start; the chosen destination, look, cut
    # timing, focus and native UI pixels remain intact. No model redesign.
    if (manifest is not None and source_path is not None and
            source_size is not None and fps is not None and
            isinstance(corrected.get("studioStage"),dict)):
        from spatial_studio_stage import detect_appearance_onset
        stage=corrected["studioStage"]
        keys=stage.get("camera",[])
        light=stage.get("lighting",{})
        if isinstance(keys,list) and isinstance(light,dict):
            events=manifest.get("events",[])
            for i,key in enumerate(keys):
                if i==0 or not isinstance(key,dict):
                    continue
                focus=key.get("focus","")
                parts=focus.split(":") if isinstance(focus,str) else []
                if (len(parts)!=3 or parts[0]!="event" or
                    not parts[1].isdigit() or parts[2] not in ("result","component") or
                    key.get("cut") is True):
                    continue
                event_index=int(parts[1])
                if event_index>=len(events) or event_index!=light.get("eventIndex"):
                    continue
                current=key.get("startAt",keys[i-1].get("at"))
                at=key.get("at")
                if type(current) not in (int,float) or type(at) not in (int,float):
                    continue
                evidence=detect_appearance_onset(
                    source_path,source_size,events[event_index],fps)
                if evidence.get("method") not in (
                        "sustained-pixel-evidence","sustained-source-pixel-change"):
                    continue
                actual=float(evidence["time"])
                delta=actual-current
                if not (1e-6<delta<=2.01/fps and actual<at-.1):
                    continue
                if light.get("trigger","verified")!="appearance":
                    previous=light.get("trigger","verified")
                    light["trigger"]="appearance"
                    repairs.append({
                        "field":"studioStage.lighting.trigger","from":previous,
                        "to":"appearance",
                        "reason":"Source-proven result visible within two native "
                                 "frames of model camera transition start; "
                                 "same light source, no imaginary state",
                        "sourceEvidence":evidence})
                key["startAt"]=round(actual,9)
                repairs.append({
                    "field":f"studioStage.camera[{i}].startAt",
                    "from":current,"to":key["startAt"],
                    "reason":"Wait for genuine source-visible product result "
                             "before starting the model's unchanged easing",
                    "sourceEvidence":evidence})
    # Conservative source-timed correction: the model sometimes requests a
    # verified RESULT cut exactly on the press frame, one 25fps source frame
    # before the original product result is truly visible. The actual encoded
    # source detector (never guessed DOM latency) may delay this exact cut by
    # at most 2 SOURCE FRAMES. All previous/next cuts, scene content, source
    # hashes and event time are immutable; broader mistakes remain rejected.
    if (manifest is not None and source_path is not None and
            source_size is not None and fps is not None and
            isinstance(corrected.get("studioStage"),dict)):
        from spatial_studio_stage import detect_appearance_onset
        camera=corrected["studioStage"].get("camera",[])
        light=corrected["studioStage"].get("lighting",{})
        if isinstance(camera,list) and isinstance(light,dict):
            if light.get("trigger","verified") in ("appearance","verified"):
                for i,key in enumerate(camera):
                    if i==0 or not isinstance(key,dict) or key.get("cut") is not True:
                        continue
                    focus=key.get("focus")
                    chunks=focus.split(":") if isinstance(focus,str) else []
                    if (len(chunks)!=3 or chunks[0]!="event" or
                            not chunks[1].isdigit() or chunks[2] not in ("result","component")):
                        continue
                    event_i=int(chunks[1])
                    events=manifest.get("events",[])
                    if event_i>=len(events) or not isinstance(events[event_i],dict):
                        continue
                    source_onset=detect_appearance_onset(source_path,source_size,
                                                        events[event_i],fps)
                    if source_onset.get("method") not in (
                           "sustained-pixel-evidence","sustained-source-pixel-change"):
                        continue
                    old_at=key.get("at")
                    if type(old_at) not in (int,float) or not math.isfinite(old_at):
                        continue
                    onset=round(float(source_onset["time"]),6)
                    drift=onset-float(old_at)
                    if not (1e-7<drift<=2.01/fps):
                        continue
                    # No overlap with next creative key or unrelated hard cuts.
                    if (onset>=float(camera[i+1].get("at",-1)) if i+1<len(camera)
                            else False):
                        continue
                    start=key.get("startAt",float(camera[i-1].get("at",0)))
                    if abs(float(start)-float(old_at))>1e-6:
                        continue
                    if light.get("trigger","verified")!="appearance":
                        # The model demands an earlier source-result camera cut
                        # yet chose a later DOM-confirmation lighting clock.
                        # The exact source image itself proves this is a real
                        # visible change; align the existing appearance trigger
                        # rather than fake a future result.
                        previous=light.get("trigger","verified")
                        light["trigger"]="appearance"
                        repairs.append({
                            "field":"studioStage.lighting.trigger",
                            "from":previous,"to":"appearance",
                            "reason":"Source-proven genuine result was already visible; "
                                     "match requested source-frame camera cut",
                            "sourceEvidence":source_onset})
                    key["at"]=onset
                    key["startAt"]=onset
                    repairs.append({
                        "field":f"studioStage.camera[{i}].sourceCutTime",
                        "from":round(float(old_at),6),"to":onset,
                        "reason":"Real recorded result onset after press; source-verified "
                                 "native-frame cut shift <=2 frames, no synthetic state",
                        "sourceEvidence":source_onset,
                        "nativeFrame":int(round(onset*fps))})
    # Snap only model-chosen grouped DOM motion times to nearest NATIVE source
    # frame: less than half a frame change, no alterations to original model
    # creative order/offset, no source retiming, no invented UI. Strict result
    # bounds and holds still validated by real renderer.
    if fps is not None and type(fps) in (int,float) and fps>0:
        grouped=corrected.get("domPlanes")
        if isinstance(grouped,list) and 2<=len(grouped)<=3:
            for i,plane in enumerate(grouped):
                if not isinstance(plane,dict):continue
                for field in ("startAt","peakAt","endAt"):
                    at=plane.get(field)
                    if type(at) not in (int,float) or not math.isfinite(at):
                        continue
                    snapped=round(at*fps)/fps
                    if abs(snapped-at)>1e-8 and abs(snapped-at)<=.501/fps:
                        plane[field]=round(snapped,9)
                        repairs.append({"field":f"domPlanes[{i}].{field}",
                            "from":at,"to":plane[field],
                            "reason":"Nearest original source frame for live DOM plane",
                            "frame":int(round(snapped*fps))})
    # Only adjust a slightly over-late *real DOM spatial lift* peak when the
    # native source ends too soon to complete the strict 0.9s return. Preserve
    # the original start, end, real product frame and model's hero position.
    # This is an objective ≤0.20s earlier native-frame peak, never a hidden
    # creative rewrite or permission to skip required reading/return time.
    if fps is not None and type(fps) in (int,float) and fps>0:
        group=corrected.get("domPlanes")
        if isinstance(group,list) and 2<=len(group)<=3:
            for i,plane in enumerate(group):
                if not isinstance(plane,dict):continue
                start=plane.get("startAt")
                peak=plane.get("peakAt")
                end=plane.get("endAt")
                if any(type(x) not in (int,float) or not math.isfinite(x)
                       for x in (start,peak,end)):
                    continue
                if .70<=end-peak<.9-1e-7:
                    new_peak=math.floor((end-.9)*fps+1e-7)/fps
                    if (0<peak-new_peak<=.201 and
                        new_peak-start>=.35-1e-6):
                        plane["peakAt"]=round(new_peak,9)
                        repairs.append({
                            "field":f"domPlanes[{i}].peakAt",
                            "from":peak,"to":plane["peakAt"],
                            "reason":"Bounded native-frame spatial peak advance "
                                     "to ensure authentic foreground UI returns "
                                     "before unchanged source film ends",
                            "nativeFrame":round(new_peak*fps)})
    # Optional *objective* overview fit. The model already chose 'overview',
    # which means preserving most of the genuine product window. Shrink ONLY
    # the last camera scale by at most 0.22, never change focus, yaw, pitch,
    # camera time, authentic source pixels, or earlier creative shots.
    if (manifest is not None and source_path is not None and
            source_size is not None and fps is not None and
            corrected.get("presentation")=="fullscreen" and
            isinstance(corrected.get("studioStage"),dict)):
        stage=corrected["studioStage"]
        keys=stage.get("camera",[])
        payoff=stage.get("payoff",{})
        if (isinstance(keys,list) and len(keys)>=2 and isinstance(keys[-1],dict)
                and isinstance(payoff,dict) and payoff.get("mode","overview")=="overview"):
            from spatial_studio_stage import load_studio_stage
            current_scale=keys[-1].get("scale")
            if type(current_scale) in (int,float) and .77<=current_scale<=1.55:
                def valid(scale):
                    variant=copy.deepcopy(stage)
                    variant["camera"][-1]["scale"]=round(float(scale),5)
                    try:
                        st=load_studio_stage(variant,manifest,source_path,source_size,
                                             output_size,float(corrected["durationSeconds"]),fps)
                        return True,st
                    except ValueError as exc:
                        return False,str(exc)
                ok,detail=valid(current_scale)
                if not ok and "Final studio overview clips" in str(detail):
                    low=max(.55,float(current_scale)-.22)
                    works,low_stage=valid(low)
                    if works:
                        high=float(current_scale)
                        for _ in range(5):
                            trial=(low+high)/2
                            hit,_=valid(trial)
                            if hit:low=trial
                            else:high=trial
                        safe=max(float(current_scale)-.22,low-.006)
                        works,st=valid(safe)
                        if works:
                            new=round(safe,5)
                            keys[-1]["scale"]=new
                            repairs.append({"field":f"studioStage.camera[{len(keys)-1}].scale",
                                "from":current_scale,"to":new,
                                "reason":"Bounded final-scale fit to model-requested overview; "
                                "actual source geometry and original event unchanged",
                                "sourceContextVisibleFraction":round(st.context_visibility(
                                    float(corrected["durationSeconds"])),4)})
    # Compile physical depth only for an actual hash-validated grouped
    # Chromium capture. The independent source-plane cinematography helper
    # keeps model source pixels, hero sizes, frame timing and final camera.
    if (manifest is not None and manifest_path is not None and
            source_path is not None and source_size is not None and fps is not None
            and corrected.get("presentation")=="fullscreen"):
        from source_hero_choreography import fit_source_hero_choreography
        corrected,compiled=fit_source_hero_choreography(
            corrected,manifest,source_path,manifest_path,source_size,
            fps,output_size=output_size)
        repairs.extend(compiled)
    return corrected,{"schema":"sauce-bounded-studio-repair-v1",
                      "sourcePlanSha256":_digest(source),
                      "repairedPlanSha256":_digest(corrected),
                      "changes":repairs,"creativeApproval":False}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--plan",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    ap.add_argument("--manifest",type=Path,
                    help="Genuine capture evidence permits removal of unsupported cursor")
    ap.add_argument("--source",type=Path,
                    help="Optional genuine MP4 enables bounded final overview fit")
    a=ap.parse_args()
    if a.plan.resolve()==a.out.resolve():
        raise ValueError("Do not overwrite model output; preserve first-pass evidence")
    if a.out.resolve().parent!=a.plan.resolve().parent:
        raise ValueError("Repaired plan remains in the same private media directory")
    real_manifest=json.loads(a.manifest.read_text()) if a.manifest else None
    size=fps=None
    if a.source:
        info=json.loads(subprocess.check_output([
            "ffprobe","-v","error","-select_streams","v:0",
            "-show_entries","stream=width,height,avg_frame_rate",
            "-of","json",str(a.source)]))
        stream=info["streams"][0]
        size=(stream["width"],stream["height"])
        fps=float(Fraction(stream["avg_frame_rate"]))
    corrected,receipt=normalize_generated_studio_plan(
        json.loads(a.plan.read_text()),manifest=real_manifest,
        source_path=a.source,source_size=size,fps=fps,
        manifest_path=a.manifest)
    a.out.write_text(json.dumps(corrected,indent=2)+"\n")
    a.receipt.write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps({"repairCount":len(receipt["changes"]),"creativeApproval":False,
                      "requiresValidator":True}))


if __name__=="__main__":main()
