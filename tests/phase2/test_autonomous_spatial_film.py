"""Authentic-plate-only autonomous spatial motion tests. No production URL calls."""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from autonomous_spatial_film import STYLES,create_plan,run


def _case(tmp_path):
 source=tmp_path/"source.mp4"
 source.write_bytes(b"test-only source movie")
 manifest=tmp_path/"events.json"
 original={"source":"https://example.org/demo","duration":3.5,
  "cursorless":True,"events":[{"kind":"click","start":.5,"end":.51,
   "t":.92,"evidence":"Test fixture real browser result",
   "targetRect":{"x":150,"y":200,"width":100,"height":30},
   "resultRect":{"x":290,"y":100,"width":320,"height":125}}],
  "domPlanes":[{"id":"original-a"},{"id":"original-b"}]}
 manifest.write_text(json.dumps(original))
 h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 packet={"actualCapture":{"sourceSha256":h(source),
  "manifestSha256":h(manifest),"nativeFps":60.,"durationSeconds":3.5,
  "resolution":[640,360],"pointerProvenance":{
    "recordedPointerTrackAvailable":True},
  "verifiedEvents":[{"index":0,"sourceTime":{
     "start":.5,"confirmedResultAt":.92}}],
  "verifiedLiveDomPlaneGroup":{"ids":["original-a","original-b"],
    "measuredNativeSourceRects":[[290,100,145,125],[450,100,145,125]],
    "verifiedEventIndex":0,"firstPairedNativeFrame":90,
    "earliestMotionAtSeconds":1.5,
    "latestMotionEndSeconds":3.4833333333333334,
    "verifiedSynchronizedSameBrowserFrames":True}}}
 return source,manifest,packet


def test_derived_hero_motion_uses_only_actual_source_ids_and_native_clock(tmp_path):
 source,manifest,packet=_case(tmp_path)
 for style in STYLES:
  result=create_plan(source,manifest,packet,style)
  assert result["schema"]=="sauce-film-plan-v1"
  assert result["sourceSha256"]==packet["actualCapture"]["sourceSha256"]
  assert [p["id"] for p in result["domPlanes"]]==["original-a","original-b"]
  assert all(k["at"]<=3.5 for k in result["studioStage"]["camera"])
  assert all(p["startAt"]>=1.5 for p in result["domPlanes"])
  assert all(p["peakAt"]-p["startAt"]>=.35 for p in result["domPlanes"])
  assert all(p["endAt"]-p["peakAt"]>=.9 for p in result["domPlanes"])
  assert all(abs(p[time]*60-round(p[time]*60))<1e-6
             for p in result["domPlanes"] for time in ("startAt","peakAt","endAt"))
  assert len(result["domPlanes"])==2
  assert result["cursor"]=="recorded"
  assert result["audio"]["eventIndices"]==[0]


def test_never_fabricate_missing_or_unsigned_clean_plate(tmp_path):
 source,manifest,packet=_case(tmp_path)
 packet["actualCapture"]["verifiedLiveDomPlaneGroup"]=None
 with pytest.raises(ValueError,match="Cannot invent"):
  create_plan(source,manifest,packet,STYLES[0])
 packet["actualCapture"]["verifiedLiveDomPlaneGroup"]={
   "verifiedSynchronizedSameBrowserFrames":False}
 with pytest.raises(ValueError,match="Cannot invent"):
  create_plan(source,manifest,packet,STYLES[0])


def test_changed_source_and_manifest_rejected_before_work(tmp_path):
 source,manifest,packet=_case(tmp_path)
 source.write_bytes(b"altered browser movie")
 with pytest.raises(ValueError,match="Changed source"):
  create_plan(source,manifest,packet,STYLES[0])
 out=tmp_path/"original"
 with pytest.raises(ValueError,match="SHA256"):
  run(source,manifest,out,expected_source_sha256="0"*64,render=False)
 assert not out.exists()
 out.mkdir();(out/"prior-film.mp4").write_bytes(b"do not overwrite")
 with pytest.raises(ValueError,match="overwrite"):
  run(source,manifest,out,render=False)
 assert (out/"prior-film.mp4").read_bytes()==b"do not overwrite"


def test_unsupported_source_fails_closed_without_model_or_fake_layer(tmp_path,monkeypatch):
 import autonomous_spatial_film as spatial
 source,manifest,packet=_case(tmp_path)
 packet["actualCapture"]["verifiedLiveDomPlaneGroup"]=None
 monkeypatch.setattr(spatial,"build_contract",lambda *args:packet)
 out=tmp_path/"run"
 result=run(source,manifest,out,render=False)
 assert result["status"]=="no_authentic_paired_layers"
 assert result["modelCalls"]==0
 assert result["selected"] is None
 assert result["creativeApproved"] is False
 assert not list(out.glob("*-plan.json"))


def test_owner_pipeline_selects_spatial_only_with_independently_verified_plate(tmp_path,monkeypatch):
 import auto_public_ui_film as wrapper
 import autonomous_spatial_film as spatial
 monkeypatch.setattr(wrapper,"validate_public_url",lambda url:url)
 old=tmp_path/"existing";old.mkdir()
 for name in ("source-real-dpr2-60.mp4","source-events.json"):
  (old/name).write_bytes(b"private real browser fixture")
 (old/"discovery.json").write_text(json.dumps({
   "url":"https://example.org/demo","host":"example.org"}))
 monkeypatch.setattr(wrapper,"normalize",lambda *args:{
   "source":"https://example.org/demo","events":[],
   "cursorless":True})
 monkeypatch.setattr(wrapper,"build_contract",lambda *args:{
   "actualCapture":{"sourceSha256":"some-source-hash",
    "manifestSha256":"some-sidecar-hash",
    "verifiedEvents":[],"verifiedLiveDomPlaneGroup":{
      "verifiedSynchronizedSameBrowserFrames":True}}})
 calls=[]
 def fake_run(src,manifest,out,**kwargs):
  calls.append(kwargs)
  return {"status":"needs_human_review","candidates":[{
    "status":"rendered_needs_human_review",
    "film":str(tmp_path/"fake-film-from-mocked-test.mp4"),
    "filmSha256":"fake-mocked-test-digest"}]}
 monkeypatch.setattr(spatial,"run",fake_run)
 result=wrapper.run("https://example.org/demo","example.org",
                    tmp_path/"output",from_capture=old,
                    director_mode="coverage",key=None)
 assert len(calls)==1
 assert calls[0]["expected_source_sha256"]=="some-source-hash"
 assert calls[0]["expected_manifest_sha256"]=="some-sidecar-hash"
 assert result["directorMode"]=="source_true_verified_spatial"
 assert result["providerAttemptCount"]==0
 assert result["creativeApproved"] is False
 assert result["productionReady"] is False
 assert result["noAutoPublication"] is True



def test_existing_paired_capture_input_selects_spatial_without_model(tmp_path,monkeypatch):
 import auto_public_ui_film as wrapper
 import autonomous_spatial_film as spatial
 monkeypatch.setattr(wrapper,"validate_public_url",lambda url:url)
 paired=tmp_path/"paired";paired.mkdir()
 (paired/"source.mp4").write_bytes(b"test-only-paired-source")
 (paired/"capture.json").write_text(json.dumps({
  "source":"https://example.org/demo","domPlanes":[{"id":"actual-captured-a"},
      {"id":"actual-captured-b"}]}))
 packet={"actualCapture":{"sourceSha256":"real-source-hash-test",
   "manifestSha256":"real-plate-manifest-hash-test",
   "verifiedEvents":[{"index":0,"sourceTime":{"start":.5,"confirmedResultAt":.9}}],
   "verifiedLiveDomPlaneGroup":{
     "verifiedSynchronizedSameBrowserFrames":True,"ids":["actual-captured-a","actual-captured-b"]}}}
 monkeypatch.setattr(wrapper,"build_contract",lambda *args:packet)
 calls=[]
 def fake_run(source,manifest,out,**kwargs):
  calls.append((source,manifest,kwargs))
  return {"status":"needs_human_review","candidates":[{
    "name":"composed","status":"rendered_needs_human_review",
    "film":str(tmp_path/"mocked-not-an-actual-mp4.mp4"),
    "filmSha256":"test-only-mock"}]}
 monkeypatch.setattr(spatial,"run",fake_run)
 receipt=wrapper.run("https://example.org/demo","example.org",
    tmp_path/"out",from_paired_capture=paired,director_mode="coverage",key=None)
 assert len(calls)==1
 assert calls[0][0]==paired/"source.mp4"
 assert calls[0][1]==paired/"capture.json"
 assert calls[0][2]["expected_source_sha256"]=="real-source-hash-test"
 assert receipt["directorMode"]=="source_true_verified_spatial"
 assert receipt["providerAttemptCount"]==0
 assert receipt["filmSha256"]=="test-only-mock"
 assert receipt["creativeApproved"] is False
 assert receipt["noAutoPublication"] is True
 assert receipt["productionReady"] is False


def test_paired_capture_cannot_relabel_site_or_invent_missing_plate(tmp_path,monkeypatch):
 import auto_public_ui_film as wrapper
 monkeypatch.setattr(wrapper,"validate_public_url",lambda url:url)
 paired=tmp_path/"pair";paired.mkdir()
 (paired/"source.mp4").write_bytes(b"fixture")
 (paired/"capture.json").write_text(json.dumps({
  "source":"https://example.org/demo","domPlanes":[{"id":"a"},{"id":"b"}]}))
 out=tmp_path/"out"
 with pytest.raises(ValueError,match="contradicts"):
  wrapper.run("https://example.org/other","example.org",out,
              from_paired_capture=paired,director_mode="coverage")
 assert not (out/"evidence-receipt.json").exists()
 with pytest.raises(ValueError,match="requires coverage"):
  wrapper.run("https://example.org/demo","example.org",
              tmp_path/"other",from_paired_capture=paired,director_mode="gemini")
 with pytest.raises(ValueError,match="exactly one"):
  wrapper.run("https://example.org/demo","example.org",
              tmp_path/"conflict",from_capture=paired,
              from_paired_capture=paired,director_mode="coverage")
 monkeypatch.setattr(wrapper,"build_contract",lambda *args:{
   "actualCapture":{"sourceSha256":"a","manifestSha256":"b",
      "verifiedEvents":[],"verifiedLiveDomPlaneGroup":None}})
 with pytest.raises(ValueError,match="failed verification"):
  wrapper.run("https://example.org/demo","example.org",tmp_path/"fake",
              from_paired_capture=paired,director_mode="coverage")
 assert not (tmp_path/"fake"/"evidence-receipt.json").exists()
