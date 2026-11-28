"""Credential-bearing Chromium network boundary for an owner-approved job."""
from urllib.parse import urljoin, urlsplit

from backend.agentmail_auth import AuthUnavailable, origin, utcnow
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
        self.redirects=[]

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
                if not self.armed or url not in self.posts or self.writes>=8:
                    return route.abort()
                self.armed=False
                self.writes+=1
                if self.since is None:
                    self.since=utcnow()
            elif req.method not in ("GET","HEAD"):
                return route.abort()
            elif navigation and url not in self.routes and url!=self.verification_link:
                return route.abort()
            fetched=route.fetch(max_redirects=0,max_retries=0,timeout=10000)
            try:
                if 300<=fetched.status<400:
                    destination=urljoin(url,fetched.headers.get("location",""))
                    if fetched.status not in (301,302,303) or not navigation or destination not in self.routes:
                        return route.abort()
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

    def click(self,locator,writable):
        self.armed=writable
        try:
            locator.click(timeout=4000,no_wait_after=True)
            self.page.wait_for_timeout(450)
        finally:
            self.armed=False


def provision(approval,mail,conversation):
    from playwright.sync_api import Error,sync_playwright
    from backend.product_explorer import CHROME
    from backend.authorized_auth_operator import run

    approval.check()
    if approval.mode!="register":
        raise AuthUnavailable("Registration requires a registration access grant")
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=str(CHROME),headless=True,args=["--no-sandbox"])
        try:
            context=browser.new_context(service_workers="block",accept_downloads=False,permissions=[])
            page=context.new_page()
            context.on("page",lambda extra:extra.close())
            network=AuthNetwork(page,approval)
            context.route("**/*",network.route)
            context.route_web_socket("**/*",lambda socket:socket.close())
            page.goto(approval.signup_url,wait_until="domcontentloaded",timeout=16000)
            return run(page,approval,mail,conversation,network)
        except AuthUnavailable:
            raise
        except (Error,TypeError,ValueError,KeyError):
            raise AuthUnavailable("Authorized authentication interaction failed") from None
        finally:
            browser.close()
