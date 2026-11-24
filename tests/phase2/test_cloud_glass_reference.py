"""Owner cloud-glass material: real source pixels and outdoor acrylic tests."""
from pathlib import Path
import sys

import cv2
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from cloud_shadow_stage import (
    backdrop, card_mask, glass_shell_mask, stage_plate, window_geometry)
from spatial_studio_stage import load_studio_stage,render_studio_stage


def test_reference_shell_is_thick_rounded_glass_not_flat_border():
    source=(2880,1800); output=(1920,1080)
    x0,y0,x1,y1,inner_radius=window_geometry(source,output)
    inner=card_mask(source,output)
    outer=glass_shell_mask(source,output)
    assert np.all(outer[inner==255]==255)
    assert outer.sum()>inner.sum()*1.06
    assert outer[y0-12,x0+250]==255
    assert outer[y0-29,x0+250]==0
    assert outer[y0-20,x0-20]==0  # physically rounded acrylic silhouette
    assert inner[y0-12,x0+250]==0
    plate=stage_plate(source,output)
    sky=backdrop(*output)
    # Actual glass is a distinct, cloud-bearing material, not merely a 2px
    # bright border painted on the same backdrop.
    band=(outer>250)&(inner==0)
    mean_rgb_shift=np.mean(np.abs(plate[band].astype(np.int16)-
                                 sky[band].astype(np.int16)))
    assert mean_rgb_shift>5.0
    # Distinct curved top reflection and shadow, no fake popup/browser chrome.
    assert np.linalg.norm(plate[y0-10,x0+400].astype(float)-
                          sky[y0-10,x0+400].astype(float))>8
    assert np.array_equal(plate[0,0],sky[0,0])
    assert plate[y1+35,x0+450].mean()<sky[y1+35,x0+450].mean()


def test_glass_never_filters_any_opaque_product_pixel(tmp_path):
    w,h=320,180
    source=np.full((h,w,3),(37,132,229),np.uint8)
    source[40:95,65:155]=(207,64,29)
    video=tmp_path/"physical-source.mp4"
    writer=cv2.VideoWriter(str(video),cv2.VideoWriter_fourcc(*"mp4v"),
                            25,(w,h))
    assert writer.isOpened()
    for _ in range(40):writer.write(source)
    writer.release()
    event={"kind":"click","start":.4,"end":.48,"t":.7,
           "evidence":"Verified real DOM change",
           "targetRect":{"x":60,"y":55,"width":28,"height":15},
           "resultRect":{"x":65,"y":40,"width":90,"height":55}}
    manifest={"duration":1.6,"capture_rect":{"width":w,"height":h},
              "events":[event]}
    plan={"stagePreset":"cloud_shadow_v1",
          "camera":[{"at":0,"scale":.8,"center":[.5,.5]},
                    {"at":1.6,"scale":.8,"center":[.5,.5]}],
          "lighting":{"eventIndex":0,"trigger":"verified"},
          "payoff":{"region":"event:0:result","mode":"overview","minVisible":.8}}
    stage=load_studio_stage(plan,manifest,video,(w,h),(640,360),1.6,25)
    result=render_studio_stage(stage,source,0)
    output=(640,360)
    q=stage.quad(0)
    srcpoints=np.float32([[0,0],[w-1,0],[w-1,h-1],[0,h-1]])
    expected=cv2.warpPerspective(source,cv2.getPerspectiveTransform(srcpoints,q),
                                  output,flags=cv2.INTER_CUBIC,
                                  borderMode=cv2.BORDER_CONSTANT)
    m=card_mask((w,h),output)
    np.testing.assert_array_equal(result[m==255],expected[m==255])
    # Acrylic extends beyond the screen but source remains its original
    # RGB colors, including interface contrast and icon edges.
    assert (glass_shell_mask((w,h),output)>card_mask((w,h),output)).any()


def test_shell_geometry_fits_landscape_at_all_supported_sizes():
    for out in ((640,360),(1280,720),(1920,1080)):
        inner=card_mask((2880,1800),out)
        outer=glass_shell_mask((2880,1800),out)
        assert np.any(outer>inner)
        assert outer.shape==inner.shape==(out[1],out[0])
        assert not np.any(outer[0,:]) and not np.any(outer[-1,:])
        assert not np.any(outer[:,0]) and not np.any(outer[:,-1])
