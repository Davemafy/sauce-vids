"""Private auth-only acceptance probe; reuses the existing guarded product explorer.

No renderer, creative model, public endpoint or automatic approval issuance.
A separately provisioned reusable scope is mandatory.
"""
import argparse
import json
import os
import secrets
from pathlib import Path

from backend.agentmail_auth import AgentMail, AuthUnavailable, approved_session
from backend.auth_access_grant import load_scope
from backend.authorized_auth_network import provision
from backend.curious_showcase import Conversation


def run(scope_id, url, out):
    from backend.customer_browser_agent import run as explore
    from backend.customer_story import browser, shot, media, verify

    job_id = secrets.token_hex(12)
    approval = load_scope(scope_id, url, job_id)
    if not os.getenv("GEMINI_API_KEY"):
        raise AuthUnavailable("Gemini is required")
    out = Path(out)
    out.mkdir(mode=0o700, parents=False, exist_ok=False)
    receipt = {"job_id": job_id, "authenticated": False, "read_only_product_action_verified": False,
               "session_reused": False, "auth_model_calls": 0, "product_model_calls": 0}
    try:
        mail = AgentMail()
        conv = Conversation(out / "auth-model", call_budget=16)
        state = provision(approval, mail, conv)
        receipt["auth_model_calls"] = conv.calls
        receipt["authenticated"] = True
        with approved_session(approval, state):
            scout = Conversation(out / "product-model", call_budget=8)
            graph = explore(url, out / "product", scout, browser, shot, media, verify)
            receipt["product_model_calls"] = graph["calls"]
            receipt["verified_actions"] = len(graph["actions"])
            receipt["read_only_product_action_verified"] = bool(graph["actions"] and graph["proofs"])

        class NoInference:
            def ask(self, *args, **kwargs):
                raise AuthUnavailable("Session reuse required a fresh model decision")
        # Reopen a new Chromium context and independently check the signed-in
        # marker; no second registration or login attempt in this reuse check.
        provision(load_scope(scope_id, url, secrets.token_hex(12)), mail, NoInference())
        receipt["session_reused"] = True
    except Exception as exc:
        receipt["failure_type"] = type(exc).__name__
        raise
    finally:
        fd = os.open(out / "receipt.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as stream:
            json.dump(receipt, stream, indent=2)
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        receipt = run(args.scope, args.url, args.out)
    except Exception as exc:
        raise SystemExit("Auth-only probe stopped: " + type(exc).__name__) from None
    print(json.dumps(receipt))
    if not all(receipt[k] for k in ("authenticated", "read_only_product_action_verified", "session_reused")):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
