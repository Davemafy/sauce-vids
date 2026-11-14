#!/usr/bin/env python3
"""Align generated voice to exact audible words with on-device Whisper."""
from pathlib import Path
from faster_whisper import WhisperModel
import json
import soundfile as sf
import numpy as np
import subprocess
P=Path(__file__).resolve().parents[1]/"studio"/".tmp"/"film-paradigm"
model=WhisperModel("base.en",device="cpu",compute_type="int8",cpu_threads=8,num_workers=1)
pcm=np.frombuffer(subprocess.check_output(["ffmpeg","-v","error","-i",str(P/"voice.wav"),"-ac","1","-ar","16000","-f","f32le","pipe:1"]),dtype=np.float32)
segments,info=model.transcribe(pcm,beam_size=4,word_timestamps=True,vad_filter=False,condition_on_previous_text=False)
words=[];texts=[]
for s in segments:
 texts.append(s.text.strip())
 if s.words:
  for w in s.words:
   words.append({"text":w.word.strip(),"start":round(w.start,3),"end":round(w.end,3),"probability":round(w.probability,3)})
result={"words":words,"transcript":" ".join(texts),"source":"faster-whisper base.en CPU word alignment"}
(P/"word-timings.json").write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
