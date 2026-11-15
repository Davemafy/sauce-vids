/** Main renderer bridge: input JSON from Python stdin -> deterministic plan JSON. */
import {readFileSync} from "node:fs";
import {DEFAULT_STUDIO_CONFIG,TraceEvent,StudioMotionConfig,StudioPlan,finite} from "./types";
import {buildTimeWarp} from "./timeWarp";
import {buildCallouts} from "./KineticCallouts";
import {createStudioStage} from "./StudioStage";
export interface BridgeInput {events:TraceEvent[];startMs:number;durationMs:number;fps:number;config:Partial<StudioMotionConfig>}
export function buildStudioPlan(input:BridgeInput):StudioPlan{
  const c={...DEFAULT_STUDIO_CONFIG,...input.config};
  if(!Number.isInteger(c.calloutCooldownMs)||c.calloutCooldownMs<0)throw new Error("Invalid calloutCooldownMs");
  const floor=createStudioStage(c.floorReflectionIntensity);
  const time=buildTimeWarp(input.events,input.startMs,input.durationMs,input.fps,c.maxWarpSpeed,c.enableTimeWarp);
  const callouts=buildCallouts(input.events,input.startMs,time.sourceToOutput,
    {cooldownMs:c.calloutCooldownMs,lifetimeMs:c.maxCalloutLifetimeMs,enable:c.enableCallouts});
  return {schema:"sauce-studio-motion-v1",fps:input.fps,sourceDurationMs:input.durationMs,
    outputDurationMs:time.outputDurationMs,frameMap:time.frameMap,
    actionWindows:time.actionWindows,deadZones:time.deadZones,callouts,
    stage:{width:floor.width,height:floor.height,window:floor.window,
       reflectionIntensity:floor.reflectionIntensity,enabled:c.enableStudioFloor},config:c};
}
// Real Node stdout stays JSON-only; any diagnostic is written to stderr.
if(require.main===module){
  try{
    const src=readFileSync(0,"utf8");
    const input=JSON.parse(src) as BridgeInput;
    if(!Array.isArray(input.events)||!finite(input.fps))throw new Error("Malformed bridge trace");
    process.stdout.write(JSON.stringify(buildStudioPlan(input)));
  }catch(err){
    process.stderr.write(String(err)+"\n");process.exitCode=1;
  }
}
