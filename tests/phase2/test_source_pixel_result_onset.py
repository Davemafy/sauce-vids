"""Source pixel change evidence and bounded autonomous result-cut recovery."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

import cv2
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from spatial_studio_stage import detect_appearance_onset
from studio_plan_bounded_repair import normalize_generated_studio_plan


@pytest.fixture()
def change_video(tmp_path):
    def generate(*,before_action=False,transient=False):
        video=tmp_path/("before.mp4" if before_action else
                        "transient.mp4" if transient else "genuine.mp4")
        out=cv2.VideoWriter(str(video),cv2.VideoWriter_fourcc(*"mp4v"),25,(320,180))
        assert out.isOpened()
        for i in range(50):
            frame=np.full((180,320,3),70,np.uint8)
            apply=(i>=18 if before_action else 21<=i<=24 if transient else i>=21)
            if apply:
                # Genuine thin-ish neutral-gray result: NO saturation increase.
                cv2.rectangle(frame,(125,45),(203,71),(235,235,235),-1)
            out.write(frame)
        out.release()
        return video
    event={
      "kind":"theme_change","start":.8,"end":.84,"t":1.4,
      "evidence":"genuine event used to test source pixel timing",
      "targetRect":{"x":12,"y":22,"width":60,"height":20},
      "resultRect":{"x":110,"y":35,"width":160,"height":110},
      "componentRect":{"x":110,"y":35,"width":160,"height":110}}
    manifest={
      "cursorless":True,"duration":2.0,"capture_rect":{"width":320,"height":180},
      "events":[event]}
    return generate,manifest


def test_persistent_neutral_pixel_change_has_native_source_onset(change_video):
    generate,m=change_video
    video=generate()
    info=detect_appearance_onset(video,(320,180),m["events"][0],25)
    assert info["method"]=="sustained-source-pixel-change"
    assert info["candidateFrame"]==21
    assert abs(info["time"]-.84)<1e-8
    assert info["changedFraction"]>=.075
    assert info["overlapWithConfirmedChange"]>.72
    assert info["confirmedSaturationFraction"]==0.


def test_temporary_or_preclick_change_does_not_count_as_result(change_video):
    generate,m=change_video
    early=detect_appearance_onset(generate(before_action=True),(320,180),
                                  m["events"][0],25)
    transient=detect_appearance_onset(generate(transient=True),(320,180),
                                      m["events"][0],25)
    assert early["method"]=="verified-event-time"
    assert transient["method"]=="verified-event-time"
    assert early["time"]==transient["time"]==1.4


def test_bounded_result_cut_shifts_source_frame_and_aligns_light(change_video):
    generate,m=change_video
    video=generate()
    source_sha=hashlib.sha256(video.read_bytes()).hexdigest()
    p={
       "sourceSha256":source_sha,"durationSeconds":2.0,
       "presentation":"fullscreen","cursor":"none",
       "studioStage":{
         "camera":[
           {"at":0,"scale":.8,"center":[.5,.5]},
           {"at":.8,"startAt":.8,"scale":1.0,
            "focus":"event:0:result","cut":True},
           {"at":2.0,"scale":.78,"center":[.5,.5]}],
         "lighting":{"eventIndex":0,"trigger":"verified"},
         "payoff":{"mode":"detail","region":"event:0:result"}
       }}
    original=json.loads(json.dumps(p))
    updated,receipt=normalize_generated_studio_plan(
       p,manifest=m,source_path=video,source_size=(320,180),fps=25,
       output_size=(640,360))
    assert p==original
    assert updated["studioStage"]["camera"][1]["at"]==.84
    assert updated["studioStage"]["camera"][1]["startAt"]==.84
    assert updated["studioStage"]["lighting"]["trigger"]=="appearance"
    assert len(receipt["changes"])==2
    assert receipt["changes"][1]["nativeFrame"]==21
    assert updated["studioStage"]["camera"][0]==original["studioStage"]["camera"][0]
    assert updated["studioStage"]["camera"][2]==original["studioStage"]["camera"][2]
    unsafe=json.loads(json.dumps(p))
    unsafe["studioStage"]["camera"][1].update(at=.56,startAt=.56)
    unchanged,record=normalize_generated_studio_plan(
        unsafe,manifest=m,source_path=video,source_size=(320,180),fps=25,
        output_size=(640,360))
    assert unchanged["studioStage"]["camera"][1]["at"]==.56
    assert not record["changes"]


def test_source_delay_never_retargets_different_event_or_invents_result(change_video):
    generate,m=change_video
    src=generate(transient=True)
    p={"studioStage":{"camera":[
        {"at":0,"scale":.8},{"at":.8,"startAt":.8,"cut":True,
         "focus":"event:0:result","scale":1},
        {"at":2,"scale":.8}],"lighting":{"eventIndex":0,"trigger":"verified"}}}
    after,receipt=normalize_generated_studio_plan(
       p,manifest=m,source_path=src,source_size=(320,180),fps=25)
    assert after["studioStage"]["camera"][1]["at"]==.8
    assert after["studioStage"]["lighting"]["trigger"]=="verified"
    assert not receipt["changes"]
