"""Source-timed JSON reading holds must be measured, not narrated by a model."""
from pathlib import Path
import sys
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from studio_result_hold_audit import inspect_result_holds


class Stage:
    source_size=(320,180)
    output_size=(640,360)
    duration=3.

    def __init__(self,move=False,shrink=False,cut=False):
        self.move=move
        self.shrink=shrink
        self.cut=cut

    def quad(self,t):
        scale=1. if self.shrink else 2.
        delta=round(720*t) if self.move else 0.
        return np.float32([[delta,0],[delta+320*scale,0],
                           [delta+320*scale,180*scale],[delta,180*scale]])

    def source_aligned_cuts(self,fps,trim_frames=0):
        return (90,) if self.cut else ()

    def region_visibility(self,t,rect):
        return 1.


def manifest():
    return {"events":[
      {"t":.5,"evidence":"original observed DOM change",
       "resultRect":{"x":20,"y":20,"width":190,"height":38}},
      {"t":2.,"evidence":"original observed DOM change",
       "resultRect":{"x":20,"y":20,"width":190,"height":38}}]}


def test_real_steady_result_holds_are_measured_on_source_frame_clock():
    r=inspect_result_holds(Stage(),manifest(),fps=60)
    assert not r["findings"]
    assert [round(v["maxReadableSteadyHoldSeconds"],2) for v in r["measurements"]]==[1.5,1.]
    assert r["creativeApproved"] is False


def test_large_but_moving_result_does_not_fake_stable_reading_time():
    r=inspect_result_holds(Stage(move=True),manifest(),fps=60)
    assert len(r["findings"])==2
    assert all(f["code"]=="RESULT_READING_HOLD_TOO_SHORT" for f in r["findings"])


def test_static_but_tiny_result_is_not_accepted_as_readable():
    r=inspect_result_holds(Stage(shrink=True),manifest(),fps=60)
    assert len(r["findings"])==2
    assert all(x["maxReadableSteadyHoldSeconds"]==0
               for x in r["measurements"])


def test_cut_boundary_is_not_interpolated_as_smooth_exposure():
    r=inspect_result_holds(Stage(cut=True),manifest(),fps=60)
    assert not r["findings"]
    assert r["measurements"][0]["maxReadableSteadyHoldSeconds"]<1.5


def test_unverified_or_invalid_source_event_does_not_gain_a_fictional_hold():
    m=manifest()
    m["events"][1]["evidence"]=""
    r=inspect_result_holds(Stage(),m,fps=60)
    assert [x["eventIndex"] for x in r["measurements"]]==[0]
    m["events"][0]["resultRect"]["x"]=-1
    with pytest.raises(ValueError,match="genuine source"):
        inspect_result_holds(Stage(),m,fps=60)
    with pytest.raises(ValueError,match="FPS"):
        inspect_result_holds(Stage(),manifest(),fps=0)

def test_model_director_receives_strict_feedback_without_breaking_legacy_coverage(monkeypatch):
    import spatial_studio_stage
    from source_director_preflight import preflight_source_edit, director_feedback

    class PreflightStage(Stage):
        duration=10.
        def context_visibility(self,t):return 1.

    monkeypatch.setattr(spatial_studio_stage,"load_studio_stage",
                        lambda *args,**kwargs:PreflightStage(shrink=True))
    m=manifest()
    m["duration"]=10.
    plan={"durationSeconds":10.,
          "studioStage":{"camera":[
              {"at":0.,"scale":.8,"center":[.5,.5]},
              {"at":1.5,"focus":"event:0:result","scale":1.2},
              {"at":3.5,"focus":"event:1:result","scale":1.2}]},
          "audio":{"mode":"eventFoley","eventIndices":[0,1]}}
    standard=preflight_source_edit(plan,m,Path("source-test-only.mp4"),
                                   (320,180),60.,output_size=(640,360))
    strict=preflight_source_edit(plan,m,Path("source-test-only.mp4"),
                                 (320,180),60.,output_size=(640,360),
                                 enforce_reading_holds=True)
    assert standard["verdict"]=="GEOMETRY_AND_AUDIO_PREFLIGHT_PASS"
    assert strict["verdict"]=="REJECT"
    assert len(strict["findings"])==2
    assert all(f["code"]=="RESULT_READING_HOLD_TOO_SHORT"
               for f in strict["findings"])
    assert "sourceResultReadingHolds" in standard["observations"]
    assert "RESULT_READING_HOLD_TOO_SHORT" in director_feedback(strict)
