#!/usr/bin/env python3
"""Narration-driven real-product film composer, no fake interface or cursor.

The voice phrases define when attention changes. DOM receipts establish which
actual screen regions are allowed to receive emphasis. One FFmpeg pass consumes
real 60fps X11 footage and deterministic PIL typography overlays.
"""
from __future__ import annotations
import argparse, json, math, subprocess, time
from pathlib import Path
from functools import lru_cache
import cv2, numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"studio"/".tmp"/"film-paradigm"
source=P/"opensheets-real-ui-x11-60fps.mp4"
receipt=json.loads((P/"real-interactions.json").read_text())
narration=json.loads((P/"voice-timeline.json").read_text())
alignment=json.loads((P/"word-timings.json").read_text())
OUT_W,OUT_H=1920,1080
IN_W,IN_H=1600,900
FPS=60
DURATION=11.35
LEAD=float(receipt.get("lead_s",0.27))
WORDS=alignment["words"]
PHRASES=narration["phrases"]
FONT_BASE="/usr/share/fonts/truetype/liberation/"
FONT=ImageFont.truetype(FONT_BASE+"LiberationSans-Bold.ttf",37)
FONT_META=ImageFont.truetype(FONT_BASE+"LiberationSans-Regular.ttf",22)

# Trust the actual browser receipt. Do not derive shot positions from guessed
# cursor dwell. Screen coordinates are those in the original X11 capture.
select_event=next(e for e in receipt["events"] if e["kind"]=="range_select")
currency_event=next(e for e in receipt["events"] if e["kind"]=="click" and e.get("semanticGoal"))
result_event=next(e for e in receipt["events"] if e["kind"]=="state_change")
if not result_event.get("values") or len(result_event["values"])!=5:
    raise RuntimeError("The filmed application did not verify five formatted amounts")
fx=(select_event["resultRect"]["x"]+select_event["resultRect"]["width"]/2)/IN_W
fy=(select_event["resultRect"]["y"]+select_event["resultRect"]["height"]/2)/IN_H
amount_x=result_event["resultRect"]["x"]+result_event["resultRect"]["width"]/2
btn_x=currency_event["targetRect"]["x"]+currency_event["targetRect"]["width"]/2
# For the action, frame both the actual toolbar control and the selected range.
action_x=(amount_x+btn_x)*.5
result_x=(amount_x*.73+action_x*.27)
action_y=240
result_y=245

# Caption text groups are the original spoken phrases, not guessed generated
# paraphrases. The CPU-transcribed word timestamps are constrained to the
# known synthesized phrase envelopes.
word_tokens=[p["text"].split() for p in PHRASES]
if sum(len(t) for t in word_tokens)!=len(WORDS):
    raise RuntimeError("Local word alignment does not match the narration script")
captions=[]
idx=0
for phrase,tokens in zip(PHRASES,word_tokens):
    subset=WORDS[idx:idx+len(tokens)]
    idx+=len(tokens)
    windows=[]
    for i,word in enumerate(subset):
        start=max(float(phrase["start"]),float(word["start"]))
        if i==0: start=float(phrase["start"])
        nxt=(max(float(subset[i+1]["start"]),start+.08)
             if i+1<len(subset) else float(phrase["end"]))
        end=min(float(phrase["end"]),max(start+.09,nxt))
        windows.append((start,end))
    captions.append({"text":phrase["text"],"tokens":tokens,
                     "start":phrase["start"],"end":phrase["end"],
                     "windows":windows})

def ease(u):
    x=max(0.0,min(1.0,float(u)))
    return x*x*x*(x*(x*6-15)+10)

def between(t,ta,tb,va,vb):
    return va+(vb-va)*ease((t-ta)/max(.0001,tb-ta))

def camera(t):
    # Semantic cue timeline: the first push anticipates the selected amount
    # phrase; the second emphasis follows the observed completed format.
    # This is ONE coherent action with a before / action / result / return.
    start=2.44
    focused=3.41
    click=result_event["t"]
    second_start=max(5.22,click+.20)
    second_end=second_start+.67
    release_start=8.05
    release_end=10.08
    if t<start: return 1.0,IN_W*.5,IN_H*.5
    if t<focused:
        return (between(t,start,focused,1.0,1.66),
                between(t,start,focused,IN_W*.5,action_x),
                between(t,start,focused,IN_H*.5,action_y))
    if t<second_start:
        return 1.66,action_x,action_y
    if t<second_end:
        return (between(t,second_start,second_end,1.66,1.89),
                between(t,second_start,second_end,action_x,result_x),
                between(t,second_start,second_end,action_y,result_y))
    if t<release_start:
        return 1.89,result_x,result_y
    if t<release_end:
        return (between(t,release_start,release_end,1.89,1.0),
                between(t,release_start,release_end,result_x,IN_W*.5),
                between(t,release_start,release_end,result_y,IN_H*.5))
    return 1.0,IN_W*.5,IN_H*.5

def stage_base():
    # Matte art direction: neutral warm gray, natural-looking shadow, one
    # original identity mark; absolutely no gradient wallpaper/glass chrome.
    bg=Image.new("RGB",(OUT_W,OUT_H),(224,225,223))
    shadow=Image.new("L",(OUT_W,OUT_H),0)
    d=ImageDraw.Draw(shadow)
    d.rounded_rectangle((138,80,1782,1005),radius=24,fill=180)
    sm=shadow.filter(ImageFilter.GaussianBlur(29))
    dark=Image.new("RGB",(OUT_W,OUT_H),(33,38,42))
    bg.paste(dark,(0,0),sm.point(lambda x:round(x*.33)))
    # Small understated print-like label outside the screen at opening/ending.
    d=ImageDraw.Draw(bg)
    d.text((136,31),"SAUCE   /   PRODUCT FILM 01",font=FONT_META,fill=(45,47,49))
    return np.asarray(bg)[:,:,::-1].copy()

BG=stage_base()
SOURCE_CORNER=Image.new("L",(IN_W,IN_H),255)
cd=ImageDraw.Draw(SOURCE_CORNER)
# A rounded-window mask is only needed in opening/release contexts.
# Build it once and warp the same geometry alongside the screenshot.
cd.rectangle((0,0,IN_W,IN_H),fill=0)
cd.rounded_rectangle((0,0,IN_W-1,IN_H-1),radius=21,fill=255)
SRC_MASK=np.asarray(SOURCE_CORNER,dtype=np.uint8)

@lru_cache(maxsize=64)
def caption_patch(phrase_index,active):
    c=captions[phrase_index]
    tokens=c["tokens"]
    widths=[FONT.getlength(v) for v in tokens]
    spaces=[FONT.getlength(" ")]*(len(tokens)-1)
    total=sum(widths)+sum(spaces)
    width=int(total+68)
    height=94
    x=max(0,int((OUT_W-width)/2))
    y=875
    overlay=Image.new("RGBA",(width,height),(0,0,0,0))
    draw=ImageDraw.Draw(overlay)
    draw.rounded_rectangle((0,0,width-1,height-1),radius=18,fill=(12,14,16,225))
    offset=34
    for i,token in enumerate(tokens):
        color=(248,201,132,255) if i==active else (249,248,246,255)
        draw.text((round(offset),16),token,font=FONT,fill=color)
        offset+=widths[i]+(spaces[i] if i<len(spaces) else 0)
    arr=np.asarray(overlay,dtype=np.uint8)
    return (x,y,arr[:,:,:3][:,:,[2,1,0]].copy(),
            arr[:,:,3:4].astype(np.float32)/255)

def draw_captions(dst,t):
    phrase_index=next((i for i,c in enumerate(captions)
                       if c["start"]-.06 <= t <= c["end"]+.12),None)
    if phrase_index is None:return dst
    c=captions[phrase_index]
    indices=[i for i,(start,end) in enumerate(c["windows"])
             if start-.04<=t<end+.05]
    active=indices[-1] if indices else (0 if t<=c["start"] else len(c["tokens"])-1)
    x,y,patch,alpha=caption_patch(phrase_index,active)
    h,w=patch.shape[:2]
    roi=dst[y:y+h,x:x+w]
    roi[:]=(patch.astype(np.float32)*alpha+
            roi.astype(np.float32)*(1-alpha)).astype(np.uint8)
    return dst

def transform(src,t):
    zoom,cx,cy=camera(t)
    z=zoom*1.017
    dx=OUT_W*.5-z*cx
    dy=OUT_H*.5-z*cy
    scaled_w=IN_W*z
    scaled_h=IN_H*z
    # Never expose empty borders once focused; at overview show the full
    # genuine application window with the matte stage behind it.
    if zoom>=1.20:
        dx=max(OUT_W-scaled_w,min(0.,dx))
        dy=max(OUT_H-scaled_h,min(0.,dy))
    matrix=np.array([[z,0,dx],[0,z,dy]],dtype=np.float64)
    dst=BG.copy()
    cv2.warpAffine(src,matrix,(OUT_W,OUT_H),dst=dst,
                   flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_TRANSPARENT)
    if zoom<1.13:
        # Clean physical rounded corners at the overview (not a browser fake).
        mask=cv2.warpAffine(SRC_MASK,matrix,(OUT_W,OUT_H),
                            flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,
                            borderValue=0)
        alpha=(mask.astype(np.float32)/255)[:,:,None]
        dst[:]=(dst*alpha+BG*(1-alpha)).astype(np.uint8)
    return draw_captions(dst,t)

def frame_at(t):
    if t<0 or t>=DURATION:raise ValueError("Preview time outside film duration")
    original_t=LEAD+t
    raw=subprocess.check_output(["ffmpeg","-hide_banner","-loglevel","error",
        "-ss",str(original_t),"-i",str(source),"-frames:v","1",
        "-f","rawvideo","-pix_fmt","bgr24","pipe:1"],timeout=25)
    if len(raw)!=IN_W*IN_H*3:raise RuntimeError("Source preview failed")
    return transform(np.frombuffer(raw,np.uint8).reshape(IN_H,IN_W,3),t)

def full_render(destination):
    frames=round(DURATION*FPS)
    decoder=subprocess.Popen([
        "ffmpeg","-hide_banner","-loglevel","error",
        "-ss",str(LEAD),"-i",str(source),
        "-f","rawvideo","-pix_fmt","bgr24","pipe:1"],
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=5*1024*1024)
    music=ROOT.parent/"sauce-demo-assets"/"digital-clouds-mixkit.mp3"
    command=["ffmpeg","-hide_banner","-loglevel","error","-y",
             "-f","rawvideo","-pix_fmt","bgr24","-video_size",f"{OUT_W}x{OUT_H}",
             "-framerate",str(FPS),"-i","pipe:0",
             "-i",str(P/"voice.wav")]
    if music.is_file():
        command+=["-stream_loop","-1","-i",str(music),
                  "-filter_complex",
                  f"[1:a]highpass=f=65,acompressor=threshold=0.12:ratio=2.0:attack=6:release=180,volume=1.0[v];"
                  f"[2:a]atrim=duration={DURATION},volume=0.080,highpass=f=75,"
                  f"afade=t=in:st=0:d=0.55,afade=t=out:st={DURATION-1.35}:d=1.3[m];"
                  f"[v][m]amix=inputs=2:duration=longest:normalize=0,"
                  f"alimiter=limit=0.87:level=0[a]",
                  "-map","0:v","-map","[a]"]
    else:
        command+=["-map","0:v","-map","1:a"]
    command+=["-t",str(DURATION),"-c:v","libx264","-pix_fmt","yuv420p",
              "-profile:v","high","-level:v","4.2","-preset","medium","-crf","17",
              "-threads","7","-g","120","-c:a","aac","-b:a","192k",
              "-movflags","+faststart",str(destination)]
    encoder=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=5*1024*1024)
    size=IN_W*IN_H*3
    t0=time.monotonic()
    for i in range(frames):
        raw=decoder.stdout.read(size)
        if len(raw)!=size:raise RuntimeError(f"Source truncated at frame {i}/{frames}")
        src=np.frombuffer(raw,np.uint8).reshape(IN_H,IN_W,3)
        frame=transform(src,i/FPS)
        try:
            encoder.stdin.write(frame.tobytes())
        except BrokenPipeError as exc:
            detail=encoder.stderr.read().decode(errors="replace")
            raise RuntimeError("FFmpeg encoder closed unexpectedly: "+detail[-5000:]) from exc
        if i%150==0:print("FRAMES",i,"/",frames,"elapsed",round(time.monotonic()-t0,2),flush=True)
    encoder.stdin.close()
    decoder.stdout.close()
    err=encoder.stderr.read().decode(errors="replace")
    status=encoder.wait(timeout=190)
    decoder.wait(timeout=60)
    if status:raise RuntimeError("Encoder failed: "+err[-5000:])
    subprocess.run(["ffmpeg","-v","error","-xerror","-i",str(destination),
                    "-f","null","-"],check=True,timeout=190)
    probe=json.loads(subprocess.check_output([
        "ffprobe","-v","error","-show_entries",
        "stream=codec_type,codec_name,width,height,avg_frame_rate,nb_frames:"
        "format=duration,size","-of","json",str(destination)],text=True))
    video=next(x for x in probe["streams"] if x["codec_type"]=="video")
    if video["nb_frames"]!=str(frames):raise RuntimeError("Frame-count mismatch")
    result={"output":str(destination),"frames":frames,"fps":FPS,
            "verified_values":result_event["values"],
            "frame_decode_pass":True,"render_seconds":round(time.monotonic()-t0,2),
            "audio":"Kokoro speech, licensed Sauce music", "probe":probe}
    destination.with_suffix(".json").write_text(json.dumps(result,indent=2))
    print("DELIVERED",json.dumps(result),flush=True)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--preview",type=float)
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    P.mkdir(parents=True,exist_ok=True)
    if args.preview is not None:
        f=args.output or P/f"preview-{args.preview:.2f}.jpg"
        f.parent.mkdir(parents=True,exist_ok=True)
        cv2.imwrite(str(f),frame_at(args.preview),[cv2.IMWRITE_JPEG_QUALITY,90])
        print("PREVIEW",f,f.stat().st_size,flush=True)
    else:
        full_render(args.output or P/"sauce-currency-product-film-1080p60.mp4")
