"""Read-only preflight for one explicitly configured Sauce inbox.

No mailbox allocation, sending, message-body retrieval, or site sign-in.
"""
import os,re,json
from urllib.parse import quote,urlencode
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.error import URLError

class InboxUnavailable(RuntimeError):pass

class SharedInbox:
    def __init__(self,*,api_key=None,inbox_id=None,opener=None):
        self._key=api_key if api_key is not None else os.getenv("AGENTMAIL_API_KEY")
        self.inbox_id=inbox_id if inbox_id is not None else os.getenv("AGENTMAIL_INBOX_ID")
        if not self._key:raise InboxUnavailable("AgentMail not configured")
        if not isinstance(self.inbox_id,str) or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+",self.inbox_id):
            raise InboxUnavailable("Configure the dedicated AgentMail inbox")
        class NoRedirect(HTTPRedirectHandler):
            def redirect_request(self,*a,**kw):return None
        self._opener=opener or build_opener(NoRedirect())

    def check(self):
        path="inboxes/"+quote(self.inbox_id,safe="")+"/messages"
        query=urlencode({"limit":1,"include_spam":"false","include_trash":"false",
                         "include_blocked":"false","include_unauthenticated":"false"})
        req=Request("https://api.agentmail.to/v0/"+path+"?"+query,
                    headers={"Authorization":"Bearer "+self._key},method="GET")
        try:
            with self._opener.open(req,timeout=12) as response:
                if response.status!=200:raise InboxUnavailable("Message listing unavailable")
                raw=response.read(2_000_001)
            if len(raw)>2_000_000:raise InboxUnavailable("Oversized response")
            data=json.loads(raw)
            if not isinstance(data,dict) or not isinstance(data.get("messages"),list):
                raise InboxUnavailable("Malformed message listing")
        except (URLError,OSError,ValueError):raise InboxUnavailable("Message listing unavailable") from None
        return {"ready":True,"mode":"shared-inbox-read-only"}

def main():
    try:print(json.dumps(SharedInbox().check()))
    except InboxUnavailable as exc:raise SystemExit(str(exc)) from None

if __name__=="__main__":main()
