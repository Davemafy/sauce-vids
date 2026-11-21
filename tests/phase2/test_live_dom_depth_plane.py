"""Source-true separate live DOM camera plane acceptance and negative gates."""
from __future__ import annotations
import asyncio
import hashlib
import json
from pathlib import Path
import sys

import cv2
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from live_dom_depth_plane import (load_live_dom_plane,validate_matched_frames,
                                  render_live_dom_plane,PlaneFrameReader)
from spatial_studio_stage import load_studio_stage,render_studio_stage
from verified_dom_pair_capture import check_pair,capture_pair,discover_verified_dom_plane


@pytest.fixture()
def paired(tmp_path):
    src=tmp_path/"source.mp4";plate=tmp_path/"plate.mp4"
    writers=[cv2.VideoWriter(str(p),cv2.VideoWriter_fourcc(*"mp4v"),25,(320,180))
             for p in (src,plate)]
    assert all(w.isOpened() for w in writers)
    for i in range(80):
        base=np.full((180,320,3),80,dtype=np.uint8)
        front=base.copy()
        if i>=25:
            cv2.rectangle(front,(110,35),(259,109),(245,245,245),-1)
            cv2.putText(front,f"REAL {i}",(123,75),cv2.FONT_HERSHEY_SIMPLEX,
                        .57,(12,12,12),1,cv2.LINE_AA)
        writers[0].write(front);writers[1].write(base)
    for w in writers:w.release()
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    m={
      "cursorless":True,"duration":3.2,
      "capture_rect":{"width":320,"height":180},
      "events":[{
          "kind":"theme_change","start":.4,"end":.44,"t":.8,
          "evidence":"verified synthetic test event (not claimed public site)",
          "targetRect":{"x":15,"y":40,"width":80,"height":30},
          "resultRect":{"x":110,"y":35,"width":150,"height":75},
          "componentRect":{"x":110,"y":35,"width":150,"height":75}}],
      "domPlanes":[{
          "id":"real-panel","firstPairedFrame":25,
          "rect":{"x":110,"y":35,"width":150,"height":75},
          "sourceSha256":digest(src),"plateSha256":digest(plate),
          "plateFile":"plate.mp4","opaqueSurface":True,"radiusPx":0,
          "captureMethod":"playwright-visible-then-CSS-visibility-hidden-and-restored"}]
    }
    side=tmp_path/"capture.json";side.write_text(json.dumps(m))
    plan={
        "id":"real-panel","eventIndex":0,"startAt":1.,
        "peakAt":1.6,"endAt":3.0,"liftPx":58,"scale":1.08,"shadowStrength":.45}
    return src,plate,side,m,plan


def load_fixture(paired,**update):
    src,_,side,m,plan=paired
    plan={**plan,**update}
    return load_live_dom_plane(plan,m,src,side,source_size=(320,180),
                               fps=25,duration=3.2)


def test_real_source_and_plate_are_bound_by_hashes_geometry_frames(paired):
    obj=load_fixture(paired)
    assert obj.id=="real-panel"
    assert obj.first_frame==25
    assert obj.source_sha256==hashlib.sha256(paired[0].read_bytes()).hexdigest()
    assert obj.amount(.6)==0
    assert .85<obj.amount(1.8)<=1
    assert obj.amount(3.12)==0
    reader=PlaneFrameReader(obj)
    a=reader.read(25);b=reader.read(46)
    assert a.shape==(180,320,3)
    assert b.shape==a.shape
    reader.close()


def test_layer_moves_independently_and_returns_to_exact_original_source(paired):
    src,plate,side,m,_=paired
    obj=load_fixture(paired)
    cfg={
       "camera":[{"at":0,"scale":.8,"center":[.5,.5]},
                 {"at":3.2,"scale":.8,"center":[.5,.5]}],
       "lighting":{"eventIndex":0},
       "payoff":{"region":"event:0:result","minVisible":.85,"mode":"overview"}
    }
    stage=load_studio_stage(cfg,m,src,(320,180),(640,360),3.2,25)
    a=cv2.VideoCapture(str(src));b=cv2.VideoCapture(str(plate))
    a.set(cv2.CAP_PROP_POS_FRAMES,50);b.set(cv2.CAP_PROP_POS_FRAMES,50)
    ok,original=a.read();ok2,clean=b.read();a.release();b.release()
    assert ok and ok2
    static=render_studio_stage(stage,original,2.0)
    lifted=render_live_dom_plane(stage,original,clean,obj,2.0)
    assert static.shape==lifted.shape==(360,640,3)
    assert (cv2.absdiff(static,lifted)>20).mean()>.003
    assert np.array_equal(original,original.copy())
    assert np.array_equal(render_live_dom_plane(stage,original,clean,obj,.9),
                          render_studio_stage(stage,original,.9))
    assert np.array_equal(render_live_dom_plane(stage,original,clean,obj,3.13),
                          render_studio_stage(stage,original,3.13))


def test_rejects_untrusted_plate_path_and_changed_bytes(paired):
    src,plate,side,m,plan=paired
    m2=json.loads(json.dumps(m))
    m2["domPlanes"][0]["plateFile"]="../outside.mp4"
    with pytest.raises(ValueError,match="local capture-owned"):
        load_live_dom_plane(plan,m2,src,side,source_size=(320,180),fps=25,duration=3.2)
    blob=plate.read_bytes()
    try:
        plate.write_bytes(blob+b"tampered")
        with pytest.raises(ValueError,match="hashes differ"):
            load_fixture(paired)
    finally:
        plate.write_bytes(blob)


def test_rejects_opaque_and_visibility_provenance_and_unverified_action(paired):
    src,plate,side,m,plan=paired
    bad=json.loads(json.dumps(m))
    bad["domPlanes"][0]["opaqueSurface"]=False
    with pytest.raises(ValueError,match="opaque DOM"):
        load_live_dom_plane(plan,bad,src,side,source_size=(320,180),fps=25,duration=3.2)
    bad=json.loads(json.dumps(m))
    bad["domPlanes"][0]["captureMethod"]="fabricated"
    with pytest.raises(ValueError,match="provenance"):
        load_live_dom_plane(plan,bad,src,side,source_size=(320,180),fps=25,duration=3.2)
    with pytest.raises(ValueError,match="source-proof"):
        load_fixture(paired,startAt=.80)
    with pytest.raises(ValueError,match="native source frames"):
        load_fixture(paired,peakAt=1.601)
    with pytest.raises(ValueError,match="real verified event"):
        load_fixture(paired,eventIndex=7)


def test_any_background_change_outside_live_element_fails_hard():
    base=np.zeros((180,320,3),np.uint8)+70
    fg=base.copy()
    fg[40:105,95:235]=244
    verdict=validate_matched_frames(fg,base,(95,40,140,65))
    assert verdict["outsideDifferentFraction"]==0
    wrong=base.copy()
    wrong[:30,:30]=255
    with pytest.raises(ValueError,match="OUTSIDE real element"):
        validate_matched_frames(fg,wrong,(95,40,140,65))


def test_png_pair_checks_strict_geometry_and_background():
    a=np.zeros((180,320,3),np.uint8)+170
    b=a.copy()
    a[40:110,100:240]=(20,40,250)
    _,p=cv2.imencode(".png",a)
    _,q=cv2.imencode(".png",b)
    outside,inside=check_pair(p.tobytes(),q.tobytes(),(100,40,140,70))
    assert outside==0 and inside>=.9
    wrong=b.copy();wrong[12:39,12:50]=30
    _,z=cv2.imencode(".png",wrong)
    with pytest.raises(ValueError,match="outside verified plane"):
        check_pair(p.tobytes(),z.tobytes(),(100,40,140,70))
    with pytest.raises(ValueError,match="no meaningful source pixels"):
        check_pair(q.tobytes(),q.tobytes(),(100,40,140,70))


def test_actual_chromium_discovery_capture_and_restoration(tmp_path):
    from playwright.async_api import async_playwright
    binary="/opt/devmcp-browsers/chromium_headless_shell-1254/chrome-headless-shell-linux64/chrome-headless-shell"
    if not Path(binary).is_file():pytest.skip("Headless browser not installed")
    async def run():
        async with async_playwright() as pw:
            b=await pw.chromium.launch(executable_path=binary,headless=True,
                                       args=["--no-sandbox"])
            ctx=await b.new_context(viewport={"width":640,"height":360},device_scale_factor=1)
            page=await ctx.new_page()
            await page.set_content(
              '<html><body style="background:#eee">'
              '<article style="position:absolute;left:130px;top:80px;width:250px;'
              'height:150px;background:#fff;border:1px solid black">'
              '<h3>Genuine test-only UI</h3><span>120</span></article></body></html>')
            found=await discover_verified_dom_plane(page,{
                "x":130,"y":80,"width":250,"height":150})
            assert found and found["matches"]==1 and found["score"]>.95
            pair=await capture_pair(page,found["selector"],
                                    expected_native_size=(640,360))
            assert pair.opaque_surface
            assert pair.changed_fraction>.012
            assert pair.outside_fraction<.00008
            assert await page.locator(found["selector"]).is_visible()
            assert await page.evaluate("window.__sauceActiveDomPlane===undefined")
            await page.locator("article").evaluate("(e)=>e.style.background='transparent'")
            with pytest.raises(ValueError,match="transparent element"):
                await capture_pair(page,found["selector"],
                                   expected_native_size=(640,360))
            assert await page.locator(found["selector"]).is_visible()
            await b.close()
    asyncio.run(run())


def test_director_advertises_only_real_encoded_browser_plate(paired):
    from film_director_capabilities import build_contract
    src,plate,side,m,_=paired
    packet=build_contract(src,side,"Direct a genuine layered product film")
    layers=packet["actualCapture"]["verifiedLiveDomPlanes"]
    assert len(layers)==1
    assert layers[0]["id"]=="real-panel"
    assert layers[0]["firstPairedNativeFrame"]==25
    assert layers[0]["nativeSourceRect"]==[110,35,150,75]
    assert "domPlane" in packet["availableEffects"]
    assert layers[0]["cleanPlateSha256"]==hashlib.sha256(plate.read_bytes()).hexdigest()
    # A forged plate or a referenced clip never becomes a model capability.
    bad=json.loads(json.dumps(m))
    bad["domPlanes"][0]["plateSha256"]="0"*64
    bad_side=side.parent/"forged.json"
    bad_side.write_text(json.dumps(bad))
    reject=build_contract(src,bad_side,"Direct a genuine layered product film")
    assert not reject["actualCapture"]["verifiedLiveDomPlanes"]
    assert "domPlane" not in reject["availableEffects"]


def test_unrelated_result_geometry_never_admits_a_real_but_wrong_layer(paired):
    src,plate,side,m,plan=paired
    bad=json.loads(json.dumps(m))
    # The card is real but does NOT represent this verified event's result.
    wrong={"x":5,"y":135,"width":40,"height":25}
    bad["events"][0]["resultRect"]=wrong
    bad["events"][0]["componentRect"]=wrong
    with pytest.raises(ValueError,match="verified real result"):
        load_live_dom_plane(plan,bad,src,side,source_size=(320,180),
                            fps=25,duration=3.2)
