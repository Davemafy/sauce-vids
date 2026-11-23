"""Bounded experimental URL -> Stagehand/Gemini discovery -> native60 Phase 2 film.

No frontend deployment or premium-approval claim. Reuses Sauce inspector,
Stagehand 4.4 read-only observe, real-source probe, native X11 Chromium
capture, strict original event adapter and existing Phase 2 compositor.
"""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))

from backend.product_explorer import inspect
from backend.stagehand_discovery import choose_observed_action, SCHEMA
from scripts.capture_safety import validate_public_url
from scripts.capture_stagehand_verified_native import capture,sha
from verified_capture_receipt_adapter import convert
from plan_stagehand_phase2 import directed_plan,check_shell_coverage
from quality_preview_supervisor import analyze


def run(url, out, *, seconds=6.5, display=":178", stagehand_python=None):
    validate_public_url(url)
    out=Path(out).resolve()
    if out.exists():
        raise ValueError("Preserve existing source/evidence: out must not exist")
    if not 6.<=seconds<=16.:
        raise ValueError("Bounded 6..16 second source recording required")
    out.mkdir(parents=True,mode=0o700)
    out.chmod(0o700)
    receipt={
      "schema":"sauce-stagehand-phase2-live-v1",
      "url":url,"status":"failed_closed",
      "capture":None,"film":None,"premiumApproved":False,
      "sourceTrue":False}
    def save():
        (out/"experiment-receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    save()
    try:
        private=out/"private"
        private.mkdir(mode=0o700)
        inspection_dir=private/"inspection"
        report=inspect(url,inspection_dir)
        inspection=inspection_dir/"inspection.json"
        target=private/"stagehand-observations.json"
        interpreter=stagehand_python or os.getenv("SAUCE_STAGEHAND_PYTHON") or sys.executable
        if not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_GENERATIVE_AI_API_KEY") or
                (os.getenv("SAUCE_STAGEHAND_BROWSER")=="browserbase" and
                 os.getenv("BROWSERBASE_API_KEY"))):
            raise RuntimeError("Existing inference credential must be loaded by caller")
        failures=[]
        observed=None
        # Stagehand is a remote inference request, not deterministic local
        # capture. One bounded retry for transient provider/browser failures;
        # no generic nav fallback, no prompts with invented source results.
        for attempt in range(2):
            proc=subprocess.run(
                [interpreter,"-m","scripts.stagehand_public_discovery",
                 "--url",url,"--inspection",str(inspection)],
                cwd=Path(__file__).resolve().parents[1],env=os.environ.copy(),
                capture_output=True,text=True,timeout=100)
            if proc.returncode==0 and len(proc.stdout)<=32000:
                try:
                    observed=json.loads(proc.stdout)
                    break
                except (ValueError,TypeError):
                    pass
            # Keep no raw stderr, URLs with query parameters, or model data
            # in failure logs; only an exit status and attempt number.
            failures.append({"attempt":attempt+1,"exitCode":proc.returncode,
                             "nonJsonOrOversized":proc.returncode==0})
        if failures:
            (private/"stagehand-attempts.json").write_text(
                json.dumps(failures,indent=2)+"\n")
        if observed is None:
            raise RuntimeError("Read-only Stagehand observation failed")
        if (observed.get("schema")!=SCHEMA or observed.get("url")!=url or
                observed.get("actions_executed")!=0):
            raise ValueError("Untrusted or mismatched Stagehand observation")
        plan=choose_observed_action(report,observed)
        if not plan or len(plan["action_ids"])!=1:
            raise ValueError("Agent found no uniquely matched safe local product action")
        # PRIVATE model text retained as evidence only; selectors and
        # model claims cannot become source events.
        target.write_text(json.dumps(observed,indent=2)+"\n")
        receipt["selectedControlId"]=plan["action_ids"][0]
        receipt["status"]="native_source_capture";save()
        capture_dir=private/"native"
        raw=capture(url,inspection,target,capture_dir,
                    seconds=seconds,display=display)
        source=capture_dir/"source-native-dpr2-60.mp4"
        old=capture_dir/"original-source-events.json"
        manifest=capture_dir/"verified-manifest.json"
        converted=convert(source,old)
        if len(converted["events"])!=1 or converted["events"][0]["kind"]!="click":
            raise ValueError("Source action lacks genuine physical click and pixel result")
        manifest.write_text(json.dumps(converted,indent=2)+"\n")
        receipt["capture"]={
          "sha256":sha(source),"frames":raw["frameCount"],
          "pointerSamples":len(raw["pointer_samples"]),
          "verifiedEvents":len(converted["events"])}
        receipt["status"]="planning";save()
        plan,framing=directed_plan(source,manifest)
        check_shell_coverage(plan,source,manifest)
        plan_file=private/"phase2-film-plan.json"
        plan_file.write_text(json.dumps(plan,indent=2)+"\n")
        render=Path(__file__).resolve().with_name("render_event_video.py")
        command=[sys.executable,str(render),"--video",str(source),
                 "--manifest",str(manifest),"--film-plan",str(plan_file)]
        preflight=subprocess.run([*command,"--validate-only"],
                 capture_output=True,text=True,timeout=125)
        (private/"validator.log").write_text((preflight.stdout+preflight.stderr)[-18000:])
        if preflight.returncode:
            raise ValueError("Existing Phase 2 renderer denied source camera plan")
        receipt["status"]="rendering";save()
        film=private/"agent-directed-1080p60.mp4"
        export=subprocess.run([*command,"--output",str(film)],
                             capture_output=True,text=True,timeout=420)
        (private/"renderer.log").write_text((export.stdout+export.stderr)[-18000:])
        if export.returncode or not film.is_file():
            raise RuntimeError("Original Phase 2 compositor did not export film")
        receipt["film"]={"sha256":sha(film),"path":str(film)}
        receipt["sourceTrue"]=True
        receipt["status"]="encoded_qa";save()
        qa=analyze(film,evidence={
             "source_path":str(source),"source_sha256":sha(source),
             "event_manifest_path":str(manifest),
             "event_manifest_sha256":sha(manifest)},seconds=seconds)
        (private/"encoded-quality.json").write_text(json.dumps(qa,indent=2)+"\n")
        receipt["encodedQuality"]=qa["verdict"]
        receipt["qualityIssues"]=[v["code"] for v in qa.get("findings",[])]
        receipt["framing"]=framing
        receipt["status"]=("creative_reject" if qa["verdict"]=="REJECT"
                           else "human_review_required")
        save()
        return receipt
    except Exception as exc:
        receipt["status"]="failed_closed"
        receipt["failureType"]=type(exc).__name__
        save()
        raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--url",required=True)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--seconds",type=float,default=6.5)
    p.add_argument("--display",default=":178")
    p.add_argument("--stagehand-python")
    a=p.parse_args()
    result=run(a.url,a.out,seconds=a.seconds,display=a.display,
               stagehand_python=a.stagehand_python)
    print(json.dumps({k:result.get(k) for k in
       ("status","capture","film","qualityIssues","premiumApproved")},
       indent=2))


if __name__=="__main__":
    main()
