#!/usr/bin/env python3
"""Audited, *mechanical-only* normalization for generated Sauce film JSON.

Never repair creative direction, source hashes, source events, camera paths,
lighting, fake geometry, timing or clipped endings. Those are hard failures.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path


def _digest(data):
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(",",":")).encode()).hexdigest()


def normalize_generated_studio_plan(raw, *, manifest=None):
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
    a=ap.parse_args()
    if a.plan.resolve()==a.out.resolve():
        raise ValueError("Do not overwrite model output; preserve first-pass evidence")
    if a.out.resolve().parent!=a.plan.resolve().parent:
        raise ValueError("Repaired plan remains in the same private media directory")
    real_manifest=json.loads(a.manifest.read_text()) if a.manifest else None
    corrected,receipt=normalize_generated_studio_plan(
        json.loads(a.plan.read_text()),manifest=real_manifest)
    a.out.write_text(json.dumps(corrected,indent=2)+"\n")
    a.receipt.write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps({"repairCount":len(receipt["changes"]),"creativeApproval":False,
                      "requiresValidator":True}))


if __name__=="__main__":main()
