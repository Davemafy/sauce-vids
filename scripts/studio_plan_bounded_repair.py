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
from fractions import Fraction


def _digest(data):
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(",",":")).encode()).hexdigest()


def normalize_generated_studio_plan(raw, *, manifest=None, source_path=None,
                                    source_size=None, fps=None, output_size=(1920,1080)):
    if not isinstance(raw,dict):
        raise ValueError("Film plan must be an object")
    source=copy.deepcopy(raw)
    corrected=copy.deepcopy(raw)
    repairs=[]
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
        source_path=a.source,source_size=size,fps=fps)
    a.out.write_text(json.dumps(corrected,indent=2)+"\n")
    a.receipt.write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps({"repairCount":len(receipt["changes"]),"creativeApproval":False,
                      "requiresValidator":True}))


if __name__=="__main__":main()
