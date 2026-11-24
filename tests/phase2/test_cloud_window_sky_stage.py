"""Clouds in the environment; crisp real browser inside clear floating glass."""
from pathlib import Path
import sys
import hashlib

import cv2
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from cloud_window_sky_stage import (
    PRESET, sky_background, physical_plate, card_mask, object_mask, window_geometry)
from cloud_shadow_stage import backdrop as legacy_clouds, card_mask as legacy_window
from spatial_studio_stage import load_studio_stage, render_studio_stage
from studio_plan_bounded_repair import normalize_generated_studio_plan


def test_clouds_are_background_and_glass_has_its_own_physical_shape():
    output=(1920,1080)
    source=(2880,1800)
    background=sky_background(output)
    full=physical_plate(source,output)
    outer=object_mask(output)
    inner=card_mask(source,output)
    assert background.shape==full.shape==(1080,1920,3)
    # Clouds are visible across the canvas OUTSIDE the floating glass.
    outside=(outer<5)
    assert outside.mean()>.20
    # Shadows must be visible immediately outside the shell, while the
    # farther sky is unchanged and stationary.
    np.testing.assert_array_equal(full[:18,:18],background[:18,:18])
    assert np.std(background[outside].astype(float))>15
    # A neat, thin acrylic browser border — no giant cloud-filled body.
    exposed=(outer>245)&(inner==0)
    assert .027<exposed.mean()<.06
    assert (inner>245).mean()>.70
    assert np.mean(np.abs(full[exposed].astype(float)-
                          background[exposed].astype(float)))>9.
    # New cloud orientation is structurally different from old white studio.
    # The actual new artwork, not the previous tinted cobalt stage.
    original = Path(__file__).resolve().parents[2]/(
        "assets/stages/sauce_sky_halftone_1536x864.webp")
    assert original.is_file()
    assert hashlib.sha256(original.read_bytes()).hexdigest() == (
        "359bf6d37f2820b303606c2c6e4e897f6445fdd740ab46a449f1195376b55096"
    )
    exact = cv2.imread(str(original), cv2.IMREAD_COLOR)
    np.testing.assert_array_equal(sky_background((1536,864)),exact)
    assert legacy_clouds(*output).shape==background.shape
    assert np.mean(np.abs(background.astype(np.int16)-
                          legacy_clouds(*output).astype(np.int16)))>15


def test_one_large_rounded_browser_no_cutout_or_decorative_tail():
    source=(2880,1800); output=(1920,1080)
    outer=object_mask(output,source)
    inner=card_mask(source,output)
    assert (outer[inner==255]>245).all()
    x0,y0,x1,y1,_=window_geometry(source,output)
    assert 170<=x0<=215 and 45<=y0<=75
    assert 1500<=x1-x0<=1580
    assert 940<=y1-y0<=980
    # One continuous rounded-rectangle silhouette across the height; no
    # sculpted lower-right protrusion or cloud-filled decorative wing.
    for row in (250,550,850):
        xx=np.flatnonzero(outer[row]>245)
        assert xx[0]<x0 and xx[-1]>x1
        assert abs(xx[0]+xx[-1]-1920)<4
    assert outer[1000,1755]<10
    assert outer[1000,1650]>245
    assert outer[0,0]==0
    # Real browser coverage is larger than the prior 87.5%-height default.
    assert inner.sum()>legacy_window(source,output).sum()


@pytest.fixture
def actual_source_fixture(tmp_path):
    src=(320,180)
    original=np.full((180,320,3),(52,130,222),dtype=np.uint8)
    original[35:110,95:210]=(202,55,84)
    filename=tmp_path/"source-original.mp4"
    writer=cv2.VideoWriter(str(filename),cv2.VideoWriter_fourcc(*"mp4v"),25,src)
    assert writer.isOpened()
    for _ in range(60): writer.write(original)
    writer.release()
    event={"kind":"click","start":.35,"end":.45,"t":.7,
           "evidence":"Genuine browser DOM change",
           "targetRect":{"x":95,"y":35,"width":35,"height":23},
           "resultRect":{"x":95,"y":35,"width":115,"height":75}}
    manifest={"duration":2.4,"capture_rect":{"width":320,"height":180},
              "events":[event]}
    cfg={"stagePreset":PRESET,
         "camera":[{"at":0,"scale":.88,"center":[.5,.5]},
                   {"at":2.4,"startAt":1.8,"scale":.92,
                    "center":[.5,.5]}],
         "lighting":{"eventIndex":0,"trigger":"verified"},
         "payoff":{"region":"event:0:result","mode":"detail","minVisible":.7}}
    return filename,original,manifest,cfg


def test_pure_source_pixels_and_fixed_sky_during_real_camera(actual_source_fixture):
    path,frame,manifest,cfg=actual_source_fixture
    stage=load_studio_stage(cfg,manifest,path,(320,180),(640,360),2.4,25)
    assert stage.stage_preset==PRESET
    output=render_studio_stage(stage,frame,0)
    sky=sky_background((640,360))
    assert np.array_equal(output[0,0],sky[0,0])
    q=stage.quad(0)
    H=cv2.getPerspectiveTransform(np.float32([
        [0,0],[319,0],[319,179],[0,179]]),q)
    projected=cv2.warpPerspective(frame,H,(640,360),
                                  flags=cv2.INTER_CUBIC,
                                  borderMode=cv2.BORDER_CONSTANT)
    mask=card_mask((320,180),(640,360))
    np.testing.assert_array_equal(output[mask==255],projected[mask==255])
    late=render_studio_stage(stage,frame,2.4)
    assert np.array_equal(late[0,0],sky[0,0])
    assert not np.array_equal(output,late)


def test_existing_preset_and_explicit_new_sky_choice_remain_distinct():
    raw={"studioStage":{"stagePreset":PRESET,"camera":[
        {"at":0,"scale":.88},{"at":2,"scale":.88}]}}
    accepted,receipt=normalize_generated_studio_plan(raw,enforce_cloud_stage=True)
    assert accepted["studioStage"]["stagePreset"]==PRESET
    assert raw["studioStage"]["stagePreset"]==PRESET
    assert not [item for item in receipt["changes"]
                if item["field"]=="studioStage.stagePreset"]
    old=raw.copy()
    old["studioStage"]={**raw["studioStage"],"stagePreset":"classic"}
    locked,_=normalize_generated_studio_plan(old,enforce_cloud_stage=True)
    assert locked["studioStage"]["stagePreset"]=="cloud_shadow_v1"


def test_all_landscape_sizes_fit_without_source_clipping():
    for output in ((640,360),(1280,720),(1920,1080)):
        inner=card_mask((2880,1800),output)
        outer=object_mask(output,(2880,1800))
        assert np.all(outer[inner==255]>245)
        assert not np.any(outer[0,:]>10)
        assert not np.any(outer[-1,:]>10)
        assert not np.any(outer[:,0]>10)
        assert not np.any(outer[:,-1]>10)


def test_passive_paldey_showcase_uses_real_browser_over_new_clean_sky():
    from cloud_shadow_stage import render_cloud_overview
    frame=np.full((360,640,3),(21,108,225),np.uint8)
    frame[:,300:]=(196,80,21)
    original=frame.copy()
    result=render_cloud_overview(frame,(640,360),
                                  stage_preset="cloud_window_sky_v1")
    assert result.shape==frame.shape
    np.testing.assert_array_equal(frame,original)
    x0,y0,x1,y1,_=window_geometry((640,360),(640,360))
    sky=sky_background((640,360))
    np.testing.assert_array_equal(result[0,0],sky[0,0])
    np.testing.assert_array_equal(result[(y0+y1)//2,x0+20],frame[180,20])
    np.testing.assert_array_equal(result[(y0+y1)//2,x1-20],frame[180,620])
    # Product pixels are source-true, no synthetic dashboard or typography.
    old=render_cloud_overview(frame,(640,360))
    assert not np.array_equal(old[0,0],result[0,0])
