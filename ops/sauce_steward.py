#!/usr/bin/env python3
"""Persistent, bounded Sauce verification worker. No AI calls or code edits.

Only known job types execute. State survives ChatGPT logout, process crashes
and VM reboot. A separate, clean main checkout preserves production worktrees.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

STATE = Path(os.environ.get("SAUCE_STEWARD_STATE", "/var/lib/sauce-steward"))
DB_FILE = STATE / "jobs.sqlite3"
STATUS_FILE = STATE / "status.json"
REPO = "https://github.com/Davemafy/sauce-vids.git"
BRANCH = "main"
PROOF_URL = "https://devmcp.davemafy.xyz/sauce-motion-phase2/result-payoff-camera/master-1080p60.mp4"
URLS = (
    "https://devmcp.davemafy.xyz/sauce-app/studio",
    "https://devmcp.davemafy.xyz/sauce-app/studio/samples",
    "https://devmcp.davemafy.xyz/sauce-motion-phase2/result-payoff-camera/",
)
KINDS = frozenset(("sync-main", "audit-proof", "smoke-web", "test-main"))
POLL_SECONDS = 600
PROOF_INTERVAL_SECONDS = 24 * 3600
SMOKE_INTERVAL_SECONDS = 3600
MAX_ATTEMPTS = 2


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def run(command: list[str], *, cwd: Path | None = None,
        timeout: int = 60) -> str:
    cp = subprocess.run(command, cwd=cwd, text=True,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        timeout=timeout, check=False,
                        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
    if cp.returncode:
        raise RuntimeError(f"{command[0]} exited {cp.returncode}: {cp.stdout[-1700:]}")
    return cp.stdout.strip()


def connect() -> sqlite3.Connection:
    STATE.mkdir(mode=0o700, parents=True, exist_ok=True)
    db = sqlite3.connect(DB_FILE, timeout=15)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA busy_timeout=15000")
    db.execute("""
        CREATE TABLE IF NOT EXISTS jobs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'queued',
            attempts INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            started_at TEXT,
            finished_at TEXT,
            result_json TEXT,
            error TEXT
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS jobs_status ON jobs(status,id)")
    db.commit()
    return db


def enqueue(db: sqlite3.Connection, kind: str, *, dedupe: bool = True) -> int:
    if kind not in KINDS:
        raise ValueError("Unsupported job kind")
    if dedupe:
        old = db.execute(
            "SELECT id FROM jobs WHERE kind=? AND status IN ('queued','running')"
            " ORDER BY id DESC LIMIT 1", (kind,)).fetchone()
        if old:
            return int(old["id"])
    cur = db.execute(
        "INSERT INTO jobs(kind,status,created_at) VALUES(?, 'queued', ?)",
        (kind, now()))
    db.commit()
    return int(cur.lastrowid)


def recover(db: sqlite3.Connection) -> None:
    db.execute(
        "UPDATE jobs SET status='queued',started_at=NULL "
        "WHERE status='running' AND attempts < ?", (MAX_ATTEMPTS,))
    db.execute(
        "UPDATE jobs SET status='failed',finished_at=?, "
        "error='Interrupted too many times' WHERE status='running'",
        (now(),))
    db.commit()


def save_status(updates: dict) -> None:
    try:
        data = json.loads(STATUS_FILE.read_text())
    except (FileNotFoundError, ValueError):
        data = {}
    data.update(updates)
    data["updated_at"] = now()
    tmp = STATUS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    tmp.replace(STATUS_FILE)


def sync_main() -> dict:
    dest = STATE / "source-main"
    if not dest.exists():
        run(["git", "clone", "--depth", "1", "--branch", BRANCH,
             "--single-branch", REPO, str(dest)], timeout=120)
    else:
        if not (dest / ".git").is_dir():
            raise RuntimeError("Existing source-main is not a git checkout")
        if run(["git", "status", "--porcelain"], cwd=dest):
            raise RuntimeError("Preserving dirty independent source-main checkout")
        if run(["git", "branch", "--show-current"], cwd=dest) != BRANCH:
            raise RuntimeError("Source checkout is not on main")
        remote = run(["git", "remote", "get-url", "origin"], cwd=dest)
        if remote != REPO:
            raise RuntimeError("Unexpected source checkout origin")
        run(["git", "pull", "--ff-only", "--no-rebase"], cwd=dest, timeout=120)
    sha = run(["git", "rev-parse", "HEAD"], cwd=dest)
    run(["python3", "-m", "py_compile",
         "backend/live_capture.py", "backend/live_render.py",
         "backend/url_engine.py", "scripts/result_payoff.py",
         "scripts/modal_depth_capture.py"], cwd=dest, timeout=30)
    return {"main_sha": sha, "checkout": str(dest),
            "check": "source syntax passed; no working tree changed"}


def smoke_web() -> dict:
    checks = []
    for url in URLS:
        req = Request(url, method="HEAD", headers={"User-Agent": "Sauce-Steward/1"})
        try:
            with urlopen(req, timeout=12) as resp:
                code = resp.status
        except HTTPError as ex:
            code = ex.code
        except (URLError, TimeoutError, OSError) as ex:
            checks.append({"url": url, "error": type(ex).__name__})
            continue
        checks.append({"url": url, "status": code})
    if not all(item.get("status") == 200 for item in checks):
        raise RuntimeError("Web smoke failed: " + json.dumps(checks))
    return {"checks": checks}


def audit_proof() -> dict:
    # This URL is a PINNED reference film, not a promise of the newest film.
    temp = STATE / "proof-audit"
    temp.mkdir(mode=0o700, exist_ok=True)
    master = temp / "reference.mp4"
    req = Request(PROOF_URL, headers={"User-Agent": "Sauce-Steward/1"})
    max_bytes = 50 * 1024 * 1024
    with urlopen(req, timeout=25) as resp, master.open("wb") as target:
        content_length = int(resp.headers.get("Content-Length", "0") or 0)
        if content_length > max_bytes:
            raise RuntimeError("Reference MP4 exceeds 50 MB bound")
        size = 0
        digest = hashlib.sha256()
        while chunk := resp.read(262144):
            size += len(chunk)
            if size > max_bytes:
                raise RuntimeError("Reference MP4 exceeded download bound")
            target.write(chunk)
            digest.update(chunk)
    probe = json.loads(run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration,size:stream=codec_type,codec_name,width,height,"
         "r_frame_rate,nb_frames,sample_rate", "-of", "json", str(master)],
        timeout=20))
    video = next((s for s in probe["streams"]
                  if s.get("codec_type") == "video"), None)
    if not video or video.get("width") != 1920 or video.get("height") != 1080 \
            or video.get("r_frame_rate") != "60/1":
        raise RuntimeError("Reference failed 1080p60 stream check")
    run(["ffmpeg", "-v", "error", "-xerror", "-i", str(master),
         "-f", "null", "-"], timeout=90)
    # Keep a minimal, private frame sample for later visual review.
    frame = temp / "modal-entry-frame48.jpg"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-i", str(master), "-vf", "select=eq(n\\,48)",
         "-frames:v", "1", str(frame)], timeout=30)
    result = {"source_url": PROOF_URL, "reference_only": True,
              "sha256": digest.hexdigest(),
              "bytes": size, "duration": probe["format"]["duration"],
              "frames": video.get("nb_frames"), "codec": video.get("codec_name"),
              "full_decode": True, "frame48": str(frame),
              "visual_status": "requires human review; known modal occlusion"}
    (temp / "receipt.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def test_main() -> dict:
    dest = STATE / "source-main"
    if not (dest / ".git").is_dir():
        raise RuntimeError("Sync main before requesting tests")
    if run(["git", "status", "--porcelain"], cwd=dest):
        raise RuntimeError("Refusing to test a dirty source checkout")
    env_python = "/opt/sauce-vids/.venv/bin/python"
    python = env_python if Path(env_python).is_file() else sys.executable
    output = run([python, "-m", "pytest", "-q",
                  "tests/test_product_explorer.py",
                  "tests/test_url2video_api.py"], cwd=dest, timeout=180)
    return {"suite": "bounded URL pilot tests",
            "summary": output[-2000:],
            "main_sha": run(["git", "rev-parse", "HEAD"], cwd=dest)}


OPERATIONS = {
    "sync-main": sync_main,
    "smoke-web": smoke_web,
    "audit-proof": audit_proof,
    "test-main": test_main,
}


def run_next(db: sqlite3.Connection) -> bool:
    row = db.execute(
        "SELECT id,kind FROM jobs WHERE status='queued' "
        "ORDER BY id ASC LIMIT 1").fetchone()
    if not row:
        return False
    job_id = int(row["id"])
    updated = db.execute(
        "UPDATE jobs SET status='running',attempts=attempts+1,"
        "started_at=? WHERE id=? AND status='queued'",
        (now(), job_id))
    db.commit()
    if updated.rowcount != 1:
        return False
    print(f"{now()} START job={job_id} kind={row['kind']}", flush=True)
    try:
        result = OPERATIONS[row["kind"]]()
        db.execute(
            "UPDATE jobs SET status='completed',finished_at=?,result_json=?,"
            "error=NULL WHERE id=?",
            (now(), json.dumps(result, sort_keys=True), job_id))
        save_status({"last_completed_kind": row["kind"],
                     "last_completed_at": now(),
                     **({"main_sha": result["main_sha"]}
                        if "main_sha" in result else {}),
                     **({"proof_audit": result}
                        if row["kind"] == "audit-proof" else {}),
                     **({"web_smoke": result}
                        if row["kind"] == "smoke-web" else {})})
        print(f"{now()} DONE job={job_id}", flush=True)
    except Exception as ex:
        db.execute(
            "UPDATE jobs SET status='failed',finished_at=?,error=? WHERE id=?",
            (now(), f"{type(ex).__name__}: {str(ex)[:1800]}", job_id))
        save_status({"last_failed_kind": row["kind"], "last_failed_at": now(),
                     "last_error": f"{type(ex).__name__}: {str(ex)[:700]}"})
        print(f"{now()} FAILED job={job_id} {type(ex).__name__}: {ex}", flush=True)
    db.commit()
    return True


def daemon() -> None:
    db = connect()
    recover(db)
    save_status({"service": "active", "pid": os.getpid(),
                 "policy": "read-only QA; no AI calls, expenses, or code edits"})
    enqueue(db, "sync-main")
    enqueue(db, "smoke-web")
    enqueue(db, "audit-proof")
    next_poll = 0.
    last_sha = None
    last_proof = time.monotonic()
    last_smoke = time.monotonic()
    print(f"{now()} Sauce Steward online, {POLL_SECONDS}s polling", flush=True)
    while True:
        tick = time.monotonic()
        if tick >= next_poll:
            try:
                remote = run(["git", "ls-remote", REPO, "refs/heads/main"],
                             timeout=20).split()[0]
                if len(remote) != 40:
                    raise RuntimeError("Invalid remote SHA")
                if remote != last_sha:
                    enqueue(db, "sync-main")
                    last_sha = remote
                save_status({"remote_main_sha": remote, "last_polled_at": now()})
            except Exception as ex:
                save_status({"last_poll_error": f"{type(ex).__name__}: {str(ex)[:250]}"})
                print(f"{now()} POLL ERROR {ex}", flush=True)
            next_poll = tick + POLL_SECONDS
        if tick - last_smoke >= SMOKE_INTERVAL_SECONDS:
            enqueue(db, "smoke-web")
            last_smoke = tick
        if tick - last_proof >= PROOF_INTERVAL_SECONDS:
            enqueue(db, "audit-proof")
            last_proof = tick
        if not run_next(db):
            time.sleep(5)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("daemon")
    sub.add_parser("status")
    job = sub.add_parser("enqueue")
    job.add_argument("kind", choices=sorted(KINDS))
    sub.add_parser("once")
    args = parser.parse_args()
    if args.command == "daemon":
        daemon()
        return
    db = connect()
    if args.command == "enqueue":
        print(json.dumps({"job_id": enqueue(db, args.kind), "kind": args.kind}))
    elif args.command == "once":
        print(json.dumps({"ran_job": run_next(db)}))
    else:
        status = json.loads(STATUS_FILE.read_text()) if STATUS_FILE.is_file() else {}
        rows = db.execute(
            "SELECT id,kind,status,attempts,created_at,finished_at,error "
            "FROM jobs ORDER BY id DESC LIMIT 12").fetchall()
        print(json.dumps({"status": status, "recent_jobs": [dict(x) for x in rows]},
                         indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
