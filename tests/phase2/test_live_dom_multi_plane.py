"""Native-source 2-plane foreground cinematic integration and negative contracts."""
import asyncio
import hashlib
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from live_dom_multi_plane import (
    load_live_dom_planes,render_live_dom_planes,verify_group_projected_visibility,
    verify_source_relative_material)
from live_dom_depth_plane import check_multi_pair_video_frames
from spatial_studio_stage import load_studio_stage,render_studio_stage
from verified_dom_pair_capture import (
    capture_multi_pair,check_multi_pair,discover_verified_dom_planes)


@pytest.fixture
def twin(tmp_path):
    W,H=640,360
    source=tmp_path/"source.mp4"
    clean=tmp_path/"plate.mp4"
    writers=[cv2.VideoWriter(str(p),cv2.VideoWriter_fourcc(*"mp4v"),25,(W,H))
             for p in (source,clean)]
    assert all(q.isOpened() for q in writers)
    rects=[(70,75,210,115),(350,75,210,115)]
    for frame in range(100):
        background=np.full((H,W,3),75,np.uint8)
        foreground=background.copy()
        if frame>=35:
            for j,(x,y,w,h) in enumerate(rects):
                cv2.rectangle(foreground,(x,y),(x+w-1,y+h-1),(248,248,248),-1)
                cv2.putText(foreground,f"REAL {j+1} DATA",
                            (x+13,y+56),cv2.FONT_HERSHEY_SIMPLEX,.63,
                            (24,24,24),2,cv2.LINE_AA)
        writers[0].write(foreground);writers[1].write(background)
    for q in writers:q.release()
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    event={"kind":"theme_change","start":.6,"end":.601,"t":1.0,
      "evidence":"test-only genuine capture equivalent",
      "targetRect":{"x":14,"y":15,"width":60,"height":30},
      "resultRect":{"x":70,"y":75,"width":490,"height":115},
      "componentRect":{"x":70,"y":75,"width":490,"height":115}}
    planes=[{
      "id":name,"firstPairedFrame":35,
      "rect":{"x":x,"y":y,"width":w,"height":h},
      "sourceSha256":sha(source),"plateSha256":sha(clean),
      "plateFile":"plate.mp4","opaqueSurface":True,"radiusPx":0,
      "captureMethod":"playwright-visible-then-multiple-DOM-elements-hidden-and-restored"}
      for name,(x,y,w,h) in zip(("card-a","card-b"),rects)]
    m={"duration":4.0,"source":"test://synthetic-ui","cursorless":True,
       "capture_rect":{"width":W,"height":H},"events":[event],"domPlanes":planes}
    manifest=tmp_path/"capture.json"
    manifest.write_text(json.dumps(m))
    motion=[
      {"id":"card-a","eventIndex":0,"startAt":1.4,"peakAt":2.2,"endAt":3.92,
       "liftPx":50,"driftXPx":0,"scale":1.4,"heroCenter":[.3,.48]},
      {"id":"card-b","eventIndex":0,"startAt":1.8,"peakAt":2.6,"endAt":3.92,
       "liftPx":50,"driftXPx":0,"scale":1.38,"heroCenter":[.7,.48]}
    ]
    scene={"camera":[{"at":0,"scale":.8,"center":[.5,.5]},
              {"at":4.0,"scale":.67,"center":[.5,.5]}],
           "material":{"color":[17,19,24],"grain":0},
           "lighting":{"eventIndex":0,"trigger":"verified"},
           "payoff":{"region":"event:0:result","mode":"overview",
                     "minVisible":.80,"minContextVisible":.80}}
    stage=load_studio_stage(scene,m,source,(W,H),(1280,720),4.,25)
    return source,clean,manifest,m,motion,stage


def load(twin,**overrides):
    src,_,manifest,m,params,_=twin
    configs=json.loads(json.dumps(params))
    for i,values in overrides.items():
        configs[int(i)].update(values)
    return load_live_dom_planes(configs,m,src,manifest,
                                source_size=(640,360),fps=25,duration=4.0)


def test_real_matched_two_card_capture_and_screen_anchored_render(twin):
    src,clean,manifest,m,params,stage=twin
    group=load(twin)
    assert [x.id for x in group.members]==["card-a","card-b"]
    assert group.members[0].hero_center==(.3,.48)
    assert group.members[0].source_sha256==hashlib.sha256(src.read_bytes()).hexdigest()
    assert group.members[1].plate_sha256==group.members[0].plate_sha256
    assert group.active(2.5) and not group.active(.4)
    assert verify_source_relative_material(group,stage,src)["sourceRelativeSeparationVerified"]
    assert verify_group_projected_visibility(stage,group)["realHeroFramesChecked"]>40
    a=cv2.VideoCapture(str(src));b=cv2.VideoCapture(str(clean))
    a.set(cv2.CAP_PROP_POS_FRAMES,65);b.set(cv2.CAP_PROP_POS_FRAMES,65)
    ok,original=a.read();ok2,plate=b.read();a.release();b.release()
    assert ok and ok2
    result=render_live_dom_planes(stage,original,plate,group,65/25)
    assert result.shape==(720,1280,3)
    baseline=render_studio_stage(stage,original,65/25)
    assert float(np.mean(cv2.absdiff(result,baseline)))>1
    # Non-active periods remain pixel-for-pixel the old single browser stage.
    assert np.array_equal(render_live_dom_planes(stage,original,plate,group,.3),
                          render_studio_stage(stage,original,.3))
    assert np.array_equal(render_live_dom_planes(stage,original,plate,group,3.98),
                          render_studio_stage(stage,original,3.98))


def test_group_requires_exact_real_capture_set_and_same_hashed_plate(twin):
    src,clean,manifest,m,plans,stage=twin
    configs=json.loads(json.dumps(plans))
    with pytest.raises(ValueError,match="two or three"):
        load_live_dom_planes(configs[:1],m,src,manifest,
                             source_size=(640,360),fps=25,duration=4)
    configs[1]["id"]="not-a-card"
    with pytest.raises(ValueError,match="ALL genuine"):
        load_live_dom_planes(configs,m,src,manifest,
                             source_size=(640,360),fps=25,duration=4)
    bad=json.loads(json.dumps(m));bad["domPlanes"][1]["plateSha256"]="0"*64
    with pytest.raises(ValueError,match="one synchronized clean plate"):
        load_live_dom_planes(plans,bad,src,manifest,
                             source_size=(640,360),fps=25,duration=4)
    bad=json.loads(json.dumps(m))
    bad["domPlanes"][1]["rect"]=bad["domPlanes"][0]["rect"]
    with pytest.raises(ValueError,match="Overlapping"):
        load_live_dom_planes(plans,bad,src,manifest,
                             source_size=(640,360),fps=25,duration=4)


def test_forged_plate_and_unrelated_pixels_fail_closed(twin):
    src,clean,manifest,m,plans,stage=twin
    m2=json.loads(json.dumps(m))
    m2["domPlanes"][1]["captureMethod"]="inpainted"
    with pytest.raises(ValueError,match="provenance"):
        load_live_dom_planes(plans,m2,src,manifest,
                             source_size=(640,360),fps=25,duration=4)
    contents=clean.read_bytes()
    try:
        clean.write_bytes(contents+b"TAMPERED")
        with pytest.raises(ValueError,match="hashes differ"):
            load(twin)
    finally:clean.write_bytes(contents)
    original=np.zeros((360,640,3),np.uint8)+50
    back=original.copy()
    back[:20,:20]=240
    with pytest.raises(ValueError,match="outside independently hidden"):
        check_multi_pair_video_frames(original,back,[(70,75,210,115),
                                                     (350,75,210,115)])


def test_hero_requires_real_foreground_and_protects_visible_subject(twin):
    src,clean,manifest,m,plans,stage=twin
    with pytest.raises(ValueError,match="scale"):
        load(twin,**{"0":{"heroCenter":None,"scale":1.4}})
    with pytest.raises(ValueError,match="heroCenter"):
        load(twin,**{"0":{"heroCenter":[.95,.6]}})
    # The group camera/source geometry rejects hero cards placed partially offscreen.
    group=load(twin,**{"0":{"heroCenter":[.86,.7],"scale":1.55,"driftXPx":120}})
    with pytest.raises(ValueError,match="clipped|obscure"):
        verify_group_projected_visibility(stage,group)
    from dataclasses import replace
    pale=replace(stage,color=(245,245,245))
    with pytest.raises(ValueError,match="separation fails"):
        verify_source_relative_material(load(twin),pale,src)


def test_director_advertises_real_verified_group_and_refuses_forged_one(twin):
    from film_director_capabilities import build_contract
    src,clean,manifest,m,plans,stage=twin
    packet=build_contract(src,manifest,"A premium real multi-layer source UI film")
    group=packet["actualCapture"]["verifiedLiveDomPlaneGroup"]
    assert group is not None
    assert group["ids"]==["card-a","card-b"]
    assert group["firstPairedNativeFrame"]==35
    assert group["sourceTrueScreenAnchoredHeroAvailable"] is True
    assert "domPlanes" in packet["availableEffects"]
    assert group["cleanPlateSha256"]==hashlib.sha256(clean.read_bytes()).hexdigest()
    bad=json.loads(json.dumps(m));bad["domPlanes"][0]["sourceSha256"]="0"*64
    untrusted=manifest.parent/"forged.json"
    untrusted.write_text(json.dumps(bad))
    contract=build_contract(src,untrusted,"A premium real multi-layer source UI film")
    assert contract["actualCapture"]["verifiedLiveDomPlaneGroup"] is None
    assert "domPlanes" not in contract["availableEffects"]


def test_real_chromium_multiple_opaque_cards_are_original_dom_pixels(tmp_path):
    from playwright.async_api import async_playwright
    binary="/opt/devmcp-browsers/chromium_headless_shell-1254/chrome-headless-shell-linux64/chrome-headless-shell"
    if not Path(binary).is_file():
        pytest.skip("Private DevMCP browser not configured")
    async def perform():
        async with async_playwright() as p:
            browser=await p.chromium.launch(headless=True,
                executable_path=binary,args=["--no-sandbox"])
            ctx=await browser.new_context(viewport={"width":640,"height":360},
                                         device_scale_factor=1)
            page=await ctx.new_page()
            await page.set_content("""<body style="background:rgb(10,11,13)">
              <article style="position:absolute;left:40px;top:85px;width:220px;height:145px;
                             background:rgb(255,255,255);border:1px solid black">
                  <h3>Genuine test card A</h3></article>
              <article style="position:absolute;left:360px;top:85px;width:220px;height:145px;
                             background:rgb(250,250,250);border:1px solid black">
                  <h3>Genuine test card B</h3></article></body>""")
            boxes=[await loc.bounding_box() for loc in (
                 page.locator("article").nth(0),
                 page.locator("article").nth(1))]
            found=await discover_verified_dom_planes(page,boxes)
            assert found and len(found)==2
            pair=await capture_multi_pair(page,[x["selector"] for x in found],
                                          expected_native_size=(640,360))
            assert len(pair.layers)==2
            assert pair.outside_fraction<.00008
            assert all(item["changedFraction"]>.012 for item in pair.layers)
            assert await page.locator("article:visible").count()==2
            assert await page.evaluate("window.__sauceMultiCapture===undefined")
            assert check_multi_pair(pair.visible,pair.clean,
                    [p["rect"] for p in pair.layers])[0]<.00008
            await page.locator("article").nth(1).evaluate(
                "(e)=>e.style.background='transparent'")
            with pytest.raises(ValueError,match="opaque"):
                await capture_multi_pair(page,[x["selector"] for x in found],
                                         expected_native_size=(640,360))
            await browser.close()
    asyncio.run(perform())


def test_generic_source_relative_hero_depth_rejects_flat_staging(twin):
    """Two verified actual UI foreground planes require visible spatial separation."""
    from source_director_preflight import preflight_source_edit
    src,plate,manifest,m,params,_=twin
    plan={
        "durationSeconds":4.0,
        "studioStage":{
          "camera":[{"at":0,"scale":.90,"center":[.5,.5]},
                    {"at":4.0,"scale":.90,"center":[.5,.5]}],
          "lighting":{"eventIndex":0,"trigger":"verified"},
          "payoff":{"region":"event:0:result","mode":"overview",
                    "minVisible":.80,"minContextVisible":.80},
          "material":{"color":[16,17,22]}
        },
        "domPlanes":params,
        "audio":{"mode":"eventFoley","eventIndex":0,
                 "clickGain":.4,"motionGain":.2,"masterGain":.5}
    }
    report=preflight_source_edit(plan,m,src,(640,360),25,output_size=(1280,720))
    assert report["verdict"]=="REJECT"
    assert [x["code"] for x in report["findings"]]==["FLAT_FOREGROUND_HIERARCHY"]
    assert report["observations"]["heroSourceWindowAreaFraction"]>.62
    # No source UI edited. Only model's original camera scale is revised:
    # the *same* source cards remain hero-anchored at the *same* positions.
    plan["studioStage"]["camera"][0]["scale"]=.58
    plan["studioStage"]["camera"][1]["scale"]=.58
    accepted=preflight_source_edit(plan,m,src,(640,360),25,
                                   output_size=(1280,720))
    assert not accepted["findings"]
    assert accepted["verdict"]=="GEOMETRY_AND_AUDIO_PREFLIGHT_PASS"
    assert accepted["observations"]["heroSourceWindowAreaFraction"]<.62
    assert accepted["creativeApproved"] is False


def test_bounded_source_true_hero_compiler_preserves_card_size_and_rejects_collision(twin):
    """No authored website selectors/timing. Real capture proves card arrangement."""
    import copy
    from source_hero_choreography import (
        audit_hero_scene,fit_source_hero_choreography)
    from source_director_preflight import preflight_source_edit
    src,plate,manifest,m,layers,_=twin
    model={
      "schema":"sauce-film-plan-v1",
      "durationSeconds":4.0,
      "presentation":"fullscreen",
      "studioStage":{
        "camera":[{"at":0,"scale":.9,"center":[.5,.5]},
                  {"at":4.0,"scale":.9,"center":[.5,.5]}],
        "material":{"color":[18,19,24]},
        "lighting":{"eventIndex":0,"trigger":"verified"},
        "payoff":{"region":"event:0:result","mode":"overview",
                  "minVisible":.80,"minContextVisible":.80}
      },
      "audio":{"mode":"eventFoley","eventIndex":0,
               "clickGain":.4,"motionGain":.2,"masterGain":.5},
      "domPlanes":copy.deepcopy(layers)
    }
    for i,x in enumerate(model["domPlanes"]):
        x["heroCenter"]=[.35,.48] if i==0 else [.65,.48]
    initial=copy.deepcopy(model)
    bad=preflight_source_edit(model,m,src,(640,360),25,
                              output_size=(1280,720),manifest_path=manifest)
    assert bad["verdict"]=="REJECT"
    assert "FLAT_FOREGROUND_HIERARCHY" in [x["code"] for x in bad["findings"]]
    repaired,changes=fit_source_hero_choreography(
        model,m,src,manifest,(640,360),25,output_size=(1280,720))
    assert model==initial
    assert changes
    assert len(repaired["studioStage"]["camera"])==3
    assert any("studioStage.camera[1]" in c["field"] for c in changes)
    assert len([c for c in changes if c["field"].endswith("heroCenter")])==2
    assert repaired["domPlanes"][0]["scale"]==initial["domPlanes"][0]["scale"]
    assert repaired["domPlanes"][1]["scale"]==initial["domPlanes"][1]["scale"]
    assert repaired["domPlanes"][0]["startAt"]==initial["domPlanes"][0]["startAt"]
    assert repaired["domPlanes"][1]["endAt"]==initial["domPlanes"][1]["endAt"]
    assert repaired["studioStage"]["camera"][0]==initial["studioStage"]["camera"][0]
    assert repaired["studioStage"]["camera"][-1]["at"]==4.0
    assert repaired["audio"]==initial["audio"]
    after=preflight_source_edit(repaired,m,src,(640,360),25,
                                output_size=(1280,720),manifest_path=manifest)
    assert after["verdict"]=="GEOMETRY_AND_AUDIO_PREFLIGHT_PASS"
    assert after["observations"]["sourceTrueForegroundGutterPx"]>=48
    assert after["observations"]["heroSourceWindowAreaFraction"]<=.62
    assert after["creativeApproved"] is False
    a=audit_hero_scene(repaired,m,src,manifest,(640,360),25,
                       output_size=(1280,720))
    assert a["gutter"]["pixels"]>=48


def test_tampered_chromium_pair_cannot_be_scene_compiled(twin):
    """A false hidden background is NEVER authorized by the creative compiler."""
    import copy
    from source_hero_choreography import fit_source_hero_choreography
    src,plate,manifest,m,layers,_=twin
    bad=copy.deepcopy(m);bad["domPlanes"][0]["plateSha256"]="0"*64
    plan={
      "durationSeconds":4.0,"presentation":"fullscreen",
      "studioStage":{
        "camera":[{"at":0,"scale":.8,"center":[.5,.5]},
                  {"at":4.0,"scale":.8,"center":[.5,.5]}],
        "lighting":{"eventIndex":0},
        "payoff":{"region":"event:0:result","minVisible":.75}
      },
      "domPlanes":copy.deepcopy(layers)
    }
    untouched=copy.deepcopy(plan)
    output,changes=fit_source_hero_choreography(
       plan,bad,src,manifest,(640,360),25,output_size=(1280,720))
    assert output==untouched
    assert changes==[]
    assert plan==untouched


def test_unattended_model_plan_compiles_source_true_hero_cinema(
        twin,tmp_path,monkeypatch):
    """Provider supplies ONLY original creative JSON; engine arranges genuine UI."""
    import hashlib
    import auto_direct_studio_film as runner
    import quality_preview_supervisor as qa
    src,plate,manifest,m,layers,_=twin
    model={
      "schema":"sauce-film-plan-v1",
      "sourceSha256":hashlib.sha256(src.read_bytes()).hexdigest(),
      "manifestSha256":hashlib.sha256(manifest.read_bytes()).hexdigest(),
      "durationSeconds":4.,
      "presentation":"fullscreen",
      "cursor":"none",
      "studioStage":{
        "camera":[{"at":0,"scale":.9,"center":[.5,.5]},
                  {"at":4.,"scale":.9,"center":[.5,.5]}],
        "material":{"color":[20,22,24],"grain":0},
        "lighting":{"eventIndex":0,"trigger":"verified"},
        "payoff":{"region":"event:0:result","mode":"overview",
                  "minVisible":.8,"minContextVisible":.8}
      },
      "audio":{"mode":"eventFoley","eventIndex":0,
              "clickGain":.4,"motionGain":.2,"masterGain":.5},
      "domPlanes":json.loads(json.dumps(layers))
    }
    model["domPlanes"][0]["heroCenter"]=[.35,.48]
    model["domPlanes"][1]["heroCenter"]=[.65,.48]
    def actual_fake_model(source,packet,model_name,key,feedback):
        assert feedback is None
        assert packet["actualCapture"]["verifiedLiveDomPlaneGroup"]
        return json.dumps(model),{"usageMetadata":{"totalTokenCount":87}}
    def validator(source,manifest_path,plan_path,output_dir):
        plan=json.loads(plan_path.read_text())
        assert len(plan["studioStage"]["camera"])==3
        assert plan["domPlanes"][0]["heroCenter"][0]<.35
        assert plan["domPlanes"][1]["heroCenter"][0]>.65
        return True,"source-time camera and genuine pair verified"
    original_run=runner.subprocess.run
    def render(cmd,**kwargs):
        if "--output" not in cmd:return original_run(cmd,**kwargs)
        Path(cmd[cmd.index("--output")+1]).write_bytes(b"source-verified-local-demo")
        from subprocess import CompletedProcess
        return CompletedProcess(cmd,0,stdout="rendered")
    monkeypatch.setattr(runner.subprocess,"run",render)
    monkeypatch.setattr(qa,"analyze",
                        lambda *args,**kwargs:{
                            "verdict":"HUMAN_REVIEW_REQUIRED","findings":[]})
    receipt=runner.run_unattended(
       src,manifest,"A real cinematic source product film",tmp_path/"private",
       model="gemini-3-flash-preview",key="test-only",
       max_attempts=1,model_call=actual_fake_model,
       validator=validator,render=True)
    assert receipt["outcome"]=="needs_review"
    assert receipt["creativeApproved"] is False
    assert receipt["attempts"][0]["editorialPreflightFindings"]==[]
    assert receipt["attempts"][0]["editorialPreflightVerdict"]=="GEOMETRY_AND_AUDIO_PREFLIGHT_PASS"
    evidence=receipt["attempts"][0]["mechanicalChanges"]
    assert any(c["field"].startswith("studioStage.camera[1]") for c in evidence)
    assert len([c for c in evidence if c["field"].endswith("heroCenter")])==2
    report=json.loads((tmp_path/"private"/"editorial-preflight-1.json").read_text())
    assert report["observations"]["sourceTrueForegroundGutterPx"]>=48
    assert report["observations"]["heroSourceWindowAreaFraction"]<=.62
    assert (tmp_path/"private"/"model-1-original.json").is_file()
    assert (tmp_path/"private"/"model-1-mechanical-repair.json").is_file()
