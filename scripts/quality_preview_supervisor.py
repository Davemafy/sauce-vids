#!/usr/bin/env python3
"""Deterministic evidence-led film QA; no inference or compositor mutation."""
import argparse, hashlib, json, math, subprocess
from pathlib import Path
import numpy as np

def probe(path):
    return json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(path)]))

def digest(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()

def frames(path, seconds, fps=10, *, start=0.):
    if (type(start) not in (float,int) or not math.isfinite(start) or
        start<0 or start>75 or not 0<seconds<=75):
        raise ValueError("Invalid bounded source frame sample window")
    # Trim on decode, *after* -i, to align real Chromium source UI frames
    # with the separately encoded postproduced film's own exact source trim.
    cmd=["ffmpeg","-v","error","-i",str(path)]
    if start:
        cmd+=["-ss",str(round(start,5))]
    cmd+=["-t",str(seconds),"-vf",f"fps={fps},scale=160:90,format=gray","-f","rawvideo","-"]
    data=subprocess.check_output(cmd,timeout=90)
    return np.frombuffer(data,dtype=np.uint8).reshape(-1,90,160).astype(np.int16)


def _source_event_windows(manifest):
    """Native verified event or paired real browser click/outcome timestamps."""
    rows=manifest.get("events")
    if isinstance(rows,list) and rows:
        return [(float(e["start"])-.15,float(e["t"])+.2)
                for e in rows if isinstance(e,dict)
                and isinstance(e.get("evidence"),str) and e["evidence"].strip()
                and type(e.get("start")) in (int,float)
                and type(e.get("t")) in (int,float)
                and math.isfinite(e["start"]) and math.isfinite(e["t"])
                and 0<=e["start"]<=e["t"]<=75]
    rows=manifest.get("editorial_events",[])
    if not isinstance(rows,list):return []
    clicks=[e for e in rows if isinstance(e,dict) and e.get("kind")=="click"
            and isinstance(e.get("semanticGoal"),str) and e["semanticGoal"].strip()
            and type(e.get("t")) in (int,float) and math.isfinite(e["t"])]
    outcomes=[e for e in rows if isinstance(e,dict) and
              e.get("kind")=="state_change" and
              isinstance(e.get("evidence"),str) and e["evidence"].strip()
              and isinstance(e.get("resultRect"),dict) and
              type(e.get("t")) in (int,float) and math.isfinite(e["t"])]
    result=[]
    for click in clicks:
        t=float(click["t"])
        after=next((e for e in outcomes if t<=e["t"]<=t+1.8),None)
        if after is not None:
            result.append((max(0,t-.15),min(75,float(after["t"])+.2)))
    return result

def verified_focal_geometry(focal:dict, size:tuple[int,int])->list[dict]:
    """Opt-in source-verified camera/DOM geometry rejection.

    This is a *narrow* compositional check for primary-object silent studies.
    It does not measure taste or general-product UI quality. A genuine DOM
    rectangle plus the compositor's 2x3 affine must be supplied; never infer
    an attractive made-up region from video pixels.
    """
    if not isinstance(focal,dict):
        raise ValueError("Missing source measured focal geometry")
    W,H=size
    expected={"source_rect":4,"source_size":2,"camera_matrix":2,"stage_window":4}
    for key,num in expected.items():
        if not isinstance(focal.get(key),list) or len(focal[key])!=num:
            raise ValueError("Malformed recorded camera geometry: "+key)
    values=[*focal["source_rect"],*focal["source_size"],*focal["stage_window"]]
    if not all(type(x) in (int,float) and math.isfinite(x) for x in values):
        raise ValueError("Nonfinite source geometry")
    sx,sy,sw,sh=focal["source_rect"]
    srcw,srch=focal["source_size"]
    wx,wy,ww,wh=focal["stage_window"]
    if not (min(sx,sy)>=0 and min(sw,sh)>=8 and
            sx+sw<=srcw and sy+sh<=srch and
            0<=wx<W and 0<=wy<H and ww>0 and wh>0 and
            wx+ww<=W and wy+wh<=H):
        raise ValueError("Source/stage rectangle outside verified frame")
    m=np.asarray(focal["camera_matrix"],dtype=np.float64)
    if m.shape!=(2,3) or not np.isfinite(m).all():
        raise ValueError("Invalid real camera matrix")
    def visible(rect):
        x,y,w,h=rect
        corners=np.array([[x,y,1],[x+w,y,1],[x,y+h,1],[x+w,y+h,1]],np.float64)
        projected=(m@corners.T).T
        x0,y0=np.min(projected,axis=0)
        x1,y1=np.max(projected,axis=0)
        area=max(0.,x1-x0)*max(0.,y1-y0)
        cx0=max(wx,x0);cy0=max(wy,y0)
        cx1=min(wx+ww,x1);cy1=min(wy+wh,y1)
        visible_area=max(0.,cx1-cx0)*max(0.,cy1-cy0)
        return (visible_area,visible_area/max(area,1e-9),
                [round(float(v),2) for v in (x0,y0,x1-x0,y1-y0)])
    area,in_frame,projected=visible((sx,sy,sw,sh))
    fraction=float(area/(W*H))
    findings=[]
    if fraction < .08:
        findings.append({"code":"SMALL_VERIFIED_PRIMARY_SUBJECT",
                         "detail":{"fraction_of_output":round(fraction,5),
                                   "projected_rect":projected,
                                   "threshold":.08}})
    if in_frame < .975:
        findings.append({"code":"FOCAL_TARGET_CLIPPED",
                         "detail":{"fraction_inside_screen":round(in_frame,5)}})
    texts=focal.get("protected_text",[])
    if not isinstance(texts,list) or len(texts)>64:
        raise ValueError("Invalid protected text evidence")
    for item in texts:
        if not isinstance(item,dict) or not isinstance(item.get("text"),str):
            raise ValueError("Invalid text source receipt")
        rect=item.get("rect")
        if not isinstance(rect,list) or len(rect)!=4 or any(
            type(v) not in (int,float) or not math.isfinite(v) for v in rect
        ):
            raise ValueError("Missing source-measured text rectangle")
        px,py,pw,ph=rect
        if min(px,py)<0 or min(pw,ph)<1 or px+pw>srcw or py+ph>srch:
            raise ValueError("Text evidence outside source")
        visible_area,ratio,_=visible(rect)
        if visible_area>0 and .025<ratio<.975:
            findings.append({"code":"PARTIALLY_CROPPED_SOURCE_TEXT",
                             "detail":{"text":item["text"][:80],
                                       "fraction_visible":round(ratio,5)}})
        # Only operator-selected *critical* text with a measured browser
        # font size is subject to the mobile readability heuristic.
        if "source_font_px" in item:
            font=item["source_font_px"]
            if (type(font) not in (int,float) or not math.isfinite(font)
                or not 4<=font<=250):
                raise ValueError("Invalid measured source font size")
            native_scale=float(np.sqrt(abs(np.linalg.det(m[:,:2]))))
            mobile_px=float(font*native_scale*390/W)
            if ratio>=.975 and mobile_px<8.5:
                findings.append({"code":"UNREADABLE_CRITICAL_TEXT_AT_390PX",
                                 "detail":{"text":item["text"][:80],
                                           "mobile_font_px":round(mobile_px,2),
                                           "threshold_px":8.5}})
    return findings


def verified_focal_sequence(sequence:dict,size:tuple[int,int])->list[dict]:
    """Review *all supplied source-timed* camera samples, not a cherry-picked still.

    Safe as an opt-in before/after-encode measurement, without altering camera
    paths or moving browser events. Only contiguous frame-indexed sequences
    are admitted as full-sequence evidence. Never claims the film is beautiful.
    """
    if not isinstance(sequence,dict) or not isinstance(sequence.get("base"),dict):
        raise ValueError("Missing source-measured sequence base")
    frames=sequence.get("frames")
    if not isinstance(frames,list) or not 1<=len(frames)<=900:
        raise ValueError("Full geometry sequence requires 1..900 camera frames")
    if not isinstance(frames[0],dict) or frames[0].get("frame")!=0 or any(
        not isinstance(frame,dict) or type(frame.get("frame")) is not int
        or frame["frame"]!=idx for idx,frame in enumerate(frames)
    ):
        raise ValueError("Camera geometry sequence must be contiguous from frame zero")
    rollup={}
    source_texts=sequence["base"].get("protected_text",[])
    if not isinstance(source_texts,list):
        raise ValueError("Missing real text visibility evidence")
    for item in source_texts:
        if not isinstance(item,dict):
            raise ValueError("Invalid time-scoped source text evidence")
        for name in ("start_frame","end_frame"):
            if name in item and (type(item[name]) is not int
                or not 0<=item[name]<=len(frames)):
                raise ValueError("Invalid real text visibility clock")
        if item.get("end_frame",len(frames))<item.get("start_frame",0):
            raise ValueError("Reversed source text visibility")
    for entry in frames:
        active_text=[
            {key:value for key,value in item.items()
             if key not in ("start_frame","end_frame")}
            for item in source_texts
            if item.get("start_frame",0)<=entry["frame"]<
               item.get("end_frame",len(frames))]
        payload={**sequence["base"],"camera_matrix":entry.get("camera_matrix"),
                 "protected_text":active_text}
        for finding in verified_focal_geometry(payload,size):
            code=finding["code"]
            current=rollup.setdefault(code,{
                "code":code,"detail":{"first_frame":entry["frame"],
                                      "affected_frames":0,
                                      "first_evidence":finding["detail"]}})
            current["detail"]["affected_frames"]+=1
    return list(rollup.values())


def analyze(path, evidence=None, seconds=15):
    info=probe(path); video=next(s for s in info["streams"] if s["codec_type"]=="video")
    duration=float(info["format"]["duration"])
    a=frames(path,min(duration,seconds))
    if len(a)<5: raise ValueError("insufficient decodable video")
    diffs=np.abs(np.diff(a,axis=0)).mean(axis=(1,2))
    std=a.std(axis=(1,2)); means=a.mean(axis=(1,2))
    opener=diffs[:min(19,len(diffs))]
    findings=[]
    def issue(code,details): findings.append({"code":code,"detail":details})
    if len(opener)>=10 and np.percentile(opener,80)<1.3: issue("STATIC_OPENING_2S",{"p80_frame_delta":round(float(np.percentile(opener,80)),3)})
    if np.mean((means>185)&(std<30))>.35: issue("WASHED_OUT_FRAMES",{"fraction":round(float(np.mean((means>185)&(std<30))),3)})
    # A theme switch or newly displayed panel can legitimately change
    # thousands of original browser pixels IN ONE SOURCE FRAME. This is
    # not a composited editorial cut. Suppress only abrupt candidates that
    # match SHA256-verified source video changes at recorded source-event
    # times, within one QA sample frame. Any unverified/new editorial
    # discontinuity still fails closed.
    source_relative_transitions=[]
    abrupt_indices=np.where(diffs>62)[0]
    unverified_abrupt=list(abrupt_indices)
    ev=evidence if isinstance(evidence,dict) else {}
    if len(abrupt_indices) and ev.get("source_sha256") and ev.get("event_manifest_sha256"):
        original=Path(ev.get("source_path",""))
        original_manifest=Path(ev.get("event_manifest_path",""))
        if (original.is_file() and original_manifest.is_file()
                and digest(original)==ev["source_sha256"]
                and digest(original_manifest)==ev["event_manifest_sha256"]):
            try:
                manifest=json.loads(original_manifest.read_text())
                windows=_source_event_windows(manifest)
                source_trim=ev.get("source_trim_seconds",0.)
                if (type(source_trim) not in (int,float) or
                    not math.isfinite(source_trim) or
                    source_trim<0 or source_trim>75):
                    raise ValueError("Invalid original-source trim for film QA")
                original_frames=frames(original,min(duration,seconds),start=source_trim)
                original_diff=np.abs(np.diff(original_frames,axis=0)).mean(axis=(1,2))
                unverified_abrupt=[]
                for ix in abrupt_indices:
                    film_t=float(ix+1)/10
                    t=film_t+source_trim
                    close=any(begin<=t<=end for begin,end in windows)
                    matching=original_diff[max(0,ix-1):min(len(original_diff),ix+2)]
                    peak=float(max(matching,default=0))
                    if close and peak>=62 and float(diffs[ix])<=peak*1.25:
                        source_relative_transitions.append({
                           "actualSourceTime":round(t,3),
                           "filmSampleTime":round(film_t,3),
                           "sourceFrameDifference":round(peak,3),
                           "filmFrameDifference":round(float(diffs[ix]),3),
                           "verifiedRealUiTransition":True})
                    else:unverified_abrupt.append(int(ix))
            except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError):
                unverified_abrupt=list(abrupt_indices)
                source_relative_transitions=[]
    if unverified_abrupt:
        issue("ABRUPT_CUT_CANDIDATE",
              {"max_frame_delta":round(float(max(diffs[i] for i in unverified_abrupt)),2),
               "unmatchedSamples":len(unverified_abrupt)})
    if np.mean(diffs<.35)>.55: issue("REPEATED_OR_STATIC_FRAMES",{"fraction":round(float(np.mean(diffs<.35)),3)})
    # A naturally dark genuine source interface must not be treated as a
    # broken film merely because its gray standard deviation is <24. Compare
    # the encoded film to the separately SHA-verified actual source frames:
    # source-dark UI is not source damage. Still reject black/blank footage
    # and any plan that loses more than 15% of genuine source contrast.
    source_referenced_dark_ui=None
    if np.mean(std<24)>.5:
        ev=evidence if isinstance(evidence,dict) else {}
        original=Path(ev.get("source_path",""))
        if (ev.get("source_sha256") and original.is_file() and
                digest(original)==ev["source_sha256"]):
            src_frames=frames(original,min(seconds,duration))
            src_std=src_frames.std(axis=(1,2))
            src_means=src_frames.mean(axis=(1,2))
            baseline=float(np.median(src_std))
            actual=float(np.median(std))
            if (baseline<24 and float(np.median(src_means))<45
                    and baseline>=8 and actual>=max(8,baseline*.85)):
                source_referenced_dark_ui={
                    "verifiedSourceMedianGrayStd":round(baseline,3),
                    "filmMedianGrayStd":round(actual,3),
                    "sourceOriginalDarkUi":True,
                    "contrastPreservedFraction":round(actual/baseline,3)}
        if source_referenced_dark_ui is None:
            issue("LOW_VISUAL_DETAIL",
                  {"fraction":round(float(np.mean(std<24)),3)})
    audio=next((s for s in info["streams"] if s["codec_type"]=="audio"),None)
    if audio is None: issue("NO_AUDIO_STREAM",{})
    else:
        q=subprocess.run(["ffmpeg","-hide_banner","-nostats","-i",str(path),"-af","volumedetect","-f","null","-"],capture_output=True,text=True,timeout=90).stderr
        import re
        m=re.search(r"mean_volume: (-?\d+(?:\.\d+)?) dB",q)
        if "mean_volume: -inf" in q or (m and float(m.group(1)) < -58): issue("SILENT_OR_NEAR_SILENT_AUDIO",{"mean_db":float(m.group(1)) if m else None})
    ev=evidence if isinstance(evidence,dict) else {}
    if not ev.get("source_sha256") or not ev.get("source_path") or not ev.get("event_manifest_sha256"):
        issue("UNVERIFIED_SOURCE_CLAIM",{"required":["source_path","source_sha256","event_manifest_sha256"]})
    else:
        src=Path(ev["source_path"])
        if not src.is_file() or digest(src)!=ev["source_sha256"]: issue("SOURCE_HASH_MISMATCH",{})
        manifest=Path(ev.get("event_manifest_path",""))
        if not manifest.is_file() or digest(manifest)!=ev["event_manifest_sha256"]: issue("EVENT_MANIFEST_HASH_MISMATCH",{})
    if ev.get("focus_box"):
        b=ev["focus_box"]
        if b.get("width",0)*b.get("height",0) < .04*video["width"]*video["height"]: issue("SMALL_FOCAL_CONTENT",{"focus_box":b})
    if "verified_focal_geometry" in ev:
        for finding in verified_focal_geometry(
                ev["verified_focal_geometry"],(video["width"],video["height"])):
            findings.append(finding)
    if "verified_focal_sequence" in ev:
        findings.extend(verified_focal_sequence(
            ev["verified_focal_sequence"],(video["width"],video["height"])))
    return {"schema":"sauce-film-quality-v1","film":str(path),"film_sha256":digest(path),"duration":duration,"video_dimensions":[video["width"],video["height"]],"sampled_frames":len(a),  "sample_fps":10,"sourceRelativeRealUiTransitions":source_relative_transitions,
            "sourceRelativeDarkUiEvidence":source_referenced_dark_ui,
            "findings":findings,"verdict":"REJECT" if findings else "HUMAN_REVIEW_REQUIRED"}

def repair_edl(edit,manifest,report):
    """Only shorten a proven event-free static first shot, never remove real events."""
    codes={x["code"] for x in report["findings"]}
    if "STATIC_OPENING_2S" not in codes: return None
    import copy
    e=copy.deepcopy(edit); shots=e.get("shots",[])
    if len(shots)<3: return None
    first=shots[0]; keys=first.get("camera",[])
    if len(keys)!=1 or keys[0].get("f")!=0: return None
    old=first["startFrame"]; end=first["endFrame"]
    cut=min(90,end-old-13)
    if cut<30: return None
    # An event is never trimmed; absence of an event manifest fails closed.
    events=manifest.get("events")
    if not isinstance(events,list) or not events: return None
    lead=float(manifest.get("lead_s",0))
    for event in events:
        if not isinstance(event,dict) or not isinstance(event.get("t"),(int,float)): return None
        frame=round((event["t"]+lead)*60)
        if old<=frame<old+cut: return None
    first["startFrame"]=old+cut
    e.setdefault("qualityRepair",[]).append({"op":"shorten_verified_idle_opener","removed_source_frames":[old,old+cut],"source_events_preserved":True})
    return e

def supervise(video, manifest_path, edl_path, source_path, output_dir, evidence_receipt, attempts=2, render=False):
    if attempts not in (0,1,2): raise ValueError("attempt budget must be 0..2")
    output_dir.mkdir(parents=True,exist_ok=True)
    manifest=json.loads(manifest_path.read_text()); edl=json.loads(edl_path.read_text())
    # Provenance must be supplied from an independent capture receipt, not
    # manufactured by calculating the current files' hashes on demand.
    evidence=json.loads(evidence_receipt.read_text())
    if evidence.get("source_sha256")!=digest(source_path) or evidence.get("event_manifest_sha256")!=digest(manifest_path):
        raise ValueError("Recorded source/manifest mismatch; cannot authorize repair")
    if Path(evidence.get("source_path","")).resolve()!=source_path.resolve():
        raise ValueError("Source path not bound to evidence receipt")
    if Path(evidence.get("event_manifest_path","")).resolve()!=manifest_path.resolve():
        raise ValueError("Manifest path not bound to evidence receipt")
    original=analyze(video,evidence)
    receipts=[{"attempt":0,"report":original}]
    before=original
    for attempt in range(1,attempts+1):
        updated=repair_edl(edl,manifest,before)
        if updated is None:
            receipts.append({"attempt":attempt,"status":"STOP_NO_SAFE_EDL_ADJUSTMENT"});break
        new_edl=output_dir/f"candidate-{attempt}.edl.json"
        new_edl.write_text(json.dumps(updated,indent=2))
        if not render:
            receipts.append({"attempt":attempt,"status":"EDL_PROPOSED_NOT_RENDERED","edl":str(new_edl)});break
        outfile=output_dir/f"candidate-{attempt}-excerpt.mp4"
        cmd=["python3","scripts/evidence_edl_renderer.py","--video",str(source_path),"--manifest",str(manifest_path),"--edl",str(new_edl),"--out",str(outfile),"--max-frames","240"]
        proc=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
        if proc.returncode:
            receipts.append({"attempt":attempt,"status":"RENDER_FAILED","stderr":proc.stderr[-1500:]});break
        after=analyze(outfile,evidence,seconds=4)
        prior={f["code"] for f in before["findings"]}
        now={f["code"] for f in after["findings"]}
        receipts.append({"attempt":attempt,"report":after,"edl":str(new_edl),"excerpt":str(outfile),"status":"HUMAN_REVIEW_REQUIRED" if "STATIC_OPENING_2S" not in now and not(now-prior) else "REJECT"})
        if receipts[-1]["status"]=="HUMAN_REVIEW_REQUIRED":break
        if after["film_sha256"]==before["film_sha256"]:break
        before=after;edl=updated
    receipt={"schema":"sauce-bounded-quality-v1","original_sha256":original["film_sha256"],"max_attempts":attempts,"attempts":receipts,"human_approval":False}
    (output_dir/"quality-receipt.json").write_text(json.dumps(receipt,indent=2))
    return receipt

def main():
    p=argparse.ArgumentParser()
    p.add_argument("video",type=Path);p.add_argument("--manifest",type=Path);p.add_argument("--edl",type=Path)
    p.add_argument("--source",type=Path);p.add_argument("--out-dir",type=Path);p.add_argument("--attempts",type=int,default=2)
    p.add_argument("--render",action="store_true")
    p.add_argument("--evidence-receipt",type=Path)
    a=p.parse_args()
    if any(x is None for x in (a.manifest,a.edl,a.source,a.out_dir,a.evidence_receipt)):
        print(json.dumps(analyze(a.video),indent=2))
    else: print(json.dumps(supervise(a.video,a.manifest,a.edl,a.source,a.out_dir,a.evidence_receipt,a.attempts,a.render),indent=2))
if __name__=="__main__":main()
