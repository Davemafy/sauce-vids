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

def encoded_verdict(report):
    """Editorial warnings retain the private film, never grant approval."""
    return "REJECT" if split_findings(report)["technical"] else "HUMAN_REVIEW_REQUIRED"

HERO_MAX_ZOOM=1.62
HERO_MIN_ZOOM=1.20
HERO_PADDING=36.
HERO_OVERVIEW_MAX=1.075

def hero_geometry(manifest,index,source_size,output_size):
    """Fit the entire verified result and real pointer, not guessed content.

    Return peak zoom, source-derived camera translation, base aperture and
    maximum safe source-clock interval. A broad payoff can decline detail.
    """
    from cloud_window_sky_stage import window_geometry
    events=manifest["events"]
    if type(index) is not int or not 0<=index<len(events):
        raise ValueError("Invalid verified hero event")
    e=events[index];sw,sh=source_size;ow,oh=output_size
    x0,y0,x1,y1,_=window_geometry(source_size,output_size)
    sx=(x1-x0)/(sw-1);sy=(y1-y0)/(sh-1)
    r=e["resultRect"];x,y,rw,rh=(float(r[k]) for k in ("x","y","width","height"))
    if not (0<=x<x+rw<=sw and 0<=y<y+rh<=sh):
        raise ValueError("Hero result outside native source")
    begin=float(e["t"])
    end=float(events[index+1]["start"] if index+1<len(events) else manifest.get("duration",30.))-.25
    # Include the observed pointer throughout the potential hero window.
    # Interpolation is only between recorded samples, exactly as playback.
    pts=manifest.get("pointer_samples",[])
    xs=[x,x+rw];ys=[y,y+rh]
    if pts:
        a=np.asarray([[q["t"],q["x"],q["y"]] for q in pts],dtype=float)
        if a.ndim!=2 or not np.isfinite(a).all() or np.any(np.diff(a[:,0])<=0):
            raise ValueError("Invalid hero pointer provenance")
        sample=a[(a[:,0]>=begin)&(a[:,0]<=end)]
        xs.extend(sample[:,1]);ys.extend(sample[:,2])
        for t in (begin,end):
            xs.append(float(np.interp(t,a[:,0],a[:,1])))
            ys.append(float(np.interp(t,a[:,0],a[:,2])))
    left=x0+min(xs)*sx;right=x0+max(xs)*sx
    top=y0+min(ys)*sy;bottom=y0+max(ys)*sy
    cx=x0+(x+rw*.5)*sx;cy=y0+(y+rh*.5)*sy
    fit=min(HERO_MAX_ZOOM,(ow-2*HERO_PADDING)/max(1.,right-left),
            (oh-2*HERO_PADDING)/max(1.,bottom-top))
    base=(x0,y0,x1,y1)
    def transform(z):
        # Start with the actual result center; clamp to keep every protected
        # point inside output safe padding. Prefer covering the full canvas
        # where feasible without sacrificing the real result.
        def axis(center,lo,hi,extent,b0,b1):
            low=HERO_PADDING-z*lo;high=extent-HERO_PADDING-z*hi
            if low>high+1e-5:raise ValueError("Hero cannot fit protected evidence")
            cover_lo=extent-z*b1;cover_hi=-z*b0
            if cover_lo<=cover_hi:
                cl=max(low,cover_lo);ch=min(high,cover_hi)
                if cl<=ch:low,high=cl,ch
                else:
                    # Edge-aligned evidence can require a little surrounding
                    # sky. Reveal only the minimum necessary for its padding.
                    return low if low>cover_hi else high
            return max(low,min(high,extent*.5-z*center))
        return (axis(cx,left,right,ow,x0,x1),axis(cy,top,bottom,oh,y0,y1))
    return fit,transform,base,begin,end

def hero_motion_budget(zoom,translation,base,output_size):
    """Conservative duration for the existing <=8px/frame quad speed."""
    dx,dy=translation;x0,y0,x1,y1=base
    displacement=max(math.hypot((zoom-1)*x+dx,(zoom-1)*y+dy)
                     for x in (x0,x1) for y in (y0,y1))
    # cinematic asymmetric quintic derivative <=2.12; conservative 2.35.
    return max(.75,math.ceil(displacement*2.35/8)/60)

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
    hero=getattr(stage,"hero_detail_index",None)
    detail=np.zeros(frames,dtype=bool)
    hero_min=1.;hero_padding=None
    for shot_index,begin,end,_,_ in getattr(stage,"detail_shots",()):
        hero=shot_index
        if type(hero) is not int or not 0<=hero<len(events):
            raise ValueError("Invalid customer hero index")
        current=(timeline>=begin-1e-7)&(timeline<=end+1e-7)
        if np.any(detail & current):raise ValueError("Overlapping detail windows")
        detail |= current
        e=events[hero];next_press=events[hero+1]["start"] if hero+1<len(events) else frames/fps
        if begin<e["t"]-1e-7 or end>next_press-.20 or not current.any():
            raise ValueError("Hero detail overlaps unverified source time")
        box=tuple(e["resultRect"][k] for k in ("x","y","width","height"))
        sw,sh=stage.source_size
        source=np.float32([[0,0],[sw-1,0],[sw-1,sh-1],[0,sh-1]])
        x,y,w,h=box
        pts=np.float32([[[x,y],[x+w,y],[x+w,y+h],[x,y+h]]])
        for j in np.flatnonzero(current):
            t=timeline[j]
            # Check the entire transition, peak hold and release, not only a key.
            hero_min=min(hero_min,stage.region_visibility(t,box))
            M=cv2.getPerspectiveTransform(source,quads[j].astype(np.float32))
            projected=cv2.perspectiveTransform(pts,M)[0]
            pad=float(min(projected[:,0].min(),1920-projected[:,0].max(),
                          projected[:,1].min(),1080-projected[:,1].max()))
            # The wide start/release can have less than hero padding for an
            # edge-aligned source; it must still keep every pixel on screen.
            if stage.view_scale(t)>=HERO_MIN_ZOOM-1e-6 and pad<HERO_PADDING-1:
                raise ValueError("Hero payoff breaches protected text padding")
            hero_padding=pad if hero_padding is None else min(hero_padding,pad)
            px=float(np.interp(t,pointer[:,0],pointer[:,1]));py=float(np.interp(t,pointer[:,0],pointer[:,2]))
            if not stage.point_visible(t,px,py):raise ValueError("Hero detail hides recorded cursor")
        if hero_min<.999:raise ValueError("Hero detail crops verified result")
    wide=quads[~detail]
    margin=float(min(wide[:,:,0].min(),1920-wide[:,:,0].max(),wide[:,:,1].min(),1080-wide[:,:,1].max()))
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
            "heroEventIndex":getattr(stage,"hero_detail_index",None),"detailEventIndices":[v[0] for v in getattr(stage,"detail_shots",())],"heroDetailFrames":int(detail.sum()),
            "heroMinimumResultVisible":round(hero_min,5),
            "heroMinimumPaddingPx":round(hero_padding,3) if hero_padding is not None else None,
            "creativeApproved":False}
