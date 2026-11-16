"use client";
import {useEffect,useState} from "react";
import s from "./render-progress.module.css";

type Job = {
 id:string;state:"queued"|"rendering"|"ready"|"failed";
 phase?:"queued"|"compositing"|"finishing"|"complete";
 framesRendered?:number;framesTotal?:number;createdAt?:number;updatedAt?:number;
};

export function RenderProgress({job,sending,title,flavor,connectionLost=false}:{
 job:Job|null;sending:boolean;title:string;flavor:string;connectionLost?:boolean;
}) {
 const [now,setNow]=useState(()=>Date.now());
 useEffect(()=>{const timer=setInterval(()=>setNow(Date.now()),1000);return ()=>clearInterval(timer)},[]);
 const state=job?.state??"queued";
 const phase=job?.phase??(state==="rendering"?"compositing":"queued");
 const index=sending||state==="queued"?0:phase==="finishing"?2:1;
 const count=Math.max(0,job?.framesRendered??0);
 const total=Math.max(0,job?.framesTotal??0);
 const framed=total>0;
 const elapsed=Math.max(0,Math.floor((now-(job?.createdAt&&job.createdAt>0?job.createdAt:now))/1000));
 const clock=String(Math.floor(elapsed/60)).padStart(2,"0")+":"+String(elapsed%60).padStart(2,"0");
 const noFrameSignal=state==="rendering"&&phase==="compositing"&&!!job?.updatedAt&&now-job.updatedAt>45000;
 const headline=sending?"Opening the render desk.":state==="queued"?"Your film is in line.":phase==="finishing"?"The final cut is coming together.":"Compositing your film.";
 const detail=sending?"Sending the request to the render worker.":state==="queued"?"Sauce will start when a render slot opens.":phase==="finishing"?"The master is ready. Preparing the watchable preview.":"Compositing verified browser frames, camera moves, and sound.";
 const steps=[["Queue","Wait for a worker"],["Compositing","Build source frames"],["Export","Encode the film"]];
 return <div className={s.monitor} role="region" aria-label="Live film production status">
  <div className={s.top}><span className={s.live}><i aria-hidden="true"/> Sauce render session</span><time aria-label="Elapsed time">{clock}</time></div>
  <div className={s.middle}>
   <div className={s.reels} aria-hidden="true">
     <span className={[s.reel,s.reelA].join(" ")}><b>01</b><small>SOURCE</small></span>
     <span className={[s.reel,s.reelB].join(" ")}><b>02</b><small>MOTION</small></span>
     <span className={[s.reel,s.reelC].join(" ")}><b>03</b><small>MASTER</small></span>
     <span className={s.beam}/>
   </div>
   <div className={s.copy}>
    <span className={s.meta}>{title} · {flavor}</span>
    <h3>{headline}</h3>
    <p aria-live="polite">{connectionLost?"Status connection interrupted. Reconnecting automatically…":detail}</p>
    {noFrameSignal&&!connectionLost&&<p className={s.waiting}>No new frame report yet. The renderer may still be working.</p>}
   </div>
  </div>
  <div className={s.footer}>
   <div className={s.progressLabel}><span>{index===0?"Waiting for worker":index===2?"Preparing export":"Rendering real frames"}</span><span>{framed?Math.min(count,total).toLocaleString()+" / "+total.toLocaleString()+" frames":"Awaiting frame data"}</span></div>
   <div className={[s.rail,!framed?s.indeterminate:""].join(" ")}
     role={framed?"progressbar":"status"}
     aria-label={framed?"Frames composited":"Preparing render progress"}
     {...(framed?{"aria-valuemin":0,"aria-valuemax":total,"aria-valuenow":Math.min(count,total)}:{})}>
     {framed&&<span className={s.fill} style={{width:Math.round(Math.min(count,total)/total*100)+"%"}}/>}
   </div>
   <ol className={s.steps} aria-label="Production stages">
    {steps.map(([name,description],i)=><li key={name} className={[i===index?s.active:"",i<index?s.done:""].join(" ")}>
     <span className={s.number} aria-hidden="true">{i<index?"✓":String(i+1).padStart(2,"0")}</span>
     <span><strong>{name}</strong><small>{description}</small></span>
    </li>)}
   </ol>
  </div>
 </div>;
}
