import {strict as assert} from "node:assert";
import {test} from "node:test";
import {compileSourceTrueRecut} from "../sourceTrueRecut";
import {isHighIntent} from "../timeWarp";

const observed={
  duration:12,
  events:[
    {start:2.189694,end:2.310422,t:3.181067,evidence:"real screenshot and DOM verified"},
    {start:6.230606,end:6.334683,t:7.444369,evidence:"real contrast matrix opened in browser"}
  ]
};
test("source-verified outcomes protect real camera payoff within beat locked edit",()=>{
  const a=compileSourceTrueRecut(observed);
  assert.deepEqual(a,compileSourceTrueRecut(observed));
  assert.equal(a.schema,"sauce-source-true-recut-v1");
  assert.equal(a.creativeApproved,false);
  assert.equal(a.sourceFrameCount,720);
  assert.equal(a.outputFrameCount,380);
  assert.deepEqual(a.segments.map(s=>[s.startFrame,s.endFrame,s.outputStartFrame]),
    [[0,42,0],[108,270,42],[350,526,204]]);
  assert.deepEqual(a.cutsOutputFrames,[42,204]);
  assert.deepEqual(a.events.map(e=>[e.outputPressFrame,e.outputResultFrame]),
    [[66,125],[228,301]]);
  for(const e of a.events){
    assert.ok(e.outputResultFrame>e.outputPressFrame);
  }
  const frames=a.segments.flatMap(s=>Array.from(
    {length:s.endFrame-s.startFrame},(_,i)=>s.startFrame+i));
  assert.equal(new Set(frames).size,a.outputFrameCount);
  assert.ok(frames.every((v,i)=>!i||v>frames[i-1]!));
  for(const event of a.events){
    assert.ok(frames.includes(event.sourcePressFrame));
    assert.ok(frames.includes(event.sourceResultFrame));
    for(let t=event.sourceResultFrame;t<=event.sourceResultFrame+39;t++)
      assert.ok(frames.includes(t),"real confirmed result has a source-native hold");
  }
});
test("a pretend result marker cannot force editorial protection",()=>{
  assert.equal(isHighIntent({t:100,type:"verified-result"}),false);
  assert.equal(isHighIntent({t:100,type:"verified-result",verifiedSource:false}),false);
  assert.equal(isHighIntent({t:100,type:"verified-result",verifiedSource:true}),true);
  assert.equal(isHighIntent({t:100,type:"click"}),true);
});
test("missing evidence, fabricated results and nonchronological actions fail closed",()=>{
  assert.throws(()=>compileSourceTrueRecut({...observed,events:[]}),/1–4/);
  assert.throws(()=>compileSourceTrueRecut({...observed,events:[
    {...observed.events[0]!,evidence:""}]}),/source-truth-verified/);
  assert.throws(()=>compileSourceTrueRecut({...observed,events:[
    {...observed.events[0]!,t:2.0}]}),/source-truth-verified/);
  assert.throws(()=>compileSourceTrueRecut({...observed,events:[
    observed.events[0]!,{...observed.events[1]!,start:2.3}]}),
    /source-truth-verified/);
  assert.throws(()=>compileSourceTrueRecut({...observed,duration:11.991}),/native-60fps/);
});

test("cannot invent jump cuts when a dense real workflow is continuous",()=>{
  const source={duration:10.216666666666667,events:[
    {start:.755722,end:.855,t:1.989246,evidence:"real first source result"},
    {start:3.63850533,end:3.75,t:4.81532833,evidence:"real second source result"},
    {start:6.63904633,end:6.75,t:7.80868533,evidence:"real third source result"}]};
  assert.throws(()=>compileSourceTrueRecut(source),/No source-verified idle gap/);
});
