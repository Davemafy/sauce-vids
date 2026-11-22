"""Opt-in camera motion craft: source clock, endpoints, shutter and pointer."""
from pathlib import Path
import json
import sys

import cv2
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from spatial_studio_stage import (
    _eased,_cinematic_eased,load_studio_stage,render_studio_stage)


def capture(tmp_path):
    path=tmp_path/"source.mp4"
    v=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*"mp4v"),60,(320,180))
    assert v.isOpened()
    frame=np.zeros((180,320,3),np.uint8)
    frame[:]=[105,135,155]
    frame[20:65,60:190]=[0,200,85]
    for _ in range(180):v.write(frame)
    v.release()
    e={"kind":"click","start":.40,"end":.48,"t":.9,
       "evidence":"Original verified browser event",
       "targetRect":{"x":40,"y":30,"width":70,"height":28},
       "resultRect":{"x":110,"y":70,"width":140,"height":60}}
    m={"duration":3.,"events":[e],
       "capture_rect":{"width":320,"height":180}}
    cfg={"camera":[
        {"at":0,"scale":.8,"center":[.5,.5],"yaw":0,"pitch":0},
        {"at":1.95,"startAt":1.0,"scale":1.16,
         "focus":"event:0:result","yaw":0,"pitch":0},
        {"at":3.0,"startAt":2.15,"scale":.85,
         "center":[.5,.5],"yaw":0,"pitch":0}],
      "material":{"color":[25,28,32],"grain":.04},
      "lighting":{"eventIndex":0,"trigger":"verified","intensity":.2,
                  "transitionSeconds":.32},
      "payoff":{"region":"event:0:result","mode":"detail","minVisible":.7}}
    return path,m,cfg,frame


def test_cinematic_easing_monotonic_exact_and_different_from_classic():
    pts=np.linspace(0,1,121)
    for offset in (.34,-.12):
        v=[_cinematic_eased(float(x),advance=offset) for x in pts]
        assert v[0]==0 and v[-1]==1
        assert all(a<=b for a,b in zip(v,v[1:]))
        assert min(v)>=0 and max(v)<=1
        assert v[1]-.0<1e-3
        assert 1-v[-2]<1e-3
    assert _cinematic_eased(.5,advance=.34)>_eased(.5)
    assert _cinematic_eased(.5,advance=-.12)<_eased(.5)


def test_opt_in_preserves_exact_classic_pose_and_source_endpoints(tmp_path):
    path,m,cfg,src=capture(tmp_path)
    old=load_studio_stage(cfg,m,path,(320,180),(640,360),3.,60)
    cfg["motion"]={"profile":"classic","shutter":0}
    explicit=load_studio_stage(cfg,m,path,(320,180),(640,360),3.,60)
    for t in np.linspace(0,3,73):
        np.testing.assert_allclose(old.pose(float(t)),explicit.pose(float(t)),atol=0,rtol=0)
        assert old.shutter_times(float(t)) is None
    cfg["motion"]={"profile":"cinematic","shutter":.58}
    new=load_studio_stage(cfg,m,path,(320,180),(640,360),3.,60)
    for key in new.camera:
        np.testing.assert_allclose(old.pose(key.at),new.pose(key.at),atol=1e-10)
    assert not np.allclose(new.pose(1.48),old.pose(1.48))
    assert new.motion_style=="cinematic"
    assert new.fps==60


def test_shutter_only_blurs_within_original_source_camera_motion(tmp_path):
    path,m,cfg,src=capture(tmp_path)
    cfg["motion"]={"profile":"cinematic","shutter":.58}
    new=load_studio_stage(cfg,m,path,(320,180),(640,360),3.,60)
    cfg["motion"]={"profile":"cinematic","shutter":0.0}
    sharp=load_studio_stage(cfg,m,path,(320,180),(640,360),3.,60)
    assert new.shutter_times(.3) is None
    assert new.shutter_times(1.46) is not None
    assert new.shutter_times(2.03) is None
    a=render_studio_stage(new,src,1.46)
    b=render_studio_stage(sharp,src,1.46)
    assert a.shape==b.shape==(360,640,3)
    assert np.any(a!=b)
    steady=render_studio_stage(new,src,.30)
    steady_sharp=render_studio_stage(sharp,src,.30)
    np.testing.assert_array_equal(steady,steady_sharp)
    np.testing.assert_array_equal(src[30,65],[0,200,85])


def test_motion_profile_is_bounded_and_not_implicit(tmp_path):
    path,m,cfg,_=capture(tmp_path)
    for motion in ({"profile":"invented"},{"profile":"classic","shutter":.65},
                   {"profile":"cinematic","shutter":1},
                   {"profile":"cinematic","shutter":-1},
                   {"profile":"cinematic","garbage":True}):
        cfg["motion"]=motion
        with pytest.raises(ValueError):
            load_studio_stage(cfg,m,path,(320,180),(640,360),3.,60)


def test_hard_cut_disables_cross_boundary_shutter(tmp_path):
    path,m,cfg,_=capture(tmp_path)
    cfg["camera"]=[
        {"at":0,"scale":.8,"center":[.5,.5],"yaw":0,"pitch":0},
        {"at":1.5,"startAt":1.5,"scale":1.1,
         "focus":"event:0:result","yaw":0,"pitch":0,"cut":True},
        {"at":3.0,"startAt":2.15,"scale":.9,
         "center":[.5,.5],"yaw":0,"pitch":0}]
    cfg["motion"]={"profile":"cinematic","shutter":.72}
    stage=load_studio_stage(cfg,m,path,(320,180),(640,360),3.,60)
    assert stage.shutter_times(1.5) is None
    assert stage.shutter_times(1.5-.001) is None
