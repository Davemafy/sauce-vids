import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.capture_safety import validate_public_url
from backend.url2video import validate_direction,workflow_for,direct_once,NeedsKey

def test_reject_local_and_sensitive_urls():
    for url in ('http://127.0.0.1/', 'http://localhost/', 'http://10.1.2.3/',
                'http://169.254.169.254/latest/meta-data',
                'file:///etc/passwd','https://example.com:1234/',
                'https://bob:secret@example.com/'):
        with pytest.raises(ValueError):
            validate_public_url(url)

def test_reject_private_dns_rebinding():
    with patch('scripts.capture_safety.socket.getaddrinfo',return_value=[
      (2,1,6,'',('93.184.215.14',443)),(2,1,6,'',('192.168.1.1',443))]):
        with pytest.raises(ValueError):
            validate_public_url('https://some-new-public-looking-host.example.org/')

def test_director_cannot_make_up_section():
    source={"heading":[{"id":0,"text":"Workflow","tag":"h2","y":900}]}
    with pytest.raises(ValueError):
        validate_direction({"decision":"render","heading_ids":[999],
             "reason":"test","title":"a","story":"b"},source)

def test_director_can_decline_auth_gated_site():
    source={"heading":[{"id":0,"text":"Marketing","tag":"h1","y":0}]}
    plan=validate_direction({"decision":"needs_access","heading_ids":[],
        "reason":"Only sign in shown","title":"a","story":"b"},source)
    assert plan["decision"]=="needs_access"

def test_workflow_uses_no_mutating_interactions():
    source={"heading":[{"id":0,"text":"Product demo","tag":"h2","y":900}]}
    plan={"decision":"render","heading_ids":[0],"reason":"public",
          "title":"Test","story":"Product interactive"}
    steps=workflow_for(plan,source)
    assert steps and {a["action"] for a in steps}.issubset({"scroll","hover"})

def test_missing_key_does_not_generate_fake_direction(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY",raising=False)
    with pytest.raises(NeedsKey):
        direct_once({"screenshot":"/nonexistent"})
