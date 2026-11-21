"""Mechanical physical-scene compiler for authentic screen-anchored DOM hero layers.

Given a model's REAL source-backed elements and existing studio timeline,
compile a bounded browser-recession beat and modest gutter correction only
when the current independent-hero scene is demonstrably flat/colliding.

No site selector, invented UI pixels, fake result, model camera coordinate
guesswork or unbounded creative rewrite. Every change is auditable and the
unchanged strict renderer must validate the result afterward.
"""
from __future__ import annotations

import copy

import cv2
import numpy as np


def _native(x,fps):
    return round(round(float(x)*fps)/fps,9)


def _group(plan,manifest,source_path,manifest_path,size,fps):
    from live_dom_multi_plane import load_live_dom_planes
    return load_live_dom_planes(plan["domPlanes"],manifest,source_path,manifest_path,
                               source_size=size,fps=int(fps),
                               duration=float(plan["durationSeconds"]))


def _stage(plan,manifest,source_path,size,fps,output_size):
    from spatial_studio_stage import load_studio_stage
    return load_studio_stage(
        plan["studioStage"],manifest,source_path,size,output_size,
        float(plan["durationSeconds"]),fps)


def _area(stage,t,output_size):
    return float(abs(cv2.contourArea(stage.quad(t)))/
                 (output_size[0]*output_size[1]))


def _max_velocity(stage,fps):
    q=np.asarray([stage.quad(i/fps) for i in range(round(stage.duration*fps))])
    if len(q)<2:return 0.
    speeds=np.linalg.norm(np.diff(q,axis=0),axis=2)
    for cut in stage.source_aligned_cuts(fps):
        if 0<=cut-1<len(speeds):speeds[cut-1,:]=0.
    return float(speeds.max(initial=0)*fps/60)


def _measured_gutter(stage,group,t):
    from live_dom_depth_plane import projected_real_element_quad
    records=[]
    for plane in group.members:
        q=projected_real_element_quad(stage,plane,t)
        records.append({
            "id":plane.id,
            "left":float(np.min(q[:,0])),"right":float(np.max(q[:,0])),
            "top":float(np.min(q[:,1])),"bottom":float(np.max(q[:,1])),
            "centerY":float(np.mean(q[:,1])),
            "amount":plane.amount(t)
        })
    records.sort(key=lambda p:p["left"])
    if len(records)!=2:return None
    left,right=records
    vertical_overlap=max(0.,min(left["bottom"],right["bottom"])-
                        max(left["top"],right["top"]))
    min_height=min(left["bottom"]-left["top"],
                   right["bottom"]-right["top"])
    if min_height<=0 or vertical_overlap/min_height<.55:
        # True vertical stagger/stack is a separate intentional composition.
        return None
    return {"pixels":round(right["left"]-left["right"],3),
            "left":left,"right":right}


def audit_hero_scene(plan,manifest,source_path,manifest_path,size,fps,
                     *,output_size=(1920,1080)):
    """Verified physical metrics for TWO simultaneously active source UI heroes."""
    dom=plan.get("domPlanes")
    if (not isinstance(dom,list) or len(dom)!=2 or
        any(not isinstance(x,dict) or
            not isinstance(x.get("heroCenter"),list) or
            type(x.get("peakAt")) not in (int,float) or
            type(x.get("endAt")) not in (int,float)
            for x in dom)):
        return None
    peak=max(x["peakAt"] for x in dom)+.08
    release=min(x["endAt"] for x in dom)-.65
    if peak>=release:return None
    t=(peak+release)/2
    stage=_stage(plan,manifest,source_path,size,fps,output_size)
    group=_group(plan,manifest,source_path,manifest_path,size,fps)
    return {"time":t,"sourceWindowAreaFraction":_area(stage,t,output_size),
            "gutter":_measured_gutter(stage,group,t),
            "group":group,"stage":stage}


def fit_source_hero_choreography(plan,manifest,source_path,manifest_path,
                                 size,fps,*,output_size=(1920,1080)):
    """Return an independently source-audited plan, plus exact bounded changes."""
    from live_dom_multi_plane import verify_group_projected_visibility
    result=copy.deepcopy(plan)
    changes=[]
    if not isinstance(result.get("studioStage"),dict):return result,changes
    if not isinstance(result.get("domPlanes"),list):return result,changes
    try:
        evidence=audit_hero_scene(result,manifest,source_path,manifest_path,
                                  size,fps,output_size=output_size)
    except (ValueError,KeyError,TypeError,OSError):
        return result,changes
    if not evidence:return result,changes
    t=evidence["time"]
    if evidence["sourceWindowAreaFraction"]>.62:
        planes=result["domPlanes"]
        camera=result["studioStage"].get("camera",[])
        starts=[float(c["startAt"]) for c in planes]
        peaks=[float(c["peakAt"]) for c in planes]
        ends=[float(c["endAt"]) for c in planes]
        start=max(starts)
        finish=max(peaks)
        release=min(ends)-.50
        if (isinstance(camera,list) and start+.35<=finish and
            finish+.30<release and release+.28<=result["durationSeconds"]):
            for next_index in range(1,len(camera)):
                prior=camera[next_index-1];future=camera[next_index]
                if (not isinstance(prior,dict) or
                    not isinstance(future,dict)):continue
                if (prior["at"]>min(starts) or
                    future["at"]<=release+.2):continue
                if future.get("cut",False):continue
                prior_scale=prior.get("scale")
                if type(prior_scale) not in (float,int):continue
                low=max(.55,float(prior_scale)-.22)
                high=min(float(prior_scale),1.55)
                if high-low<.045:continue

                def candidate(scale):
                    state=copy.deepcopy(result)
                    keys=state["studioStage"]["camera"]
                    left=keys[next_index-1]
                    new={"at":_native(finish,fps),
                         "startAt":_native(start,fps),
                         "scale":round(scale,5),
                         "yaw":left.get("yaw",0),
                         "pitch":left.get("pitch",0)}
                    if left.get("focus","wide")!="wide":
                        new["focus"]=left["focus"]
                    else:
                        new["center"]=copy.deepcopy(left.get("center",[.5,.5]))
                    keys.insert(next_index,new)
                    next_key=keys[next_index+1]
                    old_start=float(next_key.get("startAt",left["at"]))
                    next_key["startAt"]=_native(max(old_start,release),fps)
                    try:
                        stage=_stage(state,manifest,source_path,size,fps,output_size)
                        area=_area(stage,t,output_size)
                        if _max_velocity(stage,fps)>45:
                            return None
                        return (state,area,stage)
                    except (ValueError,TypeError,IndexError):
                        return None
                feasible=candidate(low)
                if not feasible or feasible[1]>.525:continue
                for _ in range(8):
                    probe=(low+high)/2
                    tested=candidate(probe)
                    if tested and tested[1]<=.51:low=probe
                    else:high=probe
                chosen=candidate(max(.55,low-.002))
                if not chosen or chosen[1]>.525:continue
                state,area,stage=chosen
                try:
                    group=_group(state,manifest,source_path,manifest_path,size,fps)
                    verify_group_projected_visibility(stage,group)
                except (ValueError,TypeError,OSError):
                    continue
                former_next=camera[next_index]
                result=state
                changes.append({
                    "field":f"studioStage.camera[{next_index}]",
                    "from":None,
                    "to":copy.deepcopy(result["studioStage"]["camera"][next_index]),
                    "reason":"Source-verified REAL screen-anchored cards detach "
                       "before independent full-browser spatial recession. "
                       "New key is compiled exclusively from native captured "
                       "element timestamps and existing model camera pose.",
                    "sourceNativeFrame":int(round(finish*fps)),
                    "modelSourceWindowAreaFraction":round(
                        evidence["sourceWindowAreaFraction"],4),
                    "compiledSourceWindowAreaFraction":round(area,4),
                    "maxNewCameraScaleDelta":.22,
                    "modelSourceCardPositionPixelsUnmodified":True})
                changes.append({
                    "field":f"studioStage.camera[{next_index+1}].startAt",
                    "from":former_next.get("startAt"),
                    "to":result["studioStage"]["camera"][next_index+1]["startAt"],
                    "reason":"Hold genuine browser depth while two original "
                    "source-backed hero cards remain independently lifted; "
                    "restore model's unchanged final camera by original endAt."
                })
                break
    # The measured native capture, not arbitrary chosen coordinates, decides
    # whether foreground cards collide. Move at most 9% of the output width
    # per card, never change the actual source pixels, shape or model scale.
    try:
        measured=audit_hero_scene(result,manifest,source_path,manifest_path,
                                  size,fps,output_size=output_size)
        if measured and measured["gutter"] is not None:
            g=measured["gutter"]
            if g["pixels"]<56:
                planes=result["domPlanes"]
                index={p["id"]:i for i,p in enumerate(planes)}
                left=planes[index[g["left"]["id"]]]
                right=planes[index[g["right"]["id"]]]
                amount=min(g["left"]["amount"],g["right"]["amount"])
                if amount>=.9:
                    delta=(64-g["pixels"])/2/amount
                    ratio=delta/output_size[0]
                    if 0<ratio<=.09:
                        old_left=left["heroCenter"][:]
                        old_right=right["heroCenter"][:]
                        a=old_left[0]-ratio
                        b=old_right[0]+ratio
                        if .14<=a<=.86 and .14<=b<=.86:
                            trial=copy.deepcopy(result)
                            trial_dom=trial["domPlanes"]
                            trial_dom[index[g["left"]["id"]]]["heroCenter"][0]=round(a,5)
                            trial_dom[index[g["right"]["id"]]]["heroCenter"][0]=round(b,5)
                            audited=audit_hero_scene(
                                trial,manifest,source_path,manifest_path,
                                size,fps,output_size=output_size)
                            if (audited and audited["gutter"] and
                                audited["gutter"]["pixels"]>=52):
                                verify_group_projected_visibility(
                                    audited["stage"],audited["group"])
                                result=trial
                                for record,before,after in (
                                   (left,old_left,
                                    result["domPlanes"][index[left["id"]]]["heroCenter"]),
                                   (right,old_right,
                                    result["domPlanes"][index[right["id"]]]["heroCenter"])):
                                    changes.append({
                                      "field":f"domPlanes[{index[record['id']]}].heroCenter",
                                      "from":before,"to":after[:],
                                      "reason":"Source-true bounded noncolliding "
                                        "side-by-side layout for measured original "
                                        "UI component bounding boxes. No source "
                                        "text, content or camera timing changed.",
                                      "originalGutterPx":g["pixels"],
                                      "compiledGutterPx":audited["gutter"]["pixels"],
                                      "maxXShiftFraction":.09})
    except (ValueError,TypeError,KeyError,OSError):
        pass
    return result,changes
