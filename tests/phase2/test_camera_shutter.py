"""Shutter samples must remain source-true and never smear reading holds."""
from pathlib import Path
import sys
import numpy as np
import cv2
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from camera_shutter import shutter_camera_warp

class Shot:
    def length(self):
        return 100

def src():
    y,x=np.mgrid[0:160,0:240]
    return np.stack([((x//5)%2)*205+25,((y//4)%2)*220+20,
                     (((x+y)//7)%2)*200+35],axis=-1).astype(np.uint8)

def fixed(manifest,shot,f,source_size,output_size):
    return np.array([[1,0,0],[0,1,0]],dtype=np.float64)

def glide(manifest,shot,f,source_size,output_size):
    z=1+0.22*min(1,max(0,f/40))
    return np.array([[z,0,-22*(z-1)],[0,z,-15*(z-1)]],dtype=np.float64)

def test_stationary_frame_stays_pixel_identical():
    s=src()
    f=shutter_camera_warp(s,Shot(),50,{},(240,160),(240,160),fixed)
    np.testing.assert_array_equal(f,s)
    np.testing.assert_array_equal(s,src())

def test_actual_camera_movement_exposes_blur_without_inventing_source():
    s=src()
    actual=shutter_camera_warp(s,Shot(),20,{},(240,160),(240,160),glide)
    mid=glide({},Shot(),20,(240,160),(240,160))
    sharp=cv2.warpAffine(s,mid,(240,160),flags=cv2.INTER_CUBIC,
                        borderMode=cv2.BORDER_REPLICATE)
    assert actual.shape==sharp.shape and actual.dtype==np.uint8
    assert np.any(actual!=sharp)
    assert (actual>=0).all() and (actual<=255).all()
    # At the end of the camera motion there is no blur.
    stable=shutter_camera_warp(s,Shot(),75,{},(240,160),(240,160),glide)
    key=glide({},Shot(),75,(240,160),(240,160))
    np.testing.assert_array_equal(stable,cv2.warpAffine(s,key,(240,160),
                          flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE))

def test_shutter_never_samples_outside_the_current_shot():
    seen=[]
    def cam(m,shot,f,ss,os):
        seen.append(f)
        return fixed(m,shot,f,ss,os)
    s=src()
    for i in [0,99]:
        shutter_camera_warp(s,Shot(),i,{},(240,160),(240,160),cam)
    assert all(0<=v<=99 for v in seen)

def test_opt_in_wiring_keeps_default_renderer_and_pointer_layer_separate():
    x=(Path(__file__).resolve().parents[2]/'scripts/evidence_edl_renderer.py').read_text()
    assert '--camera-shutter' in x
    assert 'if motion_shutter:' in x
    assert x.index('shutter_camera_warp(')<x.index('project_pointer(image,')
