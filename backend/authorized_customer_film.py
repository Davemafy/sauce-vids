"""Private operator CLI. Never callable from the anonymous URL job API."""
import argparse,json,os,stat
from pathlib import Path
from backend.agentmail_auth import Approval,AgentMail,approved_session,provision,AuthUnavailable

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--approval",required=True,type=Path)
    parser.add_argument("--job-dir",required=True,type=Path)
    a=parser.parse_args()
    if a.approval.is_symlink() or stat.S_IMODE(a.approval.stat().st_mode)!=0o600:
        raise SystemExit("Approval file must be private mode 0600")
    try:
        data=json.loads(a.approval.read_text());approval=Approval(**data).check()
        mail=AgentMail()
        if a.job_dir.name!=approval.job_id:raise AuthUnavailable("Approval does not bind job directory")
        a.job_dir.mkdir(mode=0o700,parents=True,exist_ok=False)
        # Existence permanently records the attempt; no automatic re-registration.
        state=provision(approval,mail)
        with approved_session(approval,state):
            from backend.customer_story import execute_story_once
            result=execute_story_once(approval.product_url,a.job_dir,lambda s:print(s,flush=True))
        print(json.dumps({"status":result["status"],"creative_approved":False}))
    except (ValueError,OSError,RuntimeError,TypeError,KeyError):
        raise SystemExit("Authorized test film stopped; inspect private job receipts without retrying signup") from None

if __name__=="__main__":main()
