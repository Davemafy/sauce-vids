"""Owner-worker opt-in native 60Hz source capture of the *real Chromium viewport*.

Uses the already-installed full Chrome, dynamically isolated Xvfb display,
and FFmpeg x11grab 60/1. No fake UI, resampling to 60, or browser toolbar:
an independent real Playwright viewport screenshot calibrates the origin
before recording. The original Playwright 25fps recorder remains default.
"""
from __future__ import annotations

import json
import math
import os
import select
import signal
import subprocess
import time
from pathlib import Path

import cv2
import numpy as np


FULL_CHROME=Path("/opt/continuity-remote/chromium/chrome")
FPS=60
MAX_SOURCE_SECONDS=75


def source_video_filename(receipt:dict)->str:
    """Allow precisely two versioned source formats, never arbitrary paths."""
    name=receipt.get("video","continuous-source.webm")
    if name not in ("continuous-source.webm","continuous-source.mp4"):
        raise ValueError("Unsafe or unknown original browser recording name")
    return name


def capture_mode():
    mode=os.getenv("SAUCE_CAPTURE_MODE","playwright")
    if mode not in ("playwright","x11grab60"):
        raise ValueError("Unknown Sauce capture mode")
    return mode


def calibrate_screen_origin(viewport_image:bytes,screen_image:bytes,
                            viewport_size=(1920,1080), tolerance=11.):
    """Pixel-align independent screenshots without putting Chrome UI in video.

    Screenshot matching is temporary in-memory only. Source must occupy the
    physical capture pixel width exactly. A mismatch rejects native mode.
    """
    w,h=viewport_size
    if (w,h)!=(1920,1080):
        raise ValueError("Native capture currently calibrated only at 1080p")
    src=cv2.imdecode(np.frombuffer(viewport_image,np.uint8),cv2.IMREAD_COLOR)
    scr=cv2.imdecode(np.frombuffer(screen_image,np.uint8),cv2.IMREAD_COLOR)
    if src is None or scr is None or scr.shape[1]!=w or scr.shape[0]<h:
        raise ValueError("Invalid actual source viewport or X11 image")
    # Real Playwright page.screenshot(scale='css') yields exactly CSS pixels.
    if src.shape[:2]!=(h,w):
        raise ValueError("Real browser viewport does not fill native video")
    # Downsample for a robust bounded search against real browser content.
    stride=8
    expected=src[::stride,::stride].astype(np.int16)
    scores=[]
    for y in range(scr.shape[0]-h+1):
        observed=scr[y:y+h:stride,::stride].astype(np.int16)
        score=float(np.abs(observed-expected).mean())
        scores.append(score)
    best_y=min(range(len(scores)),key=lambda i:scores[i])
    # Independently validate the aligned *whole* source at full resolution.
    err=float(np.abs(scr[best_y:best_y+h].astype(np.int16)-
                     src.astype(np.int16)).mean())
    if err>tolerance or scores[best_y]>tolerance:
        raise RuntimeError(
            f"Native browser capture viewport calibration rejected: {err:.3f}")
    return {"x":0,"y":best_y,"width":w,"height":h,
            "mean_absolute_error":round(err,4)}


def verify_live_terminal_frames(path:Path, frames:int)->dict:
    """Fail closed if FFmpeg captured Xvfb AFTER Chromium disappeared.

    A fully black trailing X11 frame is technically valid H264, so ffprobe,
    full decoding and generic quality checks cannot detect the flash.
    Inspect only the final 8 original source frames; never recolor, freeze,
    fabricate, or edit the original pixel stream to conceal a capture bug.
    """
    if type(frames) is not int or frames<16:
        raise RuntimeError("Native browser film too short for terminal integrity check")
    cap=cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError("Cannot independently decode terminal Chromium frames")
    start=max(0,frames-8)
    try:
        cap.set(cv2.CAP_PROP_POS_FRAMES,start)
        observations=[]
        for index in range(start,frames):
            good,frame=cap.read()
            if not good or frame is None:
                raise RuntimeError(f"Native browser capture ended before frame {index}")
            thumbnail=cv2.resize(frame,(192,108),interpolation=cv2.INTER_AREA)
            max_ch=thumbnail.max(axis=2)
            observations.append({
                "is_empty_black":bool(float(np.percentile(max_ch,99.5))<10.),
                "has_page_detail":bool(float(thumbnail.mean())>25.
                                       and float(thumbnail.std())>11.)
            })
    finally:
        cap.release()
    if (observations[-1]["is_empty_black"] and
            any(o["has_page_detail"] for o in observations[:-1])):
        raise RuntimeError(
            "Native60 browser disappeared before capture stopped: "
            "black terminal frame rejected, not exported")
    return {"terminal_original_frames_checked":len(observations),
            "terminal_source_integrity_verified":True}


class Native60Recorder:
    def __init__(self,private:Path):
        self.private=Path(private)
        self.private.mkdir(mode=0o700,parents=True,exist_ok=True)
        self.display_proc=None
        self.ffmpeg_proc=None
        self.display=None
        self.geometry=None
        self.output=self.private/"continuous-source.mp4"
        self._log=(self.private/"native60-ffmpeg.log")
        self._display_log=(self.private/"native60-xvfb.log")

    def start_display(self):
        if not FULL_CHROME.is_file():
            raise RuntimeError("Installed headed Chromium unavailable")
        if self.display_proc is not None:
            raise RuntimeError("Native display already started")
        log=self._display_log.open("ab")
        try:
            p=subprocess.Popen(
                ["Xvfb","-displayfd","1","-screen","0","1920x1200x24",
                 "-nolisten","tcp","-noreset"],
                stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=log)
        finally:
            log.close()
        self.display_proc=p
        ready,_,_=select.select([p.stdout],[],[],7)
        if not ready:
            raise RuntimeError("Native capture display did not initialize")
        num=p.stdout.readline().decode("ascii",errors="replace").strip()
        if not num.isdigit() or len(num)>4 or p.poll() is not None:
            raise RuntimeError("Native capture display failed")
        self.display=":"+num
        p.stdout.close()

    def browser_environment(self):
        if not self.display:
            raise RuntimeError("Native display not started")
        return {**os.environ,"DISPLAY":self.display}

    def launch_arguments(self):
        return ["--no-sandbox","--disable-dev-shm-usage",
                "--window-position=0,0","--window-size=1920,1200",
                "--force-device-scale-factor=1","--no-first-run"]

    def calibrate(self,page):
        dims=page.evaluate("""() => ({
            width:innerWidth,height:innerHeight,dpr:devicePixelRatio,
            screenWidth:screen.width,screenHeight:screen.height
        })""")
        # Playwright virtualizes screen.height to the browser context's
        # configured viewport even though Xvfb owns a taller real display.
        # Trust pixels and actual X11 geometry, not the emulated CSS screen.
        if (dims.get("width")!=1920 or dims.get("height")!=1080 or
            dims.get("dpr")!=2 or dims.get("screenWidth")!=1920 or
            dims.get("screenHeight") not in (1080,1200)):
            raise RuntimeError("Native browser screen/viewport integrity mismatch: "+str(dims))
        page.bring_to_front()
        page_bytes=page.screenshot(type="png",scale="css",animations="disabled")
        grab=subprocess.run(
            ["ffmpeg","-hide_banner","-v","error","-nostdin",
             "-f","x11grab","-framerate","1","-video_size","1920x1200",
             "-draw_mouse","0","-i",self.display,"-frames:v","1",
             "-f","image2pipe","-vcodec","png","-"],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=19)
        if grab.returncode!=0:
            raise RuntimeError("Native capture viewport probe failed")
        self.geometry=calibrate_screen_origin(page_bytes,grab.stdout)
        # The viewport alignment metadata contains no private page pixels.
        (self.private/"native60-source-geometry.json").write_text(
            json.dumps({"schema":"sauce-native60-alignment-v1",
                        **self.geometry,"fps":FPS},indent=2)+"\n")
        return self.geometry

    def start_recording(self):
        if self.geometry is None or self.ffmpeg_proc is not None:
            raise RuntimeError("Native video not ready for recording")
        if self.output.exists():
            raise RuntimeError("Preserve an existing original source recording")
        offset=self.geometry["y"]
        log=self._log.open("ab")
        try:
            # Encode directly to original 60/1 H264. Never use fps=60 on
            # 25fps input: source frames originate from the X11 scene clock.
            cmd=["ffmpeg","-hide_banner","-v","error","-nostdin","-y",
                 "-f","x11grab","-framerate","60",
                 "-video_size","1920x1080","-grab_y",str(offset),
                 "-draw_mouse","0","-i",self.display,
                 "-c:v","libx264","-preset","veryfast","-crf","17",
                 "-threads","4","-pix_fmt","yuv420p",
                 "-movflags","+faststart","-an",str(self.output)]
            t0=time.monotonic()
            self.ffmpeg_proc=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,
                stdout=log,stderr=subprocess.STDOUT)
        finally:
            log.close()
        time.sleep(.20)
        if self.ffmpeg_proc.poll() is not None:
            raise RuntimeError("Native recorder failed before recording")
        # The emission origin is bounded by process startup. The receipt
        # notes method and lack of absolute frame hardware timestamps.
        return t0

    def stop_recording(self):
        p=self.ffmpeg_proc
        if p is None:
            raise RuntimeError("Native recording was never started")
        if p.poll() is None:
            p.send_signal(signal.SIGINT)
        try:
            code=p.wait(timeout=26)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait(timeout=5)
            raise RuntimeError("Native video encoder would not finalize")
        if code not in (0,255) or not self.output.is_file():
            raise RuntimeError("Native recorder failed: "+str(code))
        info=json.loads(subprocess.check_output(
            ["ffprobe","-v","error","-show_entries",
             "stream=codec_name,width,height,r_frame_rate,nb_frames:"
             "format=duration","-of","json",str(self.output)],
            text=True,timeout=16))
        streams=info.get("streams",[])
        if (len(streams)!=1 or streams[0].get("codec_name")!="h264"
            or streams[0].get("r_frame_rate")!="60/1"
            or (streams[0].get("width"),streams[0].get("height"))!=(1920,1080)
            or not 1.7<float(info["format"]["duration"])<=MAX_SOURCE_SECONDS):
            raise RuntimeError("Native60 source provenance mismatch")
        terminal=verify_live_terminal_frames(self.output,int(streams[0]["nb_frames"]))
        return {"source_path":self.output,
                **terminal,
                "source_fps":"60/1",
                "frames":int(streams[0]["nb_frames"]),
                "duration_seconds":float(info["format"]["duration"]),
                "source_capture_method":"x11grab60-original-browser",
                "video_size":{"width":1920,"height":1080},
                "viewport_match_error":self.geometry["mean_absolute_error"],
                "screen_origin":{"x":0,"y":self.geometry["y"]},
                "source_frame_clock":"ffmpeg-x11grab-60-wallclock"}

    def close(self):
        for p in (self.ffmpeg_proc,self.display_proc):
            if p is None:continue
            if p.poll() is None:
                p.terminate()
                try:p.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    p.kill()
                    p.wait(timeout=4)
