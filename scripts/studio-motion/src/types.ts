/** Shared contracts. Browser evidence is treated as untrusted; redact at capture. */
export interface Rect { x:number; y:number; width:number; height:number }
export interface CommitDiff {
  sha:string;
  file:string;
  title:string;
  lines:string[];
}
export interface AttentionEvidence {
  score:number;
  flow:number;
}
export interface DiffReveal extends CommitDiff {
  id:string;
  sourceMs:number;
  outputMs:number;
  durationMs:number;
}
export interface TraceEvent {
  t:number;
  type:string;
  eventType?:string;
  x?:number|null;
  y?:number|null;
  redacted?:boolean;
  selector?:string;
  tag?:string;
  role?:string;
  ariaLabel?:string;
  innerText?:string;
  box?:Rect|null;
  scroll?:{x:number;y:number};
  durationMs?:number;
  isInitial?:boolean;
  isLoading?:boolean;
  scrollMode?:"static"|"animated";
  /** Optional trusted screenshot-derived gaze proposal, not a cursor target. */
  attention?:AttentionEvidence;
  /** Optional verified, sanitized and explicitly supplied local Git evidence. */
  commit?:CommitDiff;
}
export interface StudioMotionConfig {
  enableTimeWarp:boolean;
  maxWarpSpeed:number;
  enableStudioFloor:boolean;
  floorReflectionIntensity:number;
  enableCallouts:boolean;
  calloutCooldownMs:number;
  maxCalloutLifetimeMs:number;
}
export const DEFAULT_STUDIO_CONFIG:StudioMotionConfig={
  enableTimeWarp:false,
  maxWarpSpeed:4,
  enableStudioFloor:false,
  floorReflectionIntensity:0.25,
  enableCallouts:false,
  calloutCooldownMs:2500,
  maxCalloutLifetimeMs:1800,
};
export interface FrameMap { sourceMs:number; speed:number }
export interface MappedCallout { text:string; sourceStartMs:number; outputStartMs:number; outputEndMs:number; box:Rect; kind:string }
export interface StudioPlan {
  schema:"sauce-studio-motion-v1";
  fps:number;
  sourceDurationMs:number;
  outputDurationMs:number;
  frameMap:FrameMap[];
  actionWindows:{start:number;end:number}[];
  deadZones:{start:number;end:number}[];
  callouts:MappedCallout[];
  stage:{width:number;height:number;window:{x:number;y:number;width:number;height:number};reflectionIntensity:number;enabled:boolean};
  config:StudioMotionConfig;
  motionEngine?:SauceMotionPlan;
}
export function finite(v:unknown):v is number { return typeof v==="number"&&Number.isFinite(v) }
export function clamp(v:number,a:number,b:number):number {return Math.min(b,Math.max(a,v))}


/** Sauce Motion Engine v1: all objects are deterministic JSON values.
 * Rendering adapters consume this contract; no JSX or audio asset needed.
 */
export type SauceFlavor = "clean-studio" | "3d-launch" | "hyper-cut";
export type FoleySound = "click_crisp" | "whoosh_soft" | "pop_glass";
export type IdleStrategy = "hold" | "ramp" | "cut";
export interface SpringPhysics {stiffness:number;damping:number;mass:number}
export interface SaucePreset {
  schemaVersion:1;
  id:SauceFlavor;
  label:string;
  camera:{
    mode:"flat"|"perspective";
    perspectivePx:number;
    maxTiltDeg:number;
    scaleRange:[number,number];
    spring:SpringPhysics;
    spotlight:{enabled:boolean;blurPx:number;dimOpacity:number};
  };
  director:{
    enabled:boolean;
    idleThresholdMs:number;
    idleStrategy:IdleStrategy;
    maxWarpSpeed:number;
    actionPreRollMs:number;
    actionPostRollMs:number;
    heroScoreThreshold:number;
    callouts:{enabled:boolean;cooldownMs:number;maxLifetimeMs:number};
  };
  stage:{
    floorReflectionIntensity:number;
    contactShadow:boolean;
    ambientShadow:boolean;
  };
  sound:{
    enabled:boolean;
    muted:boolean;
    masterGain:number;
    musicGain:number;
    ducking:{
      enabled:boolean;attenuationDb:number;attackMs:number;releaseMs:number;
    };
    cues:{click:"click_crisp";cameraMove:"whoosh_soft";modalOpen:"pop_glass"};
  };
  export:{width:number;height:number;fps:number};
}
export interface CameraPose {
  scale:number;
  focusX:number;
  focusY:number;
  rotateXDeg:number;
  rotateYDeg:number;
  perspectivePx:number;
  spotlightActive:boolean;
  spotlightBox:Rect|null;
  spotlightBlurPx:number;
  spotlightDimOpacity:number;
}
export interface HeroMoment {
  id:string;
  kind:"click"|"modal"|"submit"|"copy"|"paste"|"feature";
  sourceMs:number;
  outputMs:number;
  score:number;
  box:Rect|null;
  label:string|null;
}
export interface EditDecision {
  kind:"hold"|"ramp"|"cut-candidate"|"cut";
  outputFrame?:number;
  sourceStartMs:number;
  sourceEndMs:number;
  speedCap:number;
}
export interface FrameInstruction {
  outputFrame:number;
  outputTimeMs:number;
  sourceMs:number;
  speed:number;
  camera:CameraPose;
  heroId:string|null;
  /** Evidence-backed modal plane owner, null after close/expiry. */
  foregroundId?:string|null;
  diffId?:string|null;
  diffProgress?:number;
}
export interface SauceFramePlan {
  schema:"sauce-frame-plan-v1";
  presetId:SauceFlavor;
  fps:number;
  sourceDurationMs:number;
  outputDurationMs:number;
  frames:FrameInstruction[];
  actionWindows:{start:number;end:number}[];
  deadZones:{start:number;end:number}[];
  heroMoments:HeroMoment[];
  editDecisions:EditDecision[];
  diffReveals?:DiffReveal[];
  callouts:MappedCallout[];
}
export interface FoleyCue {
  sound:FoleySound;
  sourceMs:number;
  outputMs:number;
  outputSample:number;
  gain:number;
  trigger:"click"|"modal"|"camera";
}
export interface FoleyDuck {
  startSample:number;
  endSample:number;
  attenuationDb:number;
  attackMs:number;
  releaseMs:number;
}
export interface FoleyPlan {
  schema:"sauce-foley-plan-v1";
  sampleRate:48000;
  durationMs:number;
  muted:boolean;
  masterGain:number;
  musicGain:number;
  cues:FoleyCue[];
  duckIntervals:FoleyDuck[];
}
export interface SauceMotionPlan {
  schema:"sauce-motion-plan-v1";
  preset:SaucePreset;
  framePlan:SauceFramePlan;
  foleyPlan:FoleyPlan;
}
