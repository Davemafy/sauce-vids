"""Scripted v2 regression gates: source truth, camera, concealment, privacy."""
from __future__ import annotations
import hashlib
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from scripted_v2_schema import load_script,FPS
from scripted_v2_render import (ScriptedV2Compositor,conceal_terminal,
                                ease,redact,_camera_for)
from scripted_v2_capture import capture_frame_with_selector_redaction


def _script():
    path=ROOT/'demos/brimble-scripted-v2.json'
    if not (ROOT/'studio/.tmp/brimble-reference-v16-ink/session.json').exists():
        pytest.skip("Private SHA-verified Brimble session is only available on worker")
    return load_script(path)


def test_quintic_camera_reaches_rest_before_next_move():
    assert (ease(0),ease(1))==(0,1)
    eps=1e-4
    assert ease(eps)<1e-10
    assert 1-ease(1-eps)<1e-10
    assert ease(.5)==pytest.approx(.5)
    session,manifest,shots,total=_script()
    assert 25*FPS<=total<=30*FPS
    assert all(shot.hold_frames>=6 for shot in shots)
    assert shots[0].transition_frames==0
    assert shots[0].zoom>=1.45
    assert shots[-1].hold_frames>=FPS
    assert all(1.0<=_camera_for(s)[2]<=1.7 for s in shots)


def test_real_verified_images_are_large_enough_for_crisp_1440_export():
    session,manifest,shots,total=_script()
    source=session/'states'/manifest['states'][0]['file']
    raw=source.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==manifest['states'][0]['sha256']
    image=cv2.imdecode(np.frombuffer(raw,dtype=np.uint8),cv2.IMREAD_COLOR)
    assert image.shape==(1440,2560,3)
    c=ScriptedV2Compositor(session,manifest,(2560,1440))
    f=c.draw(shots[0],_camera_for(shots[0]))
    assert f.shape==(1440,2560,3)
    # Text is source-native at 1440, not a low-res 1080 frame upscaled.
    assert c.w>1920


def test_source_true_modal_remains_sharp_when_stray_terminal_is_removed():
    session,manifest,shots,total=_script()
    source=session/'states'/manifest['states'][5]['file']
    raw=cv2.imread(str(source),cv2.IMREAD_COLOR)
    fixed=conceal_terminal(raw,5)
    # Panel interior is concealed, but the observed modal content survives.
    assert not np.array_equal(raw[510,2240],fixed[510,2240])
    assert np.array_equal(raw[890,1430],fixed[890,1430])
    engine=ScriptedV2Compositor(session,manifest,(1920,1080))
    result=engine.state(shots[-1])
    assert result.shape==(1440,2560,3)


def test_optional_region_redaction_is_destructive_and_source_immutable():
    original=np.full((1440,2560,3),250,dtype=np.uint8)
    cv2.putText(original,"REAL_SECRET_VALUE",(800,700),
                cv2.FONT_HERSHEY_SIMPLEX,2,(0,0,0),5,cv2.LINE_AA)
    before=original.copy()
    hidden=redact(original,dict(x=385.,y=302.,width=450.,height=95.))
    assert np.array_equal(original,before)
    assert hidden[700,900].mean()<before[700,900].mean()
    assert not np.array_equal(hidden[700:760,900:1600],original[700:760,900:1600])


def test_film_callout_no_longer_draws_an_extra_white_arc():
    code=(ROOT/'scripts/studio_motion_callouts.py').read_text()
    assert "d.arc((" not in code
    assert "d.line((20,2,dw-20,2)" not in code
    session,meta,shots,_=_script()
    f=ScriptedV2Compositor(session,meta).draw(shots[0],_camera_for(shots[0]))
    assert np.any(f[:,:,:3] > 200)


@pytest.mark.skipif(not (ROOT/'studio/.tmp/brimble-reference-v16-ink').exists(),
                    reason="Requires a worker with headless Chromium")
def test_selector_based_private_field_blur_uses_live_geometry(tmp_path):
    from playwright.sync_api import sync_playwright
    chrome=Path('/opt/devmcp-browsers/chromium_headless_shell-1254/chrome-headless-shell-linux64/chrome-headless-shell')
    if not chrome.is_file():pytest.skip("Pinned Chromium not installed")
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path=str(chrome),
          args=['--no-sandbox','--disable-dev-shm-usage'])
        try:
            page=browser.new_page(viewport={'width':1280,'height':720},
                                  device_scale_factor=2)
            page.set_content('<html><body><input id="secret" type="password" '
                             'value="PLACEHOLDER" style="position:absolute;'
                             'left:220px;top:220px;width:340px;height:50px" />'
                             '<span id="public">Public</span></body></html>')
            path=tmp_path/'clean.png'
            receipt=capture_frame_with_selector_redaction(
                page,path,['input[type="password"]'],expected_dpr=2)
            assert receipt['redactionRegions']==1
            assert receipt['settled']['fonts']=='loaded'
            assert hashlib.sha256(path.read_bytes()).hexdigest()==receipt['sha256']
            assert cv2.imread(str(path),cv2.IMREAD_COLOR).shape==(1440,2560,3)
            with pytest.raises(RuntimeError):
                capture_frame_with_selector_redaction(
                    page,tmp_path/'fail.png',['#does-not-exist'],expected_dpr=2)
        finally:
            browser.close()


def test_window_rounding_has_no_missing_top_strip_between_corners():
    session,manifest,shots,total=_script()
    engine=ScriptedV2Compositor(session,manifest,(1920,1080))
    frame=engine.draw(shots[0],_camera_for(shots[0]))
    # The website's captured top is white, not a black 16px gap between
    # rounded corners; preserve the source-true border and antialiasing.
    assert np.mean(frame[136,960])>210
    assert np.mean(frame[146,960])>210


def test_voice_bed_ducking_and_default_silent_soundtrack(tmp_path):
    import wave
    from scripted_v2_audio import (_duck_envelope,make_soundtrack,RATE)
    n=RATE*3
    voice=np.zeros((n,2),np.float32)
    t=np.arange(RATE,dtype=np.float32)/RATE
    voice[RATE:2*RATE,:]=(.23*np.sin(2*np.pi*210*t))[:,None]
    envelope=_duck_envelope(voice)
    assert envelope[RATE+RATE//2] < .35
    assert envelope[RATE//3] > .95
    assert envelope[2*RATE+RATE//2] > .95

    filename=tmp_path/'test-voice.wav'
    with wave.open(str(filename),'wb') as w:
        w.setnchannels(2);w.setframerate(RATE);w.setsampwidth(2)
        w.writeframes((voice*32767).astype('<i2').tobytes())
    result=make_soundtrack(tmp_path/'mixed.wav',180,voice=filename,bed=True)
    assert result['ducked'] and result['samples']==n
    assert not result['silent']
    silence=make_soundtrack(tmp_path/'silent.wav',180)
    assert silence['silent'] and not silence['ducked']
    assert (tmp_path/'silent.wav').stat().st_size>0
