"""Credential-bearing Chromium network boundary for an owner-approved job."""
import re
from urllib.parse import parse_qs, urljoin, urlsplit
import json

from backend.agentmail_auth import AuthUnavailable, checked_url, check_test_surface, origin, utcnow
from scripts.capture_safety import validate_public_url


class AuthNetwork:
    def __init__(self,page,approval):
        self.page=page
        self.approval=approval
        self.routes={approval.signup_url,approval.product_url,*approval.navigation_urls}
        self.posts=set(approval.auth_posts)
        self.verification_link=None
        self.since=None
        self.writes=0
        self.armed=False
        self.navigation_armed=False
        self.bindings=()
        self.redirects=[]

    def same_origin(self,url):
        try:
            return origin(url)==origin(self.approval.signup_url) and bool(checked_url(url))
        except (ValueError,TypeError,AuthUnavailable):
            return False

    def may_visit(self,url):
        if url in self.routes:
            return True
        if self.approval.mode!="discover" or not self.same_origin(url):
            return False
        return not re.search(r"(?i)(?:^|[/_-])(delete|logout|signout|sign-out|billing|payment|checkout|purchase|invite|admin)(?:[/_-]|$)",urlsplit(url).path)

    def admit_links(self,links):
        if self.approval.mode=="discover":
            self.routes.update(url for url in links if self.may_visit(url))

    def matches_bound_form(self,request):
        if self.approval.mode!="discover" or not self.bindings or not self.may_visit(request.url):
            return False
        data=request.post_data or ""
        if len(data)>16384:
            return False
        try:
            payload=json.loads(data) if data.startswith("{") else {
                k:v[0] for k,v in parse_qs(data,max_num_fields=30).items() if len(v)==1}
        except ValueError:
            return False
        if not isinstance(payload,dict):
            return False
        # A first-party SPA may submit without a native form. Permit only the
        # request carrying the actual demo credentials or code Chromium filled.
        values=[v for v in payload.values() if isinstance(v,str)]
        return all(value in values for value in self.bindings)

    def route(self,route):
        from playwright.sync_api import Error
        req=route.request
        url=req.url
        try:
            self.approval.check()
            if origin(url)!=origin(self.approval.signup_url):
                return route.abort()
            parts=urlsplit(url)
            validate_public_url(parts._replace(query="",fragment="").geturl())
            navigation=req.is_navigation_request()
            if navigation and req.frame!=self.page.main_frame:
                return route.abort()
            if req.method=="POST":
                if not self.armed or self.writes>=8 or url not in self.posts and not self.matches_bound_form(req):
                    return route.abort()
                self.armed=False
                self.writes+=1
                if self.since is None:
                    self.since=utcnow()
            elif req.method not in ("GET","HEAD"):
                return route.abort()
            elif navigation and url not in self.routes and url!=self.verification_link:
                if not self.navigation_armed or not self.may_visit(url):
                    return route.abort()
                self.navigation_armed=False
                self.routes.add(url)
            fetched=route.fetch(max_redirects=0,max_retries=0,timeout=10000)
            try:
                if 300<=fetched.status<400:
                    destination=urljoin(url,fetched.headers.get("location",""))
                    if fetched.status not in (301,302,303) or not navigation or not self.may_visit(destination):
                        return route.abort()
                    if len(self.redirects)>=4:
                        return route.abort()
                    self.routes.add(destination)
                    self.redirects.append(destination)
                    # Chrome must never perform an unmediated redirect hop.
                    return route.fulfill(response=fetched,status=200,body="")
                return route.fulfill(response=fetched)
            finally:
                fetched.dispose()
        except (ValueError,AuthUnavailable,Error):
            route.abort()

    def follow_redirects(self):
        for _ in range(4):
            if not self.redirects:
                return
            self.page.goto(self.redirects.pop(0),wait_until="domcontentloaded",timeout=12000)
        if self.redirects:
            raise AuthUnavailable("Authentication redirect budget exhausted")

    def click(self,locator,writable,bindings=()):
        prior=self.posts
        if self.approval.mode=="discover":
            # Admit the native form action declared by the current live control.
            # A scripted request receives no inherited blanket POST permission.
            form=locator.evaluate("""e=>e.form && (e.getAttribute('formmethod') || e.form.method).toLowerCase()==='post'
                ? new URL(e.getAttribute('formaction') || e.form.action,location.href).href : null""")
            self.posts={form} if form and self.may_visit(form) else set()
        self.armed=writable
        self.navigation_armed=self.approval.mode=="discover"
        self.bindings=bindings
        try:
            locator.click(timeout=4000,no_wait_after=True)
            self.page.wait_for_timeout(450)
        finally:
            self.armed=False
            self.navigation_armed=False
            self.bindings=()
            self.posts=prior


def provision(approval,mail,conversation):
    from playwright.sync_api import Error,sync_playwright
    from backend.product_explorer import CHROME
    from backend.authorized_auth_operator import run

    approval.check()
    if approval.mode not in ("register","discover"):
        raise AuthUnavailable("Registration requires a registration access grant")
    identity=None
    if approval.mode=="discover":
        from backend.demo_identity import DemoIdentity
        identity=DemoIdentity(approval,mail.identity(approval))
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=str(CHROME),headless=True,args=["--no-sandbox"])
        try:
            context=browser.new_context(service_workers="block",accept_downloads=False,permissions=[],
                                        storage_state=identity.state if identity else None)
            page=context.new_page()
            context.on("page",lambda extra:extra.close())
            network=AuthNetwork(page,approval)
            context.route("**/*",network.route)
            context.route_web_socket("**/*",lambda socket:socket.close())
            if identity and identity.state:
                try:
                    page.goto(approval.product_url,wait_until="domcontentloaded",timeout=16000)
                    network.follow_redirects()
                    check_test_surface(page,approval)
                except (AuthUnavailable,Error):
                    pass
                else:
                    return context.storage_state()
            page.goto(approval.signup_url,wait_until="domcontentloaded",timeout=16000)
            state=run(page,approval,mail,conversation,network,identity=identity)
            if identity:
                identity.save(state)
            return state
        except AuthUnavailable:
            raise
        except (Error,TypeError,ValueError,KeyError):
            raise AuthUnavailable("Authorized authentication interaction failed") from None
        finally:
            browser.close()
