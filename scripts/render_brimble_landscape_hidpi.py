#!/usr/bin/env python3
"""Sauce landscape v06: verified 2x Chromium screenshots + original cursor data.

This renders UI at *device-pixel resolution* for a specific verified Brimble
workflow, instead of magnifying compressed 1600x900 H.264 source frames.
Original live capture remains the evidence for state transitions and pointer.
The input is an observed three-state storyboard, not generalized DOM replay.

No synthetic Brimble HTML, screenshot text replacement, false login or deploy.
"""
from __future__ import annotations
import argparse, json, math, subprocess, time
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from spring_motion import cursor_track
from action_zoom_planner import Rect, build_action_camera

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"studio"/".tmp"/"landscape-hidpi"
ORIG=ROOT/"studio"/".tmp"/"film-05"
FRAME_NAMES=["01-agent-section","02-agent-picker","03-command-copied"]
manifest=json.loads((P/"manifest.json").read_text())
events=json.loads((ORIG/"capture-events.json").read_text())
VO=json.loads((ORIG/"voice.json").read_text())["lines"]
if not manifest.get("verified") or len(manifest.get("states",{}))!=3:
 raise RuntimeError("Unverified state capture. Reject rendering.")
UI_EVENTS={e["action"]:e for e in events["events"]
           if e["action"] in ("connect-modal-visible","setup-command-visible","copy-confirmation")}
if not all(k in UI_EVENTS for k in ("connect-modal-visible","setup-command-visible")):
 raise RuntimeError("Missing actual interaction events.")
STATES=[]
for name in FRAME_NAMES:
 file=P/(name+".png")
 im=cv2.imread(str(file),cv2.IMREAD_COLOR)
 if im is None or im.shape[:2]!=(1800,3200):raise RuntimeError("Source is not 2x native Chromium.")
 import hashlib
 if hashlib.sha256(file.read_bytes()).hexdigest()!=manifest["states"][name]["sha256"]:
  raise RuntimeError("Source SHA256 changed: "+name)
 STATES.append(im)
W,H,FPS=1920,1080,60
INPUT_W,INPUT_H=3200,1800
OUT_W,OUT_H=1744,981
OX,OY=88,27
DURATION=12.9
FONTPATH=ORIG/"fonts"/"DMSans.ttf"
FONT=ImageFont.truetype(str(FONTPATH),35)
try:FONT.set_variation_by_name("Regular")
except ValueError:pass
cv2.setNumThreads(4)
parser=argparse.ArgumentParser()
parser.add_argument("--preview",type=float,default=None)
parser.add_argument("--output",type=Path,default=P/"sauce-landscape-hidpi-1080p60.mp4")
parser.add_argument("--seconds",type=float,default=None)
args=parser.parse_args()

def quint(t):
 t=max(0.0,min(1.0,float(t)))
 return t*t*t*(t*(t*6.-15.)+10.)
def interpolate(t,start,end,a,b):
 if t<=start:return a
 if t>=end:return b
 return a+(b-a)*quint((t-start)/(end-start))

def state_mix(t):
 # Both adjacent states were captured from the real live app. Cross-dissolve
 # does not claim to replay the app's internal animation.
 if t<5.011:return 0,0,0.
 if t<5.241:return 0,1,quint((t-5.011)/.23)
 if t<7.723:return 1,1,0.
 if t<7.993:return 1,2,quint((t-7.723)/.27)
 return 2,2,0.

# Camera targets are derived from cursor travel, click DOM box and actual
# state visibility, not independent timestamps that zoom into an empty scene.
AGENT_BTN=manifest["states"]["01-agent-section"]["proof"]["buttonBox"]
PICKER_BOX=manifest["states"]["02-agent-picker"]["proof"]["dialogBox"]
COPIED_BOX=manifest["states"]["03-command-copied"]["proof"]["dialogBox"]
CAMERA_FRAMES,CAMERA_CUES=build_action_camera(
 fps=FPS,duration=DURATION,
 pointer_samples=events["pointer"],
 click_time=next((e["t"] for e in events["events"]
                  if e.get("action")=="click-down" and
                  e.get("label")=="Connect your agent"),4.90),
 # Legacy sidecar lacks mouse-down events. 4.90s is the original
 # recording script's verified click schedule, not a fabricated click.
 click_rect=Rect(**AGENT_BTN),
 modal_open_time=UI_EVENTS["connect-modal-visible"]["t"],
 picker_rect=Rect(**PICKER_BOX),
 copied_time=UI_EVENTS["setup-command-visible"]["t"],
 result_rect=Rect(**COPIED_BOX),
)
(P/"action-camera-cues.json").write_text(json.dumps(CAMERA_CUES,indent=2))

def camera(t):
 index=max(0,min(len(CAMERA_FRAMES)-1,round(t*FPS)))
 return CAMERA_FRAMES[index]

BASE=Image.new("RGB",(W,H),(244,243,239))
shadow=Image.new("L",(W,H),0)
d=ImageDraw.Draw(shadow)
d.rounded_rectangle((OX,OY,OX+OUT_W-1,OY+OUT_H-1),radius=21,fill=240)
shadow=shadow.filter(ImageFilter.GaussianBlur(24))
BASE.paste((90,92,88),(0,12),shadow.point(lambda v:int(v*.24)))
bd=ImageDraw.Draw(BASE)
bd.rounded_rectangle((OX-1,OY-1,OX+OUT_W,OY+OUT_H),radius=21,
  fill=(250,250,247),outline=(192,192,187),width=2)
BASE=np.asarray(BASE)[:,:,::-1].copy()
mask=Image.new("L",(OUT_W,OUT_H),0)
ImageDraw.Draw(mask).rounded_rectangle((0,0,OUT_W-1,OUT_H-1),radius=20,fill=255)
CLIP=np.asarray(mask,dtype=np.float32)[:,:,None]/255.
CURSOR_svg='''M2 2 L2 34 L11 25 L19 43 L26 40 L18 24 L34 24 Z'''
C=(np.array([[2.,2.],[2.,34.],[11.,25.],[19.,43.],[26.,40.],[18.,24.],[34.,24.]],dtype=np.int32))
# Render cursor once as a crisp vector via Pillow (screen-pixel size).
icon=Image.new("RGBA",(43,51),(0,0,0,0))
draw=ImageDraw.Draw(icon)
draw.polygon([tuple(p) for p in C],fill=(255,255,254,255))
draw.line([tuple(p) for p in C]+[tuple(C[0])],fill=(21,23,25,255),width=3,joint="curve")
ICON=np.asarray(icon)
ICON_RGB=ICON[:,:,:3][:,:,[2,1,0]]
ICON_A=ICON[:,:,3:4].astype(np.float32)/255.
POINTER=events["pointer"]
# Critically damped pointer follows the actual telemetry, rather than each
# frame linearly lerping to the next raw sample. Click deadlines are validated.
CURSOR_FRAMES=cursor_track(
 samples=POINTER,fps=FPS,duration=DURATION,
 stiffness=784.0,damping=56.0,
)
RECORDED_CLICKS=[
 (4.90,459.22,416.38),
 (7.70,667.00,551.00),
 (10.15,655.77,628.00),
]
for click_t,target_x,target_y in RECORDED_CLICKS:
 filtered=CURSOR_FRAMES[round(click_t*FPS)]
 if math.hypot(filtered[0]-target_x,filtered[1]-target_y)>3.0:
  raise RuntimeError("Spring pointer would miss recorded click at %.3fs" % click_t)
# Event-aligned captions intentionally use no eyebrow, label or title slide.
def text_layer(words):
 width=math.ceil(FONT.getlength(words))
 if width>W-100:raise RuntimeError("Caption too long")
 img=Image.new("RGBA",(W,66),(0,0,0,0))
 d=ImageDraw.Draw(img)
 d.text(((W-width)/2,7),words,font=FONT,fill=(45,47,43,255))
 a=np.asarray(img,dtype=np.uint8)
 return a[:,:,:3][:,:,[2,1,0]], a[:,:,3:4].astype(np.float32)/255.
CAPTIONS={v["id"]:text_layer(v["text"]) for v in VO}

def warp(image,scale,fx,fy):
 factor=(OUT_W/INPUT_W)*scale
 # Focus coordinates are CSS px, source image is 2 device px / CSS px.
 dx=OUT_W/2-2*fx*factor
 dy=OUT_H/2-2*fy*factor
 dx=max(OUT_W-INPUT_W*factor,min(0,dx))
 dy=max(OUT_H-INPUT_H*factor,min(0,dy))
 mat=np.array([[factor,0,dx],[0,factor,dy]],dtype=np.float32)
 return cv2.warpAffine(image,mat,(OUT_W,OUT_H),
      flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE),factor,dx,dy

def draw_pointer(stage,t,fac,dx,dy):
 if t<3.77:return
 x,y=CURSOR_FRAMES[max(0,min(len(CURSOR_FRAMES)-1,round(t*FPS)))]
 px=int(round(OX+dx+fac*(2*x)))
 py=int(round(OY+dy+fac*(2*y)))
 h,w=ICON_RGB.shape[:2]
 l=max(OX,px);top=max(OY,py);right=min(OX+OUT_W,px+w);bot=min(OY+OUT_H,py+h)
 if l>=right or top>=bot:return
 dst=stage[top:bot,l:right]
 piece=ICON_RGB[top-py:bot-py,l-px:right-px]
 alpha=ICON_A[top-py:bot-py,l-px:right-px]
 dst[:]=np.uint8(dst.astype(np.float32)*(1-alpha)+piece*alpha)

def render(t):
 z,fx,fy=camera(t)
 a,b,blend=state_mix(t)
 curr,scale,dx,dy=warp(STATES[a],z,fx,fy)
 if b!=a:
  next_frame,_,_,_=warp(STATES[b],z,fx,fy)
  curr=cv2.addWeighted(curr,1-blend,next_frame,blend,0)
 stage=BASE.copy()
 dst=stage[OY:OY+OUT_H,OX:OX+OUT_W]
 dst[:]=np.uint8(dst.astype(np.float32)*(1-CLIP)+curr*CLIP)
 draw_pointer(stage,t,scale,dx,dy)
 line=next((r for r in VO if r["start"]<=t<=r["end"]+.08),None)
 if line:
  rgb,alpha=CAPTIONS[line["id"]]
  strip=stage[1009:1075,:]
  strip[:]=np.uint8(strip.astype(np.float32)*(1-alpha)+rgb*alpha)
 return stage

if args.preview is not None:
 args.output.parent.mkdir(parents=True,exist_ok=True)
 cv2.imwrite(str(args.output),render(args.preview),[cv2.IMWRITE_JPEG_QUALITY,91])
 print("PREVIEW",args.output,args.output.stat().st_size,flush=True)
else:
 frames=int(round((args.seconds or DURATION)*FPS))
 output= args.output
 output.parent.mkdir(parents=True,exist_ok=True)
 silent=P/"landscape-hidpi-video.mp4"
 encoder=subprocess.Popen([
  "ffmpeg","-hide_banner","-loglevel","error","-y",
  "-f","rawvideo","-pix_fmt","bgr24","-video_size",f"{W}x{H}",
  "-framerate",str(FPS),"-i","pipe:0","-an",
  "-c:v","libx264","-preset","slow","-crf","14",
  "-pix_fmt","yuv420p","-g","120","-threads","7",
  "-movflags","+faststart",str(silent)],
  stdin=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=12*1024*1024)
 start=time.monotonic()
 for n in range(frames):
  frame=render(n/FPS)
  encoder.stdin.write(frame.tobytes())
  if n%120==0:
   print("FRAMES",n,frames,"seconds",round(time.monotonic()-start,1),flush=True)
 encoder.stdin.close()
 error=encoder.stderr.read().decode(errors="replace")
 if encoder.wait(timeout=150):raise RuntimeError("FFmpeg encode failed "+error[-2500:])
 voice=ORIG/"narration.wav"
 if not voice.exists():raise RuntimeError("Voice missing")
 music=ROOT.parent/"sauce-demo-assets"/"digital-clouds-mixkit.mp3"
 args_audio=["-i",str(voice)]
 if music.exists():
  args_audio+=["-stream_loop","-1","-i",str(music)]
  filter_str=(f"[1:a]aresample=48000[v];[2:a]aresample=48000,"
    f"atrim=0:{frames/FPS},volume=0.046,afade=t=in:d=0.5,"
    f"afade=t=out:st={max(0,frames/FPS-1.4)}:d=1.3[m];"
    f"[v][m]amix=inputs=2:duration=first:normalize=0[a]")
  af=["-filter_complex",filter_str,"-map","0:v:0","-map","[a]"]
 else:af=["-map","0:v:0","-map","1:a:0"]
 temp=P/"landscape-hidpi-mixed.mp4"
 subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
     "-i",str(silent)]+args_audio+af+
     ["-c:v","copy","-c:a","aac","-b:a","192k",
      "-t",str(frames/FPS),"-movflags","+faststart",str(temp)],
     check=True,timeout=100)
 subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
     "-i",str(temp),"-map","0:v:0","-map","0:a:0",
     "-c:v","copy","-af","loudnorm=I=-16:TP=-1.5:LRA=7",
     "-c:a","aac","-b:a","192k","-movflags","+faststart",str(output)],
     check=True,timeout=100)
 subprocess.run(["ffmpeg","-v","error","-xerror","-i",str(output),"-f","null","-"],
     check=True,timeout=120)
 probe=json.loads(subprocess.check_output(["ffprobe","-v","error",
  "-show_entries","stream=codec_name,codec_type,nb_frames,width,height:format=duration,size",
  "-of","json",str(output)],text=True))
 print("COMPLETE",json.dumps({"file":str(output),"probe":probe,
      "verified":True,"seconds":round(time.monotonic()-start,1)}),flush=True)
