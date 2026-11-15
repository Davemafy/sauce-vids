#!/usr/bin/env python3
"""Verify Spring-cut motion physics and source integrity against the actual film."""
from __future__ import annotations
import argparse,hashlib,json,math,subprocess
from pathlib import Path
import cv2
import numpy as np
from spring_motion import cursor_track
from action_zoom_planner import Rect,build_action_camera

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"studio"/".tmp"/"landscape-hidpi"
CAPTURE=ROOT/"studio"/".tmp"/"film-05"/"capture-events.json"
parser=argparse.ArgumentParser()
parser.add_argument("--video",type=Path,default=P/"sauce-landscape-action-1080p60.mp4")
args=parser.parse_args()
receipt=json.loads((P/"manifest.json").read_text())
events=json.loads(CAPTURE.read_text())
UI_EVENTS={e["action"]:e for e in events["events"] if e["action"] in ("connect-modal-visible","setup-command-visible")}

assert receipt.get("verified")
for name in ("01-agent-section","02-agent-picker","03-command-copied"):
 record=receipt["states"][name]
 file=P/(name+".png")
 assert record["size"]==[3200,1800]
 assert hashlib.sha256(file.read_bytes()).hexdigest()==record["sha256"]
assert receipt["states"]["03-command-copied"]["proof"]["copyConfirmed"]

camera,cues=build_action_camera(
 fps=60,duration=12.9,
 pointer_samples=events["pointer"],
 click_time=next((e["t"] for e in events["events"] if e.get("action")=="click-down" and e.get("label")=="Connect your agent"),4.90),
 click_rect=Rect(**receipt["states"]["01-agent-section"]["proof"]["buttonBox"]),
 modal_open_time=UI_EVENTS["connect-modal-visible"]["t"],
 picker_rect=Rect(**receipt["states"]["02-agent-picker"]["proof"]["dialogBox"]),
 copied_time=UI_EVENTS["setup-command-visible"]["t"],
 result_rect=Rect(**receipt["states"]["03-command-copied"]["proof"]["dialogBox"]),
)
for index in range(math.floor(cues["first_pointer_motion"]*60)):
 z,x,y=camera[index]
 assert abs(z-1.0)<1e-10 and abs(x-800)<1e-10 and abs(y-450)<1e-10,(index,z,x,y)
approach=camera[round(cues["first_click"]*60)]
assert 1.25<approach[0]<1.34 and 640.<approach[1]<700.,approach
assert camera[round((cues["modal_visible"]-.02)*60)][0]<1.34
assert camera[round((cues["copied_state_visible"]-.02)*60)][0]<1.63
assert camera[round(8.6*60)][0]>1.65
cursor=cursor_track(samples=events["pointer"],fps=60,duration=12.9,
  stiffness=784,damping=56)
assert len(camera)==len(cursor)==774
max_scale=max(z for z,x,y in camera)
assert max_scale<=1.67+1e-9
peak_pixel_scale=(1744/3200)*max_scale
assert peak_pixel_scale<1.0

clicks=[(4.90,459.22,416.38),(7.70,667.,551.),(10.15,655.77,628.)]
click_checks=[]
for sec,x,y in clicks:
 sampled=cursor[round(sec*60)]
 error=math.dist(sampled,(x,y))
 assert error<=3.,(sec,error)
 click_checks.append({"at_sec":sec,"cursor_error_css_px":round(error,3)})

# During the copied-command hold, the real modal must stay visible,
# including its top border and footer.
rect=receipt["states"]["03-command-copied"]["proof"]["dialogBox"]
projected=[]
for seconds in (8.0,8.6,10.3,12.0):
 z,focusx,focusy=camera[round(seconds*60)]
 factor=(1744/1600)*z
 # The camera implementation clamps translation to source limits.
 dx=max(1744-3200*(1744/3200)*z,min(0.,1744/2-2*focusx*(1744/3200)*z))
 dy=max(981-1800*(1744/3200)*z,min(0.,981/2-2*focusy*(1744/3200)*z))
 sides=(dx+factor*rect["x"],dy+factor*rect["y"],
        dx+factor*(rect["x"]+rect["width"]),
        dy+factor*(rect["y"]+rect["height"]))
 assert sides[0]>=-1 and sides[1]>=-1 and sides[2]<=1745 and sides[3]<=982,(seconds,sides)
 projected.append([round(x,2) for x in sides])

metadata=json.loads(subprocess.check_output(["ffprobe","-v","error",
 "-show_entries","stream=codec_type,width,height,r_frame_rate,nb_frames:format=duration",
 "-of","json",str(args.video)],text=True))
stream=next(v for v in metadata["streams"] if v.get("codec_type")=="video")
assert (stream["width"],stream["height"])==(1920,1080)
assert stream["r_frame_rate"]=="60/1"
assert int(stream["nb_frames"])==774
# Continuous rendered movement during the first major camera push,
# rather than only setting the container's FPS to 60.
cap=cv2.VideoCapture(str(args.video))
differences=[];previous=None
for index in range(round(4.25*60),round(4.75*60)):
 cap.set(cv2.CAP_PROP_POS_FRAMES,index)
 success,frame=cap.read()
 if not success:raise RuntimeError(f"Frame {index} could not be decoded")
 gray=cv2.cvtColor(cv2.resize(frame,(320,180)),cv2.COLOR_BGR2GRAY)
 if previous is not None:
  differences.append(float(np.mean(np.abs(gray.astype(np.float32)-previous.astype(np.float32)))))
 previous=gray
cap.release()
moving=sum(d>.03 for d in differences)
assert moving>=round(len(differences)*.95),(moving,len(differences))
subprocess.run(["ffmpeg","-v","error","-xerror","-i",str(args.video),
                "-f","null","-"],check=True,timeout=100)
out={"artifact":str(args.video),"fps":60,"frames":774,
     "master_px":[1920,1080],"max_scale":round(max_scale,6),
     "max_output_per_source_px":round(peak_pixel_scale,4),
     "click_checks":click_checks,
     "camera_motion_nonstatic_frames":moving,"camera_motion_checked_frames":len(differences),
     "dialog_projected_bounds":projected,
     "complete_decode":True,"source_hash_verified":True,
     "action_camera_cues":cues,"idle_before_cursor_motion":True}
(P/"action-quality-report.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
