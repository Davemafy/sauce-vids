"""The result must animate meaningfully, without inventing product actions."""
from __future__ import annotations
import hashlib
import os
import sys
from pathlib import Path
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts"))
from result_payoff import (
    ANTICIPATION_FRAMES,DOLLY_FRAMES,READ_FRAMES,FADE_FRAMES,
    CUT_SAFE_FRAME_COUNT,CODE_READ_FRAMES,OUTPUT_READ_FRAMES,
    DETAIL_DOLLY_FRAMES,DETAIL_CONTEXT_FRAMES,
    create_payoff_plan,pose_at,append_payoff,FOCUS_ANCHOR_JS
)

EVIDENCE={"evidence":"visible-result-change","holdMs":1600.,
          "sourceMs":2017.}
ANCHOR={"kind":"pre",
        "target":{"x":487,"y":471,"width":334,"height":52},
        "dialog":{"x":440,"y":122,"width":400,"height":476}}
POSE={"scale":1.31,"focusX":640,"focusY":362.59}

def test_real_command_target_builds_bounded_animated_camera_shot():
    p=create_payoff_plan(EVIDENCE,ANCHOR,POSE)
    assert p is not None and p["sourceKind"]=="pre"
    assert 1.45<p["endScale"]<1.62
    # The source-true camera must retain the actual dialog title and
    # command, not clip the heading to center only the last <pre>.
    assert 315<p["endFocusY"]<335
    span=ANCHOR["target"]["y"]+ANCHOR["target"]["height"]-ANCHOR["dialog"]["y"]
    projected_span=span*p["endScale"]*(1480/1280)*(1200/1140)
    assert projected_span<=832-64+0.05
    assert abs(p["endFocusX"]-648)<20
    assert p["readFrames"]==CODE_READ_FRAMES
    assert p["detailFrames"]==DETAIL_DOLLY_FRAMES
    assert p["contextFrames"]==DETAIL_CONTEXT_FRAMES
    assert p["detailScale"]>p["endScale"]+.24
    assert p["detailFocusX"]==pytest.approx(ANCHOR["target"]["x"]+ANCHOR["target"]["width"]/2)
    assert p["totalFrames"]==ANTICIPATION_FRAMES+DOLLY_FRAMES+DETAIL_CONTEXT_FRAMES+DETAIL_DOLLY_FRAMES+CODE_READ_FRAMES+FADE_FRAMES
    at_start=pose_at(p,0)
    assert at_start==(1.31,640.,362.59)
    at_end=pose_at(p,ANTICIPATION_FRAMES+DOLLY_FRAMES-1)
    assert at_end==pytest.approx((p['endScale'],p['endFocusX'],p['endFocusY']))
    # Both endpoints rest: no artificial snap on a 60fps edit.
    e0=pose_at(p,ANTICIPATION_FRAMES+0)
    e1=pose_at(p,ANTICIPATION_FRAMES+1)
    e_last=pose_at(p,ANTICIPATION_FRAMES+DOLLY_FRAMES-2)
    assert e1[0]-e0[0] > 0
    assert at_end[0]-e_last[0]<.001


def test_absent_proof_or_off_modal_result_does_not_fabricate_payoff():
    assert create_payoff_plan(None,ANCHOR,POSE) is None
    assert create_payoff_plan(EVIDENCE,None,POSE) is None
    bad=dict(ANCHOR)
    bad['target']={"x":120,"y":300,"width":334,"height":52}
    assert create_payoff_plan(EVIDENCE,bad,POSE) is None
    assert create_payoff_plan(EVIDENCE,{"kind":"img",**{k:v for k,v in ANCHOR.items()
                                                     if k!="kind"}},POSE) is None


def test_native_source_footage_outro_has_camera_move_and_sharp_locked_end():
    first=np.full((1080,1920,3),111,dtype=np.uint8)
    face=np.full_like(first,170)
    # No frame allocations accumulated in the mock pipe; the implementation
    # is the same fixed-size rawvideo FFmpeg path as the real production.
    class Sink:
        def __init__(self):self.packets=0;self.key={}
        def write(self,data):
            self.packets+=1
            if self.packets in (1,8,9,44,45,110,plan["totalFrames"]):
                self.key[self.packets]=hashlib.sha256(data).hexdigest()
    class Encoder:pass
    encoder=Encoder()
    encoder.stdin=Sink()
    calls=[]
    def render(z,x,y,frame):
        calls.append((z,x,y,frame))
        return face
    plan=create_payoff_plan(EVIDENCE,ANCHOR,POSE)
    result=append_payoff(encoder,first,plan,render)
    assert encoder.stdin.packets==plan["totalFrames"]
    assert len(calls)==DOLLY_FRAMES+DETAIL_DOLLY_FRAMES
    assert result['cameraMoveFrames']==36+DETAIL_DOLLY_FRAMES
    assert result['detailFrames']==DETAIL_DOLLY_FRAMES
    assert result['holdFrames']==ANTICIPATION_FRAMES+DETAIL_CONTEXT_FRAMES+CODE_READ_FRAMES
    assert result['fadeFrames']==12
    assert result['mode']=='source-result-dolly'
    assert encoder.stdin.key[1]==encoder.stdin.key[8]
    assert encoder.stdin.key[44]==encoder.stdin.key[45]
    assert encoder.stdin.key[plan["totalFrames"]]!=encoder.stdin.key[110]
    assert np.all(first==111)


@pytest.mark.skipif(os.environ.get("SAUCE_BROWSER_TEST")!="1",
                    reason="Requires real headless Chromium")
def test_actual_brimble_command_geometry_from_verified_har_only():
    from playwright.sync_api import sync_playwright
    source=ROOT/"studio/.tmp/brimble-reference-v16-ink"
    if not (source/"network.har").exists():
        pytest.skip("Brimble verified HAR not available in this checkout")
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,
              executable_path="/opt/devmcp-browsers/chromium_headless_shell-1254/chrome-headless-shell-linux64/chrome-headless-shell",
              args=["--no-sandbox","--disable-dev-shm-usage"])
        try:
            ctx=browser.new_context(viewport={"width":1280,"height":720},
                                    service_workers="block")
            ctx.route_from_har(str(source/"network.har"),not_found="abort",
                               update=False)
            page=ctx.new_page()
            page.goto("https://www.brimble.io/",wait_until="domcontentloaded")
            page.get_by_role("button",name="Connect your agent").click()
            page.get_by_role("dialog").wait_for(state="visible")
            page.get_by_text("Codex",exact=True).click()
            box=page.evaluate(FOCUS_ANCHOR_JS)
            plan=create_payoff_plan(EVIDENCE,box,POSE)
            assert plan is not None and plan["sourceKind"]=="pre"
            # The export has no product text and never clones the real
            # command into fabricated SVG/HTML layers.
            assert "text" not in str(box).lower()
            ctx.close()
        finally:
            browser.close()



def test_read_duration_is_source_verified_and_bounded():
    code_plan=create_payoff_plan(EVIDENCE,ANCHOR,POSE)
    output_plan=create_payoff_plan(EVIDENCE,{**ANCHOR,"kind":"output"},POSE)
    simple_plan=create_payoff_plan(EVIDENCE,{**ANCHOR,"kind":"p"},POSE)
    assert code_plan['readFrames']==CODE_READ_FRAMES
    assert output_plan['readFrames']==OUTPUT_READ_FRAMES
    assert simple_plan['readFrames']==READ_FRAMES
    assert [p['totalFrames'] for p in (simple_plan,output_plan,code_plan)]==[
        CUT_SAFE_FRAME_COUNT,
        CUT_SAFE_FRAME_COUNT+OUTPUT_READ_FRAMES-READ_FRAMES,
        CUT_SAFE_FRAME_COUNT+CODE_READ_FRAMES-READ_FRAMES+
          DETAIL_CONTEXT_FRAMES+DETAIL_DOLLY_FRAMES]
    assert all(p['totalFrames']==ANTICIPATION_FRAMES+DOLLY_FRAMES+
               p['contextFrames']+p['detailFrames']+
               p['readFrames']+FADE_FRAMES for p in
               (code_plan,output_plan,simple_plan))


def test_malformed_payoff_duration_fails_closed():
    class Sink:
        def write(self,data): raise AssertionError("Must validate before encoding")
    class Encoder: pass
    encoder=Encoder()
    encoder.stdin=Sink()
    original=np.zeros((1080,1920,3),dtype=np.uint8)
    plan=create_payoff_plan(EVIDENCE,ANCHOR,POSE)
    assert plan is not None
    for frames in (-1,121,100000,72.5,"108"):
        with pytest.raises(ValueError):
            append_payoff(encoder,original,{**plan,"readFrames":frames},
                          lambda *args: original)
    for bad in (-1,1,50,1000):
        with pytest.raises(ValueError):
            append_payoff(encoder,original,{**plan,"detailFrames":bad},
                          lambda *args: original)
