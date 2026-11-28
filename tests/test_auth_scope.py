from datetime import timedelta
import json
import pytest

from backend import agentmail_auth as auth
from backend.auth_access_grant import load_scope, load
from test_authorized_auth_operator import grant


def test_scope_is_reusable_exact_revocable_and_legacy_stays_separate(tmp_path, monkeypatch):
    monkeypatch.setenv("SAUCE_AUTH_APPROVAL_DIR", str(tmp_path))
    monkeypatch.setattr(auth, "validate_public_url", lambda url: url)
    tmp_path.chmod(0o700)
    approval = grant("https://fixture.example", mode="discover")
    details = dict(approval.__dict__)
    scope = details.pop("job_id")
    path = tmp_path / (scope + ".scope.json")
    record = {"scope_id": scope, "version": 1, "purpose": "authorized-demo-auth", "approval": details}
    path.write_text(json.dumps(record))
    path.chmod(0o600)
    first = load_scope(scope, approval.product_url, "b"*24)
    second = load_scope(scope, approval.product_url, "c"*24)
    assert first.job_id != second.job_id
    assert first.scope_digest == second.scope_digest
    with pytest.raises(auth.AuthUnavailable):
        load_scope(scope, approval.signup_url, "d"*24)
    with pytest.raises(auth.AuthUnavailable):
        load(scope, approval.product_url)
    record["approval"]["expires_at"] = (auth.utcnow() + timedelta(minutes=15)).isoformat()
    path.write_text(json.dumps(record))
    with pytest.raises(auth.AuthUnavailable):
        first.check()
    fresh = load_scope(scope, approval.product_url, "e"*24)
    path.unlink()
    with pytest.raises(auth.AuthUnavailable):
        fresh.check()


def test_legacy_grant_cannot_be_used_as_scope(tmp_path, monkeypatch):
    monkeypatch.setenv("SAUCE_AUTH_APPROVAL_DIR", str(tmp_path))
    monkeypatch.setattr(auth, "validate_public_url", lambda url: url)
    tmp_path.chmod(0o700)
    approval = grant("https://fixture.example", mode="discover")
    p = tmp_path / (approval.job_id + ".json")
    p.write_text(json.dumps(approval.__dict__))
    p.chmod(0o600)
    assert load(approval.job_id, approval.product_url)
    with pytest.raises(auth.AuthUnavailable):
        load_scope(approval.job_id, approval.product_url, "b"*24)


def test_no_inbox_allocation_when_configuration_missing(monkeypatch):
    monkeypatch.delenv("AGENTMAIL_INBOX_ID", raising=False)
    monkeypatch.setattr(auth, "validate_public_url", lambda url: url)
    approval = grant("https://fixture.example")
    mail = auth.AgentMail(api_key="fixture")
    monkeypatch.setattr(mail, "create", lambda *a: pytest.fail("No allocation"))
    with pytest.raises(auth.AuthUnavailable):
        mail.identity(approval)
