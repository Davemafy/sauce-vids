import test from "node:test";
import assert from "node:assert/strict";
import {buildTimeWarp} from "../timeWarp";
import {planCameraRig} from "../cameraRig";
import {resolvePreset} from "../presets";
import {buildCallouts} from "../KineticCallouts";
import {buildStudioPlan} from "../bridge";
import {projectAnchor,createStudioStage} from "../StudioStage";
import {TraceEvent,DEFAULT_STUDIO_CONFIG} from "../types";

const events:TraceEvent[]=[
 {t:1000,type:"click",selector:'button:has-text("Connect your agent")',box:{x:130,y:180,width:240,height:45}},
 {t:7000,type:"modal_open",innerText:"Ready to export",box:{x:600,y:250,width:320,height:220}},
];
test("locked action preroll and postroll are 1.0x, speed reaches 4x inside idle",()=>{
 const p=buildTimeWarp(events,0,9000,60,4,true);
 assert.deepEqual(p.actionWindows,[{start:600,end:1300},{start:6600,end:7300}]);
 assert.ok(p.deadZones.some(x=>x.end-x.start>3000));
 assert.ok(p.outputDurationMs<9000);
 assert.ok(p.frameMap.some(x=>x.speed>3.95));
 assert.ok(p.frameMap.every((f,i)=>i===0||f.sourceMs>p.frameMap[i-1]!.sourceMs));
 for(const f of p.frameMap) {
  if(p.actionWindows.some(a=>f.sourceMs>=a.start&&f.sourceMs<=a.end))
    assert.equal(f.speed,1);
 }
 for(const ms of [600,1000,1300,6600,7000,7300]){
  assert.ok(Math.abs(p.sourceToOutput(ms)-p.sourceToOutput(ms-.05)-.05)<.003);
 }
});
test("explicit loading and static scroll are accelerated without invading interaction guardrails",()=>{
 const evidence:TraceEvent[]=[
  {t:300,type:"loading",durationMs:500},
  {t:1550,type:"scroll",scrollMode:"static",durationMs:420,scroll:{x:0,y:500}},
  {t:2400,type:"click",tag:"button",innerText:"Save",box:{x:20,y:20,width:80,height:35}},
 ];
 const warp=buildTimeWarp(evidence,0,3100,60,4,true);
 assert.ok(warp.deadZones.some(s=>s.start<=300&&s.end>=800));
 assert.ok(warp.deadZones.some(s=>s.start<=1550&&s.end>=1970));
 const guarded=warp.frameMap.filter(f=>f.sourceMs>=2000&&f.sourceMs<=2700);
 assert.ok(guarded.every(f=>f.speed===1));
});
test("scroll traces form a compressible continuous interval without manual scrollMode tags",()=>{
 const scrolls:TraceEvent[]=Array.from({length:9},(_,i)=>({
   t:1000+i*75,type:"scroll",scroll:{x:0,y:i*95},
 }));
 scrolls.push({t:2400,type:"click",tag:"button",innerText:"Open",box:{x:20,y:20,width:100,height:38}});
 const p=buildTimeWarp(scrolls,0,2800,60,4,true);
 assert.ok(p.deadZones.some(s=>s.start<=1000&&s.end>=1600));
 assert.ok(p.frameMap.some(v=>v.sourceMs>1200&&v.sourceMs<1400&&v.speed>1.5));
 assert.ok(p.frameMap.filter(v=>v.sourceMs>=2000&&v.sourceMs<=2700).every(v=>v.speed===1));
});
test("only first focus of a field protects its action window",()=>{
 const entries:TraceEvent[]=[
  {t:1000,type:"focusin",tag:"input",selector:"#email"},
  {t:2400,type:"focusin",tag:"input",selector:"#email"},
  {t:4100,type:"focusin",tag:"textarea",selector:"#bio",isInitial:false},
 ];
 const plan=buildTimeWarp(entries,0,5000,60,4,true);
 assert.deepEqual(plan.actionWindows,[{start:600,end:1300}]);
 assert.ok(plan.deadZones.some(d=>d.start<=1300&&d.end>=5000));
});
test("callouts never overlap even when cooldown is configured below lifetime",()=>{
 const rows:TraceEvent[]=[
  {t:500,type:"click",tag:"button",innerText:"Connect",box:{x:10,y:30,width:70,height:40}},
  {t:900,type:"click",tag:"button",innerText:"Deploy",box:{x:10,y:30,width:70,height:40}},
  {t:2500,type:"click",tag:"button",innerText:"Publish",box:{x:10,y:30,width:70,height:40}},
 ];
 const cues=buildCallouts(rows,0,t=>t,{enable:true,cooldownMs:300,lifetimeMs:1800});
 assert.deepEqual(cues.map(c=>c.text),["Connect","Publish"]);
 assert.ok(cues[1]!.outputStartMs>=cues[0]!.outputEndMs);
});
test("disabled timewarp is exact real-time with no deadzone acceleration",()=>{
 const p=buildTimeWarp(events,0,9000,60,4,false);
 assert.ok(Math.abs(p.outputDurationMs-9000)<.001);
 assert.equal(p.deadZones.length,0);
 assert.ok(p.frameMap.every(x=>x.speed===1));
});
test("callout anti-clutter, labels, cooldown and no private text",()=>{
 const e:TraceEvent[]=[
 {t:1000,type:"pointerdown",tag:"button",innerText:"Connect your agent",box:{x:100,y:100,width:200,height:40}},
 {t:1200,type:"click",tag:"button",innerText:"Connect your agent",box:{x:100,y:100,width:200,height:40}},
 {t:2100,type:"click",tag:"button",innerText:"Delete item",box:{x:100,y:100,width:200,height:40}},
 {t:4200,type:"submit",role:"button",ariaLabel:"Publish site",box:{x:400,y:150,width:200,height:45}},
 {t:8400,type:"click",tag:"button",innerText:"API key = secret-123",box:{x:400,y:150,width:200,height:45}},
 ];
 const out=buildCallouts(e,0,x=>x,{enable:true,cooldownMs:2500,lifetimeMs:1800});
 assert.deepEqual(out.map(x=>x.text),["Connect Agent","Publish Site"]);
 assert.equal(out[0]!.outputEndMs-out[0]!.outputStartMs,1800);
 assert.ok(out[1]!.outputStartMs-out[0]!.outputStartMs>=2500);
});
test("3D projection centered at zero tilt and shifts under tilt",()=>{
 const stage=createStudioStage(.25);
 const box={x:170,y:175,width:80,height:40};
 const camera={zoom:1,centerX:640,centerY:360,offsetX:0,offsetY:0,sourceScale:1480/1280,rotateX:0,rotateY:0};
 const p=projectAnchor(box,camera,stage);
 assert.ok(Math.abs(p.x-(220+210*1480/1280))<.001);
 const tilted=projectAnchor(box,{...camera,rotateX:2,rotateY:2},stage);
 assert.ok(Math.hypot(tilted.x-p.x,tilted.y-p.y)>1);
 assert.throws(()=>createStudioStage(.9));
});
test("bridge deterministic across repeated builds and no callouts unless enabled",()=>{
 const input={events,startMs:0,durationMs:9000,fps:60,
  config:{...DEFAULT_STUDIO_CONFIG,enableTimeWarp:true,enableCallouts:true,enableStudioFloor:true}};
 const a=buildStudioPlan(input),b=buildStudioPlan(input);
 assert.deepEqual(a,b);
 assert.equal(a.schema,"sauce-studio-motion-v1");
 assert.equal(a.stage.window.width,1480);
 assert.equal(a.frameMap.length,Math.ceil(a.outputDurationMs/1000*60));
 assert.ok(a.callouts.length>0);
});


test("3D Launch keeps the establishing shot still until a verified product action",()=>{
 const gaze:TraceEvent[]=[
  {t:100,type:"pointermove",x:180,y:200,attention:{score:.99,flow:.9}},
  {t:650,type:"pointermove",x:240,y:220,attention:{score:.92,flow:.8}},
 ];
 const frameMap=Array.from({length:96},(_,i)=>({sourceMs:i*1000/60,speed:1}));
 const launch=planCameraRig(frameMap,[],gaze,resolvePreset("3d-launch"),0);
 assert.ok(launch.every(f=>f.scale===1 && f.focusX===640 && f.focusY===360),
   "gaze alone must not pan or push the cinematic camera");
 const hyper=planCameraRig(frameMap,[],gaze,resolvePreset("hyper-cut"),0);
 assert.ok(hyper.some(f=>f.scale>1.001),
   "retain the existing attention treatment for Hyper-Cut");
 const proof=[{id:"modal-0",kind:"modal" as const,score:95,sourceMs:650,outputMs:650,
   box:{x:475,y:120,width:330,height:310},label:null}];
 const withProof=planCameraRig(frameMap,proof,gaze,resolvePreset("3d-launch"),0);
 assert.ok(withProof.slice(50).some(f=>f.scale>1.03 && f.spotlightActive),
   "an actual observed modal must still trigger a purposeful camera shot");
 assert.ok(withProof.slice(0,39).every(f=>f.scale===1),
   "the camera must not move toward an unobserved future state");
});

test("recorded feature result holds the 3D Launch camera longer than an ordinary click",()=>{
 const source=Array.from({length:210},(_,i)=>({sourceMs:i*1000/60,speed:1}));
 const box={x:530,y:265,width:160,height:90};
 const make=(kind:"feature"|"click")=>planCameraRig(
   source,[{id:"real-event",kind,sourceMs:300,outputMs:300,box,score:99,label:null}],
   [],resolvePreset("3d-launch"),0);
 const feature=make("feature"),click=make("click");
 const frame=145; // 2.416s, after ordinary click ownership expires
 assert.ok(feature[frame]!.scale>click[frame]!.scale+.02,
   "verified feature payoff should retain focus instead of hunting for another target");
 assert.ok(feature.some(f=>f.spotlightActive));
 assert.ok(feature.every(f=>Number.isFinite(f.scale)&&f.scale<=1.36));
});
