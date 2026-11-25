"""Build a private-evidence-based diagnostic corpus. NOT premium few-shot data.

Only hashes, existing QA codes and controlled scalar metrics leave the worker.
No user prompts, private URLs, source pixels, captures or unlicensed media.
"""
import argparse
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

SHA=re.compile(r"^[a-f0-9]{64}$")
CODE=re.compile(r"^[A-Z][A-Z0-9_]{1,90}$")
VALID={"REJECT","HUMAN_REVIEW_REQUIRED","PASS"}
FAMILY={"STATIC_OPENING_2S":"story_pacing",
        "REPEATED_OR_STATIC_FRAMES":"story_pacing",
        "SMALL_FOCAL_CONTENT":"readability",
        "WASHED_OUT_FRAMES":"readability",
        "NO_AUDIO_STREAM":"sound",
        "TRANSIENT_FRAME_REVERSION":"capture_integrity",
        "TERMINAL_BROWSER_BLACKOUT":"capture_integrity"}
METRICS={"fraction","p80_frame_delta","onset_frame","restored_frame",
         "onset_seconds","duration_ms","source_to_blink_delta",
         "return_to_source_delta"}

def file_sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for part in iter(lambda:f.read(1024*1024),b""):h.update(part)
    return h.hexdigest()

def as_json(path):
    if not path.is_file() or path.stat().st_size>500000:return {}
    try:
        obj=json.loads(path.read_text())
        return obj if isinstance(obj,dict) else {}
    except (ValueError,UnicodeError,OSError):return {}

def is_sha(v):return isinstance(v,str) and SHA.fullmatch(v) is not None

def qa_findings(raw):
    if not isinstance(raw,list):return []
    cleaned=[]
    for f in raw:
        if not isinstance(f,dict) or not isinstance(f.get("code"),str) or not CODE.fullmatch(f["code"]):
            continue
        d=f.get("detail")
        d=d if isinstance(d,dict) else {}
        metrics={k:d[k] for k in sorted(METRICS.intersection(d)) if type(d[k]) in (int,float) and math.isfinite(d[k])}
        cleaned.append({"code":f["code"],"family":FAMILY.get(f["code"],"unclassified"),
                        "numeric_evidence":metrics})
    return cleaned

PUBLIC_REVIEW_ORIGINS=frozenset((
    "https://tweakcn.com/","https://tweakcn.com/editor/theme",
    "https://mantine.dev/core/modal/",
    "https://reactflow.dev/examples/interaction/drag-and-drop",
))

def curated_workflow(value):
    """Only curator-provided, previously documented PUBLIC feature labels."""
    if value is None:return None
    if not isinstance(value,dict) or set(value)-{
        "submitted_url","entry_url","actions","verified_result_seconds",
        "gemini_successful_calls","camera_plan_source"}:
        raise ValueError("Unknown curated workflow field")
    urls={}
    for k in ("submitted_url","entry_url"):
        if k in value:
            if value[k] not in PUBLIC_REVIEW_ORIGINS:
                raise ValueError("Refuse unknown potentially private URL in public corpus")
            urls[k]=value[k]
    actions=value.get("actions",[])
    if (not isinstance(actions,list) or len(actions)>10 or
            any(not isinstance(a,str) or len(a)>70 or
                not re.fullmatch(r"[a-zA-Z0-9 .+&/-]{1,70}",a)
                for a in actions)):
        raise ValueError("Unsafe or unknown public action label")
    times=value.get("verified_result_seconds",[])
    if (not isinstance(times,list) or len(times)>10 or
            any(type(t) not in (float,int) or not 0<=t<=180 for t in times)):
        raise ValueError("Unsafe result time")
    if times and len(times)!=len(actions):raise ValueError("Source action/time mismatch")
    calls=value.get("gemini_successful_calls")
    if calls is not None and (type(calls) is not int or not 0<=calls<=20):
        raise ValueError("Invalid model call count")
    camera=value.get("camera_plan_source")
    if camera is not None and camera not in ("deterministic_film_json","unknown"):
        raise ValueError("Unverified camera model attribution")
    return {**urls,"actions":actions,
            "verified_result_seconds":times,
            "gemini_successful_calls":calls,"camera_plan_source":camera}


def safe_camera_plan(job,release,source_sha):
    """Export only numeric source-pinned camera grammar, never the source UI."""
    claimed=release.get("plan_sha256")
    path=job/"private/customer-story/film-plan.json"
    if not is_sha(claimed) or not path.is_file():return None
    if file_sha(path)!=claimed:return {"hash_check":"sha_mismatch"}
    plan=as_json(path)
    if (plan.get("schema")!="sauce-film-plan-v1" or
        source_sha is None or plan.get("sourceSha256")!=source_sha):
        return {"hash_check":"contract_mismatch"}
    stage=plan.get("studioStage",{})
    if not isinstance(stage,dict):return {"hash_check":"invalid_plan"}
    keys=stage.get("camera")
    if not isinstance(keys,list) or len(keys)>70:return {"hash_check":"invalid_plan"}
    safe=[]
    for key in keys:
        if not isinstance(key,dict):return {"hash_check":"invalid_plan"}
        k={}
        for field in ("at","startAt","scale","viewScale"):
            if field in key:
                if type(key[field]) not in (float,int) or not 0<=key[field]<=200:
                    return {"hash_check":"invalid_plan"}
                k[field]=key[field]
        if "center" in key:
            center=key["center"]
            if not isinstance(center,list) or len(center)!=2 or any(
                type(n) not in (float,int) or not 0<=n<=1 for n in center):
                return {"hash_check":"invalid_plan"}
            k["center"]=center
        safe.append(k)
    return {"hash_check":"sha_match","camera_keyframes":safe,
            "stage_type":"whole_window_source_bound"}


def build(roots,annotations):
    for name,root in roots.items():
        if not name.isidentifier() or not Path(root).is_dir():raise ValueError("Explicit root required")
    collected=[];locator={}
    for name,root in sorted(roots.items()):
        root=Path(root).resolve()
        for video in sorted(root.rglob("master-1080p60.mp4")):
            if video.is_symlink() or not video.resolve().is_relative_to(root) or video.stat().st_size<1024:
                continue
            sha=file_sha(video)
            job=video.parent.parent
            quality_file=job/"export/encoded-quality.json"
            if not quality_file.is_file():quality_file=job/"encoded-quality.json"
            q=as_json(quality_file)
            rel=as_json(job/"export/release.json")
            qa_sha=q.get("film_sha256")
            binding=("sha_match" if qa_sha==sha else
                     "sha_mismatch" if is_sha(qa_sha) else
                     "unbound" if q else "missing")
            # A missing report film hash is *not* a trustworthy QA binding.
            verdict=q.get("verdict") if binding=="sha_match" else None
            if verdict not in VALID:verdict=None
            source_sha=rel.get("source_sha256")
            if not is_sha(source_sha):source_sha=None
            source_check="not_checked"
            if source_sha:
                candidates=[job/"private/customer-story/native/source.mp4",
                            job/"private/motion/continuous-source.mp4",
                            job/"private/motion/continuous-source.webm"]
                located=next((p for p in candidates if p.is_file()),None)
                if located:source_check=("sha_match" if file_sha(located)==source_sha else "sha_mismatch")
            release_sha=rel.get("film_sha256")
            rel_match=("sha_match" if release_sha==sha else
                       "sha_mismatch" if is_sha(release_sha) else "not_claimed")
            duration=q.get("duration")
            if type(duration) not in (int,float) or not 0<duration<3600:duration=None
            actions=rel.get("observed_actions")
            if type(actions) is not int or not 0<=actions<=100:actions=None
            row={"id":"film-"+sha[:20],"film_sha256":sha,
                 "quality":{"machine_verdict":verdict,"human_premium_label":"unreviewed",
                            "premium_reference_eligible":False,
                            "findings":qa_findings(q.get("findings")) if verdict else []},
                 "media":{"duration_seconds_from_qa":duration,
                          "observed_action_count_from_release":actions},
                 "evidence":{"qa_report_sha256":file_sha(quality_file) if q else None,
                             "qa_binding":binding,"release_film_binding":rel_match,
                             "source_sha256_claim":source_sha,"source_sha_check":source_check,
                             "plan_sha256_claim":rel.get("plan_sha256") if is_sha(rel.get("plan_sha256")) else None}}
            camera=safe_camera_plan(job,rel,source_sha)
            if camera is not None:row["safe_camera_plan"]=camera
            collected.append(row)
            locator.setdefault(row["id"],[]).append({"root":name,"path":video.relative_to(root).as_posix()})
    found={}
    for row in collected:found.setdefault(row["film_sha256"],row)
    missed=0
    for review in annotations:
        if (not isinstance(review,dict) or not is_sha(review.get("film_sha256")) or
            review.get("label") not in ("creative_reject","unapproved_research") or
            review.get("evidence_document")!="docs/SAUCE_HANDOFF.md" or
            not isinstance(review.get("defects"),list) or
            any(not isinstance(x,str) or not CODE.fullmatch(x) for x in review["defects"])):
            raise ValueError("Curated reviews need exact SHA, controlled defects and handoff evidence")
        target=found.get(review["film_sha256"])
        if target is None:missed+=1;continue
        if target["quality"]["human_premium_label"]!="unreviewed":raise ValueError("Duplicate human review")
        workflow=curated_workflow(review.get("workflow"))
        target["quality"].update(human_premium_label=review["label"],
                                 human_defects=review["defects"],
                                 evidence_document=review["evidence_document"])
        if workflow is not None:target["curated_public_workflow"]=workflow
    rows=sorted(found.values(),key=lambda x:x["film_sha256"])
    summary={"inventoried_binary_files":len(collected),"unique_film_binaries":len(rows),
             "duplicate_files":len(collected)-len(rows),
             "machine_qa_reports":sum(x["quality"]["machine_verdict"] is not None for x in rows),
             "machine_rejected":sum(x["quality"]["machine_verdict"]=="REJECT" for x in rows),
             "machine_qa_missing_or_untrusted":sum(x["quality"]["machine_verdict"] is None for x in rows),
             "curated_creative_rejections":sum(x["quality"]["human_premium_label"]=="creative_reject" for x in rows),
             "curated_reviews_missing_binary":missed,"premium_approved":0}
    return {"schema":"sauce-quality-diagnostics-v1","as_of_utc":"2026-11-25",
            "policy":{"purpose":"audit_negative_examples_not_few_shot",
                      "all_reference_admissions_forbidden":True,
                      "requires_human_creative_signoff":True,
                      "raw_frames_prompts_private_paths_included":False},
            "summary":summary,"cases":rows},locator

REJECTION_CODES={
    "No substantial settled visible product transformation":"WEAK_VISUAL_OUTCOME",
    "Tab not selected":"REPLAY_STATE_MISMATCH",
    "Unexpected initial public URL":"NAVIGATION_MISMATCH",
    "No valid model-authored connected story":"INVALID_MODEL_STORY",
    "No verified story after bounded evidence-led replanning":"STORY_REPLAN_EXHAUSTED",
    "Insufficient final source hold":"INSUFFICIENT_FINAL_HOLD",
    "No verified story within bounded recovery budget":"STORY_REPLAN_EXHAUSTED",
    "No verified story after bounded recovery":"STORY_REPLAN_EXHAUSTED",
}

def build_failed_attempts(roots):
    """Only typed, private, pre-render JSON rejection receipts, never log text."""
    rows=[]
    for name,root in sorted(roots.items()):
        root=Path(root).resolve()
        for path in sorted(root.rglob("rejection.json")):
            if path.is_symlink() or not path.resolve().is_relative_to(root):continue
            raw=as_json(path)
            reason=raw.get("reason")
            if not isinstance(reason,str):continue
            code=REJECTION_CODES.get(reason,"UNCLASSIFIED_REJECTION")
            h=file_sha(path)
            num=raw.get("index")
            delta=raw.get("observedDelta")
            if type(num) is not int or not 0<=num<30:num=None
            if type(delta) not in (int,float) or not 0<=delta<=1:delta=None
            rows.append({"id":"rejection-"+h[:20],
                         "rejection_receipt_sha256":h,
                         "reason_code":code,
                         "phase":"before_finished_film",
                         "failed_action_index":num,
                         "observed_pixel_delta":delta,
                         "human_review":"unreviewed",
                         "premium_reference_eligible":False})
    rows.sort(key=lambda x:x["rejection_receipt_sha256"])
    return {"schema":"sauce-pre-film-rejections-v1",
            "policy":{"purpose":"diagnostic_not_training",
                      "raw_reasons_browser_data_prompt_content_exported":False},
            "summary":{"receipts":len(rows),
                       "unclassified_reasons":sum(x["reason_code"]=="UNCLASSIFIED_REJECTION" for x in rows)},
            "cases":rows}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root",action="append",required=True,metavar="NAME=PATH")
    ap.add_argument("--annotations",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--private-index",type=Path,required=True)
    ap.add_argument("--attempts-output",type=Path)
    a=ap.parse_args();roots={}
    for item in a.root:
        if "=" not in item:ap.error("root format NAME=PATH")
        name,path=item.split("=",1)
        if name in roots:ap.error("duplicate root")
        roots[name]=Path(path)
    reviews=json.loads(a.annotations.read_text())
    if not isinstance(reviews,list):ap.error("annotations must be array")
    result,index=build(roots,reviews)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.private_index.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    a.private_index.parent.chmod(0o700)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    a.private_index.write_text(json.dumps(index,indent=2,sort_keys=True)+"\n")
    a.private_index.chmod(0o600)
    if a.attempts_output:
        attempt_data=build_failed_attempts(roots)
        a.attempts_output.parent.mkdir(parents=True,exist_ok=True)
        a.attempts_output.write_text(json.dumps(attempt_data,indent=2,sort_keys=True)+"\n")
        print("PRE_FILM",json.dumps(attempt_data["summary"],sort_keys=True))
    print("FILMS",json.dumps(result["summary"],sort_keys=True))

if __name__=="__main__":main()
