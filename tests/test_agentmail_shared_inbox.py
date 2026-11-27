import json
from urllib.parse import urlsplit,parse_qs
import pytest
from backend.agentmail_shared_inbox import SharedInbox,InboxUnavailable

class StubResponse:
    status=200
    def __enter__(self):return self
    def __exit__(self,*a):pass
    def read(self,n):return b'{"messages":[{"subject":"private fixture"}]}'

class StubTransport:
    def open(self,req,timeout):
        u=urlsplit(req.full_url)
        assert u.scheme=="https" and u.netloc=="api.agentmail.to"
        assert u.path=="/v0/inboxes/test%40example.com/messages"
        assert req.get_method()=="GET" and req.data is None and timeout==12
        assert parse_qs(u.query)["limit"]==["1"]
        return StubResponse()

def test_only_existing_inbox_listing():
    inbox=SharedInbox(api_key="fixture",inbox_id="test@example.com",opener=StubTransport())
    assert inbox.check()=={"ready":True,"mode":"shared-inbox-read-only"}

def test_explicit_mailbox_required():
    with pytest.raises(InboxUnavailable):SharedInbox(api_key="fixture",inbox_id="")
    with pytest.raises(InboxUnavailable):SharedInbox(api_key="fixture",inbox_id="https://example.com")

def test_malformed_response_fails_closed():
    class Broken(StubResponse):
        def read(self,n):return b'{"unexpected":[]}'
    class Transport:
        def open(self,*a,**k):return Broken()
    with pytest.raises(InboxUnavailable):
        SharedInbox(api_key="fixture",inbox_id="test@example.com",opener=Transport()).check()
