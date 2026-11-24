"""Proof-bound customer modal transitions after a genuine source trim."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

from scripts.quality_preview_supervisor import analyze, _source_event_windows


def _write_video(path: Path, pixels: list[np.ndarray], fps=10):
    writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*"mp4v"),
                           fps,(192,108))
    assert writer.isOpened()
    try:
        for frame in pixels:
            writer.write(frame)
    finally:
        writer.release()


def _sample(value):
    img=np.full((108,192,3),value,dtype=np.uint8)
    # A source-observed panel changing background shade, not fake UI.
    cv2.rectangle(img,(35,18),(157,93),(value//2,)*3,-1)
    return img


def _sidecar(source, event=True):
    action=[
        {"kind":"click","t":1.62,"label":"Open dialog",
         "semanticGoal":"Observe real dialog"},
        {"kind":"state_change","t":2.05,"evidence":"Real visible dialog",
         "resultRect":{"x":35,"y":18,"width":122,"height":75}},
    ] if event else []
    return {"editorial_events":action,"continuous_recording":True,
            "source_url":"https://example.com/","sha256":_sha(source)}


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_aligned_source_ui_transition_is_not_an_editorial_jump(tmp_path):
    # Original sample changes at 1.8s. The movie trims the first second
    # and therefore changes at 0.8s. Pixel/evidence must independently match.
    source_frames=[_sample(38 if i<18 else 225) for i in range(40)]
    src=tmp_path/"original.mp4"
    film=tmp_path/"film.mp4"
    sidecar=tmp_path/"manifest.json"
    _write_video(src,source_frames)
    _write_video(film,source_frames[10:35])
    sidecar.write_text(json.dumps(_sidecar(src)))
    ev={"source_path":str(src),"source_sha256":_sha(src),
        "event_manifest_path":str(sidecar),
        "event_manifest_sha256":_sha(sidecar),
        "source_trim_seconds":1.0}
    result=analyze(film,ev,seconds=2.5)
    codes={v["code"] for v in result["findings"]}
    assert "ABRUPT_CUT_CANDIDATE" not in codes
    assert result["sourceRelativeRealUiTransitions"]
    assert abs(result["sourceRelativeRealUiTransitions"][0]["actualSourceTime"]-1.8)<.11
    assert "NO_AUDIO_STREAM" in codes
    assert result["verdict"]=="REJECT"

    # Without exact event evidence, a similar-looking clip has no
    # authorization to suppress an abrupt edit.
    sidecar.write_text(json.dumps(_sidecar(src,event=False)))
    ev["event_manifest_sha256"]=_sha(sidecar)
    no_event=analyze(film,ev,seconds=2.5)
    assert "ABRUPT_CUT_CANDIDATE" in {v["code"] for v in no_event["findings"]}


def test_unsupported_source_cuts_and_missing_clicks_never_count_as_product_change():
    good={"editorial_events":[
        {"kind":"click","t":4.2,"semanticGoal":"Open observed dialog"},
        {"kind":"state_change","t":5.1,"evidence":"Real dialog",
         "resultRect":{"x":1,"y":1,"width":100,"height":100}}]}
    assert _source_event_windows(good)==[(4.05,5.3)]
    assert _source_event_windows({"editorial_events":[
        {"kind":"click","t":4.2,"semanticGoal":"Open observed dialog"},
        {"kind":"state_change","t":5.1,"evidence":"Real dialog"}]})==[]
    assert _source_event_windows({"editorial_events":[
        {"kind":"state_change","t":5.1,"evidence":"Real dialog",
         "resultRect":{"x":1,"y":1,"width":100,"height":100}}]})==[]
    assert _source_event_windows({"editorial_events":[
        {"kind":"click","t":4.2,"semanticGoal":"Click"},
        {"kind":"state_change","t":6.4,"evidence":"Late unrelated change",
         "resultRect":{"x":1,"y":1,"width":100,"height":100}}]})==[]
