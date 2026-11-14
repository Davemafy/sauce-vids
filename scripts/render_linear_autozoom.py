#!/usr/bin/env python3
"""Render a real Linear preview with event-driven Screen Studio-style focus.

Input: X11 60fps recording + timestamped DOM sidecar. Not a reconstructed UI.
Frame: Shotcandy browser-dark.svg, adapted to 16:9 content with MIT notice.
Audio: quiet licensed existing Sauce track; no synthesized clicks/voices.
No manually authored zoom keyframes or changes to captured interface.
"""
from __future__ import annotations
import argparse,io,json,math,subprocess,sys,time
from pathlib import Path

import cairosvg, cv2, numpy as np
from PIL import Image,ImageDraw,ImageFilter
from autozoom_event_planner import plan,sample_camera

PROJECT=Path(__file__).resolve().parents[1]
ROOT=PROJECT/"studio"/".tmp"/"sauce-autozoom-v1"
SRC=ROOT/"linear-official-preview-real-60.mp4"
MANIFEST=json.loads((ROOT/"linear-interactions.json").read_text())
VENDOR=PROJECT/"studio"/"assets"/"vendor"/"shotcandy"
FRAME=VENDOR/"browser-dark.svg"
MUSIC=PROJECT.parent/"sauce-demo-assets"/"digital-clouds-mixkit.mp3"
INPUT_W,INPUT_H=1320,720
FPS=60
DURATION=14.0
MASTER_W,MASTER_H=1920,1080
FRAME_W=1440
CONTENT_H=785
FRAME_HEADER_H=46
FRAME_H=FRAME_HEADER_H+CONTENT_H
# Uniform output transform; no visible user-interface aspect-ratio distortion.
FRAME_SCALE=1.114
WINDOW_W=round(FRAME_W*FRAME_SCALE)
WINDOW_H=round(FRAME_H*FRAME_SCALE)
WINDOW_X=round((MASTER_W-WINDOW_W)/2)
WINDOW_Y=round((MASTER_H-WINDOW_H)/2)
SCREEN_W=WINDOW_W
SCREEN_H=round(CONTENT_H*FRAME_SCALE)
SCREEN_X=WINDOW_X
SCREEN_Y=WINDOW_Y+round(FRAME_HEADER_H*FRAME_SCALE)
SHOTS=plan(MANIFEST["events"],{"width":INPUT_W,"height":INPUT_H},DURATION)
if len(SHOTS)!=1: raise RuntimeError(f"Expected one evidenced focus shot, got {len(SHOTS)}")
(ROOT/"camera-plan.json").write_text(json.dumps(
  {"source":"linear-interactions.json","algorithm":"event-driven camera planner, no authored cues",
   "shots":[s.dictionary() for s in SHOTS]},indent=2))

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
    src=src.replace('height="900"','height="785"')
    src=src.replace("quokka.app/overview","linear.app")
    # Keep Shotcandy's frame, clip paths, controls and border; make only the
    # placeholder body transparent so the actual capture occupies #screen.
    src=src.replace('fill="#EDE6DC"','fill="none"')
    src=src.replace('fill="url(#hatch)" opacity=".5"','fill="none" opacity="0"')
    (ROOT/"shotcandy-browser-dark-linear-adapted.svg").write_text(src)
    png=cairosvg.svg2png(bytestring=src.encode("utf-8"),
                          output_width=FRAME_W,output_height=FRAME_H)
    overlay=Image.open(io.BytesIO(png)).convert("RGBA")
    overlay=overlay.resize((WINDOW_W,WINDOW_H),Image.Resampling.LANCZOS)
    # Preserve original Shotcandy MIT attribution next to the derived SVG.
    (ROOT/"SHOTCANDY-LICENSE.txt").write_text((VENDOR/"LICENSE").read_text())
    return np.asarray(overlay,dtype=np.uint8)[:,:,[2,1,0,3]].copy()

def prepare_stage():
    frame=render_shotcandy_overlay()
    # Matte gray, restrained neutral. No invented macOS bar, gradient or fake desktop wallpaper.
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
    zoom,fx,fy= (1,.5,.5) if static else sample_camera(t,SHOTS)
    pan_x=max(0.,min(1.,.5+(fx-.5)*1.90))
    pan_y=max(0.,min(1.,.5+(fy-.5)*1.90))
    sx=(SCREEN_W/INPUT_W)*zoom
    sy=(SCREEN_H/INPUT_H)*zoom
    dx=(SCREEN_W-INPUT_W*sx)*pan_x
    dy=(SCREEN_H-INPUT_H*sy)*pan_y
    return np.array([[sx,0.,dx],[0.,sy,dy]],dtype=np.float64)

def apply(source,t,static=False):
    mat=camera_matrix(t,static=static)
    content=cv2.warpAffine(source,mat,(SCREEN_W,SCREEN_H),
           flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
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

def diagnostics():
    rows=np.array([camera_matrix(i/FPS).reshape(-1) for i in range(round(DURATION*FPS))])
    vel=np.diff(rows,axis=0)
    accel=np.diff(vel,axis=0)
    metrics={
       "frames":len(rows),
       "zoom_shots":len(SHOTS),
       "max_translation_per_frame_px":round(float(np.max(np.abs(vel[:,[2,5]]))),4),
       "max_translation_acceleration_px_per_frame_sq":
             round(float(np.max(np.abs(accel[:,[2,5]]))),4),
       "max_zoom_per_frame":round(float(np.max(np.abs(vel[:,0]))),8),
       "frame_source":"Shotcandy MIT browser-dark.svg",
       "source_capture":"official Linear interactive preview",
       "camera_plan_source":"recorded click and DOM state change",
       "browser_frame_not_handmade":True,
       "stable_window":True,
       "interpolation":"C2 quintic",
    }
    if not np.isfinite(rows).all():raise RuntimeError("Nonfinite camera matrix")
    (ROOT/"camera-metrics.json").write_text(json.dumps(metrics,indent=2))
    print("CAMERA_METRICS",json.dumps(metrics),flush=True)
    return metrics

def render(output,seconds=None,static=False):
    frames=round((seconds or DURATION)*FPS)
    frames=min(frames,round(DURATION*FPS))
    ffread=subprocess.Popen([
     "ffmpeg","-hide_banner","-loglevel","error",
     "-i",str(SRC),"-f","rawvideo","-pix_fmt","bgr24","pipe:1"
    ],stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=2*1024*1024)
    cmd=[
       "ffmpeg","-hide_banner","-loglevel","error","-y",
       "-f","rawvideo","-pix_fmt","bgr24",
       "-video_size",f"{MASTER_W}x{MASTER_H}",
       "-framerate",str(FPS),"-i","pipe:0"]
    if MUSIC.exists():
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
        image=apply(src,i/FPS,static=static)
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
            "render_seconds":round(time.monotonic()-start,2),
            "full_decode_verified":True,"static":static,
            "video":video}
    output.with_suffix(".json").write_text(json.dumps(record,indent=2))
    print("RENDER_RECEIPT",json.dumps(record),flush=True)

if __name__=="__main__":
    arg=argparse.ArgumentParser()
    arg.add_argument("--preview",type=float)
    arg.add_argument("--seconds",type=float)
    arg.add_argument("--static",action="store_true")
    args=arg.parse_args()
    diagnostics()
    if args.preview is not None:
        cmd=["ffmpeg","-hide_banner","-loglevel","error",
             "-ss",str(args.preview),"-i",str(SRC),
             "-frames:v","1","-f","rawvideo","-pix_fmt","bgr24","pipe:1"]
        raw=subprocess.check_output(cmd)
        src=np.frombuffer(raw,dtype=np.uint8).reshape(INPUT_H,INPUT_W,3)
        path=ROOT/("linear-static-preview.jpg" if args.static else "linear-autozoom-preview.jpg")
        cv2.imwrite(str(path),apply(src,args.preview,args.static),[cv2.IMWRITE_JPEG_QUALITY,88])
        print("PREVIEW",path,path.stat().st_size)
    else:
        name=("linear-static-master-1080p60.mp4" if args.static else
              "linear-autozoom-master-1080p60.mp4")
        if args.seconds is not None:name=name.replace(".mp4","-smoke.mp4")
        render(ROOT/name,args.seconds,args.static)
