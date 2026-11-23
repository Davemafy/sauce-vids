import {createHash,createHmac,timingSafeEqual} from "node:crypto";
import {NextRequest,NextResponse} from "next/server";
import {request as unixRequest} from "node:http";
import {existsSync} from "node:fs";

export const runtime="nodejs";
export const dynamic="force-dynamic";

const cookieName="sauce_url_pilot";
const maxAgeSeconds=6*60*60;
const cookiePath=(process.env.NEXT_PUBLIC_SAUCE_BASE_PATH||"")+"/api/studio/url";
type Context={params:Promise<{parts:string[]}>};
const jobPattern=/^[a-f0-9]{24}$/;
const cursorPacks=["founder-reference","studio-rounded","gloss-carbon","aero-prism","mint-studio"] as const;

function sameOrigin(req:NextRequest):boolean {
 const origin=req.headers.get("origin");
 const host=req.headers.get("x-forwarded-host")||req.headers.get("host");
 if(!origin||!host)return false;
 try {return new URL(origin).host.toLowerCase()===host.toLowerCase();}
 catch{return false;}
}
function equalsSecret(a:string,b:string):boolean {
 if(!a||!b)return false;
 const hash=(s:string)=>createHash("sha256").update(s).digest();
 return timingSafeEqual(hash(a),hash(b));
}
function signed(expires:number,secret:string) {
 return createHmac("sha256",secret).update(String(expires)).digest("hex");
}
function authenticated(req:NextRequest):boolean {
 const secret=process.env.SAUCE_URL_COOKIE_SECRET||"";
 if(secret.length<32)return false;
 const cookie=req.cookies.get(cookieName)?.value||"";
 const m=/^(\d{10})\.([a-f0-9]{64})$/.exec(cookie);
 if(!m)return false;
 const expiry=Number(m[1]);
 if(!Number.isSafeInteger(expiry)||expiry<=Math.floor(Date.now()/1000))return false;
 return equalsSecret(m[2],signed(expiry,secret));
}
const json=(body:object,status=200)=>NextResponse.json(body,{status,headers:{"Cache-Control":"no-store","X-Content-Type-Options":"nosniff"}});

const socketPath="/var/lib/sauce-url2video/sauce.sock";
async function backend(path:string,init?:RequestInit):Promise<Response> {
 if(!existsSync(socketPath))throw new Error("backend_unavailable");
 const body=typeof init?.body==="string"?init.body:undefined;
 return new Promise<Response>((resolve,reject)=>{
  const req=unixRequest({
   socketPath,path,method:init?.method||"GET",
   headers:body?{"Content-Type":"application/json","Content-Length":Buffer.byteLength(body)}:{},
  },res=>{
   const chunks:Buffer[]=[];
   let bytes=0;
   res.on("data",(chunk:Buffer)=>{
    bytes+=chunk.length;
    if(bytes>32*1024*1024){req.destroy(new Error("Media size limit"));return;}
    chunks.push(chunk);
   });
   res.on("end",()=>{
    const result=Buffer.concat(chunks);
    resolve(new Response(new Uint8Array(result),{
     status:res.statusCode||502,
     headers:{"Content-Type":String(res.headers["content-type"]||"application/octet-stream")},
    }));
   });
   res.on("error",reject);
  });
  req.setTimeout(12000,()=>req.destroy(new Error("Worker timeout")));
  req.on("error",reject);
  if(body)req.write(body);
  req.end();
 });
}
async function backendJson(path:string,body?:object) {
 const response=await backend(path,body?{
  method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body),
 }:undefined);
 return {status:response.status,data:await response.json()};
}
async function readBody(req:NextRequest){
 if(Number(req.headers.get("content-length")||"0")>2048)throw Error("large");
 const txt=await req.text();
 if(txt.length>2048)throw Error("large");
 const x=JSON.parse(txt);
 if(!x||typeof x!=="object"||Array.isArray(x))throw Error("bad");
 return x as Record<string,unknown>;
}

export async function GET(req:NextRequest,{params}:Context){
 const {parts}=await params;
 if(parts.length===1&&parts[0]==="auth")
  return json({authorized:authenticated(req),configured:existsSync(socketPath)});
 if(!authenticated(req))return json({error:"Pilot access required"},401);
 if(parts.length<2||parts[0]!=="jobs"||!jobPattern.test(parts[1]))
  return json({error:"Not found"},404);
 const id=parts[1];
 try{
  if(parts.length===2){
   const {status,data}=await backendJson("/v1/jobs/"+id);
   return json(status===200?{job:data}:{error:"Job unavailable"},status===200?200:404);
  }
  if(parts.length===3&&(parts[2]==="media"||parts[2]==="clean-media")){
   const video=parts[2]==="clean-media"?"preview-clean.mp4":"preview.mp4";
   const remote=await backend("/v1/jobs/"+id+"/"+video);
   if(!remote.ok)return json({error:"Preview not ready"},remote.status===404?404:502);
   const buf=await remote.arrayBuffer();
   return new NextResponse(buf,{status:200,headers:{
    "Content-Type":"video/mp4","Content-Length":String(buf.byteLength),
    "Cache-Control":"private, no-store","X-Content-Type-Options":"nosniff",
    "Accept-Ranges":"none",
   }});
  }
  return json({error:"Not found"},404);
 }catch{return json({error:"Could not reach the render worker"},503);}
}

export async function POST(req:NextRequest,{params}:Context) {
 const {parts}=await params;
 if(!sameOrigin(req))return json({error:"Same-origin request required"},403);
 let body:Record<string,unknown>;
 try{body=await readBody(req);}catch{return json({error:"Invalid request"},400);}
 if(parts.length===1&&parts[0]==="auth"){
  const supplied=body.code;
  if(typeof supplied!=="string"||supplied.length>128
    ||!equalsSecret(supplied,process.env.SAUCE_URL_ACCESS_CODE||""))
    return json({error:"Invalid pilot access code"},403);
  const expiry=Math.floor(Date.now()/1000)+maxAgeSeconds;
  const secret=process.env.SAUCE_URL_COOKIE_SECRET||"";
  if(secret.length<32)return json({error:"Pilot configuration unavailable"},503);
  const result=json({authorized:true});
  result.cookies.set(cookieName,String(expiry)+"."+signed(expiry,secret),{
    httpOnly:true,sameSite:"strict",secure:process.env.NODE_ENV==="production",
    maxAge:maxAgeSeconds,path:cookiePath,
  });
  return result;
 }
 if(!authenticated(req))return json({error:"Pilot access required"},401);
 if(parts.length===1&&parts[0]==="jobs"){
  const url=body.url;
  if(typeof url!=="string"||url.length>2048)
   return json({error:"Enter a valid public website URL"},400);
  try {
   const parsed=new URL(url);
   if(!["https:","http:"].includes(parsed.protocol)||parsed.username||parsed.password)
    return json({error:"Public HTTP(S) URLs only"},400);
   const cursorPack=body.cursorPack??"founder-reference";
   if(typeof cursorPack!=="string"||!(cursorPacks as readonly string[]).includes(cursorPack))
    return json({error:"Choose a supported cursor style"},422);
   const {status,data}=await backendJson("/v1/jobs",{url,brief:body.brief,audio:body.audio,cursorPack});
   return json(status===202?{jobId:data.job_id}:{error:data.error||"Unable to start job"},status);
  }catch(e){
   if(e instanceof TypeError)return json({error:"Enter a valid URL"},400);
   return json({error:"Render worker unavailable"},503);
  }
 }
 if(parts.length===3&&parts[0]==="jobs"&&jobPattern.test(parts[1])&&parts[2]==="revision"){
  try{
   const {status,data}=await backendJson("/v1/jobs/"+parts[1]+"/revision",{brief:body.brief,audio:body.audio});
   return json(status===202?{jobId:data.job_id}:{error:data.error||"Unable to revise film"},status);
  }catch{return json({error:"Render worker unavailable"},503);}
 }
 if(parts.length===3&&parts[0]==="jobs"&&jobPattern.test(parts[1])&&parts[2]==="feedback"){
  const rating=body.rating,notes=body.notes;
  if(!Number.isInteger(rating)||Number(rating)<1||Number(rating)>5||typeof notes!=="string"||notes.length>2000)
   return json({error:"Rate 1 to 5 with an optional short note"},400);
  try{
   const {status,data}=await backendJson("/v1/jobs/"+parts[1]+"/feedback",{rating,notes});
   return json(status===200?{saved:true}:{error:data.error||"Could not save review"},status);
  }catch{return json({error:"Review worker unavailable"},503);}
 }
 return json({error:"Not found"},404);
}
