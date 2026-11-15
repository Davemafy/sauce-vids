#!/usr/bin/env python3
"""Check v15 exports against the real captured session and visual requirements."""
from __future__ import annotations
from pathlib import Path
import json,math,subprocess
import cv2,numpy as np

from session_contract import verify_package
from session_replay import cursor_motion
from cinematic_tracks import cinematic_camera
from reference_cursor_v15 import load_cursor,press_scale,STYLES

ROOT=Path(__file__).resolve().parents[1]
VARIANTS={
    'ink':(ROOT/'studio/.tmp/brimble-reference-v15-ink','sauce-v15-black-1080p60.mp4'),
    'outline':(ROOT/'studio/.tmp/brimble-reference-v15-outline','sauce-v15-outline-1080p60.mp4'),
}
captures={}
for name,(directory,filename) in VARIANTS.items():
    session=json.loads((directory/'session.json').read_text())
    info=verify_package(session,directory)
    report=json.loads((directory/'replay-report.json').read_text())
    assert report['presentation_v15'] is True
    assert report['cursor_style']==name
    assert report['native_cursor_suppressed'] is True
    assert report['cursor_visibility']=='reference-svg-overlay-always-visible'
    assert report['click_feedback']=='reference-pointer-contract-0.88+svg-ripple'
    assert report['source_dpr']>=2 and report['pixel_resampling']=='Lanczos4'
    assert report['stage']=='dark-ambient-multilayer'
    assert report['presentation_only_hidden_count']==1
    assert report['frames']==252 and report['fps']==60
    assert len(report['semantic_checks'])==3
    assert len(report['visual_region_checks'])==3
    assert all(z['roi_mae']<5 for z in report['visual_region_checks'])
    cursor_sprite=load_cursor(name)
    assert cursor_sprite.rgba.ndim==3 and cursor_sprite.rgba.shape[2]==4
    assert cursor_sprite.rgba[:,:,3].max()==255
    assert 60<cursor_sprite.hotspot[0]<75
    assert 60<cursor_sprite.hotspot[1]<75
    assert cursor_sprite.geometry==STYLES[name]['size']
    # The feathered shadow must extend beyond the SVG's primary fill.
    a=cursor_sprite.rgba[:,:,3]
    assert np.count_nonzero((a>0)&(a<200))>300
    source=directory/filename
    preview=directory/'preview.mp4'
    specs=json.loads(subprocess.check_output([
        'ffprobe','-v','error','-show_entries',
        'stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames',
        '-of','json',str(source)],text=True))
    stream=next(x for x in specs['streams'] if x['codec_type']=='video')
    assert (stream['codec_name'],stream['width'],stream['height'],
            stream['r_frame_rate'],int(stream['nb_frames']))==('h264',1920,1080,'60/1',252)
    for video in (source,preview):
        subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(video),'-f','null','-'],
                       check=True,timeout=65)
    captures[name]=(session,info,report,source)

assert abs(press_scale(.075)-.88)<1e-7
assert press_scale(None)==1.0
session,info,report,_=captures['ink']
start=session['states'][0]['at_ms']
events=session['events']
cursor,_=cursor_motion(events,start,4.2,60)
camera,cues=cinematic_camera(events,start,4.2,60)
assert cues['first_pointer_motion_ms']<cues['first_click_ms']<cues['modal_visible_ms']
assert cues['max_zoom']<1.4
clicks=[e for e in events if e['type']=='pointerdown' and e.get('x') is not None]
assert len(clicks)==2
caps=[cv2.VideoCapture(str(captures[style][3])) for style in ('ink','outline')]
errors=[];different=[]
for event in clicks:
    frame=round((event['t']-start)/1000*60)
    err=math.dist(cursor[frame],(event['x'],event['y']))
    assert err<3
    errors.append(round(err,4))
    shifted=frame+5
    shots=[]
    for cap in caps:
        cap.set(cv2.CAP_PROP_POS_FRAMES,shifted)
        ok,shot=cap.read()
        assert ok
        shots.append(shot)
    z,fx,fy=camera[shifted]
    factor=(1600/(info['viewport'][0]*info['dpr']))*z
    dx=max(1600-info['viewport'][0]*info['dpr']*factor,
           min(0,800-fx*info['dpr']*factor))
    dy=max(900-info['viewport'][1]*info['dpr']*factor,
           min(0,450-fy*info['dpr']*factor))
    x=round(160+dx+cursor[shifted][0]*info['dpr']*factor)
    y=round(50+dy+cursor[shifted][1]*info['dpr']*factor)
    assert 160<x<1760 and 50<y<950
    box=(slice(y-22,y+95),slice(x-22,x+100))
    a,b=[shot[box] for shot in shots]
    difference=float(np.abs(a.astype('float32')-b.astype('float32')).mean())
    assert difference>3.5,(shifted,difference)
    different.append(round(difference,2))
for cap in caps:cap.release()

result={
    'variants':['ink','outline'],
    'reference':'user-supplied cursor images',
    'master_resolution':[1920,1080],
    'fps':60,
    'frames_per_variant':252,
    'recorded_clicks':len(clicks),
    'click_deviation_css_px':errors,
    'visual_pixel_difference_between_styles':different,
    'roi_checks_each':3,
    'semantic_checks_each':3,
    'native_cursor_suppressed':True,
    'pointer_shadow':[0,12,24,.35],
    'press_peak_scale':press_scale(.075),
    'full_decode':True
}
(VARIANTS['ink'][0]/'quality-v15.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
