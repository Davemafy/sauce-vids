"""Hash-bound editorial assessment of the actual long customer film.

Private research evidence only. Model observations cannot change source,
camera, audio, independent QA, or release approval.
"""
import json,subprocess
from pathlib import Path
from backend.curious_showcase import Conversation,_media
from backend.interactive_editorial import response

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
    conv=conversation or Conversation(directory/'gemini')
    result={**expected,'creative_approved':False,'decision':'unavailable','model_reviewed':False}
    def finish():
        result['ai_calls']=conv.calls
        tmp=receipt.with_suffix('.tmp');save(tmp,result);tmp.replace(receipt)
        return result
    if conv.calls:
        result['decision']='interrupted-review'
        return finish()
    try:
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
        prompt=("You are the creative director of a world-class motion studio. Watch the entire attached actual encoded product film, not the planned story. The master is native 60fps; this full-duration review proxy is 30fps. Do not infer source frame rate from the proxy. Would a cold viewer understand the value, stay interested and want to try the product? Be demanding. Identify timestamped visible evidence of weak pacing, tiny UI, disappearing content, camera, pointer and actual product payoff. Distinguish a bad story from capture or rendering defects. Say what to change in the next capture using specific observed moments; do not ask for invented UI, pointer data or unsupported camera effects. A pacing, contrast or focal-size warning alone does not imply a broken film; keep a usable film for owner assessment even if it is not studio-grade. Reject actual misleading, unreadable or materially weak films. Return JSON with decision (keep or reject) and observations (string with timestamps). Keep means only retain for human review, never approval. Independent encoded QA: "+json.dumps(qa['findings'])[:2000]+". Planned story, not evidence of what occurred: "+str(plan.get('story',''))[:1200]+". Selected hero action ID (intent only): "+str(plan.get("hero_action_id",""))[:80])
        verdict=response(conv.ask(prompt,media=(_media(view,'video/mp4',12*1024*1024),),json_mode=True,phase='encoded-long-story-review',stop_on_rate_limit=True),('keep','reject'))
        if verdict:
            result.update(verdict,model_reviewed=True)
        result['retained_for_human_review']=bool(verdict and verdict['decision']=='keep' and qa.get('verdict')=='HUMAN_REVIEW_REQUIRED')
    except (OSError,ValueError,RuntimeError,KeyError,TypeError,subprocess.SubprocessError) as exc:
        result['error_type']=type(exc).__name__
    return finish()
