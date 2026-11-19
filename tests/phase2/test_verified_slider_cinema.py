"""Bounded real-source DPR2 slider capture and director regression."""
import copy
from pathlib import Path
import json
import sys

import cv2
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts"))
import verified_slider_cinema as film
from verified_slider_cinema import Director, smooth
from capture_verified_slider_dpr2 import validate_public_url


def synthetic_manifest():
    price_rect=lambda x:dict(x=x,y=1158,width=498,height=122)
    slider=dict(x=758,y=731.5,width=1344,height=40)
    events=[dict(kind="pointer_approach",label="Pro change",t=1.35)]
    changes=[
        (3.01,4.09,4.27,"Pro change",926,0.25,"$35 / mo",870),
        (6.85,7.84,8.03,"Scale first change",1094,.375,"$160 / mo",1492),
        (9.85,10.86,11.02,"Scale second change",1262,.5,"$350 / mo",1492)]
    for a,b,c,label,x,value,price,rx in changes:
        events.extend([dict(kind="pointerdown",label=label,t=a,
                            pointer=dict(x=x,y=752),targetRect=slider),
                       dict(kind="pointerup",label=label,t=b),
                       dict(kind="verified_result",label=label,t=c,
                            rangeValue=value,price=price,
                            evidence="Actual browser DOM result",
                            resultRect=price_rect(rx))])
    pointer=[]
    for ti in np.arange(0,16,.10):
        if ti<1.35:
            x,y=2100.,1400.
        elif ti<3.01:
            u=smooth((ti-1.35)/(3.01-1.35))
            x=2100+(926-2100)*u;y=1400+(752-1400)*u
        elif ti<4.09:
            u=smooth((ti-3.01)/(4.09-3.01))
            x=926+168*u;y=752
        elif ti<6.85:
            x,y=1094.,752.
        elif ti<7.84:
            x=1094+168*smooth((ti-6.85)/.99);y=752
        elif ti<9.85:
            x,y=1262.,752.
        elif ti<10.86:
            x=1262+168*smooth((ti-9.85)/1.01);y=752
        elif ti<12.30:
            x,y=1430.,752.
        elif ti<13.3:
            u=smooth((ti-12.3)/1.0)
            x=1430+(2250-1430)*u;y=752+(1250-752)*u
        else:
            x,y=2250.,1250.
        pointer.append(dict(t=round(float(ti),4),x=float(x),y=float(y)))
    return dict(source_sha256="synthetic-not-real",source="https://example.com/",
                slider=dict(controlRect=slider,initialValue=.125),
                events=events,pointer_samples=pointer,cursorless=True)


def synthetic_proof():
    return dict(schema="sauce-native-dpr2-slider-proof-v1",
                sourceSha256="synthetic-not-real",
                frames=960,width=2880,height=1800,
                sourceFrameToBrowserClockOffsetFrames=5,
                nativeThumbTransitionFrames=3)


def make_director(monkeypatch):
    monkeypatch.setattr(film,"sha_file",lambda path:"synthetic-not-real")
    return Director(synthetic_manifest(),synthetic_proof(),
                    Path("/not-a-video-used-in-unit-test"))


def test_source_true_film_duration_and_first_motion(monkeypatch):
    d=make_director(monkeypatch)
    assert d.frame_count==900
    assert 20<=d.source_trim<=60
    assert d.source_trim+d.frame_count<=960
    assert d.keys[0].label=="recognize real product"
    assert d.keys[-1].frame==899
    assert len(d.keys)>=12
    assert d.keys[1].frame>=0
    assert d.keys[2].frame>d.keys[1].frame
    assert d.qa["offscreenFrames"]==0
    assert d.qa["recordedInputNeverRepositioned"] is True


def test_camera_motion_has_held_broad_shot_and_valid_changes(monkeypatch):
    d=make_director(monkeypatch)
    for f in [0,d.keys[1].frame,d.keys[3].frame,d.keys[5].frame,
              d.keys[9].frame,899]:
        matrix=d.camera(None,None,f,None,None)
        assert matrix.shape==(2,3)
        assert np.isfinite(matrix).all()
        assert matrix[0,0]==pytest.approx(matrix[1,1])
    left=d.pose(0)
    wide=d.pose(899)
    assert left[0]<1.0 and wide[0]<1.03
    assert d.pose(d.keys[4].frame)[0]>d.pose(d.keys[3].frame)[0]
    # Frames in the held portion must be literally identical affine poses.
    assert d.pose(0)==d.pose(d.keys[1].frame)
    assert d.pose(d.keys[4].frame)==d.pose(d.keys[5].frame)


def test_result_center_uses_real_click_and_dom_geometry(monkeypatch):
    d=make_director(monkeypatch)
    for i in range(3):
        x,y=d.focus(i)
        target=d.down[i]["pointer"]
        bbox=d.results[i]["resultRect"]
        rx=bbox["x"]+bbox["width"]/2.
        assert min(target["x"],rx)<=x<=max(target["x"],rx)
        assert y>target["y"]


def test_rejects_wrong_action_result_or_damaged_provenance(monkeypatch):
    monkeypatch.setattr(film,"sha_file",lambda path:"synthetic-not-real")
    m,p=synthetic_manifest(),synthetic_proof()
    p["sourceSha256"]="unrelated"
    with pytest.raises(ValueError,match="does not match"):
        Director(m,p,Path("/empty"))
    p=synthetic_proof()
    m["events"][6]["label"]="unpaired destination"
    with pytest.raises(ValueError,match="labels do not pair"):
        Director(m,p,Path("/empty"))
    m=synthetic_manifest()
    m["events"]=[e for e in m["events"] if e["kind"]!="verified_result"]
    with pytest.raises(ValueError,match="three genuine"):
        Director(m,p,Path("/empty"))
    m=synthetic_manifest()
    p["width"]=1600
    with pytest.raises(ValueError,match="native browser"):
        Director(m,p,Path("/empty"))


def test_no_artificial_source_region_pixels_when_effects_off(monkeypatch):
    d=make_director(monkeypatch)
    source=np.zeros((1800,2880,3),np.uint8)
    source[:,:]=(25,29,42)
    source[800:1250,900:1700]=(46,81,139)
    source_copy=source.copy()
    result=d.render_frame(source,0,shutter=False,ripple=False,cursor=False)
    matrix=d.camera(None,None,0,None,None)
    from floating_ui_stage import composite_stage
    original=cv2.warpAffine(source,matrix,(1920,1080),
                            flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
    expected=composite_stage(original,matrix,(2880,1800))
    np.testing.assert_array_equal(result,expected)
    np.testing.assert_array_equal(source,source_copy)


def test_public_site_guard_rejects_local_private_targets():
    for url in ["http://resend.com/pricing","https://localhost/x",
                "https://127.0.0.1/", "https://10.0.0.12",
                "https://192.168.1.4/","file:///etc/passwd",
                "https://user:pass@resend.com/","https://dashboard.internal"]:
        with pytest.raises(ValueError):
            validate_public_url(url)
    assert validate_public_url("https://resend.com/pricing")=="resend.com"


def test_capture_fixture_has_three_real_verification_targets():
    fixture=json.loads((ROOT/"tests/fixtures/resend-pricing-dpr2-15s.json").read_text())
    assert len(fixture["actions"])==3
    assert fixture["rawSeconds"]==16
    assert [a["expectedPrice"] for a in fixture["actions"]]==[
        "$35 / mo","$160 / mo","$350 / mo"]
    assert [a["expectedValue"] for a in fixture["actions"]]==[.25,.375,.5]
    for a in fixture["actions"]:
        assert 0<a["approachStart"]<a["dragStart"]<14
        assert a["dragStart"]+a["dragDuration"]<fixture["rawSeconds"]


def test_reference_motion_eases_exactly_to_hold():
    assert smooth(-1)==0 and smooth(0)==0
    assert smooth(.5)==pytest.approx(.5)
    assert smooth(1)==1 and smooth(2)==1
    h=.0001
    assert abs((smooth(h)-smooth(0))/h)<.001
    assert abs((smooth(1)-smooth(1-h))/h)<.001
