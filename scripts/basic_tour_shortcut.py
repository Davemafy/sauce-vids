#!/usr/bin/env python3
"""Source-true Basic Short Cut from the same verified scene captures.

The *complete tour is retained*. This only compiles a shorter, honest
editorial EDL from the recorded landing-page holds. It never invents a
page, browser click, cursor move, product feature, or frame. Uses existing
FFmpeg video packaging and hash-pinned scene receipts; advanced FilmPlan
continues to govern cinematic camera/effect directions separately.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from typing import Any
from io import BytesIO
from PIL import Image,ImageStat

SCHEMA="sauce-basic-short-cut-v1"
DEFAULT_MAX_SECONDS=30
FPS=30

def digest(path:Path)->str:
    h=sha256()
    with path.open("rb") as f:
        for part in iter(lambda:f.read(1024*1024),b""):
            h.update(part)
    return h.hexdigest()

def load_scene(scene_dir:Path)->dict:
    """Require existing genuine capture, source, and validated film plan."""
    receipt_file=scene_dir/"receipt.json"
    media_file=scene_dir/"segment-1080p60.mp4"
    plan_file=scene_dir/"film-plan.json"
    manifest_file=scene_dir/"capture-manifest.json"
    for f in (receipt_file,media_file,plan_file,manifest_file):
        if not f.is_file():
            raise ValueError(f"Missing verified source: {f.name}")
    receipt=json.loads(receipt_file.read_text())
    film=json.loads(plan_file.read_text())
    manifest=json.loads(manifest_file.read_text())
    if (film.get("schema")!="sauce-film-plan-v1"
            or film.get("sourceSha256")!=digest(media_file)
            or film.get("manifestSha256")!=digest(manifest_file)
            or receipt.get("encoded_sha256")!=digest(media_file)
            or receipt.get("url")!=manifest.get("source_url")):
        raise ValueError(f"Refusing unverified source: {scene_dir}")
    if film.get("cursor")!="none" or film.get("presentation")!="fullscreen":
        raise ValueError("Scroll-only short cut requires an unmodified wide source")
    if receipt.get("issues"):
        # We may still produce a REVIEW candidate, but never call it approved.
        print(f"LOW_CONFIDENCE_SOURCE {receipt['url']}: {receipt['issues']}",flush=True)
    return {"receipt":receipt,"film":film,"manifest":manifest,
            "video_path":media_file,"film_plan_path":plan_file,
            "manifest_path":manifest_file}


def hold_beats(scene:dict)->list[dict]:
    receipt=scene["receipt"]
    observed=scene["manifest"].get("observed_scroll",[])
    holds=receipt.get("hold_samples",[])
    duration=float(receipt["encoded_seconds"])
    if not holds:
        raise ValueError("No real source hold observations")
    # Existing video trim leaves ~0.6s establishing lead-in before the
    # capture_start timestamp. This is a bounded approximate alignment;
    # it is NOT a fabricated screenshot or an asserted original click.
    lead=.6
    beats=[{"index":0,"at":.40,
            "maximum":min(float(holds[0]["duration_ms"])/1000,duration-.5),
            "scroll_y":holds[0]["scroll_y"],
            "words":0,"issues":holds[0].get("issues",[])}]
    for i,action in enumerate(observed):
        if i+1>=len(holds):
            break
        hold=holds[i+1]
        at=float(action["t"])+lead+.20
        possible=min(
            float(hold["duration_ms"])/1000-.20,
            duration-at-.14)
        if possible<1.3:
            continue
        beats.append({"index":i+1,"at":round(at,3),
            "maximum":round(possible,3),
            "scroll_y":hold["scroll_y"],
            "words":0,"issues":hold.get("issues",[])})
    return beats


def salience_score(scene:dict)->float:
    """Rank real recorded first frames, never invent a homepage hook.

    A high-contrast interface often makes a more useful first frame
    than an almost-empty whitespace hero. This is only a proxy: must be
    human-reviewed; do not use an error screen as a customer film.
    """
    data=subprocess.check_output([
        "ffmpeg","-hide_banner","-loglevel","error","-ss","1.0",
        "-i",str(scene["video_path"]),"-frames:v","1",
        "-f","image2pipe","-vcodec","mjpeg","pipe:1"],timeout=30)
    image=Image.open(BytesIO(data)).convert("L").resize((320,180))
    stat=ImageStat.Stat(image)
    nonwhite=sum(1 for px in image.tobytes() if px<210)/float(image.width*image.height)
    return round(stat.stddev[0]+15*nonwhite,3)



def choose_shots(scenes:list[dict],*,duration_limit:float=DEFAULT_MAX_SECONDS,
                 hook_strategy:str="home")->dict:
    if not 1<=len(scenes)<=8:
        raise ValueError("Short cuts support 1..8 previously recorded scenes")
    if hook_strategy not in ("home","strongest_hero"):
        raise ValueError("Invalid hook strategy")
    if not 8<=duration_limit<=60:
        raise ValueError("Short Cut budget must be 8..60 seconds")
    shots=[]
    for page,scene in enumerate(scenes):
        beats=hold_beats(scene)
        # Every real chosen page gets its first hero and one later
        # section. The final homepage CTA beat is reserved for the end.
        hero=beats[0]
        shots.append({"page":page,"kind":"establish","beat":hero,
                      "start":hero["at"],"zoom":1.18,
                      "duration":min(2.65,hero["maximum"])})
        if len(beats)>3:
            candidate=beats[len(beats)//2]
            # Prefer a real hold free from observed readiness issues.
            clean=[b for b in beats[2:-1] if not b["issues"]
                   and b["maximum"]>=1.7]
            if clean:
                candidate=min(clean,key=lambda b:abs(b["index"]-candidate["index"]))
            arrival=max(.12,candidate["at"]-1.45)
            shots.append({"page":page,"kind":"feature","beat":candidate,
                          "start":arrival,"zoom":1.13,
                          "duration":min(3.85,candidate["at"]-arrival
                                         +min(2.4,candidate["maximum"]))})
        elif len(beats)>=2:
            candidate=beats[-1]
            arrival=max(.12,candidate["at"]-1.45)
            shots.append({"page":page,"kind":"feature","beat":candidate,
                          "start":arrival,"zoom":1.13,
                          "duration":min(3.85,candidate["at"]-arrival
                                         +min(2.4,candidate["maximum"]))})
    if len(scenes)>=2:
        last=hold_beats(scenes[0])[-1]
        if last["maximum"]>=1.5:
            shots.append({"page":0,"kind":"closing","beat":last,
                          "start":last["at"],"zoom":1.15,
                          "duration":min(2.6,last["maximum"])})
    salience=None
    if hook_strategy=="strongest_hero" and len(scenes)>1:
        salience=[salience_score(scene) for scene in scenes]
        opener=max(range(len(scenes)),key=lambda i:salience[i])
        if opener!=0:
            first=next(i for i,s in enumerate(shots)
                       if s["page"]==opener and s["kind"]=="establish")
            strongest=shots.pop(first)
            strongest["kind"]="hero_hook"
            strongest["zoom"]=1.10
            strongest["dynamic_push"]=True
            shots.insert(0,strongest)
    # Never solve a budget problem by speeding through the source.
    # Drop complete optional feature beats first, never truncate text
    # halfway or pretend to record an unvisited page.
    dropped=[]
    while sum(s["duration"] for s in shots)>duration_limit:
        optional=[i for i,s in enumerate(shots) if s["kind"]=="feature"]
        if not optional:
            raise ValueError("Duration budget too short for readable establishes")
        removed=shots.pop(optional[-1])
        dropped.append({"sourceScene":removed["page"],"kind":removed["kind"],
                        "reason":"duration_budget_cannot_accelerate_readable_text"})
    if sum(s["duration"] for s in shots)<4.0:
        raise ValueError("Not enough observed source footage for a cut")
    edl={
        "schema":SCHEMA,
        "source":"verified_sauce_basic_scene_receipts",
        "output":{"width":1920,"height":1080,"fps":FPS,"audio":"silent",
                  "transitions":"clean_hard_cuts"},
        "mode":"review_candidate",
        "budgetSeconds":duration_limit,
        "hookStrategy":hook_strategy,
        "heroSalienceScores":salience,
        "droppedForBudget":dropped,
        "durationSeconds":round(sum(s["duration"] for s in shots),3),
        "scenes":[{"url":s["receipt"]["url"],
                   "videoSha256":digest(s["video_path"]),
                   "manifestSha256":digest(s["manifest_path"]),
                   "originalFilmPlanSha256":digest(s["film_plan_path"])}
                  for s in scenes],
        "shots":[{"scene":s["page"],"kind":s["kind"],
                  "sourceStartSeconds":round(s["start"],3),
                  "durationSeconds":round(s["duration"],3),
                  "sourceCropZoom":s["zoom"],
                  "sourceDynamicPush":bool(s.get("dynamic_push",False)),
                  "sourceScrollY":s["beat"]["scroll_y"],
                  "sourceHoldIndex":s["beat"]["index"]}
                 for s in shots],
    }
    return edl


def compile_cut(edl:dict,scenes:list[dict],out:Path)->dict:
    out.mkdir(parents=True,exist_ok=True)
    if edl.get("schema")!=SCHEMA:
        raise ValueError("Unknown Short Cut EDL")
    if len(scenes)!=len(edl.get("scenes",[])):
        raise ValueError("Missing captured sources")
    for ref,scene in zip(edl["scenes"],scenes):
        if (ref["videoSha256"]!=digest(scene["video_path"])
                or ref["manifestSha256"]!=digest(scene["manifest_path"])
                or ref["originalFilmPlanSha256"]!=digest(scene["film_plan_path"])):
            raise ValueError("Source file changed since EDL construction")
    segments=[]
    for i,shot in enumerate(edl["shots"]):
        scene=scenes[shot["scene"]]
        start=float(shot["sourceStartSeconds"])
        dur=float(shot["durationSeconds"])
        source_dur=float(scene["receipt"]["encoded_seconds"])
        if start<.0 or dur<1.2 or start+dur>source_dur+.03:
            raise ValueError("Shot exceeds the original source recording")
        part=out/f"cut-{i:02d}.mp4"
        framecount=round(dur*FPS)
        # Real browser movement into the recorded hold, not slideshow stills.
        # Bounded center framing uses original source pixels only, no UI
        # reconstruction. In the advanced product this can be a FilmPlan
        # camera keyframe; Basic uses FFmpeg for a flat compact derivative.
        zoom=float(shot.get("sourceCropZoom",1.0))
        if not 1<=zoom<=1.22:
            raise ValueError("Unbounded Basic crop zoom")
        if shot.get("sourceDynamicPush"):
            # The gentle 1.10->1.15 camera push adds no fictional content;
            # only original source pixels sampled with FFmpeg zoompan.
            # It is limited to the opening, not gratuitously on every beat.
            camera=(f"fps={FPS},zoompan="
                    "z='min(max(zoom,1.10)+0.0007,1.15)':"
                    "x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':"
                    f"d=1:s=1920x1080:fps={FPS},"
                    "format=yuv420p,setsar=1")
        else:
            camera=(f"crop=iw/{zoom}:ih/{zoom}:(iw-iw/{zoom})/2:"
                    f"(ih-ih/{zoom})/2,scale=1920:1080:flags=lanczos,"
                    f"fps={FPS},format=yuv420p,setsar=1")
        cmd=["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
             "-ss",f"{start:.3f}","-i",str(scene["video_path"]),
             "-frames:v",str(framecount),"-vf",camera,
             "-an","-c:v","libx264","-preset","veryfast","-crf","18",
             "-movflags","+faststart",str(part)]
        subprocess.run(cmd,check=True,timeout=150)
        segments.append(part)
    concat_file=out/"private-cut-concat.txt"
    concat_file.write_text("".join(
        "file '"+str(p.resolve()).replace("'","'\\''")+"'\n"
        for p in segments))
    master=out/"short-cut-1080p30.mp4"
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin",
         "-y","-f","concat","-safe","0","-i",str(concat_file),"-map","0:v:0",
         "-c","copy","-movflags","+faststart",str(master)],
         check=True,timeout=120)
    metadata=json.loads(subprocess.check_output([
        "ffprobe","-v","error","-show_entries",
        "stream=codec_name,width,height,r_frame_rate,nb_frames:format=duration",
        "-of","json",str(master)],text=True))
    v=metadata["streams"][0]
    if (v["codec_name"],v["width"],v["height"],v["r_frame_rate"])!=(
            "h264",1920,1080,"30/1"):
        raise RuntimeError("Preview MP4 quality gate failed")
    subprocess.run(["ffmpeg","-v","error","-xerror","-i",str(master),
                    "-f","null","-"],check=True,timeout=120)
    actual=float(metadata["format"]["duration"])
    if abs(actual-edl["durationSeconds"])>.15:
        raise RuntimeError("Short Cut actual/declared duration mismatch")
    source_issues={scene["receipt"]["url"]:scene["receipt"].get("issues",[])
                   for scene in scenes if scene["receipt"].get("issues")}
    result={
        "status":("low_confidence_creative_review_required"
                  if source_issues else "technical_pass_creative_review_required"),
        "sourceIssues":source_issues,
        "schema":SCHEMA,"video":str(master),"videoSha256":digest(master),
        "durationSeconds":actual,"frames":int(v["nb_frames"]),
        "shots":len(segments),"size":master.stat().st_size,
        "nativeSourceFramesPerSecond":"25/1 in previously captured Chromium",
        "outputFps":"30/1 resampled",
        "limitations":["Human film-quality approval required",
                       "Only pre-verified source clips used",
                       "Not a substitute for the comprehensive site tour",
                       "No narrated product claims or simulated clicks"],
    }
    (out/"receipt.json").write_text(json.dumps(result,indent=2))
    (out/"short-cut-edl.json").write_text(json.dumps(edl,indent=2))
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--scene",action="append",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--max-seconds",type=float,default=DEFAULT_MAX_SECONDS)
    p.add_argument("--plan-only",action="store_true")
    p.add_argument("--hook",choices=["home","strongest_hero"],default="home")
    args=p.parse_args()
    scenes=[load_scene(d) for d in args.scene]
    edl=choose_shots(scenes,duration_limit=args.max_seconds,
                     hook_strategy=args.hook)
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"short-cut-edl.json").write_text(json.dumps(edl,indent=2))
    if args.plan_only:
        print(json.dumps(edl,indent=2))
        return
    print(json.dumps(compile_cut(edl,scenes,args.out),indent=2))


if __name__=="__main__":
    main()
