from pathlib import Path
from kokoro_onnx import Kokoro
import numpy as np,json,wave
P=Path("studio/.tmp/film-05")
B=Path("studio/.tmp/educational-pilot")
model=Kokoro(str(B/"kokoro-v1.0.int8.onnx"),str(B/"voices-v1.0.bin"))
lines=[
 ("opening",.42,"Your coding agent needs somewhere to ship."),
 ("connect",3.03,"Connect it to Brimble."),
 ("choose",5.50,"Choose the tool you use."),
 ("copy",8.05,"Copy the setup command."),
 ("approve",10.48,"Sign in to approve access.")
]
rate=24000;duration=14.5
audio=np.zeros(int(duration*rate),dtype=np.float32)
rows=[]
for name,start,words in lines:
 voice,sr=model.create(words,voice="af_heart",speed=1.08,lang="en-us")
 assert sr==rate
 voice=np.asarray(voice,dtype=np.float32)
 end=start+len(voice)/rate
 if end>14.2:raise ValueError("Overhang "+name+" "+str(end))
 off=int(start*rate)
 audio[off:off+len(voice)]+=voice
 rows.append({"id":name,"start":start,"end":round(end,3),"text":words})
 print(name,start,round(end,2),flush=True)
peak=float(np.max(np.abs(audio)))
if peak>.86:audio*=.86/peak
with wave.open(str(P/"narration.wav"),"wb") as f:
 f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate)
 f.writeframes((np.clip(audio,-1,1)*32767).astype("<i2").tobytes())
(P/"voice.json").write_text(json.dumps({"duration":duration,"voice":"Kokoro af_heart offline","lines":rows},indent=2))
