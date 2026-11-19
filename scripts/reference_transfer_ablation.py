"""Research-only reference/target ablation plans using Sauce's existing JSON schema.

Does not contact Gemini, assert premium output, or admit uncertified examples.
Only consumes a verified browser capture and a frame-measured research trace.
Output is directly executable sauce-film-plan-v1, never a second blueprint.
"""
from __future__ import annotations
import argparse,hashlib,json,math,re
from pathlib import Path
try:
    from scripts.reference_shot_fit import match_landscape_component,scale_end_for_frames
except ModuleNotFoundError:
    from reference_shot_fit import match_landscape_component,scale_end_for_frames

def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def generate_ablation_plans(source,manifest_path,trace_path,out_dir,*,duration_seconds=4.0,cursor="none"):
    source=Path(source);manifest_path=Path(manifest_path);trace_path=Path(trace_path)
    trace=json.loads(trace_path.read_text())
    if (trace.get('schema')!='sauce-reference-raster-panel-track-research-v1' or
            trace.get('approvedForGemini') is not False or
            trace.get('fidelityTier')!='research_only'):
        raise ValueError('Only an explicitly research-only measured frame track is accepted')
    observations=trace.get('measurements')
    if not isinstance(observations,list) or len(observations)<2:
        raise ValueError("A complete frame-observation track is required")
    first,last=observations[0],observations[-1]
    fps=trace.get('sourceFrameRate')
    if fps!=[30,1] or last['referenceFrame']-first['referenceFrame']+1!=len(observations):
        raise ValueError("Noncontinuous reference 30fps frame clock")
    if (not all(isinstance(r.get('box'),list) and len(r['box'])==4 for r in observations) or
            any(r['referenceFrame']!=first['referenceFrame']+i for i,r in enumerate(observations))):
        raise ValueError('Missing observed reference geometry')
    if not all(trace.get(k) for k in ('sourceSha256','method')):
        raise ValueError("Unpinned research source")
    manifest=json.loads(manifest_path.read_text())
    if manifest.get('capture_rect') != {'width':1920,'height':1080}:
        raise ValueError('Only source-true 1920x1080 landscape captures are supported by this bounded research comparison')
    events=manifest.get('events')
    if not isinstance(events,list) or len(events)!=1 or not isinstance(events[0],dict):
        raise ValueError("This bounded experiment needs one real recorded event")
    event=events[0]
    if not isinstance(event.get('evidence'),str) or not event['evidence'].strip():
        raise ValueError("Action requires actual outcome evidence")
    if not isinstance(event.get('componentRect'),dict) or not isinstance(event.get('targetRect'),dict):
        raise ValueError("Verified target and complete component are required")
    if cursor not in ('none','recorded'):raise ValueError("Invalid cursor mode")
    if not .5<=duration_seconds<=float(manifest.get('duration',0)):
        raise ValueError("Duration exceeds declared source capture")
    observed=float(event.get('t',float('nan')))
    if not math.isfinite(observed) or observed<=0 or observed>=duration_seconds:
        raise ValueError("Observed outcome must occur in the film")
    start=duration_seconds-len(observations)/30
    if observed>=start:
        # An earlier product state must never be presented as the known result.
        raise ValueError("Verified product result occurs too late for this exact reference hold")
    out_dir=Path(out_dir);out_dir.mkdir(parents=True,exist_ok=True)
    base={"schema":"sauce-film-plan-v1","sourceSha256":file_hash(source),
          "manifestSha256":file_hash(manifest_path),"durationSeconds":duration_seconds,
          "presentation":"fullscreen","cursor":cursor,"audio":{"mode":"clean"}}
    wide=[{"at":0,"anchor":"wide","zoom":1.0},{"at":duration_seconds,"anchor":"wide","zoom":1.0}]
    result_start=math.ceil(observed*10000)/10000
    if observed+.55>=duration_seconds:
        raise ValueError("Insufficient time for source-true camera plan")
    style=[
        {"at":0,"anchor":"wide","zoom":1.0},
        {"at":round(observed,4),"anchor":"wide","zoom":1.0},
        {"at":round(observed+.55,4),"startAt":result_start,
         "anchor":"event:0:component","zoom":1.12,"easing":"quintic"},
        {"at":duration_seconds,"anchor":"event:0:component","zoom":1.12}
    ]
    plans={"no_reference":dict(base,camera=wide),
           "style_description":dict(base,camera=style)}
    width,height=trace['measurements'][0]['box'][2:]
    ratio=width/height
    fit=match_landscape_component(event['componentRect'],(1920,1080),(width,height))
    if fit.eligible_geometry:
        sample_at=max(observed+.035,start-.06)
        if sample_at>start:raise ValueError("No genuine post-event sample before shot")
        scale=scale_end_for_frames(width,trace['measurements'][-1]['box'][2],len(observations))
        layer={"id":"source-true-focal-ui","anchor":"event:0:component",
            "sourceAt":round(sample_at,5),"startAt":start,"endAt":duration_seconds,
            "position":[.5,.5],"enterFrom":[.5,.5],"enterSeconds":0,
            "widthFraction":width/1920,"holdScaleEnd":scale,
            "paddingPx":fit.padding_px,"radiusPx":12,"zIndex":0}
        plans['measured_reference']=dict(base,camera=wide,composition={
            "mode":"isolated-ui","startAt":start,"background":[225,223,219],"layers":[layer]})
    for name,plan in plans.items():
        (out_dir/(name+'.json')).write_text(json.dumps(plan,indent=2)+'\n')
    report={"schema":"sauce-reference-transfer-ablation-v1",
        "researchOnly":True,"productionGeminiEligible":False,
        "geminiCalled":False,"referenceSourceSha256":trace['sourceSha256'],
        "inputSourceSha256":base['sourceSha256'],
        "captureManifestSha256":base['manifestSha256'],
        "verifiedOutcomeAt":observed,
        "referenceFrameCount":len(observations),
        "componentAspectRatio":event['componentRect']['width']/event['componentRect']['height'],
        "referenceAspectRatio":ratio,
        "geometryCompatible":fit.eligible_geometry,
        "geometryReason":fit.reason,
        "semanticTransferApproved":False,
        "renderedFiles":[],
        "armPlans":[name+'.json' for name in plans]}
    (out_dir/'ablation-receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

def main():
    p=argparse.ArgumentParser(description="Create deterministic ablation plans; no model calls or rendering")
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--reference-track',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--duration',type=float,default=4.0)
    p.add_argument('--cursor',choices=['none','recorded'],default='none')
    p.add_argument('--research-only',action='store_true',required=True,
        help='Mandatory explicit guard; uncertified references are not Gemini production data')
    a=p.parse_args()
    r=generate_ablation_plans(a.source,a.manifest,a.reference_track,a.out,
                             duration_seconds=a.duration,cursor=a.cursor)
    print(json.dumps(r,indent=2))

if __name__=='__main__':main()
