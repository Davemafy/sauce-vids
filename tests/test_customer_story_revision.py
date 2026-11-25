import json
from unittest.mock import Mock
from backend.customer_story import sha,save
from backend.customer_story_revision import revise

def baseline(tmp):
    d=tmp/"export";d.mkdir();p=d/"master-1080p60.mp4";p.write_bytes(b'baseline')
    (tmp/"private").mkdir()
    r={"film_sha256":sha(p),"source_sha256":"old","source_verified":True,"creative_approved":False,
       "encoded_quality_verdict":"REJECT","encoded_quality_responsibility":{"technical":[]},
       "encoded_quality_findings":["STATIC_OPENING_2S"],
       "encoded_editorial":{"decision":"reject","model_reviewed":True,"film_sha256":sha(p),"observations":"repetitive opening"}}
    save(d/"release.json",r);return r,p

def test_fresh_revision_never_replaces_baseline(tmp_path):
    r,p=baseline(tmp_path)
    def run(url,folder,progress,*,audio,brief):
        assert url=="https://example.com" and "repetitive opening" in brief
        assert not (folder/"export").exists()
        d=folder/"export";d.mkdir();v=d/"master-1080p60.mp4";v.write_bytes(b'fresh')
        save(d/"release.json",{**r,"film_sha256":sha(v),"source_sha256":"fresh",
             "encoded_quality_verdict":"HUMAN_REVIEW_REQUIRED","encoded_editorial":{"film_sha256":sha(v),
             "model_reviewed":True,"decision":"keep","retained_for_human_review":True}})
        return {"ai_calls":3}
    call=Mock(side_effect=run)
    a=revise("https://example.com",tmp_path,{},lambda _:None,"auto","",call)
    assert a["selected"]=="private-candidate-for-owner-review" and not a["creative_approved"]
    assert p.read_bytes()==b'baseline'
    assert revise("https://example.com",tmp_path,{},lambda _:None,"auto","",call)==a
    call.assert_called_once()

def test_no_revision_without_model_rejection(tmp_path):
    r,p=baseline(tmp_path);r["encoded_editorial"]["decision"]="keep"
    save(tmp_path/"export"/"release.json",r);call=Mock()
    assert revise("https://example.com",tmp_path,{},lambda _:None,"auto","",call)["status"]=="not-eligible"
    call.assert_not_called()

def test_interrupted_revision_no_duplicate_calls(tmp_path):
    baseline(tmp_path);(tmp_path/"private"/"customer-story-revision").mkdir()
    call=Mock()
    assert revise("https://example.com",tmp_path,{},lambda _:None,"auto","",call)["status"]=="interrupted-revision"
    call.assert_not_called()

def test_render_timeout_keeps_baseline(tmp_path):
    import subprocess
    r,p=baseline(tmp_path)
    call=Mock(side_effect=subprocess.TimeoutExpired("renderer",1))
    a=revise("https://example.com",tmp_path,{},lambda _:None,"auto","",call)
    assert a["status"]=="revision-failed" and a["selected"] is None
    assert p.read_bytes()==b'baseline'
    assert revise("https://example.com",tmp_path,{},lambda _:None,"auto","",call)==a
    call.assert_called_once()
