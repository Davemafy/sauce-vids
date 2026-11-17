"use client";

import {useEffect,useState} from "react";
import s from "./film-library.module.css";

const key="sauce-recent-film-ids-v1";
const valid=/^[a-f0-9]{24}$/;
const api=(process.env.NEXT_PUBLIC_SAUCE_BASE_PATH||"")+"/api/studio/url";
const MAX_FILMS=12;
type Job={id:string;title?:string;url?:string;stage?:string;status?:string;capture_mode?:string;created_at?:number};
type Props={authorized:boolean;activeId:string|null;refreshKey:string;onOpen:(id:string)=>void};

export function recentFilmIds():string[]{
 if(typeof window==="undefined")return [];
 try{
  const stored=JSON.parse(window.localStorage.getItem(key)||"[]");
  if(!Array.isArray(stored))return [];
  return [...new Set(stored.filter((value:unknown):value is string=>
    typeof value==="string"&&valid.test(value)))].slice(0,MAX_FILMS);
 }catch{return [];}
}

export function rememberFilm(id:string){
 if(!valid.test(id)||typeof window==="undefined")return;
 try{window.localStorage.setItem(key,JSON.stringify([id,...recentFilmIds().filter(x=>x!==id)].slice(0,MAX_FILMS)));}
 catch{/* Private browsing may block localStorage; the review link still works. */}
}

function hostname(value?:string){
 if(!value)return "Website film";
 try{return new URL(value).hostname;}catch{return "Website film";}
}
function statusLabel(job:Job){
 if(job.status==="needs_review")return "Ready to review";
 if(job.status==="failed")return "Could not finish";
 if(job.status==="needs_access")return "Access required";
 if(job.status==="needs_key")return "Unavailable";
 if(job.stage==="rendering")return "Producing";
 if(job.stage==="capturing")return "Recording";
 if(job.stage==="directing"||job.stage==="inspecting")return "Preparing";
 return "Queued";
}

export function FilmLibrary({authorized,activeId,refreshKey,onOpen}:Props){
 const [ids,setIds]=useState<string[]>([]);
 const [items,setItems]=useState<Job[]>([]);
 useEffect(()=>{
  if(authorized)setIds(recentFilmIds());
 },[authorized,refreshKey]);
 useEffect(()=>{
  if(!authorized||!ids.length){setItems([]);return;}
  let mounted=true;
  Promise.all(ids.map(async id=>{
   try{
    const response=await fetch(api+"/jobs/"+id,{cache:"no-store"});
    if(!response.ok)return null;
    const payload=await response.json() as {job?:Job};
    return payload.job?.id===id?payload.job:null;
   }catch{return null;}
  })).then(found=>{if(mounted)setItems(found.filter((item):item is Job=>item!==null));});
  return ()=>{mounted=false;};
 },[ids,authorized,refreshKey]);
 if(!authorized||!ids.length)return null;
 return <section className={s.root} aria-label="Recent films on this device">
  <div className={s.head}>
   <div><h2>Recent films</h2><p>Your jobs continue on Sauce after you close this tab.</p></div>
   <span>Saved on this device</span>
  </div>
  <ul className={s.list}>
   {items.map(item=><li key={item.id}>
    <button type="button" onClick={()=>onOpen(item.id)}
     aria-current={activeId===item.id?"true":undefined}
     className={activeId===item.id?s.current:""}>
     <span className={s.name}>{item.title||hostname(item.url)}<small>{hostname(item.url)}</small></span>
     <span className={s.state}>{statusLabel(item)}</span>
     <span className={s.open} aria-hidden="true">Open</span>
    </button>
   </li>)}
  </ul>
  <p className={s.note}>Open a saved job to review or download its film. Your browser remembers up to 12 job links; this is not an account library or cross-device sync. Pilot access is still required.</p>
 </section>;
}
