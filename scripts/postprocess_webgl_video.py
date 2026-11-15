#!/usr/bin/env python3
"""Final WebGL2 post-process on an encoded Sauce master (WebGL, not CPU approximation)."""
from __future__ import annotations
import argparse,json,os,subprocess
from pathlib import Path
import cv2
from playwright.sync_api import sync_playwright
from webgl_optics import WebGLOptics

CHROME='/opt/devmcp-browsers/chromium_headless_shell-1254/chrome-headless-shell-linux64/chrome-headless-shell'

def apply_video(input_path:Path,output:Path,*,limit_frames:int|None=None)->dict:
    if input_path.resolve()==output.resolve():raise ValueError('Separate source/output required')
    cap=cv2.VideoCapture(str(input_path))
    w,h,fps=(int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
              int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
              float(cap.get(cv2.CAP_PROP_FPS)))
    if (w,h)!=(1920,1080) or abs(fps-60)>0.01:
        raise ValueError('WebGL optics supports 1920x1080 at 60fps')
    frame_count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if frame_count<=0:raise RuntimeError('Missing input video frames')
    output.parent.mkdir(parents=True,exist_ok=True)
    video_only=output.with_name(output.stem+'-optics-video-only.mp4')
    encoder=subprocess.Popen([
        'ffmpeg','-hide_banner','-loglevel','error','-y',
        '-f','rawvideo','-pix_fmt','bgr24','-video_size','1920x1080',
        '-r','60','-i','pipe:0','-an','-c:v','libx264','-crf','14',
        '-preset','medium','-threads','7','-pix_fmt','yuv420p',
        '-movflags','+faststart',str(video_only)],
        stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    frames=0
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True,executable_path=CHROME,
                args=['--no-sandbox','--disable-dev-shm-usage',
                      '--enable-unsafe-swiftshader','--use-gl=angle',
                      '--use-angle=swiftshader'])
            context=browser.new_context(viewport={'width':1920,'height':1080})
            shader=WebGLOptics(context)
            while True:
                if limit_frames and frames>=limit_frames:break
                ok,frame=cap.read()
                if not ok:break
                output_frame=shader.apply(frame,frames)
                encoder.stdin.write(output_frame.tobytes())
                frames+=1
                if frames%60==0:print(f'WEBGL {frames}/{frame_count}',flush=True)
            shader.close();browser.close()
        encoder.stdin.close()
        if encoder.wait(timeout=120)!=0:
            raise RuntimeError('FFmpeg optics encoder exited with error')
        # Retain source soundtrack if present; -map 1:a? skips it for
        # silent proofs. The shader only affects picture.
        p=subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',
            '-i',str(video_only),'-i',str(input_path),'-map','0:v:0',
            '-map','1:a:0?','-c','copy','-shortest',
            '-movflags','+faststart',str(output)],capture_output=True,text=True)
        if p.returncode:raise RuntimeError('WebGL mux failed: '+p.stderr)
    finally:
        cap.release()
        if encoder.poll() is None:
            if encoder.stdin and not encoder.stdin.closed:encoder.stdin.close()
            try:encoder.wait(timeout=5)
            except subprocess.TimeoutExpired:encoder.kill()
        video_only.unlink(missing_ok=True)
    if frames!=min(frame_count,limit_frames or frame_count):
        raise RuntimeError(f'WebGL optics processed only {frames} frames')
    return {'renderer':'WebGL2','frames':frames,'resolution':[w,h],
            'fps':fps,'shader':'optics-webgl2.html','source':str(input_path),
            'master':str(output),'grain':.02,'edge_aberration_max_uv':.00085,
            'vignette_max':.08}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--limit-frames',type=int)
    args=parser.parse_args()
    print(json.dumps(apply_video(args.input,args.output,
              limit_frames=args.limit_frames),indent=2))
