/** Unified deterministic bridge. Legacy v1 contract stays backward-compatible.
 * When an explicit preset is selected, include the new FramePlan + FoleyPlan.
 */
import {readFileSync} from "node:fs";
import {
 DEFAULT_STUDIO_CONFIG,TraceEvent,StudioMotionConfig,StudioPlan,
 SauceFlavor,SaucePreset,SauceMotionPlan,finite
} from "./types";
import {buildTimeWarp} from "./timeWarp";
import {buildCallouts} from "./KineticCallouts";
import {createStudioStage} from "./StudioStage";
import {resolvePreset,SAUCE_FLAVORS} from "./presets";
import {buildAutoDirector} from "./autoDirector";
import {buildFoleyPlan} from "./foleyPlan";

export interface BridgeInput {
 events:TraceEvent[];
 startMs:number;
 durationMs:number;
 fps:number;
 config?:Partial<StudioMotionConfig>;
 /** Absent means the legacy silent StudioMotion v1 contract is preserved. */
 preset?:SauceFlavor|SaucePreset;
 presetOverrides?:Record<string,unknown>;
}
function parsePreset(input:BridgeInput):SaucePreset{
 if(!input.preset)throw new Error("A Sauce preset must be selected");
 if(typeof input.preset==="string"){
   if(!SAUCE_FLAVORS.includes(input.preset as SauceFlavor))
     throw new Error("Unsupported Sauce flavor");
   return resolvePreset(input.preset as SauceFlavor,input.presetOverrides);
 }
 const selected=input.preset;
 if(!SAUCE_FLAVORS.includes(selected.id))
   throw new Error("Unsupported Sauce flavor");
 return resolvePreset(selected.id,selected as unknown as Record<string,unknown>);
}
function validateInput(input:BridgeInput):void{
 if(!Array.isArray(input.events)||!finite(input.startMs)||
    !finite(input.durationMs)||input.durationMs<=0||
    input.durationMs>600000||!Number.isInteger(input.fps)||
    input.fps<1||input.fps>120)throw new Error("Malformed bridge trace");
 if(!input.events.every(e=>e&&typeof e.type==="string"&&finite(e.t)))
   throw new Error("Invalid trace events");
}
export function buildMotionEnginePlan(input:BridgeInput):SauceMotionPlan{
 validateInput(input);
 const preset=parsePreset(input);
 if(preset.export.fps!==input.fps)
   throw new Error("Preset FPS must match the source/output render frame rate");
 const direction=buildAutoDirector(input.events,input.startMs,input.durationMs,preset);
 const foley=buildFoleyPlan(input.events,input.startMs,input.durationMs,
   direction.framePlan.outputDurationMs,direction.timeWarp.sourceToOutput,
   preset,direction.framePlan.frames.map(f=>f.camera),
   direction.framePlan.frames.map(f=>({sourceMs:f.sourceMs,speed:f.speed})));
 return {schema:"sauce-motion-plan-v1",preset,
   framePlan:direction.framePlan,foleyPlan:foley};
}
export function buildStudioPlan(input:BridgeInput):StudioPlan{
 validateInput(input);
 // The initial rollout is opt-in. Existing Python v1 consumers continue
 // receiving their original layout, time map and silent audio semantics.
 if(input.preset!==undefined){
   const motion=buildMotionEnginePlan(input);
   const preset=motion.preset,frame=motion.framePlan;
   const floor=createStudioStage(preset.stage.floorReflectionIntensity);
   return {
     schema:"sauce-studio-motion-v1",
     fps:input.fps,sourceDurationMs:input.durationMs,
     outputDurationMs:frame.outputDurationMs,
     frameMap:frame.frames.map(f=>({sourceMs:f.sourceMs,speed:f.speed})),
     actionWindows:frame.actionWindows,deadZones:frame.deadZones,
     callouts:frame.callouts,
     stage:{width:floor.width,height:floor.height,window:floor.window,
       reflectionIntensity:floor.reflectionIntensity,
       enabled:preset.stage.floorReflectionIntensity>0},
     config:{
       enableTimeWarp:preset.director.enabled&&preset.director.idleStrategy!=="hold",
       maxWarpSpeed:preset.director.maxWarpSpeed,
       enableStudioFloor:preset.stage.floorReflectionIntensity>0,
       floorReflectionIntensity:preset.stage.floorReflectionIntensity,
       enableCallouts:preset.director.callouts.enabled,
       calloutCooldownMs:preset.director.callouts.cooldownMs,
       maxCalloutLifetimeMs:preset.director.callouts.maxLifetimeMs
     },
     motionEngine:motion
   };
 }
 const c={...DEFAULT_STUDIO_CONFIG,...input.config};
 if(!Number.isInteger(c.calloutCooldownMs)||c.calloutCooldownMs<0)
   throw new Error("Invalid calloutCooldownMs");
 const floor=createStudioStage(c.floorReflectionIntensity);
 const time=buildTimeWarp(input.events,input.startMs,input.durationMs,
   input.fps,c.maxWarpSpeed,c.enableTimeWarp);
 const callouts=buildCallouts(input.events,input.startMs,time.sourceToOutput,
   {cooldownMs:c.calloutCooldownMs,
    lifetimeMs:c.maxCalloutLifetimeMs,enable:c.enableCallouts});
 return {
   schema:"sauce-studio-motion-v1",fps:input.fps,
   sourceDurationMs:input.durationMs,outputDurationMs:time.outputDurationMs,
   frameMap:time.frameMap,actionWindows:time.actionWindows,
   deadZones:time.deadZones,callouts,
   stage:{width:floor.width,height:floor.height,window:floor.window,
     reflectionIntensity:floor.reflectionIntensity,enabled:c.enableStudioFloor},
   config:c
 };
}
// Stdout is JSON only. Diagnostics/errors are emitted to stderr.
if(require.main===module){
 try{
   const input=JSON.parse(readFileSync(0,"utf8")) as BridgeInput;
   process.stdout.write(JSON.stringify(buildStudioPlan(input)));
 }catch(err){
   process.stderr.write(String(err)+"\n");process.exitCode=1;
 }
}
