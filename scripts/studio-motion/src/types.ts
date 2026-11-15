/** Shared contracts. Browser evidence is treated as untrusted; redact at capture. */
export interface Rect { x:number; y:number; width:number; height:number }
export interface TraceEvent {
  t:number;
  type:string;
  eventType?:string;
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
}
export function finite(v:unknown):v is number { return typeof v==="number"&&Number.isFinite(v) }
export function clamp(v:number,a:number,b:number):number {return Math.min(b,Math.max(a,v))}
