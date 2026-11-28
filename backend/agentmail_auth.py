"""Explicitly authorized test-account onboarding, outside public capture.

Mail and credentials never enter model packets, source receipts, or render logs.
This module does not open arbitrary mail links or grant public crawlers POST.
"""
from __future__ import annotations
from dataclasses import dataclass,field
from datetime import datetime,timezone,timedelta
from email.utils import parseaddr
from html.parser import HTMLParser
from urllib.parse import urlsplit,quote
import json,os,re,secrets,time
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.parse import urlencode
from urllib.error import URLError

from scripts.capture_safety import validate_public_url

class AuthUnavailable(RuntimeError): pass

def utcnow():return datetime.now(timezone.utc)
def origin(url):
    try:
        p=urlsplit(url)
        return (p.scheme,p.hostname,p.port or 443)
    except (ValueError,TypeError):return None
def checked_url(url):
    p=urlsplit(url)
    if p.scheme!="https" or p.query or p.fragment or p.username or p.password:
        raise AuthUnavailable("Explicit HTTPS route required")
    validate_public_url(url)
    return url
def stamp(s):
    try:
        t=datetime.fromisoformat(s.replace("Z","+00:00"))
        if t.tzinfo is None:raise ValueError()
        return t
    except (ValueError,TypeError,AttributeError):raise AuthUnavailable("Invalid authorization timestamp") from None

@dataclass(frozen=True)
class Approval:
    job_id:str
    signup_url:str
    product_url:str
    sender_domains:tuple[str,...]
    expires_at:str
    first_name:str
    last_name:str
    # Exact, owner-approved authentication endpoints. No wildcard POST routes.
    auth_posts:tuple[str,...]
    session_marker:str
    verification_url_paths:tuple[str,...]=()
    test_account_authorized:bool=False
    terms_reviewed:bool=False
    test_data_only:bool=False
    model_processing_authorized:bool=False
    mode:str="register"
    navigation_urls:tuple[str,...]=()
    def check(self):
        if not re.fullmatch(r"[a-f0-9]{24}",self.job_id):raise AuthUnavailable("Invalid job identity")
        if not all(v is True for v in (self.test_account_authorized,self.terms_reviewed,self.test_data_only,self.model_processing_authorized)):
            raise AuthUnavailable("Explicit test-account, terms and test-data authorization required")
        now=utcnow();expiry=stamp(self.expires_at)
        if not now<expiry<=now+timedelta(hours=24):raise AuthUnavailable("Authorization expired or too broad")
        if self.mode not in ("register","discover","session"):
            raise AuthUnavailable("Unsupported access grant mode")
        routes=(self.signup_url,self.product_url,*self.auth_posts,*self.navigation_urls)
        for u in routes:checked_url(u)
        if ((self.mode=="register" and not self.auth_posts) or len(self.auth_posts)>8
                or len(self.navigation_urls)>16 or any(origin(u)!=origin(self.signup_url) for u in routes)):
            raise AuthUnavailable("Authentication must use explicit same-origin endpoints")
        if ((self.mode!="session" and not self.sender_domains) or len(self.sender_domains)>4 or
            any(not re.fullmatch(r"[a-z0-9]+(?:[.-][a-z0-9]+)+",s) for s in self.sender_domains)):
            raise AuthUnavailable("Exact verification sender domains required")
        if any(not re.fullmatch(r"/[A-Za-z0-9/_-]{1,100}",p) or "//" in p or ".." in p for p in self.verification_url_paths):
            raise AuthUnavailable("Invalid verification route")
        if not isinstance(self.session_marker,str) or not 3<=len(self.session_marker.strip())<=100:
            raise AuthUnavailable("An exact observed signed-in product marker is required")
        for name in (self.first_name,self.last_name):
            if not isinstance(name,str) or not 1<=len(name.strip())<=80 or any(ord(c)<32 for c in name):
                raise AuthUnavailable("Owner-supplied accurate test identity required")
        return self

class AgentMail:
    """Fixed-host receive-only API adapter; no email sending surface."""
    def __init__(self,api_key=None,opener=None):
        self._key=api_key or os.getenv("AGENTMAIL_API_KEY")
        if not self._key:raise AuthUnavailable("Provision AGENTMAIL_API_KEY server-side")
        class NoRedirect(HTTPRedirectHandler):
            def redirect_request(self,*args,**kwargs):return None
        self._opener=opener or build_opener(NoRedirect())
    def _call(self,method,path,**kw):
        url="https://api.agentmail.to/v0/"+path
        if kw.get("params"):url+="?"+urlencode(kw["params"])
        data=json.dumps(kw["json"]).encode() if "json" in kw else None
        req=Request(url,data=data,headers={"Authorization":"Bearer "+self._key,
              "Content-Type":"application/json"},method=method)
        try:
            with self._opener.open(req,timeout=12) as response:
                if response.status not in (200,201):raise AuthUnavailable("AgentMail request rejected")
                raw=response.read(2_000_001)
            if len(raw)>2_000_000:raise AuthUnavailable("Oversized AgentMail response")
            d=json.loads(raw)
            if not isinstance(d,dict):raise AuthUnavailable("Malformed AgentMail response")
            return d
        except (URLError,OSError,ValueError):raise AuthUnavailable("AgentMail request failed") from None
    def create(self,approval):
        approval.check()
        result=self._call("POST","inboxes",json={"display_name":"Sauce test account","client_id":"sauce-auth-"+approval.job_id,
                       "deactivate_at":approval.expires_at,"metadata":{"purpose":"authorized-product-demo"}})
        ident=result.get("inbox_id");email=result.get("email",ident)
        if not isinstance(email,str) or email!=ident or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+",email):
            raise AuthUnavailable("Invalid dedicated inbox")
        return email
    def identity(self,approval):
        approval.check()
        inbox=os.getenv("AGENTMAIL_INBOX_ID")
        if inbox is None and approval.mode=="register":
            return self.create(approval)
        if not isinstance(inbox,str) or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+",inbox):
            raise AuthUnavailable("Configure the existing Sauce demo inbox")
        return inbox

    def messages(self,inbox,since):
        return self._call("GET","inboxes/"+quote(inbox,safe="")+"/messages",
             params={"limit":20,"after":since.astimezone(timezone.utc).isoformat().replace("+00:00","Z"),"include_spam":"false",
                     "include_blocked":"false","include_unauthenticated":"false","include_trash":"false"}).get("messages",[])
    def message(self,inbox,ident):
        return self._call("GET","inboxes/"+quote(inbox,safe="")+"/messages/"+quote(ident,safe=""))

@dataclass(frozen=True)
class Verification:
    kind:str
    value:str=field(repr=False)

class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.urls=[]
    def handle_starttag(self,tag,attrs):
        if tag=="a":
            self.urls.extend(v for k,v in attrs if k=="href" and isinstance(v,str))

VERIFY_SUBJECT=re.compile(r"\b(verif(?:y|ication)|confirm|one.time|otp|security code|activation|sign.in code)\b",re.I)
CODE=re.compile(r"\b(?:verification|confirmation|security|one.time|sign.in|activation|otp)\s+(?:code|password|pin)(?:\s+is)?\s*[:\s-]+([0-9]{4,8})\b",re.I)

def matches_verification_envelope(message,inbox,approval,since):
    """Reject unrelated shared-mailbox messages before fetching a body."""
    approval.check()
    if message.get("inbox_id")!=inbox or "received" not in message.get("labels",[]):return False
    if set(message.get("labels",[]))&{"spam","trash","blocked","unauthenticated"}:return False
    if not isinstance(message.get("from"),str):return False
    sender=parseaddr(message["from"])[1].lower().rsplit("@",1)
    if len(sender)!=2 or sender[-1] not in approval.sender_domains:return False
    if inbox.lower() not in {parseaddr(v)[1].lower() for v in message.get("to",[]) if isinstance(v,str)}:return False
    try:
        received=stamp(message["created_at"]);sent=stamp(message["timestamp"])
    except (KeyError,AuthUnavailable):return False
    now=utcnow()
    if not since<=received<=now+timedelta(seconds=10) or not since-timedelta(seconds=30)<=sent<=now+timedelta(seconds=10):return False
    subject=message.get("subject","")
    if not isinstance(subject,str) or not VERIFY_SUBJECT.search(subject):return False
    return True

def parse_verification(message,inbox,approval,since):
    """Never give email body to a model; refuse ambiguous or off-origin tokens."""
    if not matches_verification_envelope(message,inbox,approval,since):
        return None
    subject=message.get("subject","")
    text=message.get("extracted_text") or message.get("text") or ""
    html=message.get("extracted_html") or message.get("html") or ""
    if not isinstance(text,str) or not isinstance(html,str) or len(text)+len(html)>100000:return None
    codes=set(CODE.findall(text))
    # Some authentic messages put the verification code alone in the subject.
    codes.update(CODE.findall(subject))
    codes.update(re.findall(r"\bOTP(?: code)?(?: is)?\s*[:\s-]+([0-9]{4,8})\b",text,re.I))
    links=Links();links.feed(html)
    candidates=set()
    for url in links.urls+re.findall(r'https://[^\s<>"\']+',text):
        try:
            p=urlsplit(url)
            if (p.scheme=="https" and not p.username and not p.password and not p.fragment
                and origin(url)==origin(approval.signup_url)
                and (p.path in approval.verification_url_paths or approval.mode=="discover"
                     and re.search(r"(?i)(verify|confirm|activate|magic|callback)",p.path))
                and bool(p.query) and len(url)<=2048):
                candidates.add(url)
        except ValueError:continue
    values=[Verification("code",v) for v in codes]+[Verification("link",v) for v in candidates]
    return values[0] if len(values)==1 else None

def wait_verification(mail,inbox,approval,since,*,timeout=90,sleep=time.sleep):
    approval.check()
    end=time.monotonic()+min(120,max(1,timeout));seen=set()
    for _ in range(25):
        if time.monotonic()>=end:break
        approval.check()
        matches=[]
        for row in mail.messages(inbox,since)[:20]:
            ident=row.get("message_id")
            if not isinstance(ident,str) or len(ident)>512 or ident in seen:continue
            seen.add(ident)
            if not matches_verification_envelope(row,inbox,approval,since):
                continue
            msg=mail.message(inbox,ident)
            v=parse_verification(msg,inbox,approval,since)
            if v:matches.append(v)
        if len(matches)>1:raise AuthUnavailable("Ambiguous verification mail")
        if matches:return matches[0]
        sleep(min(4,max(0,end-time.monotonic())))
    raise AuthUnavailable("Verification email not received within budget")

def unique_field(page,selector):
    rows=[r for r in page.locator(selector).all() if r.is_visible()]
    if len(rows)!=1:raise AuthUnavailable("Unsupported or ambiguous signup field")
    loc=rows[0]
    if not loc.is_enabled() or not loc.is_editable():raise AuthUnavailable("Signup field not editable")
    return loc

def fill_registration(page,approval,inbox,password):
    """Resolve only unambiguous standard fields, never model selectors."""
    approval.check()
    if page.url!=approval.signup_url:raise AuthUnavailable("Signup page identity changed")
    email=unique_field(page,'input[type="email"]')
    secret=unique_field(page,'input[type="password"]')
    # Scope the entire form by actual observed DOM; do not guess button coordinates.
    form=email.locator("xpath=ancestor::form[1]")
    if form.count()!=1 or form.locator('input[type="password"]:visible').count()!=1:
        raise AuthUnavailable("Unsupported signup form")
    if form.locator('input[type="checkbox"]:visible, input[type="file"]:visible, iframe:visible').count():
        raise AuthUnavailable("Signup requires explicit additional consent or challenge")
    first=unique_field(form,'input[autocomplete="given-name"],input[name="firstName"],input[name="first_name"]')
    last=unique_field(form,'input[autocomplete="family-name"],input[name="lastName"],input[name="last_name"]')
    # Require exactly the four recognized editable inputs.
    if form.locator('input:visible:not([type="hidden"]):not([type="submit"])').count()!=4:
        raise AuthUnavailable("Additional profile fields require owner input")
    button=form.get_by_role("button",name=re.compile(r"^(create (an )?account|sign up|register)$",re.I))
    if button.count()!=1 or not button.is_visible() or not button.is_enabled():
        raise AuthUnavailable("Ambiguous signup submission")
    first.fill(approval.first_name);last.fill(approval.last_name);email.fill(inbox);secret.fill(password)
    return button

def password():return secrets.token_urlsafe(24)+"Aa9!"


from contextvars import ContextVar
from contextlib import contextmanager

_SESSION=ContextVar("sauce_test_session",default=None)

@contextmanager
def approved_session(approval,state):
    approval.check()
    token=_SESSION.set((approval,state))
    try:yield
    finally:_SESSION.reset(token)

def test_session_active():return _SESSION.get() is not None

def session_for(url):
    session=_SESSION.get()
    if session is None:return None
    approval,state=session;approval.check()
    if url!=approval.product_url:raise AuthUnavailable("Authenticated film left approved product route")
    return state

def check_test_surface(page,approval=None):
    # A bounded explicit test-data workspace, never a login/onboarding frame.
    if page.locator('input[type="password"]:visible,input[autocomplete="one-time-code"]:visible,[data-private]:visible,[data-secret]:visible,[data-sensitive]:visible').count():
        raise AuthUnavailable("Sensitive or authentication UI cannot be filmed")
    from backend.source_action_preflight import visible_authentication_barrier
    if visible_authentication_barrier(page):raise AuthUnavailable("Authentication still required")
    current=_SESSION.get()
    if approval is None and current:approval=current[0]
    if approval is not None:
        approval.check()
        if page.url!=approval.product_url:raise AuthUnavailable("Approved product route lost")
        markers=[e for e in page.get_by_text(approval.session_marker,exact=True).all() if e.is_visible()]
        if len(markers)!=1:raise AuthUnavailable("Signed-in test product marker not observed")

def check_film_surface(page):
    """Confirm the authorized product and reject visible login identity before capture."""
    check_test_surface(page)
    inbox=os.getenv("AGENTMAIL_INBOX_ID")
    if inbox and (any(loc.is_visible() for loc in page.get_by_text(inbox,exact=False).all())
                  or page.locator("input:visible,textarea:visible").evaluate_all(
                      "(els,identity)=>els.some(e=>String(e.value||'').toLowerCase().includes(identity.toLowerCase()))",inbox)):
        raise AuthUnavailable("Demo login identity is present on the product surface")


def provision(approval,mail):
    """Single authorized signup; direct same-origin email/password forms only."""
    from playwright.sync_api import sync_playwright
    from backend.product_explorer import CHROME
    from scripts.capture_safety import guard_route
    approval.check()
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path=str(CHROME),headless=True,args=["--no-sandbox"])
        c=b.new_context(service_workers="block",accept_downloads=False,permissions=[])
        posted=set();verify_link=None;armed=False
        def guard(route):
            req=route.request;url=req.url
            if origin(url)!=origin(approval.signup_url):return route.abort("blockedbyclient")
            if req.method=="POST":
                if not armed or url not in approval.auth_posts or url in posted:
                    return route.abort("blockedbyclient")
                posted.add(url)
            elif req.method not in ("GET","HEAD"):return route.abort("blockedbyclient")
            if req.is_navigation_request() and url not in (approval.signup_url,approval.product_url,verify_link):
                return route.abort("blockedbyclient")
            if req.method=="POST" or req.is_navigation_request():
                # Reject redirects in the credential-bearing browser rather
                # than letting a server relay credentials to an unknown origin.
                try:
                    response=route.fetch(max_redirects=0,timeout=12000)
                    if 300<=response.status<400:return route.abort("blockedbyclient")
                    return route.fulfill(response=response)
                except Exception:return route.abort("blockedbyclient")
            return guard_route(route)
        c.route("**/*",guard);c.route_web_socket("**/*",lambda ws:ws.close())
        try:
            p=c.new_page();p.goto(approval.signup_url,wait_until="domcontentloaded",timeout=20000)
            if p.locator('iframe[src*="captcha"]:visible,[data-sitekey]:visible').count():
                raise AuthUnavailable("Challenge requires human completion")
            # Validate form before spending an inbox allocation.
            unique_field(p,'input[type="email"]');unique_field(p,'input[type="password"]')
            inbox=mail.identity(approval);secret=password();button=fill_registration(p,approval,inbox,secret)
            since=utcnow();armed=True;button.click(timeout=5000)
            p.wait_for_timeout(1200)
            if p.url!=approval.product_url:
                v=wait_verification(mail,inbox,approval,since)
                if v.kind=="link":
                    verify_link=v.value
                    p.goto(verify_link,wait_until="domcontentloaded",timeout=20000)
                else:
                    code=unique_field(p,'input[autocomplete="one-time-code"]')
                    code.fill(v.value)
                    button=p.get_by_role("button",name=re.compile(r"^(verify|confirm|verify email|confirm email)$",re.I))
                    if button.count()!=1 or not button.is_enabled():raise AuthUnavailable("Unsupported verification control")
                    button.click(timeout=5000)
            armed=False
            p.goto(approval.product_url,wait_until="domcontentloaded",timeout=20000)
            p.wait_for_timeout(1000)
            if p.url!=approval.product_url:raise AuthUnavailable("Approved product route not reached")
            check_test_surface(p,approval)
            if not posted:raise AuthUnavailable("No authorized signup request observed")
            # No password, inbox body, cookie or token is written to disk.
            state=c.storage_state()
            if not state.get("cookies") and not state.get("origins"):raise AuthUnavailable("No reusable test session")
            return state
        except AuthUnavailable:raise
        except Exception:raise AuthUnavailable("Authorized authentication failed; no automatic retry") from None
        finally:c.close();b.close()
