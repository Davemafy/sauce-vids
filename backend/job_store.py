"""Durable bounded job journal for the Sauce public-URL pilot.

No AI calls happen during recovery. Never replay a job that could have made
a billed direction call or performed an external browser interaction.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import secrets
import time

ID = re.compile(r"^[a-f0-9]{24}$")
DONE = frozenset({"needs_review", "needs_access", "needs_key", "failed"})
IN_PROGRESS = frozenset({"inspecting", "directing", "capturing", "rendering"})
MAX_LOAD = 10000


def save_job(root: Path, job_id: str, payload: dict) -> None:
    if not ID.fullmatch(job_id):
        raise ValueError("Invalid job identifier")
    folder = root / job_id
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = folder / (".status-" + secrets.token_hex(8) + ".tmp")
    try:
        with temporary.open("x", encoding="utf-8") as stream:
            os.chmod(temporary, 0o600)
            json.dump(payload, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, folder / "status.json")
    finally:
        temporary.unlink(missing_ok=True)


def _has_verified_export(folder: Path) -> bool:
    """Recover a legacy completed record only when a real receipt exists."""
    file = folder / "export" / "release.json"
    video = folder / "export" / "preview.mp4"
    if not (file.is_file() and video.is_file() and video.stat().st_size > 1024):
        return False
    try:
        receipt = json.loads(file.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return False
    return (receipt.get("continuous_motion") is True
            and receipt.get("source_verified") is True)


def recover_jobs(root: Path) -> tuple[dict[str, dict], list[str]]:
    """Return existing records and truly untouched pending jobs to enqueue.

    A queued job which reached inspection, direction, capture or rendering
    must NOT be automatically rerun: we cannot certify whether it consumed
    the one paid direction request before the process died.
    """
    jobs: dict[str, dict] = {}
    pending: list[str] = []
    for folder in sorted(root.iterdir(), key=lambda x: x.name):
        if len(jobs) >= MAX_LOAD:
            break
        if not (folder.is_dir() and not folder.is_symlink()
                and ID.fullmatch(folder.name)):
            continue
        status_file = folder / "status.json"
        if not status_file.is_file() or status_file.is_symlink():
            continue
        try:
            job = json.loads(status_file.read_text(encoding="utf-8"))
        except (ValueError, OSError, UnicodeError):
            continue
        if not isinstance(job, dict) or job.get("id") != folder.name:
            continue
        status = job.get("status")
        stage = job.get("stage")
        if status == "queued":
            if stage == "queued":
                pending.append(folder.name)
            elif stage == "needs_review" and _has_verified_export(folder):
                # Legacy state: finished film and receipt, pending status.
                job.update(status="needs_review", updated_at=time.time(),
                           message="Recovered verified existing film")
                save_job(root, folder.name, job)
            elif stage in DONE and stage != "needs_review":
                job.update(status=stage, updated_at=time.time())
                save_job(root, folder.name, job)
            else:
                job.update(
                    status="failed", stage="failed",
                    last_stage=stage,
                    updated_at=time.time(),
                    error="WorkerInterrupted",
                    message=("The worker restarted during production. "
                             "No automatic paid direction call was repeated. "
                             "Start a new job if you still need this film."),
                )
                save_job(root, folder.name, job)
        jobs[folder.name] = job
    return jobs, pending
