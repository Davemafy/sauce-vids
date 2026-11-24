"""Private URL scout: safe action admission, real recorded click semantics,
source-bound editing, and negative evidence guards. No Internet in unit tests.
"""
import hashlib,json,sys,cv2,numpy as np
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts"))
from public_interaction_scout import safe_action,select_story_actions,diff_score
from verified_capture_receipt_adapter import convert
from source_event_director import direction
from source_director_preflight import preflight_source_edit
from quality_preview_supervisor import analyze


def test_safe_public_controls_never_submit_or_buy():
    base={"label":"Switch to dark mode","outer":'<button type="button" aria-label="Switch to dark mode">',
          "w":32,"h":30,"role":"","tag":"BUTTON"}
    assert safe_action(base)
    assert safe_action({**base,"label":"Contrast matrix","outer":"<button>Contrast matrix</button>"})
    assert not safe_action({**base,"label":"Upgrade to Pro"})
    assert not safe_action({**base,"label":"Buy lifetime license"})
    assert not safe_action({**base,"outer":'<a href="/checkout">Theme</a>'})
    assert not safe_action({**base,"outer":'<button type="submit">Dark mode</button>'})
    assert not safe_action({**base,"label":"Submit new palette"})


def _candidate(label,changed):
    return {"label":label,"tag":"BUTTON","role":"","status":"verified_display_change",
      "originalRect":{"x":150,"y":100,"w":70,"h":28},
      "pixel":{"changedFraction":changed,"meanChannelDelta":changed*100},
      "beforeSha256":"1"*64,"afterSha256":"2"*64}


def test_scout_selects_complementary_source_backed_actions_only():
    report={"schema":"sauce-public-ui-scout-v1","observedLandingUrl":"https://design.example/demo",
            "accepted":[_candidate("Switch to dark mode",.82),
                        _candidate("Color info",.61),
                        _candidate("Contrast matrix",.58)]}
    out=select_story_actions(report)
    assert [a["label"] for a in out["actions"]]==[
        "Switch to dark mode","Contrast matrix"]
    assert [a["role"] for a in out["actions"]]==["appearance","inspection"]
    assert out["premiumApproved"] is False
    with pytest.raises(ValueError,match="No second"):
        select_story_actions({**report,"accepted":[
            _candidate("Switch to dark mode",.65),
            _candidate("Switch to light mode",.60)]})
    with pytest.raises(ValueError,match="No source UI candidates"):
        select_story_actions({**report,"accepted":None})
    with pytest.raises(ValueError,match="receipt"):
        select_story_actions({**report,"schema":"forged"})


def test_original_before_after_pixels_are_required():
    def png(color):
        f=np.full((480,640,3),color,np.uint8)
        ok,raw=cv2.imencode(".png",f)
        assert ok
        return raw.tobytes()
    assert diff_score(png(40),png(40))["changedFraction"]==0.
    assert diff_score(png(40),png(230))["changedFraction"]==1.


@pytest.fixture()
def verified_click_video(tmp_path):
    source=tmp_path/"original-60fps.mp4"
    writer=cv2.VideoWriter(str(source),cv2.VideoWriter_fourcc(*"mp4v"),60,(320,180))
    assert writer.isOpened()
    for i in range(720):
        frame=np.full((180,320,3),210 if i<138 else 32,np.uint8)
        if i>=390:frame[32:147,68:262]=(170,200,120)
        writer.write(frame)
    writer.release()
    h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    # Generated in the fixture to represent actual source-time Playwright
    # samples; not claimed as a recorded real public browser.
    points=[]
    for i in range(100):
        t=.05+.113*i
        x=250. if t<4.5 else 215.
        points.append({"t":round(t,5),"x":x,"y":42.})
    control={"x":170,"y":25,"width":120,"height":45}
    result0={"x":0,"y":0,"width":320,"height":180}
    result1={"x":68,"y":32,"width":194,"height":115}
    original=tmp_path/"original-events.json"
    actions=[]
    for i,(start,release,done,result) in enumerate([
       (2.15,2.26,3.05,result0),(6.25,6.36,7.45,result1)]):
        label="event"+str(i)
        actions.extend([
          {"kind":"pointerdown","actionKind":"click","t":start,
           "label":label,"targetRect":control},
          {"kind":"pointerup","t":release,"label":label},
          {"kind":"verified_result","t":done,"label":label,
           "resultRect":result,
           "evidence":"actual decoded source state and browser DOM changed"}])
    original.write_text(json.dumps({"source":"https://public.example/demo",
      "capture":"Chromium X11 native DPR2 60fps","fps":60,
      "source_sha256":h(source),"cursorless":True,"frameCount":720,
      "capture_rect":{"width":320,"height":180},
      "events":actions,"pointer_samples":points}))
    return source,original


def test_original_release_and_real_source_pixel_change_are_distinct(verified_click_video,tmp_path):
    source,raw=verified_click_video
    m=convert(source,raw)
    assert [e["kind"] for e in m["events"]]==["click","click"]
    assert [e["end"] for e in m["events"]]==[2.26,6.36]
    assert all(e["start"]<e["end"]<e["t"] for e in m["events"])
    assert all(f>.013 for f in m["provenance"]["sourcePixelChangedFractions"])
    manifest=tmp_path/"manifest.json";manifest.write_text(json.dumps(m))
    plan=direction(source,manifest)
    assert plan["cursor"]=="recorded"
    assert plan["audio"]["eventIndices"]==[0,1]
    assert [k["focus"] for k in plan["studioStage"]["camera"]
            if k.get("focus","").endswith(":result")]==[
           "event:0:result","event:1:result"]
    quality=preflight_source_edit(plan,m,source,(320,180),60)
    assert quality["verdict"]=="GEOMETRY_AND_AUDIO_PREFLIGHT_PASS"
    assert quality["creativeApproved"] is False


def test_forged_or_missing_actual_release_cannot_be_model_input(verified_click_video):
    source,raw=verified_click_video
    x=json.loads(raw.read_text())
    x["events"]=[e for e in x["events"] if not
                  (e["kind"]=="pointerup" and e["label"]=="event0")]
    raw.write_text(json.dumps(x))
    with pytest.raises(ValueError,match="release"):
        convert(source,raw)
    x["events"].insert(1,{"kind":"pointerup","t":5.2,"label":"event0"})
    raw.write_text(json.dumps(x))
    with pytest.raises(ValueError,match="release"):
        convert(source,raw)
    x["events"][0]["actionKind"]="purchase"
    x["events"][1]["t"]=2.26
    raw.write_text(json.dumps(x))
    with pytest.raises(ValueError,match="action kind"):
        convert(source,raw)


def test_natural_real_ui_switch_not_an_editorial_cut(verified_click_video,tmp_path):
    source,raw=verified_click_video
    m=convert(source,raw)
    manifest=tmp_path/"bound-manifest.json"
    manifest.write_text(json.dumps(m))
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    ev={"source_path":str(source),"source_sha256":sha(source),
        "event_manifest_path":str(manifest),
        "event_manifest_sha256":sha(manifest)}
    same=analyze(source,evidence=ev,seconds=12)
    assert "ABRUPT_CUT_CANDIDATE" not in [f["code"] for f in same["findings"]]
    assert same["sourceRelativeRealUiTransitions"]
    extra=tmp_path/"unsourced-film.mp4"
    writer=cv2.VideoWriter(str(extra),cv2.VideoWriter_fourcc(*"mp4v"),60,(320,180))
    assert writer.isOpened()
    inp=cv2.VideoCapture(str(source))
    for i in range(720):
        ok,frame=inp.read();assert ok
        if i>=590:frame[:]=(240,240,240)
        writer.write(frame)
    writer.release();inp.release()
    bad=analyze(extra,evidence=ev,seconds=12)
    assert "ABRUPT_CUT_CANDIDATE" in [f["code"] for f in bad["findings"]]


def test_native_draw_stroke_requires_real_release_motion_and_result(verified_click_video):
    source,raw=verified_click_video
    record=json.loads(raw.read_text())
    box={"x":0,"y":0,"width":320,"height":180}
    record.update(schema="sauce-native-draw-research-v1",before_paths=0,
        after_paths=1,surface_pixel_change=.05,decoded_surface_pixel_change=.05)
    record["events"]=[
        {"kind":"pointerdown","actionKind":"draw_stroke","t":2.15,
         "label":"draw","targetRect":box},
        {"kind":"pointerup","label":"draw","t":2.75},
        {"kind":"verified_result","label":"draw","t":3.05,
         "resultRect":box,"evidence":"fixture stroke result"}]
    record["pointer_samples"]=[{"t":round(.05+i*.02,4),
         "x":float(40+200*min(1,max(0,(.05+i*.02-2.15)/.6))),"y":80.}
         for i in range(200)]
    raw.write_text(json.dumps(record))
    result=convert(source,raw)
    assert result["events"][0]["kind"]=="draw_stroke"
    assert result["events"][0]["end"]==2.75
    for bad in [
        {**record,"after_paths":0},
        {**record,"decoded_surface_pixel_change":0},
        {**record,"events":[record["events"][0],record["events"][2]]},
        {**record,"pointer_samples":[{**p,"x":40.} for p in record["pointer_samples"]]},
    ]:
        raw.write_text(json.dumps(bad))
        with pytest.raises(ValueError,match="Drawing"):
            convert(source,raw)
