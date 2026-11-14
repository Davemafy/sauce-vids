#!/usr/bin/env python3
"""Offline documentary-style narration for an actual product workflow."""
from pathlib import Path
from kokoro_onnx import Kokoro
import numpy as np
import json, sys, wave, time
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"studio"/".tmp"/"film-paradigm"
MODEL=ROOT/"studio"/".tmp"/"educational-pilot"/"kokoro-v1.0.int8.onnx"
VOICES=ROOT/"studio"/".tmp"/"educational-pilot"/"voices-v1.0.bin"
PHRASES=[
 ("INTRO","These expenses are plain numbers."),
 ("SELECT","Select the amount column,"),
 ("FORMAT","choose currency,"),
 ("RESULT","and watch every value update."),
 ("OUTRO","No formulas. No fuss."),
]
SILENCE_BEFORE=[.50,.12,.10,.08,.14]
SILENCE_AFTER=[.18,.08,.15,.24,.65]
voice=sys.argv[1] if len(sys.argv)>1 else "af_heart"
speed=float(sys.argv[2]) if len(sys.argv)>2 else 1.07
OUT.mkdir(parents=True,exist_ok=True)
model=Kokoro(str(MODEL),str(VOICES))
parts=[];timeline=[];sample_rate=None;cursor=0
for i, (name,text) in enumerate(PHRASES):
 audio,sr=model.create(text,voice=voice,speed=speed,lang="en-us")
 audio=np.asarray(audio,dtype=np.float32)
 if sample_rate is None:sample_rate=sr
 if sr!=sample_rate:raise ValueError("Mixed sample rates")
 before=np.zeros(round(sr*SILENCE_BEFORE[i]),dtype=np.float32)
 after=np.zeros(round(sr*SILENCE_AFTER[i]),dtype=np.float32)
 t0=(cursor+len(before))/sr; t1=t0+len(audio)/sr
 timeline.append({"id":name,"text":text,"start":round(t0,4),"end":round(t1,4),
                  "duration":round(t1-t0,4)})
 chunk=np.concatenate((before,audio,after))
 parts.append(chunk);cursor+=len(chunk)
 print(name,round(t0,3),round(t1,3),flush=True)
full=np.concatenate(parts)
peak=np.max(np.abs(full))
if peak>0.90:full*=.9/peak
path=OUT/"voice.wav"
with wave.open(str(path),"wb") as ff:
 ff.setnchannels(1);ff.setsampwidth(2);ff.setframerate(sr)
 ff.writeframes((full*32767).astype("<i2").tobytes())
metadata={"script":" ".join(t for _,t in PHRASES),"voice":voice,"engine":"Kokoro 1.0 local",
          "duration":len(full)/sr,"phrases":timeline}
(OUT/"voice-timeline.json").write_text(json.dumps(metadata,indent=2))
print("COMPLETE",json.dumps(metadata),flush=True)
