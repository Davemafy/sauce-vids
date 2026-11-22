"""Source-verified reading-time audit of an actual studio film's camera JSON.

A JSON can be syntactically correct, source-true, and still have no readable
result hold. This module measures projected ORIGINAL result rectangles during
the ORIGINAL result clock, including camera velocity and visible frame size.
It never changes a source frame or claims to judge cinematography.
"""
from __future__ import annotations

import math
import cv2
import numpy as np


def inspect_result_holds(stage, manifest, *, fps, min_hold_seconds=.55,
                         max_motion_px_per_60frame=2.5,
                         min_result_width_px=360, min_result_height_px=57):
    if not math.isfinite(fps) or not 1 <= fps <= 120:
        raise ValueError("Real native source FPS required")
    if not 0 < min_hold_seconds <= 4:
        raise ValueError("Invalid readable hold duration")
    events=manifest.get("events",[])
    if not isinstance(events,list) or not events:
        return {"findings":[],"measurements":[],"creativeApproved":False}
    sw,sh=stage.source_size
    src_quad=np.float32([[0,0],[sw-1,0],[sw-1,sh-1],[0,sh-1]])
    frame_count=round(stage.duration*fps)
    if frame_count<1 or frame_count>fps*180:
        raise ValueError("Unsupported complete source-timed film duration")
    quads=np.asarray([stage.quad(i/fps) for i in range(frame_count)])
    if not np.isfinite(quads).all():
        raise ValueError("Non-finite camera path")
    # Velocity comes from the actual renderer's projected corners. An
    # intentional native-frame cut ends the previous motion interval.
    speed=np.zeros(frame_count,dtype=np.float64)
    speed[1:]=np.linalg.norm(np.diff(quads,axis=0),axis=2).max(axis=1)*fps/60
    for cut in stage.source_aligned_cuts(fps):
        if 0<=cut<frame_count:
            speed[cut]=float("inf")
    findings=[]; measurements=[]
    for i,e in enumerate(events):
        if (not isinstance(e,dict) or not e.get("evidence")
                or type(e.get("t")) not in (int,float)
                or not isinstance(e.get("resultRect"),dict)):
            continue
        x,y,w,h=(float(e["resultRect"][f]) for f in ("x","y","width","height"))
        if not all(map(math.isfinite,(x,y,w,h))) or min(w,h)<1 or min(x,y)<0 or x+w>sw or y+h>sh:
            raise ValueError("Result geometry must be from the genuine source")
        start=max(0,math.ceil(float(e["t"])*fps-1e-7))
        next_time=min((float(other["t"]) for other in events[i+1:]
                       if isinstance(other,dict)
                       and type(other.get("t")) in (int,float)
                       and other["t"]>e["t"]),default=stage.duration)
        end=min(frame_count,math.ceil(next_time*fps-1e-7))
        if start>=end:continue
        rect=np.float32([[[x,y],[x+w,y],[x+w,y+h],[x,y+h]]])
        longest=0;run=0;best_width=0;best_height=0;max_width=0;first=None
        for frame in range(start,end):
            H=cv2.getPerspectiveTransform(src_quad,quads[frame])
            pts=cv2.perspectiveTransform(rect,H)[0]
            projected_width=float(np.linalg.norm(pts[1]-pts[0]))
            projected_height=float(np.linalg.norm(pts[3]-pts[0]))
            max_width=max(max_width,projected_width)
            enough=(stage.region_visibility(frame/fps,(x,y,w,h))>=.975
                   and projected_width>=min_result_width_px
                   and projected_height>=min_result_height_px
                   and speed[frame]<=max_motion_px_per_60frame)
            if enough:
                run+=1
                if run>longest:
                    longest=run
                    first=frame-run+1
                    best_width=projected_width
                    best_height=projected_height
            else:
                run=0
        hold=round(longest/fps,4)
        item={"eventIndex":i,"confirmedResultTime":round(float(e["t"]),4),
              "maxReadableSteadyHoldSeconds":hold,
              "longestSteadyHoldStartFrame":first,
              "resultWidthPxDuringBestHold":round(best_width,1),
              "resultHeightPxDuringBestHold":round(best_height,1),
              "maximumProjectedResultWidthPx":round(max_width,1),
              "evaluatedOriginalFrameRange":[start,end],
              "thresholdSeconds":min_hold_seconds}
        measurements.append(item)
        if hold+1e-8<min_hold_seconds:
            findings.append({"code":"RESULT_READING_HOLD_TOO_SHORT",
                "detail":item,
                "directorFeedback":
                  "The real browser result is on screen, but camera movement "
                  "or small projected size leaves too little stable reading time. "
                  "Keep the verified result large, visible and physically still "
                  "for at least the measured threshold after its actual source confirmation. "
                  "It is preferable to omit an unnecessary zoom-out than to "
                  "rush the reading hold; never alter the browser event clock."})
    return {"schema":"sauce-source-result-reading-holds-v1",
            "findings":findings,"measurements":measurements,
            "creativeApproved":False}
