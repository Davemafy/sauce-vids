"""Durable bounded job journal for the Sauce public-URL pilot.

No AI calls happen during recovery. Never replay a job that could have made
a billed direction call or performed an external browser interaction.
"""
from __future__ import annotations

from hashlib import file_digest, sha256
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

    Resume rendering only from a source-verified checkpoint with budget left.
    Other interrupted jobs never repeat direction or browser actions.
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
            elif stage == "rendering" and (
                (checkpoint := load_render_checkpoint(folder, job.get("url", ""))) and checkpoint["attempts"] < 2
            ):
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
        # Older successful jobs may predate the continuous-footage status
        # fields. Recover their label ONLY from an existing verified receipt.
        if job.get("status") == "needs_review" and _has_verified_export(folder):
            missing_mode = job.get("render_mode") != "continuous-browser-capture"
            missing_capture = job.get("capture_mode") not in ("interactive", "showcase")
            if missing_mode or missing_capture:
                receipt = json.loads((folder / "export" / "release.json").read_text())
                if missing_mode:
                    job["render_mode"] = "continuous-browser-capture"
                if missing_capture and receipt.get("film_mode") in ("interactive", "showcase"):
                    job["capture_mode"] = receipt["film_mode"]
                save_job(root, folder.name, job)
        jobs[folder.name] = job
    return jobs, pending


def write_render_checkpoint(folder: Path, data: dict) -> None:
    """Publish only a fully persisted renderer input manifest."""
    temporary = folder / ".render-checkpoint.tmp"
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(data, stream)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, folder / "render-checkpoint.json")


def load_render_checkpoint(folder: Path, url: str):
    """Recover a local capture only when both source and receipt identities match."""
    motion = folder / "private" / "motion"
    try:
        data = json.loads((folder / "render-checkpoint.json").read_text())
        if data["url"] != url or data["attempts"] not in (0, 1, 2):
            return None
        receipt = (motion / "continuous-capture.json").read_bytes()
        if sha256(receipt).hexdigest() != data["receipt_sha256"]:
            return None
        record = json.loads(receipt)
        if record.get("continuous_recording") is not True:
            return None
        with (motion / "continuous-source.webm").open("rb") as source:
            if file_digest(source, "sha256").hexdigest() != record["sha256"]:
                return None
        return data
    except (OSError, KeyError, ValueError, TypeError):
        return None
