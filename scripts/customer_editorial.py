"""Bounded semantic editorial choices; actual source clocks and geometry win."""
FRAMINGS=("wide","accent","detail")
PACES=("quick","readable","linger")
TONES=("cobalt","muted","graphite","paper")
WEIGHTS={"quick":1,"readable":2,"linger":3}
DURATIONS=(22,26,30)
COMPACT_DURATIONS=(12,13,16,18,20)
THREE_ACTION_DURATIONS=(18,22,26,30)

# Native short cuts are admitted only from measured connected proof, not a
# model's arbitrary runtime request. Keep legacy detail budgets intact.
OUTCOME_DURATIONS={2:(8,9,10),3:(10,11,14,16),4:(13,16,19)}
def legacy_durations(count):
    return COMPACT_DURATIONS if count==2 else THREE_ACTION_DURATIONS if count==3 else DURATIONS

def durations(count):
    return tuple(sorted(set(legacy_durations(count))|set(OUTCOME_DURATIONS.get(count,()))))

def outcome_duration(count,duration):
    return duration in OUTCOME_DURATIONS.get(count,())


def final_slot(count,duration):
    """Short edits retain a measured action/proof budget and real reading time.

    Legacy slots remain unchanged. Capture still rejects a late confirmation
    rather than squeezing or fabricating a result.
    """
    return 6.2 if (count,duration)==(2,12) else (7.2 if (count,duration) in ((2,13),(3,18)) else 9.2)

def minimum_duration(count,duration):
    if outcome_duration(count,duration):return .8+2.5*(count-1)+4.0
    return .8+5*(count-1)+final_slot(count,duration)

def slot_budgets(beats,duration):
    """Reserve native proof + context + camera travel + readable detail."""
    count=len(beats)
    if outcome_duration(count,duration):
        if any(b["framing"]=="detail" for b in beats):return [30.]*count
        return [2.5]*(count-1)+[4.]
    return [9.0 if b["framing"]=="detail" else 5.0 for b in beats[:-1]] + [
        (7.2 if (count,duration)==(2,13) else max(9.7,final_slot(count,duration))) if beats[-1]["framing"]=="detail" else final_slot(count,duration)]

def fit_duration(data,ids,hero):
    """Compile the requested duration as a lower bound, never retime footage."""
    validate(data,ids,hero,check_budget=False)
    for d in legacy_durations(len(ids)):
        # The 13s detail allowance is for independently measured fast local
        # workflows only; generic model requests need the conservative slot.
        if len(ids)==2 and d==13 and data["beats"][-1]["framing"]=="detail":continue
        if d>=data["duration_seconds"] and d+1e-8>=.8+sum(slot_budgets(data["beats"],d)):
            return validate({**data,"duration_seconds":d},ids,hero)
    raise ValueError("Detail beats exceed supported native capture duration")

def schema(ids,fixed_duration=None,*,duration_floor=0):
    return {"type":"OBJECT","required":["accept","reason","backdrop","duration_seconds","beats"],
            "properties":{"accept":{"type":"BOOLEAN"},"reason":{"type":"STRING"},
            "backdrop":{"type":"STRING","enum":list(TONES)},
            "duration_seconds":{"type":"INTEGER","enum":([fixed_duration] if fixed_duration is not None else [d for d in legacy_durations(len(ids)) if d>=max(duration_floor,minimum_duration(len(ids),d))])},
            "beats":{"type":"ARRAY","minItems":len(ids),"maxItems":len(ids),"items":{"type":"OBJECT",
             "required":["action_id","framing","pace","purpose"],
             "properties":{"action_id":{"type":"STRING","enum":list(ids)},
               "framing":{"type":"STRING","enum":list(FRAMINGS)},
               "pace":{"type":"STRING","enum":list(PACES)},"purpose":{"type":"STRING"}}}}}}

def validate(data,ids,hero,*,check_budget=True):
    if not isinstance(data,dict) or set(data)!={"backdrop","duration_seconds","beats"}:
        raise ValueError("Missing bounded editorial direction")
    tone=data["backdrop"];beats=data["beats"]
    if not isinstance(tone,str) or tone not in TONES or not isinstance(beats,list) or len(beats)!=len(ids):
        raise ValueError("Invalid editorial backdrop or beat count")
    if len(ids) not in (2,3,4) or any(not isinstance(i,str) for i in ids) or len(set(ids))!=len(ids) or hero not in ids:
        raise ValueError("Invalid verified action sequence")
    duration=data["duration_seconds"]
    if type(duration) is not int or duration not in durations(len(ids)) or duration<minimum_duration(len(ids),duration):
        raise ValueError("Editorial duration cannot accommodate verified actions")
    for beat,action in zip(beats,ids):
        if (not isinstance(beat,dict) or set(beat)!={"action_id","framing","pace","purpose"}
                or beat["action_id"]!=action or beat["framing"] not in FRAMINGS or beat["pace"] not in PACES
                or not isinstance(beat["purpose"],str) or not 1<=len(beat["purpose"].strip())<=240):
            raise ValueError("Editorial beat must reference the exact ordered action")
    details=[b["action_id"] for b in beats if b["framing"]=="detail"]
    if len(details)>2:
        raise ValueError("At most two independently selected detail beats")
    if check_budget and duration+1e-8<.8+sum(slot_budgets(beats,duration)):
        raise ValueError("Editorial duration cannot accommodate requested detail travel and hold")
    return data

def schedule(data,ids,hero):
    """Allocate relative emphasis inside a bounded native capture.
    Wide/accent slots retain their existing minimums; detail earns extra
    native time for context, travel and reading. No source retiming.
    """
    beats=validate(data,ids,hero)["beats"]
    weights=[WEIGHTS[b["pace"]] for b in beats]
    budgets=slot_budgets(beats,data["duration_seconds"])
    extra=max(0.,data["duration_seconds"]-.8-sum(budgets))
    t=.8;starts=[t]
    for base,w in zip(budgets[:-1],weights[:-1]):
        t+=base+extra*w/sum(weights)
        starts.append(round(t,6))
    return starts


def protect_local_readability(data,actions,hero,proofs,viewport):
    """Reserve one detail shot for a small, verified embedded product payoff.

    Only the existing named local-demo adapter is admitted here. The native
    camera contract still decides actual fit, pointer visibility and timing.
    Preserve any deliberate model-selected detail and all other beat choices.
    """
    ids=[a["id"] for a in actions]
    validate(data,ids,hero,check_budget=False)
    if any(b["framing"]=="detail" for b in data["beats"]):return data,None
    w,h=viewport
    candidates=[]
    for i,(action,proof) in enumerate(zip(actions,proofs)):
        if action.get("control")!="local-demo-view" or proof.get("id")!=action["id"]:continue
        r=proof.get("result")
        if not isinstance(r,dict):continue
        x,y,rw,rh=(r.get(k) for k in ("x","y","width","height"))
        if not all(type(v) in (int,float) for v in (x,y,rw,rh)):continue
        if not (0<=x<x+rw<=w and 0<=y<y+rh<=h):continue
        if not (.18<=rw*rh/(w*h)<=.35):continue
        candidates.append(i)
    if not candidates:return data,None
    i=ids.index(hero) if ids.index(hero) in candidates else candidates[-1]
    beats=[dict(b) for b in data["beats"]]
    beats[i]["framing"]="detail"
    beats[i]["pace"]="readable"
    amended=fit_duration({**data,"beats":beats},ids,hero)
    return amended,{"action_id":ids[i],"reason":"small-verified-local-result","requested_duration":data["duration_seconds"],"compiled_duration":amended["duration_seconds"]}


def compact_fast_local(data,actions,hero,proofs):
    """Use short native capture only for quick, witnessed two-step local demos."""
    ids=[a['id'] for a in actions]
    if len(ids)!=2 or not all(a.get('control')=='local-demo-view' for a in actions):return data,None
    if len(proofs)!=2 or any(p.get('id')!=a['id'] or not isinstance(p.get('probe_seconds'),(int,float)) or not 0<p['probe_seconds']<=2.0 for a,p in zip(actions,proofs)):return data,None
    if data['beats'][0]['framing']=='detail':return data,None
    target=13 if data['beats'][-1]['framing']=='detail' else 12
    if target>=data['duration_seconds']:return data,None
    result=validate({**data,'duration_seconds':target},ids,hero)
    return result,{'reason':'measured-fast-local-workflow','previous_duration':data['duration_seconds'],'duration':target,'probe_seconds':[p['probe_seconds'] for p in proofs]}


def measured_schedule(data,actions,hero,proofs,*,duration_floor=0):
    """Allocate native action time from the connected, independently replayed proof.

    DOM-click probe time includes verification and component measurement. Native
    recording adds pointer approach and screen/geometry overhead. Keep the
    existing minimum framing slots, a readable gap and a two-second final hold.
    Never shorten requested duration here or retime captured footage.
    """
    import math
    ids=[a['id'] for a in actions]
    validate(data,ids,hero)
    if len(proofs)!=len(ids) or any(p.get('id')!=i or type(p.get('probe_seconds')) not in (float,int) or not math.isfinite(p['probe_seconds']) or p['probe_seconds']<=0 for i,p in zip(ids,proofs)):
        if outcome_duration(len(ids),data["duration_seconds"]):raise ValueError("Compact capture requires connected timing proof")
        return data,schedule(data,ids,hero),None
    beats=data['beats'];latencies=[]
    for a,p in zip(actions,proofs):
        # A picker or menu requires opener and choice, versus a single view click.
        double=a.get('control')=='presentation-combobox' or (a['kind']=='option' and a.get('control') not in ('local-demo-view','visible-radio','semantic-capability','sample-choice','observed-workspace'))
        latencies.append(p['probe_seconds']+(1.10 if double else .65))
    floors=[v+(.9 if i<len(ids)-1 else 2.15) for i,v in enumerate(latencies)]
    # A fast observed workflow should not inherit the model's duration floor.
    # Direct and multi-step controls share measured native overhead. Never
    # compact slow probes, detail shots, or an unverified source clock.
    if all(p['probe_seconds']<=2.0 for p in proofs) and not any(b['framing']=='detail' for b in beats):
        for d in OUTCOME_DURATIONS.get(len(ids),()):
            if not duration_floor<=d<=data['duration_seconds']:continue
            candidate={**data,'duration_seconds':d}
            try:validate(candidate,ids,hero)
            except ValueError:continue
            budgets=[max(x,y) for x,y in zip(slot_budgets(beats,d),floors)]
            extra=d-.8-sum(budgets)
            if extra< -1e-7:continue
            # Keep intervening reading time bounded; put fractional rounding
            # slack in the closing result rather than slowing each action.
            starts=[.8]
            for budget in budgets[:-1]:starts.append(round(starts[-1]+budget,6))
            return candidate,starts,{'reason':'outcome-driven-native-clock','probe_seconds':[p['probe_seconds'] for p in proofs],'native_estimate_seconds':[round(v,4) for v in latencies],'slot_floors_seconds':[round(v,4) for v in budgets],'requested_duration':data['duration_seconds'],'duration':d,'action_starts':starts}
    if outcome_duration(len(ids),data['duration_seconds']):raise ValueError('Compact timing no longer supported by connected proof')
    for d in legacy_durations(len(ids)):
        if d<max(duration_floor,data['duration_seconds']):continue
        candidate={**data,'duration_seconds':d}
        try:validate(candidate,ids,hero)
        except ValueError:continue
        budgets=[max(x,y) for x,y in zip(slot_budgets(beats,d),floors)]
        extra=d-.8-sum(budgets)
        if extra< -1e-7:continue
        weights=[WEIGHTS[b['pace']] for b in beats];starts=[.8]
        for budget,weight in zip(budgets[:-1],weights[:-1]):
            starts.append(round(starts[-1]+budget+max(0.,extra)*weight/sum(weights),6))
        return candidate,starts,{'reason':'measured-connected-probe-latency','probe_seconds':[p['probe_seconds'] for p in proofs],'native_estimate_seconds':[round(v,4) for v in latencies],'slot_floors_seconds':[round(v,4) for v in budgets],'requested_duration':data['duration_seconds'],'duration':d,'action_starts':starts}
    raise ValueError('Measured workflow exceeds supported native timing budget')
