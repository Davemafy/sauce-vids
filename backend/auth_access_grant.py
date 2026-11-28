"""Owner-installed, job-bound access grants. The API receives a reference."""
from dataclasses import dataclass, field
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import stat

from backend.agentmail_auth import Approval, AuthUnavailable, origin


def read_private(path, max_bytes):
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    with os.fdopen(os.open(path, flags), "rb") as handle:
        info = os.fstat(handle.fileno())
        if (not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600
                or info.st_uid != os.geteuid() or info.st_size > max_bytes):
            raise AuthUnavailable("Access grant files must be private and owned by the service")
        data = handle.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise AuthUnavailable("Access grant file is oversized")
        return json.loads(data)


def directory():
    configured = os.getenv("SAUCE_AUTH_APPROVAL_DIR")
    if not configured:
        raise AuthUnavailable("Authorized access grants are not configured")
    path = Path(configured)
    if not path.is_absolute():
        raise AuthUnavailable("Access grant directory must be absolute")
    info = path.lstat()
    if (not stat.S_ISDIR(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o700
            or info.st_uid != os.geteuid()):
        raise AuthUnavailable("Access grant directory must be private and owned by the service")
    return path


def load(grant_id, url):
    if not isinstance(grant_id, str) or not re.fullmatch("[a-f0-9]{24}", grant_id):
        raise AuthUnavailable("Invalid access grant reference")
    try:
        approval = Approval(**read_private(directory() / f"{grant_id}.json", 16384)).check()
        if approval.job_id != grant_id or approval.product_url != url:
            raise AuthUnavailable("Access grant does not authorize this job and URL")
        return approval
    except (OSError, TypeError, ValueError):
        raise AuthUnavailable("Access grant unavailable or malformed") from None


def load_session(approval):
    try:
        state = read_private(directory() / f"{approval.job_id}.session.json", 512 * 1024)
        cookies, origins = state["cookies"], state["origins"]
        site = origin(approval.product_url)[1]
        if (not isinstance(cookies, list) or not isinstance(origins, list)
                or not (cookies or origins) or len(cookies) > 120 or len(origins) > 1):
            raise ValueError()
        for cookie in cookies:
            if cookie["domain"].lower().lstrip(".") != site or cookie.get("partitionKey"):
                raise ValueError()
        for entry in origins:
            if origin(entry["origin"]) != origin(approval.product_url):
                raise ValueError()
        return {"cookies": cookies, "origins": origins}
    except (OSError, TypeError, ValueError, AttributeError, KeyError):
        raise AuthUnavailable("Transferred state must match the approved HTTPS application") from None


@dataclass(frozen=True)
class ScopedApproval(Approval):
    """New owner-issued scope; a legacy job grant is never upgraded implicitly."""
    scope_id: str = ""
    scope_digest: str = field(default="", repr=False)

    def check(self):
        super().check()
        try:
            record = read_private(directory() / f"{self.scope_id}.scope.json", 16384)
            if _scope_digest(record) != self.scope_digest:
                raise AuthUnavailable("Reusable access scope changed or revoked")
        except (OSError, TypeError, ValueError):
            raise AuthUnavailable("Reusable access scope unavailable or revoked") from None
        return self


def _scope_digest(record):
    return sha256(json.dumps(record, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_scope(scope_id, url, job_id):
    """Only an explicitly provisioned new scope can authorize a new job.

    The same private scope must remain present and unchanged on each check.
    Deleting it revokes future operations. Never fall back to a legacy grant.
    """
    if not all(isinstance(x, str) and re.fullmatch("[a-f0-9]{24}", x)
               for x in (scope_id, job_id)) or scope_id == job_id:
        raise AuthUnavailable("Invalid distinct scope and execution identities")
    try:
        path = directory() / f"{scope_id}.scope.json"
        record = read_private(path, 16384)
        if not isinstance(record, dict) or record.get("scope_id") != scope_id or record.get("version") != 1:
            raise AuthUnavailable("Invalid reusable access scope")
        if record.get("purpose") != "authorized-demo-auth" or record.get("approval", {}).get("mode") != "discover":
            raise AuthUnavailable("Scope must explicitly authorize adaptive demo authentication")
        details = record["approval"]
        if any(k in details for k in ("job_id", "scope_id", "scope_digest")) or details.get("product_url") != url:
            raise AuthUnavailable("Scope does not authorize this application")
        return ScopedApproval(**details, job_id=job_id, scope_id=scope_id,
                              scope_digest=_scope_digest(record)).check()
    except (OSError, TypeError, ValueError, KeyError, AttributeError):
        raise AuthUnavailable("Reusable access scope unavailable or malformed") from None
