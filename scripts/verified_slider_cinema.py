#!/usr/bin/env python3
"""Source-true 15-second verified slider film director.

Works from one real DPR2 browser recording, authenticated *capture evidence*
(not an authenticated web session), source cursor samples and independently
observed product-result DOM geometry. No UI synthesis, retiming of source
states, LLM, third-party music or artificial clicks.

The real captured source spans 960 frames. The flagship takes precisely its
first 900 frames at 60fps. Source click/camera event clocks are calibrated
against the actual snapped input's physical thumb in decoded video.
"""
from __future__ import annotations

import argparse, hashlib, io, json, math, subprocess, time
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from camera_shutter import shutter_camera_warp
from cinematic_recorded_pointer import CinematicRecordedPointer
from click_water_ripple import apply_click_water_ripple
from floating_ui_stage import composite_stage

FPS=60
SW,SH=2880,1800
OW,OH=1920,1080
DEFAULT_FRAMES=900
STAGE_SCALE=.93
FIT=min(OW/SW,OH/SH)
OUTPUT_BG="genuine X11 Chromium source on neutral floated stage"


def smooth(t:float)->float:
    u=max(0.,min(1.,t))
    return u*u*u*(u*(u*6.-15.)+10.)


def sha_file(file:Path)->str:
    digest=hashlib.sha256()
    with file.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class Key:
    frame:int
    zoom:float
    cx:float
    cy:float
    label:str


class Director:
    def __init__(self,manifest:dict,validation:dict,source:Path,frames:int=DEFAULT_FRAMES):
        self.m=manifest
        self.v=validation
        self.source=Path(source)
        if validation.get("schema")!="sauce-native-dpr2-slider-proof-v1":
            raise ValueError("Missing independently measured native source evidence")
        if manifest.get("source_sha256")!=validation.get("sourceSha256"):
            raise ValueError("Manifest does not match source scan")
        if sha_file(self.source)!=validation["sourceSha256"]:
            raise ValueError("Decoded film input changed")
        if frames not in (900,) and not (60<=frames<900):
            raise ValueError("Full release requires exactly 900 source frames")
        if (validation.get("frames",0)<frames or
            (validation.get("width"),validation.get("height"))!=(SW,SH)):
            raise ValueError("Invalid native browser frame geometry")
        self.frame_count=frames
        self.offset=int(validation["sourceFrameToBrowserClockOffsetFrames"])
        if abs(self.offset)>12:raise ValueError("Unacceptably uncertain source clock")
        self.down=[e for e in manifest["events"] if e["kind"]=="pointerdown"]
        self.up=[e for e in manifest["events"] if e["kind"]=="pointerup"]
        self.results=[e for e in manifest["events"] if e["kind"]=="verified_result"]
        if len(self.down)!=3 or len(self.up)!=3 or len(self.results)!=3:
            raise ValueError("Expected three genuine action/result pairs")
        vals=[float(e["rangeValue"]) for e in self.results]
        if not all(b>a for a,b in zip(vals,vals[1:])):raise ValueError("Unverified rising slider")
        prices=[e.get("price") for e in self.results]
        if not all(isinstance(price,str) and price.startswith("$") and
                   "/ mo" in price and price.strip() for price in prices):
            raise ValueError("Unverified real price text")
        if not all(isinstance(e.get("evidence"),str) and e["evidence"].strip()
                   and isinstance(e.get("resultRect"),dict) for e in self.results):
            raise ValueError("Missing observed visible price evidence")
        if [e["label"] for e in self.down]!=[e["label"] for e in self.results]:
            raise ValueError("Click and result labels do not pair")
        self.track=np.asarray([(p["t"],p["x"],p["y"])
                               for p in manifest["pointer_samples"]],np.float64)
        if self.track.ndim!=2 or self.track.shape[1]!=3 or len(self.track)<90:
            raise ValueError("Insufficient authentic pointer recording")
        if np.any(np.diff(self.track[:,0])<0):
            raise ValueError("Nonmonotone source cursor clock")
        self.pointer=CinematicRecordedPointer(
            self.track,[e["t"] for e in self.down],style="ink",film_scale=.56)
        # Discard only source-proven idle time before the first real pointer
        # approach, while retaining 26 natural establishing frames.
        approach=[e for e in manifest["events"] if e["kind"]=="pointer_approach"]
        if approach:
            first_frame=int(math.ceil(float(approach[0]["t"])*FPS-self.offset))
        else:
            first_frame=int(math.ceil(float(self.track[0,0])*FPS-self.offset))
        self.source_trim=max(0,min(60,first_frame-26))
        if self.source_trim+self.frame_count>int(validation["frames"]):
            raise ValueError("No continuous authentic source for a 900-frame film")
        self.keys=self.plan()
        self.check_geometry()

    def f(self,t):
        return int(round((float(t)-self.offset/60)*FPS))-self.source_trim

    def focus(self,idx):
        p=self.down[idx]["pointer"]
        q=self.results[idx]["resultRect"]
        rectcenter=(float(q["x"])+float(q["width"])*.5,
                    float(q["y"])+float(q["height"])*.5)
        point=(float(p["x"]),float(p["y"]))
        return (.45*point[0]+.55*rectcenter[0],
                min(SH-220,.45*point[1]+.55*rectcenter[1]+66.))

    def plan(self):
        first,second,third=self.down
        a,b,c=self.results
        fx1,fy1=self.focus(0)
        fx2,fy2=self.focus(1)
        fx3,fy3=self.focus(2)
        K=lambda t,z,cx,cy,label:Key(self.f(t),z,cx,cy,label)
        keys=[
            Key(0,.965,SW/2,SH/2,"recognize real product"),
            K(first["t"]-1.42,.965,SW/2,SH/2,"allow cursor approach"),
            K(first["t"]-.12,1.65,fx1,fy1,"zoom behind real first action"),
            K(self.up[0]["t"]+.08,1.65,fx1,fy1,"keep slider legible"),
            K(a["t"]+.48,1.79,fx1,fy1,"show observed Pro change"),
            K(second["t"]-1.20,1.79,fx1,fy1,"read verified first payoff"),
            K(second["t"]-.18,1.70,fx2,fy2,"follow next real cursor destination"),
            K(self.up[1]["t"]+.05,1.70,fx2,fy2,"see live Scale action"),
            K(b["t"]+.35,1.79,fx2,fy2,"read observed Scale price"),
            K(third["t"]-1.06,1.79,fx2,fy2,"hold genuine second payoff"),
            K(third["t"]-.20,1.70,fx3,fy3,"anticipate third real drag"),
            K(self.up[2]["t"]+.07,1.70,fx3,fy3,"hold real final click"),
            K(c["t"]+.48,1.84,fx3,fy3,"verify "+c["price"]+" outcome"),
            K(12.08,1.84,fx3,fy3,"final payoff reading"),
            K(13.46,.985,SW/2,SH/2,"release whole product"),
            Key(self.frame_count-1,.985,SW/2,SH/2,"end on legitimate UI")
        ]
        if not all(0<=k.frame<self.frame_count for k in keys):
            raise ValueError("Camera motion cannot fit the source-true film")
        if not all(b.frame>a.frame for a,b in zip(keys,keys[1:])):
            raise ValueError("Camera keys non-monotone")
        return keys

    def pose(self,frame):
        if frame<=self.keys[0].frame:
            k=self.keys[0]
            return k.zoom,k.cx,k.cy
        if frame>=self.keys[-1].frame:
            k=self.keys[-1]
            return k.zoom,k.cx,k.cy
        for i in range(len(self.keys)-1):
            left,right=self.keys[i:i+2]
            if left.frame<=frame<=right.frame:
                u=smooth((frame-left.frame)/(right.frame-left.frame))
                return (left.zoom+(right.zoom-left.zoom)*u,
                        left.cx+(right.cx-left.cx)*u,
                        left.cy+(right.cy-left.cy)*u)
        raise RuntimeError("Missing directed frame")

    def camera(self,unused_manifest,unused_shot,frame,unused_source,unused_out):
        z,x,y=self.pose(frame)
        sc=STAGE_SCALE*FIT*z
        return np.asarray([[sc,0,OW*.5-sc*x],
                           [0,sc,OH*.5-sc*y]],np.float64)

    def check_geometry(self):
        off=[]
        early=[]
        for f in range(self.frame_count):
            t=(f+self.source_trim+self.offset)/60.
            pos=self.pointer.at(t)
            if pos is None:
                early.append(f);continue
            x,y=self.camera(None,None,f,None,None) @ (pos[0],pos[1],1)
            if not 24<x<OW-24 or not 24<y<OH-24:
                off.append((f,round(float(x),1),round(float(y),1)))
        if off:raise ValueError("Recorded pointer projected outside scene "+str(off[:5]))
        # An opening establishing film may omit its first captured pointer,
        # but must never synthesize a pointer there or hide one after it appears.
        if early and (len(early)>110 or early!=list(range(len(early)))):
            raise ValueError("Too much unrecorded cursor in film")
        self.qa=dict(offscreenFrames=len(off),
                     unrecordedEstablishFrames=len(early),
                     recordedInputNeverRepositioned=True)
        for i,r in enumerate(self.results):
            f=min(self.frame_count-1,self.f(r["t"])+24)
            rect=r["resultRect"]
            point=(float(rect["x"])+float(rect["width"])/2,
                   float(rect["y"])+float(rect["height"])/2,1)
            x,y=self.camera(None,None,f,None,None)@point
            if not (100<=x<=OW-100 and 120<=y<=OH-110):
                raise ValueError(f"Source price result {i} is not readable in camera")

    def render_frame(self,source,frame:int,*,shutter=True,ripple=True,cursor=True):
        cam=self.camera(None,None,frame,None,None)
        # Same true browser frame is used for shutter sub-samples; never blend
        # pixels from different source states at a verified click boundary.
        if shutter:
            class Shot:
                def length(self):return DEFAULT_FRAMES
            image=shutter_camera_warp(source,Shot(),frame,self.m,
                                     (SW,SH),(OW,OH),self.camera)
        else:
            image=cv2.warpAffine(source,cam,(OW,OH),
                   flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
        t=(frame+self.source_trim+self.offset)/60.
        if ripple:
            for a in self.down:
                age=t-float(a["t"])
                if not 0<=age<.49:continue
                xy=a["pointer"]
                center=cam @ (float(xy["x"]),float(xy["y"]),1.)
                apply_click_water_ripple(image,(float(center[0]),float(center[1])),
                                         age,intensity=.75,lifetime_s=.49)
        image=composite_stage(image,cam,(SW,SH))
        if cursor:
            pos=self.pointer.at(t)
            if pos:
                x,y=cam @ (pos[0],pos[1],1.)
                self.pointer.paint(image,(float(x),float(y)),t)
        return image

    def export(self,output:Path,*,max_frames:int|None=None,shutter=True):
        output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
        frames=max_frames or self.frame_count
        if not 1<=frames<=self.frame_count:raise ValueError("Bad bounded preview length")
        decoder=cv2.VideoCapture(str(self.source))
        if not decoder.isOpened():raise ValueError("Cannot decode captured browser source")
        decoder.set(cv2.CAP_PROP_POS_FRAMES,self.source_trim)
        command=["ffmpeg","-hide_banner","-loglevel","error","-y",
                 "-f","rawvideo","-pix_fmt","bgr24","-video_size",f"{OW}x{OH}",
                 "-framerate",str(FPS),"-i","pipe:0",
                 "-c:v","libx264","-preset","veryfast","-crf","16",
                 "-pix_fmt","yuv420p","-g","120","-threads","5",
                 "-movflags","+faststart",str(output)]
        ff=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
        started=time.monotonic()
        try:
            for frame_idx in range(frames):
                okay,bgr=decoder.read()
                if not okay:raise RuntimeError("True source missing frame "+str(frame_idx))
                film=self.render_frame(bgr,frame_idx,shutter=shutter)
                ff.stdin.write(film.tobytes())
                if frame_idx%120==0:
                    print("RENDER",frame_idx,"/",frames,
                          round(time.monotonic()-started,2),flush=True)
            ff.stdin.close()
            err=ff.stderr.read().decode(errors="replace")
            code=ff.wait(timeout=120)
            if code:raise RuntimeError("Video encoder failed "+err[-1400:])
        finally:
            decoder.release()
            if ff.poll() is None:ff.terminate()
        print("ENCODED",output,frames,round(time.monotonic()-started,1),flush=True)
        return frames

    def stills(self,folder:Path,seconds):
        folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
        decoder=cv2.VideoCapture(str(self.source))
        try:
            for s in seconds:
                frame=round(float(s)*FPS)
                if not 0<=frame<self.frame_count:raise ValueError("Still outside film")
                decoder.set(cv2.CAP_PROP_POS_FRAMES,frame+self.source_trim)
                ok,src=decoder.read()
                if not ok:raise ValueError("Missing source still")
                img=self.render_frame(src,frame)
                outfile=folder/f"frame-{s:.2f}.jpg"
                cv2.imwrite(str(outfile),img,[cv2.IMWRITE_JPEG_QUALITY,90])
                print("STILL",outfile,flush=True)
        finally:decoder.release()

    def audio(self,silent:Path,master:Path,private_wav:Path):
        from foley_mixer import render_foley_plan
        cues=[]
        for a in self.down:
            frame=self.f(a["t"])
            cues.append(dict(sound="click_crisp",outputSample=frame*800,
                             outputMs=frame*1000/FPS,gain=.40))
        for r in self.results:
            frame=self.f(r["t"])
            cues.append(dict(sound="pop_glass",outputSample=frame*800,
                             outputMs=frame*1000/FPS,gain=.27))
        cues.sort(key=lambda c:c["outputSample"])
        plan=dict(schema="sauce-foley-plan-v1",sampleRate=48000,
                  durationMs=self.frame_count*1000/FPS,masterGain=.23,
                  musicGain=0,muted=False,duckIntervals=[],cues=cues)
        outcome=render_foley_plan(plan,private_wav,
                                  target_duration_ms=self.frame_count*1000/FPS)
        subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
            "-i",str(silent),"-i",str(private_wav),
            "-map","0:v:0","-map","1:a:0","-c:v","copy",
            "-c:a","aac","-ar","48000","-ac","2","-b:a","144k",
            "-movflags","+faststart",str(master)],
            check=True,timeout=95)
        return {"foley":outcome,"cues":cues}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source",type=Path,required=True)
    ap.add_argument("--manifest",type=Path,required=True)
    ap.add_argument("--validation",type=Path,required=True)
    ap.add_argument("--out",type=Path)
    ap.add_argument("--stills",type=str,help="Comma-delimited real capture seconds")
    ap.add_argument("--stills-dir",type=Path)
    ap.add_argument("--preview-frames",type=int)
    ap.add_argument("--no-shutter",action="store_true")
    a=ap.parse_args()
    m=json.loads(a.manifest.read_text());v=json.loads(a.validation.read_text())
    director=Director(m,v,a.source)
    print("PLAN",[(k.frame,k.zoom,round(k.cx),round(k.cy),k.label)
                  for k in director.keys],flush=True)
    print("CURSOR",director.qa,flush=True)
    if a.stills:
        if a.stills_dir is None:raise ValueError("Missing stills directory")
        director.stills(a.stills_dir,[float(t) for t in a.stills.split(",")])
    elif a.out:
        count=director.export(a.out,max_frames=a.preview_frames,
                              shutter=not a.no_shutter)
        receipt={
            "schema":"sauce-verified-slider-film-v1",
            "sourceSha256":v["sourceSha256"],
            "sourceClock":v["sourceFrameToBrowserClockOffsetFrames"],
            "sourceTrimFrames":director.source_trim,
            "sourceFrameRange":[director.source_trim,director.source_trim+count],
            "actualSourceFrames":v["frames"],
            "outputFrames":count,
            "fps":FPS,"size":[OW,OH],"cursor":director.qa,
            "keys":[k.__dict__ for k in director.keys],
            "shutter":not a.no_shutter,"ripple":True,
            "finalCreativeApproval":False
        }
        if count==900:
            master=a.out.with_name(a.out.stem.replace("-silent","")+"-master.mp4")
            wav=a.out.with_name("foley-private.wav")
            receipt["audio"]=director.audio(a.out,master,wav)
            receipt["master"]=str(master)
            receipt["masterSha256"]=sha_file(master)
        a.out.with_suffix(".receipt.json").write_text(
            json.dumps(receipt,indent=2)+"\n")
    else:
        raise ValueError("Supply --stills or --out")


if __name__=="__main__":
    main()
