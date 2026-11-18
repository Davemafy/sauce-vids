"""Source-true cursor, floating matte and ripple proof for EDL compositor."""
from pathlib import Path
import sys
import cv2
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from cinematic_recorded_pointer import (
    CinematicRecordedPointer,pointer_visibility_report)
from floating_ui_stage import floating_matrix,composite_stage,rounded_coverage
from click_water_ripple import apply_click_water_ripple


def samples():
    t=np.linspace(0,1,50)
    x=100+500*(t*t*(3-2*t))
    y=160+400*(t*t*(3-2*t))
    x[24]+=3; y[27]-=4 # actual sampling jitter
    return np.stack((t,x,y),axis=1)


def test_professional_pointer_is_brimble_sprite_and_exact_click_hotspot():
    track=samples()
    pointer=CinematicRecordedPointer(track,[.5],film_scale=.56)
    a=np.array(pointer.at(.5))
    b=np.array(pointer.click_center(.5))
    assert np.linalg.norm(a-b)<1e-7
    assert pointer.at(-.02) is None
    assert np.linalg.norm(pointer.at(1.4)-track[-1,1:])<.03
    screen=np.full((1080,1920,3),[32,34,39],np.uint8)
    pointer.paint(screen,(850,460),.5)
    assert np.any(screen[458:510,848:900] != [32,34,39])
    assert np.array_equal(screen[:100],np.full((100,1920,3),
                                                 [32,34,39],np.uint8))


def test_rounded_stage_is_real_window_floating_over_a_neutral_matte():
    src=np.full((180,320,3),[10,16,28],np.uint8)
    base=np.float64([[1,0,0],[0,1,0]])
    camera=floating_matrix(base,(320,180),.78)
    mask=rounded_coverage(camera,(320,180),(320,180))
    assert mask[90,160]==255
    assert mask[0,0]==0
    output=composite_stage(src,camera,(320,180))
    np.testing.assert_array_equal(output[90,160],src[90,160])
    assert not np.array_equal(output[0,0],src[0,0])
    assert np.array_equal(src[90,160],[10,16,28])


def test_ripple_modifies_only_real_composed_product_layer_and_settles():
    src=np.zeros((360,640,3),np.uint8)
    src[:,::4]=[160,190,235]
    before=src.copy()
    assert apply_click_water_ripple(src,(310,180),.15,intensity=.75,
                                    lifetime_s=.49)
    assert np.any(src!=before)
    still=before.copy()
    assert not apply_click_water_ripple(still,(310,180),.50,intensity=.75,
                                        lifetime_s=.49)
    np.testing.assert_array_equal(still,before)


class Shot:
    def __init__(self):
        self.start=0
        self.out_start=0
        self.label='verified action'
    def length(self):
        return 60


def test_camera_must_keep_real_cursor_inside_film():
    track=samples()
    pointer=CinematicRecordedPointer(track,[.5])
    manifest={'lead_s':0}
    def visible(*args):
        return np.float64([[1,0,0],[0,1,0]])
    good=pointer_visibility_report(pointer,[Shot()],manifest,
                                  (640,720),(640,720),visible)
    assert good['offscreenFrames']==0
    def offscreen(*args):
        return np.float64([[1,0,900],[0,1,0]])
    bad=pointer_visibility_report(pointer,[Shot()],manifest,
                                 (640,720),(640,720),offscreen)
    assert bad['offscreenFrames']>0
    assert bad['firstOffscreenFrames'][0]['shot']=='verified action'


def test_renderer_flags_and_order_preserve_source_pixels_before_pointer():
    s=(Path(__file__).resolve().parents[2]/
       'scripts/evidence_edl_renderer.py').read_text()
    assert '--floating-stage' in s and '--premium-cursor' in s
    assert '--click-water-ripple' in s and '--quality-gate' in s
    assert s.index('apply_click_water_ripple(')<s.index('composite_stage(image,')
    assert s.index('composite_stage(image,')<s.index('pointer.paint(image,')
    assert 'cursor_visibility[\'offscreenFrames\']' in s

def test_upper_result_anchor_is_real_source_geometry_not_guess():
    from evidence_edl_renderer import pose
    manifest={'events':[{
        'kind':'state_change',
        'evidence':'Real browser DOM content',
        'resultRect':{'x':500.,'y':160.,'width':650.,'height':560.}}]}
    cx,cy=pose(manifest,'result-upper:0',(1600,900))
    assert cx==825.
    assert cy==pytest.approx(350.4)
    assert pose(manifest,'result:0',(1600,900))==(825.,440.)
