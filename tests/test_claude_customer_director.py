import io
import json

from backend import claude_customer_director as claude
from backend.customer_story import story_response_schema, validated_selection


def test_claude_uses_customer_screenshots_catalog_schema_and_usage(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    catalog = [{"id": f"a{i}", "kind": "option", "label": str(i)} for i in range(3)]
    reply = {"ids": ["a0", "a1", "a2"], "hero_action_id": "a1", "story": "Proven payoff"}

    def request(req, timeout):
        assert req.full_url == "https://api.anthropic.com/v1/messages"
        assert timeout == 40
        payload = json.loads(req.data)
        assert payload["model"] == "claude-sonnet-5-5"
        assert payload["messages"][0]["content"][1]["source"]["media_type"] == "image/png"
        schema = payload["output_config"]["format"]["schema"]
        assert schema["properties"]["hero_action_id"]["enum"] == ["a0", "a1", "a2", ""]
        assert schema["additionalProperties"] is False
        return io.BytesIO(json.dumps({
            "content": [{"type": "text", "text": json.dumps(reply)}], "stop_reason": "end_turn",
            "usage": {"input_tokens": 900, "output_tokens": 40},
        }).encode())

    monkeypatch.setattr(claude, "urlopen", request)
    conversation = claude.ClaudeConversation(tmp_path)
    result = conversation.ask("Choose a hero.", media=({"inline_data": {
        "mime_type": "image/png", "data": "aW1hZ2U="}},), json_mode=True,
        phase="story-from-outcomes", response_schema=story_response_schema(catalog))
    assert validated_selection(result, catalog)["hero_action_id"] == "a1"
    assert conversation.data["attempts"][0]["usage"]["totalTokenCount"] == 940


def test_claude_missing_key_is_explicit_before_browser(monkeypatch,tmp_path):
    import pytest
    from backend.customer_story import explore
    from backend.url2video import NeedsKey
    monkeypatch.setenv('SAUCE_CUSTOMER_DIRECTOR_PROVIDER','claude')
    monkeypatch.delenv('ANTHROPIC_API_KEY',raising=False)
    with pytest.raises(NeedsKey,match='ANTHROPIC_API_KEY'):
        explore('https://example.com',tmp_path/'story',lambda _:None)


def test_claude_malformed_reply_usage_is_retained(monkeypatch,tmp_path):
    monkeypatch.setenv('ANTHROPIC_API_KEY','fixture')
    monkeypatch.setattr(claude,'urlopen',lambda req,timeout:io.BytesIO(json.dumps({
        'content':[{'type':'text','text':'not JSON'}],'stop_reason':'end_turn',
        'usage':{'input_tokens':100,'output_tokens':4}}).encode()))
    c=claude.ClaudeConversation(tmp_path)
    raw=c.ask('Select only observed IDs',phase='story-picker',json_mode=True)
    assert raw=='not JSON'
    assert c.data['attempts'][0]['usage']['totalTokenCount']==104
    assert validated_selection(raw,[]) is None


def test_motion_direction_is_in_actual_outbound_requests_and_pinned(monkeypatch,tmp_path):
    import hashlib
    monkeypatch.setenv("ANTHROPIC_API_KEY","fixture")
    payloads=[]
    def request(req,timeout):
        payloads.append(json.loads(req.data))
        return io.BytesIO(json.dumps({
            "content":[{"type":"text","text":"{}"}],"stop_reason":"end_turn",
            "usage":{"input_tokens":900,"output_tokens":4}}).encode())
    monkeypatch.setattr(claude,"urlopen",request)
    c=claude.ClaudeConversation(tmp_path)
    for phase in ("story-picker","story-from-outcomes","story-editorial"):
        c.ask("Observed fixture",phase=phase,json_mode=True)
    assert c.calls==len(payloads)==3
    for attempt,payload in zip(c.data["attempts"],payloads):
        assert "Motion-design judgment:" in payload["system"]
        assert "NOT approved production exemplars" in payload["system"]
        assert claude.PHASE_GUIDANCE[attempt["phase"]] in payload["system"]
        assert attempt["creative_prompt_version"]==claude.PROMPT_VERSION
        assert attempt["creative_prompt_sha256"]==hashlib.sha256(payload["system"].encode()).hexdigest()
    assert len({x["creative_prompt_sha256"] for x in c.data["attempts"]})==3
    assert "Current assignment:" not in payloads[-1]["messages"][0]["content"][0]["text"]


def test_claude_client_brief_does_not_force_thirty_seconds():
    from backend.customer_story import director_brief
    brief=director_brief("Emphasize the result",provider="claude")
    assert "earns its runtime" in brief and "Emphasize the result" in brief
    assert "30-second" not in brief
    assert director_brief(provider="gemini")==director_brief(provider="claude")
    assert "30-second" not in director_brief()

def test_v2_director_prioritizes_witnessed_end_state_over_cosmetic_motion():
    assert claude.PROMPT_VERSION == "motion-director-v2"
    prompt = claude.system_prompt("story-editorial")
    for rule in ("final image first", "unrelated marketing page", "390px-wide",
                 "shortest executable duration", "viewport shrink/white flashes",
                 "final after-image", "Do not infer motion or audio from stills"):
        assert rule in prompt


def test_provider_error_category_is_fixed_and_not_raw_body(monkeypatch,tmp_path):
    from urllib.error import HTTPError
    from backend.story_outcome_evidence import require_provider_reply
    import pytest
    monkeypatch.setenv('ANTHROPIC_API_KEY','fixture')
    def fail(req,timeout):
        raise HTTPError(req.full_url,400,'bad request',{},io.BytesIO(json.dumps({'error':{'message':'Credit balance too low; private example detail'}}).encode()))
    monkeypatch.setattr(claude,'urlopen',fail)
    c=claude.ClaudeConversation(tmp_path)
    r=c.ask('Synthetic observation',phase='public-browser-exploration',json_mode=True,max_attempts=1)
    assert r is None and c.calls==1
    assert c.data['attempts'][0]['provider_error_category']=='billing'
    assert 'private example detail' not in json.dumps(c.data)
    with pytest.raises(RuntimeError,match='Claude returned HTTP 400 \\(billing\\)'):
        require_provider_reply(r,c)
