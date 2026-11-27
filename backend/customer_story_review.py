"""Hash-bound editorial assessment of the actual long customer film.

Private research evidence only. Model observations cannot change source,
camera, audio, independent QA, or release approval.
"""
import json,subprocess,base64,math
import cv2
from pathlib import Path
from backend.curious_showcase import Conversation,_media
from backend.interactive_editorial import response

def review_sample_times(duration, manifest):
    """Bounded whole-film coverage plus actual contact/result neighborhoods."""
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Invalid review duration")
    last=max(0.,duration-.10)
    def clamp(t):
        return round(max(0.,min(last,t)),3)
    times={0.,clamp(last),clamp(.5),clamp(1.),clamp(2.)}
    for event in manifest.get("events",[]):
        start=float(event["start"]);result=float(event["t"])
        if not all(math.isfinite(t) for t in (start,result)):
            raise ValueError("Invalid event time")
        times.update(clamp(t) for t in (start-.2,start,result-.15,result,result+.4,result+1.2))
    if len(times)>40:raise ValueError("Oversized frame evidence")
    # Fill the largest uncovered interval first. Never discard evidence of
    # actual contact or confirmation to fit a uniform sampling budget.
    while len(times)<40:
        ordered=sorted(times)
        gap,left,right=max(((b-a,a,b) for a,b in zip(ordered,ordered[1:])),default=(0,0,0))
        if gap<=1.25:break
        times.add(clamp((left+right)/2))
    return sorted(times)

def sampled_encoded_evidence(film,duration,manifest):
    """Ordered, timestamped real master frames; no claim of video/audio review."""
    times=review_sample_times(duration,manifest)
    cap=cv2.VideoCapture(str(film))
    media=[]
    try:
        fps=cap.get(cv2.CAP_PROP_FPS);count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if fps<=0 or count<1:raise ValueError("Unreadable encoded master")
        frames=sorted(set(min(count-1,max(0,round(t*fps))) for t in times))
        actual=[]
        for n in frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES,n);ok,frame=cap.read()
            if not ok:raise ValueError("Missing sampled encoded frame")
            t=n/fps;actual.append(round(t,6))
            h,w=frame.shape[:2]
            if w>1280:frame=cv2.resize(frame,(1280,round(h*1280/w)),interpolation=cv2.INTER_AREA)
            ok,buf=cv2.imencode(".jpg",frame,[cv2.IMWRITE_JPEG_QUALITY,82])
            if not ok:raise ValueError("Frame encoding failed")
            media.extend(({"text":f"Encoded master frame at {t:.3f}s"},
                          {"inline_data":{"mime_type":"image/jpeg","data":base64.b64encode(buf).decode("ascii")}}))
        return tuple(media),actual
    finally:cap.release()

def review(film,qa,source,manifest,plan,directory,*,conversation=None):
    from backend.customer_story import sha,save
    film,source,manifest,directory=map(Path,(film,source,manifest,directory))
    directory.mkdir(mode=0o700,parents=True,exist_ok=True)
    receipt=directory/'result.json'
    digest=sha(film)
    expected={'film_sha256':digest,'source_sha256':sha(source),'manifest_sha256':sha(manifest)}
    if qa.get('film_sha256')!=digest:raise ValueError('Encoded review hash mismatch')
    if receipt.exists():
        result=json.loads(receipt.read_text())
        if any(result.get(k)!=v for k,v in expected.items()):raise ValueError('Review receipt mismatch')
        return result
    if conversation is not None:conv=conversation
    elif plan.get("director_provider")=="claude":
        from backend.claude_customer_director import ClaudeConversation
        conv=ClaudeConversation(directory/'claude')
    else:conv=Conversation(directory/'gemini')
    sampled=getattr(conv,"provider_name",None)=="Claude"
    result={**expected,'creative_approved':False,'decision':'unavailable','model_reviewed':False}
    def finish():
        result['ai_calls']=conv.calls
        tmp=receipt.with_suffix('.tmp');save(tmp,result);tmp.replace(receipt)
        return result
    if conv.calls:
        result['decision']='interrupted-review'
        return finish()
    try:
        if sampled:
            attachments,times=sampled_encoded_evidence(film,float(qa["duration"]),json.loads(manifest.read_text()))
            result.update(review_mode="timestamped-master-frames",review_frame_times=times,review_sampling="contact-result-coverage-v2")
        else:
            # Full duration, no cuts or time scaling. Keep the original master
            # untouched; derivative exists solely to fit inline model limits.
            view=directory/'review.mp4'
            subprocess.run(['ffmpeg','-v','error','-nostdin','-n','-i',str(film),
                            '-vf','scale=1280:720:flags=lanczos,fps=30',
                            '-c:v','libx264','-preset','fast','-crf','24',
                            '-c:a','aac','-b:a','96k','-movflags','+faststart',str(view)],
                           check=True,timeout=90)
            from scripts.quality_preview_supervisor import probe
            v=probe(view)
            if abs(float(v['format']['duration'])-float(qa['duration']))>0.1:
                raise ValueError('Review duration changed')
            result['review_sha256']=sha(view)
            result['review_duration']=float(v['format']['duration'])
            attachments=(_media(view,'video/mp4',12*1024*1024),)
            result['review_mode']='full-duration-video-proxy'
        prompt=("You are the creative director of a world-class motion studio. Watch the entire attached actual encoded product film, not the planned story. The master is native 60fps; this full-duration review proxy is 30fps. Do not infer source frame rate from the proxy. Would a cold viewer understand the value, stay interested and want to try the product? Be demanding. Identify timestamped visible evidence of weak pacing, tiny UI, disappearing content, camera, pointer and actual product payoff. Distinguish a bad story from capture or rendering defects. Say what to change in the next capture using specific observed moments; do not ask for invented UI, pointer data or unsupported camera effects. Judge the film as a flagship launch asset, not a tutorial or a technical pass. Reject when the sampled evidence shows materially weak product payoff, repetitive composition or unreadable UI, even if the recording is technically valid. Do not reject solely because a numerical warning exists. Explain the first meaningful change, the strongest visible result, and whether each later beat earns its screen time. Separate observed defects from unverified continuous motion or audio. Recommend one specific editorial change grounded in the visible product outcome; do not prescribe zooms merely to add motion. Return JSON with decision (keep or reject) and observations (string with timestamps). Keep means only retain for human review, never approval. Independent encoded QA: "+json.dumps(qa['findings'])[:2000]+". Planned story, not evidence of what occurred: "+str(plan.get('story',''))[:1200]+". Selected hero action ID (intent only): "+str(plan.get("hero_action_id",""))[:80])
        kwargs={}
        if sampled:
            prompt=prompt.replace("Watch the entire attached actual encoded product film, not the planned story. The master is native 60fps; this full-duration review proxy is 30fps. Do not infer source frame rate from the proxy.",
                "Inspect the ordered timestamped frames sampled from the actual encoded master. You cannot hear audio or observe every intervening frame; do not claim to have watched continuous motion or verified timing between samples. Assess visible framing, legibility and story from the supplied evidence only.")
            kwargs["response_schema"]={"type":"OBJECT","required":["decision","observations"],"properties":{
                "decision":{"type":"STRING","enum":["keep","reject"]},"observations":{"type":"STRING"}}}
        verdict=response(conv.ask(prompt,media=attachments,json_mode=True,phase='encoded-long-story-review',stop_on_rate_limit=True,**kwargs),('keep','reject'))
        if verdict:
            result.update(verdict,model_reviewed=True)
        result['retained_for_human_review']=bool(verdict and verdict['decision']=='keep' and qa.get('verdict')=='HUMAN_REVIEW_REQUIRED')
    except (OSError,ValueError,RuntimeError,KeyError,TypeError,subprocess.SubprocessError) as exc:
        result['error_type']=type(exc).__name__
    return finish()
