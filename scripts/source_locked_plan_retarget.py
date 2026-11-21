#!/usr/bin/env python3
"""Retarget saved verified source-locked camera *roles* to a new same-URL capture.

This is an offline research adapter; it NEVER admits rejected research films
to an active production/gold reference pool. It verifies ORIGINAL and NEW
source hashes, identical original public URL/action semantics and geometry,
then remaps only source-relative camera times. All UI is from the NEW
real original MP4 and the strict unchanged film renderer remains authority.

Does not retarget between distinct sites or invent source/video frames.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,math
from pathlib import Path

def digest(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):h.update(block)
    return h.hexdigest()

def _verify_capture(plan,manifest,source,manifest_path):
    if (plan.get("sourceSha256")!=digest(source) or
            plan.get("manifestSha256")!=digest(manifest_path)):
        raise ValueError("Source-bound film plan contradicts original video/manifests")
    if not isinstance(manifest,dict) or not isinstance(manifest.get("events"),list):
        raise ValueError("No verified original source events")
    actual=manifest.get("provenance",{}).get("originalSourceSha256")
    if actual!=digest(source):
        raise ValueError("Capture's source provenance not independently verified")
    if not manifest.get("cursorless") or len(manifest.get("pointer_samples",[]))<45:
        raise ValueError("Missing authentic recorded pointer approach")
    events=manifest["events"]
    if len(events)!=3:raise ValueError("Only identical 3-step source stories can be retargeted")
    for e in events:
        if (e.get("kind")!="tab_switch" or
                not e.get("evidence") or
                not isinstance(e.get("observedPublicAction"),str) or
                any(type(e.get(k)) not in (int,float) or not math.isfinite(e[k])
                    for k in ("start","t","end")) or
                not e["start"]<e["t"]<=e["end"]):
            raise ValueError("Missing genuine source-verified action grammar")
    return events

def _interp(anchors,t):
    if t<=anchors[0][0]:return anchors[0][1]
    if t>=anchors[-1][0]:return anchors[-1][1]
    for (x0,y0),(x1,y1) in zip(anchors,anchors[1:]):
        if x0<=t<=x1:
            return y0+(t-x0)*(y1-y0)/(x1-x0)
    raise ValueError("Unmappable recorded clock")

def retarget(plan,old_manifest,new_manifest,old_source,new_source,
             old_manifest_path,new_manifest_path,*,fps=60):
    from source_action_cut_budget import fit_verified_result_cut_budget
    old=_verify_capture(plan,old_manifest,old_source,old_manifest_path)
    # New film source is independently hash verified through an authenticated
    # original Chrome receipt; no new price/tab labels invented.
    new_claim={"sourceSha256":digest(new_source),
               "manifestSha256":digest(new_manifest_path)}
    new=_verify_capture(new_claim,new_manifest,new_source,new_manifest_path)
    if old_manifest.get("source")!=new_manifest.get("source"):
        raise ValueError("Research-only retarget is SAME EXACT public URL")
    if [x["observedPublicAction"] for x in old]!=[
            x["observedPublicAction"] for x in new]:
        raise ValueError("Original and new site result semantics differ")
    duration=plan.get("durationSeconds")
    if type(duration) not in (int,float) or abs(duration-new_manifest["duration"])>1e-6:
        raise ValueError("Source-relative retarget presently requires equal capture length")
    anchors=[(0.,0.)]
    for a,b in zip(old,new):
        anchors.append((a["start"],b["start"]))
        anchors.append((a["t"],b["t"]))
    anchors.append((float(duration),float(new_manifest["duration"])))
    if any(x1<=x0 or y1<=y0 for (x0,y0),(x1,y1) in zip(anchors,anchors[1:])):
        raise ValueError("Cannot retarget nonmonotonic real source timeline")
    output=copy.deepcopy(plan)
    output["sourceSha256"]=digest(new_source)
    output["manifestSha256"]=digest(new_manifest_path)
    keys=output.get("studioStage",{}).get("camera",[])
    if not isinstance(keys,list) or len(keys)<2:
        raise ValueError("Original director did not choose an original studio camera")
    diffs=[]
    for i,key in enumerate(keys):
        if not isinstance(key,dict) or type(key.get("at")) not in (int,float):
            raise ValueError("Invalid original model camera")
        before=float(key["at"])
        mapped=_interp(anchors,before)
        if key.get("cut") is True:
            # An old model result source-frame cut may be up to one native
            # frame AFTER DOM confirmation. Always map to the NEW verified
            # source-result frame, never before the new evidence exists.
            m=key.get("focus")
            if isinstance(m,str) and m.startswith("event:"):
                parts=m.split(":")
                if (len(parts)==3 and parts[1].isdigit() and
                    int(parts[1])<len(new) and parts[2] in ("target","result")):
                    e=new[int(parts[1])]
                    event_t=e["start"] if parts[2]=="target" else e["t"]
                    mapped=math.ceil(event_t*fps-1e-8)/fps
            else:
                mapped=round(mapped*fps)/fps
            key["at"]=round(mapped,9)
            key["startAt"]=key["at"]
        else:
            key["at"]=round(mapped,9)
            if "startAt" in key:
                key["startAt"]=round(_interp(anchors,float(key["startAt"])),9)
        diffs.append({"keyIndex":i,"from":before,"to":key["at"],
                      "cameraFocus":key.get("focus","wide"),
                      "sourceNativeCut":bool(key.get("cut"))})
    # Reuse source-safe real cursor grammar. Old Gemini research may exceed
    # renderer's 3-cut constraint. This separate audited pass may ONLY remove
    # matched ACTION cut keys; it leaves all verified RESULT cuts as chosen.
    output,cut_changes=fit_verified_result_cut_budget(output,new_manifest,fps,source_size=(new_manifest["capture_rect"]["width"],new_manifest["capture_rect"]["height"]))
    record={"schema":"sauce-source-locked-same-url-research-retarget-v1",
            "oldSourceSha256":digest(old_source),
            "newSourceSha256":digest(new_source),
            "oldManifestSha256":digest(old_manifest_path),
            "newManifestSha256":digest(new_manifest_path),
            "sourceUrl":old_manifest["source"],
            "originalActualEvents":[e["observedPublicAction"] for e in old],
            "modelStatus":"SAVED_RESEARCH_ONLY_NOT_GOLD",
            "originalCreativeApproval":False,
            "retargetedCreativeApproval":False,
            "sourcePixelsInvented":False,
            "eventSourceTimesChanged":False,
            "cameraTimingRemap":diffs,
            "redundantTargetCutRemovals":cut_changes,
            "newPlanSha256":hashlib.sha256(
                json.dumps(output,sort_keys=True,separators=(",",":")).encode()).hexdigest()}
    return output,record

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ("plan","old-source","old-manifest","new-source","new-manifest","output","receipt"):
        p.add_argument("--"+k,type=Path,required=True)
    a=p.parse_args()
    if a.output.exists() or a.receipt.exists():
        raise ValueError("Never overwrite source or prior creative evidence")
    plan=json.loads(a.plan.read_text())
    old=json.loads(a.old_manifest.read_text())
    new=json.loads(a.new_manifest.read_text())
    created,record=retarget(plan,old,new,a.old_source,a.new_source,
                            a.old_manifest,a.new_manifest)
    a.output.parent.mkdir(exist_ok=True,parents=True)
    a.output.write_text(json.dumps(created,indent=2)+"\n")
    a.receipt.write_text(json.dumps(record,indent=2)+"\n")
    print(json.dumps({"source":new["source"],
       "sourceTrueNativeEvents":record["originalActualEvents"],
       "retargeted":True,"researchOnly":True,
       "cutBudgetRepairCount":len(record["redundantTargetCutRemovals"])}))
if __name__=="__main__":main()
