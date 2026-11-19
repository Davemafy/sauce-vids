"""Real DOM geometry and camera projections veto unreadable opening subjects."""
import copy
import math
from pathlib import Path
import sys

import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts"))
from quality_preview_supervisor import verified_focal_geometry, verified_focal_sequence



def fixture(source_rect=None,zoom=1.73):
    s=(938./1800.)*zoom
    camera=[[s,0.,960.-s*955.],[0.,s,540.-s*955.]]
    return dict(source_rect=source_rect or [730.,740.,450.,430.],
                source_size=[2880,1800],
                camera_matrix=camera,
                stage_window=[210,71,1500,938])


def issues(result):
    return {i["code"] for i in result}


def test_rejects_small_verified_source_object_even_if_in_frame():
    evidence=fixture()
    report=verified_focal_geometry(evidence,(1920,1080))
    assert issues(report)=={"SMALL_VERIFIED_PRIMARY_SUBJECT"}
    assert report[0]["detail"]["fraction_of_output"]<.08


def test_accepts_larger_legitimate_focal_geometry():
    evidence=fixture([730.,740.,600.,500.])
    assert verified_focal_geometry(evidence,(1920,1080))==[]


def test_rejects_partially_visible_but_important_source_text():
    evidence=fixture([730.,740.,600.,500.])
    evidence["protected_text"]=[dict(text="Pricing",rect=[0,750,600,45])]
    report=verified_focal_geometry(evidence,(1920,1080))
    assert "PARTIALLY_CROPPED_SOURCE_TEXT" in issues(report)
    assert report[0]["detail"]["text"]=="Pricing"


def test_completely_offstage_focal_element_fails():
    evidence=fixture([2500.,1620.,350.,160.])
    report=verified_focal_geometry(evidence,(1920,1080))
    assert "SMALL_VERIFIED_PRIMARY_SUBJECT" in issues(report)
    assert "FOCAL_TARGET_CLIPPED" in issues(report)


@pytest.mark.parametrize("mod",[
    lambda p:p.update(source_rect=[1,2,3]),
    lambda p:p.update(source_rect=[-1,2,30,30]),
    lambda p:p.update(source_rect=[2800,1700,200,200]),
    lambda p:p.update(camera_matrix=[[1,0,0]]),
    lambda p:p.update(camera_matrix=[[float("nan"),0,0],[0,1,0]]),
    lambda p:p.update(stage_window=[100,100,3000,2000]),
    lambda p:p.update(protected_text=[{"text":"oops","rect":[1,2,3]}]),
])
def test_invalid_or_unverified_camera_geometry_fails_closed(mod):
    data=fixture()
    mod(data)
    with pytest.raises(ValueError):
        verified_focal_geometry(data,(1920,1080))


def test_protect_fully_visible_text_does_not_raise_false_clip():
    evidence=fixture([730.,740.,600.,500.])
    evidence["protected_text"]=[dict(text="Capturing",rect=[800,810,180,42])]
    assert verified_focal_geometry(evidence,(1920,1080))==[]


def test_outside_window_camera_matrix_rejects_focal_content():
    evidence=fixture([730.,740.,600.,500.])
    evidence["camera_matrix"]=[[.5,0,-2000],[0,.5,-2000]]
    findings=verified_focal_geometry(evidence,(1920,1080))
    assert {"SMALL_VERIFIED_PRIMARY_SUBJECT","FOCAL_TARGET_CLIPPED"}<=issues(findings)


def test_full_camera_sequence_cannot_hide_midshot_text_crop():
    sample=fixture([730.,740.,600.,500.])
    sample["protected_text"]=[dict(text="Pricing",rect=[0,750,600,45])]
    first=[[.52,0.,260.],[0.,.52,60.]]
    # Frames 0 and 2 are wide enough; frame 1 has a real zoom crop.
    sequence={
       "base":{k:v for k,v in sample.items() if k!="camera_matrix"},
       "frames":[
          {"frame":0,"camera_matrix":first},
          {"frame":1,"camera_matrix":sample["camera_matrix"]},
          {"frame":2,"camera_matrix":first}]}
    findings=verified_focal_sequence(sequence,(1920,1080))
    assert any(f["code"]=="PARTIALLY_CROPPED_SOURCE_TEXT"
               and f["detail"]["affected_frames"]==1
               and f["detail"]["first_frame"]==1 for f in findings)


def test_camera_sequence_requires_contiguous_evidence():
    payload={
        "base":{k:v for k,v in fixture().items() if k!="camera_matrix"},
        "frames":[{"frame":0,"camera_matrix":fixture()["camera_matrix"]},
                  {"frame":2,"camera_matrix":fixture()["camera_matrix"]}]}
    with pytest.raises(ValueError,match="contiguous"):
        verified_focal_sequence(payload,(1920,1080))
    payload["frames"]=[]
    with pytest.raises(ValueError):
        verified_focal_sequence(payload,(1920,1080))


def test_critical_verified_text_that_is_tiny_on_phone_is_rejected():
    item=fixture([730.,740.,600.,500.])
    item["protected_text"]=[
        {"text":"Publish","rect":[800,810,190,44],"source_font_px":17}]
    findings=verified_focal_geometry(item,(1920,1080))
    assert "UNREADABLE_CRITICAL_TEXT_AT_390PX" in issues(findings)
    assert not any(f["code"]=="PARTIALLY_CROPPED_SOURCE_TEXT" for f in findings)


def test_critical_large_text_on_phone_is_not_rejected():
    item=fixture([730.,740.,600.,500.])
    item["protected_text"]=[
        {"text":"Publish","rect":[800,810,190,44],"source_font_px":65}]
    assert verified_focal_geometry(item,(1920,1080))==[]


def test_time_scoped_text_only_rejects_frames_where_real_text_exists():
    source=fixture([730.,740.,600.,500.])
    source["protected_text"]=[
        dict(text="Pricing",rect=[0,750,600,45],start_frame=2,end_frame=3)]
    frames=[{"frame":i,"camera_matrix":source["camera_matrix"]} for i in range(4)]
    findings=verified_focal_sequence(
       {"base":{k:v for k,v in source.items() if k!="camera_matrix"},
        "frames":frames},(1920,1080))
    assert any(f["code"]=="PARTIALLY_CROPPED_SOURCE_TEXT"
               and f["detail"]["affected_frames"]==1
               and f["detail"]["first_frame"]==2 for f in findings)


@pytest.mark.parametrize("start,end",[(2,1),(-1,2),(0,15),(1.0,2),("1",2)])
def test_invalid_text_visibility_timestamps_rejected(start,end):
    data=fixture([730.,740.,600.,500.])
    data["protected_text"]=[
        dict(text="Pricing",rect=[0,750,600,45],
             start_frame=start,end_frame=end)]
    payload={
      "base":{k:v for k,v in data.items() if k!="camera_matrix"},
      "frames":[{"frame":i,"camera_matrix":data["camera_matrix"]}
                for i in range(4)]}
    with pytest.raises(ValueError,match="visibility"):
        verified_focal_sequence(payload,(1920,1080))
