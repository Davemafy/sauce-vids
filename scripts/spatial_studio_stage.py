"""Source-true, parameterized 2.5D studio stage for the Sauce film-plan renderer.

This module never constructs product UI. A real decoded capture (with its sole
recorded pointer, when requested) is the only screen texture. The stage can
change camera, matte, exterior light, shadow and a subdued source-derived
reflection. Every creative parameter is part of validated film JSON.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import math

import cv2
import numpy as np

from floating_ui_stage import matte
from source_mouse_spring_camera import RecordedFollow, build_follow, reference_ease_out

_EPS=1e-7


def _number(value, name, lo, hi):
    if type(value) not in (float, int) or not math.isfinite(value) or not lo <= value <= hi:
        raise ValueError(f"{name} must be finite and in [{lo}, {hi}]")
    return float(value)


def _fields(value, allowed, name):
    if not isinstance(value,dict) or set(value)-set(allowed):
        raise ValueError(f"Unknown {name} properties")
    return value


def _color(value):
    if not isinstance(value,list) or len(value)!=3 or any(type(n) is not int or not 0<=n<=255 for n in value):
        raise ValueError("studioStage.material.color must be RGB [0..255] integers")
    return tuple(value)


def _eased(p):
    t=max(0.,min(1.,p))
    return t*t*t*(t*(6*t-15)+10)


def _cinematic_eased(progress, *, advance=.34):
    """Monotone asymmetric minimum-jerk movement.

    Unlike arbitrary bounce/overshoot, this keeps both endpoints exact and
    retains zero endpoint velocity/acceleration. Advance changes WHERE peak
    speed occurs: an early purposeful move followed by a longer soft settle.
    All time changes are inside the already verified source transition.
    """
    p=max(0.,min(1.,progress))
    u=p+advance*p*(1.-p)
    return _eased(u)


@dataclass(frozen=True)
class Key:
    at:float
    start_at:float
    scale:float
    yaw:float
    pitch:float
    center_x:float
    center_y:float
    focus:str
    cut:bool=False
    view_scale:float=1.


def _event(manifest,index,duration):
    events=manifest.get("events")
    if not isinstance(events,list) or not 0<=index<len(events):
        raise ValueError("Studio lighting/focus requires a real recorded event index")
    e=events[index]
    if not isinstance(e,dict) or not isinstance(e.get("evidence"),str) or not e["evidence"].strip():
        raise ValueError("Studio event must have verified outcome evidence")
    for field in ("start","end","t"):
        _number(e.get(field),f"event.{field}",0,duration)
    # A slider can confirm its changed value while still being dragged;
    # a click's result is confirmed after its physical release.
    ordered=(e["start"]<=e["t"]<=e["end"]<=duration if e.get("kind")=="slider_change"
             else e["start"]<=e["end"]<=e["t"]<=duration)
    if not ordered:
        raise ValueError("Studio event timestamps must respect recorded action semantics")
    return e


def _bounds(e,field,source_size):
    rect=e.get(field)
    if not isinstance(rect,dict):raise ValueError(f"Studio event missing {field}")
    w,h=source_size
    x=_number(rect.get("x"),f"{field}.x",0,w)
    y=_number(rect.get("y"),f"{field}.y",0,h)
    rw=_number(rect.get("width"),f"{field}.width",1,w)
    rh=_number(rect.get("height"),f"{field}.height",1,h)
    if x+rw>w+_EPS or y+rh>h+_EPS:
        raise ValueError("Studio event bounds are outside recorded image")
    return x,y,rw,rh


def _source_fraction(source,rect):
    x,y,w,h=rect
    crop=source[round(y):round(y+h),round(x):round(x+w)]
    if crop.size==0:return 0.
    small=cv2.resize(crop,(192,108),interpolation=cv2.INTER_AREA)
    hsv=cv2.cvtColor(small,cv2.COLOR_BGR2HSV)
    return float(((hsv[:,:,1]>68)&(hsv[:,:,2]>115)).mean())


def detect_appearance_onset(source_path,source_size,event,fps):
    """Find verified *visual* onset, never before a real click release.

    Conservative: only accepts a persistent increase in saturated source
    pixels, compared with the original before/after product video. For
    grayscale-to-color theme changes this can precede downstream DOM polling.
    Otherwise, caller MUST use the recorded confirmation timestamp.
    """
    rect=_bounds(event,"resultRect",source_size)
    start=event["start"];release=event["end"];confirmed=event["t"]
    stream=cv2.VideoCapture(str(source_path))
    if not stream.isOpened():raise ValueError("Cannot inspect source video for appearance evidence")
    baseline_frame=max(0,round((start-.20)*fps))
    confirmed_frame=round(min(confirmed+.12,(stream.get(cv2.CAP_PROP_FRAME_COUNT)-1)/fps)*fps)
    fractions={}
    # A second, genuinely independent pixel-difference criterion catches
    # small real changes to text, thin graphs and borders that do NOT produce
    # the large saturated area needed by the legacy color detector.
    colored_source={}
    x,y,w,h=rect
    i=0
    try:
        while i<=confirmed_frame:
            ok,img=stream.read()
            if not ok:break
            if (i==baseline_frame or
                    i==max(0,int(math.floor(start*fps-1e-6))) or
                    i>=max(0,int((release-.08)*fps))):
                fractions[i]=_source_fraction(img,rect)
                crop=img[round(y):round(y+h),round(x):round(x+w)]
                if crop.size:
                    colored_source[i]=cv2.resize(crop,(192,108),
                                    interpolation=cv2.INTER_AREA)
            i+=1
    finally:
        stream.release()
    before=fractions.get(baseline_frame)
    after=fractions.get(confirmed_frame)
    outcome={"method":"verified-event-time","time":confirmed,
             "baselineSaturationFraction":before,
             "confirmedSaturationFraction":after,
             "candidateFrame":None,"frameRate":fps}
    if before is None or after is None:
        return outcome
    first=max(0,math.ceil(release*fps-1e-8))
    stop=min(confirmed_frame-1,math.floor(confirmed*fps))
    if after-before>=.035:
        threshold=before+max(.018,(after-before)*.38)
        # Legacy conservative saturation detection preserved unchanged.
        for k in range(first,stop):
            if (k in fractions and k+1 in fractions and
                    fractions[k]>=threshold and fractions[k+1]>=threshold):
                outcome.update(method="sustained-pixel-evidence",time=k/fps,
                               candidateFrame=k,threshold=threshold)
                return outcome
    # Fallback: the actual changed RESULT rectangle must differ *persistently*
    # from the BEFORE frame and share the SAME changed pixels with the
    # independently verified AFTER frame. This avoids admitting a temporary
    # dropdown/animation as the final product outcome.
    before_frame=colored_source.get(baseline_frame)
    after_frame=colored_source.get(confirmed_frame)
    if before_frame is None or after_frame is None:
        return outcome
    def differences(frame):
        delta=cv2.absdiff(before_frame,frame)
        return (delta.max(axis=2)>18)
    after_changed=differences(after_frame)
    total=float(after_changed.mean())
    if total<.075:
        return outcome
    # The change must not already be established BEFORE the actual recorded
    # action. This guards animated/unrelated content against attribution to
    # the verified click, including across a long lazy-loading transition.
    preaction=max(0,int(math.floor(start*fps-1e-6)))
    before_action=colored_source.get(preaction)
    if before_action is not None:
        pre_change=(cv2.absdiff(before_frame,before_action).max(axis=2)>18)
        if float(np.mean(pre_change&after_changed))/max(total,.0001)>.25:
            return outcome
    for k in range(first,stop):
        if k not in colored_source or k+1 not in colored_source:
            continue
        a=differences(colored_source[k])
        b=differences(colored_source[k+1])
        area=float(a.mean())
        if area<.075 or float(b.mean())<.075:
            continue
        shared=float(np.mean(a&b&after_changed))
        if shared/max(area,.0001)<.78 or shared/max(total,.0001)<.72:
            continue
        outcome.update(method="sustained-source-pixel-change",
                       time=k/fps,candidateFrame=k,
                       changedFraction=round(area,5),
                       overlapWithConfirmedChange=round(shared/max(total,.0001),5),
                       pixelDeltaThreshold=18)
        return outcome
    return outcome


@dataclass(frozen=True)
class StudioStage:
    camera:tuple[Key,...]
    color:tuple[int,int,int]
    grain:float
    depth:float
    reflection:float
    light_event:int
    light_intensity:float
    light_seconds:float
    onset:dict
    payoff_event:int|None
    payoff_region:str|None
    min_payoff_visible:float
    payoff_mode:str
    min_context_visible:float
    source_size:tuple[int,int]
    output_size:tuple[int,int]
    duration:float
    result_rect:tuple[float,float,float,float]
    motion_style:str
    shutter:float
    fps:float
    stage_preset:str
    mouse_follow:RecordedFollow|None=None
    immersive:bool=False

    def _sample_keys(self,t):
        prev=self.camera[0]
        for key in self.camera[1:]:
            if t<key.at:
                # Intentional hard cut holds the previous *real source* camera
                # pose until the exact source-frame boundary, then jumps. This
                # never changes the browser state or invents intermediate UI.
                if key.cut or t<key.start_at:
                    p=0.
                else:
                    progress=(t-key.start_at)/(key.at-key.start_at)
                    if self.motion_style=="reference-spring":
                        p=reference_ease_out(progress)
                    elif self.motion_style=="cinematic":
                        # Push toward an action decisively, release deliberately.
                        # Never alter the genuine click/result clock.
                        advance=.34 if key.scale>=prev.scale else -.12
                        p=_cinematic_eased(progress,advance=advance)
                    else:
                        p=_eased(progress)
                break
            prev=key
        else:
            key=prev;p=0.
        return prev,key,p

    def pose(self,t):
        prev,key,p=self._sample_keys(t)
        camera=tuple(a+(b-a)*p for a,b in zip(
            (prev.scale,prev.yaw,prev.pitch,prev.center_x,prev.center_y),
            (key.scale,key.yaw,key.pitch,key.center_x,key.center_y)))
        if self.mouse_follow is None:
            return camera
        dx,dy=self.mouse_follow.offset(t)
        scale,yaw,pitch,cx,cy=camera
        return scale,yaw,pitch,cx+dx,cy+dy

    def view_scale(self,t):
        """Physical camera dolly into/out of the whole floating window.

        The recorded browser has not been zoomed inside a rigid card: during a
        detail shot the window itself grows with its existing edge/shadow,
        then returns to the user-selected studio composition. Defaults 1.0.
        """
        if not self.immersive:
            return 1.
        a,b,p=self._sample_keys(t)
        return a.view_scale+(b.view_scale-a.view_scale)*p

    def view_transform(self,t,physical=None):
        zoom=self.view_scale(t)
        ow,oh=self.output_size
        dx=ow*(1.-zoom)*.5;dy=oh*(1.-zoom)*.5
        # The payout region is real DOM geometry from an already confirmed
        # source event. In a true close-up, keep the *upper* result controls
        # legible, instead of enlarging the modal until its header vanishes.
        # Never focus on that region BEFORE its recorded appearance.
        if (self.immersive and t>=self.onset["time"] and
                zoom>1.03 and self.result_rect is not None):
            x,y,w,h=self.result_rect
            sw,sh=self.source_size
            coverage=(w*h)/(sw*sh)
            if coverage<.85:
                if physical is None:
                    physical=self._cloud_base_quad(t)
                H=cv2.getPerspectiveTransform(np.float32(
                    [[0,0],[sw-1,0],[sw-1,sh-1],[0,sh-1]]),physical)
                # Aim the camera at the source-verified modal's upper third,
                # not an arbitrary crop or a fabricated heading location.
                focus=cv2.perspectiveTransform(np.float32([[[x+w*.5,y+h*.34]]]),H)[0,0]
                target_x=ow*.5-zoom*float(focus[0])
                target_y=oh*.5-zoom*float(focus[1])
                blend=_eased(min(1.,max(0.,(zoom-1.03)/.35)))
                dx=dx*(1-blend)+target_x*blend
                dy=dy*(1-blend)+target_y*blend
        return np.float32([[zoom,0.,dx],[0.,zoom,dy]])

    def shutter_times(self,t):
        """Same-source-frame camera exposure; never blend across a hard cut."""
        if self.shutter<=0:
            return None
        half=self.shutter/(2*self.fps)
        before=max(0.,t-half);after=min(self.duration,t+half)
        if any(k.cut and before<k.at<=after for k in self.camera):
            return None
        if after-before<=1e-9:
            return None
        motion=np.linalg.norm(self.quad(after)-self.quad(before),axis=1)
        if float(motion.max(initial=0.))<2.0:
            return None
        return before,after

    def source_aligned_cuts(self,fps,trim_frames=0):
        # Only emitted cuts strictly inside the encoded range are measured.
        return tuple(int(round(k.at*fps))-trim_frames for k in self.camera
                     if k.cut and int(round(k.at*fps))>trim_frames)

    def raw_quad(self,t):
        scale,yaw,pitch,cx,cy=self.pose(t)
        width,height=self.output_size
        sw,sh=self.source_size
        plane_w=width*scale
        plane_h=plane_w*sh/sw
        yaw=math.radians(yaw);pitch=math.radians(pitch)
        projected=[]
        for xx,yy in ((-1,-1),(1,-1),(1,1),(-1,1)):
            x=xx*math.cos(yaw);z=-xx*math.sin(yaw)
            y=yy*math.cos(pitch)-z*math.sin(pitch)
            z=yy*math.sin(pitch)+z*math.cos(pitch)
            perspective=4.9/(4.9+z)
            projected.append([cx*width+plane_w*x*perspective/2,
                              cy*height+plane_h*y*perspective/2])
        return np.float32(projected)

    def _cloud_base_quad(self,t):
        if self.stage_preset=="cloud_glass_v1":
            from cloud_glass_object_stage import window_geometry
        elif self.stage_preset in ("cloud_window_sky_v1","cloud_window_fullglass_v1"):
            from cloud_window_sky_stage import window_geometry
        else:
            from cloud_shadow_stage import window_geometry
        x0,y0,x1,y1,_=window_geometry(self.source_size,self.output_size)
        base=self.raw_quad(0)
        dst=np.float32([[x0,y0],[x1,y0],[x1,y1],[x0,y1]])
        M=cv2.getPerspectiveTransform(base,dst)
        q=cv2.perspectiveTransform(self.raw_quad(t)[None,:,:],M)[0]
        # Guard the established rigid shell against exposing empty pixels
        # under an off-center real-result focus. Do not interfere with the
        # opt-in recorded-follow or immersive dolly motion system.
        if (not self.immersive and self.mouse_follow is None and
            abs(float(q[0,1]-q[1,1]))<.02 and
            abs(float(q[1,0]-q[2,0]))<.02 and
            abs(float(q[2,1]-q[3,1]))<.02 and
            abs(float(q[3,0]-q[0,0]))<.02):
            center=q.mean(axis=0)
            w=float(q[:,0].max()-q[:,0].min())
            h=float(q[:,1].max()-q[:,1].min())
            fill=max(1.,(x1-x0)/max(w,.001),(y1-y0)/max(h,.001))
            q=(q-center)*fill+center
            dx=np.clip((x0+x1)/2-float(q[:,0].mean()),
                       x1-float(q[:,0].max()),x0-float(q[:,0].min()))
            dy=np.clip((y0+y1)/2-float(q[:,1].mean()),
                       y1-float(q[:,1].max()),y0-float(q[:,1].min()))
            q+=np.float32([dx,dy])
        return q

    def quad(self,t):
        if self.stage_preset=="classic":
            return self.raw_quad(t)
        physical=self._cloud_base_quad(t)
        if not self.immersive:
            return physical
        return cv2.transform(physical[None,:,:],self.view_transform(t,physical))[0]

    def canvas_region(self):
        ow,oh=self.output_size
        if self.immersive:
            # The close-up is a true camera move towards a physical floating
            # window, intentionally beyond the former card mask. Validate
            # actual source-target visibility against the rendered full frame.
            return np.float32([[0.,0.],[ow,0.],[ow,oh],[0.,oh]])
        if self.stage_preset=="classic":
            return np.float32([[0.,0.],[ow,0.],[ow,oh],[0.,oh]])
        if self.stage_preset=="cloud_glass_v1":
            from cloud_glass_object_stage import window_geometry
        elif self.stage_preset in ("cloud_window_sky_v1","cloud_window_fullglass_v1"):
            from cloud_window_sky_stage import window_geometry
        else:
            from cloud_shadow_stage import window_geometry
        x0,y0,x1,y1,_=window_geometry(self.source_size,self.output_size)
        return np.float32([[x0,y0],[x1,y0],[x1,y1],[x0,y1]])

    def context_visibility(self,t):
        # Fraction of the entire real interface still visible in the ending.
        q=self.quad(t)
        ow,oh=self.output_size
        area=abs(cv2.contourArea(q))
        if area<1:return 0.
        bounds=self.canvas_region()
        common,_=cv2.intersectConvexConvex(q,bounds)
        return max(0.,min(1.,float(common)/area))

    def visibility(self,t):
        if self.payoff_event is None:return 1.
        return self.region_visibility(t,self.result_rect)

    def region_visibility(self,t,rect):
        # Project an actual source-verified rectangle. The action target must
        # appear in the frame during the event; outcome proof must survive
        # the final shot. A floating source window alone is not enough.
        x,y,w,h=rect
        sw,sh=self.source_size;ow,oh=self.output_size
        q=self.quad(t)
        H=cv2.getPerspectiveTransform(np.float32(
            [[0,0],[sw-1,0],[sw-1,sh-1],[0,sh-1]]),q)
        pts=np.float32([[[x,y],[x+w,y],[x+w,y+h],[x,y+h]]])
        pts=cv2.perspectiveTransform(pts,H)[0]
        polygon=np.rint(pts).astype(np.float32)
        area=abs(cv2.contourArea(polygon))
        if area<1:return 0.
        box=self.canvas_region()
        clip,_=cv2.intersectConvexConvex(polygon,box)
        return max(0.,min(1.,float(clip)/area))

    def point_visible(self,t,source_x,source_y,margin=14):
        sw,sh=self.source_size;ow,oh=self.output_size
        matrix=cv2.getPerspectiveTransform(np.float32([
            [0,0],[sw-1,0],[sw-1,sh-1],[0,sh-1]]),self.quad(t))
        projected=cv2.perspectiveTransform(
            np.float32([[[source_x,source_y]]]),matrix)[0,0]
        frame=self.canvas_region()
        return bool(frame[0,0]+margin<=projected[0]<=frame[1,0]-margin and
                    frame[0,1]+margin<=projected[1]<=frame[2,1]-margin)


def load_studio_stage(data,manifest,source_path,source_size,output_size,duration,fps):
    _fields(data,("camera","material","depthPx","reflection","lighting","payoff","motion","stagePreset"),"studioStage")
    stage_preset=data.get("stagePreset","classic")
    if stage_preset not in ("classic","cloud_shadow_v1","cloud_glass_v1","cloud_window_sky_v1","cloud_window_fullglass_v1"):
        raise ValueError("Only approved rigid Sauce stage presets are supported")
    if stage_preset in ("cloud_shadow_v1","cloud_glass_v1","cloud_window_sky_v1","cloud_window_fullglass_v1"):
        from cloud_shadow_stage import backdrop
        # Fail closed rather than silently substituting a generic gradient.
        backdrop(*output_size)
    motion=_fields(data.get("motion",{}),("profile","shutter","follow","immersive"),"studioStage.motion")
    profile=motion.get("profile","classic")
    if profile not in ("classic","cinematic","reference-spring"):
        raise ValueError("Studio motion profile must be classic, cinematic or reference-spring")
    if ("follow" in motion) != (profile=="reference-spring"):
        raise ValueError("Recorded pointer following requires reference-spring motion profile")
    immersive=motion.get("immersive",False)
    if type(immersive) is not bool or (immersive and
                                      (profile!="reference-spring" or
                                       stage_preset not in ("cloud_shadow_v1","cloud_glass_v1","cloud_window_sky_v1","cloud_window_fullglass_v1"))):
        raise ValueError("Physical window push needs cloud stage and verified spring camera")
    shutter=_number(motion.get("shutter",0.),"studioStage.motion.shutter",0,.75)
    if shutter>0 and profile not in ("cinematic","reference-spring"):
        raise ValueError("Motion shutter requires the opt-in cinematic camera profile")
    material=_fields(data.get("material",{}),("color","grain"),"studioStage.material")
    rgb=_color(material.get("color",[28,30,32]))
    grain=_number(material.get("grain",.25),"studioStage.material.grain",0,1)
    depth=_number(data.get("depthPx",10),"studioStage.depthPx",0,24)
    reflection=_number(data.get("reflection",.08),"studioStage.reflection",0,.18)
    light=_fields(data.get("lighting"),("eventIndex","intensity","transitionSeconds","trigger"),"studioStage.lighting")
    index=light.get("eventIndex")
    if type(index) is not int:
        raise ValueError("Studio lighting requires integer eventIndex")
    ev=_event(manifest,index,duration)
    intensity=_number(light.get("intensity",.6),"studioStage.lighting.intensity",0,1.2)
    seconds=_number(light.get("transitionSeconds",.3),"studioStage.lighting.transitionSeconds",.08,1.5)
    trigger=light.get("trigger","verified")
    if trigger not in ("verified","appearance"):raise ValueError("Invalid studio lighting trigger")
    if trigger=="appearance":
        onset=detect_appearance_onset(source_path,source_size,ev,fps)
    else:
        onset={"method":"verified-event-time","time":ev["t"]}
    keys=data.get("camera")
    if not isinstance(keys,list) or not 2<=len(keys)<=24:
        raise ValueError("Studio camera requires 2..24 keys")
    parsed=[]
    for k in keys:
        _fields(k,("at","startAt","scale","viewScale","yaw","pitch","center","focus","cut"),"studioStage.camera")
        at=_number(k.get("at"),"studioStage.camera.at",0,duration)
        if parsed and at<=parsed[-1].at:
            raise ValueError("Studio camera keys must increase in time")
        start=_number(k.get("startAt",parsed[-1].at if parsed else 0),"studioStage.camera.startAt",0,at)
        if parsed and start<parsed[-1].at:
            raise ValueError("Studio camera transitions cannot overlap preceding keys")
        cut=k.get("cut",False)
        if type(cut) is not bool:
            raise ValueError("Studio cut must be an explicit boolean")
        if cut:
            if not parsed:
                raise ValueError("Studio cannot cut on the first camera key")
            if abs(start-at)>1e-6:
                raise ValueError("Studio hard cut must start exactly at its destination key time")
            if abs(at*fps-round(at*fps))>1e-4:
                raise ValueError("Studio hard cut must align with a native source frame")
            if round(at*fps)>=round(duration*fps):
                raise ValueError("Studio hard cut at the exclusive final frame is not rendered")
            # Six-decimal JSON timestamps (e.g. 0.516667 for frame31/60)
            # can be 0.000000333s past the actual native frame boundary.
            # Without snapping, pose(t) applies that camera cut ONE FRAME
            # LATE, while source_aligned_cuts() and speed exclusion treat
            # it as the earlier frame. Quantize to the ONLY frame the JSON
            # already specifies; never move a cut to a different native
            # frame or tolerate a genuinely nonaligned timestamp.
            at=round(at*fps)/fps
            start=at
            if sum(key.cut for key in parsed)>=3:
                raise ValueError("Studio allows at most 3 intentional editorial cuts")
            if any(key.cut and at-key.at<.35 for key in parsed):
                raise ValueError("Studio hard cuts must be at least 0.35 seconds apart")
        scale=_number(k.get("scale"),"studioStage.camera.scale",.55,1.55)
        view_scale=_number(k.get("viewScale",1.),"studioStage.camera.viewScale",1.,1.8)
        if not immersive and view_scale!=1.:
            raise ValueError("viewScale requires opted-in camera immersion")
        yaw=_number(k.get("yaw",0),"studioStage.camera.yaw",-16,16)
        pitch=_number(k.get("pitch",0),"studioStage.camera.pitch",-12,12)
        focus=k.get("focus","wide")
        if not isinstance(focus,str) or (focus!="wide" and not
                (focus.startswith("event:") and len(focus.split(":"))==3)):
            raise ValueError("Studio focus must be wide or verified event anchor")
        if "center" in k and focus!="wide":
            raise ValueError("Studio camera cannot mix center and event focus")
        if focus=="wide":
            center=k.get("center",[.5,.5])
            if not isinstance(center,list) or len(center)!=2:
                raise ValueError("Studio center must be normalized [x,y]")
            cx=_number(center[0],"studio.center.x",.1,.9)
            cy=_number(center[1],"studio.center.y",.1,.9)
        else:
            parts=focus.split(":")
            if parts[0]!="event" or not parts[1].isdigit() or parts[2] not in ("target","result","component"):
                raise ValueError("Invalid verified studio focus")
            related=_event(manifest,int(parts[1]),duration)
            safe_time=(onset["time"] if int(parts[1])==index else related["t"])
            if parts[2]!="target" and start<safe_time-1e-6:
                raise ValueError("Studio cannot frame result before source-visible evidence")
            box=_bounds(related,{"target":"targetRect","result":"resultRect","component":"componentRect"}[parts[2]],source_size)
            fx=(box[0]+box[2]*.5)/source_size[0]
            fy=(box[1]+box[3]*.5)/source_size[1]
            cx=.5+(0.5-fx)*scale
            cy=.5+(0.5-fy)*scale*(output_size[0]/output_size[1])*(source_size[1]/source_size[0])
        parsed.append(Key(at,start,scale,yaw,pitch,cx,cy,focus,cut,view_scale))
    if parsed[0].at!=0 or abs(parsed[-1].at-duration)>.0001:
        raise ValueError("Studio camera must cover whole film exactly")
    payoff=data.get("payoff",{})
    _fields(payoff,("region","minVisible","mode","minContextVisible"),"studioStage.payoff")
    mode=payoff.get("mode","overview")
    if mode not in ("overview","detail"):
        raise ValueError("Studio payoff mode must be overview or intentional detail")
    context=_number(payoff.get("minContextVisible",.85),
                    "studioStage.payoff.minContextVisible",.65,1)
    region=payoff.get("region",f"event:{index}:result")
    if not isinstance(region,str):
        raise ValueError("Invalid studio payoff region")
    pp=region.split(":")
    if len(pp)!=3 or pp[0]!="event" or not pp[1].isdigit() or pp[2] not in ("result","component"):
        raise ValueError("Studio payoff must be an actual result/component")
    pi=int(pp[1]);pe=_event(manifest,pi,duration)
    box=_bounds(pe,"resultRect" if pp[2]=="result" else "componentRect",source_size)
    visible=_number(payoff.get("minVisible",.82),"studioStage.payoff.minVisible",.6,1)
    # Only a source-bound observed pointer+verified event can authorize this
    # additional small camera displacement. Existing films remain unchanged.
    follower=(build_follow(manifest,source_size,duration,fps,motion["follow"])
              if profile=="reference-spring" else None)
    obj=StudioStage(tuple(parsed),rgb,grain,depth,reflection,index,intensity,seconds,
                    onset,pi,pp[2],visible,mode,context,source_size,output_size,duration,box,
                    profile,shutter,fps,stage_preset,follower,immersive)
    if follower is not None:
        # All source-declared follow actions, including actions beyond the
        # stage lighting event, must remain genuine, target-visible actions.
        # A fashionable camera move may NEVER cause a verified click to
        # disappear off the visible product canvas.
        for eid in motion["follow"]["eventIndices"]:
            followed=_event(manifest,eid,duration)
            target=_bounds(followed,"targetRect",source_size)
            for ts in (followed["start"],followed["end"]):
                fraction=obj.region_visibility(ts,target)
                if fraction<.80:
                    raise ValueError(
                        f"Recorded cursor follow hides verified click {eid} "
                        f"at {ts:.3f}s: {fraction:.3f} source-visible")
        if immersive:
            for key in obj.camera:
                parts=key.focus.split(":")
                if (len(parts)==3 and parts[0]=="event" and
                        parts[1].isdigit() and parts[2]=="result"):
                    event_id=int(parts[1])
                    region=_bounds(_event(manifest,event_id,duration),
                                   "resultRect",source_size)
                    fraction=obj.region_visibility(key.at,region)
                    # A true detail may crop context; it cannot discard the
                    # majority of the independently verified result.
                    if fraction<.70:
                        raise ValueError(
                            f"Immersive result detail crops event {event_id} "
                            f"at {key.at:.3f}s ({fraction:.3f} visible)")
    actual=obj.visibility(duration)
    # The visible click/drag location, not just the broad source window, must
    # be on screen at the moment the user acts. This fail-closed gate catches
    # Gemini's plausible-looking but narratively wrong closeups.
    target_visible=obj.region_visibility(ev["start"],_bounds(ev,"targetRect",source_size))
    if target_visible<.80:
        raise ValueError(
            f"Studio framing hides genuine action target: {target_visible:.3f} visible. "
            f"At source t={ev['start']:.4f}s, camera must place the REAL event "
            f"target on-screen. Camera.center locates the entire window in "
            f"OUTPUT space; it does not aim at part of the website. Prefer "
            f"focus='event:{index}:target' in the key active at the click. "
            f"Do not invent source coordinates or move the verified event.")
    if actual+0.001<visible:
        raise ValueError(f"Final studio payoff would be clipped: {actual:.3f} visible < {visible:.3f}")
    if stage_preset in ("cloud_shadow_v1","cloud_glass_v1","cloud_window_sky_v1","cloud_window_fullglass_v1") and mode=="overview":
        # A window is not premium if the page's original heading/navigation
        # is chopped off by a model zoom. Permit only small overview pushes;
        # large authentic detail crops must explicitly select detail mode.
        timeline=sorted({0.,duration,*[k.at for k in obj.camera],
                         *[k.start_at for k in obj.camera]})
        insufficient=[(at,obj.context_visibility(at)) for at in timeline
                      if obj.context_visibility(at)<.935]
        if insufficient:
            at,fraction=min(insufficient,key=lambda row:row[1])
            raise ValueError(
                f"Locked cloud overview would crop original browser: "
                f"{fraction:.3f} source-visible at {at:.3f}s; "
                f"require >=0.935 or explicit detail mode")
    if mode=="overview" and obj.context_visibility(duration)+.001<context:
        raise ValueError(
            f"Final studio overview clips the real interface: "
            f"{obj.context_visibility(duration):.3f} < {context:.3f}")
    return obj


@lru_cache(maxsize=3)
def _matte(width,height,color,grain):
    # Extend existing retained floating_ui_stage.matte, not a replacement stage.
    source=matte(width,height).astype(np.float32)
    bgr=np.asarray(color[::-1],dtype=np.float32)
    source+=(bgr-40.)[None,None,:]
    if grain>0:
        noise=np.random.default_rng(5437).normal(0,grain,(height,width,1)).astype(np.float32)
        source+=noise
    return np.clip(source,0,255).astype(np.float32)


def render_studio_stage(stage,frame,t):
    """Composite one genuine source frame into a camera-directed physical stage."""
    sw,sh=stage.source_size
    ow,oh=stage.output_size
    if frame.shape[:2]!=(sh,sw):
        raise ValueError("Studio source video dimensions mismatch manifest")
    if stage.stage_preset in ("cloud_shadow_v1","cloud_glass_v1","cloud_window_sky_v1","cloud_window_fullglass_v1"):
        from cloud_shadow_stage import render_cloud_stage
        return render_cloud_stage(stage,frame,t)
    board=_matte(ow,oh,stage.color,stage.grain).copy()
    onset=stage.onset["time"]
    power=_eased((t-onset)/stage.light_seconds)*stage.light_intensity
    q=stage.quad(t);qi=np.rint(q).astype(np.int32)
    # Light color is genuinely extracted from visible pixels of the recorded UI.
    if power>0:
        rect=stage.result_rect
        x,y,w,h=rect
        crop=frame[max(0,int(y)):min(sh,int(y+h)),max(0,int(x)):min(sw,int(x+w))]
        if crop.size:
            tiny=cv2.resize(crop,(96,54),interpolation=cv2.INTER_AREA)
            hsv=cv2.cvtColor(tiny,cv2.COLOR_BGR2HSV)
            selected=(hsv[:,:,1]>70)&(hsv[:,:,2]>120)
            if selected.mean()>.012:
                sampled=np.median(tiny[selected].astype(np.float32),axis=0)
            else:
                sampled=np.float32((100,107,116))
        else:sampled=np.float32((100,107,116))
        yy,xx=np.ogrid[:oh,:ow]
        # Stage-only falloff around physical object and diffuse floor reflection.
        gl=np.exp(-(((xx-ow*.53)/(ow*.32))**2+((yy-oh*.65)/(oh*.43))**2)*1.5).astype(np.float32)
        fl=np.exp(-(((xx-ow*.52)/(ow*.28))**2+((yy-oh*.94)/(oh*.17))**2)*1.7).astype(np.float32)
        board+=power*(gl*.23+fl*.14)[:,:,None]*sampled[None,None,:]
    # All masks and shadows are independent of source UI. Mask at quarter
    # resolution bounds memory and keeps this reusable on a small 4-GiB VPS.
    shad=np.zeros((oh//4,ow//4),np.uint8)
    offset=np.array([stage.depth+16,stage.depth+20],np.float32)
    cv2.fillConvexPoly(shad,np.rint((q+offset)/4).astype(np.int32),200)
    shad=cv2.GaussianBlur(shad,(31,31),11)
    shad=cv2.resize(shad,(ow,oh),interpolation=cv2.INTER_LINEAR).astype(np.float32)/255
    board*=np.maximum(.54,1-.40*shad)[:,:,None]
    # A thin back face provides physical separation without inventing chrome.
    if stage.depth:
        back=qi+int(stage.depth)
        cv2.fillConvexPoly(board,back,(19.,22.,27.),lineType=cv2.LINE_AA)
        cv2.polylines(board,[back],True,(42.,45.,52.),2,cv2.LINE_AA)
    src=np.float32([[0,0],[sw-1,0],[sw-1,sh-1],[0,sh-1]])
    warp=cv2.getPerspectiveTransform(src,q)
    projected=cv2.warpPerspective(frame,warp,(ow,oh),flags=cv2.INTER_LINEAR,
                                   borderMode=cv2.BORDER_CONSTANT)
    # Shutter motion is only an exposure of the SAME genuine source frame
    # from neighboring CAMERA positions. Never mix separate UI states or
    # motion-blur the recorded cursor tip; it is overlaid once after capture.
    exposure=stage.shutter_times(t)
    if exposure is not None:
        before,after=exposure
        early=cv2.getPerspectiveTransform(src,stage.quad(before))
        late=cv2.getPerspectiveTransform(src,stage.quad(after))
        a=cv2.warpPerspective(frame,early,(ow,oh),flags=cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_CONSTANT)
        b=cv2.warpPerspective(frame,late,(ow,oh),flags=cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_CONSTANT)
        projected=((a.astype(np.uint16)+4*projected.astype(np.uint16)+
                    b.astype(np.uint16)+3)//6).astype(np.uint8)
    mask=np.zeros((oh,ow),np.uint8)
    cv2.fillConvexPoly(mask,qi,255,lineType=cv2.LINE_AA)
    alpha=mask.astype(np.float32)[:,:,None]/255.
    board=board*(1-alpha)+projected.astype(np.float32)*alpha
    if stage.reflection and power:
        bottom=int(np.max(q[:,1]));top=int(np.min(q[:,1]))
        y0=max(0,bottom+14);left=max(0,int(np.min(q[:,0])));right=min(ow,int(np.max(q[:,0])))
        h=oh-y0
        if h>15 and right-left>80 and bottom>30:
            src_top=max(0,min(bottom-5,oh)-min(h,110))
            src_bottom=min(bottom-5,oh)
            reflected=projected[src_top:src_bottom,left:right]
            if reflected.shape[0]>5:
                patch=cv2.resize(cv2.flip(reflected,0),(right-left,h))
                patch=cv2.GaussianBlur(patch,(15,15),6).astype(np.float32)
                decay=np.exp(-np.linspace(0,4,h,dtype=np.float32))[:,None,None]
                a=stage.reflection*power*decay
                board[y0:,left:right]=board[y0:,left:right]*(1-a)+patch*a
    cv2.polylines(board,[qi],True,(77.,80.,86.),1,cv2.LINE_AA)
    return np.uint8(np.clip(board,0,255))
