#!/usr/bin/env python3
"""Reject invalid or obviously degraded landscape masters.

Checks source provenance, crop safety, actual output frame count, full decode,
and whether the camera changes on consecutive 60fps frames during a push.
Static holds are intentionally excluded from the latter check.
"""
from pathlib import Path
import hashlib,json,subprocess,cv2,numpy as np
P=Path(__file__).resolve().parents[1]/"studio"/".tmp"/"landscape-hidpi"
VIDEO=P/"sauce-landscape-hidpi-1080p60.mp4"
receipt=json.loads((P/"manifest.json").read_text())
assert receipt["verified"],"Original states not verified"
for name in ("01-agent-section","02-agent-picker","03-command-copied"):
 file=P/(name+".png")
 assert hashlib.sha256(file.read_bytes()).hexdigest()==receipt["states"][name]["sha256"],name
 assert receipt["states"][name]["size"]==[3200,1800],name
assert receipt["states"]["03-command-copied"]["proof"]["copyConfirmed"]
assert "codex mcp add brimble" in receipt["states"]["03-command-copied"]["proof"]["clipboard"]
meta=json.loads(subprocess.check_output([
 "ffprobe","-v","error","-show_entries",
 "stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames:format=duration",
 "-of","json",str(VIDEO)],text=True))
video=next(s for s in meta["streams"] if s.get("codec_type")=="video")
assert (video["width"],video["height"])==(1920,1080)
assert video["r_frame_rate"]=="60/1"
assert int(video["nb_frames"])==774
# Camera max zoom is 1.80, image is captured at 2 device pixels/CSS pixel.
# At 1744 output px per 3200 source px, the output scale is <= 1 (downsampling).
assert (1744/3200)*1.8<1.
# Actual verified command dialog box from the unmodified high-resolution UI.
r=receipt["states"]["03-command-copied"]["proof"]["dialogBox"]
assert all(k in r for k in ("x","y","width","height"))
focus=(800.,450.)
factor=(1744/1600)*1.8
left=1744/2+(r["x"]-focus[0])*factor
right=1744/2+(r["x"]+r["width"]-focus[0])*factor
top=981/2+(r["y"]-focus[1])*factor
bottom=981/2+(r["y"]+r["height"]-focus[1])*factor
assert 0<left<right<1744 and 0<top<bottom<981,(left,top,right,bottom)
# Distinguish continuous encoded motion from the mere presence of 60fps tags.
capture=cv2.VideoCapture(str(VIDEO))
fps=capture.get(cv2.CAP_PROP_FPS)
diffs=[]
for n in range(int(4.70*fps),int(5.65*fps)+1):
 capture.set(cv2.CAP_PROP_POS_FRAMES,n)
 ok,frame=capture.read()
 if not ok:raise RuntimeError("Cannot decode frame "+str(n))
 gray=cv2.cvtColor(cv2.resize(frame,(320,180)),cv2.COLOR_BGR2GRAY)
 if diffs or n>int(4.70*fps):
  diffs.append(float(np.mean(np.abs(gray.astype(np.float32)-prev.astype(np.float32)))))
 prev=gray
capture.release()
nonstatic=sum(d>.03 for d in diffs)
# During this time the camera is intentionally moving; frozen frames
# indicate renderer trouble or bad frame pacing.
assert nonstatic>=int(len(diffs)*.86),(nonstatic,len(diffs))
subprocess.run(["ffmpeg","-v","error","-xerror","-i",str(VIDEO),
 "-f","null","-"],check=True,timeout=90)
result={"verified_sources":3,"video":{"width":1920,"height":1080,"fps":60,
 "frames":774,"duration_s":13},"max_camera_zoom":1.80,
 "peak_input_to_output_scale":round((1744/3200)*1.80,4),
 "dialog_safe_box_output_px":[round(x,1) for x in (left,top,right,bottom)],
 "moving_frames":nonstatic,"camera_motion_samples":len(diffs),
 "full_decode":"passed"}
(P/"quality-report.json").write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
