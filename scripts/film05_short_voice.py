#!/usr/bin/env python3
"""Original locally generated voiceover for the phone-first Sauce Film 05 short."""
from pathlib import Path
import json,wave
import numpy as np
from kokoro_onnx import Kokoro
P=Path(__file__).resolve().parents[1]/"studio"/".tmp"/"film-05"
MODEL=Path(__file__).resolve().parents[1]/"studio"/".tmp"/"educational-pilot"
VOICE=Kokoro(str(MODEL/"kokoro-v1.0.int8.onnx"),str(MODEL/"voices-v1.0.bin"))
LINES=[
 ("hook",0.14,"Connect your coding agent."),
 ("choose",1.86,"Choose Codex."),
 ("copy",3.20,"Copy the setup command."),
 ("approve",5.10,"Then sign in to approve access.")
]
SR=24000
DURATION=8.4
audio=np.zeros(round(SR*DURATION),dtype=np.float32)
rows=[]
for name,start,words in LINES:
 track,rate=VOICE.create(words,voice="af_heart",speed=1.12,lang="en-us")
 if rate!=SR:raise RuntimeError("Unexpected TTS output sample rate")
 track=np.asarray(track,dtype=np.float32)
 end=start+len(track)/rate
 if end>DURATION-.2:raise ValueError(f"Voice overhang: {name} at {end:.2f}s")
 pos=int(start*SR)
 audio[pos:pos+len(track)]+=track
 rows.append({"id":name,"text":words,"start":start,"end":round(end,3)})
peak=float(np.max(np.abs(audio)))
if peak>.86:audio*=.86/peak
P.mkdir(parents=True,exist_ok=True)
with wave.open(str(P/"short-voice.wav"),"wb") as output:
 output.setnchannels(1);output.setsampwidth(2);output.setframerate(SR)
 output.writeframes((audio*32767).astype("<i2").tobytes())
(P/"short-voice.json").write_text(json.dumps({"lines":rows},indent=2))
print("Generated short narration",rows)
