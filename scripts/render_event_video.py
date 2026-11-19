#!/usr/bin/env python3
"""Render real product footage using evidence-based, event-driven camera focus.

Input: verified browser recording + timestamped DOM sidecar. No reconstructed UI.
Frame: Shotcandy browser-dark.svg, fitted to real video pixels with MIT notice.
Audio: optional operator-supplied licensed track; no synthetic clicks or voices.
No manually authored zoom keyframes or changes to captured interface.
"""
from __future__ import annotations
import argparse,io,json,math,subprocess,sys,time
from urllib.parse import urlsplit
from pathlib import Path

import cairosvg, cv2, numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageOps
from autozoom_event_planner import plan,sample_camera,smooth5
from anchored_result_cut import plan_result_cut
from verified_workflow_editorial import plan_verified_workflow
from source_region_mask import dim_outside_region
from recorded_pointer import pointer_track, project_pointer
from glass_loupe import LoupeStyle,apply_loupe,plan_loupe
from slider_framing import slider_framing
from live_edit_plan import sample_zoom

cv2.setNumThreads(2)

PROJECT=Path(__file__).resolve().parents[1]
DEFAULT_ROOT=PROJECT/"studio"/".tmp"/"sauce-autozoom-v1"
parser=argparse.ArgumentParser(description="Render a real browser recording with an evidence-based camera path.")
parser.add_argument("--video",type=Path,help="An actual captured browser recording, not reconstructed footage")
parser.add_argument("--manifest",type=Path,help="Timestamped capture sidecar with verified DOM events")
parser.add_argument("--film-plan",type=Path,help="Validated source-true creative plan JSON; alternative to hardcoded site edits")
parser.add_argument("--validate-only",action="store_true",help="Check source, keyframes and motion without exporting frames")
parser.add_argument("--output",type=Path,help="Output MP4 path (default: alongside the manifest)")
parser.add_argument("--music",type=Path,help="Optional licensed audio recording")
parser.add_argument("--preview",type=float)
parser.add_argument("--seconds",type=float)
parser.add_argument("--static",action="store_true")
parser.add_argument("--anchored-result-cut",action="store_true",
                    help="Opt into a fullscreen match cut on a verified product result")
parser.add_argument("--trim-real-idle-intro",action="store_true",
                    help="Exclude source-proven idle opening before its first actual pointer motion")
parser.add_argument("--verified-workflow-editorial",action="store_true",
                    help="Opt-in source-verified UI workflow story: action, result and hold")
parser.add_argument("--guided-result",action="store_true",
                    help="Frame the recorded click and smoothly push into its verified result")
parser.add_argument("--recorded-pointer",action="store_true",
                    help="Draw the timed mouse path on cursorless fullscreen footage")
parser.add_argument("--result-focus",action="store_true",
                    help="Gently dim the context outside the result after an anchored cut")
parser.add_argument("--slider-framing", action="store_true",
                    help="Keep the verified slider and its result in an undistorted crop")
parser.add_argument("--glass-loupe",action="store_true",help="Magnify a verified slider and its observed result")
parser.add_argument("--camera-profile",choices=["standard","screenstudio","action-first"],default="standard",
                    help="Reference or post-result timing; all focus targets still require observed DOM change")
parser.add_argument("--presentation",choices=["window","fullscreen"],default="window",
                    help="Window uses a licensed browser frame; fullscreen preserves raw product pixels without invented chrome")
parser.add_argument("--stage-image",type=Path,help="Operator-supplied backdrop for the window presentation")
args=parser.parse_args()
if args.film_plan:
    if any((args.anchored_result_cut,args.trim_real_idle_intro,args.verified_workflow_editorial,
            args.guided_result,args.slider_framing,args.result_focus,args.glass_loupe,
            args.stage_image is not None,args.static)):
        parser.error("--film-plan owns the camera/editorial path; conflicting legacy flags are rejected")
    # The film plan is authoritative for presentation and pointer configuration.
    FILM_PLAN_DATA=json.loads(args.film_plan.read_text())
    args.presentation=FILM_PLAN_DATA.get("presentation","fullscreen")
    args.recorded_pointer=(FILM_PLAN_DATA.get("cursor")=="recorded" and "glassLoupe" not in FILM_PLAN_DATA)
else:
    FILM_PLAN_DATA=None
if args.validate_only and FILM_PLAN_DATA is None:
    parser.error("--validate-only requires --film-plan")
if args.stage_image and (args.presentation!="window" or not args.stage_image.is_file()):
    parser.error("--stage-image requires an existing image and window presentation")
if args.anchored_result_cut and (args.presentation!="fullscreen" or args.glass_loupe):
    parser.error("--anchored-result-cut requires fullscreen presentation and its own camera")
if args.result_focus and not args.anchored_result_cut:
    parser.error("--result-focus requires --anchored-result-cut")
if args.trim_real_idle_intro and not args.verified_workflow_editorial:
    parser.error("--trim-real-idle-intro requires the verified editorial workflow")
if args.verified_workflow_editorial and (
        args.presentation!="fullscreen" or args.glass_loupe or
        args.anchored_result_cut or args.guided_result or args.static):
    parser.error("Verified workflow editorial requires a moving fullscreen source")
if args.guided_result and (args.presentation!="fullscreen" or args.glass_loupe
                           or args.anchored_result_cut or args.static):
    parser.error("--guided-result requires a fullscreen moving camera")
if args.recorded_pointer and (args.presentation!="fullscreen" or args.glass_loupe):
    parser.error("--recorded-pointer requires fullscreen without a loupe")
ROOT=(args.manifest.parent if args.manifest else DEFAULT_ROOT).resolve()
SRC=(args.video or ROOT/"linear-official-preview-real-60.mp4").resolve()
MANIFEST_PATH=(args.manifest or ROOT/"linear-interactions.json").resolve()
if not SRC.is_file() or not MANIFEST_PATH.is_file():
    parser.error("Existing --video and --manifest inputs are required")
MANIFEST=json.loads(MANIFEST_PATH.read_text())
probe=json.loads(subprocess.check_output([
    "ffprobe","-v","error","-select_streams","v:0",
    "-show_entries","stream=width,height,avg_frame_rate:format=duration",
    "-of","json",str(SRC)],text=True))
stream=probe["streams"][0]
INPUT_W,INPUT_H=int(stream["width"]),int(stream["height"])
POINTER=pointer_track(MANIFEST,INPUT_W,INPUT_H) if args.recorded_pointer else None
POINTER_PRESSES = tuple(event["t"] for event in MANIFEST.get("events", [])
                       if event.get("kind") == "pointer_down"
                       and isinstance(event.get("t"), (int, float))
                       and math.isfinite(event["t"])) if POINTER is not None else ()
if args.recorded_pointer and POINTER is None:
    parser.error("--recorded-pointer requires explicit cursorless footage and ordered pointer samples")
rect=MANIFEST.get("capture_rect",{})
if rect and (int(rect["width"]),int(rect["height"]))!=(INPUT_W,INPUT_H):
    parser.error("Manifest capture rectangle must match the source video pixels")
from fractions import Fraction
FPS=int(round(float(Fraction(stream["avg_frame_rate"]))))
if FPS not in (24,25,30,50,60):
    parser.error("Source must have a supported constant 24/25/30/50/60 fps video stream")
DURATION=min(float(MANIFEST.get("duration") or probe["format"]["duration"]),
             float(probe["format"]["duration"]))
FILM_PLAN=None
LOUPE_STYLE=LoupeStyle()
WINDOW_SCALE=None
ISOLATION=None
if FILM_PLAN_DATA is not None:
    from film_plan import load_film_plan, load_window
    FILM_PLAN=load_film_plan(FILM_PLAN_DATA, MANIFEST,SRC,MANIFEST_PATH,(INPUT_W,INPUT_H),
                            DURATION,args.film_plan)
    if "glassLoupe" in FILM_PLAN_DATA:
        LOUPE_STYLE=LoupeStyle.from_plan(FILM_PLAN_DATA["glassLoupe"])
        args.glass_loupe=True
    if "window" in FILM_PLAN_DATA:
        WINDOW_SCALE,args.stage_image=load_window(FILM_PLAN_DATA["window"],args.film_plan)
    if args.seconds is not None and not .5<=args.seconds<=FILM_PLAN.duration:
        parser.error("Review duration must be within the source-verified plan")
    args.seconds=args.seconds or FILM_PLAN.duration
    from ui_isolation_layers import load_isolation_composition
    ISOLATION=load_isolation_composition(FILM_PLAN_DATA.get("composition"),MANIFEST,
                    SRC,(INPUT_W,INPUT_H),DURATION)
    if ISOLATION is not None and FILM_PLAN.presentation!="fullscreen":
        raise ValueError("JSON UI isolation requires fullscreen composition")
    if FILM_PLAN.audio_file and args.music:
        parser.error("Film-plan audio and CLI music cannot be mixed implicitly")

if DURATION<0.5:parser.error("Video duration is too short")
VENDOR=PROJECT/"studio"/"assets"/"vendor"/"shotcandy"
FRAME=VENDOR/"browser-dark.svg"
MUSIC=args.music.resolve() if args.music else (
    PROJECT.parent/"sauce-demo-assets"/"digital-clouds-mixkit.mp3"
    if args.manifest is None else Path("/__no_licensed_audio__")
)
if args.music and not MUSIC.is_file():parser.error("Specified licensed audio file is missing")
known_url=next((MANIFEST[k] for k in ("source","site","url","final_page")
                if isinstance(MANIFEST.get(k),str) and MANIFEST[k].startswith(("http://","https://"))),None)
SCREEN_URL=(urlsplit(known_url).hostname[:34] if known_url and urlsplit(known_url).hostname else "Recorded product")
MASTER_W,MASTER_H=1920,1080
FRAME_W=1440
CONTENT_H=round(FRAME_W*INPUT_H/INPUT_W)
FRAME_HEADER_H=46
FRAME_H=FRAME_HEADER_H+CONTENT_H
FRAME_SCALE=min(1.114,(MASTER_W-210)/FRAME_W,(MASTER_H-150)/FRAME_H)
if WINDOW_SCALE is not None:
    FRAME_SCALE *= WINDOW_SCALE
elif args.glass_loupe:
    FRAME_SCALE *= .865
WINDOW_W=round(FRAME_W*FRAME_SCALE)
WINDOW_H=round(FRAME_H*FRAME_SCALE)
WINDOW_X=round((MASTER_W-WINDOW_W)/2)
WINDOW_Y=round((MASTER_H-WINDOW_H)/2)
SCREEN_W=WINDOW_W
SCREEN_H=round(CONTENT_H*FRAME_SCALE)
SCREEN_X=WINDOW_X
SCREEN_Y=WINDOW_Y+round(FRAME_HEADER_H*FRAME_SCALE)
SHOTS=plan(MANIFEST.get("events",[]),{"width":INPUT_W,"height":INPUT_H},DURATION,profile="action-first" if args.guided_result else args.camera_profile)
if args.presentation=="fullscreen":
    SCREEN_W,SCREEN_H=MASTER_W,MASTER_H
    SCREEN_X,SCREEN_Y=0,0
SLIDER_SHOT = None
EDIT_CAMERA = MANIFEST.get("edit_camera") or {}
if args.slider_framing:
    if args.presentation != "fullscreen" or args.glass_loupe or POINTER is None:
        parser.error("Slider framing requires a recorded pointer and fullscreen footage")
    slider_events = [event for event in MANIFEST.get("events", []) if event.get("kind") == "slider_change"]
    if len(slider_events) != 1 or not 0 < slider_events[0]["t"] < DURATION:
        parser.error("Expected one timed slider result")
    SLIDER_SHOT = slider_framing(slider_events[0], INPUT_W, INPUT_H)
LOUPE_SHOTS=plan_loupe(MANIFEST,INPUT_W,INPUT_H,DURATION) if args.glass_loupe else []
if FILM_PLAN is not None and args.glass_loupe and not LOUPE_SHOTS:
    parser.error("JSON glass loupe requires a verified slider with recorded pointer samples")

RESULT_CUT=plan_result_cut(MANIFEST.get("events",[]),(INPUT_W,INPUT_H),
                           (MASTER_W,MASTER_H),FPS,min(args.seconds or DURATION,DURATION)
                           ) if args.anchored_result_cut and not args.static else None
WORKFLOW_SHOT=plan_verified_workflow(
    MANIFEST.get("events",[]),(INPUT_W,INPUT_H),(MASTER_W,MASTER_H),
    min(args.seconds or DURATION,DURATION),
    MANIFEST.get("lead_s",0)) if args.verified_workflow_editorial else None
if args.verified_workflow_editorial and WORKFLOW_SHOT is None:
    parser.error("Missing verified selection, button action, result, or reading hold")
TRIM_FRAMES=0
if args.trim_real_idle_intro:
    samples=MANIFEST.get("pointer_samples")
    lead=MANIFEST.get("lead_s",0)
    if not isinstance(samples,list) or not samples or not isinstance(lead,(float,int)):
        parser.error("Need recorded first-pointer timestamps and source encoder lead")
    first=next((float(p["t"]) for p in samples if isinstance(p,dict)
                and type(p.get("t")) in (int,float)
                and math.isfinite(p["t"]) and p["t"]>=0),None)
    if first is None:
        parser.error("No real pointer movement to ground intro trim")
    TRIM_FRAMES=max(0,math.floor((first+lead-.7)*FPS))
    if TRIM_FRAMES>=math.floor(WORKFLOW_SHOT.button_start*FPS)-30:
        parser.error("Source trim would remove meaningful action")
GUIDED_SHOT=SHOTS[0] if args.guided_result and SHOTS else None
GUIDED_CLICK=next((event.get("targetRect") for event in MANIFEST.get("events", [])
                   if event.get("kind")=="click" and GUIDED_SHOT and
                   event.get("t")==GUIDED_SHOT.click),None)
if not isinstance(GUIDED_CLICK,dict) or not all(
        isinstance(GUIDED_CLICK.get(key),(int,float)) and math.isfinite(GUIDED_CLICK[key])
        for key in ("x","y","width","height")) or not (
            0<=GUIDED_CLICK["x"]<GUIDED_CLICK["x"]+GUIDED_CLICK["width"]<=INPUT_W and
            0<=GUIDED_CLICK["y"]<GUIDED_CLICK["y"]+GUIDED_CLICK["height"]<=INPUT_H):
    GUIDED_SHOT=None
WORKDIR=(args.output.resolve().parent if args.output else ROOT)
WORKDIR.mkdir(parents=True,exist_ok=True)
(WORKDIR/"camera-plan.json").write_text(json.dumps(
 {"source":str(MANIFEST_PATH),"algorithm":"event-driven camera planner, no authored cues",
  "profile":("verified-workflow-editorial" if WORKFLOW_SHOT else
             "guided-result" if GUIDED_SHOT else args.camera_profile),
  "presentation":args.presentation,
  "verifiedWorkflow":WORKFLOW_SHOT.receipt() if WORKFLOW_SHOT else None,
  "trimSourceFrames":TRIM_FRAMES,
  "anchoredResultFrame":RESULT_CUT.frame if RESULT_CUT else None,
  "guidedResultMotion":({"start":GUIDED_SHOT.start+.18,"settle":GUIDED_SHOT.start+.96}
                        if GUIDED_SHOT else None),
  "shots":[] if RESULT_CUT else [s.dictionary() for s in SHOTS]},indent=2))

def render_shotcandy_overlay():
    src=FRAME.read_text()
    # Adapt only the asset's overall height to the 1320:720 content ratio,
    # keeping its authentic controls, proportions, path shapes and typography.
    # Original screen: 1440x900. Adapted screen: 1440x785px.
    original=946.08
    total=46.08+CONTENT_H
    old_corner=923.04
    new_corner=total-23.04
    old_stroke=945.58
    new_stroke=total-.5
    src=src.replace("946.08",f"{total:.2f}")
    src=src.replace("923.04",f"{new_corner:.2f}")
    src=src.replace("945.58",f"{new_stroke:.2f}")
    src=src.replace('height="900"',f'height="{CONTENT_H}"')
    src=src.replace("quokka.app/overview",SCREEN_URL)
    # Keep Shotcandy's frame, clip paths, controls and border; make only the
    # placeholder body transparent so the actual capture occupies #screen.
    src=src.replace('fill="#EDE6DC"','fill="none"')
    src=src.replace('fill="url(#hatch)" opacity=".5"','fill="none" opacity="0"')
    (WORKDIR/"shotcandy-browser-dark-adapted.svg").write_text(src)
    png=cairosvg.svg2png(bytestring=src.encode("utf-8"),
                          output_width=FRAME_W,output_height=FRAME_H)
    overlay=Image.open(io.BytesIO(png)).convert("RGBA")
    overlay=overlay.resize((WINDOW_W,WINDOW_H),Image.Resampling.LANCZOS)
    # Preserve original Shotcandy MIT attribution next to the derived SVG.
    (WORKDIR/"SHOTCANDY-LICENSE.txt").write_text((VENDOR/"LICENSE").read_text())
    return np.asarray(overlay,dtype=np.uint8)[:,:,[2,1,0,3]].copy()

def prepare_stage():
    if args.presentation=="fullscreen":
        return (np.full((MASTER_H,MASTER_W,3),18,dtype=np.uint8),
                np.zeros((1,1,4),dtype=np.uint8),
                np.ones((1,1,1),dtype=np.float32))
    frame=render_shotcandy_overlay()
    # Matte gray, restrained neutral. No invented macOS bar, gradient or fake desktop wallpaper.
    if args.stage_image:
        with Image.open(args.stage_image) as artwork:
            background=ImageOps.fit(ImageOps.exif_transpose(artwork).convert("RGB"),
                                    (MASTER_W,MASTER_H),Image.Resampling.LANCZOS)
    else:
        background=Image.new("RGB",(MASTER_W,MASTER_H),(231,230,228))
    mask=Image.new("L",(MASTER_W,MASTER_H),0)
    painter=ImageDraw.Draw(mask)
    painter.rounded_rectangle((WINDOW_X,WINDOW_Y,WINDOW_X+WINDOW_W,
                               WINDOW_Y+WINDOW_H),radius=24*FRAME_SCALE,fill=255)
    shadow=mask.filter(ImageFilter.GaussianBlur(34))
    # Slight vertical offset produces lift without flashy glow.
    shifted=Image.new("L",(MASTER_W,MASTER_H),0)
    shifted.paste(shadow,(0,14))
    shifted=shifted.point(lambda x:int(x*.31))
    darkness=Image.new("RGB",(MASTER_W,MASTER_H),(15,16,19))
    background.paste(darkness,(0,0),shifted)
    bg=np.asarray(background,dtype=np.uint8)[:,:,::-1].copy()
    corner=Image.new("L",(FRAME_W,FRAME_H),0)
    ImageDraw.Draw(corner).rounded_rectangle((0,0,FRAME_W-1,FRAME_H-1),
                            radius=23,fill=255)
    # Content mask clips only the natural outer frame corners at the bottom.
    scaled_corner=corner.resize((WINDOW_W,WINDOW_H),Image.Resampling.LANCZOS)
    screen_mask=np.asarray(scaled_corner.crop((
        0,round(FRAME_HEADER_H*FRAME_SCALE),WINDOW_W,
        round(FRAME_HEADER_H*FRAME_SCALE)+SCREEN_H)),dtype=np.uint8)
    return bg,frame,screen_mask.astype(np.float32)[:,:,None]/255.

BASE,OVERLAY,SCREEN_MASK=prepare_stage()
OVERLAY_ALPHA=OVERLAY[:,:,3:4].astype(np.float32)/255.0
OVERLAY_RGB=OVERLAY[:,:,:3].astype(np.float32)

def camera_matrix(t,static=False):
    if FILM_PLAN is not None:
        return FILM_PLAN.at(t,(SCREEN_W,SCREEN_H),stretch=args.glass_loupe)
    if WORKFLOW_SHOT is not None and not static:
        return WORKFLOW_SHOT.matrix(t)
    if RESULT_CUT is not None and not static and round(t*FPS)>=RESULT_CUT.frame:
        return RESULT_CUT.matrix.copy()
    zoom,fx,fy= (1,.5,.5) if static or RESULT_CUT is not None else sample_camera(t,SHOTS)
    if GUIDED_SHOT is not None and not static:
        click=GUIDED_CLICK
        result=GUIDED_SHOT.result_rect
        left=min(click["x"],result["x"])
        right=max(click["x"]+click["width"],result["x"]+result["width"])
        top=min(click["y"],result["y"])
        bottom=max(click["y"]+click["height"],result["y"]+result["height"])
        opening=min(1.48,INPUT_W/(right-left+INPUT_W*.08),
                    INPUT_H/(bottom-top+INPUT_H*.08))
        end=min(2.2,INPUT_W/(result["width"]+INPUT_W*.16),
                INPUT_H/(result["height"]+INPUT_H*.16))
        progress=smooth5((t-GUIDED_SHOT.start-.18)/.78)
        zoom=opening+(max(opening,end)-opening)*progress
        fx=((left+right)*.5/INPUT_W)*(1-progress)+(GUIDED_SHOT.focus_x-.12/end)*progress
        fy=((top+bottom)*.5/INPUT_H)*(1-progress)+GUIDED_SHOT.focus_y*progress
    if SLIDER_SHOT is not None and not static:
        opening, tight, fx, fy = SLIDER_SHOT
        progress = smooth5((t - slider_events[0]["t"]) / .55)
        zoom = sample_zoom(t,EDIT_CAMERA["keys"],smooth5) if EDIT_CAMERA else opening + (tight - opening) * progress
    if args.presentation=="fullscreen":
        # Pixel-perfect isotropic scaling. Preserve source aspect ratio.
        # The target content region moves toward the optical center without
        # exposing off-canvas or distorting a single source UI pixel.
        factor=min(SCREEN_W/INPUT_W,SCREEN_H/INPUT_H)*zoom
        crop_w,crop_h=INPUT_W*factor,INPUT_H*factor
        dx=SCREEN_W/2-fx*crop_w
        dy=SCREEN_H/2-fy*crop_h
        dx=(max(SCREEN_W-crop_w,min(0.,dx)) if crop_w>=SCREEN_W
            else (SCREEN_W-crop_w)/2)
        dy=(max(SCREEN_H-crop_h,min(0.,dy)) if crop_h>=SCREEN_H
            else (SCREEN_H-crop_h)/2)
        return np.array([[factor,0.,dx],[0.,factor,dy]],dtype=np.float64)
    pan_x=max(0.,min(1.,.5+(fx-.5)*1.90))
    pan_y=max(0.,min(1.,.5+(fy-.5)*1.90))
    sx=(SCREEN_W/INPUT_W)*zoom
    sy=(SCREEN_H/INPUT_H)*zoom
    dx=(SCREEN_W-INPUT_W*sx)*pan_x
    dy=(SCREEN_H-INPUT_H*sy)*pan_y
    return np.array([[sx,0.,dx],[0.,sy,dy]],dtype=np.float64)

def compose_window(source,t,static=False):
    if ISOLATION is not None:
        from ui_isolation_layers import render_isolated_stage
        isolated=render_isolated_stage(ISOLATION,t,(SCREEN_W,SCREEN_H))
        if isolated is not None:
            return isolated
    mat=camera_matrix(t,static=static)
    content=cv2.warpAffine(source,mat,(SCREEN_W,SCREEN_H),
           flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
    if args.presentation=="fullscreen":
        # Blank bars only occur when source is not 16:9; no fake desktop.
        if INPUT_W/INPUT_H!=SCREEN_W/SCREEN_H and mat[0,0]<=min(SCREEN_W/INPUT_W,SCREEN_H/INPUT_H)+1e-4:
            cropped=content.copy()
            if INPUT_W/INPUT_H>SCREEN_W/SCREEN_H:
                h=round(INPUT_H*mat[1,1]); y=round((SCREEN_H-h)/2)
                cropped[:max(0,y),:]=(18,18,18)
                cropped[min(SCREEN_H,y+h):,:]=(18,18,18)
            else:
                width=round(INPUT_W*mat[0,0]);x=round((SCREEN_W-width)/2)
                cropped[:,:max(0,x)]=(18,18,18)
                cropped[:,min(SCREEN_W,x+width):]=(18,18,18)
            return cropped
        return content
    stage=BASE.copy()
    clip=stage[SCREEN_Y:SCREEN_Y+SCREEN_H,SCREEN_X:SCREEN_X+SCREEN_W]
    if SCREEN_MASK.min()>=1:
        clip[:]=content
    else:
        clip[:]=np.clip(content.astype(np.float32)*SCREEN_MASK+
                        clip.astype(np.float32)*(1-SCREEN_MASK),0,255).astype(np.uint8)
    # Use the installed SVG frame itself as the window artwork.
    window=stage[WINDOW_Y:WINDOW_Y+WINDOW_H,WINDOW_X:WINDOW_X+WINDOW_W]
    window[:]=np.clip(OVERLAY_RGB*OVERLAY_ALPHA+
             window.astype(np.float32)*(1-OVERLAY_ALPHA),0,255).astype(np.uint8)
    return stage

def apply(source,t,static=False):
    stage=compose_window(source,t,static)
    if POINTER is not None and (ISOLATION is None or not ISOLATION.active(t)) and (FILM_PLAN is None or t >= float(POINTER[0,0])):
        press=max((1.-smooth5((t-down)/.18) for down in POINTER_PRESSES
                   if 0<=t-down<.18),default=0.)
        stage=project_pointer(stage,POINTER,camera_matrix(t,static),t,
                              scale=(.73 if FILM_PLAN is not None else
                                     EDIT_CAMERA.get("cursor_scale",.85) if SLIDER_SHOT
                                     else 1.6-.18*press))
    if args.result_focus and RESULT_CUT is not None and not static:
        elapsed_frames = round(t * FPS) - RESULT_CUT.frame
        if elapsed_frames > 0:
            x0, y0, x1, y1 = RESULT_CUT.source_bounds
            left, top = RESULT_CUT.matrix @ [x0, y0, 1.]
            right, bottom = RESULT_CUT.matrix @ [x1, y1, 1.]
            return dim_outside_region(stage, (left, top, right, bottom),
                                      .08 * smooth5(elapsed_frames / (FPS * .25)))
    shot=next((shot for shot in LOUPE_SHOTS if shot.start<=t<shot.end),None)
    if shot is None:
        return stage
    matrix=camera_matrix(t,static)
    matrix[:,2]+=(SCREEN_X,SCREEN_Y)
    return apply_loupe(stage,source,matrix,shot,t,LOUPE_STYLE)

def diagnostics():
    end_frames=round(min(args.seconds or DURATION,DURATION)*FPS)
    frames=end_frames-TRIM_FRAMES
    if frames<24:raise ValueError("Too few genuine source frames after trim")
    rows=np.array([camera_matrix((TRIM_FRAMES+i)/FPS,static=args.static).reshape(-1)
                   for i in range(frames)])
    vel=np.diff(rows,axis=0)
    accel=np.diff(vel,axis=0)
    continuous_vel=vel
    if WORKFLOW_SHOT is not None:
        # A documented, intentional action-to-result edit is not a
        # single-frame camera pan. Measure motion speed separately.
        cut_at=math.ceil(WORKFLOW_SHOT.result_start*FPS)-TRIM_FRAMES
        if 0<cut_at<len(rows):
            continuous_vel=np.delete(vel,cut_at-1,axis=0)
    metrics={
       "frames":len(rows),
       "zoom_shots":(len(FILM_PLAN.camera_keys)-1 if FILM_PLAN is not None else
                     0 if args.static or RESULT_CUT else len(SHOTS)),
       "anchored_result_frame":RESULT_CUT.frame if RESULT_CUT else None,
       "result_focus":bool(args.result_focus and RESULT_CUT),
       "verified_workflow_editorial":WORKFLOW_SHOT is not None,
       "trimmed_real_idle_frames":TRIM_FRAMES,
       "cut_on_verified_result_source_frame":(
           math.ceil(WORKFLOW_SHOT.result_start*FPS) if WORKFLOW_SHOT else None),
       "glass_loupe_shots":len(LOUPE_SHOTS),
       "slider_framed": SLIDER_SHOT is not None,
       "recorded_pointer_samples":len(POINTER) if POINTER is not None else 0,
       "max_translation_per_frame_px":round(float(np.max(np.abs(vel[:,[2,5]]),initial=0)),4),
       "max_continuous_translation_per_frame_px":round(
           float(np.max(np.abs(continuous_vel[:,[2,5]]),initial=0)),4),
       "max_translation_acceleration_px_per_frame_sq":
             round(float(np.max(np.abs(accel[:,[2,5]]),initial=0)),4),
       "max_zoom_per_frame":round(float(np.max(np.abs(vel[:,0]),initial=0)),8),
       "frame_source":("unmodified browser recording" if args.presentation=="fullscreen" else "Shotcandy MIT browser-dark.svg"),
       "camera_profile":("json-film-plan-v1" if FILM_PLAN is not None else
                         "verified-workflow-editorial" if WORKFLOW_SHOT else
                         "guided-result" if GUIDED_SHOT else args.camera_profile),
       "presentation":args.presentation,
       "source_capture":str(MANIFEST.get("source_kind",MANIFEST.get("capture","verified browser recording"))),
       "camera_plan_source":("source-verified JSON keyframes"
                              if FILM_PLAN is not None else "recorded click and DOM state change"),
       "browser_frame_not_handmade":True,
       "stable_window":True,
       "interpolation":("verified outcome cut + C2 quintic motion"
                        if WORKFLOW_SHOT else
                        "hard cut" if RESULT_CUT else "C2 quintic"),
    }
    if not np.isfinite(rows).all():raise RuntimeError("Nonfinite camera matrix")
    if FILM_PLAN is not None:
        # Validate motion in 60fps-equivalent units, even for 24/25/30fps sources.
        speed60=metrics["max_translation_per_frame_px"] * FPS/60
        zoom60=metrics["max_zoom_per_frame"] * FPS/60
        if speed60 > 16.0 or zoom60 > .015:
            raise ValueError("JSON film camera moves too abruptly: revise the keyframes, not the source video")
    (WORKDIR/"camera-metrics.json").write_text(json.dumps(metrics,indent=2))
    print("CAMERA_METRICS",json.dumps(metrics),flush=True)
    return metrics

def render(output,seconds=None,static=False):
    end_frames=min(round((seconds or DURATION)*FPS),round(DURATION*FPS))
    frames=end_frames-TRIM_FRAMES
    if frames<24:raise ValueError("No meaningful source frames after cut")
    decoder=["ffmpeg","-hide_banner","-loglevel","error"]
    if TRIM_FRAMES:
        decoder+=["-ss",f"{TRIM_FRAMES/FPS:.9f}"]
    decoder+=["-i",str(SRC),"-f","rawvideo","-pix_fmt","bgr24","pipe:1"]
    ffread=subprocess.Popen(decoder,stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,bufsize=2*1024*1024)
    cmd=[
       "ffmpeg","-hide_banner","-loglevel","error","-y",
       "-f","rawvideo","-pix_fmt","bgr24",
       "-video_size",f"{MASTER_W}x{MASTER_H}",
       "-framerate",str(FPS),"-i","pipe:0"]
    if FILM_PLAN is not None and FILM_PLAN.audio_file is not None:
        cmd+=["-i",str(FILM_PLAN.audio_file),"-map","0:v:0","-map","1:a:0",
              "-c:a","aac","-ar","48000","-b:a","128k"]
    elif MUSIC.exists():
        cmd+=["-stream_loop","-1","-i",str(MUSIC),
              "-filter_complex",
              f"[1:a]atrim=duration={frames/FPS},volume=.16,highpass=f=60,lowpass=f=9000,"
              "afade=t=in:st=0:d=0.8,"
              f"afade=t=out:st={max(0,frames/FPS-1.5)}:d=1.25,"
              "alimiter=limit=.70:level=0[a]",
              "-map","0:v:0","-map","[a]","-c:a","aac","-b:a","128k"]
    else:cmd+=["-an"]
    cmd+=["-t",str(frames/FPS),
       "-c:v","libx264","-pix_fmt","yuv420p","-profile:v","high",
       "-level:v","4.2","-preset","veryfast","-crf","17",
       "-g","120","-threads","6","-movflags","+faststart",str(output)]
    encoder=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=2*1024*1024)
    frame_size=INPUT_W*INPUT_H*3
    start=time.monotonic()
    for i in range(frames):
        raw=ffread.stdout.read(frame_size)
        if len(raw)!=frame_size: raise RuntimeError(f"Short source frame: {i}")
        src=np.frombuffer(raw,dtype=np.uint8).reshape(INPUT_H,INPUT_W,3)
        image=apply(src,(i+TRIM_FRAMES)/FPS,static=static)
        encoder.stdin.write(image.tobytes())
        if i%180==0:print("RENDER",i,"/",frames,
                         round(time.monotonic()-start,2),"sec",flush=True)
    encoder.stdin.close()
    ffread.stdout.close()
    err=encoder.stderr.read().decode(errors="replace")
    code=encoder.wait(timeout=150)
    ffread.wait(timeout=150)
    if code:raise RuntimeError(err[-3000:])
    video=json.loads(subprocess.check_output([
        "ffprobe","-v","error","-show_entries",
        "stream=codec_name,codec_type,width,height,nb_frames,avg_frame_rate:format=duration,size","-of","json",str(output)],text=True))
    visual=next(s for s in video["streams"] if s["codec_type"]=="video")
    assert visual["nb_frames"]==str(frames)
    subprocess.run(["ffmpeg","-v","error","-xerror","-i",str(output),
                   "-f","null","-"],check=True,timeout=240)
    record={"file":str(output),"duration":frames/FPS,"frames":frames,
            "trimmed_source_frames":TRIM_FRAMES,
            "source_end_frame":end_frames,
            "source_timeline_preserved":True,
            "render_seconds":round(time.monotonic()-start,2),
            "full_decode_verified":True,"static":static,
            "video":video}
    if FILM_PLAN is not None:
        record["film_plan"]={"schema":"sauce-film-plan-v1",
            "planSha256":__import__("hashlib").sha256(args.film_plan.read_bytes()).hexdigest(),
            "sourceSha256":FILM_PLAN.source_sha256,
            "manifestSha256":FILM_PLAN.manifest_sha256,
            "cameraKeyframes":len(FILM_PLAN.camera_keys),
            "audioFileIncluded":bool(FILM_PLAN.audio_file),
            "creativeApproval":False}
        if ISOLATION is not None:
            record["film_plan"]["isolation"]={
                "mode":"isolated-ui","startAt":ISOLATION.start_at,
                "sourceFreeze":True,
                "layers":[{"id":layer.id,"sourceAt":layer.source_at,
                           "anchor":layer.anchor,"boundsPx":layer.source_bounds,
                           "sourceFrameIndex":layer.source_frame_index,
                           "cropPixelsSha256":layer.source_crop_sha256}
                          for layer in ISOLATION.layers]}
    output.with_suffix(".json").write_text(json.dumps(record,indent=2))
    print("RENDER_RECEIPT",json.dumps(record),flush=True)

if __name__=="__main__":
    diagnostics()
    if args.validate_only:
        print("JSON_FILM_PLAN_VALIDATED",json.dumps({
            "sourceSha256":FILM_PLAN.source_sha256,
            "manifestSha256":FILM_PLAN.manifest_sha256,
            "planSha256":__import__("hashlib").sha256(args.film_plan.read_bytes()).hexdigest(),
            "durationSeconds":FILM_PLAN.duration,
            "keyframes":len(FILM_PLAN.camera_keys),
            "creativeApproval":False},sort_keys=True),flush=True)
        sys.exit(0)
    if args.preview is not None:
        if args.preview < 0 or args.preview >= DURATION:
            parser.error("--preview must be within the actual recording duration")
        cmd=["ffmpeg","-hide_banner","-loglevel","error",
             "-ss",str(args.preview),"-i",str(SRC),
             "-frames:v","1","-f","rawvideo","-pix_fmt","bgr24","pipe:1"]
        raw=subprocess.check_output(cmd)
        src=np.frombuffer(raw,dtype=np.uint8).reshape(INPUT_H,INPUT_W,3)
        path=args.output or ROOT/("sauce-static-preview.jpg" if args.static else "sauce-autozoom-preview.jpg")
        path.parent.mkdir(parents=True,exist_ok=True)
        cv2.imwrite(str(path),apply(src,args.preview,args.static),[cv2.IMWRITE_JPEG_QUALITY,88])
        print("PREVIEW",path,path.stat().st_size)
    else:
        name=("linear-static-master-1080p60.mp4" if args.static else
              "linear-autozoom-master-1080p60.mp4") if args.manifest is None else "sauce-autozoom-master.mp4"
        if args.seconds is not None:name=name.replace(".mp4","-smoke.mp4")
        output=(args.output or ROOT/name).resolve()
        output.parent.mkdir(parents=True,exist_ok=True)
        render(output,args.seconds,args.static)
