"""Contract tests for real source pixel UI separation, not creative approval."""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from ui_isolation_layers import load_isolation_composition, render_isolated_stage


@pytest.fixture
def subject(tmp_path):
    path=tmp_path/"capture.mp4"
    writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*"mp4v"),30.0,(320,180))
    assert writer.isOpened()
    for n in range(90):
        frame=np.full((180,320,3),(15,19,23),np.uint8)
        cv2.rectangle(frame,(115,55),(204,95),
                      (15,100,180) if n<35 else (30,210,80),-1)
        writer.write(frame)
    writer.release()
    manifest={"events":[{"t":1.0,"evidence":"Observed actual browser UI update",
                          "targetRect":{"x":25,"y":27,"width":80,"height":20},
                          "resultRect":{"x":115,"y":55,"width":90,"height":40}}]}
    spec={"mode":"isolated-ui","startAt":1.35,"background":[245,244,241],
          "layers":[{"id":"outcome","anchor":"event:0:result",
                      "sourceAt":1.3,"startAt":1.35,"endAt":2.5,
                      "position":[.5,.5],"enterFrom":[.5,.5],
                      "widthFraction":.34,"paddingPx":8,"radiusPx":3,
                      "enterSeconds":.2,"zIndex":1}]}
    return path,manifest,spec


def load(s):
    source,manifest,raw=s
    return load_isolation_composition(raw,manifest,source,(320,180),3.0)


def test_real_frame_isolated_and_unmodified_inside_matting(subject):
    spec=load(subject)
    assert not spec.active(.95)
    assert render_isolated_stage(spec,1.0,(640,360)) is None
    assert spec.active(1.6)
    output=render_isolated_stage(spec,1.7,(640,360))
    assert output.shape==(360,640,3)
    assert np.array_equal(output[0,0],np.array([241,244,245],np.uint8))
    layer=spec.layers[0]
    assert layer.source_bounds==(107,47,213,103)
    assert np.mean(layer.crop[8:48,8:98,1])>150  # real post-action content
    assert not np.all(output[180,320]==output[0,0])


def test_reject_result_before_observed_change(subject):
    source,manifest,raw=subject
    raw["layers"][0]["sourceAt"]=.4
    with pytest.raises(ValueError,match="before it exists"):
        load(subject)


def test_reject_future_frame_reveal(subject):
    source,manifest,raw=subject
    raw["layers"][0]["sourceAt"]=1.8
    with pytest.raises(ValueError,match="future UI state"):
        load(subject)


def test_reject_unverified_event(subject):
    source,manifest,raw=subject
    manifest["events"][0]["evidence"]=""
    with pytest.raises(ValueError,match="genuine verified outcome"):
        load(subject)


def test_reject_unknown_effect(subject):
    source,manifest,raw=subject
    raw["layers"][0]["ai_synthesize_missing_pixels"]=True
    with pytest.raises(ValueError,match="Invalid UI layer fields"):
        load(subject)


def test_reject_duplicate_layer_id(subject):
    source,manifest,raw=subject
    raw["layers"].append(dict(raw["layers"][0]))
    with pytest.raises(ValueError,match="unique and simple"):
        load(subject)


def test_reject_absurd_source_crop(subject):
    source,manifest,raw=subject
    manifest["events"][0]["resultRect"]["x"]=300
    with pytest.raises(ValueError,match="outside verified source"):
        load(subject)


def test_reject_off_stage_placement(subject):
    source,manifest,raw=subject
    raw["layers"][0]["position"]=[0.0,0.0]
    raw["layers"][0]["enterFrom"]=[0.0,0.0]
    plan=load(subject)
    with pytest.raises(ValueError,match="safe margins"):
        render_isolated_stage(plan,1.6,(640,360))


def test_reject_layer_count_overflow(subject):
    source,manifest,raw=subject
    raw["layers"]*=7
    with pytest.raises(ValueError,match="1..6"):
        load(subject)


def test_original_source_cursor_reappears_when_isolation_ends(subject):
    spec=load(subject)
    assert render_isolated_stage(spec,2.9,(640,360)) is None


def test_complete_component_region_is_used_without_heuristic_padding(subject):
    source, manifest, raw = subject
    manifest["events"][0]["componentRect"]={
        "x":108,"y":20,"width":106,"height":120}
    layer=raw["layers"][0]
    layer["anchor"]="event:0:component"
    layer["paddingPx"]=0
    plan=load(subject)
    assert plan.layers[0].source_bounds==(108,20,214,140)
    assert plan.layers[0].anchor=="event:0:component"


def test_missing_component_does_not_fallback_to_changed_price_text(subject):
    source,manifest,raw=subject
    raw["layers"][0]["anchor"]="event:0:component"
    with pytest.raises(ValueError,match="Missing verified source rectangle"):
        load(subject)


def test_reject_partial_component_outside_recorded_frame(subject):
    source,manifest,raw=subject
    raw["layers"][0]["anchor"]="event:0:component"
    manifest["events"][0]["componentRect"]={
        "x":108,"y":20,"width":106,"height":181}
    with pytest.raises(ValueError,match="outside verified source pixels"):
        load(subject)


def test_complete_component_must_not_appear_before_actual_event(subject):
    source,manifest,raw=subject
    raw["layers"][0]["anchor"]="event:0:component"
    raw["layers"][0]["sourceAt"]=.4
    manifest["events"][0]["componentRect"]={
        "x":108,"y":20,"width":106,"height":120}
    with pytest.raises(ValueError,match="before it exists"):
        load(subject)
