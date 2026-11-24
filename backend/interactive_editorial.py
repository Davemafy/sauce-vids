"""Private, bounded encoded-film review for verified local sequences."""
import json,subprocess
from pathlib import Path
from hashlib import file_digest
from backend.curious_showcase import Conversation,_media,prefer_revision

def evidence(export,source):
    export,source=Path(export),Path(source)
    film=export/'master-1080p60.mp4'
    release=json.loads((export/'release.json').read_text())
    qa=json.loads((export/'encoded-quality.json').read_text())
    capture=json.loads((source/'continuous-capture.json').read_text())
    from backend.native60_capture import source_video_filename
    def digest(path):
        with path.open('rb') as f:return file_digest(f,'sha256').hexdigest()
    if (release.get('film_mode')!='interactive' or release.get('source_verified') is not True
        or not capture.get('sequence_proof') or release.get('source_sha256')!=capture.get('sha256')
        or digest(source/source_video_filename(capture))!=capture['sha256']
        or digest(film)!=qa.get('film_sha256') or release.get('encoded_quality_verdict')!=qa.get('verdict')):
        raise ValueError('Encoded sequence evidence mismatch')
    return film,qa,release

def response(raw,choices):
    try:r=json.loads(raw)
    except (ValueError,TypeError):return None
    if not isinstance(r,dict) or r.get('decision') not in choices:return None
    observations=r.get('observations')
    if isinstance(observations,dict) and observations:
        # Gemini sometimes returns its timestamp/critique fields as an object.
        # Preserve them as inert text; the decision is still independently
        # allowlisted and no arbitrary model fields reach the renderer.
        observations=json.dumps(observations,ensure_ascii=False)
    if not isinstance(observations,str) or not observations.strip():return None
    return {'decision':r['decision'],'observations':observations[:2000]}

def critique(conv,base,phase,other=None):
    film,qa,_=base
    if phase=='encoded-interactive-review':
        choices=('keep','compact','reject')
        prompt=("Hey Gemini, watch this actual encoded software demo. If you were a stranger, "
                "where would you lose interest? Which action and result do you actually see? "
                "Name specific timestamps, judge pointer, readable payoff, pacing and composition. "
                "Can a shorter native recording of the SAME verified sequence help? "
                "Compact removes excess waiting, never invents actions or alters the source. "
                "If the idea itself is weak, reject it. Return a JSON object with decision (one of keep, compact, reject) and observations (a concise string with timestamps). ")
    else:
        choices=('baseline','candidate','reject')
        prompt=("Watch BOTH actual encoded films (baseline first, candidate second). "
                "Did we really improve the story, motion and readable payoff, or merely shorten the film? "
                "Identify visible moments and timestamps. Reject both if neither works. "
                "Return a JSON object with decision (one of baseline, candidate, reject) and observations (a concise string with timestamps). ")
    media=(_media(film,'video/mp4',12*1024*1024),)
    if other:
        media+=(_media(other[0],'video/mp4',12*1024*1024),)
        prompt+=' Candidate encoded QA: '+json.dumps(other[1].get('findings',[]))[:2000]
    prompt+=' Baseline encoded QA: '+json.dumps(qa.get('findings',[]))[:2000]
    return response(conv.ask(prompt,media=media,json_mode=True,phase=phase,stop_on_rate_limit=True),choices)

def choose_candidate(base,candidate,judgment):
    return bool(judgment and judgment['decision']=='candidate'
                and candidate.get('verdict')=='HUMAN_REVIEW_REQUIRED'
                and prefer_revision(base,candidate))

def run(base_export,base_source,directory,make_candidate,*,conversation=None):
    directory=Path(directory);directory.mkdir(mode=0o700,parents=True,exist_ok=True)
    receipt=directory/'result.json'
    if receipt.exists():return json.loads(receipt.read_text())
    conv=conversation or Conversation(directory/'gemini')
    result={'schema':'sauce-interactive-editorial-v1','creative_approved':False,
            'selected':None,'model_reviewed':False,'revision_rendered':False}
    # A started attempt is durable: recovery never spends again or promotes
    # an incomplete candidate on the strength of an old response.
    def save():
        result['ai_calls']=conv.calls
        tmp=receipt.with_suffix('.tmp');tmp.write_text(json.dumps(result,indent=2));tmp.replace(receipt)
        return result
    if conv.calls:
        result['decision']='interrupted-review';return save()
    try:
        base=evidence(base_export,base_source)
        result['baseline_sha256']=base[1]['film_sha256']
        first=critique(conv,base,'encoded-interactive-review')
        result['first_review']=first
        result['model_reviewed']=first is not None
        if first is None:
            result['decision']='model-unavailable-or-invalid';return save()
        result['decision']=first['decision']
        if first['decision']=='keep' and base[1].get('verdict')=='HUMAN_REVIEW_REQUIRED':
            result['selected']='baseline'
        if first['decision']!='compact':return save()
        export,source=make_candidate()
        candidate=evidence(export,source)
        result['revision_rendered']=True
        result['candidate_sha256']=candidate[1]['film_sha256']
        result['candidate_qa']=candidate[1]['verdict']
        final=critique(conv,base,'encoded-interactive-comparison',candidate)
        result['comparison']=final
        if choose_candidate(base[1],candidate[1],final):result['selected']='candidate'
        else:
            result['decision']='revision-not-admitted'
            if final and final['decision']=='baseline' and base[1].get('verdict')=='HUMAN_REVIEW_REQUIRED':
                result['selected']='baseline'
    except (RuntimeError,ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError) as exc:
        result['decision']='review-or-revision-failed';result['error_type']=type(exc).__name__
    return save()
