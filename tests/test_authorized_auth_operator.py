from datetime import timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import re
from threading import Thread
from urllib.parse import parse_qs

import pytest

from backend import agentmail_auth as auth, authorized_auth_network as network
from backend.auth_access_grant import load, load_session


def grant(base, **extra):
    data=dict(job_id="a"*24,signup_url=base+"/login",product_url=base+"/app",
              sender_domains=("fixture.example",),expires_at=(auth.utcnow()+timedelta(hours=1)).isoformat(),
              first_name="Demo",last_name="Tester",auth_posts=tuple(base+x for x in ("/register","/verify","/setup")),
              navigation_urls=tuple(base+x for x in ("/join","/check","/onboard")),session_marker="Demo workspace",
              test_account_authorized=True,terms_reviewed=True,test_data_only=True,model_processing_authorized=True)
    return auth.Approval(**{**data,**extra})


def test_job_bound_session_transfer(tmp_path,monkeypatch):
    monkeypatch.setattr(auth,"validate_public_url",lambda url:url)
    monkeypatch.setenv("SAUCE_AUTH_APPROVAL_DIR",str(tmp_path))
    tmp_path.chmod(0o700)
    obj=grant("https://fixture.example",mode="session",sender_domains=(),auth_posts=())
    p=tmp_path/(obj.job_id+".json")
    p.write_text(json.dumps(obj.__dict__))
    p.chmod(0o600)
    state=tmp_path/(obj.job_id+".session.json")
    state.write_text(json.dumps({"cookies":[{"domain":".fixture.example","value":"secret"}],"origins":[]}))
    state.chmod(0o600)
    approved=load(obj.job_id,obj.product_url)
    assert load_session(approved)["cookies"][0]["domain"]==".fixture.example"
    with pytest.raises(auth.AuthUnavailable):
        load(obj.job_id,obj.signup_url)
    state.write_text(json.dumps({"cookies":[{"domain":".other.example"}],"origins":[]}))
    with pytest.raises(auth.AuthUnavailable):
        load_session(approved)
    state.unlink()
    state.symlink_to(p)
    with pytest.raises(auth.AuthUnavailable):
        load_session(approved)


@pytest.mark.parametrize("mode",("register","discover"))
def test_real_chromium_registration_code_onboarding_and_session(monkeypatch,tmp_path,mode):
    monkeypatch.setattr(auth,"checked_url",lambda url:url)
    monkeypatch.setattr(network,"checked_url",lambda url:url)
    monkeypatch.setattr(network,"validate_public_url",lambda url:url)
    monkeypatch.setenv("SAUCE_AUTH_APPROVAL_DIR",str(tmp_path))
    tmp_path.chmod(0o700)
    received=[]
    pages={
        "/login":'<h1>Join the space</h1><a href="/join">New profile</a>',
        "/join":'<h1>Create profile</h1><form action="/register" method="post"><input name="contact" placeholder="Work email"><input type="password" name="password"><button>Get started</button></form>',
        "/check":'<h1>Check your inbox</h1><form action="/verify" method="post"><input type="tel" name="otp" aria-label="Verification code"><button>Validate</button></form>',
        "/onboard":'<h1>Your first workspace</h1><form action="/setup" method="post"><input name="team" placeholder="Workspace title"><button>Continue</button></form>',
    }
    class HTTP(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            body=pages.get(self.path)
            if self.path=="/app" and "access=fixture-value" in self.headers.get("Cookie",""):
                body="<h1>Demo workspace</h1>"
            self.send_response(200 if body else 404)
            self.send_header("Content-Type","text/html")
            self.end_headers()
            self.wfile.write((body or "").encode())
        def do_POST(self):
            fields=parse_qs(self.rfile.read(int(self.headers["Content-Length"])).decode())
            received.append((self.path,fields))
            required={"/register": "contact","/verify":"otp","/setup":"team"}[self.path]
            if not fields.get(required) or self.path=="/verify" and fields["otp"]!=[otp]:
                self.send_error(400)
                return
            landing={"/register":"/check","/verify":"/onboard","/setup":"/app"}[self.path]
            self.send_response(303)
            self.send_header("Location",landing)
            if self.path=="/setup":self.send_header("Set-Cookie","access=fixture-value; Path=/; HttpOnly")
            self.end_headers()
    http=ThreadingHTTPServer(("127.0.0.1",0),HTTP)
    thread=Thread(target=http.serve_forever,daemon=True)
    thread.start()
    email="fixture@agentmail.to"
    otp="418902"
    monkeypatch.setattr("backend.authorized_auth_operator.wait_verification",lambda *a:auth.Verification("code",otp))
    class Mail:
        def create(self,approval):return email
        def identity(self,approval):return email
    class Gemini:
        steps=iter((
            ("click","login","New profile",""),("fill","registration","Work email","email"),
            ("fill","registration","password","password"),("click","registration","Get started",""),
            ("click","verification","Validate",""),
            ("verify_email","verification",None,""),("fill","verification","Verification code","code"),
            ("click","verification","Validate",""),("fill","onboarding","Workspace title","workspace"),
            ("click","onboarding","Continue",""),
        ))
        def ask(self,prompt,**kw):
            assert "media" not in kw
            assert email not in prompt and otp not in prompt and "fixture-value" not in prompt
            operation,phase,label,role=next(self.steps)
            candidates=re.search(r'(\{"controls":.*)$',prompt)
            controls=json.loads(candidates.group(1))["controls"]
            target=next((r["id"] for r in controls if r["label"]==label),"")
            return json.dumps(dict(operation=operation,phase=phase,target=target,role=role,option=""))
    try:
        kwargs={"mode":"discover","auth_posts":(),"navigation_urls":()} if mode=="discover" else {}
        approval=grant(f"http://127.0.0.1:{http.server_port}",**kwargs)
        state=network.provision(approval,Mail(),Gemini())
        assert [path for path,_ in received]==["/register","/verify","/setup"]
        assert received[0][1]["contact"]==[email]
        assert received[1][1]["otp"]==[otp]
        assert received[2][1]["team"]==["Sauce Demo"]
        assert state["cookies"][0]["name"]=="access"
        if mode=="discover":
            class NoDecisions:
                def ask(self,*a,**kw):pytest.fail("Reusable session should not reauthenticate")
            assert network.provision(approval,Mail(),NoDecisions())["cookies"][0]["name"]=="access"
            assert len(received)==3
            assert all(p.stat().st_mode&0o777==0o600 for p in tmp_path.glob("*.identity"))
    finally:
        http.shutdown()
        http.server_close()
