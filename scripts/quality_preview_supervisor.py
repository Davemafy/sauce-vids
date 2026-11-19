#!/usr/bin/env python3
"""Deterministic evidence-led film QA; no inference or compositor mutation."""
import argparse, hashlib, json, subprocess
from pathlib import Path
import numpy as np

def probe(path):
    return json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(path)]))

def digest(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()

def frames(path, seconds, fps=10):
    cmd=["ffmpeg","-v","error","-i",str(path),"-t",str(seconds),"-vf",f"fps={fps},scale=160:90,format=gray","-f","rawvideo","-"]
    data=subprocess.check_output(cmd,timeout=90)
    return np.frombuffer(data,dtype=np.uint8).reshape(-1,90,160).astype(np.int16)

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
    if np.any(diffs>62): issue("ABRUPT_CUT_CANDIDATE",{"max_frame_delta":round(float(max(diffs)),2)})
    if np.mean(diffs<.35)>.55: issue("REPEATED_OR_STATIC_FRAMES",{"fraction":round(float(np.mean(diffs<.35)),3)})
    if np.mean(std<24)>.5: issue("LOW_VISUAL_DETAIL",{"fraction":round(float(np.mean(std<24)),3)})
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
    return {"schema":"sauce-film-quality-v1","film":str(path),"film_sha256":digest(path),"duration":duration,"video_dimensions":[video["width"],video["height"]],"sampled_frames":len(a),"sample_fps":10,"findings":findings,"verdict":"REJECT" if findings else "HUMAN_REVIEW_REQUIRED"}

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
