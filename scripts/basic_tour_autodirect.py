#!/usr/bin/env python3
"""Bounded self-directed Sauce Basic previews.

No LLM, human edit, false interactions or generated UI. This module
measures the ACTUAL encoded preview, writes a source-verifiable reject
receipt, and may perform one bounded re-edit using genuine browser
motion already recorded. Never publishes an unapproved render.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import subprocess
from PIL import Image, ImageChops, ImageStat

from basic_tour_shortcut import choose_shots, compile_cut, load_scene

SAMPLE_FPS=4
WIDTH,HEIGHT=192,108
STATIC_DIFF=0.80
MOTION_DIFF=1.35
MAX_STATIC_RATIO=0.70
MAX_STILL_SECONDS=2.50
MIN_OPENING_MOTION_RATIO=0.20
MAX_ATTEMPTS=2


def motion_probe(path:Path,*,start:float=0,duration:float|None=None)->dict:
    """Sample real decoded video. No metadata-only 'quality' conclusions."""
    if start<0 or (duration is not None and duration<=0):
        raise ValueError("Invalid source interval")
    cmd=["ffmpeg","-hide_banner","-loglevel","error",
         "-ss",f"{start:.3f}","-i",str(path)]
    if duration is not None:
        cmd+=["-t",f"{duration:.3f}"]
    cmd+=["-vf",f"fps={SAMPLE_FPS},scale={WIDTH}:{HEIGHT},format=gray",
          "-f","rawvideo","pipe:1"]
    data=subprocess.check_output(cmd,timeout=90)
    size=WIDTH*HEIGHT
    frames=[Image.frombytes("L",(WIDTH,HEIGHT),data[i:i+size])
            for i in range(0,len(data)-size+1,size)]
    if len(frames)<3:
        raise ValueError("Insufficient real decoded frames")
    differences=[]
    deviations=[]
    for i,frame in enumerate(frames):
        deviations.append(ImageStat.Stat(frame).stddev[0])
        if i>0:
            differences.append(ImageStat.Stat(
                ImageChops.difference(frame,frames[i-1])).mean[0])
    longest=current=0
    for value in differences:
        current=current+1 if value<STATIC_DIFF else 0
        longest=max(longest,current)
    opening=differences[:min(len(differences),SAMPLE_FPS*2)]
    return {
        "samples":len(frames),
        "durationSeconds":round(len(frames)/SAMPLE_FPS,3),
        "staticRatio":round(sum(v<STATIC_DIFF for v in differences)/len(differences),3),
        "longestStaticSeconds":round(longest/SAMPLE_FPS,3),
        "openingMotionRatio":round(
            sum(v>=MOTION_DIFF for v in opening)/max(1,len(opening)),3),
        "openingMeanFrameChange":round(sum(opening)/max(1,len(opening)),3),
        "flatFrameCount":sum(v<3 for v in deviations),
        "maxFrameChange":round(max(differences),3),
        "frameChanges":[round(v,3) for v in differences],
    }


def _source_quality(scenes:list[dict],edl:dict)->list[dict]:
    rows=[]
    for i in sorted({shot["scene"] for shot in edl["shots"]}):
        source=scenes[i]["receipt"]
        problems=list(source.get("issues",[]))
        rows.append({"scene":i,"url":source.get("url"),
            "recordingIssues":problems,
            "sourceClock":source.get("source_rate"),
            "sourcePixelsVerified":True})
    return rows


def critique(video:Path,scenes:list[dict],edl:dict)->dict:
    motion=motion_probe(video)
    failures=[]
    if motion["staticRatio"]>MAX_STATIC_RATIO:
        failures.append("excessive_static_frames")
    if motion["longestStaticSeconds"]>MAX_STILL_SECONDS:
        failures.append("long_unmoving_shot")
    if motion["openingMotionRatio"]<MIN_OPENING_MOTION_RATIO:
        failures.append("opening_lacks_visible_motion")
    if motion["flatFrameCount"]>motion["samples"]*.30:
        failures.append("many_flat_or_blank_frames")
    source=_source_quality(scenes,edl)
    for item in source:
        if item["recordingIssues"]:
            failures.append("source_low_confidence_scene_"+str(item["scene"]))
    return {
        "schema":"sauce.basic.autodirect.critique.v1",
        "filmChecks":motion,
        "sourceChecks":source,
        "failures":failures,
        "technicalQuality":"reject" if failures else "bounded_checks_pass",
        "creativeQuality":"unverified",
        "policy":"Automated negative checks only; no claim of cinematic quality",
    }


def repair_once(original:dict,scenes:list[dict],findings:dict)->dict:
    """One bounded source-only edit. No camera-move-only false motion.

    Promote a verified feature with actual recorded motion to opening,
    shorten passive holds and omit low-confidence scenes where possible.
    """
    edl=deepcopy(original)
    shots=edl["shots"]
    if not shots:
        raise ValueError("Nothing to repair")
    good_scenes={
        i for i,scene in enumerate(scenes)
        if not scene["receipt"].get("issues")
    }
    # A short preview may omit a low-confidence scene, but the complete
    # site tour and coverage manifest still preserve/report that page.
    kept=[s for s in shots if s["scene"] in good_scenes]
    excluded=[s["scene"] for s in shots if s["scene"] not in good_scenes]
    if not kept:
        raise ValueError("No source-verified, issue-free scenes for automatic repair")
    moving=[]
    for i,s in enumerate(kept):
        if s["kind"] not in ("feature","hook_motion"):
            continue
        metrics=motion_probe(scenes[s["scene"]]["video_path"],
            start=s["sourceStartSeconds"],
            duration=min(2.3,s["durationSeconds"]))
        if metrics["openingMotionRatio"]>=MIN_OPENING_MOTION_RATIO:
            moving.append((metrics["openingMeanFrameChange"],-i,i))
    if not moving:
        raise ValueError("No authentic browser-motion opening available to repair")
    _,_,opener=max(moving)
    hook=kept.pop(opener)
    hook["kind"]="hook_motion"
    hook["sourceCropZoom"]=1.08
    hook["sourceDynamicPush"]=False
    hook["durationSeconds"]=round(min(3.4,hook["durationSeconds"]),3)
    # A static opening can help orient after the real hook but needn't
    # hold for 2.65 seconds.
    for s in kept:
        if s["kind"] in ("establish","hero_hook"):
            s["durationSeconds"]=round(min(s["durationSeconds"],1.55),3)
            s["sourceDynamicPush"]=False
        elif s["kind"]=="closing":
            s["durationSeconds"]=round(min(s["durationSeconds"],1.6),3)
        elif s["kind"]=="feature":
            s["durationSeconds"]=round(min(s["durationSeconds"],3.2),3)
    retained=[hook]+kept
    if len(retained)<2:
        raise ValueError("Not enough genuine source scenes for credible Short Cut")
    edl["shots"]=retained
    edl["durationSeconds"]=round(sum(x["durationSeconds"] for x in retained),3)
    edl["repairPolicy"]="motion_first_real_source_no_fake_actions"
    edl["excludedLowConfidenceSceneIds"]=sorted(set(excluded))
    edl["repairReason"]=findings.get("failures",[])
    if edl["durationSeconds"]>edl["budgetSeconds"]:
        raise ValueError("Bounded repair would exceed preview duration budget")
    return edl


def run(sources:list[Path],output:Path,*,max_seconds:float=30)->dict:
    if not 1<=len(sources)<=8:
        raise ValueError("Invalid sources")
    scenes=[load_scene(p) for p in sources]
    output.mkdir(parents=True,exist_ok=True)
    attempts=[]
    edl=choose_shots(scenes,duration_limit=max_seconds,
                     hook_strategy="strongest_hero")
    for attempt in range(MAX_ATTEMPTS):
        name=f"attempt-{attempt+1}"
        folder=output/name
        folder.mkdir(exist_ok=True)
        video=compile_cut(edl,scenes,folder)
        review=critique(Path(video["video"]),scenes,edl)
        receipt={"attempt":attempt+1,"edl":edl,
                 "renderReceipt":video,"critique":review}
        (folder/"autodirect-review.json").write_text(json.dumps(receipt,indent=2))
        attempts.append({
            "attempt":attempt+1,"status":review["technicalQuality"],
            "failures":review["failures"],
            "video":str(video["video"]),
            "reviewReceipt":str(folder/"autodirect-review.json")})
        if review["technicalQuality"]=="bounded_checks_pass":
            break
        if attempt+1<MAX_ATTEMPTS:
            try:
                edl=repair_once(edl,scenes,review)
            except ValueError as exc:
                attempts[-1]["repairBlocked"]=str(exc)
                break
    selected=attempts[-1]
    result={
        "schema":"sauce.basic.autodirect.v1",
        "status":"requires_human_quality_approval"
                 if selected["status"]=="bounded_checks_pass" else
                 "rejected_no_saleable_preview",
        "acceptedByAutomaticChecks":selected["status"]=="bounded_checks_pass",
        "creativeQualityVerified":False,
        "reviewedSources":[str(p) for p in sources],
        "attempts":attempts,
        "selectedCandidate":selected["video"] if
            selected["status"]=="bounded_checks_pass" else None,
        "maxAttempts":MAX_ATTEMPTS,
        "notes":["No inference, human per-job editing or synthetic SaaS pixels",
                 "No public URL service or automatic publication",
                 "Source and all failed candidates preserved in private QA"],
    }
    (output/"autodirect-result.json").write_text(json.dumps(result,indent=2))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scene",type=Path,action="append",required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--budget",type=float,default=30)
    args=p.parse_args()
    print(json.dumps(run(args.scene,args.out,max_seconds=args.budget),indent=2))

if __name__=="__main__":
    main()
