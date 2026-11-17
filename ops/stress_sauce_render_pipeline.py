#!/usr/bin/env python3
"""Bounded real Chromium + FFmpeg throughput test on Sauce's own public demo.

Zero inference, zero job POSTs, zero customer jobs. The recorded page is owned
by Sauce; every output frame comes from a real Chromium capture and is verified
by the production live_render module. Run only on the authorized Vultr host.

Example:
  sudo -u devmcp env GEMINI_API_KEY='' nice -n 10 \
    /opt/sauce-vids/.venv/bin/python ops/stress_sauce_render_pipeline.py
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = Path("/var/lib/sauce-steward/qa-logs/render-stress-20261117")
INSPECTION = OUT / "inspection" / "inspection.json"
URL = "https://devmcp.davemafy.xyz/sauce-app/studio/samples"
PROD_JOBS = Path("/var/lib/sauce-url2video/jobs")
MIN_AVAILABLE_KB = 4 * 1024 * 1024
MIN_FREE_BYTES = 8 * 1024**3
RUN_TIMEOUT_S = {"capture": 125, "render": 270}
MAX_PROFILES = (1, 2, 4)


def check_no_production_jobs():
    for path in PROD_JOBS.glob("*/status.json"):
        try:
            j = json.loads(path.read_text())
            if j.get("status") == "queued":
                raise RuntimeError("Live or queued customer job: abort staging stress run")
        except (OSError, UnicodeError, ValueError):
            continue


def mem_available_kb():
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1])
    raise RuntimeError("MemAvailable missing")


def check_resource_budget():
    if mem_available_kb() < MIN_AVAILABLE_KB:
        raise RuntimeError("Too little available RAM for safe staging")
    if shutil.disk_usage(OUT).free < MIN_FREE_BYTES:
        raise RuntimeError("Insufficient free storage for staging")


def cpu_stats():
    fields = Path("/proc/stat").read_text().splitlines()[0].split()[1:]
    nums = [int(s) for s in fields[:8]]
    return sum(nums), nums[3] + nums[4]


def size_tree(root: Path):
    return sum(p.stat().st_size for p in root.rglob("*") if p.is_file())


def sha256(file: Path):
    h = hashlib.sha256()
    with file.open("rb") as stream:
        for data in iter(lambda: stream.read(2**20), b""):
            h.update(data)
    return h.hexdigest()


def run_stage(cmd: list[str], logfile: Path, stage: str, abort: threading.Event,
              active: dict[int, subprocess.Popen], lock: threading.Lock):
    start = time.monotonic()
    with logfile.open("wb") as stream:
        proc = subprocess.Popen(cmd, stdout=stream, stderr=subprocess.STDOUT,
                                cwd=ROOT, start_new_session=True,
                                env={**os.environ, "GEMINI_API_KEY": "",
                                     "SAUCE_SAFE_PUBLIC_ONLY": "1"})
        with lock:
            active[proc.pid] = proc
        try:
            while proc.poll() is None:
                if abort.is_set() or time.monotonic() - start > RUN_TIMEOUT_S[stage]:
                    os.killpg(proc.pid, signal.SIGTERM)
                    try:
                        proc.wait(timeout=4)
                    except subprocess.TimeoutExpired:
                        os.killpg(proc.pid, signal.SIGKILL)
                        proc.wait(timeout=3)
                    raise RuntimeError("Resource guard or stage timeout in " + stage)
                time.sleep(.25)
            if proc.returncode != 0:
                raise RuntimeError(stage + "_exit_" + str(proc.returncode))
        finally:
            with lock:
                active.pop(proc.pid, None)
    return round(time.monotonic() - start, 3)


def job(index: int, wave: Path, plan: Path, abort: threading.Event,
        active: dict[int, subprocess.Popen], lock: threading.Lock):
    dest = wave / ("job-%02d" % index)
    dest.mkdir(mode=0o700)
    source, export = dest / "source", dest / "export"
    start = time.monotonic()
    result = {"job":index, "ok":False}
    try:
        cap = run_stage([
            sys.executable, "-m", "backend.live_capture",
            "--url", URL, "--out", str(source),
            "--inspection", str(INSPECTION), "--plan", str(plan),
        ], dest / "capture.log", "capture", abort, active, lock)
        result["capture_s"] = cap
        receipt = json.loads((source / "continuous-capture.json").read_text())
        if receipt["source_url"] != URL or not receipt["continuous_recording"]:
            raise RuntimeError("Source provenance verification failed")
        result["source_webm_bytes"] = (source / "continuous-source.webm").stat().st_size
        result["source_sha_verified"] = (
            sha256(source / "continuous-source.webm") == receipt["sha256"])
        if not result["source_sha_verified"]:
            raise RuntimeError("Source digest mismatch")
        enc = run_stage([
            sys.executable, "-m", "backend.live_render",
            "--source", str(source), "--out", str(export),
            "--title", "Sauce sample page", "--story", "Public sample walkthrough",
            "--mode", "showcase",
        ], dest / "render.log", "render", abort, active, lock)
        result["render_s"] = enc
        ledger = json.loads((export / "release.json").read_text())
        if not (ledger["continuous_motion"] is True and
                ledger["source_verified"] is True and
                ledger["source_sha256"] == receipt["sha256"] and
                ledger["master_dimensions"] == [1920,1080] and
                ledger["master_fps"] == 60):
            raise RuntimeError("Release ledger provenance or master mismatch")
        result["master_bytes"] = (export / "master-1080p60.mp4").stat().st_size
        result["preview_bytes"] = (export / "preview.mp4").stat().st_size
        result["duration_s"] = ledger["duration_seconds"]
        result["ok"] = True
    except Exception as e:
        result["error"] = str(e)[:100]
        abort.set()
    result["total_s"] = round(time.monotonic() - start, 3)
    return result


def monitor(abort:threading.Event, stopped:threading.Event, samples:list[dict]):
    prev_total,prev_idle = cpu_stats()
    while not stopped.wait(.5):
        total,idle=cpu_stats()
        dtotal=total-prev_total
        didle=idle-prev_idle
        util=max(0.0,min(100.0,100.0*(1-didle/dtotal))) if dtotal>0 else 0.0
        memory_kb=mem_available_kb()
        samples.append({"cpu_pct":round(util,1),"available_ram_mb":round(memory_kb/1024,1)})
        prev_total,prev_idle=total,idle
        if memory_kb<MIN_AVAILABLE_KB or shutil.disk_usage(OUT).free<MIN_FREE_BYTES:
            abort.set()


def run_wave(concurrency:int):
    if concurrency not in MAX_PROFILES:
        raise ValueError("Unsupported concurrent real-render profile")
    check_no_production_jobs()
    check_resource_budget()
    wave = OUT / ("actual-%d-clients" % concurrency)
    wave.mkdir(mode=0o700,parents=True,exist_ok=False)
    plan = wave / "plan.json"
    plan.write_text(json.dumps({
        "mode":"showcase", "heading_ids":["h0","h3"],
        "action_ids":[], "title":"Real Sauce sample demo"
    }))
    lock=threading.Lock()
    active:dict[int,subprocess.Popen]={}
    abort,stopped=threading.Event(),threading.Event()
    samples:list[dict]=[]
    clock=time.monotonic()
    observer=threading.Thread(target=monitor,args=(abort,stopped,samples),daemon=True)
    observer.start()
    try:
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            results=list(pool.map(
                lambda i:job(i,wave,plan,abort,active,lock),
                range(concurrency)))
    finally:
        stopped.set()
        observer.join(timeout=2)
        if abort.is_set():
            with lock:
                for proc in active.values():
                    if proc.poll() is None:
                        os.killpg(proc.pid, signal.SIGTERM)
    elapsed=round(time.monotonic()-clock,3)
    report={
        "concurrency":concurrency,
        "source":"Actual Sauce-controlled public page, no fabricated frames",
        "real_chromium_captures":sum("capture_s" in r for r in results),
        "successful_master_exports":sum(r["ok"] for r in results),
        "jobs":results, "wall_s":elapsed,
        "peak_vm_cpu_pct":max((r["cpu_pct"] for r in samples),default=None),
        "min_vm_available_ram_mb":min((r["available_ram_mb"] for r in samples),default=None),
        "wave_output_bytes":size_tree(wave),
        "total_encoded_video_seconds":round(sum(r.get("duration_s",0) for r in results),2),
        "sample_count":len(samples),
        "zero_ai_calls":True,
        "no_production_job_post":True,
    }
    (wave/"summary.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,sort_keys=True),flush=True)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profiles",default="1,2,4")
    args=parser.parse_args()
    profiles=[int(s.strip()) for s in args.profiles.split(",")]
    if len(profiles)>3 or len(profiles)!=len(set(profiles)) or any(x not in MAX_PROFILES for x in profiles):
        raise SystemExit("Profiles must be a unique subset of 1,2,4")
    if os.environ.get("GEMINI_API_KEY"):
        raise SystemExit("Disable paid inference explicitly for this stress harness")
    if not INSPECTION.is_file():
        raise SystemExit("Real product-explorer inspection is missing")
    report=json.loads(INSPECTION.read_text())
    if report.get("url")!=URL or not {"h0","h3"}.issubset({x["id"] for x in report["headings"]}):
        raise SystemExit("Inspection source/heading mismatch")
    OUT.mkdir(mode=0o700,parents=True,exist_ok=True)
    for concurrency in profiles:
        result=run_wave(concurrency)
        if result["successful_master_exports"]!=concurrency:
            raise SystemExit(1)


if __name__=="__main__":
    main()
