"""Fail-closed tests for new URL -> genuine UI tab capture and source cut grammar.

Mocked browser objects verify rejection logic without contacting websites.
Positive real Chromium capture+render evidence remains in private worker QA.
"""
from __future__ import annotations
import copy,hashlib,json,sys
from pathlib import Path
import cv2,numpy as np,pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
import source_truth_tab_capture as capture
from source_action_cut_budget import fit_verified_result_cut_budget
from source_locked_plan_retarget import retarget
import auto_public_ui_film


class FakeTab:
    def click(self,timeout=2500):return None
class FakeLocator:
    def get_by_role(self,role,name,exact=True):
        assert role=="tab" and exact
        return FakeTab()
class FakePage(FakeLocator):
    def __init__(self,text_len,after_state):
        self.text_len=text_len;self.after_state=after_state
    def wait_for_timeout(self,ms):pass
    def evaluate(self,script,name=None):
        if script==capture.PANEL_JS:
            return {"selected":True,"panelVisible":True,
                    "control":[140.,70.,90.,28.],
                    "result":[300.,140.,900.,580.]}
        if "innerText" in script:return self.text_len
        raise AssertionError(script[:80])


def test_real_result_substance_veto_rejects_empty_tab(monkeypatch):
    before=np.full((900,1440,3),17,np.uint8)
    after=before.copy()
    # Real screen result pixels: visually changed but blank.
    after[140:720,300:1200]=(46,46,46)
    monkeypatch.setattr(capture,"screenshot_bgr",lambda page:after)
    with pytest.raises(ValueError,match="readable visual substance"):
        capture.score_actual_tab(FakePage(352,after), "Custom",before)
    after=before.copy()
    for y in range(140,720,20):
        cv2.rectangle(after,(320,y),(1110,y+7),(200,200,200),-1)
    monkeypatch.setattr(capture,"screenshot_bgr",lambda page:after)
    passed=capture.score_actual_tab(FakePage(2200,after),"Dashboard",before)
    assert passed["score"]>.045
    assert passed["observedVisibleTextChars"]==2200
    assert passed["originalResultGrayStd"]>22


def test_only_safe_public_aria_tab_candidates():
    class Page:
        def evaluate(self,expr):
            return [
             {"name":"Dashboard","group":[500,130,450],
              "selected":False,"inDisallowedContainer":False,"disabled":False,
              "isLink":False,"hasUnsafeForm":False},
             {"name":"Marketing","group":[500,130,450],
              "selected":False,"inDisallowedContainer":False,"disabled":False,
              "isLink":False,"hasUnsafeForm":False},
             {"name":"Application","group":[500,130,450],
              "selected":False,"inDisallowedContainer":False,"disabled":False,
              "isLink":False,"hasUnsafeForm":False},
             {"name":"Delete Account","group":[500,130,450],
              "selected":False,"inDisallowedContainer":False,"disabled":False,
              "isLink":False,"hasUnsafeForm":False},
             {"name":"Checkout","group":[500,130,450],
              "selected":False,"inDisallowedContainer":False,"disabled":False,
              "isLink":False,"hasUnsafeForm":False},
             {"name":"Sign In","group":[500,130,450],
              "selected":False,"inDisallowedContainer":True,"disabled":False,
              "isLink":False,"hasUnsafeForm":False},
            ]
    assert [v["name"] for v in capture._candidates(Page())]==[
        "Dashboard","Marketing","Application"]


def actual_story():
    W,H=2880,1800
    original=[]
    pts=[]
    keys=[{"at":0.,"scale":.88,"center":[.5,.5]}]
    starts=[2.,6.,10.]
    for i,start in enumerate(starts):
        x=1250.+i*160
        original.append({
            "kind":"tab_switch","start":start,"end":start+1.,
            "t":start+1.,"evidence":"Original native source visible result",
            "observedPublicAction":["Marketing","Dashboard","Application"][i],
            "targetRect":{"x":x,"y":270,"width":160.,"height":56.},
            "resultRect":{"x":800.,"y":400.,"width":1800.,"height":1300.}})
        for j in range(22):
            t=start-1.45+j*.048
            pts.append({"t":round(t,6),
                "x":round(x-60+115*(j/21),3),
                "y":298.})
        keys.extend([
            {"at":start,"startAt":start,"scale":1.15,
             "focus":f"event:{i}:target","cut":True},
            {"at":start+1.,"startAt":start+1.,"scale":.95,
             "focus":f"event:{i}:result","cut":True},
        ])
    keys.append({"at":16.,"scale":.9,"center":[.5,.5]})
    manifest={"cursorless":True,"duration":16.,
              "source":"https://tweakcn.com/editor/theme",
              "capture_rect":{"width":W,"height":H},
              "events":original,"pointer_samples":pts}
    plan={"schema":"sauce-film-plan-v1","durationSeconds":16.,
          "cursor":"recorded","presentation":"fullscreen",
          "studioStage":{"camera":keys,
             "lighting":{"eventIndex":2},"payoff":{"mode":"overview",
                   "region":"event:2:result"}},
          "audio":{"mode":"eventFoley","eventIndices":[0,1,2]}}
    return plan,manifest


def test_all_real_approaches_preserved_and_tiny_top_tabs_keep_browser():
    plan,manifest=actual_story()
    original=copy.deepcopy(plan)
    revised,changes=fit_verified_result_cut_budget(
        plan,manifest,60,source_size=(2880,1800))
    assert plan==original
    assert len(revised["studioStage"]["camera"])==8
    assert len(changes)==3
    for i,entry in enumerate(changes):
        assert entry["eventIndex"]==i
        assert entry["sourcePointerApproachSamples"]>=9
        assert entry["to"]["center"]==[.5,.5]
        assert "focus" not in entry["to"]
        assert not entry["to"].get("cut",False)
        assert entry["to"]["startAt"]<entry["to"]["at"]
    result_cuts=[k for k in revised["studioStage"]["camera"] if k.get("cut")]
    assert [k["at"] for k in result_cuts]==[3.,7.,11.]
    assert [k["focus"] for k in result_cuts]==[
        "event:0:result","event:1:result","event:2:result"]


def test_fake_missing_pointer_drops_only_redundant_actions():
    original,manifest=actual_story()
    broken=copy.deepcopy(manifest)
    broken["pointer_samples"]=[]
    revised,receipt=fit_verified_result_cut_budget(
        original,broken,60,source_size=(2880,1800))
    assert len(revised["studioStage"]["camera"])==5
    assert len([k for k in revised["studioStage"]["camera"] if k.get("cut")])==3
    assert len(receipt)==3
    assert all(c["to"] is None for c in receipt)
    rejected=copy.deepcopy(original)
    rejected["studioStage"]["camera"][2]["at"]=3.006
    result,changes=fit_verified_result_cut_budget(
        rejected,manifest,60,source_size=(2880,1800))
    assert result==rejected and changes==[]


def test_cannot_retarget_different_site_or_forged_source(tmp_path):
    plan,manifest=actual_story()
    a=tmp_path/"source-old.mp4";b=tmp_path/"source-new.mp4"
    a.write_bytes(b"actual-original-file");b.write_bytes(b"second-authentic-source")
    x=tmp_path/"old.json";y=tmp_path/"new.json"
    first=copy.deepcopy(manifest);second=copy.deepcopy(manifest)
    first["provenance"]={"originalSourceSha256":hashlib.sha256(a.read_bytes()).hexdigest()}
    second["provenance"]={"originalSourceSha256":hashlib.sha256(b.read_bytes()).hexdigest()}
    second["pointer_samples"]=[dict(p,t=p["t"]+.1) for p in second["pointer_samples"]]
    for event in second["events"]:
        event["start"]+=.1
        event["t"]+=.1
        event["end"]+=.1
    x.write_text(json.dumps(first));y.write_text(json.dumps(second))
    plan["sourceSha256"]=hashlib.sha256(a.read_bytes()).hexdigest()
    plan["manifestSha256"]=hashlib.sha256(x.read_bytes()).hexdigest()
    output,audit=retarget(plan,first,second,a,b,x,y)
    assert output["sourceSha256"]==hashlib.sha256(b.read_bytes()).hexdigest()
    assert audit["originalCreativeApproval"] is False
    assert audit["modelStatus"]=="SAVED_RESEARCH_ONLY_NOT_GOLD"
    assert [k["at"] for k in output["studioStage"]["camera"] if k.get("cut")]==[
        3.1,7.1,11.1]
    forged=copy.deepcopy(second);forged["source"]="https://different.example/page"
    with pytest.raises(ValueError,match="SAME EXACT"):
        retarget(plan,first,forged,a,b,x,y)
    a.write_bytes(b"tampered-original")
    with pytest.raises(ValueError,match="contradicts"):
        retarget(plan,first,second,a,b,x,y)


def test_one_command_wrapper_source_only_no_model_and_public_allowlist(tmp_path,monkeypatch):
    monkeypatch.setattr(auto_public_ui_film,"validate_public_url",lambda url:url)
    existing=tmp_path/"private-capture";existing.mkdir()
    for file in ("source-real-dpr2-60.mp4","source-events.json"):
        (existing/file).write_text("source")
    (existing/"discovery.json").write_text(json.dumps({
        "url":"https://real.example/docs",
        "host":"real.example",
        "actions":[{"name":"Marketing"},{"name":"Dashboard"}]}))
    manifest={"source":"https://real.example/docs","events":[],
              "cursorless":True}
    monkeypatch.setattr(auto_public_ui_film,"normalize",lambda *args:manifest)
    monkeypatch.setattr(auto_public_ui_film,"build_contract",lambda *args:{
       "actualCapture":{"sourceSha256":"source-real-hash",
        "manifestSha256":"real-manifest-hash",
        "verifiedEvents":[{"index":0,"sourceTime":{"start":1.,"confirmedResultAt":2.},
                             "verifiedObservedPublicAction":"Marketing"}]}})
    dst=tmp_path/"output"
    receipt=auto_public_ui_film.run("https://real.example/docs","real.example",dst,
        from_capture=existing,capture_only=True)
    assert receipt["status"]=="verified_capture_ready"
    assert receipt["filmSha256"] if "filmSha256" in receipt else True
    assert receipt["creativeApproved"] is False
    assert receipt["productionReady"] is False
    assert (dst/"source-locked-manifest.json").exists()
    with pytest.raises(ValueError,match="allowed public host"):
        auto_public_ui_film.run("https://real.example/docs","evil.example",
            tmp_path/"bad",from_capture=existing,capture_only=True)
    with pytest.raises(ValueError,match="empty"):
        auto_public_ui_film.run("https://real.example/docs","real.example",
            dst,from_capture=existing,capture_only=True)
