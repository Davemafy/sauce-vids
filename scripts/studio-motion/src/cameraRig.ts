/** Deterministic spring camera rig. No wall-clock, randomness or DOM reads.
 * All values are computed sequentially once; any output frame is seekable.
 */
import {CameraPose,FrameMap,HeroMoment,Rect,SaucePreset,TraceEvent,clamp,finite} from "./types";
import {visualGazeTargets} from "./timeWarp";

class Spring {
  position:number;velocity=0;
  constructor(initial:number,private readonly mass:number,
              private readonly stiffness:number,private readonly damping:number){
    this.position=initial;
  }
  step(target:number,dt:number):number{
    if(dt<=0)return this.position;
    const omega=Math.sqrt(this.stiffness/this.mass);
    const zeta=this.damping/(2*Math.sqrt(this.stiffness*this.mass));
    const y=this.position-target,v=this.velocity;
    let yn:number,vn:number;
    if(Math.abs(zeta-1)<1e-8){
      const a=v+omega*y,d=Math.exp(-omega*dt);
      yn=(y+a*dt)*d;
      vn=(v-omega*a*dt)*d;
    }else if(zeta<1){
      const alpha=zeta*omega,wd=omega*Math.sqrt(1-zeta*zeta);
      const co=Math.cos(wd*dt),si=Math.sin(wd*dt),d=Math.exp(-alpha*dt);
      yn=d*(y*co+(v+alpha*y)*si/wd);
      vn=d*(v*co-(alpha*v+omega*omega*y)*si/wd);
    }else{
      const root=Math.sqrt(zeta*zeta-1),r1=-omega*(zeta-root),r2=-omega*(zeta+root);
      const c1=(v-r2*y)/(r1-r2),c2=y-c1;
      yn=c1*Math.exp(r1*dt)+c2*Math.exp(r2*dt);
      vn=r1*c1*Math.exp(r1*dt)+r2*c2*Math.exp(r2*dt);
    }
    this.position=target+yn;this.velocity=vn;return this.position;
  }
}
function rounded(v:number,places:number):number{
  const n=Number(v.toFixed(places));
  return Object.is(n,-0)?0:n;
}
function safeBox(box:Rect|null):box is Rect{
  return !!box&&[box.x,box.y,box.width,box.height].every(finite)
    &&box.width>=2&&box.height>=2;
}
interface CursorSample{t:number;x:number;y:number}
function sampleCursor(events:TraceEvent[],startMs:number):CursorSample[]{
  return events.filter(e=>(e.type==="pointermove"||e.eventType==="pointermove")
       &&finite(e.t)&&finite(e.x)&&finite(e.y))
    .map(e=>({t:e.t-startMs,x:e.x as number,y:e.y as number}))
    .sort((a,b)=>a.t-b.t);
}
function velocityAt(t:number,samples:CursorSample[],hint:number):{x:number;y:number;index:number}{
  let j=hint;
  while(j+1<samples.length&&samples[j+1]!.t<=t)j++;
  if(j<1)return {x:0,y:0,index:j};
  const a=samples[j-1]!,b=samples[j]!;
  const dt=(b.t-a.t)/1000;
  if(dt<=0||t-b.t>160||dt>0.45)return {x:0,y:0,index:j};
  return {x:clamp((b.x-a.x)/dt,-2000,2000),
          y:clamp((b.y-a.y)/dt,-2000,2000),index:j};
}
export function planCameraRig(
  frameMap:FrameMap[],heroMoments:HeroMoment[],events:TraceEvent[],
  preset:SaucePreset,startMs:number,viewport:{width:number;height:number}={width:1280,height:720}
):CameraPose[]{
  if(!finite(startMs)||viewport.width<=0||viewport.height<=0)
    throw new Error("Invalid camera source viewport");
  const p=preset.camera,dt=1/preset.export.fps;
  const newSpring=(x:number)=>new Spring(x,p.spring.mass,p.spring.stiffness,p.spring.damping);
  const centerX=viewport.width/2,centerY=viewport.height/2;
  const scale=newSpring(1),cx=newSpring(centerX),cy=newSpring(centerY);
  const rx=newSpring(0),ry=newSpring(0);
  const heroes=[...heroMoments].sort((a,b)=>a.sourceMs-b.sourceMs);
  const cursors=sampleCursor(events,startMs);
  const gaze=visualGazeTargets(events,startMs,
      frameMap.length?frameMap[frameMap.length-1]!.sourceMs:0);
  const out:CameraPose[]=[];
  let heroIndex=-1,cursorIndex=0,gazeIndex=-1;
  for(let i=0;i<frameMap.length;i++){
    const sourceMs=frameMap[i]!.sourceMs;
    while(heroIndex+1<heroes.length&&heroes[heroIndex+1]!.sourceMs<=sourceMs)heroIndex++;
    const hero=heroIndex>=0?heroes[heroIndex]!:null;
    while(gazeIndex+1<gaze.length&&gaze[gazeIndex+1]!.sourceMs<=sourceMs)gazeIndex++;
    const candidate=gazeIndex>=0?gaze[gazeIndex]!:null;
    const attention=candidate && sourceMs-candidate.sourceMs<1500 &&
      candidate.score>=.4 ? candidate:null;
    const modalClosed=hero?.kind==="modal"&&events.some(e=>{
      const k=(e.eventType||e.type).toLowerCase().replaceAll("_","-");
      return ["modal-close","modal-closed","dialog-hidden","dialog-closed"].includes(k)
        &&e.t-startMs>hero.sourceMs&&e.t-startMs<=sourceMs;
    });
    const active=hero&&!modalClosed&&sourceMs-hero.sourceMs<
      (hero.kind==="modal"?2400:1800)&&safeBox(hero.box)?hero:null;
    const box=active?.box||null;
    let desiredScale=1,desiredX=centerX,desiredY=centerY,desiredRX=0,desiredRY=0;
    if(box){
      const maxSafe=Math.min(p.scaleRange[1],
        (viewport.width-96)/box.width,
        (viewport.height-90)/box.height);
      desiredScale=clamp((active!.kind==="modal"?1.31:1.19),
        p.scaleRange[0],Math.max(p.scaleRange[0],maxSafe));
      desiredX=clamp(box.x+box.width/2,0,viewport.width);
      desiredY=clamp(box.y+box.height/2,0,viewport.height);
    }
    if(p.mode==="perspective" && !box && attention){
      // Small contextual emphasis only; a verified action always wins.
      desiredScale=clamp(1+attention.score*.065,1,p.scaleRange[1]);
      desiredX=clamp(attention.x,viewport.width*.22,viewport.width*.78);
      desiredY=clamp(attention.y,viewport.height*.22,viewport.height*.78);
    }
    if(p.mode==="perspective"){
      const v=velocityAt(sourceMs,cursors,cursorIndex);
      cursorIndex=v.index;
      // Pointer travel provides inertia, but never manufactures a pre-click
      // zoom. The camera can tilt slightly during approach.
      desiredRX=clamp(-p.maxTiltDeg*Math.tanh(v.y/1550),-p.maxTiltDeg,p.maxTiltDeg);
      desiredRY=clamp(p.maxTiltDeg*Math.tanh(v.x/1550),-p.maxTiltDeg,p.maxTiltDeg);
      if(hero?.kind==="feature" && sourceMs-hero.sourceMs<2100){
        // Micro-pivot explicitly tied to the recorded commit event.
        desiredRY=clamp(desiredRY+1.65,-p.maxTiltDeg,p.maxTiltDeg);
        desiredRX=clamp(desiredRX-.65,-p.maxTiltDeg,p.maxTiltDeg);
      }
      if(box){
        desiredRX+=clamp((desiredY-centerY)/viewport.height*.6,-.35,.35);
        desiredRY+=clamp((desiredX-centerX)/viewport.width*.6,-.35,.35);
      }
      desiredRX=clamp(desiredRX,-p.maxTiltDeg,p.maxTiltDeg);
      desiredRY=clamp(desiredRY,-p.maxTiltDeg,p.maxTiltDeg);
    }
    if(i>0){
      scale.step(desiredScale,dt);cx.step(desiredX,dt);cy.step(desiredY,dt);
      rx.step(desiredRX,dt);ry.step(desiredRY,dt);
    }
    out.push({
      scale:+clamp(scale.position,p.scaleRange[0],p.scaleRange[1]).toFixed(6),
      focusX:+clamp(cx.position,0,viewport.width).toFixed(5),
      focusY:+clamp(cy.position,0,viewport.height).toFixed(5),
      rotateXDeg:rounded(clamp(rx.position,-p.maxTiltDeg,p.maxTiltDeg),6),
      rotateYDeg:rounded(clamp(ry.position,-p.maxTiltDeg,p.maxTiltDeg),6),
      perspectivePx:p.perspectivePx,
      spotlightActive:!!box&&p.spotlight.enabled&&scale.position>1.025,
      spotlightBox:box?{...box}:null,
      spotlightBlurPx:p.spotlight.blurPx,
      spotlightDimOpacity:p.spotlight.dimOpacity
    });
  }
  return out;
}
