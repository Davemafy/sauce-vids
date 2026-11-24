"""Bounded safe public UI hypotheses for a real URL-to-video customer job.

Inspect candidate controls, trigger each in an independent disposable browser,
and admit only genuine source-visible outcomes. No model selectors or fabricated
screen states. Persist failure receipts to explain why the next candidate
was tried. This tool is not a premium film quality approval.
"""
from __future__ import annotations
import json
from pathlib import Path

from backend.product_explorer import normalize,safe_public_modal_opener
from backend.source_action_preflight import probe_public_action


def investigate_modal_candidates(url,report,directory,seed_plan,admit,*,limit=3):
    if type(limit) is not int or not 1<=limit<=4:
        raise ValueError("Public exploration budget must be bounded")
    controls=[c for c in report.get("controls",[]) if safe_public_modal_opener(c)][:limit]
    base=Path(directory)
    base.mkdir(mode=0o700,parents=True,exist_ok=True)
    attempts=[]
    selected=None
    for n,control in enumerate(controls):
        proposal=normalize({
            "mode":"interactive","action_ids":[control["id"]],
            "heading_ids":seed_plan.get("heading_ids",[]),
            "title":seed_plan.get("title"),
            "reason":"Real observed public modal"
        },report)
        evidence=None
        try:
            evidence=probe_public_action(
                url,report,control["id"],base/("candidate-"+str(n)))
            admit(proposal,report,evidence)
        except (ValueError,RuntimeError,OSError,TimeoutError,KeyError,TypeError) as exc:
            attempts.append({"control_id":control["id"],
                             "decision":evidence.get("decision") if evidence else "probe_failed",
                             "status":"rejected",
                             "reason_type":type(exc).__name__})
        else:
            attempts.append({"control_id":control["id"],
                             "decision":evidence["decision"],
                             "status":"source_proven_candidate",
                             "result_area_fraction":evidence["result_area_fraction"],
                             "changed_result_fraction":evidence["changed_result_fraction"]})
            selected=(proposal,evidence)
            break
    (base/"receipt.json").write_text(json.dumps({
        "schema":"sauce-public-modal-investigation-v1",
        "attempts":attempts,"max_candidates":limit,"creative_approved":False},
        indent=2)+"\n")
    return selected
