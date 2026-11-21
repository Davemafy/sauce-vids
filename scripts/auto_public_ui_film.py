#!/usr/bin/env python3
"""Experimental ONE public URL -> genuine action discovery -> 60fps source -> film.

Narrow automatic action scope: anonymous, public, reversible ARIA preview tabs.
No generic clicks, payment, authenticated controls, form edits, uploads, or
invented screenshots. Safe egress requires a real OS-level egress-filtered
container before exposing this to untrusted users. Owner-approved CLI only.

Each stage stores source-bound private evidence. On inference quota failure,
the actual source and event sidecar remain; no fallback fake film or auto
publication. A validated MP4 is always HUMAN_REVIEW_REQUIRED, never gold.
"""
from __future__ import annotations
import argparse,json,os,sys
from pathlib import Path
from urllib.parse import urlsplit

from capture_safety import validate_public_url
from source_truth_tab_capture import discover,record
from verified_public_tab_receipt import normalize
from film_director_capabilities import build_contract


def run(url:str,allowed_host:str,out:Path,*,seconds:float=16.,
        from_capture:Path|None=None,capture_only:bool=False,
        model:str="gemini-3-flash-preview",max_attempts:int=3,
        reference_videos:tuple[Path,...]=(),key:str|None=None,
        client_brief:str|None=None)->dict:
    validate_public_url(url)
    if urlsplit(url).hostname!=allowed_host:
        raise ValueError("One explicitly allowed public host must match the requested URL")
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise ValueError("New output must be empty; do not overwrite source or prior model receipts")
    out.mkdir(parents=True,exist_ok=True,mode=0o700)
    try:os.chmod(out,0o700)
    except OSError:pass
    if from_capture is None:
        proof=discover(url,allowed_host)
        capture_dir=out/"capture"
        recording=record(url,proof,capture_dir,duration=seconds)
        source=Path(recording["source"]).resolve()
        source_receipt=Path(recording["receipt"]).resolve()
        discovery_file=(capture_dir/"discovery.json").resolve()
    else:
        capture_dir=Path(from_capture).resolve()
        source=(capture_dir/"source-real-dpr2-60.mp4").resolve()
        source_receipt=(capture_dir/"source-events.json").resolve()
        discovery_file=(capture_dir/"discovery.json").resolve()
        if not all(x.is_file() for x in (source,source_receipt,discovery_file)):
            raise ValueError("Missing previous genuine browser source/receipt/discovery")
        proof=json.loads(discovery_file.read_text())
        if proof.get("url")!=url or proof.get("host")!=allowed_host:
            raise ValueError("Original capture public URL contradicts request")
    manifest=normalize(source,source_receipt,discovery_file)
    manifest_path=out/"source-locked-manifest.json"
    manifest_path.write_text(json.dumps(manifest,indent=2)+"\n")
    if not client_brief:
        client_brief=("Direct a cinematic 16:9 product demo of the REAL public "
                      "software interface. Preserve the original recorded "
                      "cursor approach and every browser-verified actual "
                      "interaction/result. Use the original evidence to "
                      "discover the action labels, geometry and time. Keep "
                      "context while approaching tiny top-edge controls, "
                      "make real changed results readable, then return to "
                      "actual source. Use source-timed sound for every true "
                      "interaction. No fictional software or outcomes.")
    packet=build_contract(source,manifest_path,client_brief)
    receipt={
        "schema":"sauce-autonomous-public-ui-film-v1",
        "url":url,
        "status":"verified_capture_ready",
        "source":str(source),
        "sourceSha256":packet["actualCapture"]["sourceSha256"],
        "manifest":str(manifest_path),
        "manifestSha256":packet["actualCapture"]["manifestSha256"],
        "actualActions":[{"index":e["index"],
                          "label":e.get("verifiedObservedPublicAction"),
                          "sourceTime":e["sourceTime"]}
                         for e in packet["actualCapture"]["verifiedEvents"]],
        "recordedSourceOnly":True,
        "noAutoPublication":True,
        "creativeApproved":False,
        "independentPremiumApproval":False,
        "scope":"explicit-allowlist anonymous public reversible ARIA tabs",
        "productionReady":False}
    (out/"evidence-receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    if capture_only:
        return receipt
    if not key:
        receipt["status"]="fail_closed_provider_key_unavailable"
        (out/"evidence-receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
        return receipt
    from auto_direct_studio_film import run_unattended
    directed=run_unattended(
        source,manifest_path,client_brief,out/"director",
        model=model,key=key,max_attempts=max_attempts,render=True,
        reference_paths=tuple(reference_videos))
    receipt["status"]=(
        "film_requires_human_review" if directed.get("outcome")=="needs_review"
        else "director_failed_source_retained")
    receipt["providerOutcome"]=directed.get("outcome")
    receipt["film"]=str(out/"director"/"film.mp4") if directed.get("outcome")=="needs_review" else None
    receipt["providerAttemptCount"]=len(directed.get("attempts",[]))
    receipt["filmSha256"]=directed.get("filmSha256") if directed.get("outcome")=="needs_review" else None
    (out/"evidence-receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--url",required=True)
    p.add_argument("--allowed-host",required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--seconds",type=float,default=16.)
    p.add_argument("--from-capture",type=Path)
    p.add_argument("--capture-only",action="store_true")
    p.add_argument("--model",default="gemini-3-flash-preview")
    p.add_argument("--max-attempts",type=int,default=3)
    p.add_argument("--reference-video",type=Path,action="append",default=[])
    p.add_argument("--brief")
    a=p.parse_args()
    key=os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    result=run(a.url,a.allowed_host,a.out,seconds=a.seconds,
        from_capture=a.from_capture,capture_only=a.capture_only,
        model=a.model,max_attempts=a.max_attempts,
        reference_videos=tuple(a.reference_video),key=key,
        client_brief=a.brief)
    print(json.dumps({k:result.get(k) for k in
        ("status","url","sourceSha256","manifestSha256","actualActions",
         "providerOutcome","providerAttemptCount","film","filmSha256",
         "creativeApproved","productionReady")},indent=2))
    if result["status"] not in ("verified_capture_ready","film_requires_human_review"):
        raise SystemExit(2)

if __name__=="__main__":main()
