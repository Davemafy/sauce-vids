import type { Metadata } from "next";
import { StudioScreen } from "./studio-client";
export const metadata:Metadata={
 title:"Sauce Studio — Make a recording worth watching",
 description:"Select a recording, choose Clean Studio, 3D Launch or Hyper-Cut, and render a real demo."
};
export default function StudioPage(){return <StudioScreen/>;}
