#!/usr/bin/env python3
"""PRIVATE RESEARCH: one allowlisted public URL -> real discovered-action demo.

Not a general-public ingestion endpoint. Network-level egress isolation,
legal site permissions, authenticated access and production concurrency still
require separate engineering. Never auto-publishes or approves a film.
"""
from __future__ import annotations
import argparse,hashlib,json,os,subprocess,sys,time
from pathlib import Path
from urllib.parse import urlsplit
from public_interaction_scout import discover
from record_scouted_interactions import capture
from verified_capture_receipt_adapter import convert
from source_event_director import direction
from source_director_preflight import preflight_source_edit
from quality_preview_supervisor import analyze
from capture_safety import validate_public_url


def filehash(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for piece in iter(lambda:f.read(1048576),b""):h.update(piece)
    return h.hexdigest()


def run(url,host,out,*,seconds=12,display=":154",max_probes=8):
    actual=(urlsplit(validate_public_url(url)).hostname or "").lower()
    if actual!=host.lower():raise ValueError("Explicit allowed public hostname mismatch")
    out=Path(out).resolve()
    if out.exists() and any(out.iterdir()):
        raise ValueError("Refuse to replace an existing output or original evidence")
    out.mkdir(parents=True,exist_ok=True,mode=0o700)
    try:os.chmod(out,0o700)
    except OSError:pass
    started=time.monotonic()
    receipt={
        "schema":"sauce-public-url-to-film-private-research-v1",
        "requestedUrl":url,"allowedHost":host,
        "creativeApproved":False,"customerApproved":False,
        "productionReady":False,
        "status":"failed_closed","stage":"discovery",
        "stages":[],"source":None,"film":None}
    def write(): (out/"run-receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    write()
    try:
        discovery=discover(url,host,max_probes=max_probes,out=out/"discovery")
        plan=discovery.get("autoActionPlan")
        if plan is None:raise ValueError("No two distinct source-visible safe actions")
        receipt["stages"].append({"stage":"discovery","status":"verified",
             "testedControls":discovery["probed"],
             "chosenControls":[x["label"] for x in plan["actions"]],
             "selectionMethod":plan["selectionMethod"]})
        receipt["stage"]="real-browser-recording";write()
        folder=out/"capture"
        raw=capture(out/"discovery/scout-evidence.json",folder,host,
                    labels=None,seconds=seconds,display=display)
        source=folder/"source-native-dpr2-60.mp4"
        rawpath=folder/"original-source-events.json"
        receipt["source"]={"file":str(source),
                            "sha256":filehash(source),
                            "originalReceiptSha256":filehash(rawpath),
                            "nativeFrames":raw["frameCount"],
                            "originalPointerSamples":len(raw["pointer_samples"]),
                            "origin":raw["source"]}
        receipt["stages"].append({"stage":"recording","status":"verified",
             "sourceNativeFrames":raw["frameCount"],
             "capturedEvents":len(raw["events"])})
        receipt["stage"]="independent-source-assertions";write()
        manifest=folder/"verified-manifest.json"
        verified=convert(source,rawpath)
        if len(verified["events"])!=2 or any(e["kind"]!="click" for e in verified["events"]):
            raise ValueError("Independent original click-release evidence failed")
        manifest.write_text(json.dumps(verified,indent=2)+"\n")
        receipt["stages"].append({"stage":"independent-source-assertions",
             "status":"verified",
             "pixelChanges":verified["provenance"]["sourcePixelChangedFractions"],
             "realClickCount":2})
        receipt["stage"]="evidence-locked-source-director";write()
        film_plan=direction(source,manifest)
        plan_path=out/"source-event-film-plan.json"
        plan_path.write_text(json.dumps(film_plan,indent=2)+"\n")
        report=preflight_source_edit(film_plan,verified,source,(2880,1800),60,
                                     manifest_path=manifest)
        (out/"editorial-preflight.json").write_text(json.dumps(report,indent=2)+"\n")
        if report["findings"]:
            raise ValueError("Physical source-bound editorial preflight rejected plan: "+
                             ",".join(f["code"] for f in report["findings"]))
        def renderer(*args,timeout=140):
            p=[sys.executable,str(Path(__file__).with_name("render_event_video.py")),
                "--video",str(source),"--manifest",str(manifest),
                "--film-plan",str(plan_path),*args]
            result=subprocess.run(p,capture_output=True,text=True,
                                  timeout=timeout,check=False)
            return result.returncode,(result.stdout+"\n"+result.stderr)[-9000:]
        rc,log=renderer("--validate-only")
        (out/"validator.log").write_text(log)
        if rc:raise ValueError("Original renderer refused source-bound plan")
        receipt["stages"].append({"stage":"director","status":"source-verified",
             "kind":"deterministic_no_model","planSha256":filehash(plan_path),
             "eventCoverage":[0,1]})
        receipt["stage"]="render";write()
        film=out/"private-demo-1080p60.mp4"
        rc,log=renderer("--output",str(film),timeout=330)
        (out/"render.log").write_text(log)
        if rc or not film.is_file():
            raise RuntimeError("Actual native-source render failed")
        receipt["film"]={"file":str(film),"sha256":filehash(film)}
        receipt["stages"].append({"stage":"render","status":"full-decode-rendered",
             "filmSha256":receipt["film"]["sha256"]})
        receipt["stage"]="encoded-qa";write()
        qa=analyze(film,evidence={
            "source_path":str(source),"source_sha256":filehash(source),
            "event_manifest_path":str(manifest),
            "event_manifest_sha256":filehash(manifest)},seconds=seconds)
        (out/"encoded-qa.json").write_text(json.dumps(qa,indent=2)+"\n")
        receipt["encodedQaVerdict"]=qa["verdict"]
        receipt["encodedFindings"]=[f["code"] for f in qa["findings"]]
        receipt["status"]="human_review_required" if qa["verdict"]!="REJECT" else "technical_render_creative_reject"
        receipt["stage"]="done"
        receipt["elapsedSeconds"]=round(time.monotonic()-started,2)
        write()
        return receipt
    except Exception as exc:
        receipt["status"]="failed_closed"
        receipt["exceptionType"]=type(exc).__name__
        receipt["elapsedSeconds"]=round(time.monotonic()-started,2)
        write()
        raise


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--url",required=True)
    ap.add_argument("--allow-host",required=True)
    ap.add_argument("--out",required=True,type=Path)
    ap.add_argument("--seconds",type=int,default=12)
    ap.add_argument("--display",default=":154")
    ap.add_argument("--max-probes",type=int,default=8)
    a=ap.parse_args()
    result=run(a.url,a.allow_host,a.out,seconds=a.seconds,
               display=a.display,max_probes=a.max_probes)
    print(json.dumps({"status":result["status"],"source":result["source"],
       "film":result["film"],"qa":result.get("encodedFindings"),
       "elapsedSeconds":result["elapsedSeconds"],"premiumApproved":False},indent=2))
