"""Disk restart safety for Sauce's background product-film jobs."""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from backend.job_store import recover_jobs, save_job, write_render_checkpoint


class ProductJobRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.job_id = "1234567890abcdef12345678"

    def tearDown(self):
        self.tmp.cleanup()

    def record(self, status="queued", stage="queued"):
        job = {"id": self.job_id, "url": "https://example.com/",
               "status": status, "stage": stage,
               "created_at": 100, "updated_at": 100}
        save_job(self.root, self.job_id, job)
        return job

    def test_unstarted_job_rejoins_queue(self):
        self.record()
        jobs, pending = recover_jobs(self.root)
        self.assertEqual(pending, [self.job_id])
        self.assertEqual(jobs[self.job_id]["stage"], "queued")

    def test_mid_capture_never_replays_paid_direction(self):
        for phase in ("inspecting", "directing", "capturing", "rendering"):
            with self.subTest(phase=phase):
                self.record(stage=phase)
                jobs, pending = recover_jobs(self.root)
                self.assertEqual(pending, [])
                self.assertEqual(jobs[self.job_id]["status"], "failed")
                self.assertEqual(jobs[self.job_id]["error"], "WorkerInterrupted")
                self.assertEqual(jobs[self.job_id]["last_stage"], phase)
                self.assertEqual(json.loads((self.root/self.job_id/"status.json").read_text())
                                 ["status"], "failed")

    def test_only_a_verified_checkpoint_with_budget_can_restart_rendering(self):
        job = self.record(stage="rendering")
        folder = self.root / self.job_id
        motion = folder / "private" / "motion"
        motion.mkdir(parents=True)
        source = b"captured browser bytes"
        raw = json.dumps({"continuous_recording": True, "sha256": sha256(source).hexdigest()}).encode()
        (motion / "continuous-source.webm").write_bytes(source)
        (motion / "continuous-capture.json").write_bytes(raw)
        checkpoint = {"url": job["url"], "receipt_sha256": sha256(raw).hexdigest(), "attempts": 1}
        write_render_checkpoint(folder, checkpoint)
        self.assertEqual(recover_jobs(self.root)[1], [self.job_id])
        write_render_checkpoint(folder, {**checkpoint, "attempts": 2})
        self.assertFalse(recover_jobs(self.root)[1])
        self.record(stage="rendering")
        write_render_checkpoint(folder, checkpoint)
        (motion / "continuous-source.webm").write_bytes(b"changed")
        self.assertFalse(recover_jobs(self.root)[1])

    def test_completed_video_retained_unchanged(self):
        original = self.record(status="needs_review", stage="needs_review")
        jobs, pending = recover_jobs(self.root)
        self.assertEqual(pending, [])
        self.assertEqual(jobs[self.job_id], original)

    def test_legacy_queued_result_requires_real_receipt(self):
        self.record(stage="needs_review")
        jobs, pending = recover_jobs(self.root)
        self.assertEqual(jobs[self.job_id]["status"], "failed")
        self.assertFalse(pending)
        self.record(stage="needs_review")
        export = self.root/self.job_id/"export"
        export.mkdir()
        (export/"preview.mp4").write_bytes(b"x" * 2048)
        (export/"release.json").write_text(json.dumps({
            "continuous_motion": True, "source_verified": True}))
        jobs, pending = recover_jobs(self.root)
        self.assertEqual(jobs[self.job_id]["status"], "needs_review")
        self.assertFalse(pending)

    def test_legacy_verified_video_restores_source_true_label(self):
        self.record(status="needs_review", stage="needs_review")
        export = self.root/self.job_id/"export"
        export.mkdir()
        (export/"preview.mp4").write_bytes(b"x" * 2048)
        (export/"release.json").write_text(json.dumps({
            "continuous_motion": True, "source_verified": True,
            "render_mode": "continuous-browser-capture",
            "film_mode": "interactive"}))
        jobs, _ = recover_jobs(self.root)
        self.assertEqual(jobs[self.job_id]["render_mode"], "continuous-browser-capture")
        self.assertEqual(jobs[self.job_id]["capture_mode"], "interactive")

    def test_failed_job_is_not_automatically_retried(self):
        self.record(status="failed", stage="failed")
        _, pending = recover_jobs(self.root)
        self.assertEqual(pending, [])

    def test_status_save_is_atomic_and_private(self):
        self.record()
        file = self.root/self.job_id/"status.json"
        self.assertEqual(file.stat().st_mode & 0o777, 0o600)
        self.assertEqual(len(list(file.parent.glob(".status-*.tmp"))), 0)
        self.record(stage="rendering")
        self.assertEqual(json.loads(file.read_text())["stage"], "rendering")

    def test_invalid_folders_and_partial_records_are_ignored(self):
        (self.root/"not-a-job").mkdir()
        (self.root/"not-a-job"/"status.json").write_text("{}")
        self.record()
        (self.root/self.job_id/"status.json").write_text('{"status":')
        jobs, pending = recover_jobs(self.root)
        self.assertEqual(jobs, {})
        self.assertFalse(pending)

    def test_incorrect_job_identity_ignored(self):
        self.record()
        file = self.root/self.job_id/"status.json"
        payload=json.loads(file.read_text())
        payload["id"]="abcdefabcdefabcdefabcdef"
        file.write_text(json.dumps(payload))
        jobs, pending = recover_jobs(self.root)
        self.assertFalse(jobs)
        self.assertFalse(pending)

    def test_bad_job_id_rejected(self):
        with self.assertRaises(ValueError):
            save_job(self.root, "../escape", {})
        with self.assertRaises(ValueError):
            save_job(self.root, "zz"*12, {})


if __name__ == "__main__":
    unittest.main()
