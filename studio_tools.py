"""Hermes-facing production tools: accept decisions, produce verifiable media.

No built-in creative model and no autonomous storyboard heuristics. Assets are
read exclusively from proven Sauce capture runs and a licensed local asset root.
"""
from __future__ import annotations

import fcntl
import json
import os
from pathlib import Path
import shutil
from urllib.parse import urlsplit

from . import director, tools
from .studio import render_project as engine


def _receipt(**items):
    return json.dumps(items, ensure_ascii=False)


def _run(run_id: str) -> tuple[str, Path]:
    ident = tools._id(run_id)
    return ident, tools._dir(ident)


def _asset_name(run_id: str, name: str, kind: str) -> str:
    approved_exts = (
        {".mp3", ".wav", ".ogg", ".m4a"} if kind == "audio"
        else {".png", ".jpg", ".jpeg"}
    )
    original = director._asset(name, approved_exts)
    stage_dir = engine.STATIC / kind
    stage_dir.mkdir(parents=True, exist_ok=True)
    saved = f"{run_id}-{original.name}"
    shutil.copyfile(original, stage_dir / saved)
    return f"{kind}/{saved}"


def compose(args, **kwargs):
    """Store a validated Hermes-selected composition for one captured run."""
    try:
        ident, folder = _run(args.get("run_id"))
        # Composite the ORIGINAL video when available. Reusing final.mp4
        # would bake in the legacy 720p zoom, scaling and second encode.
        source = folder / "recording.webm"
        if not source.is_file():
            source = folder / "final.mp4"  # Compatibility with older runs
        capture_file = folder / "capture.json"
        if (not source.is_file() or source.is_symlink()
            or not capture_file.is_file() or capture_file.is_symlink()):
            raise ValueError("Real browser capture receipt and original recording required")
        receipt = json.loads(capture_file.read_text())
        actual_url = receipt.get("url")
        if not isinstance(actual_url, str) or not actual_url.startswith("https://"):
            raise ValueError("No verified public source URL in capture receipt")
        proposed = args.get("project")
        if not isinstance(proposed, dict):
            raise ValueError("Supply a complete versioned StudioProject object")
        # Copy to isolate each run from subsequent edits/renders of the source.
        project = json.loads(json.dumps(proposed))
        if len(project.get("scenes", [])) != 1:
            raise ValueError("One floating-window scene is supported in v0.4")
        scene = project["scenes"][0]
        browser = scene.get("browser", {})
        visible_url = browser.get("url", "")
        host = (urlsplit(visible_url if visible_url.startswith("https://")
                         else "https://" + visible_url).hostname or "")
        capture_host = (urlsplit(actual_url).hostname or "")
        if host.removeprefix("www.") != capture_host.removeprefix("www."):
            raise ValueError("Browser address must match the captured site")
        stage_dir = engine.STATIC / "footage"
        stage_dir.mkdir(parents=True, exist_ok=True)
        stage_name = f"footage/{ident}{source.suffix}"
        shutil.copyfile(source, engine.STATIC / stage_name)
        scene["footage"] = stage_name
        # The footage is always the actual captured run. Never trust an
        # agent-provided path, license assertion or provenance string.
        project["provenance"] = {"run_id":ident, "source_url":actual_url}

        if project.get("audio"):
            name = args.get("music_asset")
            if not name:
                raise ValueError("music_asset filename required for licensed audio")
            project["audio"]["file"] = _asset_name(ident, name, "audio")
        if project.get("background", {}).get("kind") == "image":
            name = args.get("background_asset")
            if not name:
                raise ValueError("background_asset filename required for image background")
            project["background"]["file"] = _asset_name(ident, name, "backgrounds")

        props = {"project":project}
        engine.validate(props, shutil.which("ffprobe") or "ffprobe")
        target = folder / "studio-project.json"
        target.write_text(json.dumps(props, indent=2))
        return _receipt(ok=True, run_id=ident, project_file=str(target),
                        scenes=1, render_backend="bounded-remotion-ffmpeg")
    except Exception as exc:
        return _receipt(ok=False, error=str(exc)[:800])


def _render_from_saved(run_id: str, preview_time: float | None):
    ident, folder = _run(run_id)
    project = folder / "studio-project.json"
    if not project.is_file():
        raise ValueError("Call sauce_compose first")
    if not (engine.STUDIO/"node_modules"/".bin"/"remotion").is_file():
        raise ValueError("Studio dependencies not installed. Run npm ci in studio/")
    out = folder / ("studio-preview.png" if preview_time is not None
                    else "studio-final.mp4")
    tools.ROOT.mkdir(parents=True, exist_ok=True)
    lock = tools.ROOT / ".studio-render.lock"
    with lock.open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("Studio renderer busy. Only one job can run on this VM.")
        try:
            result = engine.render(
                project, out, preview_at=preview_time,
                browser_exe=os.environ.get("SAUCE_REMOTION_BROWSER") or None
            )
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)
    result["run_id"] = ident
    return _receipt(**result)


def preview(args, **kwargs):
    try:
        time_s = args.get("time_s", 3.0)
        if type(time_s) not in (int, float):
            raise ValueError("time_s must be a number")
        return _render_from_saved(args.get("run_id"), float(time_s))
    except Exception as exc:
        return _receipt(ok=False, error=str(exc)[:800])


def render_project(args, **kwargs):
    try:
        return _render_from_saved(args.get("run_id"), None)
    except Exception as exc:
        return _receipt(ok=False, error=str(exc)[:800])
