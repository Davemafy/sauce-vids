"""Cloud stage contract: fixed 16:9 backdrop and rounded source-true window."""
from pathlib import Path
import sys

import cv2
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from cloud_shadow_stage import (PRESET,CLOUD,backdrop,window_geometry,
                                card_mask,stage_plate)
from spatial_studio_stage import load_studio_stage,render_studio_stage
from studio_plan_bounded_repair import normalize_generated_studio_plan


@pytest.fixture()
def source(tmp_path):
    w=cv2.VideoWriter(str(tmp_path/"real.mp4"),cv2.VideoWriter_fourcc(*"mp4v"),25,(320,180))
    assert w.isOpened()
    f=np.full((180,320,3),(50,120,180),np.uint8)
    f[30:120,100:260]=(220,40,100)
    for _ in range(60):w.write(f)
    w.release()
    e={"kind":"click","start":.35,"end":.50,"t":.7,
       "evidence":"Real original Chromium state change observed",
       "targetRect":{"x":85,"y":30,"width":45,"height":25},
       "resultRect":{"x":100,"y":30,"width":160,"height":90}}
    m={"duration":2.4,"events":[e],"capture_rect":{"width":320,"height":180}}
    p={"stagePreset":PRESET,
       "camera":[{"at":0,"scale":.79,"center":[.5,.5],"yaw":0,"pitch":0},
                 {"at":1.4,"startAt":.85,"scale":.86,"center":[.5,.5],
                  "yaw":0,"pitch":0},
                 {"at":2.4,"startAt":1.8,"scale":.81,"center":[.5,.5],
                  "yaw":0,"pitch":0}],
       "lighting":{"eventIndex":0,"trigger":"verified"},
       "payoff":{"region":"event:0:result","mode":"overview","minVisible":.80}}
    return tmp_path/"real.mp4",m,p,f


def test_cloud_is_a_real_local_asset_and_fixed_rounded_card():
    assert CLOUD.is_file()
    x0,y0,x1,y1,r=window_geometry((2880,1800),(1920,1080))
    assert 120<y0<200 and 280<x0<370
    assert x1-x0>1200 and y1-y0>800
    assert 16<=r<=25
    m=card_mask((2880,1800),(1920,1080))
    assert m[y0,x0]==0 and m[y0,x0+r+4]>250
    assert m[y0+2,x0+2]==0  # genuinely rounded, no rectangular source pixels
    assert m[540,960]==255
    assert m[0,0]==0
    cloud=backdrop(1920,1080)
    stage=stage_plate((2880,1800),(1920,1080))
    assert cloud.shape==(1080,1920,3)
    assert cloud[0,0,0]>cloud[0,0,2]  # actual blue-sky palette
    assert np.array_equal(stage[0,0],cloud[0,0])
    assert np.mean(stage[y1+18,x0+60:x1-60]) < np.mean(cloud[y1+18,x0+60:x1-60])


def test_fixed_shell_but_moving_inner_source_uses_original_pixels(source):
    video,m,plan,original=source
    stage=load_studio_stage(plan,m,video,(320,180),(640,360),2.4,25)
    assert stage.stage_preset==PRESET
    x0,y0,x1,y1,_=window_geometry((320,180),(640,360))
    np.testing.assert_allclose(stage.quad(0),
      np.float32([[x0,y0],[x1,y0],[x1,y1],[x0,y1]]),atol=.002)
    assert stage.context_visibility(0)>0.99
    before=original.copy()
    a=render_studio_stage(stage,original,0)
    b=render_studio_stage(stage,original,1.6)
    assert a.shape==b.shape==(360,640,3)
    np.testing.assert_array_equal(original,before)
    assert not np.array_equal(a,b), "The real camera must work inside fixed stage"
    msk=card_mask((320,180),(640,360))
    assert np.array_equal(a[0,0],b[0,0]),"Locked cloud never changes with product motion"
    assert a[y0,x0].tolist()==b[y0,x0].tolist()
    assert a[(y0+y1)//2,(x0+x1)//2].tolist()!=[0,0,0]


def test_only_approved_preset_and_model_cannot_change_fixed_stage(source):
    video,m,plan,original=source
    with pytest.raises(ValueError,match="approved rigid"):
        load_studio_stage({**plan,"stagePreset":"random_gradient"},m,video,
                          (320,180),(640,360),2.4,25)
    raw={"studioStage":{"camera":plan["camera"],"stagePreset":"classic"}}
    classic,_=normalize_generated_studio_plan(raw)
    assert classic["studioStage"]["stagePreset"]=="classic"
    locked,proof=normalize_generated_studio_plan(raw,enforce_cloud_stage=True)
    assert locked["studioStage"]["stagePreset"]==PRESET
    assert raw["studioStage"]["stagePreset"]=="classic"
    assert proof["changes"][0]["field"]=="studioStage.stagePreset"



def test_spatial_plane_source_truth_is_not_overridden_by_cloud_lock():
    base={"studioStage":{"camera":[{"at":0,"scale":.8},
                                    {"at":2.,"scale":.8}]},
          "domPlanes":[{"source":"genuine spatial media"}]}
    plan,receipt=normalize_generated_studio_plan(
        base,enforce_cloud_stage=True)
    assert "stagePreset" not in plan["studioStage"]
    assert base==plan
    assert not receipt["changes"]
    singular={"studioStage":base["studioStage"],
              "domPlane":{"source":"original capture"}}
    checked,_=normalize_generated_studio_plan(
        singular,enforce_cloud_stage=True)
    assert "stagePreset" not in checked["studioStage"]
