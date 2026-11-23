"""Read-only Stagehand hints mapped to independently observed Sauce public controls."""
from __future__ import annotations
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from backend.product_explorer import allowed, normalize
from scripts.capture_safety import validate_public_url

SCHEMA = "sauce-stagehand-observations-v1"


def _canonical(s):
    return re.sub(r"\s+", " ", str(s).strip()).casefold()


def choose_observed_action(report: dict, observations: dict):
    """Fail closed. Never trust an AI-generated selector, action or claimed result."""
    if (not isinstance(observations, dict) or observations.get("schema") != SCHEMA
            or _canonical(observations.get("url", "")) !=
               _canonical(report.get("source_url", report.get("url", "")))):
        return None
    hints = observations.get("observations")
    if not isinstance(hints, list) or len(hints) > 6:
        return None
    source = report.get("url", "")
    controls = [c for c in report.get("controls", [])
                if isinstance(c, dict) and c.get("text") and allowed(c, source)]
    for hint in hints:
        if not isinstance(hint, dict):
            continue
        description = hint.get("description")
        if not isinstance(description, str) or not 4 <= len(description) <= 180:
            continue
        desc = _canonical(description)
        # Require a complete, uniquely matched text label. No fuzzy short-token
        # selection and no Stagehand selector coordinates are ever accepted.
        candidates = [c for c in controls if len(_canonical(c["text"])) >= 4 and (
            _canonical(c["text"]) == desc or re.search(
                r"(?<!\w)" + re.escape(_canonical(c["text"])) + r"(?!\w)", desc))]
        if len(candidates) != 1:
            continue
        candidate = candidates[0]
        if not re.fullmatch(r"a\d{1,3}", candidate.get("id", "")):
            continue
        return normalize({
            "mode": "interactive", "action_ids": [candidate["id"]],
            "title": report.get("title", "Product demo"),
            "reason": "Stagehand proposed an observed safe control; real outcome not yet verified",
        }, report)
    return None


def run_stagehand_discovery(report: dict, private_dir: Path, *, timeout_seconds=95):
    """Opt-in isolated SDK subprocess; exceptions and no-key cases fall back."""
    if os.getenv("SAUCE_STAGEHAND_DISCOVERY") != "1":
        return None
    key = os.getenv("GOOGLE_GENERATIVE_AI_API_KEY") or os.getenv("GEMINI_API_KEY")
    bb = os.getenv("BROWSERBASE_API_KEY")
    if not key and not (bb and os.getenv("SAUCE_STAGEHAND_BROWSER") == "browserbase"):
        return None
    url = report["source_url"]
    validate_public_url(url)
    private_dir = Path(private_dir)
    private_dir.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parents[1]
    interpreter = os.getenv("SAUCE_STAGEHAND_PYTHON", sys.executable)
    try:
        task = subprocess.run(
            [interpreter, "-m", "scripts.stagehand_public_discovery",
             "--url", url, "--inspection", str(private_dir / "inspection.json")],
            cwd=root, env=os.environ.copy(), text=True, capture_output=True,
            timeout=timeout_seconds, check=False,
        )
        if task.returncode != 0 or len(task.stdout) > 32000:
            return None
        data = json.loads(task.stdout)
        if data.get("schema") != SCHEMA or data.get("url") != url:
            return None
        plan = choose_observed_action(report, data)
        # Private receipt is intentionally metadata only, not model output,
        # browser screenshots, selectors, secrets or alleged product results.
        (private_dir / "stagehand-discovery.json").write_text(json.dumps({
            "schema": SCHEMA, "url": url,
            "provider": data.get("provider"),
            "observations_count": len(data.get("observations", [])),
            "selected_observed_id": plan["action_ids"][0] if plan else None,
            "outcome_verified": False, "creative_approved": False,
        }, indent=2) + "\n")
        return plan
    except (OSError, subprocess.TimeoutExpired, ValueError, TypeError, KeyError):
        return None
