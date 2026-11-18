import test from "node:test";
import assert from "node:assert/strict";
import {buildStudioPlan,buildMotionEnginePlan} from "../bridge";
import {resolvePreset,SAUCE_FLAVORS} from "../presets";
import {TraceEvent,FoleyCue} from "../types";
import {detectHeroMoments} from "../autoDirector";
import {buildTimeWarp} from "../timeWarp";
import {planCameraRig} from "../cameraRig";

const richTrace:TraceEvent[]=[
 {t:0,type:"pointermove",x:50,y:400},
 {t:350,type:"pointermove",x:170,y:360},
 {t:690,type:"pointermove",x:280,y:290},
 {t:940,type:"pointerdown",tag:"button",selector:"#connect",
   ariaLabel:"Connect your agent",box:{x:260,y:250,width:190,height:45},x:320,y:275},
 {t:978,type:"click",tag:"button",selector:"#connect",
   innerText:"Connect your agent",box:{x:260,y:250,width:190,height:45},x:320,y:275},
 {t:1260,type:"dialog-visible",role:"dialog",ariaLabel:"Connect your agent",
   box:{x:455,y:155,width:370,height:390}},
 {t:2020,type:"copy",tag:"button",ariaLabel:"Copy command",
   box:{x:660,y:360,width:140,height:45}},
 {t:5450,type:"pointerdown",tag:"button",selector:"#deploy",
   innerText:"Deploy",box:{x:690,y:425,width:180,height:50}},
 {t:5500,type:"click",tag:"button",selector:"#deploy",
   innerText:"Deploy",box:{x:690,y:425,width:180,height:50}},
];
const input=(preset:"clean-studio"|"3d-launch"|"hyper-cut")=>({
  events:richTrace,startMs:0,durationMs:8000,fps:60,preset
});

test("all three Sauce flavors are versioned, serializable and distinct",()=>{
  assert.deepEqual(SAUCE_FLAVORS,["clean-studio","3d-launch","hyper-cut"]);
  const flavors=SAUCE_FLAVORS.map(id=>resolvePreset(id));
  for(const item of flavors){
    const rebuilt=JSON.parse(JSON.stringify(item));
    assert.deepEqual(rebuilt,item);
    assert.equal(item.schemaVersion,1);
    assert.deepEqual(item.export,{width:1920,height:1080,fps:60});
  }
  assert.equal(flavors[0]!.camera.mode,"flat");
  assert.equal(flavors[1]!.camera.perspectivePx,1200);
  assert.deepEqual(flavors[1]!.camera.spring,
    {stiffness:180,damping:24,mass:1});
  assert.equal(flavors[1]!.camera.spotlight.blurPx,6);
  assert.equal(flavors[2]!.director.idleStrategy,"cut");
  assert.notDeepEqual(flavors[0]!.director,flavors[1]!.director);
});

test("preset overrides are immutable, validated, and deny unknown keys",()=>{
  const tuned=resolvePreset("3d-launch",{
    sound:{muted:true},director:{maxWarpSpeed:3.5},
    camera:{spotlight:{blurPx:5}}
  });
  assert.equal(tuned.sound.muted,true);
  assert.equal(tuned.director.maxWarpSpeed,3.5);
  assert.equal(tuned.camera.spotlight.blurPx,5);
  assert.equal(resolvePreset("3d-launch").sound.muted,false);
  assert.throws(()=>resolvePreset("3d-launch",{camera:{perspectivePx:1}}));
  assert.throws(()=>resolvePreset("3d-launch",{camera:{notASetting:true}}));
  assert.throws(()=>resolvePreset("hyper-cut",{id:"3d-launch"}));
  assert.throws(()=>resolvePreset("clean-studio",{sound:{musicGain:8}}));
});

test("director scores only real hero moments and deduplicates click sequences",()=>{
  const p=resolvePreset("3d-launch");
  const heroes=detectHeroMoments(richTrace,0,8000,p,x=>x);
  assert.deepEqual(heroes.map(x=>x.kind),
    ["click","modal","copy","click"]);
  assert.deepEqual(heroes.map(x=>x.sourceMs),[940,1260,2020,5450]);
  assert.deepEqual(heroes.map(x=>x.id),
    ["hero-0","hero-1","hero-2","hero-3"]);
  const privateTrace:TraceEvent[]=[{t:1000,type:"click",tag:"button",
    ariaLabel:"API key secret 123",box:{x:10,y:10,width:100,height:30}}];
  assert.equal(detectHeroMoments(privateTrace,0,2000,p,x=>x)[0]!.label,null);
});

test("camera starts flat, then follows verified target with bounded spring tilt",()=>{
  const plan=buildMotionEnginePlan(input("3d-launch")).framePlan;
  assert.equal(plan.frames[0]!.camera.scale,1);
  assert.equal(plan.frames[0]!.camera.rotateYDeg,0);
  const before=plan.frames.filter(f=>f.sourceMs<940);
  assert.ok(before.every(f=>f.camera.scale===1));
  const action=plan.frames.find(f=>f.sourceMs>1330&&f.sourceMs<1700);
  assert.ok(action);
  assert.ok(action!.camera.scale>1.03);
  assert.ok(action!.camera.spotlightActive);
  assert.ok(action!.camera.spotlightBox);
  assert.ok(plan.frames.every(f=>Math.abs(f.camera.rotateXDeg)<=2.500001 &&
    Math.abs(f.camera.rotateYDeg)<=2.500001));
  assert.ok(plan.frames.every((f,i)=>i===0 ||
    f.sourceMs>plan.frames[i-1]!.sourceMs));
});

test("timewarp respects configurable idle threshold and 400/300 action locks",()=>{
  const events:TraceEvent[]=[{t:2200,type:"click",tag:"button",box:{
    x:5,y:5,width:40,height:24}}];
  const p=buildTimeWarp(events,0,5000,60,4,true,{
    idleThresholdMs:600,actionPreRollMs:400,actionPostRollMs:300
  });
  assert.deepEqual(p.actionWindows,[{start:1800,end:2500}]);
  assert.ok(p.deadZones.some(d=>d.start===0&&d.end===1800));
  const protectedFrames=p.frameMap.filter(f=>f.sourceMs>=1800&&f.sourceMs<=2500);
  assert.ok(protectedFrames.length>20);
  assert.ok(protectedFrames.every(f=>f.speed===1));
  assert.ok(p.outputDurationMs<5000);
  assert.throws(()=>buildTimeWarp(events,0,5000,60,4,true,{idleThresholdMs:50}));
});

test("Foley click and modal cues align to mapped output sample clock",()=>{
  const plan=buildMotionEnginePlan(input("3d-launch"));
  const f=plan.foleyPlan,frames=plan.framePlan.frames;
  assert.equal(f.sampleRate,48000);
  assert.equal(f.schema,"sauce-foley-plan-v1");
  assert.equal(f.muted,false);
  assert.ok(f.cues.every(c=>c.outputSample>=0 &&
    c.outputSample<Math.ceil(f.durationMs*48)));
  assert.equal(f.cues.filter(c=>c.sound==="click_crisp").length,2);
  assert.equal(f.cues.filter(c=>c.sound==="pop_glass").length,1);
  const expected=(src:number)=>{
    const candidate=frames.reduce((best,item)=>
      Math.abs(item.sourceMs-src)<Math.abs(best.sourceMs-src)?item:best,frames[0]!);
    return candidate.outputTimeMs;
  };
  for(const [source,sound] of [[940,"click_crisp"],[1260,"pop_glass"]] as const){
    const cue=f.cues.find(c=>c.sound===sound&&Math.abs(c.sourceMs-source)<1);
    assert.ok(cue);
    // Event mapping may be between output frames; expect <1/60 second.
    assert.ok(Math.abs(cue!.outputMs-expected(source))<1000/60+0.1);
    assert.ok(Math.abs(cue!.outputMs-cue!.outputSample/48)<.001);
  }
  assert.ok(f.duckIntervals.every(d=>d.endSample>d.startSample));
});

test("clean is silent by default, Launch schedules cues, hyper-cut proposes cuts",()=>{
 const clean=buildMotionEnginePlan(input("clean-studio"));
 const launch=buildMotionEnginePlan(input("3d-launch"));
 const hyper=buildMotionEnginePlan(input("hyper-cut"));
 assert.equal(clean.framePlan.outputDurationMs,8000);
 assert.equal(clean.foleyPlan.cues.length,0);
 assert.ok(clean.framePlan.frames.every(f=>f.camera.rotateXDeg===0 &&
   f.camera.rotateYDeg===0));
 assert.ok(launch.framePlan.outputDurationMs<clean.framePlan.outputDurationMs);
 assert.ok(hyper.framePlan.outputDurationMs<launch.framePlan.outputDurationMs);
 assert.ok(hyper.framePlan.editDecisions.some(d=>d.kind==="cut-candidate"));
 assert.ok(hyper.foleyPlan.cues.length>0);
});

test("selected preset remains consumable through original StudioPlan bridge",()=>{
 const x=buildStudioPlan(input("3d-launch"));
 assert.equal(x.schema,"sauce-studio-motion-v1");
 assert.equal(x.motionEngine?.schema,"sauce-motion-plan-v1");
 assert.equal(x.frameMap.length,x.motionEngine?.framePlan.frames.length);
 assert.deepEqual(x.frameMap.map(f=>f.sourceMs),
   x.motionEngine?.framePlan.frames.map(f=>f.sourceMs));
 assert.deepEqual(x.callouts,x.motionEngine?.framePlan.callouts);
 assert.equal(x.stage.reflectionIntensity,.25);
});

test("plan is pure and deterministic; full JSON roundtrip is stable",()=>{
 const a=buildStudioPlan(input("3d-launch"));
 const b=buildStudioPlan(input("3d-launch"));
 assert.deepEqual(a,b);
 assert.deepEqual(JSON.parse(JSON.stringify(a)),a);
 assert.equal(a.motionEngine?.framePlan.frames.length,a.frameMap.length);
});

test("verified feature commit reveals an actual diff on the 60fps frame clock",()=>{
  const commit={sha:"a1b2c3d4e5f6a7b8",file:"src/engine.ts",title:"Ship real capture",
    lines:["@@ -2,2 +2,2 @@","-const mode = 'draft';","+const mode = 'ready';"]};
  const event:TraceEvent={t:2100,type:"feature-commit",commit};
  const captured={events:[...richTrace,event],startMs:0,durationMs:8000,
    fps:60,preset:"3d-launch" as const};
  const one=buildMotionEnginePlan(captured),two=buildMotionEnginePlan(captured);
  assert.deepEqual(one,two);
  const diff=one.framePlan.diffReveals?.[0];
  assert.ok(diff);
  assert.equal(diff!.sha,commit.sha);
  assert.deepEqual(diff!.lines,commit.lines);
  const active=one.framePlan.frames.filter(f=>f.diffId===diff!.id);
  assert.ok(active.length>20);
  assert.ok(active.some(f=>f.diffProgress!>0.5));
  assert.ok(active.every(f=>f.diffProgress!>=0&&f.diffProgress!<=1));
  assert.ok(one.framePlan.heroMoments.some(h=>h.kind==="feature"));
  const changed=one.framePlan.frames.find(f=>f.sourceMs>2200&&f.sourceMs<2600);
  assert.ok(changed && changed.camera.rotateYDeg>0.02);
});

test("unverified or private Git snippets are rejected rather than fabricated",()=>{
  const publicDiff={sha:"f".repeat(40),file:"src/index.ts",title:"Build feature",
    lines:["@@ -1 +1 @@","+export const enabled = true;"]};
  for(const commit of [
    {...publicDiff,sha:"main"},
    {...publicDiff,file:"../../keys.txt"},
    {...publicDiff,lines:["+const apiKey='private_key' "]},
    {...publicDiff,lines:Array.from({length:20},()=>"+x")}
  ]){
    const plan=buildMotionEnginePlan({...input("3d-launch"),events:[
      {t:1800,type:"feature-commit",commit}
    ]});
    assert.equal(plan.framePlan.diffReveals?.length,0);
    assert.equal(plan.framePlan.heroMoments.length,0);
  }
});

test("saliency protects time but cannot direct a cinematic shot before a verified action",()=>{
  const gaze:TraceEvent={type:"visual-attention",t:1400,x:980,y:190,
    attention:{score:.9,flow:.7}};
  const warp=buildTimeWarp([gaze],0,3500,60,3,true);
  assert.equal(warp.gazeTargets.length,1);
  assert.ok(warp.actionWindows.some(w=>w.start<=1400&&w.end>=1400));
  const evidence=[gaze,{t:2000,type:"pointermove",x:50,y:50}];
  const plan=buildMotionEnginePlan({...input("3d-launch"),durationMs:3500,
     events:evidence});
  const f=plan.framePlan.frames.find(f=>f.sourceMs>1800&&f.sourceMs<1950);
  assert.ok(f);
  assert.equal(f!.camera.focusX,640);
  assert.equal(f!.camera.focusY,360);
  assert.equal(f!.camera.scale,1);
  const hyper=buildMotionEnginePlan({...input("hyper-cut"),durationMs:3500,
    events:evidence});
  assert.ok(hyper.framePlan.frames.some(f=>f.camera.scale>1.002),
    "hyper-cut retains the intentional saliency camera response");
  assert.ok(plan.framePlan.frames.every((f,i)=>i===0 ||
    f.outputTimeMs>plan.framePlan.frames[i-1]!.outputTimeMs));
});

test("elevated dialog ownership persists through child actions and expires on close",()=>{
  const plan=buildMotionEnginePlan(input("3d-launch")).framePlan;
  const modal=plan.heroMoments.find(h=>h.kind==="modal")!;
  const afterCopy=plan.frames.find(f=>f.sourceMs>3000&&f.sourceMs<3100)!;
  assert.equal(afterCopy.foregroundId,modal.id);
  assert.ok(afterCopy.heroId);
  const afterExpiry=plan.frames.find(f=>f.sourceMs>3700&&f.sourceMs<3800)!;
  assert.equal(afterExpiry.foregroundId,null);
  const closed=buildMotionEnginePlan({...input("3d-launch"),
    events:[...richTrace,{t:2600,type:"dialog-hidden"}]}).framePlan;
  const pastClose=closed.frames.find(f=>f.sourceMs>3000&&f.sourceMs<3100)!;
  assert.equal(pastClose.foregroundId,null);
});

test("executed beat cuts enforce the 150-frame ceiling and skip real idle source",()=>{
  const events:TraceEvent[]=[
    {type:"pointerdown",t:1000,tag:"button",box:{x:30,y:40,width:180,height:40}},
    {type:"pointerdown",t:12500,tag:"button",box:{x:600,y:280,width:200,height:44}},
    {type:"dialog-visible",t:24000,role:"dialog",
      box:{x:430,y:150,width:400,height:360}}
  ];
  const plan=buildMotionEnginePlan({events,startMs:0,durationMs:27000,
    fps:60,preset:"3d-launch"});
  const frames=plan.framePlan.frames,cuts=plan.framePlan.editDecisions
    .filter(x=>x.kind==="cut");
  assert.ok(cuts.length>=2,"Long real pauses require executed cuts");
  assert.ok(cuts.some(c=>c.sourceEndMs-c.sourceStartMs>2000),
    "At least one cut must actually skip recorded idle source frames");
  const bounds=[0,...cuts.map(c=>c.outputFrame!),frames.length];
  assert.ok(bounds.slice(1).every((b,i)=>b-bounds[i]!<=150),
    "No uninterrupted shot may exceed 150 frames");
  assert.ok(frames.length<27000*60/1000);
  assert.ok(frames.every((f,i)=>i===0||f.sourceMs>frames[i-1]!.sourceMs));
  for(const source of [1000,12500,24000]){
    const shown=frames.find(f=>f.sourceMs>=source);
    assert.ok(shown&&shown.sourceMs-source<1000/60+1e-2,
      "A real hero action must remain visible after the cut");
  }
  for(const cue of plan.foleyPlan.cues){
    assert.equal(cue.outputSample%800,0);
    const shown=frames.find(f=>f.sourceMs>=cue.sourceMs);
    assert.ok(shown);
    assert.equal(cue.outputSample,shown!.outputFrame*800);
  }
  assert.equal(plan.foleyPlan.durationMs,plan.framePlan.outputDurationMs);
});

test("no-action sessions end within one 2-second beat without fake cuts",()=>{
  const plan=buildMotionEnginePlan({events:[],startMs:0,
    durationMs:15000,fps:60,preset:"3d-launch"});
  assert.equal(plan.framePlan.frames.length,120);
  assert.ok(!plan.framePlan.editDecisions.some(c=>c.kind==="cut"));
  assert.equal(plan.foleyPlan.cues.length,0);
});

test("cut begins on the visible frame after an observed action, never beforehand",()=>{
  const events:TraceEvent[]=[
    {type:"pointerdown",t:600,tag:"button",box:{x:50,y:60,width:100,height:30}},
    {type:"dialog-visible",t:1100,role:"dialog",
      box:{x:380,y:160,width:400,height:380}},
    {type:"pointerdown",t:2700,tag:"span",
      box:{x:450,y:470,width:140,height:25}}
  ];
  const plan=buildMotionEnginePlan({events,startMs:0,
    durationMs:4500,fps:60,preset:"3d-launch"});
  const later=plan.framePlan.heroMoments.find(h=>h.kind==="click"&&h.sourceMs===2700);
  assert.ok(later,"Observed nested modal click must rank as a real hero");
  const mapped=plan.framePlan.frames.find(f=>f.sourceMs>=2700);
  assert.ok(mapped);
  assert.ok(plan.framePlan.editDecisions.some(c=>c.kind==="cut"));
  const cue=plan.foleyPlan.cues.find(c=>c.trigger==="click"&&c.sourceMs===2700);
  assert.equal(cue?.outputSample,mapped!.outputFrame*800);
});

test("modal Z-plane holds one restrained 3D tilt through pointer travel",()=>{
  const plan=buildMotionEnginePlan(input("3d-launch")).framePlan;
  const approach=plan.frames.filter(f=>f.sourceMs>=250&&f.sourceMs<=800);
  assert.ok(approach.length>5);
  assert.ok(approach.every(f=>Math.abs(f.camera.rotateXDeg)<.000001&&
    Math.abs(f.camera.rotateYDeg)<.000001));
  const stable=plan.frames.filter(f=>f.sourceMs>=1760&&f.sourceMs<=1950);
  assert.ok(stable.length>=5);
  assert.ok(stable.every(f=>f.foregroundId!==null));
  for(const f of stable){
    assert.ok(Math.abs(f.camera.rotateXDeg-.30)<.02);
    assert.ok(Math.abs(f.camera.rotateYDeg+.40)<.02);
  }
  // The verified feature commit remains allowed its existing micro-pivot.
  const feature=plan.frames.find(f=>f.sourceMs>=2020 && f.sourceMs<2090);
  assert.ok(feature);
});

test("Codex child click retains dialog-wide framing across executed cut",()=>{
  const events:TraceEvent[]=[
    {t:786,type:"pointerdown",tag:"button",
      box:{x:200.19,y:344.21,width:208.06,height:32.32}},
    {t:916,type:"dialog-visible",role:"dialog",ariaLabel:"Connect your agent",
      box:{x:440,y:182.59,width:400,height:360}},
    {t:2069,type:"pointerdown",tag:"span",innerText:"Codex",
      box:{x:487,y:451,width:254,height:20}},
  ];
  const plan=buildMotionEnginePlan({
    events,startMs:0,durationMs:4200,fps:60,preset:"3d-launch"
  }).framePlan;
  const modal=plan.heroMoments.find(h=>h.kind==="modal");
  const codex=plan.heroMoments.find(h=>h.kind==="click"&&h.sourceMs===2069);
  assert.ok(modal&&codex);
  const before=plan.frames.find(f=>f.sourceMs>=1900)!;
  const after=plan.frames.find(f=>f.sourceMs>=2250)!;
  for(const point of [before,after]){
    assert.ok(Math.abs(point.camera.scale-1.31)<.001);
    assert.ok(Math.abs(point.camera.focusX-640)<.002);
    assert.ok(Math.abs(point.camera.focusY-362.59)<.002);
    assert.deepEqual(point.camera.spotlightBox,modal!.box);
  }
  const cut=plan.editDecisions.find(e=>e.kind==="cut"&&
    e.sourceEndMs>=2069);
  assert.ok(cut,"Keep real beat cut rather than removing the action");
  const pre=plan.frames[cut!.outputFrame!-1]!.camera;
  const post=plan.frames[cut!.outputFrame!]!.camera;
  assert.ok(Math.abs(pre.scale-post.scale)<.0005);
  assert.ok(Math.abs(pre.focusX-post.focusX)<.002);
  assert.ok(Math.abs(pre.focusY-post.focusY)<.002);
  const ending=plan.frames[plan.frames.length-1]!.camera;
  assert.ok(Math.abs(ending.scale-1.31)<.002);
  assert.ok(Math.abs(ending.focusX-640)<.01);
});

test("camera releases dialog only on an observed close event",()=>{
  const events:TraceEvent[]=[
    {t:916,type:"dialog-visible",role:"dialog",
      box:{x:440,y:182.59,width:400,height:360}},
    {t:2069,type:"pointerdown",tag:"span",innerText:"Codex",
      box:{x:487,y:451,width:254,height:20}},
    {t:2600,type:"dialog-hidden"},
  ];
  const plan=buildMotionEnginePlan({
    events,startMs:0,durationMs:4700,fps:60,preset:"3d-launch"
  }).framePlan;
  const open=plan.frames.find(f=>f.sourceMs>=2400)!;
  const closed=plan.frames.find(f=>f.sourceMs>=4300)!;
  assert.ok(Math.abs(open.camera.scale-1.31)<.01);
  assert.ok(closed.camera.scale<1.10);
  assert.equal(closed.camera.spotlightBox,null);
});

test("3D Launch stage selects fluted glass; validated overrides stay deterministic",()=>{
  const threeD=resolvePreset("3d-launch");
  assert.equal(threeD.stage.backdropStyle,"fluted-glass");
  assert.equal(resolvePreset("clean-studio").stage.backdropStyle,"obsidian-grain");
  assert.equal(resolvePreset("hyper-cut").stage.backdropStyle,"chromatic-bloom");
  const override=resolvePreset("3d-launch",{stage:{backdropStyle:"chromatic-bloom"}});
  assert.equal(override.stage.backdropStyle,"chromatic-bloom");
  assert.equal(resolvePreset("3d-launch").stage.backdropStyle,"fluted-glass");
  assert.throws(()=>resolvePreset("3d-launch",
    {stage:{backdropStyle:"unrecognized"}}));
  assert.deepEqual(threeD.camera.spring,{mass:1,stiffness:180,damping:24});
  assert.equal(threeD.camera.perspectivePx,1200);
  assert.equal(threeD.camera.spotlight.blurPx,6);
  assert.deepEqual(buildMotionEnginePlan(input("3d-launch")).preset.stage,
    threeD.stage);
});

test("flagged exact mass-spring overshoots then settles and orbit remains alive",()=>{
  const preset=resolvePreset("3d-launch",{
    camera:{spring:{mass:1,stiffness:180,damping:18},orbit:{enabled:true}}
  });
  assert.equal(preset.camera.spring.stiffness,180);
  assert.equal(preset.camera.orbit.periodMs,2200);
  const frameMap=Array.from({length:210},(_,i)=>({sourceMs:i*1000/60,speed:1}));
  const modal={id:"modal-test",kind:"modal" as const,sourceMs:400,outputMs:400,
    score:100,box:{x:550,y:240,width:460,height:360},label:"Dialog"};
  // No editorial cuts: isolate the true second-order spring response.
  const poses=planCameraRig(frameMap,[modal],[],preset,0);
  const targetScale=1.31;
  const transition=poses.slice(24,150);
  const peak=Math.max(...transition.map(p=>p.scale));
  assert.ok(peak>targetScale+.006,"Underdamped scale overshoot: "+peak);
  const last=poses.at(-1)!;
  assert.ok(Math.abs(last.scale-targetScale)<.001);
  assert.ok(last.focusX>640 && last.focusX<850);
  const orbit=poses.slice(95,185);
  const amplitude=Math.max(...orbit.map(p=>p.rotateYDeg))-
                  Math.min(...orbit.map(p=>p.rotateYDeg));
  assert.ok(amplitude>.09,"Modal orbit must keep moving: "+amplitude);
  const defaultPreset=resolvePreset("3d-launch");
  assert.equal(defaultPreset.camera.orbit.enabled,false);
  assert.deepEqual(defaultPreset.camera.spring,{mass:1,stiffness:180,damping:24});
  const off=planCameraRig(frameMap,[modal],[],defaultPreset,0);
  assert.equal(new Set(off.slice(110,185).map(p=>p.rotateYDeg)).size,1);
  // Fixed frame clock yields deterministic poses, including velocity states.
  assert.deepEqual(poses,planCameraRig(frameMap,[modal],[],preset,0));
});

test("modal opening <=300ms after a click cancels trigger-button camera drift",()=>{
  const p=resolvePreset("3d-launch");
  const events:TraceEvent[]=[
    {t:786,type:"pointerdown",tag:"button",selector:"#trigger",
      box:{x:200,y:344,width:208,height:32}},
    {t:786.5,type:"click",tag:"button",selector:"#trigger",
      box:{x:200,y:344,width:208,height:32}},
    {t:916,type:"dialog-visible",role:"dialog",
      box:{x:440,y:182,width:400,height:360}}
  ];
  const frames=Array.from({length:170},(_,i)=>({sourceMs:i*1000/60,speed:1}));
  const heroes=detectHeroMoments(events,0,2800,p,x=>x);
  const poses=planCameraRig(frames,heroes,events,p,0);
  const waiting=frames.map((f,i)=>({f,p:poses[i]!}))
    .filter(x=>x.f.sourceMs>=786&&x.f.sourceMs<916);
  assert.ok(waiting.length>=5);
  assert.ok(waiting.every(x=>x.p.scale===1&&x.p.focusX===640&&x.p.focusY===360),
    "Trigger click must not pull the camera to its left-side tooltip");
  const centered=poses[110]!;
  assert.ok(centered.scale>1.17);
  assert.ok(Math.abs(centered.focusX-640)<1);
  assert.ok(Math.abs(centered.focusY-362)<5);
  // A late unrelated modal should not retroactively suppress button intent.
  const late=[...events.slice(0,2),{...events[2]!,t:1200}];
  const lateHeroes=detectHeroMoments(late,0,2800,p,x=>x);
  const latePoses=planCameraRig(frames,lateHeroes,late,p,0);
  assert.ok(latePoses[63]!.scale>1.01);
});
