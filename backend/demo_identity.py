"""Private app-origin demo identity. Files never enter a film job directory."""
from hashlib import sha256
import json
import os
import secrets

from backend.agentmail_auth import AuthUnavailable, origin, password
from backend.auth_access_grant import directory, read_private


class DemoIdentity:
    def __init__(self,approval,inbox):
        approval.check()
        key=json.dumps([origin(approval.product_url),inbox.lower()])
        self.path=directory()/(sha256(key.encode()).hexdigest()+".identity")
        self.inbox=inbox
        try:
            record=read_private(self.path,512*1024)
            self.password=record["password"]
            self.state=record.get("state")
            if not isinstance(self.password,str) or len(self.password)<24:
                raise ValueError()
        except FileNotFoundError:
            self.password=password()
            self.state=None
            self.save(None)
        except (OSError,TypeError,ValueError,KeyError):
            raise AuthUnavailable("Stored demo identity could not be read") from None

    def save(self,state):
        payload=json.dumps({"password":self.password,"state":state}).encode()
        if len(payload)>512*1024:
            raise AuthUnavailable("Reusable demo session exceeds the storage limit")
        temporary=self.path.with_name("."+self.path.name+"."+secrets.token_hex(8))
        try:
            fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,"wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary,self.path)
        finally:
            temporary.unlink(missing_ok=True)
