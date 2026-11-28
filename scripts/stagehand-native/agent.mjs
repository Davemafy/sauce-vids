/** Stagehand owns the autonomous execution loop. Sauce only records evidence.
 * This adapter is for a previously authorized, secret-free product surface.
 * The caller MUST independently enforce browser/network authorization. No
 * credential-bearing page or untrusted CDP connection is admitted here.
 */
import { mkdir, appendFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import { performance } from 'node:perf_hooks';

const digest = b => createHash('sha256').update(b).digest('hex');
const cleanUsage = u => Object.fromEntries(Object.entries(u ?? {}).filter(([k,v]) => /^[A-Za-z_]+$/.test(k) && typeof v === 'number' && Number.isFinite(v) && v >= 0));
const safeName = name => typeof name === 'string' && /^[A-Za-z][A-Za-z0-9_]{0,63}$/.test(name) ? name : 'unknown';

export async function executeNativeTask({stagehand, page, model, instruction, out, assertSurface, verifyOutcome, maxSteps=12, timeoutMs=90000}) {
  if(!/^google\/gemini-[A-Za-z0-9.-]+$/.test(model))throw new Error('Gemini only');
  if(typeof instruction !== 'string'||!instruction.trim()||instruction.length>3000)throw new Error('Invalid objective');
  if(typeof assertSurface !== 'function'||typeof verifyOutcome !== 'function')throw new Error('Independent scope and outcome verification required');
  if(!Number.isInteger(maxSteps)||maxSteps<1||maxSteps>24||!Number.isInteger(timeoutMs)||timeoutMs<1000||timeoutMs>180000)throw new Error('Invalid execution budget');
  await assertSurface();
  await mkdir(out,{mode:0o700});
  const start=performance.now(), controller=new AbortController();
  const timer=setTimeout(()=>controller.abort(),timeoutMs);
  let stepCount=0, evidenceCount=0, screenshotCount=0, blocked=false, result=null, errorType=null;
  async function save(row){await appendFile(join(out,'evidence.jsonl'),JSON.stringify({t:Math.round(performance.now()-start),...row})+'\n',{mode:0o600});}
  async function check(){try{await assertSurface();}catch{blocked=true;controller.abort();throw new Error('Product surface no longer authorized');}}
  async function retain(bytes){
    await check();
    if(!Buffer.isBuffer(bytes)||bytes.length<8||bytes.length>20_000_000)return;
    const name=`frame-${String(++screenshotCount).padStart(4,'0')}.png`;
    await writeFile(join(out,name),bytes,{mode:0o600,flag:'wx'});
    await save({type:'frame',file:name,sha256:digest(bytes)});
  }
  try{
    const agent=stagehand.agent({mode:'dom',model,executionModel:model});
    result=await agent.execute({instruction,maxSteps,page,signal:controller.signal,toolTimeout:15000,excludeTools:['search'],callbacks:{
      prepareStep:async()=>{await check();return {};},
      onStepFinish:async step=>{await check();stepCount++;await save({type:'step',tools:(step.toolCalls??[]).map(c=>safeName(c.toolName)),usage:cleanUsage(step.usage)});},
      onEvidence:async event=>{
        // Do not persist action args, raw model responses, reasoning, URLs, AX trees or tool outputs.
        await check();evidenceCount++;
        if(event.type==='step_finished')await save({type:'action',tool:safeName(event.actionName),ok:event.toolOutput?.ok===true});
        else if(event.type==='screenshot')await retain(event.screenshot);
        else if(event.type==='step_observed')await save({type:'observation'});
        else if(event.type==='final_answer'&&event.observation?.screenshot)await retain(event.observation.screenshot);
      }
    }});
  }catch(e){errorType=safeName(e?.name);}
  finally{clearTimeout(timer);}
  let verified=false;
  if(!blocked){try{await check();verified=(await verifyOutcome())===true;}catch{verified=false;}}
  // Agent's own success bit is not a verification or a creative approval.
  const receipt={schema:'sauce-stagehand-native-v1',model,stepCount,evidenceCount,screenshotCount,elapsedMs:Math.round(performance.now()-start),agentReportedSuccess:result?.success===true,verifiedOutcome:verified,scopeBlocked:blocked,errorType,usage:cleanUsage(result?.usage),metrics:cleanUsage(await stagehand.metrics),creativeApproved:false};
  await writeFile(join(out,'receipt.json'),JSON.stringify(receipt,null,2)+'\n',{mode:0o600,flag:'wx'});
  return receipt;
}
