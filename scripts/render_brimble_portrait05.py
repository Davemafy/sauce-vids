#!/usr/bin/env python3
"""Film 05: real Brimble workflow, one continuous capture, restrained camera.

No simulated product frames, no false deployment claim. Source click/DOM
events, captured web page and cursor path are independently retained.
"""
from pathlib import Path
import json,subprocess,time,io,math,argparse
import numpy as np,cv2,cairosvg
from PIL import Image,ImageDraw,ImageFont,ImageFilter
P=Path(__file__).resolve().parents[1]/"studio"/".tmp"/"film-05"
SOURCE=P/"capture.mp4"
REC=json.loads((P/"capture-events.json").read_text())
VO=json.loads((P/"voice.json").read_text())["lines"]
MUSIC=P.parents[3]/"sauce-demo-assets"/"digital-clouds-mixkit.mp3"
W,H,SW,SH,FPS=1080,1920,1600,900,60
DUR=12.9
PX,PY,PW,PH=45,235,990,1320
BORDER=21
assert PH/SH>1
assert [e['action'] for e in REC['events']][:2]==['connect-modal-visible','setup-command-visible']
CAPTURE=SOURCE
parser=argparse.ArgumentParser()
parser.add_argument("--preview",type=float)
parser.add_argument("--output",type=Path,default=P/"sauce-film05-portrait-1080x1920.mp4")
parser.add_argument("--seconds",type=float)
args=parser.parse_args()
cv2.setNumThreads(4)

def ease(u):
 u=max(0.,min(1.,float(u)))
 return u*u*u*(u*(u*6-15)+10)
def between(t,a,b,x,y):
 if t<=a:return x
 if t>=b:return y
 return x+(y-x)*ease((t-a)/(b-a))

def camera(t):
 if t<4.35:return (1.,735.,450.)
 if t<5.75:return (between(t,4.35,5.75,1.,1.33),between(t,4.35,5.75,735.,800.),450.)
 if t<7.73:return (1.33,800.,450.)
 if t<8.62:return (between(t,7.73,8.62,1.33,1.48),
                    800.,between(t,7.73,8.62,450.,500.))
 return (1.48,800.,500.)

def stage():
 # No gradient/glass; a light neutral canvas like the product itself.
 img=Image.new("RGB",(W,H),(238,237,232))
 shadow=Image.new("L",(W,H),0)
 d=ImageDraw.Draw(shadow)
 d.rounded_rectangle((PX,PY,PX+PW,PY+PH),radius=BORDER,fill=240)
 blurred=shadow.filter(ImageFilter.GaussianBlur(26))
 img.paste((79,81,79),(0,19),blurred.point(lambda x:int(x*.33)))
 d=ImageDraw.Draw(img)
 d.rounded_rectangle((PX-1,PY-1,PX+PW,PY+PH),radius=BORDER,
   fill=(252,252,250),outline=(185,185,181),width=2)
 # Native portrait title, not a letterboxed landscape video.
 dm=str(P/"fonts"/"DMSans.ttf")
 title=ImageFont.truetype(dm,56)
 micro=ImageFont.truetype(dm,28)
 d.text((60,62),"BRIMBLE  /  SETUP",font=micro,fill=(95,97,93))
 d.text((60,117),"Connect your agent.",font=title,fill=(36,38,35))
 d.text((61,184),"A real, one-take software walkthrough",font=micro,fill=(111,113,108))
 return np.asarray(img)[:,:,::-1].copy()
BASE=stage()
# Clip dynamic browser pixels to rounded-corner window. No fake browser chrome.
shape=Image.new("L",(PW,PH),0)
ImageDraw.Draw(shape).rounded_rectangle((0,0,PW-1,PH-1),radius=BORDER,fill=255)
CLIP=np.asarray(shape,dtype=np.float32)[:,:,None]/255.

# Cursor is a real interaction track, not a fake pointer baked into UI footage.
svg='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 38 48">
 <path d="M4 3 V40 L13 31 L21 46 L29 42 L21 27 L36 27 Z"
 fill="#ffffff" stroke="#181a1d" stroke-width="3" stroke-linejoin="round"/></svg>'''
icon=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(),
  output_width=36,output_height=46))).convert("RGBA")
C=np.asarray(icon,dtype=np.uint8)
CURSOR_RGB=C[:,:,[2,1,0]]
CURSOR_ALPHA=C[:,:,3:4].astype(np.float32)/255
dots=REC["pointer"];TIMES=np.array([x[0] for x in dots])
XS=np.array([x[1] for x in dots]);YS=np.array([x[2] for x in dots])
def pointer(src,t):
 if t<3.65:return src
 ix=int(round(np.interp(t,TIMES,XS)))
 iy=int(round(np.interp(t,TIMES,YS)))
 w,h=CURSOR_RGB.shape[1],CURSOR_RGB.shape[0]
 left=max(0,ix);top=max(0,iy)
 right=min(SW,ix+w);bottom=min(SH,iy+h)
 if right<=left or bottom<=top:return src
 out=src.copy()
 sub=out[top:bottom,left:right]
 rgb=CURSOR_RGB[top-iy:bottom-iy,left-ix:right-ix]
 a=CURSOR_ALPHA[top-iy:bottom-iy,left-ix:right-ix]
 sub[:]=np.uint8(sub.astype(np.float32)*(1-a)+rgb*a)
 return out

FONTFILE=P/"fonts"/"DMSans.ttf"
FONT=ImageFont.truetype(str(FONTFILE),68)
try:FONT.set_variation_by_name("SemiBold")
except Exception:pass
def caption_cache():
 cache={}
 for item in VO:
  words=item["text"].split()
  lines=[];line=""
  for word in words:
   candidate=(line+" "+word).strip()
   if line and FONT.getlength(candidate)>W-90:
    lines.append(line);line=word
   else:line=candidate
  if line:lines.append(line)
  img=Image.new("RGBA",(W,215),(0,0,0,0))
  d=ImageDraw.Draw(img)
  for i,line in enumerate(lines[:3]):
   width=d.textlength(line,font=FONT)
   d.text(((W-width)/2,12+i*78),line,font=FONT,fill=(39,42,39,255))
  rgba=np.asarray(img,dtype=np.uint8)
  cache[item["id"]]=(rgba[:,:,[2,1,0]],rgba[:,:,3:4].astype(np.float32)/255)
 return cache
CAPTION=caption_cache()

def make_frame(src,t):
 z,fx,fy=camera(t)
 scale=(PH/SH)*z
 xx=(PW/2-fx*scale)
 yy=(PH/2-fy*scale)
 xx=max(PW-SW*scale,min(0,xx))
 yy=max(PH-SH*scale,min(0,yy))
 mat=np.array([[scale,0,xx],[0,scale,yy]],dtype=np.float32)
 video=cv2.warpAffine(pointer(src,t),mat,(PW,PH),
   flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
 out=BASE.copy()
 area=out[PY:PY+PH,PX:PX+PW]
 area[:]=np.uint8(area*(1-CLIP)+video*CLIP)
 row=next((row for row in VO if row["start"]<=t<=row["end"]+.15),None)
 if row:
  rgb,a=CAPTION[row["id"]]
  low=out[1600:1600+215,0:W]
  ht=min(low.shape[0],rgb.shape[0])
  low[:ht]=np.uint8(low[:ht].astype(np.float32)*(1-a[:ht])+rgb[:ht]*a[:ht])
 return out

def get_preview(t):
 raw=subprocess.check_output(['ffmpeg','-hide_banner','-loglevel','error','-ss',str(t),'-i',str(SOURCE),
  '-frames:v','1','-f','rawvideo','-pix_fmt','bgr24','pipe:1'])
 return make_frame(np.frombuffer(raw,dtype=np.uint8).reshape(SH,SW,3),t)
if args.preview is not None:
 args.output.parent.mkdir(parents=True,exist_ok=True)
 img=get_preview(args.preview)
 cv2.imwrite(str(args.output),img,[cv2.IMWRITE_JPEG_QUALITY,89])
 print('PREVIEW',args.output,args.output.stat().st_size)
else:
 frames=round((args.seconds or DUR)*FPS)
 decoder=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-i',str(SOURCE),
  '-f','rawvideo','-pix_fmt','bgr24','pipe:1'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 vid=P/"film05-video.mp4"
 enc=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-y',
  '-f','rawvideo','-pix_fmt','bgr24','-video_size',f'{W}x{H}','-framerate',str(FPS),
  '-i','pipe:0','-an','-c:v','libx264','-preset','veryfast','-crf','16',
  '-pix_fmt','yuv420p','-g','120','-threads','7','-movflags','+faststart',str(vid)],
  stdin=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=8*1024*1024)
 began=time.monotonic()
 for i in range(frames):
  data=decoder.stdout.read(SW*SH*3)
  if len(data)!=SW*SH*3:raise RuntimeError('Decode ended early '+str(i))
  src=np.frombuffer(data,dtype=np.uint8).reshape(SH,SW,3)
  img=make_frame(src,i/FPS)
  enc.stdin.write(img.tobytes())
  if i%150==0:print('RENDER',i,frames,round(time.monotonic()-began,1),flush=True)
 enc.stdin.close()
 decoder.stdout.close()
 err=enc.stderr.read().decode(errors='replace')
 if enc.wait(timeout=120):raise RuntimeError('encode failure '+err[-500:])
 decoder.wait(timeout=120)
 voice=P/'narration.wav'
 if not voice.is_file():raise RuntimeError('Narration missing')
 mix=P/'mixed.mp4'
 if MUSIC.is_file():
  af=f'[1:a]aresample=48000[v];[2:a]aresample=48000,atrim=0:{frames/FPS},volume=.055,afade=t=in:d=0.5,afade=t=out:st=12.8:d=1.3[m];[v][m]amix=inputs=2:duration=first:normalize=0[a]'
  mux=['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(vid),
   '-i',str(voice),'-stream_loop','-1','-i',str(MUSIC),
   '-filter_complex',af,'-map','0:v:0','-map','[a]']
 else:
  mux=['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(vid),
       '-i',str(voice),'-map','0:v:0','-map','1:a:0']
 mux+=['-c:v','copy','-c:a','aac','-b:a','192k','-t',str(frames/FPS),str(mix)]
 subprocess.run(mux,check=True,timeout=90)
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',
  '-i',str(mix),'-c:v','copy','-af','loudnorm=I=-16:TP=-1.5:LRA=7',
  '-c:a','aac','-b:a','192k','-movflags','+faststart',str(args.output)],
  check=True,timeout=90)
 subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(args.output),
  '-f','null','-'],check=True,timeout=90)
 print('COMPLETE',args.output,args.output.stat().st_size,'s',frames/FPS,'elapsed',round(time.monotonic()-began,1),flush=True)
