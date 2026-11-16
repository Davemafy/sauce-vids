"use client";
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import styles from "./studio.module.css";
import {RenderProgress} from "./render-progress";

type Flavor = "clean-studio" | "3d-launch" | "hyper-cut";
type Recording = "brimble" | "sauce";
type Job = {
 id:string; recording:Recording; preset:Flavor; foley:boolean;
 state:"queued"|"rendering"|"ready"|"failed"; message?:string;
 phase?:"queued"|"compositing"|"finishing"|"complete";
 framesRendered?:number;framesTotal?:number;createdAt?:number;updatedAt?:number;
 previewUrl?:string; masterUrl?:string;
};
type Catalog = {
 available:boolean;
 recordings:Array<{id:Recording;title:string;subtitle:string}>;
};
const flavors:{id:Flavor;name:string;detail:string;descriptor:string}[]=[
 {id:"clean-studio",name:"Clean Studio",detail:"Clear, quiet, and considered.",descriptor:"Natural framing"},
 {id:"3d-launch",name:"3D Launch",detail:"Depth, presence, and a little theatre.",descriptor:"Cinematic"},
 {id:"hyper-cut",name:"Hyper-Cut",detail:"Fast cuts for short attention spans.",descriptor:"High energy"},
];
const basePath=process.env.NEXT_PUBLIC_SAUCE_BASE_PATH || "";
const publicDemo="https://devmcp.davemafy.xyz/sauce-motion-phase2/preview.mp4";
const publicPoster="https://devmcp.davemafy.xyz/sauce-motion-phase2/poster.jpg";
const initialCatalog:Catalog={available:false,recordings:[
 {id:"brimble",title:"Brimble · Connect an agent",subtitle:"Real product interaction"},
 {id:"sauce",title:"Sauce · Workspace creation",subtitle:"Local demo trace"},
]};
function humanStatus(state:Job["state"]) {
 return state==="queued"?"In queue":state==="rendering"?"Rendering frames":state==="ready"?"Ready to watch":"Render failed";
}
export function StudioScreen(){
 const [catalog,setCatalog]=useState<Catalog>(initialCatalog);
 const [recording,setRecording]=useState<Recording>("brimble");
 const [preset,setPreset]=useState<Flavor>("3d-launch");
 const [foley,setFoley]=useState(true);
 const [job,setJob]=useState<Job|null>(null);
 const [sending,setSending]=useState(false);
 const [connectionLost,setConnectionLost]=useState(false);
 const [error,setError]=useState("");
 const [soundOn,setSoundOn]=useState(false);
 const flavor=flavors.find(f=>f.id===preset)!;
 const reference=recording==="brimble"&&preset==="3d-launch"&&foley;
 const isWorking=sending||job?.state==="queued"||job?.state==="rendering";
 const videoSrc=job?.state==="ready"?job.previewUrl:!job&&reference?publicDemo:undefined;
 const poster=reference?publicPoster:undefined;
 const activeVideo=useMemo(()=>`${recording}-${preset}-${foley}-${job?.id||"ref"}`,[recording,preset,foley,job?.id]);
 useEffect(()=>{
  let alive=true;
  fetch(`${basePath}/api/studio/catalog`,{cache:"no-store"}).then(r=>r.json()).then((data:Catalog)=>{
    if(alive&&data&&Array.isArray(data.recordings))setCatalog(data);
  }).catch(()=>{if(alive)setError("The rendering worker is unavailable.");});
  return ()=>{alive=false;};
 },[]);
 useEffect(()=>{
  // A reload should reconnect to the real job, not reset the screen to idle.
  const saved=window.sessionStorage.getItem("sauce-studio-job");
  if(!saved || !/^(brimble|sauce)-(clean-studio|3d-launch|hyper-cut)-(sound|silent)$/.test(saved))return;
  let alive=true;
  fetch(basePath+"/api/studio/jobs/"+encodeURIComponent(saved),{cache:"no-store"})
    .then(r=>{if(!r.ok)throw new Error("Job is no longer available");return r.json();})
    .then((data:{job:Job})=>{
      if(!alive||!data.job)return;
      setRecording(data.job.recording);setPreset(data.job.preset);setFoley(data.job.foley);
      setJob(data.job);
    }).catch(()=>{window.sessionStorage.removeItem("sauce-studio-job");});
  return ()=>{alive=false;};
 },[]);
 useEffect(()=>{
  if(!job||!["queued","rendering"].includes(job.state))return;
  let alive=true;
  const timer=setInterval(()=>{
   fetch(`${basePath}/api/studio/jobs/${encodeURIComponent(job.id)}`,{cache:"no-store"})
    .then(r=>{
      if(r.status===404) {
        setJob(current=>current?{...current,state:"failed",message:"Render worker restarted. Start this film again."}:null);
        window.sessionStorage.removeItem("sauce-studio-job");
        throw new Error("Job no longer exists");
      }
      if(!r.ok)throw new Error("Status check failed");
      return r.json();
    })
    .then((data:{job:Job})=>{
      if(!alive)return;
      if(data.job){setJob(data.job);setConnectionLost(false);}
    })
    .catch(()=>{if(alive)setConnectionLost(true);});
  },1600);
  return ()=>{alive=false;clearInterval(timer);};
 },[job?.id,job?.state]);
 const change= (next:Recording,flavor:Flavor,sound:boolean)=>{
  setRecording(next);setPreset(flavor);setFoley(sound);setJob(null);setError("");setConnectionLost(false);setSoundOn(false);
  window.sessionStorage.removeItem("sauce-studio-job");
 };
 async function render(){
  if(!catalog.available||sending)return;
  setSending(true);setJob(null);setError("");setConnectionLost(false);
  try{
   const response=await fetch(`${basePath}/api/studio/jobs`,{
    method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({recording,preset,foley}),
   });
   const data=await response.json();
   if(!response.ok||!data.job)throw new Error(data.error||"Could not start render");
   setJob(data.job as Job);
   window.sessionStorage.setItem("sauce-studio-job",(data.job as Job).id);
  }catch(e){setError(e instanceof Error?e.message:"Could not start render");}
  finally{setSending(false);}
 }
 return <div className={styles.shell}>
  <header className={styles.topbar}>
   <div className={styles.brandArea}>
    <Link href="/" className={styles.brand} aria-label="Sauce home">Sauce</Link>
    <div className={styles.brandRule}/>
    <span className={styles.workspace}>Studio <span className={styles.beta}>Preview</span></span>
   </div>
   <div className={styles.topActions}>
    <span className={styles.availability}><span className={catalog.available?styles.online:styles.offline}/>{catalog.available?"Render worker online":"Render worker offline"}</span>
    <Link href="/" className={styles.back}>Back to Sauce <span aria-hidden>↗</span></Link>
   </div>
  </header>
  <main className={styles.page}>
   <div className={styles.headline}>
    <div><span className={styles.index}>01 / Studio</span>
     <h1>Make a recording <em>worth watching.</em></h1>
     <p>Choose the moment. Pick a flavor. Sauce handles the camera, timing and details.</p>
    </div>
    <div className={styles.headMeta}>1080p <span>·</span> 60 fps <span>·</span> Verified browser frames</div>
   </div>
   <div className={styles.workbench}>
    <aside className={styles.controls}>
     <div className={styles.controlSection}>
      <div className={styles.sectionHeading}><span>01</span><h2>Your recording</h2></div>
      <label htmlFor="recording" className={styles.fieldLabel}>Verified source</label>
      <select id="recording" className={styles.select} value={recording}
       onChange={e=>change(e.target.value as Recording,preset,foley)}>
       {catalog.recordings.map(r=><option key={r.id} value={r.id}>{r.title}</option>)}
      </select>
      <p className={styles.helper}>{catalog.recordings.find(r=>r.id===recording)?.subtitle}. Sample recordings only in this pilot.</p>
     </div>
     <div className={styles.controlSection}>
      <div className={styles.sectionHeading}><span>02</span><h2>Choose a flavor</h2></div>
      <div className={styles.presets} role="group" aria-label="Motion preset">
       {flavors.map((f,i)=><button type="button" key={f.id}
         className={`${styles.preset} ${preset===f.id?styles.presetSelected:""}`}
         aria-pressed={preset===f.id} onClick={()=>change(recording,f.id,foley)}>
        <span className={`${styles.presetIcon} ${styles[`presetArt${i}`]}`} aria-hidden>
         <i/><b/><i/>
        </span>
        <span className={styles.presetCopy}><strong>{f.name}</strong><small>{f.detail}</small></span>
        <span className={styles.presetCheck} aria-hidden>{preset===f.id?"●":"○"}</span>
       </button>)}
      </div>
     </div>
     <div className={styles.controlSection}>
      <div className={styles.sectionHeading}><span>03</span><h2>Finish</h2></div>
      <label className={styles.toggleRow}>
       <span><strong>Foley sound</strong><small>Clicks, whooshes, modal details</small></span>
       <input type="checkbox" role="switch" checked={foley}
         onChange={e=>change(recording,preset,e.target.checked)}/>
       <span className={styles.switchTrack} aria-hidden><span/></span>
      </label>
      <p className={styles.helper}>Timed to the final edit, not the original recording.</p>
     </div>
     <button type="button" onClick={render}
      disabled={!catalog.available||sending||job?.state==="rendering"||job?.state==="queued"}
      className={styles.renderButton}>
      <span>{sending?"Starting…":job?.state==="rendering"?"Rendering…":job?.state==="queued"?"In queue…":`Render ${flavor.name}`}</span>
      <span aria-hidden>↗</span>
     </button>
     {job&&<div className={styles.jobResult} aria-live="polite">
      <span className={styles.jobDot}/><div><strong>{humanStatus(job.state)}</strong>
       <p>{job.message||"Preparing export"}</p></div>
     </div>}
     {error&&<p role="alert" className={styles.error}>{error}</p>}
     {!catalog.available&&<p className={styles.helper}>Render buttons activate on the configured Vultr worker. The sample film can still be viewed.</p>}
    </aside>
    <section className={styles.previewSection} aria-label="Film preview">
      <div className={styles.previewTop}>
       <div><span className={styles.previewEyebrow}>Playback</span><h2>{flavor.name}</h2></div>
       <div className={styles.previewHeaderActions}>
         <span className={styles.resolution}>16:9 <span>·</span> H.264</span>
         <button type="button" className={styles.previewRender}
           disabled={!catalog.available||sending||job?.state==="rendering"||job?.state==="queued"}
           onClick={render}>
           {sending||job?.state==="rendering"||job?.state==="queued"?"Working…":"Create film"} <span aria-hidden>↗</span>
         </button>
       </div>
      </div>
      <div className={[styles.stage,isWorking?styles.stageWorking:""].join(" ")} aria-busy={isWorking}>
       {isWorking?
        <RenderProgress job={job} sending={sending} title={catalog.recordings.find(r=>r.id===recording)?.title||recording} flavor={flavor.name} connectionLost={connectionLost}/>:
       videoSrc?
        <video key={activeVideo} controls autoPlay muted={!soundOn} playsInline
          preload="metadata" poster={poster} className={styles.video} src={videoSrc}
          aria-label={`${flavor.name} demo video`}/>:
        <div className={styles.emptyFilm}>
         <div className={styles.emptyWindow}><span/><span/><span/></div>
         <span className={styles.emptyText}>Your {flavor.name} film appears here.</span>
         <span className={styles.emptyHint}>Render this flavor to see the actual output.</span>
        </div>
       }
      </div>
      <div className={styles.previewBottom}>
       <div><strong>{isWorking?"Producing your film":job?.state==="ready"?"Rendered export":job?.state==="failed"?"Render unsuccessful":videoSrc?"Reference film":"Awaiting render"}</strong>
         <p>{isWorking?"Live renderer updates appear above. Frame counts are measured, not estimated.":job?.state==="ready"?"The result above was generated by the real Sauce engine.":job?.state==="failed"?"The export did not complete. You can try this preset again.":videoSrc?"Brimble, rendered with the 3D Launch preset.":"The selected preset has not been rendered yet."}</p>
       </div>
       <div className={styles.previewActions}>
        {videoSrc&&<button type="button" className={styles.soundButton}
         onClick={()=>setSoundOn(v=>!v)} aria-label={soundOn?"Mute preview":"Enable preview audio"}>
          {soundOn?"Sound on":"Hear Foley"}
         </button>}
        {job?.state==="ready"&&job.masterUrl&&<a className={styles.download} href={job.masterUrl} download>1080p master ↗</a>}
       </div>
      </div>
      <div className={styles.proof}>
       <div><strong>Real actions</strong><span>Not invented motion</span></div>
       <div><strong>Frame accurate</strong><span>Verified 60fps timeline</span></div>
       <div><strong>Made to ship</strong><span>One click to a finished MP4</span></div>
      </div>
    </section>
   </div>
  </main>
 </div>;
}
