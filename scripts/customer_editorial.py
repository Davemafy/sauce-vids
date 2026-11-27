"""Bounded semantic editorial choices; actual source clocks and geometry win."""
FRAMINGS=("wide","accent","detail")
PACES=("quick","readable","linger")
TONES=("cobalt","muted","graphite")
WEIGHTS={"quick":1,"readable":2,"linger":3}
DURATIONS=(22,26,30)
COMPACT_DURATIONS=(13,16,18,20)
THREE_ACTION_DURATIONS=(18,22,26,30)

def durations(count):
    return COMPACT_DURATIONS if count==2 else THREE_ACTION_DURATIONS if count==3 else DURATIONS

def final_slot(count,duration):
    """Short edits retain a measured action/proof budget and real reading time.

    Legacy slots remain unchanged. Capture still rejects a late confirmation
    rather than squeezing or fabricating a result.
    """
    return 7.2 if (count,duration) in ((2,13),(3,18)) else 9.2

def minimum_duration(count,duration):
    return .8+5*(count-1)+final_slot(count,duration)

def slot_budgets(beats,duration):
    """Reserve native proof + context + camera travel + readable detail."""
    count=len(beats)
    return [9.0 if b["framing"]=="detail" else 5.0 for b in beats[:-1]] + [
        max(9.7,final_slot(count,duration)) if beats[-1]["framing"]=="detail" else final_slot(count,duration)]

def fit_duration(data,ids,hero):
    """Compile the requested duration as a lower bound, never retime footage."""
    validate(data,ids,hero,check_budget=False)
    for d in durations(len(ids)):
        if d>=data["duration_seconds"] and d+1e-8>=.8+sum(slot_budgets(data["beats"],d)):
            return validate({**data,"duration_seconds":d},ids,hero)
    raise ValueError("Detail beats exceed supported native capture duration")

def schema(ids):
    return {"type":"OBJECT","required":["accept","reason","backdrop","duration_seconds","beats"],
            "properties":{"accept":{"type":"BOOLEAN"},"reason":{"type":"STRING"},
            "backdrop":{"type":"STRING","enum":list(TONES)},
            "duration_seconds":{"type":"INTEGER","enum":[d for d in durations(len(ids)) if d>=minimum_duration(len(ids),d)]},
            "beats":{"type":"ARRAY","items":{"type":"OBJECT",
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
