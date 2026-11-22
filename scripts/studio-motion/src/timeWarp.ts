/** Monotonic offline time remapping, rather than changing wall-clock playback rate.
 * Protected windows have exactly 1x source speed; idle spans use cubic Hermite
 * ramps with zero slope at both boundaries. Source time never runs backward.
 */
import {TraceEvent,FrameMap,clamp,finite} from "./types";
export interface Interval {start:number;end:number}
export interface GazeTarget {sourceMs:number;x:number;y:number;score:number;flow:number}
/** Screen-space visual evidence is optional; never infer a target from cursor alone. */
export function visualGazeTargets(events:TraceEvent[],startMs:number,durationMs:number):GazeTarget[]{
  const targets:GazeTarget[]=[];
  for(const e of events){
    const a=e.attention;
    if(!a || !finite(e.t) || !finite(e.x) || !finite(e.y) ||
       !finite(a.score) || !finite(a.flow) || a.score<.3 || a.score>1 ||
       a.flow<0 || a.flow>1 || e.x<0 || e.y<0 || e.x>2560 || e.y>1440)continue;
    const t=e.t-startMs;
    if(t<0||t>durationMs)continue;
    targets.push({sourceMs:t,x:e.x,y:e.y,score:a.score,flow:a.flow});
  }
  return targets.sort((a,b)=>a.sourceMs-b.sourceMs||b.score-a.score);
}
export interface TimeWarpOptions {
  idleThresholdMs?:number;
  actionPreRollMs?:number;
  actionPostRollMs?:number;
}

export interface TimeWarpPlan {
  sourceDurationMs:number;
  outputDurationMs:number;
  frameMap:FrameMap[];
  actionWindows:Interval[];
  deadZones:Interval[];
  sourceToOutput:(t:number)=>number;
  gazeTargets:GazeTarget[];
  cuts?:BeatCut[];
}
function kindOf(e:TraceEvent):string{return (e.eventType||e.type||"").toLowerCase().replaceAll("_","-")}
export function isHighIntent(e:TraceEvent):boolean {
  const k=kindOf(e);
  // Existing film-plan editor may protect a verified RESULT and its reading
  // hold, not only the initiating click. The caller must have independently
  // admitted the source-bound outcome; never trust an unverified model marker.
  if(k==="verified-result")return e.verifiedSource===true;
  if (["click","pointerdown","submit","modal-open","dialog-visible","modal-opened","copy","paste"].includes(k))return true;
  if (["focus","focusin"].includes(k))return e.isInitial===true ||
    (e.isInitial!==false && (e.role==="textbox" || e.tag==="input" || e.tag==="textarea"));
  return false;
}
function unify(rows:Interval[]):Interval[]{
  const sorted=rows.filter(r=>r.end>r.start).sort((a,b)=>a.start-b.start);
  const out:Interval[]=[];
  for(const r of sorted){
    const last=out[out.length-1];
    if(last&&r.start<=last.end)last.end=Math.max(last.end,r.end);
    else out.push({...r});
  }
  return out;
}
function smoothstep(u:number):number{
  const t=clamp(u,0,1);return t*t*(3-2*t);
}
function sourceSpeed(t:number,dead:Interval[],maxSpeed:number):number {
  const d=dead.find(g=>t>=g.start && t<=g.end);
  if(!d)return 1;
  const duration=d.end-d.start;
  const ramp=Math.min(360,duration*.28);
  const head=smoothstep((t-d.start)/ramp);
  const tail=smoothstep((d.end-t)/ramp);
  // cubic Hermite at both boundaries, 1x exactly before protected actions
  return 1+(maxSpeed-1)*Math.min(head,tail);
}
export function buildTimeWarp(events:TraceEvent[],startMs:number,
 sourceDurationMs:number,fps:number,maxWarpSpeed=4,enabled=true,
 options:TimeWarpOptions={}):TimeWarpPlan{
  if(!finite(startMs)||!finite(sourceDurationMs)||sourceDurationMs<=0||sourceDurationMs>600000)
    throw new Error("Invalid source duration or trace origin");
  if(!finite(fps)||fps<1||fps>120)throw new Error("FPS outside supported interval");
  if(!finite(maxWarpSpeed)||maxWarpSpeed<1||maxWarpSpeed>4)throw new Error("maxWarpSpeed must be 1–4");
  const idle=options.idleThresholdMs??800;
  const preroll=options.actionPreRollMs??400;
  const postroll=options.actionPostRollMs??300;
  if(![idle,preroll,postroll].every(finite)||idle<200||idle>10000||
     preroll<0||preroll>1500||postroll<0||postroll>1500)
    throw new Error("Invalid temporal director thresholds");
  // Only initial focus for each target is an action. Later refocus must
  // not keep dead zones locked at 1x forever.
  const firstFocus=new Set<string>();
  const intents=events.filter(e=>finite(e.t)&&isHighIntent(e))
    .sort((a,b)=>a.t-b.t).filter(e=>{
      const kind=kindOf(e);
      if(kind!=="focus"&&kind!=="focusin")return true;
      const key=e.selector || e.ariaLabel ||
        JSON.stringify([e.tag,e.role,e.box?.x,e.box?.y]);
      if(firstFocus.has(key))return false;
      firstFocus.add(key);
      return true;
    });
  const gazeTargets=visualGazeTargets(events,startMs,sourceDurationMs);
  const locks=unify([...intents.map(e=>({
    start:clamp(e.t-startMs-preroll,0,sourceDurationMs),
    end:clamp(e.t-startMs+postroll,0,sourceDurationMs),
  })),...gazeTargets.filter(g=>g.score>=.65&&g.flow>=.20).map(g=>({
    start:clamp(g.sourceMs-100,0,sourceDurationMs),
    end:clamp(g.sourceMs+190,0,sourceDurationMs)
  }))]);
  let cursor=0;const gaps:Interval[]=[];
  for(const protectedWindow of locks){
    if(protectedWindow.start-cursor>idle)gaps.push({start:cursor,end:protectedWindow.start});
    cursor=Math.max(cursor,protectedWindow.end);
  }
  if(sourceDurationMs-cursor>idle)gaps.push({start:cursor,end:sourceDurationMs});
  // Explicitly observed loading states and continuous static scrolls are
  // compressible even when shorter than 800ms. They NEVER override action
  // windows, and must have a trustworthy start and duration in the trace.
  const evidence=events.filter(e=>finite(e.t)&&finite(e.durationMs)
    && (e.durationMs??0)>=180 && (
      ["loading","loading-state","loading_start"].includes(kindOf(e))
      ||e.isLoading===true || (kindOf(e)==="scroll"&&e.scrollMode==="static")
    )).map(e=>({
      start:clamp(e.t-startMs,0,sourceDurationMs),
      end:clamp(e.t-startMs+(e.durationMs??0),0,sourceDurationMs)
    }));
  // Also derive continuous static scroll intervals directly from captured
  // scroll samples; no special client instrumentation is required. This
  // groups real wheel movement, never click/submit focus windows.
  const rawScrolls=events.filter(e=>kindOf(e)==="scroll"&&e.scroll
    &&finite(e.scroll.x)&&finite(e.scroll.y)&&finite(e.t))
    .sort((a,b)=>a.t-b.t);
  const scrollRuns:Interval[]=[];
  let runStart=0;
  function finishRun(endIndex:number):void{
    if(endIndex-runStart<3)return;
    const begin=rawScrolls[runStart]!,end=rawScrolls[endIndex]!;
    const duration=end.t-begin.t;
    const traveled=Math.hypot((end.scroll?.x??0)-(begin.scroll?.x??0),
                              (end.scroll?.y??0)-(begin.scroll?.y??0));
    if(duration>=350&&traveled>=75)
      scrollRuns.push({start:clamp(begin.t-startMs,0,sourceDurationMs),
                       end:clamp(end.t-startMs,0,sourceDurationMs)});
  }
  for(let i=1;i<rawScrolls.length;i++){
    const previous=rawScrolls[i-1]!,current=rawScrolls[i]!;
    if(current.t-previous.t>180){
      finishRun(i-1);
      runStart=i;
    }
  }
  if(rawScrolls.length)finishRun(rawScrolls.length-1);
  const candidates=unify([...gaps,...evidence,...scrollRuns]);
  let pieces:Interval[]=candidates;
  for(const guard of locks){
    const next:Interval[]=[];
    for(const piece of pieces){
      if(piece.end<=guard.start||piece.start>=guard.end){next.push(piece);continue;}
      if(guard.start>piece.start)next.push({start:piece.start,end:guard.start});
      if(guard.end<piece.end)next.push({start:guard.end,end:piece.end});
    }
    pieces=next;
  }
  const dead=enabled&&maxWarpSpeed>1?pieces.filter(x=>x.end-x.start>=180):[];
  const step=8;const source=[0],output=[0];
  let t=0,total=0;
  while(t<sourceDurationMs-1e-8){
    const next=Math.min(sourceDurationMs,t+step);
    const dt=next-t;
    const v1=sourceSpeed(t,dead,maxWarpSpeed);
    const v2=sourceSpeed(next,dead,maxWarpSpeed);
    total+=dt*(1/v1+1/v2)*.5;
    source.push(next);output.push(total);t=next;
  }
  function invert(outMs:number):number{
    const x=clamp(outMs,0,total);
    let lo=0,hi=output.length-1;
    while(lo+1<hi){const m=(lo+hi)>>1; if((output[m]??0)<x)lo=m;else hi=m;}
    const a=output[lo]??0,b=output[hi]??total;
    const frac=(b-a)>1e-9?(x-a)/(b-a):0;
    return (source[lo]??0)+((source[hi]??sourceDurationMs)-(source[lo]??0))*frac;
  }
  function sourceToOutput(srcMs:number):number{
    const x=clamp(srcMs,0,sourceDurationMs);
    let lo=0,hi=source.length-1;
    while(lo+1<hi){const m=(lo+hi)>>1;if((source[m]??0)<x)lo=m;else hi=m;}
    const a=source[lo]??0,b=source[hi]??sourceDurationMs;
    const u=b>a?(x-a)/(b-a):0;
    return (output[lo]??0)+u*((output[hi]??total)-(output[lo]??0));
  }
  const count=Math.max(1,Math.ceil(total*fps/1000));
  const frameMap:FrameMap[]=[];
  for(let i=0;i<count;i++){
    const s=invert(i*1000/fps);
    frameMap.push({sourceMs:+s.toFixed(5),speed:+sourceSpeed(s,dead,maxWarpSpeed).toFixed(5)});
  }
  for(let i=1;i<count;i++)if(frameMap[i]!.sourceMs<=frameMap[i-1]!.sourceMs)
    throw new Error("Time map is not strictly increasing at requested fps");
  return {sourceDurationMs,outputDurationMs:+total.toFixed(5),
          frameMap,actionWindows:locks,deadZones:dead,sourceToOutput,gazeTargets};
}


/** A real edit list, not a promise to cut someday.
 * Source frames outside evidence-backed action beats are omitted. A cut also
 * creates a distinct camera shot if the source frames are adjacent.
 */
export interface BeatCut {
  outputFrame:number;
  sourceStartMs:number;
  sourceEndMs:number;
}
export interface BeatLockedWarp extends TimeWarpPlan { cuts:BeatCut[] }

export function beatLockTimeWarp(
  base:TimeWarpPlan,events:TraceEvent[],startMs:number,fps:number
):BeatLockedWarp {
  if(fps!==60)throw new Error("Beat locking requires the 60fps export clock");
  const source=base.frameMap;
  if(!source.length)throw new Error("Cannot beat-lock an empty capture");
  const fpsMs=1000/fps;
  const closest=(src:number):number=>{
    let lo=0,hi=source.length;
    while(lo<hi){const mid=(lo+hi)>>1;
      if(source[mid]!.sourceMs<src)lo=mid+1;else hi=mid;
    }
    // Land on the first actually displayed post-event source frame.
    return Math.min(source.length-1,lo);
  };
  const relevant=events.filter(e=>finite(e.t)&&isHighIntent(e)
    &&e.t-startMs>=0&&e.t-startMs<=base.sourceDurationMs)
    .sort((a,b)=>a.t-b.t);
  const anchors:{index:number;modal:boolean}[]=[];
  for(const e of relevant){
    const at=closest(e.t-startMs);
    const previous=anchors[anchors.length-1];
    // One human action, not separate click/pointerdown/focus shots.
    if(previous&&Math.abs(source[at]!.sourceMs-source[previous.index]!.sourceMs)<170){
      if(["dialog-visible","modal-open","modal-opened"].includes(kindOf(e)))
        previous.modal=true;
      continue;
    }
    anchors.push({index:at,modal:["dialog-visible","modal-open","modal-opened"].includes(kindOf(e))});
  }
  const chosen=new Uint8Array(source.length);
  if(anchors.length){
    for(const a of anchors){
      const start=Math.max(0,a.index-24);
      const end=Math.min(source.length,a.index+(a.modal?90:78)+1);
      for(let i=start;i<end;i++)chosen[i]=1;
    }
    // Preserve opening orientation when the first meaningful action arrives quickly.
    if(anchors[0]!.index<=60)
      for(let i=0;i<=anchors[0]!.index;i++)chosen[i]=1;
  }else{
    // No observed actions: never invent events, scrolling or endless ambience.
    for(let i=0;i<Math.min(source.length,120);i++)chosen[i]=1;
  }
  // Avoid stroboscopic microcuts in short pre-action gaps.
  let left=-1;
  for(let i=0;i<chosen.length;i++)if(chosen[i]){
    if(left>=0&&i-left<=19)
      for(let j=left+1;j<i;j++)chosen[j]=1;
    left=i;
  }
  const original:number[]=[];
  for(let i=0;i<chosen.length;i++)if(chosen[i])original.push(i);
  if(original.length===0)throw new Error("No source-true frames retained");
  const frames=original.map(i=>({...source[i]!}));
  const cutSet=new Set<number>();
  // Discontinuous source mapping: the renderer actually skips the idle frames.
  for(let i=1;i<original.length;i++)
    if(original[i]!-original[i-1]!>1)cutSet.add(i);
  const anchorFrames=anchors.map(a=>{
    let lo=0,hi=original.length;
    while(lo<hi){const m=(lo+hi)>>1;
      if(original[m]!<a.index)lo=m+1;else hi=m;}
    return Math.min(original.length-1,lo);
  });
  // Deliberate beats of 60–120 frames; NEVER exceed 150 per shot.
  const forcedCuts:number[]=[];
  let shotStart=0;
  for(const boundary of [...cutSet].sort((a,b)=>a-b).concat([original.length])){
    let end=boundary;
    while(end-shotStart>150){
      // Cuts land ON an observed action, never 20 frames before its pointer.
      const choices=anchorFrames
        .filter(a=>a-shotStart>=60&&a-shotStart<=150&&end-a>=60);
      const ideal=shotStart+112;
      const next=choices.length
        ?choices.sort((a,b)=>Math.abs(a-ideal)-Math.abs(b-ideal))[0]!
        :Math.min(end-60,shotStart+120);
      if(next<=shotStart||next>=end)throw new Error("Invalid edit boundary");
      forcedCuts.push(next);shotStart=next;
    }
    shotStart=boundary;
  }
  for(const n of forcedCuts)cutSet.add(n);
  const cuts=[...cutSet].sort((a,b)=>a-b).filter(n=>n>0&&n<frames.length)
    .map(outputFrame=>({
       outputFrame,
       sourceStartMs:frames[outputFrame-1]!.sourceMs,
       sourceEndMs:frames[outputFrame]!.sourceMs
    }));
  const mapped=(src:number):number=>{
    const v=clamp(src,0,base.sourceDurationMs);
    let lo=0,hi=frames.length;
    while(lo<hi){const mid=(lo+hi)>>1;
      if(frames[mid]!.sourceMs<v)lo=mid+1;else hi=mid;
    }
    const index=Math.min(frames.length-1,lo);
    return index*fpsMs;
  };
  return {...base,frameMap:frames,cuts,
    outputDurationMs:+(frames.length*fpsMs).toFixed(5),
    sourceToOutput:mapped};
}
