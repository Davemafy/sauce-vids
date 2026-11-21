"""Single-call experiment source-trim provenance and exact 60fps clock guards."""
import hashlib
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from source_action_clip_preprocess import choose_windows,remap_manifest,verified_input,produce
from foley_mixer import render_foley_plan


def _raw():
    events=[]
    for start,result in [(3.0,4.2),(6.8,8.0),(9.8,11.0)]:
        events.append({
          "kind":"slider_change","start":start,"t":result,"end":result,
          "evidence":"Original Chromium action and independently observed UI result",
          "targetRect":{"x":20,"y":15,"width":100,"height":10},
          "resultRect":{"x":35,"y":55,"width":75,"height":30}})
    samples=[{"t":round(i*.04+.01,5),"x":60.,"y":20.}
             for i in range(395)]
    return {"source":"https://example.com/pricing",
      "duration":16.0,"cursorless":True,
      "capture_rect":{"width":160,"height":90},
      "events":events,"pointer_samples":samples}


def test_windows_preserve_three_real_result_intervals_but_remove_idle():
    raw=_raw()
    windows=choose_windows(raw["events"],60,960)
    assert windows[0][0]>0
    assert sum(b-a for a,b in windows)<960
    for event in raw["events"]:
        assert any(a/60<=event["start"] and event["t"]<b/60
                   for a,b in windows)
    edited,spans=remap_manifest(raw,windows,60)
    assert len(edited["events"])==3
    assert len(edited["pointer_samples"])<len(raw["pointer_samples"])
    assert all(b["t"]>a["t"] for a,b in zip(
        edited["pointer_samples"],edited["pointer_samples"][1:]))
    assert [event["kind"] for event in edited["events"]]==["slider_change"]*3
    assert [event["resultRect"] for event in edited["events"]]==[
        event["resultRect"] for event in raw["events"]]
    assert edited["duration"]==sum(s["frames"] for s in spans)/60
    assert edited["events"][0]["start"]>=.7
    assert raw["events"][0]["start"]==3.0


def test_bad_source_hash_or_cursor_trace_refused_before_edition(tmp_path):
    src=tmp_path/"source.mp4";src.write_bytes(b"original video")
    man=tmp_path/"manifest.json";man.write_text(json.dumps(_raw()))
    with pytest.raises(ValueError,match="hash mismatch"):
        verified_input(src,man,"0"*64,hashlib.sha256(man.read_bytes()).hexdigest())
    with pytest.raises(ValueError,match="hash mismatch"):
        verified_input(src,man,hashlib.sha256(src.read_bytes()).hexdigest(),"f"*64)
    raw=_raw();raw["pointer_samples"]=[]
    with pytest.raises(ValueError,match="recorded real cursor"):
        remap_manifest(raw,[(0,960)],60)


def test_noninteger_millisecond_60fps_duration_preserves_audio_sample_clock(tmp_path):
    seconds=613/60
    sample_count=613*800
    plan={"schema":"sauce-foley-plan-v1","sampleRate":48000,
          "durationMs":seconds*1000,"masterGain":.2,"musicGain":0,
          "muted":False,"duckIntervals":[],
          "cues":[{"sound":"click_crisp","outputSample":48000,
                   "outputMs":1000,"gain":.25}]}
    receipt=render_foley_plan(plan,tmp_path/"foley.wav",
                              target_duration_ms=seconds*1000)
    import wave
    with wave.open(str(tmp_path/"foley.wav")) as sound:
        assert sound.getnframes()==sample_count
        assert sound.getframerate()==48000
    assert receipt is not None
    plan["durationMs"]=round(seconds*1000)
    with pytest.raises(ValueError,match="Audio cannot end"):
        render_foley_plan(plan,tmp_path/"rejected.wav",
                          target_duration_ms=seconds*1000)


def test_output_is_real_frames_rebased_and_cannot_be_overwritten(tmp_path):
    src=tmp_path/"real.mp4"
    writer=cv2.VideoWriter(str(src),cv2.VideoWriter_fourcc(*"mp4v"),
                           60,(160,90))
    assert writer.isOpened()
    for i in range(540):
        frame=np.full((90,160,3),38,np.uint8)
        if i>=100:frame[55:85,35:110]=(50,180,140)
        if i>=280:frame[55:85,35:110]=(50,70,180)
        writer.write(frame)
    writer.release()
    raw=_raw()
    raw["duration"]=9.
    raw["events"]=raw["events"][:2]
    raw["events"][0].update({"start":1.6,"t":2.1,"end":2.1})
    raw["events"][1].update({"start":4.4,"t":4.9,"end":4.9})
    raw["pointer_samples"]=[p for p in raw["pointer_samples"] if p["t"]<9]
    manifest=tmp_path/"manifest.json";manifest.write_text(json.dumps(raw))
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    receipt=produce(src,manifest,tmp_path/"out",sha(src),sha(manifest))
    assert receipt["originalSourceSha256"]==sha(src)
    assert receipt["protectedEvents"]==2
    assert receipt["outputFrameCount"]<540
    assert receipt["sourceType"]=="EDITED_AUTHENTIC_FRAMES_NOT_CONTINUOUS_BROWSER_RECORDING"
    assert sha(src)==receipt["originalSourceSha256"]
    new=json.loads((tmp_path/"out"/"rebased-verified-events.json").read_text())
    assert new["duration"]==receipt["outputFrameCount"]/60
    assert len(new["events"])==2
    assert new["events"][0]["t"]<new["events"][1]["start"]
    with pytest.raises(ValueError,match="Refuse overwriting"):
        produce(src,manifest,tmp_path/"out",sha(src),sha(manifest))
