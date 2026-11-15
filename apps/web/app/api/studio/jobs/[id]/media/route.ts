import { readMedia } from "../../../../../../lib/studio-renderer";
export const runtime="nodejs";
export const dynamic="force-dynamic";
export async function GET(request:Request,{params}:{params:Promise<{id:string}>}) {
  const {id}=await params;
  const type=new URL(request.url).searchParams.get("type");
  if(type!=="preview"&&type!=="master")return new Response("Invalid media type",{status:400});
  const data=readMedia(id,type);
  if(!data)return new Response("Render unavailable",{status:404});
  const range=request.headers.get("range");
  const headers:Record<string,string>={
    "Content-Type":"video/mp4",
    "Cache-Control":"private, max-age=120",
    "Accept-Ranges":"bytes",
    "X-Content-Type-Options":"nosniff",
  };
  if(range) {
    const match=/^bytes=(\d+)-(\d*)$/.exec(range);
    if(!match)return new Response(null,{status:416,headers:{"Content-Range":`bytes */${data.length}`}});
    const start=Number(match[1]);
    const end=match[2]?Math.min(Number(match[2]),data.length-1):data.length-1;
    if(start>=data.length||end<start)
      return new Response(null,{status:416,headers:{"Content-Range":`bytes */${data.length}`}});
    headers["Content-Range"]=`bytes ${start}-${end}/${data.length}`;
    headers["Content-Length"]=String(end-start+1);
    return new Response(new Uint8Array(data.subarray(start,end+1)),{status:206,headers});
  }
  headers["Content-Length"]=String(data.length);
  return new Response(new Uint8Array(data),{headers});
}
