"""The visual-reference glass OBJECT must be visible and source-safe."""
from pathlib import Path
import sys
import cv2
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from cloud_glass_object_stage import PRESET,object_mask,card_mask,window_geometry,stage_plate
from cloud_shadow_stage import card_mask as legacy_card_mask
from spatial_studio_stage import load_studio_stage,render_studio_stage


def fixture(tmp_path):
    original=np.full((180,320,3),(36,128,219),dtype=np.uint8)
    original[40:120,90:230]=(219,40,80)
    file=tmp_path/"original-real-source.mp4"
    enc=cv2.VideoWriter(str(file),cv2.VideoWriter_fourcc(*"mp4v"),25,(320,180))
    assert enc.isOpened()
    for _ in range(60):enc.write(original)
    enc.release()
    event={"kind":"click","start":.35,"end":.5,"t":.7,
           "evidence":"Actual verified DOM changed",
           "targetRect":{"x":92,"y":45,"width":44,"height":25},
           "resultRect":{"x":90,"y":40,"width":140,"height":80}}
    manifest={"duration":2.4,"capture_rect":{"width":320,"height":180},
              "events":[event]}
    stage={"stagePreset":PRESET,
           "camera":[{"at":0,"scale":.88,"center":[.5,.5]},
                     {"at":2.4,"startAt":1.5,"scale":.9,
                      "center":[.5,.5]}],
           "lighting":{"eventIndex":0,"trigger":"verified"},
           "payoff":{"region":"event:0:result","mode":"detail","minVisible":.8}}
    return file,manifest,stage,original


def test_glass_object_is_big_visible_organic_and_white_backed():
    outer=object_mask((1920,1080))
    inner=card_mask((2880,1800),(1920,1080))
    visible_material=(outer>250)&(inner==0)
    assert visible_material.mean()>.28  # Not another invisible 26px bezel.
    assert np.all(outer[inner==255]==255)
    assert outer[300,1800]>220
    assert outer[950,1800]<30  # Lower-right sculpted recess.
    assert outer[950,1150]>220  # Lower-left body and short right tail.
    assert outer[0,0]<10
    x0,y0,x1,y1,_=window_geometry((2880,1800),(1920,1080))
    assert 120<y0<170 and y1<1000
    assert x1-x0<1400
    plate=stage_plate((2880,1800),(1920,1080))
    assert plate.shape==(1080,1920,3)
    np.testing.assert_allclose(plate[0,0],[250,251,253],atol=3)
    # Wide white studio catchlight, not fluorescent blue border.
    assert plate[77,400].mean()>plate[170,400].mean()
    assert plate[500,1810].mean()<plate[0,0].mean()


def test_new_reference_preset_does_not_mutate_legacy_stage():
    old=legacy_card_mask((2880,1800),(1920,1080))
    new=card_mask((2880,1800),(1920,1080))
    assert old.sum()>new.sum()*1.35
    assert old.shape==new.shape


def test_real_browser_pixels_overlay_glass_without_recolouring(tmp_path):
    video,manifest,plan,original=fixture(tmp_path)
    stage=load_studio_stage(plan,manifest,video,(320,180),(640,360),2.4,25)
    assert stage.stage_preset==PRESET
    frame=render_studio_stage(stage,original,0)
    assert frame.shape==(360,640,3)
    srcpoints=np.float32([[0,0],[319,0],[319,179],[0,179]])
    mat=cv2.getPerspectiveTransform(srcpoints,stage.quad(0))
    expected=cv2.warpPerspective(original,mat,(640,360),
                                 flags=cv2.INTER_CUBIC,
                                 borderMode=cv2.BORDER_CONSTANT)
    mask=card_mask((320,180),(640,360))
    np.testing.assert_array_equal(frame[mask==255],expected[mask==255])
    # Source continues to cover true verified event without fake screen.
    assert stage.visibility(0)>0.99
    assert stage.context_visibility(0)>0.99


def test_organic_glass_object_is_landscape_and_bounded():
    for dims in ((640,360),(1280,720),(1920,1080)):
        mask=object_mask(dims)
        x0,y0,x1,y1,_=window_geometry((2880,1800),dims)
        browser=card_mask((2880,1800),dims)
        assert not np.any(mask[0,:]>200)
        assert not np.any(mask[-1,:]>200)
        assert not np.any(mask[:,0]>200)
        assert not np.any(mask[:,-1]>200)
        assert np.all(mask[browser==255]>200)
        assert x0>0 and y0>0 and x1<dims[0] and y1<dims[1]
