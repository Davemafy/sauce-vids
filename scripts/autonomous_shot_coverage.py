#!/usr/bin/env python3
"""Deterministic multi-angle shot coverage for genuine captured Sauce events.

Not a model, visual critic, new browser capture or creative approval. Generates
camera candidates from a SHA-pinned native source and real DOM geometry,
rejects impossible shots using the original renderer, then renders at most two.
This is deliberately owner-only until the existing URL egress restrictions
are independently addressed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

import cv2
import numpy as np

from film_director_capabilities import build_contract
from source_director_preflight import preflight_source_edit
from spatial_studio_stage import load_studio_stage

RENDERER=Path(__file__).with_name("render_event_video.py")
PROFILES=(
    ("balanced",.81,1.03,1.20,False,True),
    ("proof",.80,1.00,1.30,False,True),
    ("punchy",.82,1.08,1.35,True,False),
    ("spacious",.78,.98,1.17,False,True),
    ("precise",.82,1.09,1.43,True,False),
    ("restrained",.84,1.01,1.23,False,False),
    ("cinematic",.84,1.01,1.23,False,False),
    ("cinematic_paced",.84,1.01,1.23,False,False),
)

PANEL_PROFILES=(
    ("panel_soft",.80,.94,.90,False,False),
    ("panel_context",.78,.90,.85,False,True),
    ("panel_punch",.81,1.03,.98,True,False),
    ("panel_cut",.80,.98,.94,True,False),
    ("panel_cinematic",.80,.94,.90,False,False),
)


def select_profiles(manifest,source_size):
    """A large verified UI pane needs context, not a card-scale close-up."""
    w,h=source_size
    events=manifest.get("events",[])
    fractions=[]
    for e in events:
        rect=e.get("resultRect") if isinstance(e,dict) else None
        if not isinstance(rect,dict):raise ValueError("Source result geometry missing")
        x,y,rw,rh=(float(rect[k]) for k in ("x","y","width","height"))
        if not (0<=x and 0<=y and rw>0 and rh>0 and x+rw<=w and y+rh<=h):
            raise ValueError("Source result geometry outside captured viewport")
        fractions.append(rw*rh/(w*h))
    return PANEL_PROFILES if fractions and max(fractions)>.25 else PROFILES


def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for b in iter(lambda:stream.read(1048576),b""):
            h.update(b)
    return h.hexdigest()


def frame(t,fps,ceil=False):
    n=math.ceil(t*fps-1e-8) if ceil else math.floor(t*fps+1e-8)
    return n/fps


def _pointer_start(pointer,press,*,after=0.):
    """Only this action's actual source-clock pointer approach may trigger a push."""
    before=[p for p in pointer if isinstance(p,dict) and
            type(p.get("t")) in (int,float) and after<=p["t"]<press]
    if len(before)<3:
        return None
    origin=before[0]
    for p in before[1:]:
        if math.hypot(p["x"]-origin["x"],p["y"]-origin["y"])>=12:
            return p["t"]
    return None


def make_plan(source,manifest,packet,profile):
    name,opening,target_zoom,result_zoom,hard_cuts,wide_breaks=profile
    fps=float(packet["actualCapture"]["nativeFps"])
    duration=float(packet["actualCapture"]["durationSeconds"])
    actual=json.loads(Path(manifest).read_text())
    events=actual["events"]
    verified_indices=[e["index"] for e in packet["actualCapture"]["verifiedEvents"]]
    if verified_indices!=list(range(len(events))):
        raise ValueError("Refuse event indices that did not pass captured source-evidence admission")
    pointer=actual.get("pointer_samples",[])
    if not 1<=len(events)<=4 or not packet["actualCapture"][
        "pointerProvenance"]["recordedPointerTrackAvailable"]:
        raise ValueError("Requires one to four genuine results and recorded pointer")
    keys=[{"at":0.,"scale":opening,"center":[.5,.5],"yaw":0,"pitch":0}]
    rows=[]
    for i,e in enumerate(events):
        if not (isinstance(e.get("evidence"),str) and e["evidence"].strip()
                and 0<e["start"]<=e["t"]<=duration-.6):
            raise ValueError("Missing ordered genuine action/result")
        press=float(e["start"])
        onset=frame(float(e["t"]),fps,ceil=True)
        last=keys[-1]["at"]
        # Tiny controls get full source context on approach; never zoom into a
        # result that is not yet source-visible.
        aim=frame(press-.04,fps)
        prev_result=float(events[i-1]["t"])+.04 if i else 0.
        movement=_pointer_start(pointer,press,after=prev_result)
        begin=(max(last,frame(max(0.,movement+.10),fps))
               if movement is not None else aim)
        if begin+.13<aim:
            keys.append({"at":aim,"startAt":begin,"scale":target_zoom,
                         "focus":f"event:{i}:target","yaw":0,"pitch":0})
        elif i>0 and aim-last>.55:
            # Without a recorded approach, RELEASE to full browser context
            # before the next authentic action instead of staying cropped on
            # yesterday's result. This is not a fabricated pointer zoom.
            # A stronger event-cut closeup needs longer release travel,
            # with a genuine reading hold before it opens to context.
            release_start=frame(max(last+(.48 if hard_cuts else .22),
                                    aim-(1.20 if hard_cuts else .55)),fps)
            if release_start+.10<aim:
                keys.append({"at":aim,"startAt":release_start,
                             "scale":opening+.025,"center":[.5,.5],
                             "yaw":0,"pitch":0})
        # First action with no genuine approach remains an honest wide shot.
        result_at=(onset if hard_cuts else
                   frame(onset+(.82 if name=="cinematic_paced" else .68),fps,ceil=True))
        if result_at<=keys[-1]["at"]+.02 or result_at>=duration-.25:
            raise ValueError("No safe genuine outcome camera interval")
        result_key={"at":result_at,"startAt":result_at if hard_cuts else onset,
                    "scale":result_zoom,"focus":f"event:{i}:result",
                    "yaw":0,"pitch":0}
        if hard_cuts:result_key["cut"]=True
        keys.append(result_key)
        rows.append({"eventIndex":i,"press":press,"result":e["t"],
                     "aimAt":aim,"resultFocusAt":result_at})
        if name=="cinematic_paced" and i+1<len(events):
            # Give the genuine result a reading hold, then release at a
            # reference-inspired, physically legible pace. This may finish
            # during the NEXT genuine pointer action, but the exact
            # action-time target and actual recorded pointer must remain in
            # view. Those independent projection gates run below.
            upcoming=events[i+1]
            hold_start=frame(result_at+.12,fps,ceil=True)
            release_at=frame(min(float(upcoming["start"])+.32,
                                  float(upcoming["t"])-.70),fps)
            if release_at-hold_start>=.80:
                keys.append({"at":release_at,"startAt":hold_start,
                             "scale":opening+.025,"center":[.5,.5],
                             "yaw":0,"pitch":0})
        if i+1<len(events) and wide_breaks:
            nxt=float(events[i+1]["start"])
            release=frame(nxt-.66,fps)
            if release-result_at>=.65:
                change=frame(max(result_at+.30,release-.32),fps)
                if change<release-.10:
                    keys.append({"at":release,"startAt":change,
                                 "scale":opening+.04,"center":[.5,.5],
                                 "yaw":0,"pitch":0})
    if keys[-1]["at"]>=duration-.4:
        raise ValueError("Missing final genuine payoff duration")
    # Final frame keeps the last actual result readable, with a slow
    # purposeful settle rather than automatically zooming back to a tiny UI.
    keys.append({"at":duration,"startAt":frame(max(keys[-1]["at"]+.20,
                     duration-1.25),fps),
                 "scale":min(1.48,result_zoom+.035),
                 "focus":f"event:{len(events)-1}:result",
                 "yaw":0,"pitch":0})
    if len(keys)>24:
        raise ValueError("Too many source-derived shot keys")
    plan={
      "schema":"sauce-film-plan-v1",
      "sourceSha256":sha(source),"manifestSha256":sha(manifest),
      "durationSeconds":duration,"presentation":"fullscreen",
      "cursor":"recorded",
      "audio":{"mode":"eventFoley","eventIndices":list(range(len(events))),
               "clickGain":.34,"motionGain":.17,"masterGain":.45},
      "studioStage":{
        "stagePreset":"cloud_shadow_v1",
        "camera":keys,
        "material":{"color":[30,32,38],"grain":.12},
        "lighting":{"eventIndex":len(events)-1,"trigger":"verified",
                    "intensity":.38,"transitionSeconds":.34},
        "depthPx":8,"reflection":.035,
        "payoff":{"region":f"event:{len(events)-1}:result",
                  "mode":"detail","minVisible":.94,"minContextVisible":.66}
      }}
    if "cinematic" in name:
        plan["studioStage"]["motion"]={"profile":"cinematic","shutter":.58}
    return plan,rows



def geometry_score(stage,manifest,beats,*,fps):
    """Reject unreadable or clipped shots before spending cycles on full rendering.

    This score measures ONLY source provenance/geometry, not cinematic taste.
    Projection is the exact compositor's homography, not invented CSS crops.
    """
    sw,sh=stage.source_size;ow,oh=stage.output_size
    begin_context=min(stage.context_visibility(t) for t in (0.,min(.18,stage.duration)))
    if begin_context<.76:
        raise ValueError("Opening removes recognizable source context")
    metrics=[]
    for row in beats:
        i=row["eventIndex"];e=manifest["events"][i]
        result=e["resultRect"];target=e["targetRect"]
        action_visible=stage.region_visibility(row["press"],
            (target["x"],target["y"],target["width"],target["height"]))
        sample=min(stage.duration-.02,max(row["resultFocusAt"]+.10,row["result"]+.10))
        visibility=stage.region_visibility(sample,
            (result["x"],result["y"],result["width"],result["height"]))
        if action_visible<.96 or visibility<.98:
            raise ValueError("Projected real action or outcome clipped")
        # A large DOM target can be technically visible while the authentic
        # pointer tip is outside the crop. Demand the actual recorded tip.
        recorded=[p for p in manifest.get("pointer_samples",[])
            if isinstance(p,dict) and type(p.get("t")) in (int,float)
            and abs(p["t"]-row["press"])<=.13]
        if recorded:
            near=min(recorded,key=lambda p:abs(p["t"]-row["press"]))
            if not stage.point_visible(row["press"],float(near["x"]),
                                       float(near["y"])):
                raise ValueError("Authentic recorded pointer is off-screen at action")
        if row["resultFocusAt"]+1/fps<e["t"]:
            raise ValueError("Result camera started before verified source state")
        q=stage.quad(sample)
        H=cv2.getPerspectiveTransform(np.float32([[0,0],[sw-1,0],
                    [sw-1,sh-1],[0,sh-1]]),q)
        x,y,w,h=map(float,(result["x"],result["y"],
                           result["width"],result["height"]))
        corners=np.float32([[[x,y],[x+w,y],[x+w,y+h],[x,y+h]]])
        projected=cv2.perspectiveTransform(corners,H)[0]
        width=float(np.linalg.norm(projected[1]-projected[0]))
        height=float(np.linalg.norm(projected[3]-projected[0]))
        if width<225 or height<57:
            raise ValueError("Real result appears too small at 1080p")
        metrics.append({"eventIndex":i,"actionVisibleFraction":round(action_visible,4),
            "resultVisibleFraction":round(visibility,4),
            "resultProjectedWidthPx":round(width,1),
            "resultProjectedHeightPx":round(height,1),
            "resultContextFraction":round(stage.context_visibility(sample),4)})
    widths=[m["resultProjectedWidthPx"] for m in metrics]
    context=[m["resultContextFraction"] for m in metrics]
    # Beyond ~450px width, extra enlargement often removes useful context;
    # minimize literal screen area required to read the genuine UI.
    text_readability=sum(min(1.,w/435) for w in widths)/len(widths)
    overcrop=sum(max(0.,.55-c) for c in context)/len(context)
    cuts=sum(k.cut for k in stage.camera)
    objective=round(100*text_readability +8*begin_context -
                    55*overcrop-2*cuts,3)
    return {"score":objective,"openingSourceContext":round(begin_context,4),
            "projectedEvents":metrics,"hardCuts":cuts,
            "qualityIsCreativeApproval":False}


def _render_validate(source,manifest,plan,out):
    cmd=[sys.executable,str(RENDERER),"--video",str(source),
         "--manifest",str(manifest),"--film-plan",str(plan)]
    result=subprocess.run([*cmd,"--validate-only"],capture_output=True,
                          text=True,timeout=140,check=False)
    (out/(plan.stem+"-validate.log")).write_text(
        (result.stdout+"\n"+result.stderr)[-18000:])
    return result.returncode==0


def candidate_plans(source,manifest,brief,out,*,profiles=None):
    """All candidates share one true source clock and original event IDs."""
    out=Path(out).resolve()
    source=Path(source).resolve();manifest=Path(manifest).resolve()
    packet=build_contract(source,manifest,brief)
    raw=json.loads(manifest.read_text())
    fps=packet["actualCapture"]["nativeFps"]
    size=tuple(packet["actualCapture"]["resolution"])
    if profiles is None:
        profiles=select_profiles(raw,size)
    ranked=[]
    for profile in profiles:
        name=profile[0]
        row={"name":name,"status":"rejected","sourceSha256":sha(source),
             "manifestSha256":sha(manifest)}
        try:
            plan,beats=make_plan(source,manifest,packet,profile)
            stage=load_studio_stage(plan["studioStage"],raw,source,size,
                                    (1920,1080),plan["durationSeconds"],fps)
            score=geometry_score(stage,raw,beats,fps=fps)
            row.update(score)
            if name=="cinematic_paced":
                # Reference-inspired motion bound is stricter than the
                # legacy emergency 45px/native60 tolerance. If the actual
                # browser geometry cannot fit a legible move in source time,
                # reject this candidate instead of disguising a whip-pan
                # under motion blur or changing source timestamps.
                quads=np.asarray([stage.quad(i/fps)
                     for i in range(round(stage.duration*fps))])
                displacements=np.linalg.norm(np.diff(quads,axis=0),
                                             axis=2).max(axis=1)*fps/60
                top=float(displacements.max(initial=0))
                row["motionMaxPxPerNative60Frame"]=round(top,3)
                if top>32.:
                    raise ValueError("Cinematic motion speed exceeds reference-paced "
                                     "source-verified safety bound")
            preflight=preflight_source_edit(plan,raw,source,size,fps,
                                            manifest_path=manifest)
            if preflight["findings"]:
                row.update(status="source_preflight_reject",
                    findings=[f["code"] for f in preflight["findings"]])
                ranked.append(row)
                continue
            path=out/(name+"-film-plan.json")
            path.write_text(json.dumps(plan,indent=2)+"\n")
            if not _render_validate(source,manifest,path,out):
                row["status"]="renderer_reject"
                ranked.append(row)
                continue
            row.update(status="source_verified_plan",planPath=str(path))
        except (ValueError,TypeError,KeyError,RuntimeError,
                subprocess.SubprocessError) as e:
            row.update(status="candidate_invalid",reason=type(e).__name__+
                       ": "+str(e)[:180])
        ranked.append(row)
    return sorted(ranked,key=lambda r:(r["status"]=="source_verified_plan",
               r.get("score",-1000),r["name"]),reverse=True)



def choose_diverse(ranked,max_renders):
    """If valid, compare cinematic movement to source-identical classic motion."""
    accepted=[r for r in ranked if r["status"]=="source_verified_plan"]
    if not accepted:return []
    best=accepted[0]
    motion=next((r for r in accepted if "cinematic" in r["name"]
                 and r["score"]>=best["score"]-1.5),None)
    first=motion or best
    chosen=[first]
    if motion is not None:
        baseline=next((r for r in accepted if r is not first
                       and r["hardCuts"]==first["hardCuts"]
                       and abs(r["score"]-first["score"])<.001
                       and "cinematic" not in r["name"]),None)
        if baseline is not None and max_renders>1:chosen.append(baseline)
    else:
        different=next((r for r in accepted if r is not first and
                        r["hardCuts"]!=first["hardCuts"]),None)
        if different is not None and max_renders>1:chosen.append(different)
    chosen.extend(r for r in accepted if r not in chosen)
    return chosen[:max_renders]


def run(source,manifest,out,*,brief="Demonstrate real observed product value",
        expected_source_sha256=None,expected_manifest_sha256=None,
        max_renders=2,render=True,profiles=None):
    """One autonomous, bounded editing pass. Never self-approves creative quality."""
    source=Path(source).resolve();manifest=Path(manifest).resolve()
    out=Path(out).resolve()
    if not source.is_file() or not manifest.is_file():
        raise ValueError("An actual source MP4 and verified event sidecar are required")
    if source.suffix.lower()!=".mp4" or not isinstance(brief,str) or not 4<=len(brief.strip())<=1200:
        raise ValueError("Unsafe source type or story objective")
    actual_s,actual_m=sha(source),sha(manifest)
    if expected_source_sha256 is not None and expected_source_sha256!=actual_s:
        raise ValueError("Original capture SHA256 changed")
    if expected_manifest_sha256 is not None and expected_manifest_sha256!=actual_m:
        raise ValueError("Verified event manifest SHA256 changed")
    if not isinstance(max_renders,int) or not 1<=max_renders<=3:
        raise ValueError("One to three private renders allowed")
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise ValueError("Cannot overwrite earlier owner experiments")
    out.mkdir(parents=True,exist_ok=True,mode=0o700)
    receipt={"schema":"sauce-autonomous-shot-coverage-v1",
        "sourceSha256":actual_s,"manifestSha256":actual_m,
        "source":str(source),"manifest":str(manifest),
        "renderer":"verified Sauce render_event_video.py",
        "modelRequests":0,"sourcePixelsRecreated":False,
        "creativeApproved":False,"productionReady":False,
        "status":"pending","candidates":[],"selected":None,
        "rendered":[],"observedFilmQuality":"unreviewed"}
    def save():
        (out/"coverage-receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    try:
        receipt["candidates"]=candidate_plans(source,manifest,brief,out,profiles=profiles)
        choices=choose_diverse(receipt["candidates"],max_renders)
        if not choices:
            receipt["status"]="rejected_no_source_valid_camera"
            return receipt
        for row in choices:
            if not render:
                receipt["rendered"].append({"profile":row["name"],
                         "status":"source_verified_plan_only"})
                continue
            film=out/(row["name"]+"-coverage.mp4")
            cmd=[sys.executable,str(RENDERER),"--video",str(source),
                 "--manifest",str(manifest),"--film-plan",row["planPath"],
                 "--output",str(film)]
            process=subprocess.run(cmd,capture_output=True,text=True,
                                   timeout=370,check=False)
            (out/(row["name"]+"-render.log")).write_text(
                (process.stdout+"\n"+process.stderr)[-19000:])
            result={"profile":row["name"],"status":"render_failed"}
            receipt["rendered"].append(result)
            if process.returncode!=0 or not film.is_file():continue
            from quality_preview_supervisor import analyze
            qa=analyze(film,evidence={
                "source_path":str(source),"source_sha256":actual_s,
                "event_manifest_path":str(manifest),"event_manifest_sha256":actual_m},
                seconds=min(15.,float(json.loads(manifest.read_text())["duration"])))
            (out/(row["name"]+"-encoded-qa.json")).write_text(
                json.dumps(qa,indent=2)+"\n")
            result.update({"film":str(film),"filmSha256":sha(film),
                "status":"rendered_objective_reject" if qa["verdict"]=="REJECT"
                         else "rendered_needs_human_review",
                "encodedQaVerdict":qa["verdict"],
                "encodedQaFindings":[f["code"] for f in qa["findings"]]})
        accepted=[r for r in receipt["rendered"] if
            r["status"] in ("rendered_needs_human_review","source_verified_plan_only")]
        if accepted:
            receipt["selected"]=accepted[0]["profile"]
            receipt["status"]=("source_verified_plans_only" if not render
                                else "requires_human_creative_review")
        else:
            receipt["status"]="technical_render_creative_reject"
        receipt["observedFilmQuality"]="requires_human_evaluation"
        return receipt
    finally:
        save()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",required=True,type=Path)
    p.add_argument("--manifest",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--brief",default="Demonstrate genuine source-verified product value")
    p.add_argument("--expected-source-sha256")
    p.add_argument("--expected-manifest-sha256")
    p.add_argument("--max-renders",type=int,default=2)
    p.add_argument("--validate-only",action="store_true")
    a=p.parse_args()
    res=run(a.source,a.manifest,a.out,brief=a.brief,
            expected_source_sha256=a.expected_source_sha256,
            expected_manifest_sha256=a.expected_manifest_sha256,
            max_renders=a.max_renders,render=not a.validate_only)
    print(json.dumps({"status":res["status"],"selected":res["selected"],
        "modelRequests":0,"rendered":res["rendered"],
        "creativeApproved":False},indent=2))
    if res["status"] not in ("requires_human_creative_review",
                            "source_verified_plans_only"):
        raise SystemExit(2)


if __name__=="__main__":main()
