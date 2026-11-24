"""Opt-in URL -> observed public route -> safe probe -> visual editorial candidate.

No invented URLs or selectors, no auth, no execution of model-proposed actions.
A candidate is not a native capture, a film approval, or a release.
"""
from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

from backend.story_discovery import discover_public_product, public_same_origin
from backend.product_explorer import inspect, allowed
from backend.source_action_preflight import probe_public_action
from backend.outcome_editorial_gate import pair_from_probe, evaluate


# Select a bounded set of independently observed local controls. Settings can
# be investigated, but only visual editorial evidence can admit a core payoff.
LOW_VALUE = re.compile(r"(?i)\b(?:dark mode|light mode|theme toggle|menu|read more|learn more)\b")


def local_url(url):
    u = urlsplit(url)
    return (u.scheme, u.netloc.lower(), u.path.rstrip("/") or "/")


def candidates(research):
    """Stable page/control ordering, distribute budget across actual routes."""
    origin = research["requested_url"]
    queues = []
    for page in research.get("pages", []):
        if not public_same_origin(page["url"], origin):
            continue
        controls = [c for c in page["controls"]
                    if c.get("kind") in ("button", "tab")
                    and c.get("policy", {}).get("class") == "reversible_local_ui"
                    and not c.get("policy", {}).get("requires_authorization", True)]
        controls.sort(key=lambda c: (bool(LOW_VALUE.search(c["text"])), c["kind"] != "button"))
        if controls:
            queues.append((page, controls))
    # Deeper pages get first look; interleave rather than exhaust one route.
    queues.sort(key=lambda pc: local_url(pc[0]["url"]) == local_url(origin))
    out = []
    while any(cs for _, cs in queues):
        for page, cs in queues:
            if cs:
                out.append((page, cs.pop(0)))
    return out


def run(url, out, *, max_pages=3, max_probes=3, request=None):
    if type(max_probes) is not int or not 1 <= max_probes <= 3:
        raise ValueError("Expected 1..3 public action probes")
    out = Path(out)
    out.mkdir(mode=0o700, parents=True, exist_ok=False)
    research = discover_public_product(url, out / "research", max_pages=max_pages,
                                       route_focus=True)
    pairs, routes, attempts = [], {}, []
    inspections, blocked, attempted_controls = {}, set(), set()
    for page, hint in candidates(research):
        if len(attempts) >= max_probes:
            break
        target = page["url"]
        if target in blocked:
            continue
        if target not in inspections:
            try:
                report = inspect(target, out / ("inspect-" + page["id"]))
                if (not public_same_origin(report["url"], url)
                        or local_url(report["url"]) != local_url(target)):
                    raise ValueError("Fresh inspection changed public route")
                inspections[target] = report
            except Exception as exc:
                blocked.add(target)
                attempts.append({"route": target, "decision": "inspection_failed",
                                 "error_type": type(exc).__name__})
                continue
        report = inspections[target]
        matches = [c for c in report["controls"]
                   if c.get("kind") == hint["kind"] and c.get("text") == hint["text"]
                   and allowed(c, report["url"])]
        if len(matches) != 1:
            continue
        control = matches[0]
        key = (target, control["id"])
        if key in attempted_controls:
            continue
        attempted_controls.add(key)
        directory = out / ("probe-" + str(len(attempts)+1))
        row = {"route": target, "observed_id": control["id"], "label": control["text"]}
        try:
            proof = probe_public_action(target, report, control["id"], directory,
                                        local_only=True)
            row["decision"] = proof["decision"]
            if proof["decision"] == "authentication_required":
                blocked.add(target)
            if proof["decision"] == "visible_outcome_candidate":
                pair = pair_from_probe(report, control["id"], proof, directory)
                # Namespaced mapping keeps same control IDs on different routes
                # from aliasing each other inside the existing editorial gate.
                global_id = "a" + str(len(pairs)+1)
                routes[global_id] = {**row, "proof_dir": str(directory)}
                pair["id"] = global_id
                pair["label"] = (urlsplit(target).path + ": " + control["text"])[:160]
                pairs.append(pair)
        except Exception as exc:
            row.update(decision="probe_failed", error_type=type(exc).__name__)
        attempts.append(row)
    result = {"schema":"sauce-route-outcome-discovery-v1", "source_url":url,
              "routes":[{"id":p["id"],"url":p["url"],"title":p["title"]}
                        for p in research["pages"]],
              "attempts":attempts, "route_failures":research.get("failures", []),
              "editorial":None,"selected":None,"creative_approved":False,
              "production_ready":False}
    # Save the evidence trail before a potentially unavailable provider call.
    receipt=out/"receipt.json"
    receipt.write_text(json.dumps(result,indent=2)+"\n")
    if pairs:
        editorial=evaluate(research["pages"][0]["title"][:160],pairs,out/"editorial",request=request)
        result["editorial"]=editorial
        result["selected"]=routes.get(editorial["admitted_id"])
        receipt.write_text(json.dumps(result,indent=2)+"\n")
    return result

def resume_review(out, *, request=None):
    """Resume only the stored outcome evidence; no fresh navigation or clicks."""
    out = Path(out)
    receipt = out / "receipt.json"
    result = json.loads(receipt.read_text())
    research = json.loads((out/"research"/"research.json").read_text())
    if (result.get("schema") != "sauce-route-outcome-discovery-v1"
            or result.get("source_url") != research.get("requested_url")):
        raise ValueError("Route checkpoint mismatch")
    pages = {p["url"]: p for p in research["pages"]}
    pairs, mapping = [], {}
    for i, attempt in enumerate(result["attempts"], 1):
        if attempt["decision"] != "visible_outcome_candidate":
            continue
        target = attempt["route"]
        page = pages[target]
        if not re.fullmatch(r"p[0-4]",page["id"]) or not public_same_origin(target,result["source_url"]):
            raise ValueError("Invalid checkpoint route")
        report = json.loads((out/("inspect-"+page["id"])/"inspection.json").read_text())
        if report["url"] != target:
            raise ValueError("Inspection route mismatch")
        directory = out/("probe-"+str(i))
        proof = json.loads((directory/"outcome.json").read_text())
        pair = pair_from_probe(report,attempt["observed_id"],proof,directory)
        if pair["label"] != attempt["label"]:
            raise ValueError("Checkpoint control mismatch")
        ident = "a"+str(len(pairs)+1)
        mapping[ident] = {**attempt,"proof_dir":str(directory)}
        pair["id"] = ident
        pair["label"] = (urlsplit(target).path+": "+pair["label"])[:160]
        pairs.append(pair)
    if not pairs:
        return result
    editorial = evaluate(research["pages"][0]["title"][:160],pairs,out/"editorial",
                         request=request,resume=True)
    result["editorial"] = editorial
    result["selected"] = mapping.get(editorial["admitted_id"])
    with tempfile.NamedTemporaryFile(mode="w",dir=out,prefix=".receipt-",delete=False) as stream:
        temp = Path(stream.name)
        stream.write(json.dumps(result,indent=2)+"\n")
    temp.replace(receipt)
    return result


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--url");p.add_argument("--out",type=Path,required=True)
    p.add_argument("--resume",action="store_true",help="Review stored evidence only; never crawl again")
    p.add_argument("--max-pages",type=int,default=3);p.add_argument("--max-probes",type=int,default=3)
    a=p.parse_args()
    if a.resume:
        if a.url: p.error("--resume uses the recorded URL, not a new URL")
        result=resume_review(a.out)
    else:
        if not a.url: p.error("--url required for a new discovery")
        result=run(a.url,a.out,max_pages=a.max_pages,max_probes=a.max_probes)
    print(json.dumps(result,indent=2))
