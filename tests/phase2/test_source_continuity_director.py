"""Proof-bound source continuity and automatic direction tests."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import sys

import cv2
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2] / "scripts"))
from source_continuity_scan import (
    unstable_runs, stable_segments, scan_source, runs_of_flags
)
from source_true_director import create_directed_edl, _focus_kind


def make_manifest():
    sw,sh=2640,1440
    rect=lambda x,y,w,h:{"x":x,"y":y,"width":w,"height":h}
    dates=[(2.403,4.0861),(7.3146,8.6332),(11.5519,12.8198)]
    points=[(1.1832,775,340),(2.403,248,366),
            (4.0861,1307,292),(7.3146,248,818),
            (8.6332,1800,760),(11.5519,248,878),
            (12.8198,780,915),(14.0827,1102,955)]
    events=[]
    targets=[rect(200,330,100,80),rect(200,790,100,60),
             rect(200,850,100,60)]
    outcomes=[
        {"evidence":"Real Diff tab and HomeScreen.tsx visible",
         "resultRect":rect(1120,230,1501,1210)},
        {"evidence":"Real workspace changes from code diff to agent task columns",
         "resultRect":rect(620,100,1966,1267)},
        {"evidence":"Real 3,389, 1,128, 729 counters and agent throughput chart",
         "resultRect":rect(620,100,1966,1267),
         "summaryRects":[rect(800,270,520,160),
                         rect(1335,270,530,160),
                         rect(1880,270,510,160)]}
    ]
    for i,(click,change) in enumerate(dates):
        events += [
            {"kind":"click","label":("Reviews","Agent tasks","Agent Insights")[i],
             "semanticGoal":"Inspect verified product behavior",
             "t":click,"targetRect":targets[i]},
            {"kind":"state_change","t":change,**outcomes[i]}
        ]
    return {
        "source":"https://example.test/synthetic",
        "source_kind":"synthetic-unit-test",
        "lead_s":.28,"cursorless":True,
        "capture_rect":rect(0,0,sw,sh),
        "events":events,
        "pointer_samples":[{"t":t,"x":x,"y":y} for t,x,y in points],
        "source_sha256":"synthetic-fixture-hash",
    }


def make_continuity():
    return {"schema":"sauce-source-instability-v1",
            "sourceSha256":"synthetic-fixture-hash",
            "sourceWidth":2640,"sourceHeight":1440,"fps":60,
            "decodedFrames":1110,
            "unstableRanges":[[0,0],[185,257],[484,533],[733,778]],
            "stableSegments":[[2,185],[259,484],[535,733],[780,1110]]}


def test_detects_relative_flash_intervals_without_false_alarm_light_theme():
    white=np.full(300,.004)
    border=np.full(300,.001)
    white[60:110]=.1515
    border[60:110]=.5331
    white[130:170]=.14
    border[130:170]=.50
    white[0]=.14
    border[0]=.50
    assert unstable_runs(white,border)==[[0,0],[60,109],[130,169]]
    light=np.full(300,.96)
    light[:]=.91 # baseline is consistently bright
    assert unstable_runs(light,light)==[]
    with pytest.raises(ValueError):
        unstable_runs(np.array([np.nan]),np.array([.5]))
    assert runs_of_flags(np.array([False,True,True,False,True]))==[]


def test_stable_intervals_are_exclusive_and_frame_guarded():
    ranges=[[0,0],[185,257],[484,533],[733,778]]
    assert stable_segments(1110,ranges)==[[2,185],[259,484],[535,733],[780,1110]]
    with pytest.raises(ValueError):
        stable_segments(1110,[[5,9],[8,12]])
    with pytest.raises(ValueError):
        stable_segments(0,[])


def test_video_scanner_streams_real_frames_with_bounded_receipt(tmp_path):
    video=tmp_path/"dark-ui-source.mp4"
    fourcc=cv2.VideoWriter_fourcc(*"mp4v")
    out=cv2.VideoWriter(str(video),fourcc,60,(640,360))
    assert out.isOpened()
    for i in range(180):
        frame=np.full((360,640,3),(30,28,26),np.uint8)
        frame[40:260,160:600]=(54,59,62)
        if 60<=i<=90:
            frame[:, :160]=(255,255,255)
        out.write(frame)
    out.release()
    info=scan_source(video)
    assert info["decodedFrames"]==180
    assert info["unstableRanges"]==[[60,90]]
    assert info["stableSegments"]==[[0,60],[92,180]]
    assert info["requiresHumanVisualReview"] is True
    with pytest.raises(ValueError,match="SHA256"):
        scan_source(video,expected_sha256="different")


def test_auto_director_builds_four_authentic_phases_without_input_mutation():
    m,r=make_manifest(),make_continuity()
    original=copy.deepcopy((m,r))
    edl,proof=create_directed_edl(m,r)
    assert proof["frames"]==790
    assert proof["creativeApproved"] is False
    assert proof["cursorVisibility"]["offscreenFrames"]==0
    assert proof["cursorVisibility"]["unrecordedOpeningFrames"]==0
    assert edl["autoDirected"]["manualShotSelection"] is False
    assert edl["unstableRanges"]==r["unstableRanges"]
    assert edl["shots"][1]["camera"][1]["anchor"]=="result-upper:0"
    assert edl["shots"][2]["camera"][1]["anchor"]=="result:1"
    assert edl["shots"][3]["camera"][-1]["anchor"]=="overview:2"
    assert (m,r)==original


def test_destination_semantics_beat_previous_code_view():
    assert _focus_kind({"evidence":"Real workspace changes from code diff to agent task columns"})=="board"
    assert _focus_kind({"evidence":"Real code diff in browser"})=="code"
    assert _focus_kind({"evidence":"Chart","summaryRects":[{"x":1},{"x":3}]})=="group"


def test_auto_planner_rejects_missing_acts_outcomes_or_wrong_source():
    m,r=make_manifest(),make_continuity()
    broken=copy.deepcopy(m)
    broken["events"]=[v for v in broken["events"] if v.get("kind")!="click"]
    with pytest.raises(ValueError,match="three verified"):
        create_directed_edl(broken,r)
    broken=copy.deepcopy(m)
    broken["events"][1]["evidence"]=""
    with pytest.raises(ValueError,match="three verified"):
        create_directed_edl(broken,r)
    broken=copy.deepcopy(m)
    broken["events"][0]["targetRect"]["x"]=1600
    with pytest.raises(ValueError,match="hotspot"):
        create_directed_edl(broken,r)
    bad_r=copy.deepcopy(r)
    bad_r["sourceSha256"]="other-hash"
    with pytest.raises(ValueError,match="hashes disagree"):
        create_directed_edl(m,bad_r)


def test_auto_planner_rejects_uncaptured_transitions_or_short_source():
    m,r=make_manifest(),make_continuity()
    bad=copy.deepcopy(r)
    bad["stableSegments"]=[[2,185],[259,484],[535,1110]]
    with pytest.raises(ValueError,match="unknown source continuity"):
        create_directed_edl(m,bad)
    bad=copy.deepcopy(r)
    bad["stableSegments"][1]=[259,320]
    with pytest.raises(ValueError,match="too short"):
        create_directed_edl(m,bad)

from source_continuity_scan import validate_continuity_receipt
from source_verified_whip import whip_phase,camera_whip_dx,film_shutter_whip


def test_source_receipt_verifies_actual_stable_shot_ranges():
    m,r=make_manifest(),make_continuity()
    edit,_=create_directed_edl(m,r)
    assert validate_continuity_receipt(r,source_sha256=m["source_sha256"],
                source_frames=1110,source_size=(2640,1440),edit=edit)
    bad=copy.deepcopy(edit)
    bad["shots"][1]["startFrame"]=257
    with pytest.raises(ValueError,match="unverified unstable"):
        validate_continuity_receipt(r,source_sha256=m["source_sha256"],
                 source_frames=1110,source_size=(2640,1440),edit=bad)
    bad=copy.deepcopy(edit)
    bad["unstableRanges"]=[]
    with pytest.raises(ValueError,match="different instability"):
        validate_continuity_receipt(r,source_sha256=m["source_sha256"],
                 source_frames=1110,source_size=(2640,1440),edit=bad)
    modified=copy.deepcopy(r)
    modified["stableSegments"][1][0]+=1
    with pytest.raises(ValueError,match="modified"):
        validate_continuity_receipt(modified,source_sha256=m["source_sha256"],
                 source_frames=1110,source_size=(2640,1440),edit=edit)


def test_source_whip_has_exact_stable_frames_and_no_cross_source_ghost():
    n=180
    x=np.zeros((360,640,3),np.uint8)
    x[:,:,:]=(12,19,32)
    x[45:220,40:240]=(230,210,175)
    immutable=x.copy()
    for frame in (5,60,170):
        assert whip_phase(frame,n,incoming=True,outgoing=True)==0
    assert whip_phase(0,n,incoming=True,outgoing=False)==-1
    assert whip_phase(n-1,n,incoming=False,outgoing=True)==1
    assert whip_phase(2,n,incoming=True,outgoing=True)<0
    assert whip_phase(n-3,n,incoming=True,outgoing=True)>0
    assert camera_whip_dx(-1,1920)==-60
    assert camera_whip_dx(1,960)==30
    assert film_shutter_whip(x,0) is x
    blurred=film_shutter_whip(x,1)
    assert blurred.shape==x.shape
    assert blurred.dtype==x.dtype
    # A blurred source frame contains only the real source layer, not UI
    # from another page state as the old crossfade incorrectly did.
    assert blurred[10,10].tolist()==[12,19,32]
    assert blurred[130,130].tolist()==[230,210,175]
    assert not np.array_equal(blurred, x)
    np.testing.assert_array_equal(x,immutable)
    with pytest.raises(ValueError):
        film_shutter_whip(x,2)
    with pytest.raises(ValueError):
        whip_phase(0,n,incoming=True,outgoing=False,frames=9)


def test_bounded_auto_render_flags_require_source_proof():
    renderer=(Path(__file__).resolve().parents[2]/
              'scripts/evidence_edl_renderer.py').read_text()
    for flag in ["--source-verified-whip","--continuity-receipt",
                 "--quality-gate","--premium-cursor"]:
        assert flag in renderer
    assert "validate_continuity_receipt(" in renderer
    assert renderer.index("film_shutter_whip(image,phase)") < renderer.index(
        "pointer.paint(image,")
