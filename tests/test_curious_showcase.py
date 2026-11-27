import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from backend.curious_showcase import Conversation, checked_plan, direct, review, prefer_revision
from backend.url_engine import direction


class CuriousShowcaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        shot = self.root / "public.jpg"
        shot.write_bytes(b"public screenshot fixture")
        self.report = {"url": "https://example.com/", "title": "Example", "controls": [],
                       "screenshot": str(shot), "height": 4100, "headings": [
            {"id":"h0","tag":"h1","text":"A useful product","y":100,"selector":"#hero"},
            {"id":"h1","tag":"h2","text":"How it works","y":950,"selector":"#workflow"},
            {"id":"h2","tag":"h2","text":"Features","y":2100,"selector":"#features"},
            {"id":"h3","tag":"h2","text":"Pricing","y":3100,"selector":"#pricing"}]}

    def test_validated_pacing_and_ids_only(self):
        good = checked_plan({"heading_ids":["h2","h1"],"pace":"brisk",
                             "action_ids":["invented"]}, self.report)
        self.assertEqual(good["heading_ids"], ["h1","h2"])
        self.assertEqual(good["action_ids"], [])
        self.assertEqual(good["showcase_pace"], "brisk")
        for ids in (["h1","invented"], ["h1","h3"], ["h1","h1"], ["h0","h2"]):
            self.assertIsNone(checked_plan({"heading_ids":ids,"pace":"brisk"},self.report))
        self.assertIsNone(checked_plan({"heading_ids":["h1","h2"],"pace":"arbitrary"},self.report))
        self.assertIsNone(checked_plan({"heading_ids":["h1","h2"],"pace":[]},self.report))

    def test_actual_followup_contains_previous_answer_and_recovers_without_rebilling(self):
        calls = []
        def transport(_, model, contents, json_mode):
            calls.append((model, contents, json_mode))
            if len(calls) == 1:
                return "The workflow is more meaningful than the pricing section.", {"totalTokenCount":20}
            return json.dumps({"heading_ids":["h1","h2"],"pace":"readable"}), {"totalTokenCount":30}
        with patch.object(Conversation,"_request",transport):
            plan,n = direct(self.report,self.root/"conversation")
            again,n2 = direct(self.report,self.root/"conversation")
        self.assertEqual((n,n2,len(calls)), (2,2,2))
        self.assertEqual(plan,again)
        self.assertEqual([row["role"] for row in calls[1][1]], ["user","model","user"])
        self.assertIn("workflow is more meaningful",calls[1][1][1]["parts"][0]["text"])
        self.assertEqual(plan["showcase_pace"],"readable")

    def test_outage_retains_honest_deterministic_fallback(self):
        def fail(*args):
            raise HTTPError("https://example.com",503,"unavailable",{},None)
        with patch.dict(os.environ,{"GEMINI_API_KEY":"fixture","SAUCE_DIRECTOR_MODEL":"gemini-3.1-flash-lite","SAUCE_CURIOUS_FALLBACK_MODEL":"gemini-3.5-flash-lite"}),patch.object(Conversation,"_request",fail):
            plan,n,source=direction(self.report,curiosity_dir=self.root/"failure")
        self.assertEqual((source,n),("provider-or-plan-fallback",2))
        self.assertEqual(plan["heading_ids"],["h1","h2"])
        conv=Conversation(self.root/"failure")
        self.assertFalse(conv.succeeded)
        self.assertEqual([a["http_status"] for a in conv.data["attempts"]],[503,503])

    def test_review_attaches_exact_encoded_video_and_retains_history(self):
        calls=[]
        def transport(_,model,contents,json_mode):
            calls.append(contents)
            if len(calls)==1:return "Explore the workflow.",{}
            return json.dumps({"heading_ids":["h1","h2"],"pace":"balanced" if len(calls)==2 else "brisk",
                               "observations":"At 2s the workflow title holds too long."}),{}
        directory=self.root/"review"
        export=self.root/"export";export.mkdir()
        video=export/"master-1080p60.mp4";video.write_bytes(b"encoded fixture")
        (export/"release.json").write_text(json.dumps({"film_mode":"showcase","source_verified":True}))
        (export/"encoded-quality.json").write_text(json.dumps({"film_sha256":hashlib.sha256(video.read_bytes()).hexdigest(),"findings":[]}))
        with patch.object(Conversation,"_request",transport):
            plan,_=direct(self.report,directory)
            revised,n=review(self.report,plan,export,directory)
            again,n2=review(self.report,plan,export,directory)
        self.assertEqual((n,n2,len(calls)),(3,3,3))
        self.assertIsNone(again)
        self.assertEqual(revised["showcase_pace"],"brisk")
        self.assertTrue(Conversation(directory).data["review_valid"])
        self.assertEqual([x["role"] for x in calls[2]],["user","model","user","model","user"])
        self.assertEqual(calls[2][-1]["parts"][1]["inline_data"]["mime_type"],"video/mp4")

    def test_truncated_review_has_one_bounded_repair(self):
        calls=[]
        def transport(_,model,contents,json_mode):
            calls.append(contents)
            if len(calls)==1:return "Show the workflow.",{}
            if len(calls)==2:return json.dumps({"heading_ids":["h1","h2"],"pace":"balanced"}),{}
            if len(calls)==3:return '{"observations":"truncated',{"finishReason":"MAX_TOKENS"}
            return json.dumps({"observations":"At 2s the title is static.","heading_ids":["h1","h2"],"pace":"brisk"}),{}
        d=self.root/"repair"
        export=self.root/"export";export.mkdir()
        video=export/"master-1080p60.mp4";video.write_bytes(b"encoded fixture")
        (export/"release.json").write_text(json.dumps({"film_mode":"showcase","source_verified":True}))
        (export/"encoded-quality.json").write_text(json.dumps({"film_sha256":hashlib.sha256(video.read_bytes()).hexdigest(),"findings":[]}))
        with patch.object(Conversation,"_request",transport):
            plan,_=direct(self.report,d)
            revised,n=review(self.report,plan,export,d)
            again,n2=review(self.report,plan,export,d)
        self.assertEqual((n,n2,len(calls)),(4,4,4))
        self.assertIsNone(again)
        self.assertEqual(revised["showcase_pace"],"brisk")
        self.assertTrue(Conversation(d).data["review_valid"])

    def test_revision_gate_does_not_claim_approval(self):
        def qa(frac,p80,extra=()):
            return {"findings":[{"code":"REPEATED_OR_STATIC_FRAMES","detail":{"fraction":frac}},
                                {"code":"STATIC_OPENING_2S","detail":{"p80_frame_delta":p80}},
                                *[{"code":x,"detail":{}} for x in extra]]}
        self.assertTrue(prefer_revision(qa(.8,.2),qa(.7,.6)))
        self.assertFalse(prefer_revision(qa(.8,.2),qa(.7,.6,["ABRUPT_CUT_CANDIDATE"])))
        self.assertFalse(prefer_revision(qa(.8,.2),qa(.85,.1)))
        self.assertFalse(prefer_revision(qa(.8,.2),qa(.8,.2)))


if __name__=="__main__":
    unittest.main()


def test_structured_story_503_backoff_recovers_and_counts_every_request(tmp_path,monkeypatch):
    from backend.curious_showcase import Conversation
    delays=[];attempts=[]
    monkeypatch.setattr("backend.curious_showcase.time.sleep",delays.append)
    def request(model,contents,json_mode,schema):
        attempts.append((model,schema))
        if len(attempts)<3:raise HTTPError("https://example.com",503,"unavailable",{},None)
        return '{"ids":["a0"]}',{"totalTokenCount":11}
    conv=Conversation(tmp_path/"conv",request=request)
    schema={"type":"OBJECT"}
    result=conv.ask("Observed IDs",json_mode=True,phase="story-plan",response_schema=schema)
    assert result=='{"ids":["a0"]}'
    assert delays==[.75,1.5] and conv.calls==3
    assert len({x[0] for x in attempts})==1
    assert [a["status"] for a in conv.data["attempts"]]==["failed","failed","ok"]
    assert [a.get("retry_delay_seconds") for a in conv.data["attempts"]]==[.75,1.5,None]


def test_structured_story_rate_limit_is_not_retried(tmp_path,monkeypatch):
    from backend.curious_showcase import Conversation
    delays=[]
    monkeypatch.setattr("backend.curious_showcase.time.sleep",delays.append)
    def request(*args):raise HTTPError("https://example.com",429,"limited",{},None)
    conv=Conversation(tmp_path/"conv",request=request)
    assert conv.ask("Observed IDs",json_mode=True,phase="story-plan",response_schema={"type":"OBJECT"},stop_on_rate_limit=True) is None
    assert conv.calls==1 and not delays

def test_gemini_customer_wire_matches_shared_direction_and_numeric_duration(monkeypatch,tmp_path):
    import io
    from backend import curious_showcase as gemini
    from backend.claude_customer_director import system_prompt,PROMPT_VERSION
    from scripts.customer_editorial import schema,validate
    monkeypatch.setenv("GEMINI_API_KEY","fixture")
    monkeypatch.setenv("SAUCE_DIRECTOR_MODEL","gemini-3.1-flash-lite")
    ids=["x","y"]
    reply={"accept":True,"reason":"Witnessed result","backdrop":"muted","duration_seconds":13,
           "beats":[{"action_id":x,"framing":"wide","pace":"readable","purpose":"Observed change"} for x in ids]}
    original=schema(ids)
    calls=[]
    def transport(req,timeout):
        payload=json.loads(req.data)
        calls.append(payload)
        assert payload["system_instruction"]["parts"][0]["text"]==system_prompt("story-editorial")
        cfg=payload["generationConfig"]
        assert "responseSchema" not in cfg
        wire=cfg["responseJsonSchema"]
        assert wire["type"]=="object"
        assert wire["properties"]["duration_seconds"]=={"type":"integer","enum":[13,16,18,20]}
        assert wire["properties"]["beats"]["items"]["properties"]["action_id"]["enum"]==ids
        return io.BytesIO(json.dumps({"candidates":[{"content":{"parts":[{"text":json.dumps(reply)}]},"finishReason":"STOP"}],
          "usageMetadata":{"totalTokenCount":500}}).encode())
    monkeypatch.setattr(gemini,"urlopen",transport)
    conv=gemini.Conversation(tmp_path)
    result=json.loads(conv.ask("Observed fixture",phase="story-editorial",json_mode=True,response_schema=original))
    assert validate({k:result[k] for k in ("backdrop","duration_seconds","beats")},ids,"y")["duration_seconds"]==13
    assert conv.calls==1
    assert conv.data["attempts"][0]["creative_prompt_version"]==PROMPT_VERSION
    assert conv.data["attempts"][0]["creative_prompt_sha256"]==hashlib.sha256(system_prompt("story-editorial").encode()).hexdigest()
    assert original==schema(ids) # non-mutating transport conversion


def test_gemini_legacy_showcase_wire_is_unchanged(monkeypatch,tmp_path):
    import io
    from backend import curious_showcase as gemini
    monkeypatch.setenv("GEMINI_API_KEY","fixture")
    def transport(req,timeout):
        payload=json.loads(req.data)
        assert "system_instruction" not in payload
        assert "responseJsonSchema" not in payload["generationConfig"]
        return io.BytesIO(b'{"candidates":[{"content":{"parts":[{"text":"ok"}]}}]}')
    monkeypatch.setattr(gemini,"urlopen",transport)
    assert gemini.Conversation(tmp_path).ask("fixture",phase="explore")=="ok"
