#!/usr/bin/env python3
"""Acceptance gate for two genuinely distinct MIT Tabler SVG cursors on real video."""
from __future__ import annotations
import json,hashlib,math,subprocess,sys
from pathlib import Path
import cv2,numpy as np
from session_contract import verify_package
from session_replay import cursor_motion
from cinematic_tracks import cinematic_camera
from online_cursor_assets import icon,hotspot

ROOT=Path(__file__).resolve().parents[1]
MODES={
 'ink':ROOT/'studio/.tmp/brimble-tabler-v14',
 'outline':ROOT/'studio/.tmp/brimble-tabler-v14-outline'
}
data={}
for style,folder in MODES.items():
    j=json.loads((folder/'session.json').read_text())
    info=verify_package(j,folder)
    report=json.loads((folder/'replay-report.json').read_text())
    master=folder/f'sauce-v14-{style}-1080p60.mp4'
    preview=folder/f'sauce-v14-{style}-preview.mp4'
    assert master.is_file() and preview.is_file()
    assert report['presentation_v14'] is True
    assert report['cursor_style']==style
    assert report['native_cursor_suppressed'] is True
    assert report['cursor_visibility']=='tabler-svg-overlay-always-visible'
    assert report['source_dpr']==2
    assert report['pixel_resampling']=='Lanczos4'
    assert report['click_feedback']=='tabler-pointer-contract-0.85+svg-ripple'
    assert report['presentation_only_hidden_count']==1
    assert report['frames']==252 and report['fps']==60
    assert len(report['semantic_checks'])==3
    assert len(report['visual_region_checks'])==3
    assert all(x['roi_mae']<5 for x in report['visual_region_checks'])
    pointer=icon(style)
    assert pointer.shape==(52,46,4)
    assert np.count_nonzero(pointer[:,:,3]>0)>200
    hx,hy=hotspot(style)
    assert 0<hx<10 and 0<hy<12
    spec=json.loads(subprocess.check_output([
      'ffprobe','-v','error','-show_entries',
      'stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames',
      '-of','json',str(master)],text=True))
    stream=next(x for x in spec['streams'] if x['codec_type']=='video')
    assert (stream['codec_name'],stream['width'],stream['height'],
            stream['r_frame_rate'],int(stream['nb_frames']))==('h264',1920,1080,'60/1',252)
    subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(master),
                    '-f','null','-'],check=True,timeout=60)
    subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(preview),
                    '-f','null','-'],check=True,timeout=60)
    data[style]=(j,info,report,master)

j,info,report,_=data['ink']
events=j['events'];start=j['states'][0]['at_ms']
cursor,_=cursor_motion(events,start,4.2,60)
camera,meta=cinematic_camera(events,start,4.2,60)
clicks=[e for e in events if e['type']=='pointerdown']
assert len(clicks)==2
assert meta['first_pointer_motion_ms']<meta['first_click_ms']<meta['modal_visible_ms']
caps=[cv2.VideoCapture(str(data[style][3])) for style in ('ink','outline')]
diffs=[]
click_errors=[]
for ev in clicks:
    frame=round((ev['t']-start)*60/1000)+5
    click_frame=round((ev['t']-start)*60/1000)
    err=math.dist(cursor[click_frame],(ev['x'],ev['y']))
    assert err<3.
    click_errors.append(round(err,4))
    shots=[]
    for cap in caps:
        cap.set(cv2.CAP_PROP_POS_FRAMES,frame)
        ok,shot=cap.read()
        assert ok
        shots.append(shot)
    z,fx,fy=camera[frame]
    scale=(1600/(1280*info['dpr']))*z
    dx=max(1600-2560*scale,min(0,800-fx*2*scale))
    dy=max(900-1440*scale,min(0,450-fy*2*scale))
    x=round(160+dx+cursor[frame][0]*2*scale)
    y=round(50+dy+cursor[frame][1]*2*scale)
    assert 160<x<1760 and 50<y<950
    a=shots[0][y-12:y+70,x-12:x+75]
    b=shots[1][y-12:y+70,x-12:x+75]
    mae=float(np.abs(a.astype('float32')-b.astype('float32')).mean())
    assert mae>5,(frame,mae)
    diffs.append(round(mae,2))
for cap in caps:cap.release()
result={'styles':list(MODES),
        'source':'https://github.com/tabler/tabler-icons (MIT)',
        'resolution':'1920x1080','fps':60,'frames_per_style':252,
        'recorded_clicks':2,'click_target_error_css_px':click_errors,
        'different_cursor_pixels_at_clicks_mae':diffs,
        'semantic_checks_each':3,'pixel_region_checks_each':3,
        'native_cursor_suppressed':True,'full_decode_master_and_previews':True,
        'original_site_state_preserved':True}
(MODES['ink']/'quality-v14.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
