"""Strict customer whole-window craft contract, independent of model taste.

The existing permissive research renderer remains available for optical studies.
A customer story cannot use these experiments to bypass visibility, continuity
or source-event audio guarantees. No source pixels or event times are edited.
"""
import math
import numpy as np
import cv2

EDITORIAL_FINDINGS=frozenset({"STATIC_OPENING_2S","REPEATED_OR_STATIC_FRAMES","SMALL_FOCAL_CONTENT"})

def split_findings(report):
    """Unknown findings fail closed; editorial never means Gemini is at fault."""
    findings=report.get("findings")
    if not isinstance(findings,list):raise ValueError("Missing encoded quality findings")
    codes=[f["code"] for f in findings]
    return {"technical": [c for c in codes if c not in EDITORIAL_FINDINGS],
            "editorial": [c for c in codes if c in EDITORIAL_FINDINGS],
            "creativeApproved":False}

def verify_plan(plan,manifest,stage,pointer,fps,frames,trim=0):
    events=manifest.get("events",[])
    if (fps!=60 or not 3<=len(events)<=6 or trim!=0 or
            frames!=round(plan["durationSeconds"]*60) or
            frames!=round(manifest["duration"]*60) or
            min(stage.source_size)<1800 or stage.output_size!=(1920,1080) or
            manifest.get("cursorless") is not True):
        raise ValueError("Customer craft requires complete native source timeline and verified actions")
    if (set(plan)-{"schema","sourceSha256","manifestSha256","durationSeconds","presentation","cursor","audio","studioStage","camera","cursorPack"}
            or plan.get("presentation")!="fullscreen" or plan.get("cursor")!="recorded"
            or stage.stage_preset!="cloud_window_clearface_v1" or not stage.immersive
            or stage.motion_style!="cinematic" or stage.shutter!=0
            or stage.payoff_mode!="overview" or stage.source_aligned_cuts(fps)):
        raise ValueError("Customer craft requires a continuous clearface whole-window plan, not optical experiments")
    audio=plan.get("audio",{})
    if (audio.get("mode")!="eventFoley" or audio.get("eventIndices")!=list(range(len(events)))
        or not .30<=audio.get("clickGain",0)<=.65 or not .12<=audio.get("motionGain",0)<=.35
        or not .65<=audio.get("masterGain",0)<=.9):
        raise ValueError("Customer craft needs audible bounded Foley for every genuine action")
    if pointer is None or len(pointer)<25:raise ValueError("Missing original pointer track")
    timeline=np.arange(frames,dtype=float)/fps
    quads=np.asarray([stage.quad(t) for t in timeline])
    if quads.shape!=(frames,4,2) or not np.isfinite(quads).all():raise ValueError("Invalid projected window")
    margin=float(min(quads[:,:,0].min(),1920-quads[:,:,0].max(),quads[:,:,1].min(),1080-quads[:,:,1].max()))
    if margin<24:raise ValueError("Customer window breaches 24px physical safe margin")
    speed=float(np.linalg.norm(np.diff(quads,axis=0),axis=2).max(initial=0))
    acceleration=float(np.linalg.norm(np.diff(quads,n=2,axis=0),axis=2).max(initial=0))
    if speed>8 or acceleration>1.5:raise ValueError("Customer window motion is too abrupt")
    # Verify the whole action, not only the final illuminated event. Real
    # cursor tip uses the same source->display projection as the renderer.
    min_target=1.;min_result=1.;checks=0
    sw,sh=stage.source_size
    source=np.float32([[0,0],[sw-1,0],[sw-1,sh-1],[0,sh-1]])
    for i,e in enumerate(events):
        start,end,confirmed=(float(e[k]) for k in ("start","end","t"))
        if not 0<=start<end<=confirmed<frames/fps:raise ValueError("Invalid verified action timing")
        target=e["targetRect"];result=e["resultRect"]
        px=float(np.interp(start,pointer[:,0],pointer[:,1]))
        py=float(np.interp(start,pointer[:,0],pointer[:,2]))
        if not (target["x"]-4<=px<=target["x"]+target["width"]+4
                and target["y"]-4<=py<=target["y"]+target["height"]+4):
            raise ValueError(f"Recorded cursor misses genuine action target {i}")
        target_box=tuple(target[k] for k in ("x","y","width","height"))
        result_box=tuple(result[k] for k in ("x","y","width","height"))
        first=max(0,math.floor(start*fps));last=min(frames-1,math.ceil(end*fps))
        for j in range(first,last+1):
            t=j/fps
            min_target=min(min_target,stage.region_visibility(t,target_box))
            px=float(np.interp(t,pointer[:,0],pointer[:,1]));py=float(np.interp(t,pointer[:,0],pointer[:,2]))
            H=cv2.getPerspectiveTransform(source,quads[j].astype(np.float32))
            x,y=cv2.perspectiveTransform(np.float32([[[px,py]]]),H)[0,0]
            if not (14<=x<=1906 and 14<=y<=1066 and stage.point_visible(t,px,py)):
                raise ValueError(f"Customer cursor leaves visible stage at action {i}")
            checks+=1
        # Each payoff must remain readable for its actual first half-second,
        # before the next event; no final-only visibility loophole.
        until=min(confirmed+.5,events[i+1]["start"] if i+1<len(events) else frames/fps)
        for j in range(math.ceil(confirmed*fps),min(frames,math.floor(until*fps)+1)):
            min_result=min(min_result,stage.region_visibility(j/fps,result_box))
        if min_target<.99 or min_result<.99:raise ValueError(f"Customer camera clips verified action/result {i}")
    return {"schema":"sauce-customer-craft-v1","checkedFrames":frames,
            "checkedActions":len(events),"checkedPointerFrames":checks,
            "minimumWindowMarginPx":round(margin,3),"maximumQuadSpeedPx":round(speed,4),
            "maximumQuadAccelerationPx":round(acceleration,4),
            "minimumTargetVisible":round(min_target,5),"minimumResultVisible":round(min_result,5),
            "creativeApproved":False}
