from dataclasses import replace
from datetime import timedelta
from types import SimpleNamespace
import json
import pytest
from backend import agentmail_auth as auth

@pytest.fixture
def approval(monkeypatch):
    monkeypatch.setattr(auth,"validate_public_url",lambda url:url)
    return auth.Approval(job_id="a"*24,signup_url="https://demo.example.com/signup",
        product_url="https://demo.example.com/dashboard",sender_domains=("demo.example.com",),
        expires_at=(auth.utcnow()+timedelta(hours=1)).isoformat(),first_name="Authorized",
        last_name="Tester",auth_posts=("https://demo.example.com/api/register",),
        session_marker="Test workspace",verification_url_paths=("/verify",),
        test_account_authorized=True,terms_reviewed=True,test_data_only=True,
        model_processing_authorized=True)

def message():
    t=auth.utcnow().isoformat()
    return {"inbox_id":"test@agentmail.to","labels":["received"],"from":"App <verify@demo.example.com>",
            "to":["test@agentmail.to"],"created_at":t,"timestamp":t,"subject":"Verify your account",
            "text":"Your verification code is 123456"}

def test_permission_is_exact(approval):
    assert approval.check() is approval
    for a in (replace(approval,terms_reviewed=False),replace(approval,test_data_only=False),
              replace(approval,auth_posts=("https://other.example.com/register",)),
              replace(approval,expires_at=(auth.utcnow()-timedelta(seconds=1)).isoformat())):
        with pytest.raises(auth.AuthUnavailable):a.check()

def test_email_filters_and_secret_repr(approval):
    m=message();since=auth.utcnow()-timedelta(seconds=2)
    v=auth.parse_verification(m,m["inbox_id"],approval,since)
    assert v.kind=="code" and v.value=="123456" and v.value not in repr(v)
    for overrides in ({"from":"verify@demo.example.com.evil.com"},{"to":["different@agentmail.to"]},
                      {"labels":["received","unauthenticated"]},{"created_at":"2020-01-01T00:00:00Z"},
                      {"text":"Your verification code is 123456. Confirmation code: 123457"}):
        assert auth.parse_verification({**m,**overrides},m["inbox_id"],approval,since) is None

def test_magic_links_exact_path_and_origin(approval):
    m=message();m["text"]="Verify your account";since=auth.utcnow()-timedelta(seconds=2)
    for link,expected in [("https://demo.example.com/verify?token=abc",True),
        ("https://evil.example.com/verify?token=abc",False),
        ("https://demo.example.com/logout?token=abc",False)]:
        m["html"]=f'<a href="{link}">verify</a>'
        v=auth.parse_verification(m,m["inbox_id"],approval,since)
        assert bool(v)==expected
        if v:assert v.value==link and v.kind=="link"

def test_session_context_never_leaks_to_public(approval):
    assert auth.session_for(approval.product_url) is None
    state={"cookies":[]}
    with auth.approved_session(approval,state):
        assert auth.session_for(approval.product_url) is state
        with pytest.raises(auth.AuthUnavailable):auth.session_for("https://other.example.com/")
    assert auth.session_for(approval.product_url) is None

def test_inbox_create_bounded_and_idempotent(approval):
    class Fake:
        def open(self,req,timeout):
            assert req.full_url=="https://api.agentmail.to/v0/inboxes"
            assert timeout==12 and req.get_method()=="POST"
            d=json.loads(req.data)
            assert d["client_id"]=="sauce-auth-"+approval.job_id and d["deactivate_at"]==approval.expires_at
            class Response:
                status=200
                def __enter__(self):return self
                def __exit__(self,*a):pass
                def read(self,n):return b'{"email":"test@agentmail.to","inbox_id":"test@agentmail.to"}'
            return Response()
    assert auth.AgentMail(api_key="fixture",opener=Fake()).create(approval)=="test@agentmail.to"

def test_real_chromium_form_filled_without_submit(approval):
    from playwright.sync_api import sync_playwright
    from backend.product_explorer import CHROME
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path=str(CHROME),headless=True,args=["--no-sandbox"])
        p=b.new_page();p.route(approval.signup_url,lambda r:r.fulfill(body='''
        <form><input autocomplete="given-name"><input autocomplete="family-name">
        <input type="email"><input type="password"><button>Create account</button></form>
        ''',content_type="text/html"))
        p.goto(approval.signup_url)
        btn=auth.fill_registration(p,approval,"test@agentmail.to","local-only")
        assert p.locator('input[type="email"]').input_value()=="test@agentmail.to"
        assert btn.is_visible()
        p.locator('form').evaluate("e=>e.insertAdjacentHTML('beforeend','<input type=checkbox>')")
        with pytest.raises(auth.AuthUnavailable):auth.fill_registration(p,approval,"test@agentmail.to","local-only")
        b.close()


def test_capture_checks_authorized_surface_before_and_after_screenshot(approval,monkeypatch):
    """Synthetic in-memory product fixture; no account, mail or network auth."""
    from backend import customer_story as story
    from backend.product_explorer import CHROME
    from playwright.sync_api import sync_playwright
    from unittest.mock import Mock
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path=str(CHROME),headless=True,args=["--no-sandbox"])
        try:
            p=b.new_page()
            p.route("**/*",lambda r:r.fulfill(status=200,content_type="text/html",
                body="<main><h1>Test workspace</h1><p>Fixture product</p></main>"))
            p.goto(approval.product_url)
            raw=story.public_shot
            spy=Mock(wraps=raw)
            monkeypatch.setattr(story,"public_shot",spy)
            with auth.approved_session(approval,{"cookies":[],"origins":[]}):
                assert story.shot(p).startswith(b"\x89PNG")
                spy.assert_called_once()
                p.locator("h1").evaluate("e=>e.textContent='Session expired'")
                with pytest.raises(auth.AuthUnavailable,match="marker"):
                    story.shot(p)
                assert spy.call_count==1
                p.locator("h1").evaluate("e=>e.textContent='Test workspace'")
                def changed_during_capture(page):
                    image=raw(page)
                    page.locator("main").evaluate("e=>e.insertAdjacentHTML('beforeend','<input type=password>')")
                    return image
                monkeypatch.setattr(story,"public_shot",changed_during_capture)
                with pytest.raises(auth.AuthUnavailable,match="Sensitive"):
                    story.shot(p)
            assert auth.session_for(approval.product_url) is None
        finally:b.close()


def test_public_screenshot_does_not_enter_private_session_checks(monkeypatch):
    from backend import customer_story as story
    from unittest.mock import Mock
    page=Mock()
    capture=Mock(return_value=b"fixture-image")
    check=Mock()
    monkeypatch.setattr(story,"public_shot",capture)
    monkeypatch.setattr(auth,"check_test_surface",check)
    assert story.shot(page)==b"fixture-image"
    capture.assert_called_once_with(page)
    check.assert_not_called()
