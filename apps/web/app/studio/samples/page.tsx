import type {Metadata} from "next";
import Link from "next/link";
import {StudioScreen} from "../studio-client";
export const metadata:Metadata={
 title:"Sample recordings — Sauce Studio",
 description:"Try Sauce presets with verified sample recordings."
};
export default function SamplesPage(){
 return <><div style={{background:"#111116",padding:"14px 5%",color:"#dcb28d",fontSize:13}}>
  <Link style={{color:"inherit"}} href="/studio">← Create a film from a URL</Link>
 </div><StudioScreen/></>;
}
