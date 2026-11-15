#!/usr/bin/env python3
"""Sauce v13 quality gate over the actual master MP4 and session evidence."""
from __future__ import annotations
from pathlib import Path
import json,math,subprocess,sys
import cv2
import numpy as np
from session_contract import verify_package
from session_replay import cursor_motion
from cinematic_presentation_v13 import (make_dark_stage,pointer_image,click_ring_frames,
    cursor_press_scale,WINDOW_X,WINDOW_Y,WINDOW_W,WINDOW_H)
from cinematic_tracks import cinematic_camera

ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'studio/.tmp/brimble-cinematic-v11-release'
video=p/'sauce-v13-1080p60.mp4'
j=json.loads((p/'session.json').read_text())
r=json.loads((p/'replay-report.json').read_text())
info=verify_package(j,p)
assert r['presentation_v13'] is True
assert r['native_cursor_suppressed'] is True
assert r['cursor_asset']=='assets/cursors/sauce-pointer.svg'
assert r['stage']=='dark-ambient-multilayer'
assert r['cursor_visibility']=='svg-overlay-always-visible'
assert r['click_feedback']=='svg-pointer-contract-0.85+svg-ripple'
assert r['source_dpr']>=2
assert r['pixel_resampling']=='Lanczos4'
assert r['presentation_only_hidden_selector']=='img[src*="bee-cutout"]'
assert r['presentation_only_hidden_count']==1
assert len(r['semantic_checks'])==3 and len(r['visual_region_checks'])==3
assert all(e['roi_mae']<5 for e in r['visual_region_checks'])
assert r['animated_frame_effects']>=100

events=j['events'];start=j['states'][0]['at_ms']
camera,meta=cinematic_camera(events,start,4.2,60)
assert meta['first_pointer_motion_ms']<meta['first_click_ms']<meta['modal_visible_ms']
assert max(v[0] for v in camera)<1.40
cursor,_=cursor_motion(events,start,4.2,60)
clicks=[e for e in events if e['type']=='pointerdown']
assert len(clicks)==2
click_errors=[]
for e in clicks:
 frame=round((e['t']-start)*60/1000)
 err=math.dist(cursor[frame],(e['x'],e['y']))
 assert err<3.,err
 click_errors.append(round(err,4))
assert abs(cursor_press_scale(.075)-.85)<1e-9
assert cursor_press_scale(.25)==1.

svg=pointer_image()
assert svg.shape==(38,28,4)
assert np.count_nonzero(svg[:,:,3]>0)>180
assert len(click_ring_frames())>=20
assert click_ring_frames()[0].shape==(72,72,4)

spec=json.loads(subprocess.check_output([
  'ffprobe','-v','error','-show_entries',
  'stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames:format=duration,size',
  '-of','json',str(video)],text=True))
video_stream=next(x for x in spec['streams'] if x['codec_type']=='video')
assert (video_stream['codec_name'],video_stream['width'],video_stream['height'],
        video_stream['r_frame_rate'],int(video_stream['nb_frames']))==('h264',1920,1080,'60/1',252)
subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(video),'-f','null','-'],
    check=True,timeout=90)

stage,clip=make_dark_stage()
assert clip.shape==(900,1600,1)
capture=cv2.VideoCapture(str(video))
capture.set(cv2.CAP_PROP_POS_FRAMES,180)
ok,frame=capture.read()
assert ok
# Dark frame is ENCODED into the MP4, not CSS-only.
outer=np.concatenate([
    frame[70:950,10:90,:].reshape((-1,3)),
    frame[70:950,1830:1910,:].reshape((-1,3))
])
assert np.mean(outer)<75,np.mean(outer)
assert np.std(outer)>4,np.std(outer)
# Custom SVG cursor produces visible high-contrast pixels over both clicks.
for e in clicks:
 idx=round((e['t']-start)*60/1000)+5
 capture.set(cv2.CAP_PROP_POS_FRAMES,idx)
 good,shot=capture.read()
 assert good
 cam=camera[idx]
 z,fx,fy=cam;scale=(WINDOW_W/(info['viewport'][0]*info['dpr']))*z
 dx=max(WINDOW_W-info['viewport'][0]*info['dpr']*scale,
        min(0.,WINDOW_W/2-fx*info['dpr']*scale))
 dy=max(WINDOW_H-info['viewport'][1]*info['dpr']*scale,
        min(0.,WINDOW_H/2-fy*info['dpr']*scale))
 px=round(WINDOW_X+dx+cursor[idx][0]*info['dpr']*scale)
 py=round(WINDOW_Y+dy+cursor[idx][1]*info['dpr']*scale)
 roi=shot[max(0,py-3):py+35,max(0,px-3):px+31]
 assert roi.size>0
 assert (roi.max()-roi.min())>30,(idx,roi.max()-roi.min())
capture.release()

result={'master':str(video),'frames':252,'fps':60,'resolution':[1920,1080],
        'source_dpr':info['dpr'],'cursor_asset':r['cursor_asset'],
        'no_native_cursor':True,'svg_click_ring':True,
        'click_coordinate_error_css_px':click_errors,
        'semantic_checks':3,'pixel_roi_checks':3,
        'dark_stage_average_brightness':round(float(np.mean(outer)),2),
        'dark_stage_color_variance':round(float(np.std(outer)),2),
        'source_and_export_decode':'passed'}
(p/'quality-v13.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
