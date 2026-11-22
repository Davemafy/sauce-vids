/** Source-verified temporal film editor: a small adapter to the EXISTING
 * Phase 1 beatLockTimeWarp. No browser simulation, no fabricated frames.
 * Outputs intervals of original 60Hz frames to retain and an exact event map.
 */
import {buildTimeWarp,beatLockTimeWarp} from "./timeWarp";
import {TraceEvent} from "./types";
import {readFileSync} from "node:fs";

type SourceEvent = {start:number;end?:number;t:number;evidence:string};
export interface SourceManifest {duration:number; events:SourceEvent[]}
export interface RetainedSegment {startFrame:number;endFrame:number;outputStartFrame:number}
export interface OutputEvent {
  index:number;
  sourcePressFrame:number;
  sourceResultFrame:number;
  outputPressFrame:number;
  outputResultFrame:number;
}
export interface SourceTrueRecut {
  schema:"sauce-source-true-recut-v1";
  fps:60;
  sourceFrameCount:number;
  outputFrameCount:number;
  selectedOriginalFrameCount:number;
  seconds:number;
  segments:RetainedSegment[];
  cutsOutputFrames:number[];
  events:OutputEvent[];
  sourceVerified:boolean;
  creativeApproved:false;
}

export function compileSourceTrueRecut(manifest:SourceManifest):SourceTrueRecut {
  const fps=60;
  const d=manifest?.duration;
  const events=manifest?.events;
  if(typeof d!=="number" || !Number.isFinite(d) || d<4 || d>30 ||
     Math.abs(d*fps-Math.round(d*fps))>1e-4)
    throw Error("Need original 4–30s native-60fps source duration");
  if(!Array.isArray(events)||events.length<1||events.length>4)
    throw Error("Need 1–4 real source-observed actions");
  const n=Math.round(d*fps),trace:TraceEvent[]=[];
  let lastConfirmed=0;
  for(const e of events){
    const {start,t,end}=e;
    const release=end??start+.06;
    if(![start,t,release].every(x=>typeof x==="number"&&Number.isFinite(x))||
       typeof e.evidence!=="string"||e.evidence.trim().length<8||
       start<.5||start<=lastConfirmed||release<start||
       release>t||t-release>3||t>d-0.45){
      throw Error("No source-truth-verified ordered press/release/result timing");
    }
    // Valid source-receipt "start" is a real press, never fabricated by
    // this planner. The result marker is NOT claimed to be a modal or click.
    trace.push({t:start*1000,type:"click"});
    trace.push({t:t*1000,type:"verified-result",verifiedSource:true});
    lastConfirmed=t;
  }
  // Reuse proven 60Hz timeline beat-lock engine WITHOUT speedups: every
  // output video frame is an existing distinct, monotonic source frame.
  const base=buildTimeWarp(trace,0,d*1000,fps,1,false);
  const locked=beatLockTimeWarp(base,trace,0,fps);
  const chosen=new Set<number>();
  // A measured, truthful establishing span is editorially important if the
  // first click happens after the source begins. No freeze/fictional hook.
  const opening=Math.min(42,Math.max(20,Math.floor(events[0]!.start*fps)-36));
  for(let f=0;f<opening;f++)chosen.add(f);
  for(const x of locked.frameMap){
    const f=Math.round(x.sourceMs/1000*fps);
    if(f<0||f>=n)throw Error("Out-of-bounds native source frame");
    chosen.add(f);
  }
  const frames=[...chosen].sort((a,b)=>a-b);
  if(frames.length<180 || frames.length>=n || frames.length>1800)
    throw Error("No meaningful bounded nontrivial source edit");
  const segments:RetainedSegment[]=[];
  for(let i=0;i<frames.length;i++){
    const frame=frames[i]!,previous=frames[i-1];
    if(previous!==undefined && frame<=previous)
      throw Error("Nonmonotonic source edit");
    if(previous===undefined || frame>previous+1)
      segments.push({startFrame:frame,endFrame:frame+1,outputStartFrame:i});
    else segments[segments.length-1]!.endFrame=frame+1;
  }
  // A source that already flows from one genuine action to the next does
  // NOT need forced jump cuts. Preserve it unedited instead of trimming
  // its final source hold and claiming a better film.
  if(segments.length<2)throw Error("No source-verified idle gap worth an editorial cut");
  if(segments.length>12)throw Error("Excessive rapid-cut montage");
  const index=new Map(frames.map((f,i)=>[f,i]));
  const mapped:OutputEvent[]=events.map((e,i)=>{
    const press=Math.ceil(e.start*fps-1e-8);
    const result=Math.ceil(e.t*fps-1e-8);
    const p=index.get(press),r=index.get(result);
    if(p===undefined||r===undefined||r<=p)
      throw Error("Original recorded action or result was cut");
    // Protect original action, never remove its actual on-screen interval.
    for(let f=press;f<=result;f++)
      if(index.get(f)===undefined)
        throw Error("Actual recorded interaction truncated by an edit");
    // Preserve a genuine reading hold after every resulting state.
    const end=Math.min(n-1,result+Math.ceil(.65*fps));
    for(let f=result;f<=end;f++)
      if(index.get(f)===undefined)
        throw Error("Source-verified post-result hold missing");
    return {index:i,sourcePressFrame:press,sourceResultFrame:result,
            outputPressFrame:p,outputResultFrame:r};
  });
  if(mapped.some((e,i)=>i>0&&e.outputPressFrame<=mapped[i-1]!.outputResultFrame))
    throw Error("Nonchronological user workflow");
  return {schema:"sauce-source-true-recut-v1",fps:60,
          sourceFrameCount:n,outputFrameCount:frames.length,
          selectedOriginalFrameCount:frames.length,
          seconds:+(frames.length/fps).toFixed(6),
          segments,cutsOutputFrames:segments.slice(1).map(s=>s.outputStartFrame),
          events:mapped,sourceVerified:true,creativeApproved:false};
}

if(require.main===module){
  try{
    if(process.argv.length!==3)throw Error("Usage: sourceTrueRecut manifest.json");
    const m=JSON.parse(readFileSync(process.argv[2]!,"utf8")) as SourceManifest;
    process.stdout.write(JSON.stringify(compileSourceTrueRecut(m))+"\n");
  }catch(e){
    process.stderr.write((e instanceof Error?e.message:"Invalid manifest")+"\n");
    process.exitCode=2;
  }
}

