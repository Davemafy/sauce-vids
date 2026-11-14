#!/usr/bin/env python3
"""One coherent product film: actual Resend pricing capture, real pointer, physical lens.

Visual grammar reverse-engineered from user-supplied Screen Studio references:
floating browser in a photographed desktop, circular loupe following a live
control, readable hold on the actual changed price, exact phrase captions.

The interface and pricing remain original video pixels throughout.
"""
from __future__ import annotations
import argparse,io,json,math,subprocess,time
from functools import lru_cache
from pathlib import Path
import numpy as np,cv2,cairosvg
from PIL import Image,ImageDraw,ImageFont,ImageFilter

PROJECT=Path(__file__).resolve().parents[1]
P=PROJECT/"studio"/".tmp"/"film-03"
SRC=P/"resend-real-slider-60.mp4"
RECEIPT=json.loads((P/"resend-events.json").read_text())
NARRATION=json.loads((P/"narration.json").read_text())
W,H,FPS=1920,1080,60
SW,SH=1440,900
DURATION=16.
WIN_X,WIN_Y=240,67
WIN_W,WIN_H=1440,946
HEAD_H=46
SC_X,SC_Y=WIN_X,WIN_Y+HEAD_H
LENS_R=363
C_BG=(12,14,17)
FRAME=PROJECT/"studio"/"assets"/"vendor"/"shotcandy"/"browser-dark.svg"
PHOTO=PROJECT/"studio"/".tmp"/"saas-kiva"/"rocky-coast.jpg"
MUSIC=PROJECT.parent/"sauce-demo-assets"/"digital-clouds-mixkit.mp3"
FONT_ROOT=Path("/usr/share/fonts/truetype")
FONT=ImageFont.truetype(str(FONT_ROOT/"liberation2"/"LiberationSans-Bold.ttf"),49) if (FONT_ROOT/"liberation2"/"LiberationSans-Bold.ttf").exists() else ImageFont.truetype(str(FONT_ROOT/"dejavu"/"DejaVuSans.ttf"),48)
CAPS=[
 (.55,1.49,"Three thousand emails"),
 (1.49,2.51,"start free."),
 (3.55,4.97,"Fifty thousand emails?"),
 (4.97,6.48,"Twenty dollars a month."),
 (7.55,8.90,"A hundred thousand?"),
 (8.90,10.24,"Thirty-five dollars."),
 (10.75,11.55,"One slider."),
 (11.55,12.44,"The price changes"),
 (12.44,13.86,"right where you need it.")
]
parser=argparse.ArgumentParser()
parser.add_argument("--preview",type=float,default=None)
parser.add_argument("--seconds",type=float,default=None)
parser.add_argument("--out",type=Path,default=P/"resend-final-1080p60.mp4")
args=parser.parse_args()
if not SRC.is_file() or not FRAME.is_file() or not PHOTO.is_file():raise RuntimeError("Missing real capture or licensed assets")
if len(RECEIPT["events"])<3:raise RuntimeError("No verified source events")
actions=[e for e in RECEIPT["events"] if e["kind"] in ("click","state_change")]
if len(actions)!=2 or actions[0]["price"]!="$20 / mo" or actions[1]["price"]!="$35 / mo":
 raise RuntimeError("Recorded price verification did not pass")
cv2.setNumThreads(4)

def ease(x):
 u=max(0.,min(1.,float(x)))
 return u*u*u*(u*(u*6-15)+10)
def lerp(a,b,u):return a+(b-a)*ease(u)
def interp(t,start,end,lo,hi):
 return lerp(lo,hi,(t-start)/(end-start)) if start<=t<end else (lo if t<start else hi)

def lens_state(t):
 if t<3.2:return 0.,(780.,510.),(467.,477.)
 strength=interp(t,3.2,3.7,0.,1.) if t<3.7 else (
          interp(t,12.8,13.55,1.,0.) if t>12.8 else 1.)
 if t<7.8:
  center=(835.,511.)
  focus=(542.,484.)
 elif t<9.1:
  u=ease((t-7.8)/1.3)
  center=(835+150*u,511+27*u)
  focus=(542+23*u,484+41*u)
 else:
  center=(985.,538.)
  focus=(565.,525.)
 return strength,center,focus

def backdrop():
 im=Image.open(PHOTO).convert("RGB")
 img=Image.fromarray(np.asarray(im.resize((W,H),Image.Resampling.LANCZOS)).copy())
 a=np.asarray(img,dtype=np.float32)*.88
 img=Image.fromarray(np.uint8(np.clip(a+[5,6,10],0,255)))
 # Window shadow beneath the reused Shotcandy frame.
 sh=Image.new("L",(W,H),0)
 d=ImageDraw.Draw(sh)
 d.rounded_rectangle((WIN_X,WIN_Y,WIN_X+WIN_W,WIN_Y+WIN_H),radius=24,fill=255)
 sh=sh.filter(ImageFilter.GaussianBlur(37))
 alpha=sh.point(lambda x:int(x*.45))
 dark=Image.new("RGB",(W,H),(1,3,6))
 shadowed=Image.new("RGB",(W,H))
 shadowed.paste(img)
 shadowed.paste(dark,(0,16),alpha)
 return np.asarray(shadowed)[:,:,::-1].copy()

def frame_layer():
 src=FRAME.read_text().replace("quokka.app/overview","resend.com/pricing")
 src=src.replace('fill="#EDE6DC"','fill="none"')
 src=src.replace('fill="url(#hatch)" opacity=".5"','fill="none" opacity="0"')
 png=cairosvg.svg2png(bytestring=src.encode(),output_width=WIN_W,output_height=WIN_H)
 rgba=np.asarray(Image.open(io.BytesIO(png)).convert("RGBA"),dtype=np.uint8)
 return rgba[:,:,[2,1,0,3]].copy()

BACK=backdrop()
BROWSER=frame_layer()
SCREEN_MASK=Image.new("L",(WIN_W,WIN_H),0)
sd=ImageDraw.Draw(SCREEN_MASK)
sd.rounded_rectangle((0,0,WIN_W-1,WIN_H-1),radius=24,fill=255)
SCREEN_MASK=np.asarray(SCREEN_MASK,dtype=np.uint8)[HEAD_H:,:]/255.
FRAME_ALPHA=BROWSER[:,:,3:4].astype(np.float32)/255.

# Loupe geometry is fixed and reused for 60fps stability.
Y,X=np.mgrid[-LENS_R:LENS_R+1,-LENS_R:LENS_R+1].astype(np.float32)
R=np.sqrt(X*X+Y*Y)
disc=np.clip((LENS_R-.5-R)/1.9,0,1).astype(np.float32)[:,:,None]
edge=np.clip((R-(LENS_R-3.7))/2.3,0,1)*np.clip((LENS_R+1-R)/1.9,0,1)
shmask=np.clip((LENS_R+20-R)/24,0,1)-np.clip((LENS_R-2-R)/3,0,1)
shmask=np.clip(shmask,0,1)
mask_h,mask_w=disc.shape[:2]
font_y=H-130

@lru_cache(maxsize=15)
def caption_img(caption):
 txt=caption.strip()
 width=math.ceil(FONT.getlength(txt))+78
 hh=88
 a=Image.new("RGBA",(width,hh),(0,0,0,0))
 d=ImageDraw.Draw(a)
 d.rounded_rectangle((0,0,width-1,hh-1),radius=13,fill=(8,9,11,234))
 d.text(((width-FONT.getlength(txt))/2,14),txt,font=FONT,fill=(247,247,245,255))
 z=np.asarray(a,dtype=np.uint8)
 return z[:,:,[2,1,0]],z[:,:,3:4]/255.

def apply_caps(stage,t):
 current=next((caption for a,b,caption in CAPS if a<=t<b),None)
 if current is None:return
 rgb,alpha=caption_img(current)
 hh,ww=rgb.shape[:2]
 x=(W-ww)//2
 y=H-135
 roi=stage[y:y+hh,x:x+ww]
 roi[:]=(roi.astype(np.float32)*(1-alpha)+rgb.astype(np.float32)*alpha).astype(np.uint8)

def frame(src,t):
 stage=BACK.copy()
 # Film shot: source UI frame stays physically fixed in the wallpaper.
 content=src
 part=stage[SC_Y:SC_Y+SH,SC_X:SC_X+SW]
 cm=SCREEN_MASK[:,:,None]
 part[:]=(part*(1-cm)+content*cm).astype(np.uint8)
 # Licensed browser frame, transparent opening for real screen footage.
 roi=stage[WIN_Y:WIN_Y+WIN_H,WIN_X:WIN_X+WIN_W]
 roi[:]=(roi.astype(np.float32)*(1-FRAME_ALPHA)+BROWSER[:,:,:3].astype(np.float32)*FRAME_ALPHA).astype(np.uint8)
 strength,center,focus=lens_state(t)
 if strength>.003:
  cx,cy=center
  x0=int(round(cx-LENS_R));y0=int(round(cy-LENS_R))
  x1=x0+mask_w;y1=y0+mask_h
  if x0<0 or y0<0 or x1>W or y1>H:raise RuntimeError("Lens outside canvas")
  roi=stage[y0:y1,x0:x1]
  zoom=2.03
  map_x=(focus[0]+X/zoom).astype(np.float32)
  map_y=(focus[1]+Y/zoom).astype(np.float32)
  magnified=cv2.remap(src,map_x,map_y,cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
  # Separate physically soft shadow, thin rim and sampled real pixels.
  shadow=(shmask[:,:,None]*strength*.39)
  roi[:]=(roi.astype(np.float32)*(1-shadow)).astype(np.uint8)
  alpha=disc*strength
  roi[:]=(roi.astype(np.float32)*(1-alpha)+magnified.astype(np.float32)*alpha).astype(np.uint8)
  rim=np.clip(edge*strength*.65,0,.75)[:,:,None]
  roi[:]=(roi.astype(np.float32)*(1-rim)+np.array([156,166,178],dtype=np.float32)*rim).astype(np.uint8)
 apply_caps(stage,t)
 return stage

def read_frame_at(t):
 raw=subprocess.check_output(["ffmpeg","-hide_banner","-loglevel","error","-ss",str(t),
                               "-i",str(SRC),"-frames:v","1","-f","rawvideo","-pix_fmt","bgr24","pipe:1"])
 return np.frombuffer(raw,dtype=np.uint8).reshape(SH,SW,3)

if args.preview is not None:
 out=args.out
 out.parent.mkdir(parents=True,exist_ok=True)
 cv2.imwrite(str(out),frame(read_frame_at(args.preview),args.preview),[cv2.IMWRITE_JPEG_QUALITY,90])
 print("PREVIEW",out,out.stat().st_size,flush=True)
else:
 frames=round(min(args.seconds or DURATION,DURATION)*FPS)
 args.out.parent.mkdir(parents=True,exist_ok=True)
 decoder=subprocess.Popen(["ffmpeg","-hide_banner","-loglevel","error","-i",str(SRC),"-f","rawvideo",
                           "-pix_fmt","bgr24","pipe:1"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 video=P/"film03-video-only.mp4"
 encode=["ffmpeg","-hide_banner","-loglevel","error","-y","-f","rawvideo","-pix_fmt","bgr24",
         "-video_size",f"{W}x{H}","-framerate",str(FPS),"-i","pipe:0","-an",
         "-c:v","libx264","-preset","veryfast","-crf","17","-g","120",
         "-pix_fmt","yuv420p","-movflags","+faststart","-threads","7",str(video)]
 encoder=subprocess.Popen(encode,stdin=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=8*1024*1024)
 begin=time.perf_counter()
 for i in range(frames):
  data=decoder.stdout.read(SW*SH*3)
  if len(data)<SW*SH*3:raise RuntimeError(f"Decoded frame {i} too short")
  src=np.frombuffer(data,dtype=np.uint8).reshape(SH,SW,3)
  img=frame(src,i/FPS)
  encoder.stdin.write(img.tobytes())
  if i%120==0:print("RENDER",i,"/",frames,round(time.perf_counter()-begin,1),flush=True)
 encoder.stdin.close()
 decoder.stdout.close()
 err=encoder.stderr.read().decode(errors="replace")
 rc=encoder.wait(timeout=120)
 if rc:raise RuntimeError("Encoder failure: "+err[-1800:])
 # Sound design: original, locally generated voice + low-level licensed music bed.
 voice=P/"narration.wav"
 mux=["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(video),
      "-i",str(voice)]
 if MUSIC.is_file():
  mux+=["-stream_loop","-1","-i",str(MUSIC),
        "-filter_complex",f"[1:a]aresample=48000,volume=1.0[v];[2:a]aresample=48000,atrim=0:{frames/FPS},volume=0.085,afade=t=in:d=0.6,afade=t=out:st={max(0,frames/FPS-1.7)}:d=1.5[m];[v][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=.90[a]",
        "-map","0:v:0","-map","[a]"]
 else:
  mux+=["-map","0:v:0","-map","1:a:0"]
 mux+=["-c:v","copy","-c:a","aac","-b:a","192k","-t",str(frames/FPS),
       "-movflags","+faststart",str(args.out)]
 subprocess.run(mux,check=True,timeout=95)
 probe=json.loads(subprocess.check_output(["ffprobe","-v","error",
     "-show_entries","stream=codec_name,codec_type,width,height,avg_frame_rate,nb_frames:format=duration,size",
     "-of","json",str(args.out)],text=True))
 subprocess.run(["ffmpeg","-v","error","-xerror","-i",str(args.out),"-f","null","-"],check=True,timeout=110)
 print("FINAL",json.dumps({"output":str(args.out),"probe":probe,
     "source":"resend.com/pricing live capture","verified_price_states":["$20 / mo","$35 / mo"],
     "full_decode":True,"seconds_elapsed":round(time.perf_counter()-begin,1)}),flush=True)
