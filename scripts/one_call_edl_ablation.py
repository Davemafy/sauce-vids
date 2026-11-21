#!/usr/bin/env python3
"""One Gemini API request for 2-3 source-locked edit alternatives. Research only."""
import argparse
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.error import HTTPError,URLError
from urllib.request import Request,urlopen
from auto_direct_studio_film import (
    MAX_SOURCE_BYTES,RENDERER,_validate,safe_model_name,sha)
from film_director_capabilities import build_contract
from studio_plan_bounded_repair import normalize_generated_studio_plan
from source_director_preflight import preflight_source_edit

SCHEMA="sauce-single-call-variants-v1"


def request_once(source,packet,model,key):
    """Exactly one generateContent call; no retry, tool loop or hallucinated fallback."""
    source=Path(source)
    if source.stat().st_size>MAX_SOURCE_BYTES:
        raise ValueError("Source too large for bounded model direction")
    prompt=(
      "You are editing a premium software product demonstration. Output ONE JSON "
      "object containing TWO or THREE distinct executable Sauce film plans for the "
      "SAME authentic captured product footage. Return strict JSON shaped "
      '{"schema":"sauce-single-call-variants-v1","selected":"tight","variants":'
      '[{"id":"tight","filmPlan":{FULL sauce-film-plan-v1 JSON}},'
      '{"id":"readable","filmPlan":{FULL sauce-film-plan-v1 JSON}}]}. '
      "Select your preferred variant. Choose different camera shot rhythms and "
      "legible result holds, not arbitrary duration changes. Use ONLY real source "
      "actions, original pointer and verified result geometry. Never invent UI, "
      "success states, timestamps, media hashes, selectors or evidence. All real "
      "results and action Foley must remain in the source timeline. "
      "An actual local validator will reject unverified content. "
      "ACTUAL ENGINE SCHEMA AND SOURCE PACKET:\n"+
      json.dumps(packet,separators=(",",":"),ensure_ascii=False))
    payload={"contents":[{"role":"user","parts":[{"text":prompt},
      {"inline_data":{"mime_type":"video/mp4",
        "data":base64.b64encode(source.read_bytes()).decode("ascii")}}]}],
      "generationConfig":{"temperature":.55,"responseMimeType":"application/json",
                           "maxOutputTokens":16000}}
    request=Request("https://generativelanguage.googleapis.com/v1beta/models/"+
      safe_model_name(model)+":generateContent",
      data=json.dumps(payload).encode(),method="POST",
      headers={"Content-Type":"application/json","X-goog-api-key":key})
    with urlopen(request,timeout=180) as response:
        response=json.load(response)
    c=(response.get("candidates") or [{}])[0]
    raw="".join(p.get("text","") for p in c.get("content",{}).get("parts",[]))
    return raw,{"usageMetadata":response.get("usageMetadata",{}),
                "finishReason":c.get("finishReason")}


def check_variants(data,packet):
    if not isinstance(data,dict) or set(data)!={"schema","selected","variants"} or data["schema"]!=SCHEMA:
        raise ValueError("Invalid single-response envelope")
    variants=data["variants"]
    if not isinstance(variants,list) or not 2<=len(variants)<=3:
        raise ValueError("Expected 2-3 contrasting edits")
    seen=set()
    for v in variants:
        if not isinstance(v,dict) or set(v)!={"id","filmPlan"}:
            raise ValueError("Malformed edit variant")
        name=v["id"]
        if not isinstance(name,str) or not 1<=len(name)<=25 or not all(
            c.isalnum() or c in "_-" for c in name) or name in seen:
            raise ValueError("Unsafe or duplicate variant ID")
        seen.add(name)
        p=v["filmPlan"]
        if not isinstance(p,dict) or p.get("schema")!="sauce-film-plan-v1" or (
            p.get("sourceSha256")!=packet["actualCapture"]["sourceSha256"] or
            p.get("manifestSha256")!=packet["actualCapture"]["manifestSha256"]):
            raise ValueError("Missing or forged source/manifest identity")
    if data["selected"] not in seen:
        raise ValueError("Selected variant is missing")
    return variants



def run(source,manifest,brief,out,*,model,key,
        model_call=request_once,validator=_validate,render=False):
    source=Path(source).resolve();manifest=Path(manifest).resolve();out=Path(out).resolve()
    if not source.is_file() or not manifest.is_file():
        raise ValueError("Real original video and verified manifest are mandatory")
    if not key:
        raise ValueError("Existing configured Gemini key is absent")
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise ValueError("Refuse overwrite of other research artifacts")
    packet=build_contract(source,manifest,brief)
    out.mkdir(parents=True,exist_ok=True,mode=0o700)
    receipt={"schema":"sauce-one-call-ablation-receipt-v1",
             "sourceSha256":sha(source),"manifestSha256":sha(manifest),
             "model":model,"apiCalls":0,"status":"pending",
             "modelSelected":None,"selected":None,
             "variants":[],"rendered":[],"creativeApproved":False}
    try:
        receipt["apiCalls"]=1
        raw,usage=model_call(source,packet,model,key)
        receipt["usage"]=usage
        (out/"one-model-response.json").write_text(raw)
        data=json.loads(raw)
        variants=check_variants(data,packet)
        receipt["modelSelected"]=data["selected"]
        truth=json.loads(manifest.read_text())
        fps=packet["actualCapture"]["nativeFps"]
        size=tuple(packet["actualCapture"]["resolution"])
        valid=[]
        for item in variants:
            name=item["id"]
            result={"id":name,"status":"rejected"}
            receipt["variants"].append(result)
            try:
                normalized,repair=normalize_generated_studio_plan(
                    item["filmPlan"],manifest=truth,
                    source_path=source,source_size=size,fps=fps,
                    manifest_path=manifest)
                path=out/(name+"-normalized.json")
                path.write_text(json.dumps(normalized,indent=2)+"\n")
                (out/(name+"-repair.json")).write_text(json.dumps(repair,indent=2)+"\n")
                okay,detail=validator(source,manifest,path,out)
                if not okay:
                    result.update(status="renderer_reject",detail=detail[-1200:])
                    continue
                preflight=preflight_source_edit(normalized,truth,source,size,fps,
                    audio_required=True,manifest_path=manifest)
                if preflight["findings"]:
                    result.update(status="preflight_reject",
                        findings=[r["code"] for r in preflight["findings"]])
                    continue
                result["status"]="validated"
                valid.append(name)
                if render:
                    film=out/(name+".mp4")
                    done=subprocess.run([sys.executable,str(RENDERER),
                        "--video",str(source),"--manifest",str(manifest),
                        "--film-plan",str(path),"--output",str(film)],
                        capture_output=True,text=True,timeout=350,check=False)
                    (out/(name+"-render.log")).write_text(
                        (done.stdout+done.stderr)[-14000:])
                    if done.returncode or not film.is_file():
                        result["status"]="render_failed"
                        continue
                    from quality_preview_supervisor import analyze
                    qa=analyze(film,evidence={
                        "source_path":str(source),"source_sha256":sha(source),
                        "event_manifest_path":str(manifest),
                        "event_manifest_sha256":sha(manifest)},
                        seconds=min(15,packet["actualCapture"]["durationSeconds"]))
                    (out/(name+"-qa.json")).write_text(json.dumps(qa,indent=2)+"\n")
                    result["filmSha256"]=sha(film)
                    result["qualityVerdict"]=qa["verdict"]
                    result["status"]=("rendered_objective_reject"
                        if qa["verdict"]=="REJECT" else "rendered_needs_review")
                    if qa["verdict"]!="REJECT":
                        receipt["rendered"].append(name)
            except (ValueError,RuntimeError,TypeError,KeyError,
                    subprocess.SubprocessError,OSError) as e:
                result.update(status="validation_error",errorType=type(e).__name__)
        eligible=receipt["rendered"] if render else valid
        if eligible:
            receipt["selected"]=(data["selected"] if data["selected"] in eligible
                                  else eligible[0])
            receipt["status"]=("needs_human_review" if render
                                else "validated_not_rendered")
        else:
            receipt["status"]="all_variants_rejected"
    except HTTPError as e:
        receipt.update(status="provider_unavailable",providerHttpStatus=int(e.code))
    except (URLError,TimeoutError,OSError) as e:
        receipt.update(status="provider_unavailable",errorType=type(e).__name__)
    except (ValueError,TypeError,KeyError,json.JSONDecodeError) as e:
        receipt.update(status="invalid_response",errorType=type(e).__name__)
    finally:
        (out/"one-call-receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",required=True,type=Path)
    p.add_argument("--manifest",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--brief",required=True)
    p.add_argument("--model",default="gemini-3.7-flash")
    p.add_argument("--render",action="store_true")
    a=p.parse_args()
    key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    r=run(a.source,a.manifest,a.brief,a.out,model=a.model,key=key,
          render=a.render)
    print(json.dumps({"status":r["status"],"apiCalls":r["apiCalls"],
                      "selected":r["selected"],"rendered":r["rendered"]}))
    if r["status"] not in ("needs_human_review","validated_not_rendered"):
        raise SystemExit(2)


if __name__=="__main__":
    main()
