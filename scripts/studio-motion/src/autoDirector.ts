/** Evidence-first director. Plans shots; never fabricates source UI actions.
 * The "cut" strategy emits cut-candidates in Phase 1, not silent time jumps.
 */
import {
  EditDecision,HeroMoment,SauceFramePlan,SaucePreset,TraceEvent,
  finite,Rect,DiffReveal,CommitDiff,clamp
} from "./types";
import {buildTimeWarp,TimeWarpPlan} from "./timeWarp";
import {planCameraRig} from "./cameraRig";
import {buildCallouts} from "./KineticCallouts";

function kind(e:TraceEvent):string{
  return (e.eventType||e.type).toLowerCase().replaceAll("_","-");
}
function validBox(b:Rect|null|undefined):b is Rect{
  return !!b&&[b.x,b.y,b.width,b.height].every(finite)&&
    b.width>=2&&b.height>=2;
}
const PRIVATE=/password|secret|api.?key|token|credit.?card|otp|[\w.+-]+@[\w.-]+\.[a-z]{2,}/i;
function safeCommit(value:CommitDiff|undefined):CommitDiff|null {
  if(!value || typeof value!=="object" || !/^[a-f0-9]{7,40}$/i.test(value.sha) ||
    typeof value.file!=="string" || !/^[A-Za-z0-9_.\/-]{1,140}$/.test(value.file) ||
    value.file.includes("..") || typeof value.title!=="string" ||
    !Array.isArray(value.lines) || value.lines.length<1 || value.lines.length>16)
    return null;
  const secret=/(?:secret|password|token|api.?key|private.?key|authorization|[\w.+-]+@[\w.-]+\.[a-z]{2,})/i;
  const lines=value.lines;
  if(lines.some(line=>typeof line!=="string" || line.length>160 ||
    !/^[ +\-@]/.test(line) || secret.test(line) || /[\x00-\x08\x0B-\x1F]/.test(line)))return null;
  if(value.title.length>72 || secret.test(value.title))return null;
  return {sha:value.sha.toLowerCase(),file:value.file,title:value.title,
          lines:lines.slice()};
}
function safeLabel(e:TraceEvent):string|null{
  const raw=e.ariaLabel||e.innerText;
  if(!raw||PRIVATE.test(raw))return null;
  const trimmed=raw.replace(/\s+/g," ").trim();
  if(trimmed.length>60||trimmed.length<2)return null;
  return trimmed.split(" ").slice(0,5).join(" ");
}
function rank(e:TraceEvent):{kind:HeroMoment["kind"];score:number}|null{
  const k=kind(e);
  if(["modal-open","modal-opened","dialog-visible"].includes(k))
    return {kind:"modal",score:95};
  if(k==="feature-commit" && e.commit)return {kind:"feature",score:99};
  if(k==="submit")return {kind:"submit",score:90};
  if(k==="copy"||k==="paste")return {kind:k,score:82};
  if(k==="click"||k==="pointerdown"){
    const primary=e.tag==="button"||e.role==="button"||
      /^button(?:[:.\[]|$)/i.test(e.selector||"");
    return {kind:"click",score:primary?78:45};
  }
  return null;
}
export function detectHeroMoments(
  events:TraceEvent[],startMs:number,durationMs:number,preset:SaucePreset,
  sourceToOutput:(ms:number)=>number
):HeroMoment[]{
  if(!preset.director.enabled)return [];
  const ordered=[...events].filter(e=>finite(e.t))
    .sort((a,b)=>a.t-b.t);
  const heroes:HeroMoment[]=[];
  for(let i=0;i<ordered.length;i++){
    const event=ordered[i]!,found=rank(event);
    if(found?.kind==="feature" && !safeCommit(event.commit))continue;
    if(!found||found.score<preset.director.heroScoreThreshold)continue;
    const t=event.t-startMs;
    if(t<0||t>durationMs)continue;
    // The real "click" follows "pointerdown" by milliseconds. Keep one
    // moment at the actual initial press rather than inventing two shots.
    if(kind(event)==="click"){
      const prior=ordered.slice(Math.max(0,i-5),i).find(e=>
        kind(e)==="pointerdown"&&Math.abs(event.t-e.t)<=160&&
        (e.selector===event.selector||
         (validBox(e.box)&&validBox(event.box)&&
         Math.abs(e.box.x-event.box.x)<4&&Math.abs(e.box.y-event.box.y)<4)));
      if(prior)continue;
    }
    const previous=heroes[heroes.length-1];
    if(previous&&previous.kind===found.kind&&Math.abs(t-previous.sourceMs)<135)
      continue;
    const mapped=sourceToOutput(t);
    if(!finite(mapped))throw new Error("Invalid director output timestamp");
    heroes.push({
      id:"hero-"+heroes.length,
      kind:found.kind,
      sourceMs:+t.toFixed(4),
      outputMs:+mapped.toFixed(4),
      score:found.score,
      box:validBox(event.box)?{...event.box}:null,
      label:safeLabel(event)
    });
  }
  return heroes;
}
export const MODAL_FOREGROUND_LIFETIME_MS=2400;
const MODAL_CLOSE_TYPES=new Set(["dialog-hidden","dialog-closed","modal-close","modal-closed"]);
export interface AutoDirectorResult{
  framePlan:SauceFramePlan;
  timeWarp:TimeWarpPlan;
}
export function buildAutoDirector(
  events:TraceEvent[],startMs:number,durationMs:number,preset:SaucePreset,
  viewport:{width:number;height:number}={width:1280,height:720}
):AutoDirectorResult{
  const d=preset.director;
  const applyWarp=d.enabled&&d.idleStrategy!=="hold"&&d.maxWarpSpeed>1;
  const warp=buildTimeWarp(events,startMs,durationMs,preset.export.fps,
    d.maxWarpSpeed,applyWarp,{
      idleThresholdMs:d.idleThresholdMs,
      actionPreRollMs:d.actionPreRollMs,
      actionPostRollMs:d.actionPostRollMs
    });
  const hero=detectHeroMoments(events,startMs,durationMs,preset,warp.sourceToOutput);
  const diffs:DiffReveal[]=[];
  for(const event of [...events].sort((a,b)=>a.t-b.t)){
    if((event.eventType||event.type).toLowerCase().replaceAll("_","-")!=="feature-commit")continue;
    const commit=safeCommit(event.commit),sourceMs=event.t-startMs;
    if(!commit || !finite(sourceMs) || sourceMs<0 || sourceMs>durationMs ||
       !hero.some(h=>h.kind==="feature"&&Math.abs(h.sourceMs-sourceMs)<.001))continue;
    const outputMs=warp.sourceToOutput(sourceMs);
    diffs.push({...commit,id:"diff-"+diffs.length,sourceMs,outputMs,
      durationMs:Math.max(0,Math.min(2100,warp.outputDurationMs-outputMs))});
  }
  const camera=planCameraRig(warp.frameMap,hero,events,preset,startMs,viewport);
  const approvedEvents=events.filter(e=>hero.some(h=>Math.abs(h.sourceMs-(e.t-startMs))<.001));
  const callouts=buildCallouts(approvedEvents,startMs,warp.sourceToOutput,{
    enable:d.enabled&&d.callouts.enabled,
    cooldownMs:d.callouts.cooldownMs,
    lifetimeMs:d.callouts.maxLifetimeMs
  });
  const closingEvents=events.filter(e=>finite(e.t) &&
    MODAL_CLOSE_TYPES.has(kind(e))).map(e=>e.t-startMs).sort((a,b)=>a-b);
  const modalHeroes=hero.filter(h=>h.kind==="modal");
  const cuts:EditDecision[]=warp.deadZones.map(g=>({
    // Cut-candidates are metadata until a cut-safe renderer exists.
    kind:d.idleStrategy==="cut"?"cut-candidate":"ramp",
    sourceStartMs:g.start,sourceEndMs:g.end,speedCap:d.maxWarpSpeed
  }));
  const frames=warp.frameMap.map((m,i)=>{
    const diff=[...diffs].reverse().find(d=>
      i*1000/preset.export.fps>=d.outputMs &&
      i*1000/preset.export.fps<d.outputMs+d.durationMs);
    const dt=diff?i*1000/preset.export.fps-diff.outputMs:0;
    const edge=diff?Math.min(1,dt/220,(diff.durationMs-dt)/250):0;
    const diffProgress=diff?clamp(edge,0,1)**2*(3-2*clamp(edge,0,1)):0;
    const foreground=[...modalHeroes].reverse().find(h=>
      h.sourceMs<=m.sourceMs &&
      m.sourceMs-h.sourceMs<MODAL_FOREGROUND_LIFETIME_MS &&
      !closingEvents.some(t=>t>h.sourceMs&&t<=m.sourceMs));
    const active=[...hero].reverse().find(h=>h.sourceMs<=m.sourceMs
      &&m.sourceMs-h.sourceMs<(h.kind==="modal"?MODAL_FOREGROUND_LIFETIME_MS:1800)
      &&!(h.kind==="modal"&&closingEvents.some(t=>t>h.sourceMs&&t<=m.sourceMs)));
    return {
      outputFrame:i,
      outputTimeMs:+(i*1000/preset.export.fps).toFixed(5),
      sourceMs:m.sourceMs,speed:m.speed,camera:camera[i]!,
      heroId:active?.id||null,
      foregroundId:foreground?.id||null,
      diffId:diff?.id||null,diffProgress:+diffProgress.toFixed(5)
    };
  });
  return {
    framePlan:{
      schema:"sauce-frame-plan-v1",presetId:preset.id,
      fps:preset.export.fps,sourceDurationMs:durationMs,
      outputDurationMs:warp.outputDurationMs,
      frames,actionWindows:warp.actionWindows,deadZones:warp.deadZones,
      heroMoments:hero,editDecisions:cuts,callouts,diffReveals:diffs
    },
    timeWarp:warp
  };
}
