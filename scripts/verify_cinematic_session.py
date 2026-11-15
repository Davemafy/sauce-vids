#!/usr/bin/env python3
"""On-machine acceptance gate for Sauce cinematic session v11.

Reads real capture evidence and the finished MP4. This is an integration
test, not a replacement for subjective film critique.
"""
from __future__ import annotations
import json,math,subprocess,sys
from pathlib import Path
import cv2,numpy as np
from session_contract import verify_package
from cinematic_tracks import cinematic_camera
from session_replay import cursor_motion

BASE=Path(__file__).resolve().parents[1]/'studio'/'.tmp'/'brimble-cinematic-v11-release'
manifest=json.loads((BASE/'session.json').read_text())
info=verify_package(manifest,BASE)
report=json.loads((BASE/'replay-report.json').read_text())
master=BASE/'sauce-v11-1080p60.mp4'
assert master.is_file(),master
assert report['video'].endswith('sauce-v11-1080p60.mp4')
assert report['verified_semantics']
assert len(report['semantic_checks'])>=3
assert len(report['visual_region_checks'])>=3
assert all(row['roi_mae']<5 for row in report['visual_region_checks'])
assert report['animated_frame_effects']>0
assert report['editorial_background_focus'] is True

events=manifest['events']
start=float(manifest['states'][0]['at_ms'])
duration=report['seconds']
fps=report['fps']
assert (fps,report['frames'])==(60,252)
track,meta=cinematic_camera(events,start,duration,fps)
assert track and len(track)==252
assert meta['first_zoom_frame']>=1
assert meta['first_pointer_motion_ms'] < meta['first_click_ms'] < meta['modal_visible_ms']
assert meta['max_zoom']<=1.44
assert 1.32 < meta['max_zoom'] < 1.43
for index in range(math.floor((meta['first_pointer_motion_ms']-start)/1000*fps)):
    assert track[index]==(1.,640.,360.),(index,track[index])
click_locations=[]
cursor,samples=cursor_motion(events,start,duration,fps)
for e in events:
    if e['type']!='pointerdown':continue
    frame=round((e['t']-start)*fps/1000.)
    actual=(e['x'],e['y'])
    proposed=cursor[frame]
    deviation=math.dist(actual,proposed)
    assert deviation<3,(frame,deviation)
    click_locations.append({'at_s':round(frame/fps,3),'deviation_px':round(deviation,4)})
assert len(click_locations)==2

metadata=json.loads(subprocess.check_output([
 'ffprobe','-v','error','-show_entries',
 'stream=codec_name,codec_type,width,height,r_frame_rate,nb_frames:format=duration,size',
 '-of','json',str(master)],text=True))
stream=next(item for item in metadata['streams'] if item['codec_type']=='video')
assert (stream['codec_name'],stream['width'],stream['height'])==('h264',1920,1080)
assert stream['r_frame_rate']=='60/1'
assert int(stream['nb_frames'])==252
subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(master),
                '-f','null','-'],check=True,timeout=70)
capture=cv2.VideoCapture(str(master))
diffs=[]
last=None
# The recorded cursor traverses the Connect button approach here.
for i in range(round(.30*fps),round(.75*fps)):
    capture.set(cv2.CAP_PROP_POS_FRAMES,i)
    okay,frame=capture.read()
    if not okay:raise RuntimeError('Unrendered camera frame '+str(i))
    gray=cv2.cvtColor(cv2.resize(frame,(320,180)),cv2.COLOR_BGR2GRAY)
    if last is not None:
        diffs.append(float(np.mean(np.abs(gray.astype(np.float32)-last.astype(np.float32)))))
    last=gray
capture.release()
moving=sum(d>.02 for d in diffs)
assert moving>=math.floor(len(diffs)*.8),(moving,len(diffs))
result={
    'video':str(master),'frames':252,'fps':60,
    'capture_states':len(manifest['states']),
    'capture_events':len(events),
    'first_pointer_motion_ms':meta['first_pointer_motion_ms'],
    'first_click_ms':meta['first_click_ms'],
    'modal_visible_ms':meta['modal_visible_ms'],
    'max_zoom':meta['max_zoom'],
    'first_zoom_frame':meta['first_zoom_frame'],
    'click_target_errors':click_locations,
    'semantic_checks':len(report['semantic_checks']),
    'pixel_region_checks':len(report['visual_region_checks']),
    'max_roi_mae':max(r['roi_mae'] for r in report['visual_region_checks']),
    'active_moving_frames':moving,'active_frames_checked':len(diffs),
    'full_decode':True,
}
(BASE/'quality-v11.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
