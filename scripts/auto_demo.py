#!/usr/bin/env python3
"""Run the actual Sauce Vids one-URL pipeline without a configured Hermes model.

Example:
SAUCE_ALLOWED_HOSTS=www.brimble.io,brimble.io python3 scripts/auto_demo.py \
  --url https://www.brimble.io/agent --project brimble --duration 20
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description="Record and edit a truthful public-site demo")
    parser.add_argument("--url", required=True)
    parser.add_argument("--project", default="demo")
    parser.add_argument("--duration", type=float, default=20)
    parser.add_argument("--music-asset")
    parser.add_argument("--background-asset")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "sauce_vids", root / "__init__.py", submodule_search_locations=[str(root)])
    module = importlib.util.module_from_spec(spec)
    sys.modules["sauce_vids"] = module
    spec.loader.exec_module(module)

    result = json.loads(module.autopilot.run({
        "url": args.url, "project": args.project,
        "duration_seconds": args.duration,
        "music_asset": args.music_asset,
        "background_asset": args.background_asset,
    }))
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
