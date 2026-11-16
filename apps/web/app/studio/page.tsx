import type {Metadata} from "next";
import {UrlFlowScreen} from "./url-flow";
export const metadata:Metadata={
 title:"URL to Film — Sauce Studio",
 description:"Turn a public product URL into a directed demo using real browser captures."
};
export default function StudioPage(){return <UrlFlowScreen/>;}
