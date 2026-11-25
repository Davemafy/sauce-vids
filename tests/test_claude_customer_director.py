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
