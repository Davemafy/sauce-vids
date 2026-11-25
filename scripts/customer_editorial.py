"""Bounded semantic editorial choices; actual source clocks and geometry win."""
FRAMINGS=("wide","accent","detail")
PACES=("quick","readable","linger")
TONES=("cobalt","muted","graphite")
WEIGHTS={"quick":1,"readable":2,"linger":3}
DURATIONS=(22,26,30)

def schema(ids):
    return {"type":"OBJECT","required":["accept","reason","backdrop","duration_seconds","beats"],
            "properties":{"accept":{"type":"BOOLEAN"},"reason":{"type":"STRING"},
            "backdrop":{"type":"STRING","enum":list(TONES)},
            "duration_seconds":{"type":"INTEGER","enum":[d for d in DURATIONS if d>=.8+5*(len(ids)-1)+9.2]},
            "beats":{"type":"ARRAY","items":{"type":"OBJECT",
             "required":["action_id","framing","pace","purpose"],
             "properties":{"action_id":{"type":"STRING","enum":list(ids)},
               "framing":{"type":"STRING","enum":list(FRAMINGS)},
               "pace":{"type":"STRING","enum":list(PACES)},"purpose":{"type":"STRING"}}}}}}

def validate(data,ids,hero):
    if not isinstance(data,dict) or set(data)!={"backdrop","duration_seconds","beats"}:
        raise ValueError("Missing bounded editorial direction")
    tone=data["backdrop"];beats=data["beats"]
    if not isinstance(tone,str) or tone not in TONES or not isinstance(beats,list) or len(beats)!=len(ids):
        raise ValueError("Invalid editorial backdrop or beat count")
    if len(ids) not in (3,4) or any(not isinstance(i,str) for i in ids) or len(set(ids))!=len(ids) or hero not in ids:
        raise ValueError("Invalid verified action sequence")
    duration=data["duration_seconds"]
    if type(duration) is not int or duration not in DURATIONS or duration<.8+5*(len(ids)-1)+9.2:
        raise ValueError("Editorial duration cannot accommodate verified actions")
    for beat,action in zip(beats,ids):
        if (not isinstance(beat,dict) or set(beat)!={"action_id","framing","pace","purpose"}
                or beat["action_id"]!=action or beat["framing"] not in FRAMINGS or beat["pace"] not in PACES
                or not isinstance(beat["purpose"],str) or not 1<=len(beat["purpose"].strip())<=240):
            raise ValueError("Editorial beat must reference the exact ordered action")
        if beat["framing"]=="detail" and action!=hero:
            raise ValueError("Detail requires selected verified hero")
    return data

def schedule(data,ids,hero):
    """Allocate relative emphasis inside a bounded native capture.
    Every action retains >=5s slot; final slot >=9.2s, no source retiming.
    """
    beats=validate(data,ids,hero)["beats"]
    weights=[WEIGHTS[b["pace"]] for b in beats]
    extra=data["duration_seconds"]-.8-5.*(len(ids)-1)-9.2
    t=.8;starts=[t]
    for w in weights[:-1]:
        t+=5.+extra*w/sum(weights)
        starts.append(round(t,6))
    return starts
