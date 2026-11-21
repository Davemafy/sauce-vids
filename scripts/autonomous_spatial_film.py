"""Generate spatial film plans only from real synchronized Chromium DOM planes."""
from __future__ import annotations
import hashlib,json,math
from pathlib import Path
from film_director_capabilities import build_contract
from live_dom_multi_plane import load_live_dom_planes,verify_group_projected_visibility,verify_source_relative_material
from spatial_studio_stage import load_studio_stage
from source_director_preflight import preflight_source_edit

STYLES=(
 {"name":"composed","scale":1.29,"recede":.76,"delay":.16},
 {"name":"dimensional","scale":1.40,"recede":.73,"delay":.20},
 {"name":"subtle","scale":1.16,"recede":.78,"delay":.12},
)

def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()

def snap(t,fps,up=False):
 return (math.ceil(t*fps-1e-8) if up else math.floor(t*fps+1e-8))/fps

def clamp(x,a,b):return min(b,max(a,x))

def create_plan(source,manifest,contract,style):
 cap=contract["actualCapture"];group=cap.get("verifiedLiveDomPlaneGroup")
 if not group or not group["verifiedSynchronizedSameBrowserFrames"]:
  raise ValueError("Cannot invent DOM spatial layers without real paired capture")
 if sha(source)!=cap["sourceSha256"] or sha(manifest)!=cap["manifestSha256"]:
  raise ValueError("Changed source/manifest")
 fps=float(cap["nativeFps"]);end=float(cap["durationSeconds"])
 if fps not in (24,25,30,50,60) or not 2.9<=end<=45:
  raise ValueError("Unsupported paired native source clock or duration")
 events=cap["verifiedEvents"]; ix=group["verifiedEventIndex"]
 if ix not in range(len(events)) or events[ix]["index"]!=ix:
  raise ValueError("Unverified event index")
 event=events[ix]["sourceTime"]
 first=snap(max(float(group["earliestMotionAtSeconds"]),
       event["confirmedResultAt"]+.12),fps,True)
 last=snap(min(end-.01,group["latestMotionEndSeconds"]),fps)
 if last-first<1.5:raise ValueError("No source time for lift, read and safe return")
 original=json.loads(Path(manifest).read_text())
 rects=group["measuredNativeSourceRects"];ids=group["ids"]
 if len(ids) not in (2,3) or len(rects)!=len(ids) or len(original["domPlanes"])!=len(ids):
  raise ValueError("Missing independently paired real elements")
 W,H=cap["resolution"]
 order=sorted(range(len(ids)),key=lambda i:rects[i][0]+rects[i][2]/2)
 layers=[]
 for rank,i in enumerate(order):
  x,y,w,h=rects[i]
  # Cinema coordinates are inferred from original card ordering and geometry.
  hx=clamp(.5+(rank-(len(ids)-1)/2)*(.41 if len(ids)==2 else .29),.17,.83)
  hy=clamp(.5+(((y+h/2)/H)-.5)*.20,.40,.56)
  start=snap(first+min(.25,rank*style["delay"]),fps,True)
  peak=snap(min(last-.93,start+max(.48,(last-first)*.35)),fps)
  if peak-start<.35 or last-peak<.9:raise ValueError("No readable real layer hold")
  layers.append({"id":ids[i],"eventIndex":ix,
    "startAt":start,"peakAt":peak,"endAt":last,
    "liftPx":0,"scale":style["scale"],"shadowStrength":.43,
    "heroCenter":[round(hx,5),round(hy,5)]})
 intro=snap(max(event["confirmedResultAt"]+.23,first-.26),fps,True)
 recede=snap(min(last-.66,first+(last-first)*.53),fps)
 settle=snap(max(recede+.20,last-.35),fps)
 if not .2<intro<recede<settle<end:
  raise ValueError("Invalid authentic source timing for spatial motion")
 camera=[
  {"at":0,"scale":.83,"center":[.5,.5],"yaw":0,"pitch":0},
  {"at":intro,"startAt":snap(max(.03,intro-.28),fps),
   "scale":.82,"focus":f"event:{ix}:result","yaw":0,"pitch":0},
  {"at":recede,"startAt":snap(max(intro+.05,first),fps),
   "scale":style["recede"],"center":[.5,.5],"yaw":0,"pitch":0},
  {"at":end,"startAt":settle,"scale":.83,
   "center":[.5,.5],"yaw":0,"pitch":0}]
 return {"schema":"sauce-film-plan-v1",
  "sourceSha256":cap["sourceSha256"],"manifestSha256":cap["manifestSha256"],
  "durationSeconds":end,"presentation":"fullscreen",
  "cursor":"recorded" if cap["pointerProvenance"]["recordedPointerTrackAvailable"] else "none",
  "audio":{"mode":"eventFoley","eventIndices":list(range(len(events))),
            "clickGain":.35,"motionGain":.16,"masterGain":.45},
  "studioStage":{"camera":camera,"material":{"color":[18,20,25],"grain":.06},
     "depthPx":12,"reflection":.04,
     "lighting":{"eventIndex":ix,"trigger":"verified","intensity":.48,"transitionSeconds":.35},
     "payoff":{"region":f"event:{ix}:result","mode":"overview",
       "minVisible":.90,"minContextVisible":.80}},
  "domPlanes":layers}

def validate_plan(plan,source,manifest,contract):
 raw=json.loads(Path(manifest).read_text());cap=contract["actualCapture"]
 size=tuple(cap["resolution"]);fps=cap["nativeFps"];duration=cap["durationSeconds"]
 stage=load_studio_stage(plan["studioStage"],raw,source,size,(1920,1080),duration,fps)
 group=load_live_dom_planes(plan["domPlanes"],raw,source,manifest,
                           source_size=size,fps=int(fps),duration=duration)
 geometry=verify_group_projected_visibility(stage,group)
 material=verify_source_relative_material(group,stage,source)
 pre=preflight_source_edit(plan,raw,source,size,fps,manifest_path=manifest)
 if pre["findings"]:
  raise ValueError("Strict preflight rejected: "+",".join(f["code"] for f in pre["findings"]))
 return {"geometry":geometry,"material":material,"preflight":pre}


def run(source,manifest,out,*,expected_source_sha256=None,
        expected_manifest_sha256=None,render=True,styles=STYLES):
 """Bounded, no-model, no-overwrite spatial direction on a genuine paired capture."""
 import subprocess,sys
 from quality_preview_supervisor import analyze
 source=Path(source).resolve();manifest=Path(manifest).resolve();out=Path(out).resolve()
 if not source.is_file() or not manifest.is_file():
  raise ValueError("Need authentic browser source and paired clean-plate manifest")
 source_hash=sha(source);manifest_hash=sha(manifest)
 if expected_source_sha256 and expected_source_sha256!=source_hash:
  raise ValueError("Actual original source SHA256 changed")
 if expected_manifest_sha256 and expected_manifest_sha256!=manifest_hash:
  raise ValueError("Actual original manifest SHA256 changed")
 if out.exists() and (not out.is_dir() or any(out.iterdir())):
  raise ValueError("Refuse to overwrite previous media")
 out.mkdir(parents=True,mode=0o700,exist_ok=True)
 receipt={"schema":"sauce-autonomous-real-spatial-v1",
  "sourceSha256":source_hash,"manifestSha256":manifest_hash,
  "modelCalls":0,"creativeApproved":False,"productionReady":False,
  "autoPublished":False,"status":"rejected","candidates":[],"selected":None}
 def save():
  (out/"autonomous-spatial-receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
 try:
  packet=build_contract(source,manifest,"Film real UI with independent source-verified DOM layers")
  if not packet["actualCapture"].get("verifiedLiveDomPlaneGroup"):
   receipt["status"]="no_authentic_paired_layers"
   return receipt
  for style in styles:
   name=style["name"]
   row={"name":name,"status":"rejected"}
   receipt["candidates"].append(row)
   try:
    plan=create_plan(source,manifest,packet,style)
    proof=validate_plan(plan,source,manifest,packet)
    plan_path=out/(name+"-plan.json")
    plan_path.write_text(json.dumps(plan,indent=2)+"\n")
    (out/(name+"-source-proof.json")).write_text(json.dumps(proof,indent=2)+"\n")
    base=[sys.executable,str(Path(__file__).with_name("render_event_video.py")),
     "--video",str(source),"--manifest",str(manifest),"--film-plan",str(plan_path)]
    check=subprocess.run([*base,"--validate-only"],capture_output=True,text=True,
                         check=False,timeout=170)
    (out/(name+"-validator.log")).write_text((check.stdout+"\n"+check.stderr)[-12000:])
    if check.returncode:
     row["status"]="renderer_reject"
     continue
    row["status"]="source-verified-plan"
    if not render:continue
    film=out/(name+".mp4")
    done=subprocess.run([*base,"--output",str(film)],capture_output=True,
                        text=True,check=False,timeout=360)
    (out/(name+"-render.log")).write_text((done.stdout+"\n"+done.stderr)[-12000:])
    if done.returncode or not film.is_file():
     row["status"]="render_failed"
     continue
    qa=analyze(film,evidence={
      "source_path":str(source),"source_sha256":source_hash,
      "event_manifest_path":str(manifest),"event_manifest_sha256":manifest_hash},
      seconds=min(float(packet["actualCapture"]["durationSeconds"]),15))
    (out/(name+"-qa.json")).write_text(json.dumps(qa,indent=2)+"\n")
    row.update(status="rendered_objective_reject" if qa["verdict"]=="REJECT"
       else "rendered_needs_human_review",
       film=str(film),filmSha256=sha(film),encodedQaVerdict=qa["verdict"],
       encodedQaFindings=[x["code"] for x in qa["findings"]],
       authenticLayerIds=packet["actualCapture"]["verifiedLiveDomPlaneGroup"]["ids"])
   except (ValueError,RuntimeError,TypeError,KeyError,OSError,
           subprocess.SubprocessError) as error:
    row.update(status="source_gate_reject",error=type(error).__name__+
               ": "+str(error)[:200])
  valid=[row for row in receipt["candidates"] if row["status"] in (
       "source-verified-plan","rendered_needs_human_review")]
  if valid:
   receipt["selected"]=valid[0]["name"]
   receipt["status"]="needs_human_review" if render else "verified_plan_only"
  else:receipt["status"]="all_spatial_candidates_rejected"
  return receipt
 finally:save()


def main():
 import argparse
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--source",required=True,type=Path)
 p.add_argument("--manifest",required=True,type=Path)
 p.add_argument("--out",required=True,type=Path)
 p.add_argument("--expected-source-sha256")
 p.add_argument("--expected-manifest-sha256")
 p.add_argument("--validate-only",action="store_true")
 args=p.parse_args()
 result=run(args.source,args.manifest,args.out,
            expected_source_sha256=args.expected_source_sha256,
            expected_manifest_sha256=args.expected_manifest_sha256,
            render=not args.validate_only)
 print(json.dumps(result,indent=2))
 if result["status"] not in ("needs_human_review","verified_plan_only"):
  raise SystemExit(2)

if __name__=="__main__":main()
