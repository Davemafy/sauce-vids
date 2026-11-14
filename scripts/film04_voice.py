#!/usr/bin/env python3
"""Offline speech for tight, truthful Resend pricing demonstration."""
import json,wave
from pathlib import Path
import numpy as np
from kokoro_onnx import Kokoro
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"studio"/".tmp"/"film-04"
BASE=ROOT/"studio"/".tmp"/"educational-pilot"
STORY=[
 ("start",0.38,"Three thousand emails start free."),
 ("fifty",2.63,"Fifty thousand? Twenty dollars a month."),
 ("hundred",5.18,"A hundred thousand? Thirty-five dollars."),
 ("finish",7.78,"One slider. Clear pricing.")
]
MODEL=Kokoro(str(BASE/"kokoro-v1.0.int8.onnx"),str(BASE/"voices-v1.0.bin"))
sr=24000
samples=np.zeros(int(10.4*sr),dtype=np.float32)
records=[]
for name,start,script in STORY:
 audio,rate=MODEL.create(script,voice="af_heart",speed=1.19,lang="en-us")
 assert rate==sr
 audio=np.asarray(audio,dtype=np.float32)
 end=start+len(audio)/sr
 if end>=10.2:raise RuntimeError(f"Speech overhang: {name} {end}")
 left=int(start*sr)
 samples[left:left+len(audio)]+=audio
 records.append({"id":name,"start":start,"end":round(end,3),"text":script})
 print(name,round(start,3),round(end,3),flush=True)
peak=float(np.max(np.abs(samples)))
if peak>.9:samples*=.9/peak
OUT.mkdir(parents=True,exist_ok=True)
with wave.open(str(OUT/"voice.wav"),"wb") as f:
 f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr)
 f.writeframes((samples*32767).astype("<i2").tobytes())
(OUT/"voice.json").write_text(json.dumps({"duration":10.4,"voice":"Kokoro local af_heart","phrases":records},indent=2))
