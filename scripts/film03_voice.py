#!/usr/bin/env python3
"""Generate truthful, event-aligned narration locally. Offline Kokoro."""
import json,wave
from pathlib import Path
import numpy as np
from kokoro_onnx import Kokoro
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"studio"/".tmp"/"film-03"
P.mkdir(parents=True,exist_ok=True)
MODEL=ROOT/"studio"/".tmp"/"educational-pilot"/"kokoro-v1.0.int8.onnx"
VOICES=ROOT/"studio"/".tmp"/"educational-pilot"/"voices-v1.0.bin"
LINES=[
 ("free",0.55,"Three thousand emails start free."),
 ("fifty",3.55,"Fifty thousand emails? Twenty dollars a month."),
 ("hundred",7.55,"A hundred thousand? Thirty-five dollars."),
 ("close",10.75,"One slider. The price changes right where you need it.")
]
kokoro=Kokoro(str(MODEL),str(VOICES))
sr=24000
timeline=[]
full=np.zeros(int(16.2*sr),dtype=np.float32)
for name,start,text in LINES:
    data,rate=kokoro.create(text,voice="af_heart",speed=1.07,lang="en-us")
    if rate!=sr:raise ValueError("Unexpected model rate")
    data=np.asarray(data,dtype=np.float32)
    finish=start+len(data)/sr
    if finish>16.1:raise ValueError(f"Narration extends beyond film: {name} ends {finish}")
    timeline.append({"id":name,"text":text,"start":start,"end":round(finish,3)})
    a=int(start*sr)
    full[a:a+len(data)]+=data
    print("PHRASE",name,start,round(finish,3),flush=True)
peak=float(np.max(np.abs(full)))
if peak>.85:full*=.85/peak
out=P/"narration.wav"
with wave.open(str(out),"wb") as f:
    f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr)
    f.writeframes((np.clip(full,-1,1)*32767).astype("<i2").tobytes())
(P/"narration.json").write_text(json.dumps({"duration":16.2,"phrases":timeline,"voice":"Kokoro af_heart","source":"offline original narration"},indent=2))
print("DONE",out,flush=True)
