"""Native Stagehand evidence -> source-truthful Sauce Phase 2 studio film plan.

This does not ask an LLM to invent coordinates, results, clicks or timing.
The agent selects the actual safe public workflow; all creative shot positions,
clock times, physical zoom and source provenance remain anchored to that capture.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from source_event_director import direction


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def actual_source(manifest, video):
    if manifest.get("cursorless") is not True:
        raise ValueError("No original cursorless browser source")
    prov=manifest.get("provenance",{})
    if prov.get("capture")!="Chromium X11 native DPR2 60fps":
        raise ValueError("Original native 60fps Chromium proof is mandatory")
    if prov.get("originalSourceSha256")!=sha(video):
        raise ValueError("Source SHA256 mismatch")
    if len(manifest.get("pointer_samples",[]))<25:
        raise ValueError("A real recorded mouse approach is mandatory")
    if len(manifest.get("events",[]))!=1:
        raise ValueError("Bounded one-real-action Stagehand director only")
    e=manifest["events"][0]
    if e.get("kind")!="click" or not e.get("evidence"):
        raise ValueError("The source event must be an independently verified click")
    return e


def _round(t):
    return round(float(t),6)


def directed_plan(source, manifest):
    source=Path(source)
    manifest=Path(manifest)
    raw=json.loads(manifest.read_text())
    e=actual_source(raw,source)
    plan=direction(source,manifest)
    duration=float(plan["durationSeconds"])
    w=raw["capture_rect"]["width"]
    h=raw["capture_rect"]["height"]
    result=e["resultRect"]
    fraction=(result["width"]*result["height"])/(w*h)
    if not (6.<=duration<=16. and 0.035<=fraction<=0.48):
        # A full-screen theme change is a truthful overview, not a modal
        # cinematic closeup; never force a synthetic compact result region.
        return plan,{"strategy":"source-true-overview","resultFraction":round(fraction,5)}
    start=e["start"];observed=e["t"]
    if (start<.7 or observed+2.75>=duration or
        start-.62<.40 or observed<=start):
        raise ValueError("No readable source-proven click/result/hold timeline")
    # Scale the entire physical browser and its genuine source pixel texture.
    # On a 1920x1080 cloud stage .96 overscans the card at click by ~9%,
    # protecting against blank side strips during bounded cursor following.
    # The 1.2/1.4 post-result closeup remains under strict motion and crop
    # validation, and leaves long enough to understand source DOM content.
    keys=[
      {"at":0,"scale":.88,"viewScale":1,
       "center":[.5,.5],"yaw":0,"pitch":0},
      {"at":_round(start-.12),"startAt":_round(start-.62),
       "scale":.96,"viewScale":1,
       "center":[.5,.5],"yaw":0,"pitch":0},
      {"at":_round(observed+.92),"startAt":_round(observed+.08),
       "scale":1.2,"viewScale":1.4,
       "focus":"event:0:result","yaw":0,"pitch":0},
      {"at":_round(duration),"startAt":_round(duration-1.5),
       "scale":.88,"viewScale":1,
       "center":[.5,.5],"yaw":0,"pitch":0}
    ]
    if not keys[2]["at"]<keys[3]["startAt"]-.7:
        raise ValueError("No independently readable hold after source result")
    studio=plan["studioStage"]
    studio["camera"]=keys
    studio["motion"]={
      "profile":"reference-spring","immersive":True,"shutter":.25,
      "follow":{"mode":"source-cursor-spring","eventIndices":[0],
                "responseSeconds":.38,"strength":.12,
                "deadzone":.12,"maxOffset":.02,
                "beforeSeconds":.60,"afterSeconds":.60}}
    # Never create an art-directed result focus before a genuine verified
    # browser result exists. No manually supplied pixel coordinates.
    if keys[2]["startAt"]<=observed:
        raise ValueError("Pre-action result presentation prohibited")
    return plan,{"strategy":"source-native-causal-detail",
      "resultFraction":round(fraction,5),
      "contextUntilPress":True,"resultFirstAt":keys[2]["startAt"],
      "confirmedResultAt":observed,"premiumApproved":False}


def check_shell_coverage(plan, source, manifest):
    """Deny a black/unfilled card: original video must cover physical shell."""
    from spatial_studio_stage import load_studio_stage
    from fractions import Fraction
    import subprocess
    info=json.loads(subprocess.check_output([
       "ffprobe","-v","error","-select_streams","v:0",
       "-show_entries","stream=width,height,avg_frame_rate",
       "-of","json",str(source)],text=True))
    s=info["streams"][0]
    w,h=int(s["width"]),int(s["height"])
    fps=float(Fraction(s["avg_frame_rate"]))
    if fps!=60.:
        raise ValueError("No native60 source")
    duration=plan["durationSeconds"]
    stage=load_studio_stage(plan["studioStage"],
         json.loads(Path(manifest).read_text()),source,(w,h),(1920,1080),
         duration,fps)
    if stage.stage_preset=="cloud_shadow_v1":
        from cloud_shadow_stage import window_geometry
    elif stage.stage_preset=="cloud_window_volume_v1":
        from cloud_window_volume_stage import window_geometry
    elif stage.stage_preset in ("cloud_window_sky_v1","cloud_window_fullglass_v1","cloud_window_clearface_v1","cloud_luminous_display_v1"):
        from cloud_window_sky_stage import window_geometry
    else:
        raise ValueError("Stage identity must be approved cloud backdrop")
    x0,y0,x1,y1,_=window_geometry((w,h),(1920,1080))
    # At all 60fps sample times, the genuine browser source quad encloses
    # the visible card. Interpolation is smooth and the checker is conservative.
    for i in range(math.floor(duration*fps)):
        t=i/fps
        q=stage._cloud_base_quad(t)
        bounds=(float(q[:,0].min()),float(q[:,1].min()),
                float(q[:,0].max()),float(q[:,1].max()))
        if bounds[0]>x0+1 or bounds[1]>y0+1 or bounds[2]<x1-1 or bounds[3]<y1-1:
            raise ValueError("Source frame would leave a black strip in Cloud Shadow "
                             f"at original t={t:.3f}s")
    return True


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",required=True,type=Path)
    p.add_argument("--manifest",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    if a.out.exists():raise ValueError("Never overwrite a previous source film plan")
    plan,reason=directed_plan(a.source,a.manifest)
    check_shell_coverage(plan,a.source,a.manifest)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(plan,indent=2)+"\n")
    print(json.dumps({"plan":str(a.out),"reason":reason,
       "sourceSha256":plan["sourceSha256"],"humanApproval":False}))


if __name__=="__main__":
    main()
