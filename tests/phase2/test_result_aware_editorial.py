"""Editorial gating tests: only evidence-backed modal/result events extend film."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts"))
from result_reveal import classify_result,append_result_hold

def test_bounded_dwell_padding_and_identical_sharp_source_frames():
    evidence=classify_result({"valid":True,"changedText":True,
        "addedTextNodes":3,"heightGain":40},2150)
    assert evidence and 1200<=evidence["holdMs"]<=1800
    assert evidence["evidence"]=="visible-result-change"
    assert evidence["fadeMs"]==350
    frame=np.zeros((12,20,3),dtype=np.uint8)+210
    frame[3:9,5:15]=(240,245,250)
    class Pipe:
        def __init__(self):self.chunks=[]
        def write(self,raw):self.chunks.append(raw)
    encoder=type("Encoder",(),{})()
    encoder.stdin=Pipe()
    added=append_result_hold(encoder,frame,60,evidence)
    assert 72<=added["holdFrames"]<=108
    assert added["fadeFrames"]==21
    assert added["totalFrames"]==len(encoder.stdin.chunks)
    assert all(b==frame.tobytes() for b in
               encoder.stdin.chunks[:added["holdFrames"]])
    assert np.all(np.frombuffer(encoder.stdin.chunks[-1],dtype=np.uint8)
               .reshape(frame.shape)==np.array([15,10,9],dtype=np.uint8))
    assert np.array_equal(frame[3:9,5:15],
                          np.full((6,10,3),(240,245,250),dtype=np.uint8))
    assert append_result_hold(encoder,frame,60,None)["totalFrames"]==0

def test_unchanged_modal_does_not_create_dead_air():
    assert classify_result({"valid":True,"changedText":False,
                            "addedTextNodes":0,"heightGain":9},1200) is None
    assert classify_result({"valid":False,"changedText":True,
                            "addedTextNodes":8,"heightGain":400},800) is None
    assert classify_result({"valid":True,"changedText":True,
                            "addedTextNodes":1,"heightGain":0},1900)["holdMs"]>=1200
    assert classify_result({"valid":True,"changedText":False,
                            "addedTextNodes":0,"heightGain":50},1900)["evidence"]=="container-expansion"


@pytest.mark.skipif(os.environ.get("SAUCE_BROWSER_TEST")!="1",
                    reason="Requires sandboxed Chromium capture")
def test_capture_links_fast_modal_and_real_code_expansion(tmp_path):
    from session_capture import record
    from session_contract import verify_package
    fixture=tmp_path/"app.html"
    fixture.write_text("""<!doctype html><html><head><style>
       html,body{font-family:Arial}
       #modal{display:none;position:fixed;z-index:100;top:120px;
          left:300px;width:410px;padding:20px;background:white;
          border:1px solid #ddd;border-radius:12px}
       #modal.open{display:block}
       #result{margin-top:14px;padding:30px;background:#fafafa}
       </style></head><body><main>
       <button id="connect">Connect Agent</button>
       <div id="modal" class="modal" role="dialog" aria-modal="true">
         <h2>Connect your agent</h2>
         <button id="codex">Codex</button><div id="result" hidden></div>
       </div></main><script>
       document.getElementById('connect').onclick=()=>setTimeout(()=>{
         document.getElementById('modal').classList.add('open')},130);
       document.getElementById('codex').onclick=()=>{
         const r=document.getElementById('result');r.hidden=false;
         r.innerHTML='<p>Copy the generated command</p><pre>demo command</pre>';
       }</script></body></html>""")
    output=tmp_path/"recording"
    actions=[
        {"action":"click","selector":"#connect","settle_ms":260,
         "expect_selector":"[role=dialog]"},
        {"action":"click","selector":"#codex","settle_ms":250,
         "expect_text":"Copy the generated command"}]
    session=record(fixture.as_uri(),actions,output,1280,720,2)
    verify_package(session,output)
    clicks=[e for e in session["events"] if e.get("type")=="click"]
    modals=[e for e in session["events"] if e.get("type")=="dialog-visible"]
    results=[e for e in session["events"] if e.get("type")=="result-revealed"]
    assert len(clicks)==2
    assert len(modals)>=1
    assert modals[0]["triggeredByClick"] is True
    assert 0<=modals[0]["triggerLatencyMs"]<=300
    assert session["workflow"][-1]["result_evidence"]["evidence"] in {
        "visible-result-change","container-expansion"}
    assert results and results[-1]["redacted"]
    assert "demo command" not in json.dumps(session)


@pytest.mark.skipif(os.environ.get("SAUCE_BROWSER_TEST")!="1",
                    reason="Requires real Chromium")
def test_recorder_detects_high_z_overlay_without_role_dialog(tmp_path):
    from session_capture import record
    html=tmp_path/"overlay.html"
    html.write_text("""<!doctype html><html><style>
       #floating{display:none;position:fixed;left:300px;top:120px;
         width:380px;height:260px;background:white;z-index:70}
       #floating.open{display:block}</style>
       <button id="show">Show overlay</button>
       <section id="floating" data-state="open"><h2>Popover result</h2>
         <p>Visible elevated content</p></section>
       <script>document.getElementById('show').onclick=()=>setTimeout(
         ()=>document.getElementById('floating').classList.add('open'),120)
       </script></html>""")
    output=tmp_path/"capture"
    session=record(html.as_uri(),[
       {"action":"click","selector":"#show","settle_ms":280,
        "expect_selector":"#floating"}],output,1280,720,2)
    click=next(e for e in session["events"] if e["type"]=="click")
    overlay=next(e for e in session["events"] if
                 e["type"]=="dialog-visible")
    assert overlay["overlaySource"]=="observed-high-z"
    assert overlay["triggeredByClick"]
    assert 0<=overlay["triggerLatencyMs"]<=300
    assert overlay["t"]>click["t"]
    assert overlay["role"]=="dialog"
