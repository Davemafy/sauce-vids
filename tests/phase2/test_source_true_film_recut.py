"""Source-true beat cuts: never replace original browser frames or fake events."""
from pathlib import Path
import sys,json
import numpy as np
import cv2
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from source_true_film_recut import _filter,compile_timeline,verify_lineage,run


def test_native_frame_audio_cut_filter_matches_60hz_48khz():
    graph=_filter([{"startFrame":0,"endFrame":42},
                   {"startFrame":108,"endFrame":270}])
    assert "[0:v]trim=start_frame=0:end_frame=42" in graph
    assert "[0:a]atrim=start_sample=86400:end_sample=216000" in graph
    assert "concat=n=2:v=1:a=1" in graph


def test_real_ts_beat_lock_compiles_only_original_action_and_result(tmp_path):
    m=tmp_path/"manifest.json"
    m.write_text(json.dumps({"duration":12,"events":[
        {"start":2.189694,"end":2.310422,"t":3.181067,
         "evidence":"actual verified Chromium browser state change"},
        {"start":6.230606,"end":6.334683,"t":7.444369,
         "evidence":"actual contrast matrix observed in source"}]}))
    out=compile_timeline(m)
    assert out["schema"]=="sauce-source-true-recut-v1"
    assert out["outputFrameCount"]==380
    assert out["cutsOutputFrames"]==[42,204]
    assert out["events"][0]["sourceResultFrame"]==191
    assert out["events"][1]["outputPressFrame"]==228
    bad=tmp_path/"bad.json"
    bad.write_text(json.dumps({"duration":12,"events":[{"t":3,"start":2}]}))
    with pytest.raises(ValueError,match="source timeline rejected"):
        compile_timeline(bad)


def _write(path,offset=0):
    codec=cv2.VideoWriter_fourcc(*"mp4v")
    writer=cv2.VideoWriter(str(path),codec,60,(320,180))
    assert writer.isOpened()
    for i in range(90):
        v=(i*3+offset)%255
        frame=np.full((180,320,3),[v,v//2,180],np.uint8)
        frame[20:70,80:190]=(15,210,20)
        writer.write(frame)
    writer.release()


def test_recut_preserves_actual_frame_lineage_and_refuses_reordered_frames(tmp_path):
    original=tmp_path/"source.mp4";_write(original)
    # Same original frames, no reencoding: a proof of exact source-index map.
    r=verify_lineage(original,original,
        [{"startFrame":0,"endFrame":90,"outputStartFrame":0}],
        [{"outputPressFrame":12,"outputResultFrame":40}],90)
    assert r["sampledOutputFrames"]>15
    assert r["maxDownscaledGrayMAE"]<.01
    with pytest.raises(ValueError,match="duplicated or reordered"):
        verify_lineage(original,original,[
            {"startFrame":20,"endFrame":40,"outputStartFrame":0},
            {"startFrame":10,"endFrame":30,"outputStartFrame":20}
        ],[],40)


def test_recut_refuses_missing_or_overwritten_evidence(tmp_path):
    files=[tmp_path/n for n in ("source.mp4","manifest.json","master.mp4",
                               "source.receipt.json","film.plan.json")]
    for f in files:f.write_bytes(b"synthetic test fixture only")
    out=tmp_path/"future.mp4"
    with pytest.raises(Exception):
        run(*files,out,tmp_path/"future.receipt.json")
    assert not out.exists()
    out.write_bytes(b"valuable previous work")
    with pytest.raises(ValueError,match="No overwrite"):
        run(*files,out,tmp_path/"future.receipt.json")
    assert out.read_bytes()==b"valuable previous work"
