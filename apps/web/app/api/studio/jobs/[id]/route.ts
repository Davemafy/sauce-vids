import { NextResponse } from "next/server";
import { describeJob, getJob } from "../../../../../lib/studio-renderer";
export const runtime="nodejs";
export const dynamic="force-dynamic";
export async function GET(_:Request,{params}:{params:Promise<{id:string}>}) {
  const {id}=await params;
  const job=getJob(id);
  return NextResponse.json(job?{job:describeJob(job)}:{error:"Job not found"},
    {status:job?200:404,headers:{"Cache-Control":"no-store"}});
}
