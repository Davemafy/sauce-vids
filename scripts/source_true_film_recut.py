#!/usr/bin/env python3
"""Owner-only source-true time recut. Compile using the existing TS beat-lock engine.

Never invent or reorder source frames. Reuse a previously verified Sauce
1920x1080/60 master, editing its genuine video AND timed event Foley together.
"""
from __future__ import annotations
import argparse,hashlib,json,subprocess
from pathlib import Path
import cv2,numpy as np

RATE=60
COMPILER=Path(__file__).resolve().parent/"studio-motion/dist/sourceTrueRecut.js"


def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for piece in iter(lambda:f.read(1<<20),b""):
            h.update(piece)
    return h.hexdigest()


def probe(path):
    d=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries",
        "stream=codec_name,codec_type,width,height,nb_frames,r_frame_rate,sample_rate:format=duration",
        "-of","json",str(path)],text=True,timeout=25))
    return d


def validate(source,manifest,master,receipt,plan):
    if any(not p.is_file() or p.is_symlink() for p in
           (source,manifest,master,receipt,plan)):
        raise ValueError("Original regular source/master/receipt files required")
    original=json.loads(manifest.read_text())
    edl=json.loads(plan.read_text())
    r=json.loads(receipt.read_text())
    src_sha=sha(source);man_sha=sha(manifest)
    declared=r.get("film_plan",{})
    if (edl.get("sourceSha256")!=src_sha or
        edl.get("manifestSha256")!=man_sha or
        declared.get("sourceSha256")!=src_sha or
        declared.get("manifestSha256")!=man_sha or
        declared.get("planSha256")!=sha(plan)):
        raise ValueError("Original browser/film evidence hash mismatch")
    if Path(r.get("file","")).resolve()!=master.resolve() or not r.get("full_decode_verified"):
        raise ValueError("Original renderer did not certify this exact master")
    src=next(s for s in probe(source)["streams"] if s["codec_type"]=="video")
    info=probe(master);vid=next(s for s in info["streams"] if s["codec_type"]=="video")
    audio=next((s for s in info["streams"] if s["codec_type"]=="audio"),{})
    frames=int(src.get("nb_frames") or 0)
    if (src.get("r_frame_rate")!="60/1" or vid.get("r_frame_rate")!="60/1"
        or (vid.get("width"),vid.get("height"))!=(1920,1080)
        or audio.get("sample_rate")!="48000" or vid.get("codec_name")!="h264"
        or int(vid.get("nb_frames") or -1)!=frames
        or int(r.get("frames",-1))!=frames
        or frames!=round(float(original.get("duration",0))*RATE)):
        raise ValueError("Original source and rendered master are not native source-clock matches")
    return src_sha,man_sha,frames


def _filter(segments):
    parts=[]
    for i,s in enumerate(segments):
        a=int(s["startFrame"]);b=int(s["endFrame"])
        parts.extend((f"[0:v]trim=start_frame={a}:end_frame={b},setpts=PTS-STARTPTS[v{i}]",
                      f"[0:a]atrim=start_sample={a*800}:end_sample={b*800},asetpts=PTS-STARTPTS[a{i}]"))
    refs="".join(f"[v{i}][a{i}]" for i in range(len(segments)))
    return ";".join(parts+[f"{refs}concat=n={len(segments)}:v=1:a=1[v][a]"])


def verify_lineage(original,edited,segments,events,count):
    mapping=[f for s in segments for f in range(s["startFrame"],s["endFrame"])]
    if len(mapping)!=count or len(set(mapping))!=count or mapping!=sorted(mapping):
        raise ValueError("Temporal edit duplicated or reordered source footage")
    sample={0,count-1,*range(0,count,max(1,count//27))}
    for s in segments:
        f=s["outputStartFrame"]
        sample.update((max(0,f-1),f,min(count-1,f+1)))
    for e in events:
        for field in ("outputPressFrame","outputResultFrame"):
            f=e[field]
            sample.update((max(0,f-1),f,min(count-1,f+1)))
    o=cv2.VideoCapture(str(original));p=cv2.VideoCapture(str(edited))
    if not o.isOpened() or not p.isOpened():raise ValueError("Could not decode both films")
    diffs=[]
    try:
        for ix in sorted(sample):
            o.set(cv2.CAP_PROP_POS_FRAMES,mapping[ix])
            p.set(cv2.CAP_PROP_POS_FRAMES,ix)
            ok,a=o.read();good,b=p.read()
            if not ok or not good:raise ValueError("Missing source-frame evidence")
            def gray(v):
                return cv2.resize(cv2.cvtColor(v,cv2.COLOR_BGR2GRAY),(320,180),
                                  interpolation=cv2.INTER_AREA).astype(np.float32)
            distance=float(np.abs(gray(a)-gray(b)).mean())
            if distance>5.:raise ValueError("Original product pixels changed outside recompression tolerance")
            diffs.append(distance)
    finally:
        o.release();p.release()
    return {"sampledOutputFrames":len(diffs),
            "maxDownscaledGrayMAE":round(max(diffs),4),
            "medianDownscaledGrayMAE":round(float(np.median(diffs)),4),
            "sourceOriginalFramesOnly":True}


def compile_timeline(manifest):
    if not COMPILER.is_file():
        raise ValueError("Existing TS beat-lock planner not built")
    compiled=subprocess.run(["node",str(COMPILER),str(manifest)],
                            capture_output=True,text=True,timeout=40,check=False)
    if compiled.returncode:
        raise ValueError("Original source timeline rejected: "+compiled.stderr[-300:])
    return json.loads(compiled.stdout)


def run(source,manifest,master,prior_receipt,film_plan,out,receipt_out):
    source,manifest,master,prior_receipt,film_plan,out,receipt_out=map(Path,
        (source,manifest,master,prior_receipt,film_plan,out,receipt_out))
    if out.exists() or receipt_out.exists() or out.resolve()==master.resolve():
        raise ValueError("No overwrite of original or prior experiment")
    src_sha,man_sha,original_frames=validate(
        source,manifest,master,prior_receipt,film_plan)
    edit=compile_timeline(manifest)
    segments=edit.get("segments",[])
    count=edit.get("outputFrameCount")
    if (edit.get("schema")!="sauce-source-true-recut-v1" or
        edit.get("sourceFrameCount")!=original_frames or edit.get("fps")!=60
        or not isinstance(count,int) or not 180<=count<original_frames
        or not 2<=len(segments)<=12 or
        sum(s["endFrame"]-s["startFrame"] for s in segments)!=count):
        raise ValueError("Malformed / nonproductive native source time cut")
    if any(not 0<=s["startFrame"]<s["endFrame"]<=original_frames
           for s in segments):
        raise ValueError("Edit outside source bounds")
    out.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    temp=out.with_name(out.stem+".partial.mp4")
    if temp.exists():raise ValueError("Unfinished previous render exists")
    try:
        cmd=["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
             "-i",str(master),"-filter_complex",_filter(segments),
             "-map","[v]","-map","[a]","-r","60","-fps_mode","cfr",
             "-c:v","libx264","-preset","medium","-crf","15","-pix_fmt","yuv420p",
             "-g","120","-c:a","aac","-ar","48000","-b:a","128k",
             "-movflags","+faststart",str(temp)]
        subprocess.run(cmd,capture_output=True,check=True,timeout=240)
        parsed=probe(temp)
        v=next(s for s in parsed["streams"] if s["codec_type"]=="video")
        a=next(s for s in parsed["streams"] if s["codec_type"]=="audio")
        duration=float(parsed["format"]["duration"])
        if ((v.get("width"),v.get("height"),v.get("r_frame_rate"))!=(1920,1080,"60/1")
            or int(v["nb_frames"])!=count or a.get("sample_rate")!="48000"
            or abs(duration-count/RATE)>.055):
            raise ValueError("Native frame/audio timeline mismatch in edited film")
        subprocess.run(["ffmpeg","-v","error","-xerror","-i",str(temp),
                        "-f","null","-"],timeout=240,check=True)
        pixels=verify_lineage(master,temp,segments,edit["events"],count)
        record={"schema":"sauce-temporal-film-v1",
                "sourceSha256":src_sha,"manifestSha256":man_sha,
                "originalFilmSha256":sha(master),"originalPlanSha256":sha(film_plan),
                "outputFilmSha256":sha(temp),"sourceFrames":original_frames,
                "outputFrames":count,"outputDurationSeconds":duration,
                "videoCodec":"h264","audioRate":48000,"nativeFps":60,
                "sourceFrameEdit":edit,"pixelLineage":pixels,
                "fullDecodeVerified":True,"creativeApproved":False,
                "productionReady":False}
        temp.rename(out)
        receipt_out.write_text(json.dumps(record,indent=2)+"\n")
        return record
    finally:
        if temp.exists():temp.unlink()


if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ("source","manifest","master","render-receipt","film-plan","output","receipt"):
        ap.add_argument("--"+name,required=True,type=Path)
    x=ap.parse_args()
    record=run(x.source,x.manifest,x.master,x.render_receipt,
               x.film_plan,x.output,x.receipt)
    print(json.dumps({"frameCount":record["outputFrames"],
      "seconds":record["outputDurationSeconds"],
      "filmSha256":record["outputFilmSha256"],
      "lineage":record["pixelLineage"],"creativeApproved":False},indent=2))
