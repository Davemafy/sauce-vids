"""Source-relative film-direction preflight for unattended Sauce product demos.

An objective veto on obviously broken first impressions and missing click audio,
not a taste score. It audits only real source geometry/real recorded events.
Never changes a director's shot, fabricates UI, or accepts a film as premium.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any


def _has_real_action(manifest:dict) -> bool:
    return any(
        isinstance(e,dict)
        and isinstance(e.get("evidence"),str) and bool(e["evidence"].strip())
        and isinstance(e.get("kind"),str)
        and e.get("kind") not in ("page_load","idle","navigation")
        for e in manifest.get("events",[])
    )


def preflight_source_edit(plan:dict,manifest:dict,source_path:Path,
                          source_size:tuple[int,int],fps:float,
                          *,output_size=(1920,1080),audio_required=True,
                          manifest_path=None) -> dict:
    """Return source-grounded failures, NEVER a creative quality approval."""
    faults=[]
    observations={}
    stage_plan=plan.get("studioStage")
    if isinstance(stage_plan,dict):
        from spatial_studio_stage import load_studio_stage
        stage=load_studio_stage(
            stage_plan,manifest,source_path,source_size,output_size,
            float(plan["durationSeconds"]),fps)
        actions=[float(event["start"]) for event in manifest.get("events",[])
                 if isinstance(event,dict)
                 and type(event.get("start")) in (int,float)
                 and 0<=event["start"]<=plan["durationSeconds"]]
        first_action=min(actions) if actions else plan["durationSeconds"]
        # An establishing view must reveal the genuine software, rather
        # than arbitrarily clipping 60% of its browser window. Do not
        # demand a static first 2 seconds, just legible *first frames*.
        times=(0.,min(.18,max(0.,first_action*.4)))
        values=[stage.context_visibility(t) for t in times]
        observations["openingSourceContextFraction"]=[
            round(float(x),4) for x in values]
        observations["openingSamplesSeconds"]=[round(float(t),4) for t in times]
        fraction=min(values)
        if fraction<.76:
            faults.append({
                "code":"UNRECOGNIZABLE_OPENING_CROP",
                "detail":{"actualOpeningContextFraction":round(fraction,4),
                          "minimumFraction":.76,
                          "sourceFrames":[round(t*fps) for t in times]},
                "directorFeedback":
                  "The first source-backed frames crop away most of the real "
                  "application before its action is established. Establish a "
                  "legible, recognizable opening of the *real* interface "
                  "(>=76% source window visible for the first 0.18s); "
                  "then use a deliberate native-frame cut or move to the "
                  "actual target. Keep the genuine event and foreground "
                  "planes. The camera center is OUTPUT placement, not a "
                  "source focus coordinate."
            })
    # Screen-anchored foreground should have a discernibly separate REAL
    # browser background. This is a role-based shot check, not a generic
    # aesthetic. Full-interface shots (no independent heroCenter) are exempt.
    # The strict source/hash/plate validator runs BEFORE this advisory veto.
    if isinstance(stage_plan,dict):
        group=plan.get("domPlanes")
        if isinstance(group,list) and len(group)>=2 and all(
             isinstance(p,dict) and isinstance(p.get("heroCenter"),list)
             and type(p.get("peakAt")) in (int,float)
             and type(p.get("endAt")) in (int,float)
             for p in group):
            fully_up=max(float(p["peakAt"]) for p in group)+.08
            release=min(float(p["endAt"]) for p in group)-.65
            if fully_up < release:
                midpoint=(fully_up+release)/2
                frame_ratio=abs(__import__("cv2").contourArea(
                    stage.quad(midpoint)))/(output_size[0]*output_size[1])
                observations["heroSourceWindowAreaFraction"]=round(frame_ratio,4)
                observations["heroStageSampleSeconds"]=round(midpoint,4)
                if frame_ratio>.62:
                    faults.append({
                        "code":"FLAT_FOREGROUND_HIERARCHY",
                        "detail":{"actualSourceWindowAreaFraction":round(frame_ratio,4),
                                  "maximumForSimultaneousTwoHeroCards":.62,
                                  "sourceFrame":round(midpoint*fps)},
                        "directorFeedback":
                          "When both genuine source UI cards are screen-anchored "
                          "in the foreground, the real browser still fills "
                          "too much of the canvas, visually flattening the "
                          "depth effect. Recompose the WHOLE genuine browser "
                          "window to <=62% of the film area during the "
                          "two-card hero beat, while the actual source-backed "
                          "cards remain large, fully visible, non-overlapping "
                          "and readable. Or omit heroCenter if a full "
                          "browser-interface shot is more appropriate. "
                          "Do not fabricate a new backdrop or UI."
                    })
    # Real paired DOM element geometry is ground truth, not a guessed screen
    # "layout". When two simultaneously lifted *original* cards have an
    # inadequate actual projected gutter, the model/editor must separate
    # them or select non-overlapping choreography. No fake UI workaround.
    if manifest_path is not None and isinstance(plan.get("domPlanes"),list):
        from source_hero_choreography import audit_hero_scene
        physical=audit_hero_scene(
            plan,manifest,source_path,manifest_path,source_size,fps,
            output_size=output_size)
        if physical and physical["gutter"] is not None:
            gap=physical["gutter"]["pixels"]
            observations["sourceTrueForegroundGutterPx"]=gap
            if gap<48:
                faults.append({
                  "code":"SOURCE_HERO_CARDS_COLLIDE",
                  "detail":{"actualOutputGutterPx":gap,"minimumPx":48,
                            "sourceFrame":round(physical["time"]*fps)},
                  "directorFeedback":
                    "The two *original* projected UI cards merge or overlap "
                    "in the hero beat. Give independently lifted cards "
                    "a clear >=48px real output gutter, either via safe "
                    "heroCenter positions, subtle size or staggered timing. "
                    "The actual browser/source UI pixels and interactions "
                    "must remain untouched."
                })
    # Missing sound is a product-demo storytelling problem but must NEVER
    # override explicit real customer muted intent or invent audio events.
    if audio_required and _has_real_action(manifest):
        audio=plan.get("audio")
        mode=audio.get("mode") if isinstance(audio,dict) else None
        observations["modelSelectedAudioMode"]=mode or "none"
        if mode not in ("eventFoley","source"):
            faults.append({
                "code":"ACTION_FILM_WITHOUT_VERIFIED_AUDIO",
                "detail":{"actualMode":mode or "none","hasRecordedEvent":True},
                "directorFeedback":
                  "The film has a real recorded interaction but your JSON "
                  "provides no audio track. Use the engine's documented "
                  "source-event-locked eventFoley at restrained levels, "
                  "or preserve actual source audio if verified and supported. "
                  "Never synthesize fictional clicks or add unauthorized music."
            })
    return {
        "schema":"sauce-source-director-preflight-v1",
        "verdict":"REJECT" if faults else "GEOMETRY_AND_AUDIO_PREFLIGHT_PASS",
        "creativeApproved":False,
        "actualSourceSize":list(source_size),
        "nativeFps":fps,
        "observations":observations,
        "findings":faults
    }


def director_feedback(report:dict)->str:
    if not report.get("findings"):return ""
    return (
      "EDITORIAL SOURCE-EVIDENCE REJECTION: The code-valid film plan has "
      "these concrete, measurable first-impression defects. Reconsider "
      "its creative camera and sound choices; do not invent any UI or "
      "change source events. Return a NEW complete JSON plan, not prose.\n"
      + "\n".join(
         f"* {f['code']}: {f['directorFeedback']} "
         f"[measured={f['detail']}]"
         for f in report["findings"]
      )
    )
