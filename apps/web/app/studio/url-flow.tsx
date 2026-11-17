"use client";
import {useCallback,useEffect,useState,type FormEvent} from "react";
import Link from "next/link";
import s from "./url-flow.module.css";
import {FilmLibrary,rememberFilm,recentFilmIds} from "./film-library";

const api=(process.env.NEXT_PUBLIC_SAUCE_BASE_PATH||"")+"/api/studio/url";
type Stage="queued"|"inspecting"|"directing"|"capturing"|"rendering"|"needs_access"|"needs_review"|"failed"|"needs_key";
type Job={id:string;url:string;stage:Stage;status:string;reason?:string;error?:string;message?:string;created_at?:number;updated_at?:number;stage_started_at?:number;frames_rendered?:number;frames_total?:number;title?:string;ai_calls?:number;capture_mode?:"interactive"|"showcase";render_mode?:string;direction_source?:string;video_type?:string;};
const steps:[Stage,string,string][]=[
 ["inspecting","Explore","Reading real page structure"],
 ["directing","Direct","Finding the story worth showing"],
 ["capturing","Capture","Recording actual browser motion"],
 ["rendering","Produce","Encoding continuous browser footage"],
];
const elapsed=(ms:number)=>{
 const seconds=Math.max(0,Math.floor(ms/1000));
 return String(Math.floor(seconds/60)).padStart(2,"0")+":"+String(seconds%60).padStart(2,"0");
};
function host(raw:string){try{return new URL(raw).hostname;}catch{return raw;}}
function urlValue(raw:string){
 const trimmed=raw.trim();
 return /^https?:\/\//i.test(trimmed)?trimmed:"https://"+trimmed;
}
const titles:Record<string,string>={
 queued:"Your film is in line.",
 inspecting:"Getting to know the product.",
 directing:"Finding the moment worth watching.",
 capturing:"Recording what actually happens.",
 rendering:"Building your film, frame by frame.",
};
const details:Record<string,string>={
 queued:"Your request was accepted. Waiting for a free capture slot.",
 inspecting:"Reading real page structure, visible controls, and design signals.",
 directing:"One AI call decides whether this product can be filmed faithfully.",
 capturing:"Recording real scrolling, pointer motion, and visible UI changes.",
 rendering:"Encoding the continuous browser recording into your playable film.",
};

export function UrlFlowScreen(){
 const [url,setUrl]=useState("");
 const [code,setCode]=useState("");
 const [unlocked,setUnlocked]=useState(false);
 const [authLoading,setAuthLoading]=useState(true);
 const [authBusy,setAuthBusy]=useState(false);
 const [jobId,setJobId]=useState<string|null>(null);
 const [job,setJob]=useState<Job|null>(null);
 const [sending,setSending]=useState(false);
 const [pollError,setPollError]=useState(false);
 const [error,setError]=useState("");
 const [now,setNow]=useState(()=>Date.now());
 const [rating,setRating]=useState(0);
 const [review,setReview]=useState("");
 const [saving,setSaving]=useState(false);
 const [saved,setSaved]=useState(false);

 const readJob=useCallback(async(id:string)=>{
  const response=await fetch(api+"/jobs/"+id,{cache:"no-store"});
  if(response.status===401){setUnlocked(false);throw new Error("Pilot session expired");}
  if(!response.ok)throw new Error("Job status unavailable");
  const data=await response.json() as {job:Job};
  if(data.job){setJob(data.job);setPollError(false);}
 },[]);

 useEffect(()=>{
  let live=true;
  const shared=new URLSearchParams(window.location.search).get("job");
  const previous=shared&&/^[a-f0-9]{24}$/.test(shared)?shared:(sessionStorage.getItem("sauce-url-job")||recentFilmIds()[0]);
  if(previous&&/^[a-f0-9]{24}$/.test(previous)){
    setJobId(previous);sessionStorage.setItem("sauce-url-job",previous);
    rememberFilm(previous);
  }
  fetch(api+"/auth",{cache:"no-store"}).then(r=>r.json()).then(data=>{
   if(live)setUnlocked(data.authorized===true);
  }).catch(()=>{if(live)setError("Could not connect to the private studio.");})
    .finally(()=>{if(live)setAuthLoading(false);});
  const timer=setInterval(()=>setNow(Date.now()),1000);
  return ()=>{live=false;clearInterval(timer);};
 },[]);

 const terminal=job?.status==="needs_review"||job?.status==="needs_access"||job?.status==="failed"||job?.status==="needs_key";
 useEffect(()=>{
  if(!unlocked||!jobId||terminal)return;
  let live=true;
  const poll=()=>readJob(jobId).catch(()=>{if(live)setPollError(true);});
  poll();
  const timer=setInterval(poll,1600);
  return ()=>{live=false;clearInterval(timer);};
 },[unlocked,jobId,terminal,readJob]);

 async function authorize(event:FormEvent<HTMLFormElement>){
  event.preventDefault();setError("");setAuthBusy(true);
  try{
   const response=await fetch(api+"/auth",{
    method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({code:code.trim()}),
   });
   const body=await response.json();
   if(!response.ok)throw Error(body.error||"Access denied");
   setUnlocked(true);setCode("");
  }catch(e){setError(e instanceof Error?e.message:"Access could not be verified.");}
  finally{setAuthBusy(false);}
 }
 async function begin(event:FormEvent<HTMLFormElement>){
  event.preventDefault();
  if(!unlocked||sending)return;
  setError("");setSending(true);setJobId(null);setJob(null);setRating(0);setReview("");setSaved(false);
  sessionStorage.removeItem("sauce-url-job");
  try{
   const value=urlValue(url);
   const parsed=new URL(value);
   if(!["https:","http:"].includes(parsed.protocol))throw Error("Use a public HTTP or HTTPS URL.");
   // Avoid sending unreviewed tracking or access tokens from copied URL queries.
   parsed.search="";parsed.hash="";
   const publicUrl=parsed.toString();
   const response=await fetch(api+"/jobs",{
    method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url:publicUrl}),
   });
   const body=await response.json();
   if(!response.ok)throw Error(body.error||"Could not create film job");
   const id=body.jobId as string;
   if(!/^[a-f0-9]{24}$/.test(id))throw Error("Invalid job identifier");
   setJobId(id);sessionStorage.setItem("sauce-url-job",id);
   rememberFilm(id);
   setJob({id,url:publicUrl,stage:"queued",status:"queued",created_at:Date.now()/1000});
  }catch(e){setError(e instanceof Error?e.message:"Could not start this film");}
  finally{setSending(false);}
 }
 async function submitReview(){
  if(!jobId||!rating||saving)return;
  setSaving(true);setError("");
  try{
   const response=await fetch(api+"/jobs/"+jobId+"/feedback",{
    method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({rating,notes:review}),
   });
   const body=await response.json();
   if(!response.ok)throw Error(body.error||"Could not save review");
   setSaved(true);
  }catch(e){setError(e instanceof Error?e.message:"Could not save review");}
  finally{setSaving(false);}
 }
 const stage=job?.stage||"queued";
 const ready=job?.status==="needs_review";
 const blocked=job?.status==="needs_access";
 const failed=job?.status==="failed"||job?.status==="needs_key";
 const working=!!jobId&&unlocked&&!terminal;
 const showProgress=sending||working;
 const current=Math.max(0,steps.findIndex(x=>x[0]===stage));
 const total=job?.frames_total||0;
 const measured=stage==="rendering"&&total>0;
 const count=Math.min(total,Math.max(0,job?.frames_rendered||0));
 const duration=job?.created_at?now-job.created_at*1000:0;
 function clearJob(){setJobId(null);setJob(null);setPollError(false);setError("");sessionStorage.removeItem("sauce-url-job");}
 function openSavedFilm(id:string){
  setJob(null);setJobId(id);setPollError(false);setError("");
  sessionStorage.setItem("sauce-url-job",id);
  rememberFilm(id);
  void readJob(id).catch(()=>setPollError(true));
 }
 return <div className={s.shell}>
  <header className={s.topbar}>
   <Link href="/" className={s.brand} aria-label="Sauce home">Sauce</Link>
   <div className={s.topRight}><span>Studio</span><i aria-hidden="true"/><span>From URL</span><Link href="/studio/samples">Sample recordings</Link></div>
  </header>
  <main className={s.main}>
   <div className={s.intro}>
    <div><span className={s.kicker}>Create a product film</span>
     <h1>Your product deserves <em>a better take.</em></h1>
     <p>Give Sauce a link. It explores the public product, directs a sequence, and builds a film from what actually exists.</p>
    </div>
    <aside className={s.introAside}>Real screens.<br/>Directed motion.<br/>No invented demos.</aside>
   </div>
   <div className={s.card}>
    <div className={s.cardHead}><strong>Start with a link</strong><span>Private pilot</span></div>
    <form className={s.urlForm} onSubmit={begin}>
     <label htmlFor="source-url">Product website</label>
     <div className={s.formRow}>
      <input id="source-url" type="text" inputMode="url" autoComplete="url"
       placeholder="https://yourproduct.com" value={url}
       onChange={e=>setUrl(e.target.value)} required disabled={showProgress}/>
      <button type="submit" disabled={!unlocked||showProgress||!url.trim()}>
       {sending?"Starting…":showProgress?"Making film…":"Make film"} <span aria-hidden="true">↗</span>
      </button>
     </div>
     <p className={s.fieldNote}>Public websites only. No sign-ins or application submissions.</p>
    </form>
    {!authLoading&&!unlocked&&<form onSubmit={authorize} className={s.access}>
     <div><strong>Unlock private pilot</strong><p>Rendering is currently reserved for invited testers.</p></div>
     <div className={s.accessRow}>
      <input type="password" aria-label="Private pilot access code" placeholder="Access code" autoComplete="off" value={code} onChange={e=>setCode(e.target.value)} required/>
      <button type="submit" disabled={authBusy||!code.trim()}>{authBusy?"Checking…":"Unlock"}</button>
     </div>
    </form>}
    {unlocked&&<div className={s.connected}><i aria-hidden="true">✓</i> Private worker connected <span>·</span> One AI direction call per job</div>}
    {authLoading&&<p role="status" className={s.fieldNote}>Checking pilot access…</p>}
   </div>
   {error&&<div className={s.error} role="alert">{error}</div>}
   {!showProgress&&!jobId&&<div className={s.idle}>
    <div className={s.idleFrames} aria-hidden="true"><span/><span/><span/></div>
    <h2>From a link to a film.</h2>
    <p>When production starts, this space becomes a live desk showing what Sauce is actually doing.</p>
    <div className={s.idleSteps}><span>Explore</span><span>Direct</span><span>Capture</span><span>Produce</span></div>
   </div>}

   {showProgress&&<section className={s.production} aria-label="Live URL film production status" aria-busy="true">
    <div className={s.productionHead}><span className={s.live}><i aria-hidden="true"/> Production in progress</span><time aria-label="Elapsed time">{elapsed(duration)}</time></div>
    <div className={s.productionMain}>
     <div className={s.frames} aria-hidden="true">
      <div className={s.frameStack}><span>01</span><span>02</span><span>03</span></div>
      <div className={s.scanner}/>
     </div>
     <div className={s.productionCopy}>
      <span className={s.domain}>{host(job?.url||urlValue(url))}</span>
      <h2>{sending?"Opening the render desk.":titles[stage]||"Continuing production."}</h2>
      <p aria-live="polite" aria-atomic="true">{pollError?"Status connection interrupted. Reconnecting without stopping the job…":details[stage]||"Sauce is working on the edit."}</p>
      <small>You can close this tab. Sauce will finish the job on the server and keep the review link for your return.</small>
     </div>
    </div>
    <div className={s.productionFooter}>
     <div className={s.readout}><strong>{measured?"Compositing real frames":sending?"Starting job":steps[current]?.[1]||"Preparing"}</strong><span>{measured?count.toLocaleString()+" / "+total.toLocaleString()+" frames":"Stage "+(current+1)+" of 4"}</span></div>
     <div className={s.rail+(measured?"":" "+s.waitingRail)}
       role={measured?"progressbar":"status"} aria-label={measured?"Verified frames rendered":"Current production stage"}
       {...(measured?{"aria-valuemin":0,"aria-valuemax":total,"aria-valuenow":count}:{})}>
      {measured&&<span style={{width:Math.round(count/total*100)+"%"}}/>}
     </div>
     <ol className={s.steps} aria-label="Production stages">{steps.map(([id,label,detail],i)=>
      <li key={id} className={(i===current?s.active:"")+(i<current?" "+s.complete:"")}>
       <span>{i<current?"✓":String(i+1).padStart(2,"0")}</span>
       <div><strong>{label}</strong><small>{detail}</small></div>
      </li>)}</ol>
    </div>
   </section>}

   {terminal&&<section className={s.result} aria-live="polite">
    <div className={s.resultHead}><span>{ready?(job?.render_mode==="continuous-browser-capture"?"Continuous recording · Review required":"Earlier still-frame draft"):blocked?"Capture paused":"Production stopped"}</span><time>{elapsed(duration)}</time></div>
    {ready&&<><h2>Your first cut is ready.</h2>
     <p>{job?.render_mode==="continuous-browser-capture"?
       (job?.capture_mode==="interactive"?
       "Continuous real browser footage, including a safe observed interaction. Private functionality and independent replay remain unverified. Review before sharing.":
       "Continuous public-website footage with real scrolling. Sign-in-only product features are not demonstrated. Review before sharing."):
       "This older draft was assembled from still screenshots. Re-create this URL to get a continuous browser recording instead."}</p>
     <video src={api+"/jobs/"+jobId+"/media"} className={s.video} controls preload="metadata" playsInline aria-label="AI-directed Sauce video preview"/>
     <div className={s.outputLinks}>
       <a href={api+"/jobs/"+jobId+"/media"} download={"sauce-"+(job?.capture_mode||"preview")+".mp4"}>Download MP4 <span aria-hidden="true">↓</span></a>
       <a href={(process.env.NEXT_PUBLIC_SAUCE_BASE_PATH||"")+"/studio?job="+jobId}>Open review link <span aria-hidden="true">↗</span></a>
     </div>
     <div className={s.review}>
      <h3>Would you share this?</h3><p>Review notes inform future jobs. An approved film will not be regenerated automatically.</p>
      <div className={s.stars} role="group" aria-label="Rate film quality from one to five">{[1,2,3,4,5].map(n=><button key={n} type="button" aria-label={"Rate "+n+" out of 5"} aria-pressed={rating===n} onClick={()=>{setRating(n);setSaved(false);}} className={rating===n?s.chosen:""}>{n}</button>)}</div>
      <label htmlFor="film-feedback">What should change? <span>(optional)</span></label>
      <textarea id="film-feedback" value={review} maxLength={2000} onChange={e=>setReview(e.target.value)} placeholder="Framing, pacing, readability…"/>
      <button className={s.reviewButton} type="button" disabled={!rating||saving} onClick={submitReview}>{saving?"Saving…":saved?"Review saved ✓":"Save review"}</button>
     </div>
    </>}
    {blocked&&<><h2>This product needs more than a link.</h2><p>{job?.reason||"The meaningful product workflow requires access. Sauce will not fabricate footage."}</p><div className={s.notice}>No video created. Use an authorized test account for the real workflow.</div></>}
    {failed&&<><h2>We couldn't complete this cut.</h2><p>{job?.message||"The attempt ended before Sauce produced a verified video. Nothing was published."}</p><div className={s.notice}>Try another accessible public URL. If this site requires sign-in or blocks automated browsers, Sauce cannot capture it anonymously.</div></>}
    <button type="button" className={s.another} onClick={clearJob}>↻ Make another film</button>
   </section>}
   <FilmLibrary authorized={unlocked} activeId={jobId} refreshKey={(jobId||"")+":"+(job?.stage||"")+":"+(job?.status||"")} onOpen={openSavedFilm}/>
   <footer className={s.footer}><span>Made with Sauce</span><span>One direction call. Real browser capture. Human-reviewed output.</span></footer>
  </main>
 </div>;
}
