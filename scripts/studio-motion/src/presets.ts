/** Validated, versioned and fully JSON-serializable one-click Sauce flavors. */
import {SauceFlavor,SaucePreset,finite} from "./types";

const BASE:SaucePreset={
  schemaVersion:1,id:"clean-studio",label:"Clean Studio",
  camera:{
    mode:"flat",perspectivePx:1200,maxTiltDeg:0,
    scaleRange:[1,1.28],
    spring:{mass:1,stiffness:180,damping:24},
    orbit:{enabled:false,periodMs:2200,amplitudeXDeg:.13,amplitudeYDeg:.18},
    spotlight:{enabled:false,blurPx:0,dimOpacity:0}
  },
  director:{
    enabled:true,idleThresholdMs:600,idleStrategy:"hold",maxWarpSpeed:1,
    actionPreRollMs:400,actionPostRollMs:300,heroScoreThreshold:70,
    callouts:{enabled:false,cooldownMs:2500,maxLifetimeMs:1800}
  },
  stage:{floorReflectionIntensity:0,contactShadow:false,ambientShadow:false,
    backdropStyle:"obsidian-grain"},
  sound:{
    enabled:false,muted:false,masterGain:.32,musicGain:.12,
    ducking:{enabled:true,attenuationDb:-9,attackMs:35,releaseMs:220},
    cues:{click:"click_crisp",cameraMove:"whoosh_soft",modalOpen:"pop_glass"}
  },
  export:{width:1920,height:1080,fps:60}
};

const registry:Record<SauceFlavor,SaucePreset>={
  "clean-studio":BASE,
  "3d-launch":{
    ...BASE,id:"3d-launch",label:"3D Launch",
    camera:{
      mode:"perspective",perspectivePx:1200,maxTiltDeg:2.5,
      scaleRange:[1,1.36],
      spring:{mass:1,stiffness:180,damping:24},
      orbit:{enabled:false,periodMs:2200,amplitudeXDeg:.13,amplitudeYDeg:.18},
      spotlight:{enabled:true,blurPx:6,dimOpacity:.25}
    },
    director:{
      ...BASE.director,idleStrategy:"ramp",maxWarpSpeed:2.5,
      heroScoreThreshold:65,
      callouts:{enabled:true,cooldownMs:2500,maxLifetimeMs:1800}
    },
    stage:{floorReflectionIntensity:.25,contactShadow:true,ambientShadow:true,
      backdropStyle:"fluted-glass"},
    sound:{...BASE.sound,enabled:true,masterGain:.31,musicGain:.10}
  },
  "hyper-cut":{
    ...BASE,id:"hyper-cut",label:"Hyper-Cut",
    camera:{
      mode:"perspective",perspectivePx:1200,maxTiltDeg:4,
      scaleRange:[1,1.48],
      spring:{mass:1,stiffness:235,damping:28},
      orbit:{enabled:false,periodMs:2200,amplitudeXDeg:.13,amplitudeYDeg:.18},
      spotlight:{enabled:true,blurPx:4,dimOpacity:.18}
    },
    director:{
      ...BASE.director,idleStrategy:"cut",maxWarpSpeed:4,
      idleThresholdMs:600,heroScoreThreshold:60,
      callouts:{enabled:true,cooldownMs:2200,maxLifetimeMs:1400}
    },
    stage:{floorReflectionIntensity:.12,contactShadow:true,ambientShadow:true,
      backdropStyle:"chromatic-bloom"},
    sound:{...BASE.sound,enabled:true,masterGain:.36,musicGain:.08}
  }
};
export const SAUCE_FLAVORS:readonly SauceFlavor[]=["clean-studio","3d-launch","hyper-cut"] as const;

type JsonObject=Record<string,unknown>;
function plainObject(v:unknown):v is JsonObject{
  return v!==null&&typeof v==="object"&&!Array.isArray(v)
    &&(Object.getPrototypeOf(v)===Object.prototype||Object.getPrototypeOf(v)===null);
}
function copy<T>(v:T):T{return JSON.parse(JSON.stringify(v)) as T;}
function mergeKnown(base:JsonObject,override:JsonObject,path="preset"):JsonObject{
  for(const [key,value] of Object.entries(override)){
    if(key==="__proto__"||key==="constructor"||key==="prototype"||
       !Object.prototype.hasOwnProperty.call(base,key))
      throw new Error("Unknown preset field: "+path+"."+key);
    const previous=base[key];
    if(plainObject(previous)&&plainObject(value))
      base[key]=mergeKnown({...previous},value,path+"."+key);
    else base[key]=value;
  }
  return base;
}
function range(n:unknown,min:number,max:number,name:string):number{
  if(!finite(n)||n<min||n>max)throw new Error("Invalid "+name);
  return n;
}
export function validatePreset(input:SaucePreset):SaucePreset{
  if(!plainObject(input)||input.schemaVersion!==1||
     !SAUCE_FLAVORS.includes(input.id)||
     typeof input.label!=="string"||input.label.length>40)
    throw new Error("Invalid SaucePreset schema/version/id");
  const c=input.camera,d=input.director,s=input.stage,f=input.sound,e=input.export;
  if(!c||!d||!s||!f||!e)throw new Error("Incomplete SaucePreset");
  if(c.mode!=="flat"&&c.mode!=="perspective")throw new Error("Invalid camera mode");
  range(c.perspectivePx,600,3000,"perspectivePx");
  range(c.maxTiltDeg,0,6,"maxTiltDeg");
  if(!Array.isArray(c.scaleRange)||c.scaleRange.length!==2)throw new Error("Invalid scaleRange");
  range(c.scaleRange[0],.8,2,"scaleRange[0]");
  range(c.scaleRange[1],c.scaleRange[0],2,"scaleRange[1]");
  range(c.spring.mass,.1,5,"spring.mass");
  range(c.spring.stiffness,20,600,"spring.stiffness");
  range(c.spring.damping,0,100,"spring.damping");
  if(typeof c.orbit?.enabled!=="boolean")throw new Error("Invalid orbital flag");
  range(c.orbit.periodMs,800,8000,"orbit.periodMs");
  range(c.orbit.amplitudeXDeg,0,.35,"orbit.amplitudeXDeg");
  range(c.orbit.amplitudeYDeg,0,.35,"orbit.amplitudeYDeg");
  if(typeof c.spotlight.enabled!=="boolean")throw new Error("Invalid spotlight");
  range(c.spotlight.blurPx,0,24,"spotlight.blurPx");
  range(c.spotlight.dimOpacity,0,.7,"spotlight.dimOpacity");
  if(!["hold","ramp","cut"].includes(d.idleStrategy)||typeof d.enabled!=="boolean")
    throw new Error("Invalid director");
  range(d.idleThresholdMs,300,10000,"idleThresholdMs");
  range(d.maxWarpSpeed,1,4,"maxWarpSpeed");
  range(d.actionPreRollMs,0,1500,"actionPreRollMs");
  range(d.actionPostRollMs,0,1500,"actionPostRollMs");
  range(d.heroScoreThreshold,0,100,"heroScoreThreshold");
  if(typeof d.callouts.enabled!=="boolean")throw new Error("Invalid callout enabled");
  range(d.callouts.cooldownMs,0,30000,"callouts.cooldownMs");
  range(d.callouts.maxLifetimeMs,100,1800,"callouts.maxLifetimeMs");
  range(s.floorReflectionIntensity,0,.5,"floorReflectionIntensity");
  if(typeof s.contactShadow!=="boolean"||typeof s.ambientShadow!=="boolean")
    throw new Error("Invalid shadows");
  if(!["obsidian-grain","fluted-glass","chromatic-bloom"].includes(s.backdropStyle))
    throw new Error("Invalid backdropStyle");
  if(typeof f.enabled!=="boolean"||typeof f.muted!=="boolean"||
     typeof f.ducking.enabled!=="boolean")throw new Error("Invalid audio toggles");
  range(f.masterGain,0,1,"masterGain");
  range(f.musicGain,0,1,"musicGain");
  range(f.ducking.attenuationDb,-24,0,"attenuationDb");
  range(f.ducking.attackMs,0,1000,"ducking.attackMs");
  range(f.ducking.releaseMs,0,3000,"ducking.releaseMs");
  if(f.cues.click!=="click_crisp"||f.cues.cameraMove!=="whoosh_soft"||
     f.cues.modalOpen!=="pop_glass")throw new Error("Invalid cue identifiers");
  if(!Number.isInteger(e.width)||!Number.isInteger(e.height)||
     e.width<640||e.width>3840||e.height<360||e.height>2160||
     ![24,30,60].includes(e.fps))
    throw new Error("Unsupported export dimensions or fps");
  if(e.width*9!==e.height*16)throw new Error("Preset must export 16:9");
  return input;
}
/** Deep override only known keys; does not mutate the registry or accept extra fields. */
export function resolvePreset(id:SauceFlavor="clean-studio",
   overrides?:Record<string,unknown>):SaucePreset{
  if(!SAUCE_FLAVORS.includes(id))throw new Error("Unknown Sauce flavor");
  const base=copy(registry[id]);
  if(overrides){
    if(!plainObject(overrides))throw new Error("Preset overrides must be an object");
    const updated=mergeKnown(base as unknown as JsonObject,overrides) as unknown as SaucePreset;
    if(updated.id!==id||updated.schemaVersion!==1)throw new Error("Preset identity cannot change");
    return validatePreset(updated);
  }
  return validatePreset(base);
}
