#!/usr/bin/env python3
"""Bounded, read-only load test of the deployed Sauce private pilot.

No POSTs, no new jobs, no AI direction calls and no credentials in output.
On failure returns nonzero and preserves a private aggregate JSON receipt.
Run only on the authorized host that owns the Unix socket and job records.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import http.client
import json
from pathlib import Path
import random
import socket
import statistics
import time

PRIVATE_SOCKET = Path("/var/lib/sauce-url2video/sauce.sock")
JOBS = Path("/var/lib/sauce-url2video/jobs")
MAX_CLIENTS = 32
MAX_CALLS = 600
MAX_MEDIA_BYTES = 16 * 1024 * 1024


class LocalUnixConnection(http.client.HTTPConnection):
    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(str(PRIVATE_SOCKET))


def source_media() -> tuple[str, int]:
    choices: list[tuple[str, int]] = []
    if not PRIVATE_SOCKET.is_socket():
        raise RuntimeError("Private Unix socket missing")
    for item in JOBS.glob("*/status.json"):
        try:
            metadata = json.loads(item.read_text())
            release = json.loads((item.parent / "export" / "release.json").read_text())
            file = item.parent / "export" / "preview.mp4"
            length = file.stat().st_size
            if (metadata.get("status") == "needs_review"
                and release.get("continuous_motion") is True
                and release.get("source_verified") is True
                and 1024 < length <= MAX_MEDIA_BYTES):
                choices.append((item.parent.name, length))
        except (ValueError, OSError):
            pass
    if not choices:
        raise RuntimeError("No verified source-true media for safe read-only test")
    return max(choices, key=lambda x:x[1])


def make_tasks(health: int, status: int, media: int) -> list[tuple[str, int]]:
    values = (health, status, media)
    if any(type(x) is not int or x < 0 for x in values) or not 0 < sum(values) <= MAX_CALLS:
        raise ValueError(f"Test must contain 1..{MAX_CALLS} read-only calls")
    work = ([(name, i) for name, count in
             (("health", health),("status", status),("media", media))
             for i in range(count)])
    random.Random(3).shuffle(work)
    return work


def one(kind: str, _: int, job_id: str, media_bytes: int, timeout: int = 9) -> dict:
    start = time.monotonic()
    conn = None
    try:
        conn = (http.client.HTTPConnection("127.0.0.1", 8767, timeout=timeout)
                if kind == "health" else
                LocalUnixConnection("localhost", timeout=timeout))
        route = ("/health" if kind == "health"
                 else "/v1/jobs/" + job_id + ("/preview.mp4" if kind == "media" else ""))
        conn.request("GET", route)
        response = conn.getresponse()
        body = response.read()
        good = response.status == 200
        if kind == "media":
            good = good and len(body) == media_bytes and body[4:8] == b"ftyp"
        else:
            expected = "ready" if kind == "health" else "needs_review"
            good = good and json.loads(body).get("status") == expected
        return {"kind":kind,"ok":good,"elapsed_ms":(time.monotonic()-start)*1000,
                "error":None if good else f"HTTP{response.status}_invalid_response"}
    except Exception as exc:
        return {"kind":kind,"ok":False,"elapsed_ms":(time.monotonic()-start)*1000,
                "error":type(exc).__name__}
    finally:
        if conn is not None:
            conn.close()


def summarize(rows: list[dict], clients: int) -> dict:
    details: dict[str, dict] = {}
    for kind in ("health","status","media"):
        subset = [r for r in rows if r["kind"] == kind]
        if not subset:
            continue
        times = sorted(r["elapsed_ms"] for r in subset)
        errors = Counter(str(r["error"]) for r in subset if not r["ok"])
        details[kind] = {
            "requests":len(subset),
            "errors":sum(errors.values()),
            "error_types":dict(errors),
            "p50_ms":round(statistics.median(times), 2),
            "p95_ms":round(times[max(0,int(len(times)*.95)-1)],2),
            "max_ms":round(times[-1],2),
        }
    return {"clients":clients,"requests":len(rows),
            "errors":sum(not x["ok"] for x in rows),"endpoints":details,
            "scope":"GET-only private health/status/source-verified media; no new jobs, no paid inference"}


def run_profile(clients: int, health: int, status: int, media: int) -> dict:
    if type(clients) is not int or not 1 <= clients <= MAX_CLIENTS:
        raise ValueError(f"Concurrency must be 1..{MAX_CLIENTS}")
    jobs = make_tasks(health,status,media)
    job_id,media_bytes=source_media()
    started=time.monotonic()
    with ThreadPoolExecutor(max_workers=clients) as pool:
        rows=list(pool.map(lambda item:one(*item,job_id,media_bytes),jobs))
    report=summarize(rows,clients)
    report["total_wall_seconds"]=round(time.monotonic()-started,3)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clients",type=int,default=12)
    parser.add_argument("--health",type=int,default=100)
    parser.add_argument("--status",type=int,default=120)
    parser.add_argument("--media",type=int,default=24)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    result=run_profile(args.clients,args.health,args.status,args.media)
    print(json.dumps(result,sort_keys=True,indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
        args.output.chmod(0o600)
    if result["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
