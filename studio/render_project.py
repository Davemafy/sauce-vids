#!/usr/bin/env python3
"""Memory-bounded Sauce Studio renderer.

Remotion composes the art-directed window/background/chrome once. FFmpeg
composites *real* recorded browser footage and a licensed audio track through
a rounded mask. This keeps long renders within a 1 GiB isolated VM worker.

Current contract: one static floating-browser scene (no fake camera keyframes).
Full multi-scene/moving-window compositor is deliberately future work.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


STUDIO = Path(__file__).resolve().parent
STATIC = STUDIO / "public"
COMPONENT = "SauceStage"
_SAFE_FILE = re.compile(r"^[a-zA-Z0-9_.-]+$")


def approved_file(kind: str, path: str) -> Path:
    if not isinstance(path, str):
        raise ValueError(f"Invalid {kind} file")
    pieces = path.split("/")
    if len(pieces) != 2 or pieces[0] != kind or not _SAFE_FILE.fullmatch(pieces[1]):
        raise ValueError(f"{kind} filename must be {kind}/<safe-local-file>")
    loc = (STATIC / path).resolve()
    root = STATIC.resolve()
    if root not in loc.parents or not loc.is_file() or loc.is_symlink():
        raise ValueError(f"Approved {kind} file not found: {path}")
    return loc


def _duration(ffprobe: str, path: Path) -> tuple[float, int, int]:
    out = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,width,height",
         "-of", "json", str(path)],
        capture_output=True, text=True, timeout=30, check=True,
    )
    meta = json.loads(out.stdout)
    video = next((s for s in meta.get("streams", [])
                  if s.get("codec_type") == "video"), None)
    if not video:
        raise ValueError("The approved footage has no video stream")
    return float(meta["format"].get("duration") or 0), int(video["width"]), int(video["height"])


def validate(props: dict, ffprobe: str) -> dict:
    if not isinstance(props, dict) or not isinstance(props.get("project"), dict):
        raise ValueError("Project JSON requires a project object")
    project = props["project"]
    if project.get("schema_version") != 1:
        raise ValueError("Unsupported project schema")
    canvas = project.get("canvas", {})
    width, height, fps, duration = [
        canvas.get(x) for x in ("width", "height", "fps", "duration_frames")
    ]
    if (width, height, fps) != (1920, 1080, 30) or not isinstance(duration,int) or not 30 <= duration <= 1800:
        raise ValueError("Studio v0.4 currently supports 1920×1080, 30fps, 1–60 seconds")
    bg = project.get("background", {})
    if bg.get("kind") == "preset":
        if bg.get("preset") not in ("lilac-sunset", "warm-paper", "ink", "sauce"):
            raise ValueError("Unknown stage background preset")
    elif bg.get("kind") == "image":
        approved_file("backgrounds",bg.get("file"))
    else:
        raise ValueError("Background must be a known preset or an approved local image")

    scenes = project.get("scenes")
    if not isinstance(scenes,list) or len(scenes) != 1:
        raise ValueError("Memory-bounded compositor requires exactly one scene")
    scene = scenes[0]
    if scene.get("start_frame") != 0 or scene.get("duration_frames") != duration:
        raise ValueError("Scene must cover the entire canvas duration")
    footage = approved_file("footage",scene.get("footage"))
    offset = scene.get("footage_start_frame",0)
    if not isinstance(offset,int) or offset < 0:
        raise ValueError("Invalid footage offset")
    source_duration, video_w, video_h = _duration(ffprobe, footage)
    if duration / fps + offset / fps > source_duration + 0.05:
        raise ValueError("Requested frames exceed the real captured footage")
    browser = scene.get("browser", {})
    if not isinstance(browser,dict):
        raise ValueError("Browser must be an object")
    bwidth, x, y, radius = [browser.get(n) for n in ("width","x","y","radius")]
    ratio = browser.get("aspect_ratio")
    if (not all(type(v) in (int,float) and math.isfinite(v)
                for v in (bwidth,x,y,radius,ratio))
        or not 1400 <= bwidth <= 1650 or not 0 <= x
        or not 0 <= y or not 0 <= radius <= 36
        or not 1.2 <= ratio <= 2.5):
        raise ValueError("Browser framing is invalid")
    if abs(ratio - (video_w/video_h)) > .015:
        raise ValueError("Window aspect ratio differs from recorded video; refusing to stretch UI")
    video_height = round(bwidth/ratio)
    # Never enlarge under-resolved screen pixels. A 720p or 1440px legacy
    # capture cannot magically become readable by rendering at 1080p.
    if video_w < bwidth or video_h < video_height:
        raise ValueError("Source capture is smaller than the displayed window; recapture at native resolution")
    chrome_h = 86
    if x + bwidth > width or y + video_height + chrome_h > height:
        raise ValueError("Browser content would extend beyond the canvas")
    for key in ("title","url"):
        val = browser.get(key)
        if not isinstance(val,str) or len(val)>120:
            raise ValueError(f"Invalid window {key}")
    if browser.get("chrome") not in ("dark","light"):
        raise ValueError("Unknown browser chrome style")
    camera=scene.get("camera",[])
    if (not isinstance(camera,list)
        or any(k.get("scale") != 1 or k.get("focus_x") != .5 or k.get("focus_y") != .5
               for k in camera)):
        raise ValueError("Current bounded renderer requires a static stage camera; motion must come from the recorded footage")
    audio = project.get("audio")
    if audio:
        approved_file("audio",audio.get("file"))
        gain=audio.get("volume")
        if type(gain) not in (float,int) or not 0 <= gain <= 1:
            raise ValueError("Audio volume must be 0–1")
    return {
      "project":project, "footage":footage,
      "duration_s":duration/fps, "fps":fps,
      "window": {"x":int(x),"y":int(y+chrome_h),"width":int(bwidth),"height":video_height,"radius":int(radius)},
      "audio": approved_file("audio",audio["file"]) if audio else None,
    }


def command(args:list[str], timeout:int=300) -> None:
    """Own the entire renderer process group, including Chromium grandchildren."""
    import signal
    child = subprocess.Popen(args, cwd=STUDIO, start_new_session=True)
    try:
        exit_code = child.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        # subprocess.run() kills only its direct child. npx -> node -> Chrome
        # can otherwise survive indefinitely and exhaust the 1GiB worker.
        try:
            os.killpg(child.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            child.wait(timeout=3)
        except subprocess.TimeoutExpired:
            try: os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError: pass
            child.wait()
        raise RuntimeError(f"Render timed out after {timeout}s; all Sauce child processes terminated")
    if exit_code:
        raise RuntimeError(f"Render command exited {exit_code}")


def render(project_file:Path, output:Path, preview_at:float|None, browser_exe:str|None) -> dict:
    ffmpeg=shutil.which("ffmpeg")
    ffprobe=shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise ValueError("FFmpeg and ffprobe are required")
    data=json.loads(project_file.read_text())
    validated=validate(data,ffprobe)
    scene=validated["project"]["scenes"][0]
    window=validated["window"]
    target=output.resolve()
    target.parent.mkdir(parents=True,exist_ok=True)
    work=target.parent/(target.stem+"-stage")
    work.mkdir(exist_ok=True)
    stage=work/"stage.png"
    matte=work/"matte.png"
    cmd=[
      "npx","remotion","still","src/index.ts",COMPONENT,str(stage),
      "--props="+str(project_file.resolve()),"--log=error",
    ]
    if browser_exe:
        cmd+=["--browser-executable="+browser_exe]
    command(cmd,120)
    from PIL import Image, ImageDraw
    image=Image.new("L",(window["width"],window["height"]),0)
    drawer=ImageDraw.Draw(image)
    drawer.rounded_rectangle(
        (0,0,window["width"]-1,window["height"]-1),
        radius=window["radius"],fill=255)
    image.save(matte)
    duration=validated["duration_s"]
    if preview_at is not None:
        if not 0 <= preview_at < duration:
            raise ValueError("Preview frame outside clip")
        cmd=[ffmpeg,"-hide_banner","-loglevel","error","-y",
             "-ss",str(preview_at+scene.get("footage_start_frame",0)/30),
             "-i",str(validated["footage"]),
             "-i",str(stage),"-i",str(matte),
             "-filter_complex",
             f"[0:v]scale={window['width']}:{window['height']}:flags=lanczos,"
             "format=rgba[footage];[2:v]format=gray[mask];"
             "[footage][mask]alphamerge[rounded];"
             f"[1:v][rounded]overlay={window['x']}:{window['y']}:format=auto,"
             "format=rgb24[v]",
             "-map","[v]","-frames:v","1",str(target)]
        command(cmd,45)
    else:
        cmd=[
          ffmpeg,"-hide_banner","-loglevel","error","-y",
          "-filter_complex_threads","1","-threads","1",
          "-loop","1","-framerate","30","-i",str(stage),
          "-ss",str(scene.get("footage_start_frame",0)/30),
          "-i",str(validated["footage"]),
          "-loop","1","-framerate","30","-i",str(matte),
        ]
        if validated["audio"]:
            cmd+=["-stream_loop","-1","-i",str(validated["audio"])]
        filters=[
            f"[1:v]fps=30,scale={window['width']}:{window['height']}:flags=lanczos,"
            "format=rgba[footage]",
            "[2:v]format=gray[mask]",
            "[footage][mask]alphamerge[rounded]",
            f"[0:v][rounded]overlay={window['x']}:{window['y']}:shortest=1:format=auto,"
            "format=yuv420p[v]"
        ]
        if validated["audio"]:
            fade=max(0,duration-.8)
            filters.append(f"[3:a]atrim=0:{duration:.3f},asetpts=PTS-STARTPTS,"
               f"volume={validated['project']['audio']['volume']},"
               "afade=t=in:st=0:d=0.3,"
               f"afade=t=out:st={fade:.3f}:d=0.8[a]")
        cmd+=["-filter_complex",";".join(filters),"-map","[v]"]
        if validated["audio"]:
            cmd+=["-map","[a]","-c:a","aac","-b:a","160k"]
        else:
            cmd+=["-an"]
        cmd+=["-t",f"{duration:.3f}","-c:v","libx264","-pix_fmt","yuv420p",
              "-crf","19","-preset","veryfast","-threads","1",
              "-movflags","+faststart",str(target)]
        command(cmd,360)
    actual = _duration(ffprobe,target)
    receipt={
      "ok":True,"file":str(target),"bytes":target.stat().st_size,
      "duration_s":actual[0],"width":actual[1],"height":actual[2],
      "source":str(validated["footage"]),
      "project":str(project_file.resolve()),"mode":"preview" if preview_at is not None else "full",
      "compositor":"Remotion still stage + bounded FFmpeg real-footage overlay"
    }
    (target.parent/(target.stem+"-receipt.json")).write_text(json.dumps(receipt,indent=2))
    return receipt


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--project",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    parser.add_argument("--preview-at",type=float)
    parser.add_argument("--browser-executable")
    args=parser.parse_args()
    try:
        print(json.dumps(render(args.project,args.out,args.preview_at,args.browser_executable),indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"ok":False,"error":str(exc)}),file=sys.stderr)
        return 1


if __name__=="__main__":
    raise SystemExit(main())
