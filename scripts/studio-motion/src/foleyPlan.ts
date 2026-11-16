/** Deterministic Foley instructions. This module schedules sounds only;
 * Phase 2's Python mixer will synthesize/read assets at these sample indices.
 */
import {CameraPose,FrameMap,FoleyCue,FoleyDuck,FoleyPlan,SaucePreset,TraceEvent,clamp,finite} from "./types";
const RATE=48000 as const;
const samples=(ms:number)=>Math.max(0,Math.round(ms*RATE/1000));
const eventKind=(e:TraceEvent)=>(e.eventType||e.type).toLowerCase().replaceAll("_","-");
function isModal(k:string):boolean{
  return k==="dialog-visible"||k==="modal-open"||k==="modal-opened";
}
function coalesceIntervals(rows:FoleyDuck[]):FoleyDuck[]{
  const sorted=[...rows].sort((a,b)=>a.startSample-b.startSample);
  const out:FoleyDuck[]=[];
  for(const row of sorted){
    const prev=out[out.length-1];
    if(prev&&row.startSample<=prev.endSample){
      prev.endSample=Math.max(prev.endSample,row.endSample);
    }else out.push({...row});
  }
  return out;
}
export function buildFoleyPlan(
  events:TraceEvent[],startMs:number,sourceDurationMs:number,
  outputDurationMs:number,sourceToOutput:(sourceMs:number)=>number,
  preset:SaucePreset,camera:CameraPose[],frameMap:FrameMap[],
  cutFrames:ReadonlySet<number>=new Set()
):FoleyPlan{
  if(![startMs,sourceDurationMs,outputDurationMs].every(finite)||
     sourceDurationMs<=0||outputDurationMs<=0)throw new Error("Invalid Foley clock");
  if(camera.length!==frameMap.length)throw new Error("Foley camera/frame map mismatch");
  const s=preset.sound;
  const plan:FoleyPlan={
    schema:"sauce-foley-plan-v1",sampleRate:RATE,durationMs:outputDurationMs,
    muted:s.muted,masterGain:s.masterGain,musicGain:s.musicGain,
    cues:[],duckIntervals:[]
  };
  if(!s.enabled)return plan;
  const candidates:{sourceMs:number;outputMs:number;sound:FoleyCue["sound"];
    gain:number;trigger:FoleyCue["trigger"]}[]=[];
  let lastClick=-Infinity,lastModal=-Infinity;
  for(const e of [...events].sort((a,b)=>a.t-b.t)){
    if(!finite(e.t))continue;
    const sourceMs=e.t-startMs;
    if(sourceMs<0||sourceMs>sourceDurationMs)continue;
    const kind=eventKind(e);
    const mapped=sourceToOutput(sourceMs);
    if(!finite(mapped))throw new Error("Invalid mapped Foley timestamp");
    if((kind==="click"||kind==="pointerdown")&&sourceMs-lastClick>135){
      candidates.push({sourceMs,outputMs:mapped,
        sound:s.cues.click,gain:.68,trigger:"click"});
      lastClick=sourceMs;
    }else if(isModal(kind)&&sourceMs-lastModal>250){
      candidates.push({sourceMs,outputMs:mapped,
        sound:s.cues.modalOpen,gain:.58,trigger:"modal"});
      lastModal=sourceMs;
    }
  }
  // Camera whooshes are driven by genuine generated keyframe movement.
  // A threshold and cooldown prevent per-frame sound spam.
  const fps=preset.export.fps;
  let lastWhoosh=-Infinity;
  for(let i=5;i<camera.length;i++){
    const current=camera[i]!,earlier=camera[i-5]!;
    const t=i*1000/fps;
    if(t-lastWhoosh<600)continue;
    // Hard cuts are edits, not physical camera whooshes.
    if([...cutFrames].some(c=>c>=i-5&&c<=i))continue;
    const scaleRate=Math.abs(current.scale-earlier.scale)*fps/5;
    const panRate=Math.hypot(current.focusX-earlier.focusX,
                             current.focusY-earlier.focusY)*fps/5;
    const tiltRate=Math.hypot(current.rotateXDeg-earlier.rotateXDeg,
                              current.rotateYDeg-earlier.rotateYDeg)*fps/5;
    if(scaleRate<.48&&panRate<225&&tiltRate<6)continue;
    // Use the SAME output-frame -> source clock as the video compositor.
    // Frame index interpolation would desynchronize Foley under time warp.
    const sourceMs=frameMap[i]!.sourceMs;
    candidates.push({sourceMs,outputMs:t,
       sound:s.cues.cameraMove,gain:.35,trigger:"camera"});
    lastWhoosh=t;
  }
  const endSample=samples(outputDurationMs);
  const ordered=candidates.sort((a,b)=>a.outputMs-b.outputMs ||
    a.trigger.localeCompare(b.trigger));
  for(const item of ordered){
    // The executed beat cut and the audible transient share one 60fps
   // sample boundary: exactly 800 samples per frame, no accumulated drift.
   const quantized=preset.id==="3d-launch"
     ?Math.round(item.outputMs*preset.export.fps/1000)*(RATE/preset.export.fps)
     :samples(item.outputMs);
   const at=clamp(quantized,0,endSample-1);
    plan.cues.push({
      sound:item.sound,
      outputSample:at,outputMs:+(at/RATE*1000).toFixed(5),
      sourceMs:+item.sourceMs.toFixed(5),
      gain:item.gain,trigger:item.trigger
    });
  }
  if(s.ducking.enabled){
    const d=s.ducking;
    plan.duckIntervals=coalesceIntervals(plan.cues.map(c=>({
      startSample:Math.max(0,c.outputSample-samples(d.attackMs)),
      endSample:Math.min(endSample,c.outputSample+samples(d.releaseMs)),
      attenuationDb:d.attenuationDb,attackMs:d.attackMs,releaseMs:d.releaseMs
    })).filter(row=>row.endSample>row.startSample));
  }
  return plan;
}
