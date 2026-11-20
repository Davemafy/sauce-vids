#!/usr/bin/env python3
"""Bounded unattended Sauce creative-direction runner for real verified source video.

The program is deliberately small: prepare source-hash-bound capabilities,
ask one Gemini model for film JSON, normalize only a documented mechanical
compatibility error, invoke the SAME strict renderer validator, optionally
make one model repair attempt, then render or reject. Never manual per-site
compositor code, fabricated UI, fallback fake click, or implicit approval.

This is a local/worker entry point and does not change the running pilot
backend. Model keys live exclusively in the invoking process environment.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.error import HTTPError,URLError
from urllib.request import Request,urlopen

from film_director_capabilities import build_contract
from studio_plan_bounded_repair import normalize_generated_studio_plan


RENDERER=Path(__file__).resolve().with_name("render_event_video.py")
MAX_SOURCE_BYTES=24*1024*1024
MAX_SOURCE_SECONDS=30
MAX_ATTEMPTS=2
MODELS_PREFIX="https://generativelanguage.googleapis.com/v1beta/models/"
TEMPERATURE=.70


def sha(path):
    dig=hashlib.sha256()
    with Path(path).open("rb") as inp:
        for block in iter(lambda:inp.read(1024*1024),b""):
            dig.update(block)
    return dig.hexdigest()


def safe_model_name(value):
    if not isinstance(value,str) or not value or len(value)>75 or not all(
       c.isalnum() or c in ("-", ".") for c in value):
        raise ValueError("Untrusted model identifier")
    return value


def _model_request(source,packet,model,key,feedback=None):
    """One network call. Never persist the API key, raw data or headers."""
    source=Path(source)
    if source.stat().st_size>MAX_SOURCE_BYTES:
        raise ValueError("Real source exceeds bounded vision request size")
    model=safe_model_name(model)
    prompt=(
        "You are a cinematic software-product film director. Direct a compelling "
        "short, source-true film from the attached genuine browser recording. "
        "The controls listed in the attached capability packet are real capabilities "
        "of the renderer, not instructions to use every effect. Return ONE exact "
        "sauce-film-plan-v1 JSON object. Do not invent product UI, cursor motions, "
        "buttons, time travel, overlays or fictional results. The visible real "
        "interaction must be clear, and the final verified product result must "
        "remain legible. Your output will be independently validated and rendered "
        "without any human fixes. Production quality requires strong first-second "
        "composition, ambitious but useful spatial staging, and readable payoff.\n"
        "REAL VERIFIED SOURCE + EXACT EXECUTABLE CONTRACT:\n"+
        json.dumps(packet,ensure_ascii=False,separators=(",",":"))
    )
    if feedback:
        prompt+=(
            "\nThe previous attempt failed the actual local validator. "
            "Retain the creative direction but resolve the following concrete "
            "errors. No imaginary capabilities or arbitrary textual excuses:\n"+
            feedback[:2600]
        )
    parts=[
        {"text":prompt},
        {"inline_data":{"mime_type":"video/mp4",
                        "data":base64.b64encode(source.read_bytes()).decode("ascii")}}
    ]
    payload={"contents":[{"role":"user","parts":parts}],
             "generationConfig":{"temperature":TEMPERATURE,
                                 "responseMimeType":"application/json",
                                 "maxOutputTokens":9000}}
    url=MODELS_PREFIX+model+":generateContent"
    req=Request(url,data=json.dumps(payload).encode(),method="POST",
                headers={"Content-Type":"application/json","x-goog-api-key":key})
    with urlopen(req,timeout=170) as response:
        body=json.load(response)
    candidate=(body.get("candidates") or [{}])[0]
    raw="".join(part.get("text","") for part in
                candidate.get("content",{}).get("parts",[]))
    return raw,{"model":model,"finishReason":candidate.get("finishReason"),
                "usageMetadata":body.get("usageMetadata",{}),
                "sourceSha256":packet["actualCapture"]["sourceSha256"]}


def _validate(source,manifest,plan,output_dir,timeout=120):
    log=output_dir/(plan.stem+"-validation.log")
    args=[sys.executable,str(RENDERER),"--video",str(source),"--manifest",str(manifest),
          "--film-plan",str(plan),"--validate-only"]
    try:
        result=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                              timeout=timeout,text=True,cwd=RENDERER.parents[1],check=False)
        message=result.stdout or ""
        log.write_text(message[-12000:])
        return result.returncode==0,message[-3500:]
    except subprocess.TimeoutExpired:
        log.write_text("Renderer validation timeout\n")
        return False,"Renderer validation timeout"


def run_unattended(source,manifest,brief,out,*,model,key,max_attempts=MAX_ATTEMPTS,
                   model_call=_model_request,validator=_validate,
                   render=True):
    """Run an evidence-first film job; returns private receipts and stage status.

    Output is fail-closed: cannot render until an actual renderer --validate-only
    pass. Does not infer meaning from a self-reported model confidence score.
    """
    if type(max_attempts) is not int or not 1<=max_attempts<=2:
        raise ValueError("Only one attempt and at most one bounded retry permitted")
    source=Path(source).resolve();manifest=Path(manifest).resolve();out=Path(out).resolve()
    if not source.is_file() or not manifest.is_file() or not source.suffix.lower()==".mp4":
        raise ValueError("A real local MP4 and sidecar are required")
    if not key:
        raise RuntimeError("Gemini credential unavailable; no invented fallback output")
    if source.stat().st_size>MAX_SOURCE_BYTES:
        raise ValueError("Source exceeds bounded model-video size")
    packet=build_contract(source,manifest,brief)
    if packet["actualCapture"]["durationSeconds"]>MAX_SOURCE_SECONDS:
        raise ValueError("A 30s max original source is required for bounded model direction")
    model=safe_model_name(model)
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise ValueError("Output must be a fresh empty private directory")
    out.mkdir(parents=True,exist_ok=True,mode=0o700)
    try:os.chmod(out,0o700)
    except OSError:pass
    (out/"source-packet.json").write_text(json.dumps(packet,indent=2)+"\n")
    result={"schema":"sauce-auto-director-receipt-v1",
            "sourceSha256":sha(source),"manifestSha256":sha(manifest),
            "model":model,"creativeApproved":False,"attempts":[],
            "outcome":"failed","rendered":False,
            "why":"pending first source-verified direction"}
    feedback=None
    for i in range(1,max_attempts+1):
        record={"attempt":i,"status":"pending"}
        result["attempts"].append(record)
        try:
            began=time.monotonic()
            raw,usage=model_call(source,packet,model,key,feedback)
            record.update(usage)
            record["modelSeconds"]=round(time.monotonic()-began,2)
            raw_path=out/f"model-{i}-raw.txt"
            raw_path.write_text(raw)
            plan=json.loads(raw)
            if not isinstance(plan,dict):
                raise ValueError("Model output was not one JSON object")
            if plan.get("sourceSha256")!=packet["actualCapture"]["sourceSha256"] or (
                plan.get("manifestSha256")!=packet["actualCapture"]["manifestSha256"]):
                raise ValueError("Model source/manifest hashes contradict actual capture")
            original=out/f"model-{i}-original.json"
            original.write_text(json.dumps(plan,indent=2)+"\n")
            amended,repair=normalize_generated_studio_plan(
                plan,manifest=json.loads(manifest.read_text()))
            normalized=out/f"model-{i}-normalized.json"
            normalized.write_text(json.dumps(amended,indent=2)+"\n")
            (out/f"model-{i}-mechanical-repair.json").write_text(
                json.dumps(repair,indent=2)+"\n")
            valid,detail=validator(source,manifest,normalized,out)
            record.update({"status":"validated" if valid else "validator_reject",
                           "validatorMessage":detail[-1700:],
                           "mechanicalChanges":repair["changes"]})
            if not valid:
                feedback=detail+"\nPrevious model JSON:\n"+raw[:4200]
                continue
            if render:
                film=out/"film.mp4"
                cmd=[sys.executable,str(RENDERER),"--video",str(source),
                     "--manifest",str(manifest),"--film-plan",str(normalized),
                     "--output",str(film)]
                done=subprocess.run(cmd,cwd=RENDERER.parents[1],
                                    stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                                    text=True,timeout=300,check=False)
                (out/"render.log").write_text((done.stdout or "")[-15000:])
                if done.returncode or not film.is_file():
                    raise RuntimeError("Validated plan failed final full-decode render")
                record["filmSha256"]=sha(film)
                result["filmSha256"]=record["filmSha256"]
                result["rendered"]=True
                # Reuse Sauce's EXISTING actual-encoded-frame + audio supervisor.
                # This is evidence-only QA, NOT a premium taste score.
                from quality_preview_supervisor import analyze
                evidence={"source_path":str(source),"source_sha256":sha(source),
                          "event_manifest_path":str(manifest),
                          "event_manifest_sha256":sha(manifest)}
                quality=analyze(film,evidence=evidence,
                                seconds=min(15.,packet["actualCapture"]["durationSeconds"]))
                (out/"encoded-visual-qa.json").write_text(json.dumps(quality,indent=2)+"\n")
                record["encodedVisualVerdict"]=quality["verdict"]
                record["encodedVisualFindings"]=[finding["code"]
                                                for finding in quality["findings"]]
                if quality["verdict"]=="REJECT":
                    record["status"]="rendered_objective_reject"
                    result["outcome"]="objective_reject"
                    result["why"]="Existing encoded-film supervisor rejected source-backed defects"
                else:
                    record["status"]="rendered_needs_visual_review"
                    result["outcome"]="needs_review"
            else:
                result["outcome"]="validated_not_rendered"
            if result["outcome"]!="objective_reject":
                result["why"]="source-verified JSON passed actual local renderer; creative approval pending"
            result["winningAttempt"]=i
            break
        except (HTTPError,URLError,TimeoutError,ValueError,TypeError,
                KeyError,IndexError,RuntimeError,subprocess.TimeoutExpired,OSError) as exc:
            record["status"]="error"
            record["errorType"]=type(exc).__name__
            record["error"]="Model/provider/renderer failed safely; see attempt receipt"
            feedback=("Previous attempt failed: "+type(exc).__name__+
                      ". Return complete valid JSON and preserve locked source hashes.")
        finally:
            (out/"unattended-receipt.json").write_text(json.dumps(result,indent=2)+"\n")
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--brief",required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--model",default=os.environ.get("SAUCE_DIRECTOR_MODEL","gemini-3-flash-preview"))
    p.add_argument("--max-attempts",type=int,default=2)
    a=p.parse_args()
    key=os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    r=run_unattended(a.source,a.manifest,a.brief,a.out,
          model=a.model,key=key,max_attempts=a.max_attempts)
    print(json.dumps({"outcome":r["outcome"],"rendered":r["rendered"],
        "attempts":len(r["attempts"]),"creativeApproved":False,
        "receipt":str(a.out/"unattended-receipt.json")}))
    if r["outcome"]!="needs_review":raise SystemExit(2)


if __name__=="__main__":
    main()
