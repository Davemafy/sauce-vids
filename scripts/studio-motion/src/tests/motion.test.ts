import test from "node:test";
import assert from "node:assert/strict";
import {buildTimeWarp} from "../timeWarp";
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
