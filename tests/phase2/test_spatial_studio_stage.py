"""Cross-site reusable studio-stage tests: real-frame provenance, timing, bounds."""
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from spatial_studio_stage import (load_studio_stage, render_studio_stage,
                                  detect_appearance_onset, _source_fraction)


@pytest.fixture()
def capture(tmp_path):
    fps=25;size=(320,180);n=60
    source=tmp_path/"source.mp4"
    out=cv2.VideoWriter(str(source),cv2.VideoWriter_fourcc(*"mp4v"),fps,size)
    assert out.isOpened()
    for i in range(n):
        f=np.full((180,320,3),210,dtype=np.uint8)
        # Only a genuine recorded result changes after the mouse release.
        if i>=26:
            f[27:145,115:290]=(12,25,240)
        out.write(f)
    out.release()
    assert source.is_file() and source.stat().st_size>1000
    event={
        "kind":"theme_change","start":.60,"end":.84,"t":1.40,
        "evidence":"verified original source-theme CSS and pixel difference",
        "targetRect":{"x":15,"y":28,"width":58,"height":19},
        "resultRect":{"x":115,"y":27,"width":175,"height":118},
        "componentRect":{"x":130,"y":35,"width":38,"height":33}}
    m={"cursorless":True,"capture_rect":{"width":320,"height":180},
       "duration":n/fps,"events":[event]}
    return tmp_path,source,m


def plan(duration=2.4,*,appearance=True):
    return {"camera":[
        {"at":0,"scale":.75,"center":[.50,.50],"yaw":-5,"pitch":-3},
        {"at":.9,"scale":.78,"center":[.51,.48],"yaw":-3,"pitch":-2},
        {"at":1.70,"startAt":1.08,"scale":.79,"focus":"event:0:result","yaw":1,"pitch":1},
        {"at":duration,"startAt":1.8,"scale":.78,"focus":"event:0:result","yaw":0,"pitch":0}],
        "material":{"color":[24,25,27],"grain":.3},
        "lighting":{"eventIndex":0,"trigger":"appearance" if appearance else "verified",
                    "intensity":.7,"transitionSeconds":.28},
        "depthPx":10,"reflection":.06,
        "payoff":{"region":"event:0:result","minVisible":.78,"mode":"overview"}}


def load(cfg,m,source,duration=2.4):
    return load_studio_stage(cfg,m,source,(320,180),(640,360),duration,25)


def test_sustained_source_pixel_change_is_earlier_than_dom_confirmation(capture):
    _,src,m=capture
    evidence=detect_appearance_onset(src,(320,180),m["events"][0],25)
    assert evidence["method"]=="sustained-pixel-evidence"
    assert evidence["candidateFrame"]==26
    assert evidence["time"]==pytest.approx(1.04)
    assert evidence["time"]>m["events"][0]["end"]
    assert evidence["time"]<m["events"][0]["t"]


def test_stage_json_is_generic_and_uses_original_ui_pixels(capture):
    _,src,m=capture
    stage=load(plan(),m,src)
    assert stage.onset["time"]==pytest.approx(1.04)
    assert stage.visibility(2.4)>.78
    assert stage.context_visibility(2.4)>.85
    frame=np.full((180,320,3),211,dtype=np.uint8)
    snapshot=frame.copy()
    rendered=render_studio_stage(stage,frame,0)
    assert rendered.shape==(360,640,3)
    assert rendered.dtype==np.uint8
    assert np.array_equal(frame,snapshot), "no rewriting genuine product UI"
    assert rendered.std()>0.4


def test_result_effect_never_appears_before_source_pixels(capture):
    _,src,m=capture
    stage=load(plan(),m,src)
    # Stage light only after source appearance, not on the button press.
    before=np.full((180,320,3),211,dtype=np.uint8)
    after=before.copy()
    after[27:145,115:290]=(12,25,240)
    a=render_studio_stage(stage,before,.80)
    b=render_studio_stage(stage,before,.98)
    # Keyframes can move the captured UI, but both stage backgrounds have no
    # saturated event-colored lighting in the corners before source onset.
    assert np.array_equal(a[0,0],b[0,0])
    c=render_studio_stage(stage,after,1.60)
    # Light stage; never need to paint product UI to get that response.
    assert not np.array_equal(a[0,0],c[0,0]) or np.mean(c[350,250])>np.mean(a[350,250])


def test_grayscale_video_does_not_guess_appearance_event(capture,tmp_path):
    _,src,m=capture
    flat=tmp_path/"flat.mp4"
    out=cv2.VideoWriter(str(flat),cv2.VideoWriter_fourcc(*"mp4v"),25,(320,180))
    for i in range(60):out.write(np.full((180,320,3),205,dtype=np.uint8))
    out.release()
    ev=detect_appearance_onset(flat,(320,180),m["events"][0],25)
    assert ev["method"]=="verified-event-time"
    assert ev["time"]==m["events"][0]["t"]


def test_result_anchor_cannot_precede_detected_pixel_evidence(capture):
    _,src,m=capture
    cfg=plan();cfg["camera"][2]["startAt"]=.96
    with pytest.raises(ValueError,match="source-visible"):
        load(cfg,m,src)


def test_multi_event_result_anchor_cannot_bypass_own_confirmation(capture):
    _,src,m=capture
    m["events"].append({**m["events"][0],"t":1.88,"end":1.7,
                        "start":1.55})
    cfg=plan();cfg["camera"][2]["focus"]="event:1:result"
    with pytest.raises(ValueError,match="source-visible"):
        load(cfg,m,src)


@pytest.mark.parametrize("patch",[
    {"lighting":{"eventIndex":5}},
    {"lighting":{"eventIndex":0,"trigger":"unverified"}},
    {"material":{"color":[300,0,0]}},
    {"material":{"grain":2.}},
    {"reflection":.5},
    {"depthPx":50},
    {"imagination":"fake product"},
])
def test_invalid_unbounded_or_unverified_studio_controls_rejected(capture,patch):
    _,src,m=capture;cfg=plan();cfg.update(patch)
    with pytest.raises(ValueError):
        load(cfg,m,src)


def test_overview_finally_requires_whole_product_context(capture):
    _,src,m=capture;cfg=plan()
    cfg["camera"][-1]={"at":2.4,"startAt":1.8,"scale":1.55,
                        "center":[.18,.15],"yaw":10,"pitch":5}
    with pytest.raises(ValueError,match="overview clips|payoff would be clipped"):
        load(cfg,m,src)


def test_detail_mode_is_explicit_and_still_requires_verified_target(capture):
    _,src,m=capture;cfg=plan()
    cfg["payoff"]={"region":"event:0:component","mode":"detail","minVisible":.6}
    st=load(cfg,m,src)
    assert st.payoff_region=="component"
    assert st.payoff_mode=="detail"


def test_slider_confirmed_mid_drag_is_admissible(capture):
    _,src,m=capture
    e=m["events"][0]
    e.update({"kind":"slider_change","start":0.,"t":1.4,"end":1.8})
    cfg=plan(appearance=False)
    cfg["camera"][2]["startAt"]=1.40  # Source-visible event.t gate is mandatory.
    st=load(cfg,m,src)
    assert st.onset["method"]=="verified-event-time"
    assert st.onset["time"]==1.4


def test_opposite_end_user_ui_source_is_not_assumed_25fps(capture):
    _,src,m=capture;cfg=plan(appearance=False)
    cfg["camera"][2]["startAt"]=1.40  # Source-visible event.t gate is mandatory.
    st=load(cfg,m,src)
    assert st.source_size==(320,180)
    assert st.output_size==(640,360)
    assert st.onset["time"]==1.4


def test_source_true_action_target_must_be_visible(capture):
    _,src,m=capture;cfg=plan()
    cfg["camera"][0].update(scale=1.55,center=[.1,.1])
    cfg["camera"][1].update(scale=1.55,center=[.1,.1])
    with pytest.raises(ValueError,match="genuine action target"):
        load(cfg,m,src)


def test_rendered_cursor_projection_catches_model_wrong_focus(capture):
    _,src,m=capture
    st=load(plan(),m,src)
    assert st.point_visible(.60,40,35)
    assert not st.point_visible(.60,2000,2000)


def test_bounded_model_repair_changes_only_unambiguous_presentation():
    from studio_plan_bounded_repair import normalize_generated_studio_plan
    p={"schema":"sauce-film-plan-v1","presentation":"window","studioStage":{
        "camera":[{"at":0,"scale":.8},{"at":2.4,"scale":.8}],
        "lighting":{"eventIndex":0}}}
    fixed,receipt=normalize_generated_studio_plan(p)
    assert p["presentation"]=="window"  # never overwrite model evidence
    assert fixed["presentation"]=="fullscreen"
    assert fixed["studioStage"]==p["studioStage"]  # no camera manipulation
    assert len(receipt["changes"])==1
    assert receipt["creativeApproval"] is False


def test_bounded_repair_never_strips_existing_window_or_invents_camera():
    from studio_plan_bounded_repair import normalize_generated_studio_plan
    p={"studioStage":{},"presentation":"window","window":{"scale":.8}}
    fixed,receipt=normalize_generated_studio_plan(p)
    assert fixed==p
    assert not receipt["changes"]


def test_director_packet_uses_measured_source_and_no_dom_text(capture):
    import hashlib
    from film_director_capabilities import build_contract
    root,src,m=capture
    manifest=root/"capture.json"
    m["events"][0]["evidence"]="SECRET_should_not_leave_worker"
    manifest.write_text(json.dumps(m))
    packet=build_contract(src,manifest,"Direct a source-true product film")
    assert packet["actualCapture"]["sourceSha256"]==hashlib.sha256(src.read_bytes()).hexdigest()
    assert packet["actualCapture"]["nativeFps"]==25
    assert packet["actualCapture"]["verifiedEvents"][0]["kind"]=="theme_change"
    assert "studioStage" in packet["outputSchema"]["properties"]
    assert "SECRET_should_not_leave_worker" not in json.dumps(packet)
    assert packet["localGate"]["creativeApproval"] is False


def test_event_foley_validates_source_action_not_fabricated_timestamps(capture):
    import hashlib
    from film_plan import load_film_plan
    root,source,manifest=capture
    mp=root/"capture.json"
    mp.write_text(json.dumps(manifest))
    plan_data={"schema":"sauce-film-plan-v1",
        "sourceSha256":hashlib.sha256(source.read_bytes()).hexdigest(),
        "manifestSha256":hashlib.sha256(mp.read_bytes()).hexdigest(),
        "durationSeconds":2.4,"presentation":"fullscreen","cursor":"none",
        "camera":[{"at":0,"anchor":"wide","zoom":1},
                  {"at":2.4,"anchor":"wide","zoom":1}],
        "audio":{"mode":"eventFoley","eventIndex":0,
                 "clickGain":.5,"motionGain":.3,"masterGain":.55}}
    result=load_film_plan(plan_data,manifest,source,mp,(320,180),2.4,root/"plan.json")
    assert result.duration==2.4
    assert result.audio_file is None
    bad=json.loads(json.dumps(plan_data))
    bad["audio"]["eventIndex"]=12
    with pytest.raises(ValueError,match="genuine event"):
        load_film_plan(bad,manifest,source,mp,(320,180),2.4,root/"plan.json")
    bad=json.loads(json.dumps(plan_data))
    bad["audio"]["clickGain"]=1.2
    with pytest.raises(ValueError,match="out of bounds"):
        load_film_plan(bad,manifest,source,mp,(320,180),2.4,root/"plan.json")
    bad=json.loads(json.dumps(plan_data))
    bad["audio"]["file"]="/tmp/unsafe.wav"
    with pytest.raises(ValueError,match="not paths"):
        load_film_plan(bad,manifest,source,mp,(320,180),2.4,root/"plan.json")


def test_studio_stage_owns_camera_without_dummy_flat_camera(capture):
    import hashlib
    from film_plan import load_film_plan
    root,source,manifest=capture
    mp=root/"capture.json";mp.write_text(json.dumps(manifest))
    plan_data={"schema":"sauce-film-plan-v1",
        "sourceSha256":hashlib.sha256(source.read_bytes()).hexdigest(),
        "manifestSha256":hashlib.sha256(mp.read_bytes()).hexdigest(),
        "durationSeconds":2.4,"presentation":"fullscreen","cursor":"none",
        "studioStage":plan()}
    result=load_film_plan(plan_data,manifest,source,mp,(320,180),2.4,root/"plan.json")
    assert len(result.camera_keys)==2
    assert all(k.zoom==1 for k in result.camera_keys)
    assert result.camera_keys[-1].at==2.4
