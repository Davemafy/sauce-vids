"""Phase 2 multi-plane depth: exact perspective, occlusion and safe fallback."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import cv2
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from spatial_parallax import window_homography,projected_target_quad,map_pointer
from cinematic_stage import CinematicStage
from multi_plane_depth import focus_background_plane,composite_elevated_modal
from modal_depth_capture import verified_modal_background

WINDOW=(220,124,1480,832)
BOX={'x':440.,'y':183.,'width':400.,'height':360.}
F=1480/1280

def test_h0_h60_exact_perspective_at_zero_tilt():
    H0=window_homography(*WINDOW,0.,0.,focal=1200,z=0.)
    H60=window_homography(*WINDOW,0.,0.,focal=1200,z=60.)
    x,y=1100.,540.
    bg=map_pointer(H0,x,y)
    fg=map_pointer(H60,x,y)
    center=(960.,540.)
    assert np.allclose(bg,(x,y),atol=.001)
    assert np.allclose(fg,(center[0]+(x-center[0])*1200/1140,
                           center[1]+(y-center[1])*1200/1140),atol=.005)
    assert fg[0]>bg[0]
    with pytest.raises(ValueError):window_homography(*WINDOW,1.,1.,focal=1200,z=-10.)
    with pytest.raises(ValueError):window_homography(*WINDOW,1.,1.,focal=1200,z=61.)

def test_tilt_projects_two_distinct_planes_and_preserves_background_math():
    H=window_homography(*WINDOW,1.2,-2.1,focal=1200,z=0.)
    raw=projected_target_quad(BOX,WINDOW,F,0,0,1.2,-2.1,perspective_px=1200)
    src=np.float32([[
        [WINDOW[0]+BOX['x']*F,WINDOW[1]+BOX['y']*F],
        [WINDOW[0]+(BOX['x']+BOX['width'])*F,WINDOW[1]+BOX['y']*F],
        [WINDOW[0]+(BOX['x']+BOX['width'])*F,WINDOW[1]+(BOX['y']+BOX['height'])*F],
        [WINDOW[0]+BOX['x']*F,WINDOW[1]+(BOX['y']+BOX['height'])*F]
    ]])
    assert np.allclose(raw,cv2.perspectiveTransform(src,H)[0],atol=.005)
    elevated=projected_target_quad(BOX,WINDOW,F,0,0,1.2,-2.1,
                                    perspective_px=1200,z=60.)
    assert not np.allclose(raw,elevated)
    assert abs(np.linalg.norm(elevated[1]-elevated[0])/
               np.linalg.norm(raw[1]-raw[0])-1)>.04

def test_background_blur_and_elevated_original_pixels_no_ghost_copy():
    base=np.full((1080,1920,3),80,dtype=np.uint8)
    image=np.full((832,1480,3),80,dtype=np.uint8)
    # Deliberately striped source content: any elevated pixels MUST derive from it.
    x0=int(round(BOX['x']*F));y0=int(round(BOX['y']*F))
    x1=int(round((BOX['x']+BOX['width'])*F))
    y1=int(round((BOX['y']+BOX['height'])*F))
    image[y0:y1,x0:x1]=(245,225,200)
    image[y0+20:y1-20:17,x0+15:x1-15]=(30,20,10)
    frame=focus_background_plane(base,WINDOW,(1.,1.6),1200.,6.,.25)
    before=frame.copy()
    out=composite_elevated_modal(frame,image,BOX,WINDOW,F,0,0,(1.,1.6),1200.,12.)
    quad=projected_target_quad(BOX,WINDOW,F,0,0,1.,1.6,
                                perspective_px=1200,z=60.)
    cx,cy=np.rint(quad.mean(axis=0)).astype(int)
    assert out[cy,cx].mean()>before[cy,cx].mean()+40
    assert not np.shares_memory(out,base)
    assert np.array_equal(out[10,10],base[10,10])
    assert np.array_equal(base[540,960],[80,80,80])

def test_single_plane_fallback_is_identical_without_verified_background():
    stage=CinematicStage()
    source=np.full((832,1480,3),180,dtype=np.uint8)
    spotlight={'active':True,'box':BOX,'factor':F,'dx':0.,'dy':0.,
               'blurPx':6.,'dimOpacity':.25}
    baseline=stage.render(source,tilt=(1.,1.5),perspective_px=1200.,
                          spotlight=spotlight)
    fallback=stage.render(source,tilt=(1.,1.5),perspective_px=1200.,
                          spotlight=spotlight,foreground=None)
    assert np.array_equal(baseline,fallback)

def test_modal_hide_restores_original_style_after_background_screenshot():
    actual=np.full((720,1280,3),100,dtype=np.uint8)
    ok,raw=cv2.imencode('.png',actual)
    assert ok
    class FakePage:
        def __init__(self):self.actions=[]
        def evaluate(self,js,arg=None):
            self.actions.append('hide' if arg else 'restore')
            if arg:return {'box':BOX,'radiusCss':12}
        def screenshot(self,**options):
            self.actions.append('screenshot')
            return raw.tobytes()
    page=FakePage()
    result=verified_modal_background(page,BOX,(720,1280))
    assert result is not None
    assert np.array_equal(result[0],actual)
    assert page.actions==['hide','screenshot','restore']
