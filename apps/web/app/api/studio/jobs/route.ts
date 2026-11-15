import { NextRequest, NextResponse } from "next/server";
import { describeJob, submitJob, studioAvailable } from "../../../../lib/studio-renderer";
export const runtime="nodejs";
export const dynamic="force-dynamic";
function sameOrigin(request:NextRequest) {
  const origin=request.headers.get("origin");
  const hostname=request.headers.get("x-forwarded-host") || request.headers.get("host");
  try { return !!origin && new URL(origin).host === hostname; }
  catch { return false; }
}
export async function POST(request:NextRequest) {
  if(!sameOrigin(request))
    return NextResponse.json({error:"Same-origin request required"},{status:403});
  if(!studioAvailable())
    return NextResponse.json({error:"Rendering worker is not configured"},{status:503});
  if(Number(request.headers.get("content-length")||0)>512)
    return NextResponse.json({error:"Invalid request size"},{status:413});
  try {
    const body=await request.json() as Record<string,unknown>;
    if(!body || typeof body!=="object" || Object.keys(body).some(k=>!["recording","preset","foley"].includes(k)))
      return NextResponse.json({error:"Invalid render request"},{status:400});
    const job=submitJob(body.recording,body.preset,body.foley);
    return NextResponse.json({job:describeJob(job)},{status:job.state==="ready"?200:202,headers:{"Cache-Control":"no-store"}});
  } catch(e) {
    const kind=(e as Error).message;
    return NextResponse.json({error:kind==="capacity"?"Render catalog is at capacity":kind==="unavailable"?"Worker unavailable":"Select a valid recording and preset"},
      {status:kind==="capacity"?429:kind==="unavailable"?503:400});
  }
}
