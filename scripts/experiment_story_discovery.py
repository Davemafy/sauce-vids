"""Research an authorized public product and test one evidence-grounded Gemini story.

Never executes button actions. All screenshot/research/plan artifacts remain private.
Example:
  python3 scripts/experiment_story_discovery.py --url https://refit.davemafy.xyz \\
      --out .tmp-director-refit/experiment --max-pages 4
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.story_discovery import discover_public_product, direct_story, SCHEMA


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--max-pages", type=int, default=4)
    ap.add_argument("--model", default="gemini-3.1-flash-lite")
    ap.add_argument("--research-only", action="store_true")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    research = discover_public_product(a.url, a.out / "private-research",
                                       max_pages=a.max_pages)
    report = {
        "research_pages": [{"id": p["id"], "url": p["url"],
                            "controls": len(p["controls"]),
                            "high_risk": [
                                {"id": c["id"], "text": c["text"],
                                 "class": c["policy"]["class"]}
                                for c in p["controls"]
                                if c["policy"]["requires_authorization"]]}
                           for p in research["pages"]],
        "mutating_actions_executed": 0,
        "film_generated": False,
        "creative_approved": False,
    }
    if not a.research_only:
        try:
            plan, usage = direct_story(research, model=a.model)
            report["story"] = plan
            report["usage"] = usage
            (a.out / "storyboard.json").write_text(json.dumps(plan, indent=2) + "\n")
        except Exception as e:
            report["model_error"] = type(e).__name__ + ": " + str(e)[:200]
    (a.out / "experiment-receipt.json").write_text(
        json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 1 if report.get("model_error") else 0


if __name__ == "__main__":
    raise SystemExit(main())
