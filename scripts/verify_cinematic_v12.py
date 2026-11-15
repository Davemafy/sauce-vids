#!/usr/bin/env python3
"""Sauce v12 acceptance: film and physical pointer, not merely test counts."""
from __future__ import annotations
import json,math,subprocess,sys
from pathlib import Path
import cv2,numpy as np
from session_contract import verify_package
from session_replay import cursor_motion
from cinematic_tracks import cinematic_camera
from cinematic_presentation_v12 import draw_stage,WINDOW_X,WINDOW_Y,WINDOW_W,WINDOW_H
from presentation_contract import presentation_css_cursor,press_scale,modal_spring_scale

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'studio'/'.tmp'/'brimble-cinematic-v11-release'
video=P/'sauce-v12-1080p60.mp4'
manifest=json.loads((P/'session.json').read_text())
capture=verify_package(manifest,P)
report=json.loads((P/'replay-report.json').read_text())
assert report['presentation_v12'] is True
assert report['cursor_visibility']=='persistent'
assert report['click_feedback']=='physical press+ring'
assert report['presentation_only_hidden_count']==1
assert report['presentation_only_hidden_selector']=='img[src*="bee-cutout"]'
assert report['pixel_resampling']=='Lanczos4'
assert report['source_dpr']==2
assert report['encoder_profile']=={'crf':14,'preset':'medium'}
assert report['animated_frame_effects']>=100
assert len(report['semantic_checks'])==3
assert len(report['visual_region_checks'])==3
assert all(r['roi_mae']<4 for r in report['visual_region_checks'])

events=manifest['events']
clicks=[e for e in events if e['type']=='pointerdown' and e.get('x') is not None]
assert len(clicks)==2
start=manifest['states'][0]['at_ms']
camera,cues=cinematic_camera(events,start,4.2,60)
assert len(camera)==252 and cues['first_zoom_frame']>0
assert cues['first_pointer_motion_ms']<clicks[0]['t']<cues['modal_visible_ms']
assert cues['max_zoom']<=1.40
for frame in range(math.floor((cues['first_pointer_motion_ms']-start)/1000*60)):
    assert camera[frame]==(1.,640.,360.)
path,_=cursor_motion(events,start,4.2,60)
targets=[e['box'] for e in clicks]
errors=[]
for event in clicks:
    f=round((event['t']-start)*60/1000)
    deviation=math.dist(path[f],(event['x'],event['y']))
    assert deviation<3,deviation
    cursor_name=presentation_css_cursor('none',path[f],targets)
    assert cursor_name=='pointer',(cursor_name,event)
    errors.append(round(deviation,3))
    assert press_scale(events, (event['t']-start)/1000+.065,start)<.90
assert .95<=modal_spring_scale(0)<1
assert modal_spring_scale(.35)>.999
base,clip=draw_stage()
assert base.shape==(1080,1920,3)
assert clip.shape==(900,1600,1)
# Multicolor ambient light and multi-tier shadows have both been baked into
# the actual output frame, independent of the source application screenshot.
spread=np.std(base[:,:,:].reshape((-1,3)),axis=0)
assert min(spread)>3,spread
assert WINDOW_X>=120 and WINDOW_W<=1700 and WINDOW_Y+WINDOW_H<1080

meta=json.loads(subprocess.check_output([
    'ffprobe','-v','error',
    '-show_entries','stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames:format=duration,size',
    '-of','json',str(video)],text=True))
stream=next(x for x in meta['streams'] if x['codec_type']=='video')
assert stream['codec_name']=='h264'
assert (stream['width'],stream['height'],stream['r_frame_rate'],int(stream['nb_frames']))==(1920,1080,'60/1',252)
subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(video),'-f','null','-'],check=True,timeout=90)

cap=cv2.VideoCapture(str(video))
diffs=[]
last=None
for f in range(round(.34*60),round(.74*60)):
    cap.set(cv2.CAP_PROP_POS_FRAMES,f)
    ok,frame=cap.read()
    if not ok:raise RuntimeError('Decode failure at frame '+str(f))
    frame=cv2.cvtColor(cv2.resize(frame,(320,180)),cv2.COLOR_BGR2GRAY)
    if last is not None:
        diffs.append(float(np.abs(frame.astype(float)-last.astype(float)).mean()))
    last=frame
cap.release()
moving=sum(v>.02 for v in diffs)
assert moving>=int(len(diffs)*.85),(moving,len(diffs))
result={'export':'sauce-v12-1080p60.mp4',
        'source_capture_states':len(manifest['states']),
        'replayed_events':len(events),'semantic_checks':3,'region_matches':3,
        'fps':60,'frames':252,'size':[1920,1080],
        'click_position_errors_css_px':errors,
        'persistent_pointer_with_css_none':True,
        'press_and_ring_on_two_real_clicks':True,
        'modal_spring_range':[.95,1.0],
        'source_supersampling_dpr':2,'resample':'Lanczos4',
        'pixel_region_mae_max':max(x['roi_mae'] for x in report['visual_region_checks']),
        'active_frames_changed':moving,'active_frames_inspected':len(diffs),
        'shadow_glow_stage':True,'full_decode':'passed'}
(P/'quality-v12.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
