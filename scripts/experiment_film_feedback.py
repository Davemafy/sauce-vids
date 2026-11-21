#!/usr/bin/env python3
"""Opt-in real-video feedback loop for existing Sauce source-true JSON films.

Runs a Gemini visual critique of a *finished* MP4, then asks for revised
camera keyframes and deterministically validates them against the immutable
recorded source. The current film and criticism prompts are specifically
calibrated to the public Refit historic-evidence experiment; this is NOT an
arbitrary-URL production director. No browser actions, site clicks or generated UI.
CLI: python3 scripts/experiment_film_feedback.py --baseline-video ...
  --source-video ... --manifest ... --base-plan ... --out ...
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / "scripts" / "render_event_video.py"
MODEL = "gemini-3.1-flash-lite"
MAX_VIDEO = 12 * 1024 * 1024
REVIEW_SCHEMA = "sauce-video-critique-experiment-v1"


def film_bytes(path: Path) -> bytes:
    """Protect against accidentally sending arbitrary giant/private files."""
    if path.suffix.lower() != ".mp4" or not path.is_file():
        raise ValueError("A finished MP4 file is required")
    if path.stat().st_size > MAX_VIDEO or path.stat().st_size < 30000:
        raise ValueError("Video exceeds bounded experiment size or is empty")
    return path.read_bytes()


def request(parts, *, model=MODEL, max_output=2500, temperature=0.3) -> tuple[str, dict]:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("Existing Gemini inference credential not available")
    body = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "maxOutputTokens":max_output, "temperature":temperature,
        },
    }
    req = Request(
        "https://generativelanguage.googleapis.com/v1beta/models/" +
        model + ":generateContent",
        data=json.dumps(body).encode(), method="POST",
        headers={"Content-Type":"application/json",
                 "X-goog-api-key":key})
    try:
        with urlopen(req, timeout=120) as resp:
            answer=json.load(resp)
    except HTTPError as error:
        raise RuntimeError("Video Gemini API HTTP " + str(error.code)) from error
    txt="".join(p.get("text","") for p in answer["candidates"][0]["content"]["parts"])
    if not txt.strip():
        raise RuntimeError("Empty creative review response")
    usage=answer.get("usageMetadata",{})
    return txt, {
        "model":model,"input_tokens":usage.get("promptTokenCount"),
        "output_tokens":usage.get("candidatesTokenCount"),
        "total_tokens":usage.get("totalTokenCount"),
        "video_prompt_tokens":sum(x.get("tokenCount",0) for x in usage.get("promptTokensDetails",[])
                                  if x.get("modality")=="VIDEO"),
        "calls":1
    }


def video_part(path:Path) -> dict:
    return {"inline_data":{"mime_type":"video/mp4",
                           "data":base64.b64encode(film_bytes(path)).decode("ascii")}}


def run_review(video:Path, out:Path, *, model=MODEL, product_goal="",
               previous_note="") -> tuple[dict,dict]:
    prompt = (
        "You are an unforgiving senior software-product film editor. WATCH THE ACTUAL "
        "attached encoded video from beginning to end; do not guess from a screenplay. "
        "This is a source-true product demo, not an invitation to invent scenes. "
        "What happens in the real frame at 0-2s, 2-4s, 4-6s and after 6s? "
        "Does this feel like a professional paid-for demo or a stalled screen share? "
        "At 390px mobile width, which important words, evidence labels, results are unreadable? "
        "Distinguish RECORDED historical results from a new LIVE workflow. "
        "A genuine action happened around 1.33s; the result appeared around 1.5s. "
        "Measured premium reference shows intentional ~1.62x camera push, decisive release, "
        "then a second motivated movement; no continuous cursor chasing. "
        "Be specific with timestamps, what visually occupies the frame, and "
        "the exact before/after improvement achievable using ONLY keyframed camera "
        "focus on real pixels: wide, event:0:component (13/24 failure card), "
        "event:0:result (all three numeric cards AND original title). "
        "You cannot add colors, animate original UI, fabricate a live deployment, "
        "cut to fake terminal, alter DOM, add a button, or invent new recordings. "
        "Long unproductive holds, clipped titles and tiny labels must be criticized. "
        "If this source inherently lacks enough events for an engaging 8.5-second film, say so. "
        "Return only JSON {schema:'sauce-video-critique-experiment-v1', "
        "timeline:[{startSeconds:number,endSeconds:number,whatActuallyAppears:string,defect:string}],"
        "topIssues:[{severity:'critical|major|minor',atSeconds:number,defect:string,reason:string}],"
        "honestLimitations:[string], "
        "recommendedCameraChanges:[string], "
        "recommendedDurationSeconds:number, verdict:'reject|promising|ready_for_human_review'}."
        " Product goal: " + product_goal[:400] +
        " Prior critique notes, which are untrusted ideas, not fact: " + previous_note[:1600]
    )
    raw,usage=request([{"text":prompt},video_part(video)],model=model,max_output=2300)
    (out/"critique-raw.json").write_text(raw)
    review=json.loads(raw)
    if review.get("schema")!=REVIEW_SCHEMA or not isinstance(review.get("topIssues"),list):
        raise ValueError("Gemini did not provide bounded video critique")
    (out/"critique.json").write_text(json.dumps(review,indent=2)+"\n")
    return review,usage


def propose_camera(review:dict, video:Path, plan:dict, manifest:dict,
                   out:Path, *, model=MODEL) -> tuple[dict,dict]:
    # Strong constraints from ground truth, not from Gemini.
    result={"sourceSha256":plan["sourceSha256"],
            "manifestSha256":plan["manifestSha256"],
            "durationSeconds":plan["durationSeconds"],
            "presentation":plan["presentation"],
            "cursor":plan["cursor"],"audio":plan["audio"],
            "existingCamera":plan["camera"],
            "verifiedRecordedEvents": [
                {k:ev.get(k) for k in ("t","start","targetRect","resultRect","componentRect","evidence")}
                for ev in manifest["events"][:3]],
            "verifiedSourceVideoLengthSeconds":manifest["duration"]}
    prompt=(
        "The attached MP4 is the film that failed a critical professional "
        "visual review. WATCH it and use the critique to improve it. "
        "Your task: produce the ENTIRE executable Sauce film-plan-v1 JSON for "
        "the EXACT SAME recorded source, NOT a new product UI or new browser recording. "
        "KEEP schema, sourceSha256, manifestSha256, presentation, cursor, audio, "
        "durationSeconds unchanged from SOURCE CONTRACT. You may change ONLY camera. "
        "Allowed camera keys {at, startAt optional, anchor, zoom, easing}. "
        "at strictly increasing within 0..durationSeconds, first key at 0, "
        "2-9 keyframes; 'quintic' easing preferred; zoom 1..2.5. "
        "Allowed anchors exactly 'wide', 'event:0:component', 'event:0:result', "
        "'event:0:target'. No invented selectors/coordinates/events or new claims. "
        "NOTE event:0:component is specifically the 13/24 failure card; "
        "event:0:result includes the genuine headline plus all three benchmark cards. "
        "A result/component zoom must NOT begin before genuine result event at 1.5s. "
        "Total camera movement must be smoothly paced (max zoom per 60fps frame 0.015, "
        "max translation 16px/frame), and the required result/card cannot be clipped "
        "at camera endpoints. Prefer distinct 'failure close-up -> full evidence release' "
        "or 'overview -> failure focus -> broader proof', not a frozen screenshot. "
        "The 390px phone viewer must know that 13 of 24 failed and adapted 24/24 passed. "
        "Do not hide entire heading while framing a full proof. "
        "Do NOT pad unproductive holds simply to reach duration. "
        "Keep original audio exactly synced; it ends around 8.35s so do not "
        "shorten this experiment until a new audio track is actually generated. "
        "This is a creative-direction-only experiment, no new features. "
        "Return ONLY JSON satisfying the existing schema. "
        "AUTHORITATIVE SOURCE CONTRACT:\n" + json.dumps(result,ensure_ascii=False) +
        "\nCRITIQUE OF THE ACTUAL MP4:\n"+json.dumps(review,ensure_ascii=False))
    raw,usage=request([{"text":prompt},video_part(video)],model=model,max_output=1600,temperature=.55)
    (out/"model-plan-raw.json").write_text(raw)
    proposal=json.loads(raw)
    return constrained_plan(plan,proposal),usage


def constrained_plan(base:dict, proposal:dict) -> dict:
    # Correct a common harmless response-envelope error WITHOUT correcting
    # invented actions or accepting changes to locked source evidence.
    if isinstance(proposal,list):
        if proposal and all(isinstance(k,dict) and "at" in k and "anchor" in k
                            for k in proposal):
            # The model returned the camera array itself. This is still
            # precisely the restricted, editable field of the locked plan.
            proposal={"camera":proposal}
        elif len(proposal)==1:
            proposal=proposal[0]
    # Never trust a model to update source or evidence hashes, audio or media.
    if not isinstance(proposal,dict) or not isinstance(proposal.get("camera"),list):
        raise ValueError("Model did not return film-plan camera")
    allowed={"schema","sourceSha256","manifestSha256","durationSeconds",
             "presentation","cursor","audio","camera"}
    if set(proposal)-allowed:
        raise ValueError("Model invented unsupported film-plan controls")
    for key in allowed-{"camera"}:
        # Omitted immutable metadata is injected from our verified base plan;
        # a DIFFERENT explicitly submitted immutable value is never allowed.
        if key in proposal and proposal[key]!=base.get(key):
            raise ValueError("Model attempted to change immutable "+key)
    camera=proposal["camera"]
    if not 2<=len(camera)<=9:
        raise ValueError("Camera must have 2..9 bounded keys")
    for item in camera:
        if not isinstance(item,dict) or set(item)-{"at","startAt","anchor","zoom","easing"}:
            raise ValueError("Unexpected camera fields")
        if item.get("anchor") not in ("wide","event:0:component","event:0:result","event:0:target"):
            raise ValueError("Model invented unsupported anchor")
    return {**base, "camera":camera}


def validate_pre_action_camera(plan:dict,manifest:dict)->None:
    """The movie may not establish interest by anticipating unseen proof."""
    events=manifest.get("events") or []
    if not events or not isinstance(events[0].get("t"),(int,float)):
        raise ValueError("Missing verified source result timestamp")
    onset=float(events[0]["t"])
    for k in plan["camera"]:
        if float(k["at"])<=onset+1e-6 and (
                k["anchor"]!="wide" or abs(float(k["zoom"])-1.)>1e-6):
            raise ValueError("Pre-action zoom: remain wide with zoom 1.0 through verified result at "+str(onset))


def validation(plan_path:Path,source:Path,manifest:Path,python=sys.executable)->str:
    command=[python,str(RENDERER),"--video",str(source),"--manifest",str(manifest),
             "--film-plan",str(plan_path),"--validate-only"]
    proc=subprocess.run(command,capture_output=True,text=True,timeout=75,cwd=ROOT)
    msg=(proc.stdout+"\n"+proc.stderr)[-4000:]
    if proc.returncode!=0 or "JSON_FILM_PLAN_VALIDATED" not in msg:
        raise ValueError("Source-true film plan failed validation: "+msg[-1200:])
    return msg


def model_video_compare(baseline:Path,revised:Path,out:Path,*,model=MODEL):
    prompt=(
        "WATCH BOTH actual full encoded MP4 videos. The first is Film A (baseline), "
        "second Film B (revision). Both are footage of the exact same public Refit "
        "website and historical recorded evaluation, not an actual fresh agent run. "
        "You are a demanding impartial editor. Which one better tells the truthful "
        "24/24 -> 13/24 -> 24/24 result with cinematic action-following camera and "
        "readability in a 390px mobile player? Give actual timestamps and what visibly "
        "changes; do not award high ratings for smooth rendering alone. "
        "Check for new clipping, lack of a strong opening, unwarranted post-result "
        "holds, unmotivated zooms, and whether small headings are legible. "
        "Return ONLY JSON with schema:'sauce-blind-video-comparison-v1', "
        "winner:'A|B|tie', "
        "filmA:{pacing:number,mobileReadability:number,clarity:number}, "
        "filmB:{pacing:number,mobileReadability:number,clarity:number}, "
        "observedChanges:[string], stillWeak:[string], "
        "worthPublishing:boolean, nextDirection:string. "
        "Ratings from 1 to 5 reflect only what is visible; never claim "
        "ready to publish if the story or mobile legibility still fails."
    )
    raw,usage=request([{"text":prompt},video_part(baseline),video_part(revised)],
                      model=model,max_output=1500,temperature=.2)
    (out/"comparison-raw.json").write_text(raw)
    result=json.loads(raw)
    # Model occasionally substitutes the schema's name for the *key*.
    # Recover only that envelope typo, never inferred ratings or conclusions.
    if (result.get("schema") is None and
        result.get("sauce-blind-video-comparison-v1")=="sauce-blind-video-comparison-v1"):
        result={"schema":"sauce-blind-video-comparison-v1",
                **{k:v for k,v in result.items() if k!="sauce-blind-video-comparison-v1"},
                "responseEnvelopeCorrected":True}
    if (result.get("schema")!="sauce-blind-video-comparison-v1" or
            result.get("winner") not in ("A","B","tie")):
        raise ValueError("Unknown or incomplete comparison schema; preserve the raw response")
    # A model's worthPublishing verdict is NEVER human creative acceptance.
    result["creativeApproval"]=False
    (out/"comparison.json").write_text(json.dumps(result,indent=2)+"\n")
    return result,usage


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline-video",required=True,type=Path)
    ap.add_argument("--source-video",required=True,type=Path)
    ap.add_argument("--manifest",required=True,type=Path)
    ap.add_argument("--base-plan",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    ap.add_argument("--model",default=MODEL)
    ap.add_argument("--renderer-python",default=sys.executable)
    ap.add_argument("--compare-only",type=Path,
                    help="Revised finished film MP4 to compare with baseline")
    args=ap.parse_args()
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    film_bytes(args.baseline_video)
    if args.compare_only:
        comparison,usage=model_video_compare(args.baseline_video,args.compare_only,out,
                                              model=args.model)
        (out/"usage.json").write_text(json.dumps([usage],indent=2)+"\n")
        print(json.dumps({"comparison":comparison,"usage":usage},indent=2))
        return
    source=args.source_video.resolve();manifest=args.manifest.resolve()
    original=args.base_plan.resolve();video=args.baseline_video.resolve()
    base=json.loads(original.read_text())
    evidence=json.loads(manifest.read_text())
    if hashlib.sha256(source.read_bytes()).hexdigest()!=base["sourceSha256"]:
        raise ValueError("Source video does not match the prior creative plan")
    if hashlib.sha256(manifest.read_bytes()).hexdigest()!=base["manifestSha256"]:
        raise ValueError("Evidence manifest does not match the prior creative plan")
    validation(original,source,manifest,python=args.renderer_python)
    # The existing renderer resolves licensed voice audio RELATIVE to its
    # validated plan directory. Keep bytes, path and sync unchanged; copy the
    # exact private asset rather than weakening its path sandbox checks.
    if base.get("audio",{}).get("mode")=="file":
        relative=base["audio"]["file"]
        original_audio=(original.parent/relative).resolve()
        dest=(out/relative).resolve()
        if not dest.is_relative_to(out) or not original_audio.is_file():
            raise ValueError("Original private narration is unavailable")
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(original_audio,dest)
        if hashlib.sha256(original_audio.read_bytes()).digest()!=hashlib.sha256(dest.read_bytes()).digest():
            raise ValueError("Audio copy changed original narration bytes")
    calls=[]
    prior_review=out/"critique.json"
    prior_proposal=out/"model-plan-raw.json"
    if prior_review.is_file() and prior_proposal.is_file():
        # Resume the exact previously paid model attempts after a deterministic
        # validation failure. Do not repeat expensive video inference.
        critique=json.loads(prior_review.read_text())
        candidate=constrained_plan(base,json.loads(prior_proposal.read_text()))
        calls=[{"model":args.model,"calls":2,"total_tokens":None,
                "note":"Reused completed Gemini review and plan; prior failed run did not persist token metadata"}]
        repaired=sorted(out.glob("repair-model-raw-*.json"))
        if repaired:
            candidate=constrained_plan(base,json.loads(repaired[-1].read_text()))
            calls[0]["note"] += "; resumed newest previously paid correction"
    else:
        critique,usage=run_review(video,out,model=args.model,
                                product_goal="Show real Refit historical 24/24 -> 13/24 -> 24/24 proof on X")
        calls.append(usage)
        candidate,usage=propose_camera(critique,video,base,evidence,out,model=args.model)
        calls.append(usage)
    candidate_path=out/"revised-film-plan.json"
    for attempt in range(3):
        candidate_path.write_text(json.dumps(candidate,indent=2)+"\n")
        try:
            # The real recorded event clock, not the director's wishes,
            # determines when the result may appear in a camera close-up.
            validate_pre_action_camera(candidate,evidence)
            validation(candidate_path,source,manifest,python=args.renderer_python)
            break
        except ValueError as ex:
            (out/f"validation-rejection-{attempt}.txt").write_text(str(ex)+"\n")
            if attempt==2:
                (out/"usage.json").write_text(json.dumps(calls,indent=2)+"\n")
                raise
            repair_prompt=(
                "You previously WATCHED the actual 8.5-second Sauce film and "
                "proposed this camera edit, but the deterministic SOURCE-TRUE "
                "video validator REJECTED it. Revise only the camera keyframes. "
                "Do not edit browser source, events, audio, hashes, crop rectangles "
                "or film duration. Return ONLY JSON with the field camera as an "
                "array of 2-9 keyframes (at, optional startAt, anchor, zoom, easing). "
                "at must be strictly increasing, first at 0. IMPORTANT: the "
                "first two keys must remain wide at zoom 1.0 until t1.5, "
                "because Sauce forbids pre-action zooms. Allowed anchors "
                "wide, event:0:component (13/24 failure), event:0:result "
                "(heading + all cards), event:0:target. A camera move towards "
                "result or component starts only AFTER t1.5 when the page "
                "actually reveals the card. The source frame must remain "
                "inside 1920x1080: a zoom of 1.8 on full result is marginal; "
                "try 1.45-1.55 for full evidence. Smooth transitions usually "
                "need >=1.5 seconds; no frame exceeds 16px translation or "
                ".015 zoom. A fixed 8.5s voice track ends t8.345; "
                "preserve runtime. Address the actual critique, not arbitrary moves. "
                "EXACT ERROR: "+str(ex)[-1250:]+"\nYOUR REJECTED CAMERA: "+
                json.dumps(candidate["camera"]) + "\nVISUAL CRITIQUE: "+
                json.dumps(critique)[:4500])
            raw,receipt=request([{"text":repair_prompt},video_part(video)],
                                model=args.model,max_output=1100,temperature=.3)
            calls.append(receipt)
            (out/f"repair-model-raw-{attempt}.json").write_text(raw)
            partial=json.loads(raw)
            candidate=constrained_plan(base,partial)
            (out/"usage.json").write_text(json.dumps(calls,indent=2)+"\n")
    (out/"usage.json").write_text(json.dumps(calls,indent=2)+"\n")
    output=out/"revised-film-1080p60.mp4"
    subprocess.run([args.renderer_python,str(RENDERER),"--video",str(source),
                    "--manifest",str(manifest),"--film-plan",str(candidate_path),
                    "--output",str(output)],cwd=ROOT,check=True,timeout=160)
    check=subprocess.run(["ffmpeg","-v","error","-xerror","-i",str(output),
                          "-f","null","-"],capture_output=True,timeout=35)
    if check.returncode!=0:
        raise RuntimeError("Full encoded MP4 failed decode")
    comparison,usage=model_video_compare(video,output,out,model=args.model)
    calls.append(usage)
    (out/"usage.json").write_text(json.dumps(calls,indent=2)+"\n")
    print(json.dumps({"sourceSha256":base["sourceSha256"],
                      "output":str(output),"outputSha256":hashlib.sha256(output.read_bytes()).hexdigest(),
                      "review":critique,"comparison":comparison,
                      "usage":calls,"creativeApproved":False},indent=2))


if __name__=="__main__":
    main()
