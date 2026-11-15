import { NextResponse } from "next/server";
import { RECORDINGS, studioAvailable } from "../../../../lib/studio-renderer";
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export function GET() {
  return NextResponse.json({
    available: studioAvailable(),
    recordings: Object.values(RECORDINGS).map(({id,title,subtitle}) => ({id,title,subtitle})),
    presets: ["clean-studio","3d-launch","hyper-cut"],
    mode: "bounded-demo-catalog",
  }, { headers: {"Cache-Control":"no-store"} });
}
