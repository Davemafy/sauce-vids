#!/usr/bin/env python3
"""Sauce Film 04: single real product action, voice-first, large dynamic lens.

Scene content comes exclusively from the real recorded Resend browser footage.
The physical stage, frame, lens and typography are editorial layers. A compact
10.4-second narrative replaces Film 03's 16-second, mostly stationary lens.
"""
from __future__ import annotations
import argparse,io,json,math,subprocess,time
from pathlib import Path
from functools import lru_cache
import cv2,cairosvg,numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageFont

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"studio"/".tmp"/"film-04"
SOURCE=P/"resend-cursorless-60.mp4"
RECEIPT=json.loads((P/"cursor-events.json").read_text())
VOICES=json.loads((P/"voice.json").read_text())["phrases"]
FRAME=ROOT/"studio"/"assets"/"vendor"/"shotcandy"/"browser-dark.svg"
PHOTO=P/"alpine-lake-unsplash.jpg"
W,H,FPS=1920,1080,60
SW,SH=1440,900
CROP_H=760
DURATION=10.4
WIN_W=1540
SCREEN_H=int(round(CROP_H*WIN_W/SW))
HEADER=int(round(46.08*WIN_W/SW))
WIN_H=HEADER+SCREEN_H
WX=(W-WIN_W)//2
WY=87
SY=WY+HEADER
MAX_R=632
VID=P/"film04-video.mp4"
FONT_PATH="/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT=ImageFont.truetype(FONT_PATH,53)
MUSIC=ROOT.parent/"sauce-demo-assets"/"digital-clouds-mixkit.mp3"
VOICED=P/"voice.wav"
OUT=P/"sauce-film04-1080p60.mp4"
CAPTIONS=[
(.38,1.28,"Three thousand emails"),
(1.28,2.23,"start free."),
(2.63,3.56,"Fifty thousand?"),
(3.56,4.89,"Twenty dollars a month."),
(5.18,6.22,"A hundred thousand?"),
(6.22,7.54,"Thirty-five dollars."),
(7.78,8.57,"One slider."),
(8.57,9.79,"Clear pricing.")
]
assert len([e for e in RECEIPT["events"] if e.get("price")])==2
assert "$20 / mo" in [e.get("price") for e in RECEIPT["events"]]
assert "$35 / mo" in [e.get("price") for e in RECEIPT["events"]]
cv2.setNumThreads(4)
parser=argparse.ArgumentParser()
parser.add_argument("--frame",type=float,help="Preview a still at a film timestamp")
parser.add_argument("--output",type=Path,default=OUT)
parser.add_argument("--seconds",type=float)
args=parser.parse_args()

def smoother(u):
 x=max(0.,min(1.,float(u)))
 return x*x*x*(x*(x*6-15)+10)
def transition(t,a,b,lo,hi):
 if t<=a:return lo
 if t>=b:return hi
 return lo+(hi-lo)*smoother((t-a)/(b-a))
MAP=[
(0.0,.2),(.9,1.2),(1.8,2.25),(2.55,3.85),
(3.59,4.98),(4.92,6.65),(5.4,7.35),
(6.05,9.15),(7.5,11.45),(9.2,14.3),(10.4,15.88)
]
# Monotone cubic retiming: continuous velocity without piecewise-linear
# speed jumps at edit boundaries. Preserve chronology and real app states.
KNOT_T=np.array([k[0] for k in MAP],dtype=np.float64)
KNOT_SRC=np.array([k[1] for k in MAP],dtype=np.float64)
STEP=np.diff(KNOT_T)
DELTA=np.diff(KNOT_SRC)/STEP
SLOPE=np.zeros_like(KNOT_T)
SLOPE[0]=DELTA[0]
SLOPE[-1]=DELTA[-1]
for q in range(1,len(KNOT_T)-1):
 if DELTA[q-1]*DELTA[q]<=0:
  SLOPE[q]=0.
 else:
  a=2*STEP[q]+STEP[q-1]
  b=STEP[q]+2*STEP[q-1]
  SLOPE[q]=(a+b)/(a/DELTA[q-1]+b/DELTA[q])
def source_time(t):
 i=int(np.searchsorted(KNOT_T,t,side="right")-1)
 i=max(0,min(len(STEP)-1,i))
 u=float(np.clip((t-KNOT_T[i])/STEP[i],0,1))
 u2,u3=u*u,u*u*u
 return float((2*u3-3*u2+1)*KNOT_SRC[i]
  +(u3-2*u2+u)*STEP[i]*SLOPE[i]
  +(-2*u3+3*u2)*KNOT_SRC[i+1]
  +(u3-u2)*STEP[i]*SLOPE[i+1])

def lens_state(t):
 if t<1.38 or t>=9.08:
  return 0.,(865.,514.),(590.,463.),2.5
 if t<2.12:r=transition(t,1.38,2.12,0.,320.)
 elif t<3.37:r=transition(t,2.12,3.37,320.,MAX_R)
 elif t<7.42:r=float(MAX_R)
 else:r=transition(t,7.42,9.08,float(MAX_R),0.)
 cx=transition(t,1.38,3.4,805.,985.) if t<3.4 else transition(t,5.2,7.1,985.,1040.)
 cy=transition(t,1.38,3.4,515.,542.) if t<3.4 else transition(t,5.2,7.1,542.,553.)
 fx=transition(t,4.85,6.65,584.,631.)
 fy=transition(t,4.85,6.65,489.,514.)
 magnify=transition(t,1.38,3.37,1.40,2.32)
 return r,(cx,cy),(fx,fy),magnify

def make_browser():
 text=FRAME.read_text()
 replacements={
  "946.08":"806.08","923.04":"783.04","945.58":"805.58",
  'height="900"':'height="760"',
  "quokka.app/overview":"resend.com/pricing",
  'fill="#EDE6DC"':'fill="none"',
  'fill="url(#hatch)" opacity=".5"':'fill="none" opacity="0"'
 }
 for old,new in replacements.items():
  if old not in text:raise ValueError("Browser SVG missing "+old)
  text=text.replace(old,new)
 rgba=Image.open(io.BytesIO(cairosvg.svg2png(
  bytestring=text.encode("utf-8"),
  output_width=WIN_W,output_height=WIN_H))).convert("RGBA")
 out=np.asarray(rgba,dtype=np.uint8)
 return out[:,:,[2,1,0,3]].copy()

def build_stage():
 photo=Image.open(PHOTO).convert("RGB").resize((W,H),Image.Resampling.LANCZOS)
 # The reference's background is light, not dark graded.
 photo=photo.filter(ImageFilter.GaussianBlur(.7))
 base=Image.fromarray(np.uint8(np.clip(np.asarray(photo,dtype=np.float32)*.93+3,0,255)))
 sh=Image.new("L",(W,H),0)
 p=ImageDraw.Draw(sh)
 p.rounded_rectangle((WX,WY,WX+WIN_W-1,WY+WIN_H-1),radius=23,fill=255)
 shadow=sh.filter(ImageFilter.GaussianBlur(31))
 shadow_layer=Image.new("L",(W,H),0)
 shadow_layer.paste(shadow,(0,18))
 shadow_layer=shadow_layer.point(lambda a:int(a*.39))
 base.paste((14,21,28),(0,0,W,H),shadow_layer)
 return np.asarray(base)[:,:,::-1].copy()
STAGE=build_stage()
BROWSER=make_browser()
B_ALPHA=BROWSER[:,:,3:4].astype(np.float32)/255
SCREEN_MASK=Image.new("L",(WIN_W,WIN_H),0)
dr=ImageDraw.Draw(SCREEN_MASK)
dr.rounded_rectangle((0,0,WIN_W-1,WIN_H-1),radius=23,fill=255)
SMASK=np.asarray(SCREEN_MASK,dtype=np.uint8)[HEADER:,:].astype(np.float32)[:,:,None]/255

@lru_cache(maxsize=16)
def caption_overlay(text):
 txt=text.strip()
 width=math.ceil(FONT.getlength(txt))+94
 ht=86
 img=Image.new("RGBA",(width,ht),(0,0,0,0))
 draw=ImageDraw.Draw(img)
 draw.rounded_rectangle((0,0,width-1,ht-1),radius=14,fill=(12,14,18,234))
 draw.text(((width-FONT.getlength(txt))/2,12),txt,font=FONT,fill=(252,251,248,255))
 pix=np.asarray(img,dtype=np.uint8)
 return pix[:,:,[2,1,0]].copy(),pix[:,:,3:4].astype(np.float32)/255.
def add_caption(dst,t):
 words=next((txt for start,end,txt in CAPTIONS if start<=t<end),None)
 if not words:return
 pix,a=caption_overlay(words)
 hh,ww=pix.shape[:2]
 y=H-101;x=(W-ww)//2
 roi=dst[y:y+hh,x:x+ww]
 roi[:]=np.uint8(roi*(1-a)+pix*a)

# Independent cursor channel: raw X11 source excludes the system pointer.
# Location comes from the same captured native interaction sidecar as the UI.
# The old Film 03 baked pointer was ~70px off its real target.
def pointer_art():
 svg='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 54">
 <path d="M4 3 L4 44 L14 35 L23 52 L31 48 L23 31 L39 30 Z"
 fill="#fafafa" stroke="#15171a" stroke-width="3.4"
 stroke-linejoin="round" stroke-linecap="round"/>
 <path d="M11 35 L23 50" fill="none" stroke="#ffffff"
 stroke-opacity=".35" stroke-width="1.3"/></svg>'''
 png=cairosvg.svg2png(bytestring=svg.encode("utf-8"),output_width=35,output_height=47)
 data=np.asarray(Image.open(io.BytesIO(png)).convert("RGBA"),dtype=np.uint8)
 return data[:,:,[2,1,0]],data[:,:,3:4].astype(np.float32)/255.
POINTER_RGB,POINTER_ALPHA=pointer_art()
CURSOR=sorted(RECEIPT["pointer_samples"],key=lambda e:e["t"])
CURSOR_TIMES=np.array([float(v["t"]) for v in CURSOR])
CURSOR_X=np.array([float(v["x"]) for v in CURSOR])
CURSOR_Y=np.array([float(v["y"]) for v in CURSOR])
if len(CURSOR)<40:raise RuntimeError("Missing real, timestamped cursor path")
def composite_pointer(img,t):
 x=float(np.interp(t,CURSOR_TIMES,CURSOR_X))
 y=float(np.interp(t,CURSOR_TIMES,CURSOR_Y))
 # Place tip at browser content coordinates; do not use the obsolete Xvfb
 # decoration offset from the physically mismatched Film 03 pointer.
 x=int(round(x));y=int(round(y))
 h,w=POINTER_RGB.shape[:2]
 x0=max(0,x);y0=max(0,y)
 x1=min(SW,x+w);y1=min(SH,y+h)
 if x1<=x0 or y1<=y0:return img
 patch=POINTER_RGB[y0-y:y1-y,x0-x:x1-x]
 alpha=POINTER_ALPHA[y0-y:y1-y,x0-x:x1-x]
 out=img.copy()
 roi=out[y0:y1,x0:x1]
 roi[:]=np.uint8(roi.astype(np.float32)*(1-alpha)+patch*alpha)
 return out

def make_frame(original,t):
 stage=STAGE.copy()
 cropped=original[:CROP_H]
 resized=cv2.resize(cropped,(WIN_W,SCREEN_H),interpolation=cv2.INTER_CUBIC)
 roi=stage[SY:SY+SCREEN_H,WX:WX+WIN_W]
 roi[:]=np.uint8(roi*(1-SMASK)+resized*SMASK)
 area=stage[WY:WY+WIN_H,WX:WX+WIN_W]
 area[:]=np.uint8(area*(1-B_ALPHA)+BROWSER[:,:,:3]*B_ALPHA)
 radius,center,focus,magnification=lens_state(t)
 if radius>1:
  cx,cy=center
  # Allow natural lens clipping at the top and bottom of the 16:9 film.
  left=max(0,int(cx-radius-7));right=min(W,int(cx+radius+8))
  top=max(0,int(cy-radius-7));bottom=min(H,int(cy+radius+8))
  yy=np.arange(top,bottom,dtype=np.float32)[:,None]-cy
  xx=np.arange(left,right,dtype=np.float32)[None,:]-cx
  dist=np.sqrt(xx*xx+yy*yy)
  # A graduated, approximately one-pixel antialiased circular boundary.
  alpha=np.clip(radius-dist+.55,0,1).astype(np.float32)[:,:,None]
  if alpha.max()>.001:
   mapx=(focus[0]+xx/magnification).astype(np.float32)
   mapy=(focus[1]+yy/magnification).astype(np.float32)
   # OpenCV remap requires full two-dimensional maps.
   mapx=np.broadcast_to(mapx,(bottom-top,right-left)).copy()
   mapy=np.broadcast_to(mapy,(bottom-top,right-left)).copy()
   enlarged=cv2.remap(original,mapx,mapy,cv2.INTER_CUBIC,
                      borderMode=cv2.BORDER_REPLICATE)
   dest=stage[top:bottom,left:right]
   # Very subtle shadow and rim, not a painted gray filter over the UI.
   shadow=np.clip((radius+14-dist)/13,0,1)-np.clip((radius-2-dist)/2,0,1)
   dest[:]=np.uint8(dest.astype(np.float32)*(1-.30*shadow[:,:,None]))
   dest[:]=np.uint8(dest.astype(np.float32)*(1-alpha)+enlarged*alpha)
   line=np.clip(radius-dist+1.5,0,1)-np.clip(radius-dist-1.2,0,1)
   tint=line[:,:,None]*.28
   dest[:]=np.uint8(dest*(1-tint)+np.array([193,200,213],np.float32)*tint)
 add_caption(stage,t)
 return stage

def preview_frame(t):
 src_t=source_time(t)
 cmd=["ffmpeg","-hide_banner","-loglevel","error","-ss",str(src_t),
      "-i",str(SOURCE),"-frames:v","1","-f","rawvideo","-pix_fmt","bgr24","pipe:1"]
 raw=subprocess.check_output(cmd)
 source=np.frombuffer(raw,dtype=np.uint8).reshape(SH,SW,3)
 return make_frame(composite_pointer(source,src_t),t)
def inspect_audio():
 if not VOICED.exists():raise RuntimeError("No actual voice track")
 if not MUSIC.exists():raise RuntimeError("Music bed missing")

if args.frame is not None:
 if not 0<=args.frame<DURATION:raise ValueError("Preview outside film")
 args.output.parent.mkdir(parents=True,exist_ok=True)
 cv2.imwrite(str(args.output),preview_frame(args.frame),[cv2.IMWRITE_JPEG_QUALITY,91])
 print("PREVIEW",args.output,args.output.stat().st_size,flush=True)
else:
 inspect_audio()
 frames=round(min(args.seconds or DURATION,DURATION)*FPS)
 dec=subprocess.Popen(["ffmpeg","-hide_banner","-loglevel","error","-i",str(SOURCE),
   "-f","rawvideo","-pix_fmt","bgr24","pipe:1"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=8*1024*1024)
 vid_cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-f","rawvideo","-pix_fmt","bgr24",
          "-video_size",f"{W}x{H}","-framerate",str(FPS),"-i","pipe:0","-an",
          "-c:v","libx264","-preset","veryfast","-crf","17","-g","120",
          "-pix_fmt","yuv420p","-movflags","+faststart","-threads","6",str(VID)]
 enc=subprocess.Popen(vid_cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=8*1024*1024)
 last_index=-1
 original=None
 frame_size=SW*SH*3
 begin=time.monotonic()
 for i in range(frames):
  t=i/FPS
  src_idx=int(round(source_time(t)*FPS))
  while last_index<src_idx:
   raw=dec.stdout.read(frame_size)
   if len(raw)!=frame_size:raise RuntimeError("Source frame ended prematurely")
   original=np.frombuffer(raw,dtype=np.uint8).reshape(SH,SW,3)
   last_index+=1
  img=make_frame(composite_pointer(original,source_time(t)),t)
  enc.stdin.write(img.tobytes())
  if i%120==0:print("RENDER",i,"/",frames,"elapsed",round(time.monotonic()-begin,1),flush=True)
 enc.stdin.close()
 dec.stdout.close()
 error=enc.stderr.read().decode(errors="replace")
 if enc.wait(timeout=120):raise RuntimeError(error[-3000:])
 dec.wait(timeout=120)
 duration=frames/FPS
 audio_filter=(f"[1:a]aresample=48000[v];"
               f"[2:a]aresample=48000,atrim=0:{duration},"
               f"volume=0.052,afade=t=in:d=0.4,"
               f"afade=t=out:st={max(0,duration-1.25)}:d=1.2[m];"
               f"[v][m]amix=inputs=2:duration=first:normalize=0[a]")
 temp=P/"film04-mixed.mp4"
 mux=["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(VID),
      "-i",str(VOICED),"-stream_loop","-1","-i",str(MUSIC),
      "-filter_complex",audio_filter,"-map","0:v:0","-map","[a]",
      "-c:v","copy","-c:a","aac","-b:a","192k","-t",str(duration),
      "-movflags","+faststart",str(temp)]
 subprocess.run(mux,check=True,timeout=100)
 normalize=["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(temp),
     "-map","0:v:0","-map","0:a:0","-c:v","copy",
     "-af","loudnorm=I=-16:TP=-1.5:LRA=7",
     "-c:a","aac","-b:a","192k","-movflags","+faststart",str(args.output)]
 subprocess.run(normalize,check=True,timeout=90)
 subprocess.run(["ffmpeg","-v","error","-xerror","-i",str(args.output),
   "-f","null","-"],check=True,timeout=125)
 stats=json.loads(subprocess.check_output(["ffprobe","-v","error",
  "-show_entries","stream=codec_name,codec_type,nb_frames,width,height,avg_frame_rate:format=duration,size",
  "-of","json",str(args.output)],text=True))
 print("SUCCESS",json.dumps({"output":str(args.output),"stats":stats,
   "decode_passed":True,"elapsed":round(time.monotonic()-begin,2)}),flush=True)
