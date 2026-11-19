"""Sauce Basic encoded-media acceptance checks (not creative approval).

Inspects the actual delivered MP4 and samples decoded pixels. The source
manifest and per-hold DOM gates remain separate. A white landing page is
not inherently a blank frame, so low-variance sampled frames flag review
rather than silently deleting sections. No OCR or AI inference required.
"""
from __future__ import annotations
from datetime import datetime,timezone
from io import BytesIO
import json
import math
from pathlib import Path
import subprocess
from PIL import Image,ImageDraw,ImageFilter,ImageStat

def probe_video(path:Path)->dict:
    return json.loads(subprocess.check_output([
      "ffprobe","-v","error","-show_entries",
      "format=duration,size:stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,nb_frames:"
      "chapter=start_time,end_time:chapter_tags=title",
      "-of","json",str(path)],text=True,timeout=30))

def frame_at(video:Path,t:float)->Image.Image:
    raw=subprocess.check_output([
        "ffmpeg","-hide_banner","-loglevel","error",
        "-ss",str(round(t,4)),"-i",str(video),"-frames:v","1",
        "-f","image2pipe","-vcodec","mjpeg","-q:v","2","pipe:1"
    ],timeout=50)
    return Image.open(BytesIO(raw)).convert("RGB")

def analyse_master(video:Path, out_dir:Path, *,
                   chapters:int, source_rates:list[str]|None=None,
                   sample_count:int=16)->dict:
    video=Path(video)
    out_dir=Path(out_dir)
    out_dir.mkdir(parents=True,exist_ok=True)
    obj=probe_video(video)
    streams=[s for s in obj.get("streams",[]) if s.get("codec_type")=="video"]
    issues=[]
    warnings=[]
    if len(streams)!=1:
        issues.append("exactly_one_video_stream_required")
        stream=streams[0] if streams else {}
    else:
        stream=streams[0]
    if (stream.get("codec_name"),stream.get("width"),stream.get("height"),
            stream.get("r_frame_rate"),stream.get("avg_frame_rate"))!=(
            "h264",1920,1080,"60/1","60/1"):
        issues.append("master_codec_resolution_or_clock_wrong")
    length=float(obj.get("format",{}).get("duration",0))
    n=int(stream.get("nb_frames") or 0)
    if n<1 or not math.isclose(n/60,length,abs_tol=1/60+.01):
        issues.append("frame_count_duration_mismatch")
    marks=obj.get("chapters",[])
    if len(marks)!=chapters:
        issues.append("wrong_chapter_count")
    for k,c in enumerate(marks):
        try:
            a=float(c["start_time"]);b=float(c["end_time"])
            if a<0 or b<=a or b>length+.05:raise ValueError()
            if k and abs(a-float(marks[k-1]["end_time"]))>.045:
                raise ValueError()
            if not c.get("tags",{}).get("title"):
                raise ValueError()
        except (ValueError,TypeError,KeyError):
            issues.append("chapter_timestamps_or_labels_invalid")
    for fps in source_rates or []:
        if fps!="60/1" and "source_not_native_60fps" not in warnings:
            warnings.append("source_not_native_60fps")

    # Real media decode is required; ffprobe metadata alone is not proof.
    decode=subprocess.run(["ffmpeg","-hide_banner","-loglevel","error",
        "-xerror","-i",str(video),"-f","null","-"],
        text=True,capture_output=True,timeout=230)
    if decode.returncode!=0:
        issues.append("full_decode_failed")

    times=[.3]+[(i+.5)*length/max(2,sample_count-1)
                for i in range(max(0,sample_count-2))]+[max(.3,length-.3)]
    for c in marks[1:]:
        boundary=float(c["start_time"])
        times.extend([max(.12,boundary-.18),min(length-.12,boundary+.18)])
    times=sorted(set(round(min(length-.12,max(.12,t)),3) for t in times))
    sheet=Image.new("RGB",(4*480,math.ceil(len(times)/4)*292),(24,24,24))
    draw=ImageDraw.Draw(sheet)
    sample=[]
    for i,t in enumerate(times):
        frame=frame_at(video,t)
        thumbnail=frame.resize((480,270),Image.Resampling.LANCZOS)
        gray=thumbnail.convert("L")
        avg=ImageStat.Stat(gray).mean[0]
        std=ImageStat.Stat(gray).stddev[0]
        edge=ImageStat.Stat(gray.filter(ImageFilter.FIND_EDGES)).mean[0]
        # The threshold is for *entirely blank/flat* frames, not genuine
        # white design pages with low-density type.
        suspected=std<2.5 and edge<5.5
        if suspected:
            warnings.append("suspected_blank_or_flat_frame_at_"+str(t))
        sample.append({"t_seconds":t,"luma_mean":round(avg,2),
                       "luma_stddev":round(std,2),"edge_mean":round(edge,2),
                       "suspected_flat":suspected})
        x=(i%4)*480;y=(i//4)*292
        sheet.paste(thumbnail,(x,y))
        draw.text((x+10,y+273),f"{t:.2f}s",fill="#fff")
    sheet_path=out_dir/"basic-contact-sheet.jpg"
    sheet.save(sheet_path,quality=86)
    result={
        "status":"technical_reject" if issues else "technical_pass_creative_pending",
        "master":str(video),"duration_seconds":round(length,3),
        "frames":n,"rate":stream.get("r_frame_rate"),
        "width":stream.get("width"),"height":stream.get("height"),
        "source_rates":source_rates or [],"chapters":len(marks),
        "issues":issues,"warnings":sorted(set(warnings)),
        "pixel_samples":sample,
        "contact_sheet":str(sheet_path),
        "review_required":"Human must inspect 1080p frames, scene holds, text, cursor, overlays, audio/privacy and chapter cuts",
    }
    (out_dir/"basic-media-qa.json").write_text(json.dumps(result,indent=2)+"\n")
    return result
