/** Native agent attached to a Sauce-guarded, unauthenticated browser. */
import { Stagehand } from '@browserbasehq/stagehand';
import { executeNativeTask } from './agent.mjs';
import { readFile } from 'node:fs/promises';
const config=JSON.parse(await readFile(process.argv[2],'utf8'));
const endpoint=new URL(config.cdpUrl), source=new URL(config.url);
if(endpoint.protocol!=='ws:'||endpoint.hostname!=='127.0.0.1'||!/^\/devtools\/browser\/[a-f0-9-]+$/.test(endpoint.pathname)||endpoint.username||endpoint.password||endpoint.search||endpoint.hash)throw Error('Private local Chromium endpoint required');
if(!['http:','https:'].includes(source.protocol)||source.username||source.password||source.search||source.hash)throw Error('Public source required');
if(!/^google\/gemini-[A-Za-z0-9.-]+$/.test(config.model))throw Error('Gemini only');
if(!process.env.GEMINI_API_KEY&&!process.env.GOOGLE_GENERATIVE_AI_API_KEY)throw Error('Gemini not configured');
process.env.GOOGLE_GENERATIVE_AI_API_KEY ||= process.env.GEMINI_API_KEY;
const stagehand=new Stagehand({env:'LOCAL',experimental:true,disableAPI:true,verbose:0,keepAlive:true,model:config.model,localBrowserLaunchOptions:{cdpUrl:config.cdpUrl}});
try{
 await stagehand.init();
 const pages=stagehand.context.pages();
 if(pages.length!==1||pages[0].url()!==config.url)throw Error('Unexpected initial browser surface');
 const page=pages[0];
 async function assertSurface(){
   if(stagehand.context.pages().length!==1||new URL(page.url()).origin!==source.origin)throw Error('Browser scope changed');
   const blocked=await page.evaluate(()=>Array.from(document.querySelectorAll('input[type=password],input[autocomplete=one-time-code],[data-private],[data-secret],[data-sensitive],iframe[src*=captcha],[data-sitekey]')).some(e=>e.checkVisibility()));
   if(blocked)throw Error('Sensitive or authentication surface');
 }
 const receipt=await executeNativeTask({stagehand,page,model:config.model,instruction:config.instruction,out:config.out,maxSteps:config.maxSteps,timeoutMs:config.timeoutMs,assertSurface,
   // Generic agent success is not independent semantic completion.
   verifyOutcome:async()=>false});
 console.log(JSON.stringify({schema:receipt.schema,steps:receipt.stepCount,reportedSuccess:receipt.agentReportedSuccess,verifiedOutcome:receipt.verifiedOutcome,scopeBlocked:receipt.scopeBlocked,errorType:receipt.errorType}));
}finally{await stagehand.close().catch(()=>{});}
