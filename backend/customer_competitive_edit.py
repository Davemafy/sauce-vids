"""Opt-in fixed-source editorial competition; proxies never become masters."""
import json,random,subprocess
from pathlib import Path
import cv2
from scripts import customer_editorial as ed
from backend.customer_story_review import review_sample_times

WEIGHTS={'comprehension':20,'composition':20,'motion_proxy':20,'narrative':15,'originality':15,'publishability':10}
LENSES=('clarity and buyer payoff; consider the quiet paper studio backdrop when UI is dense','decisive composition and emphasis; use a backdrop that separates the product from its environment','rhythm and narrative contrast; avoid decorative motion or a busy environment')

def score_rows(raw,labels):
    data=json.loads(raw);rows=data['scores']
    if not isinstance(rows,list) or len(rows)!=len(labels):raise ValueError('Incomplete ranking')
    scores={}
    for row in rows:
        label=row['id'];values=row['rubric']
        if label not in labels or label in scores or set(values)!=set(WEIGHTS):raise ValueError('Invalid rubric identity')
        if any(type(v)!=int or not 0<=v<=100 for v in values.values()):raise ValueError('Invalid rubric score')
        scores[label]=sum(values[k]*w for k,w in WEIGHTS.items())/100
    return scores

def fixed_source_intent(verdict,baseline,ids,hero):
    """Descriptions are not camera inputs; preserve the already verified purposes."""
    if verdict.get('accept') is not True:raise ValueError('Director abstained')
    if verdict.get('duration_seconds')!=baseline['duration_seconds']:raise ValueError('Source duration changed')
    beats=verdict.get('beats')
    if not isinstance(beats,list) or len(beats)!=len(ids):raise ValueError('Wrong beat count')
    clean=[]
    for b,original in zip(beats,baseline['beats']):
        if not isinstance(b,dict) or set(b)!={'action_id','framing','pace','purpose'} or b['action_id']!=original['action_id']:
            raise ValueError('Wrong beat identity')
        clean.append({**b,'purpose':original['purpose']})
    return ed.validate({'backdrop':verdict.get('backdrop'),'duration_seconds':baseline['duration_seconds'],'beats':clean},ids,hero)

def compete(source,manifest,plan,directory,run,*,factory=None):
    from backend.customer_story import sha,save,media
    from backend.claude_customer_director import ClaudeConversation
    directory=Path(directory);source=Path(source);manifest=Path(manifest)
    baseline=plan['editorial'];ids=[a['id'] for a in plan['actions']];hero=plan['hero_action_id'];duration=baseline['duration_seconds']
    if directory.exists():raise ValueError('Competitive edit already attempted')
    directory.mkdir(mode=0o700)
    factory=factory or ClaudeConversation
    state={'source_sha256':sha(source),'manifest_sha256':sha(manifest),'creative_approved':False,'selected':None,'calls':0,'candidates':[],'mode':'fixed-source-12fps-visual-proxy'}
    def persist():save(directory/'result.json',state)
    persist()
    evidence=json.loads(manifest.read_text());events=evidence['events']
    packet={'duration':duration,'actions':[{'id':i,'label':e.get('label'),'start':e['start'],'result_at':e['t'],'resultRect':e['resultRect'],'componentRect':e.get('componentRect')} for i,e in zip(ids,events)],'hero':hero,'story':plan['story']}
    # Provide identical actual source stills to all three fresh conversations.
    cap=cv2.VideoCapture(str(source));attachments=[]
    try:
        for t in [0.]+[min(duration-.1,e['t']+.4) for e in events]:
            cap.set(cv2.CAP_PROP_POS_FRAMES,round(t*60));ok,im=cap.read()
            if not ok:raise ValueError('Missing fixed source evidence')
            im=cv2.resize(im,(960,540),interpolation=cv2.INTER_AREA);ok,b=cv2.imencode('.png',im)
            if not ok:raise ValueError('Missing encoded evidence')
            attachments.append(media(b.tobytes()))
    finally:cap.release()
    proposals=[]
    for index,lens in enumerate(LENSES):
        d=directory/f'director-{index+1}';d.mkdir(mode=0o700)
        c=factory(d/'model');row={'id':str(index+1),'status':'started'};state['candidates'].append(row);persist()
        try:
            raw=c.ask('Independently direct this actual recorded workflow with emphasis on '+lens+'. Use the exact unchanged action order and duration; no edits to source time or actions. Select a distinct useful framing and backdrop: expressive cobalt, quiet blue-gray muted, restrained dark graphite, or quiet neutral paper without cloud texture. Make the actual product the visual hero, not the decorative backdrop. Never add a gratuitous slow camera move to disguise dead time. Keep each purpose under 120 characters; the existing verified action purposes are retained. Return accept, reason, backdrop, duration_seconds, beats. Evidence: '+json.dumps(packet),media=tuple(attachments),json_mode=True,phase='story-editorial',stop_on_rate_limit=True,response_schema=ed.schema(ids),max_attempts=1)
            v=json.loads(raw)
            save(d/'raw-verdict.json',v)
            intent=fixed_source_intent(v,baseline,ids,hero)
            save(d/'intent.json',{'ids':ids,'hero':hero,'editorial':intent})
            run('source_event_director.py','--source',source,'--manifest',manifest,'--out',d/'plan.json','--hero-event-index',ids.index(hero),'--editorial-intent',d/'intent.json')
            run('render_event_video.py','--video',source,'--manifest',manifest,'--film-plan',d/'plan.json','--customer-craft-contract','--ranking-preview','--output',d/'preview.mp4')
            row.update(status='rendered',preview_sha256=sha(d/'preview.mp4'),plan_sha256=sha(d/'plan.json'))
            proposals.append((row,intent,d))
        except (ValueError,TypeError,KeyError,OSError,RuntimeError,subprocess.SubprocessError) as exc:
            row.update(status='failed',error_type=type(exc).__name__,reason=str(exc)[:240])
        finally:
            state['calls']+=c.calls;persist()
        if any(a.get('http_status')==429 for a in c.data.get('attempts',[])):break
    # No pretend three-way comparison if a candidate fails or duplicates.
    unique={}
    for proposal in proposals:
        row,intent,d=proposal
        # Equivalent camera/backdrop choices aren't three creative alternatives.
        # Compare physical plan identity rather than incidental MP4 metadata.
        key=row['plan_sha256']
        if key not in unique:unique[key]=proposal
        else:row['status']='duplicate-plan'
    proposals=list(unique.values())
    if len(proposals)<2:
        state['status']='incomplete-or-duplicate';persist();return baseline,state['calls']
    random.SystemRandom().shuffle(proposals)
    labels=['A','B','C'][:len(proposals)];mapping=dict(zip(labels,proposals));state['blind_mapping']={k:v[0]['id'] for k,v in mapping.items()};persist()
    parts=[];pacing={}
    from backend.customer_story_review import pacing_evidence
    import base64
    # Same event-oriented sample times for each actual rendered proxy.
    times=review_sample_times(duration,evidence)
    # Keep equal coverage and bounded image cost; retain opening and ending.
    times=[times[round(i*(len(times)-1)/7)] for i in range(8)]
    for label,(_,_,d) in mapping.items():
        pacing[label]=pacing_evidence(d/'preview.mp4',evidence,duration)
        cap=cv2.VideoCapture(str(d/'preview.mp4'))
        try:
            if round(cap.get(cv2.CAP_PROP_FPS))!=12 or round(cap.get(cv2.CAP_PROP_FRAME_COUNT))!=round(duration*12):raise ValueError('Proxy clock mismatch')
            for t in times:
                n=min(round(duration*12)-1,round(t*12));cap.set(cv2.CAP_PROP_POS_FRAMES,n);ok,im=cap.read()
                if not ok:raise ValueError('Missing preview sample')
                ok,b=cv2.imencode('.jpg',im,[cv2.IMWRITE_JPEG_QUALITY,78])
                if not ok:raise ValueError('Missing preview image')
                parts.extend(({'text':f'Anonymous candidate {label}, {n/12:.3f}s'},{'inline_data':{'mime_type':'image/jpeg','data':base64.b64encode(b).decode('ascii')}}))
        finally:cap.release()
    critic=factory(directory/'critic');schema={'type':'OBJECT','required':['scores'],'properties':{'scores':{'type':'ARRAY','items':{'type':'OBJECT','required':['id','rubric'],'properties':{'id':{'type':'STRING','enum':labels},'rubric':{'type':'OBJECT','required':list(WEIGHTS),'properties':{k:{'type':'INTEGER'} for k in WEIGHTS}}}}}}}
    try:
        raw=critic.ask('Rank every anonymous actual rendered visual preview against the same rubric. Score each dimension 0–100. Penalize redundant holds, slow pointless pushes, delayed payoff and an idle ending under motion_proxy and publishability; do not reward motion for its own sake. Motion_proxy measures only observable framing changes and sampled frame differences; do not claim continuous motion or audio review. No candidate is approved by this ranking. Measured pacing: '+json.dumps(pacing)+'. Weights: '+json.dumps(WEIGHTS),media=tuple(parts),json_mode=True,phase='encoded-long-story-review',stop_on_rate_limit=True,response_schema=schema,max_attempts=1)
        scores=score_rows(raw,labels);state['scores']=scores
        best=max(labels,key=lambda k:scores[k]);state['selected']=mapping[best][0]['id'];state['status']='ranked' if len(proposals)==3 else 'ranked-two';state['pacing']=pacing
        return mapping[best][1],state['calls']+critic.calls
    except (ValueError,TypeError,KeyError,OSError,RuntimeError) as exc:
        state.update(status='critic-unavailable',error_type=type(exc).__name__);return baseline,state['calls']+critic.calls
    finally:
        state['calls']+=critic.calls;persist()
