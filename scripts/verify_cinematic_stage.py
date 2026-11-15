#!/usr/bin/env python3
"""Decode the real production export and inspect its root-stage pixels."""
from __future__ import annotations
from pathlib import Path
import json,subprocess,sys
import cv2
import numpy as np
from cinematic_stage import (CinematicStage,CinematicCursor,
    WINDOW_X,WINDOW_Y,WINDOW_WIDTH,WINDOW_HEIGHT,STAGE_BACKGROUND,
    GLOW_BLUR,BACKDROP_BLUR)
from session_contract import verify_package

BASE=Path(__file__).resolve().parents[1]
P=BASE/'studio/.tmp/sauce-cinematic-stage-v18'
SOURCE=BASE/'studio/.tmp/brimble-reference-v16-ink'
master=P/'master-1080p60.mp4'
release=json.loads((P/'release.json').read_text())
assert release['root_component']=='CinematicStage'
assert release['cursor_component']=='CinematicCursor'
assert release['window']==[220,124,1480,832]
assert release['stage_background']=='#090a0f'
assert release['glow_blur_px']==140
assert release['window_backdrop_blur_px']==24
assert release['source_dpr']>=2
assert release['preview_resampling']=='lanczos'
assert release['clicks']==2
assert release['semantic_checks']==3
assert release['pixel_region_checks']==3
verify_package(json.loads((SOURCE/'session.json').read_text()),SOURCE)

meta=json.loads(subprocess.check_output([
    'ffprobe','-v','error',
    '-show_entries','stream=codec_name,codec_type,width,height,r_frame_rate,nb_frames',
    '-of','json',str(master)],text=True))
stream=next(v for v in meta['streams'] if v['codec_type']=='video')
assert (stream['width'],stream['height'],stream['r_frame_rate'],int(stream['nb_frames']))==(
    1920,1080,'60/1',252)
cap=cv2.VideoCapture(str(master))
cap.set(cv2.CAP_PROP_POS_FRAMES,12)
ok,frame=cap.read();assert ok
assert frame.shape==(1080,1920,3)
# Frame is dark at the very top-left; flat white stage would fail.
assert frame[12,12].mean()<35,frame[12,12]
# Outside left of window differs strongly from white website interior.
outside=frame[300,WINDOW_X-40].astype(np.float32)
inside=frame[300,WINDOW_X+40].astype(np.float32)
assert outside.mean()<105,outside
assert inside.mean()>160,inside
# Rich multi-hue glows visibly affect the stage without painting over
# the original site screenshot.
a=frame[440,100].astype(np.float32)
b=frame[440,1830].astype(np.float32)
assert np.linalg.norm(a-b)>4,(a,b)
cap.release()

stage=CinematicStage()
assert stage.window==(220,124,1480,832)
# A synthetic site frame proves the pointer is AFTER the screenshot:
site=np.full((WINDOW_HEIGHT,WINDOW_WIDTH,3),230,dtype=np.uint8)
scene=stage.render(site)
events=[{'type':'pointerdown','t':500.,'x':520.,'y':400.}]
cursor=CinematicCursor(stage,events,0,'ink',.56)
after=stage.render(site,lambda out:cursor.draw(out,(520.,400.),.55,1.,0.,0.))
# The composited cursor+ring changes pixels over the source site, but
# the underlying source frame remains unmodified.
assert int(np.abs(scene.astype('int16')-after.astype('int16')).sum())>10000
assert np.all(site==230)

print(json.dumps({'master':str(master),'frames':252,'fps':60,
   'stage_background':'#090a0f','window':stage.window,
   'pixel_dark_root':True,'ambient_color_variation':True,
   'cursor_above_site':True,'source_unmodified':True,
   'source_dpr':release['source_dpr'],
   'semantic_checks':release['semantic_checks'],
   'region_checks':release['pixel_region_checks']},indent=2))
