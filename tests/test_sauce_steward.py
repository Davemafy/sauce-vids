"""Offline safety and persistence tests for the Sauce Steward daemon."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import sqlite3
import tempfile
import unittest

FILE = Path(__file__).resolve().parents[1] / "ops" / "sauce_steward.py"
spec = importlib.util.spec_from_file_location("sauce_steward", FILE)
steward = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(steward)


class StewardPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_state = steward.STATE
        self.old_db = steward.DB_FILE
        self.old_status = steward.STATUS_FILE
        steward.STATE = Path(self.tmp.name)
        steward.DB_FILE = steward.STATE / "jobs.sqlite3"
        steward.STATUS_FILE = steward.STATE / "status.json"
        self.db = steward.connect()

    def tearDown(self):
        self.db.close()
        steward.STATE = self.old_state
        steward.DB_FILE = self.old_db
        steward.STATUS_FILE = self.old_status
        self.tmp.cleanup()

    def test_allowlisted_tasks_only(self):
        for kind in ("sync-main", "smoke-web", "audit-proof", "test-main"):
            self.assertIn(kind, steward.KINDS)
        with self.assertRaises(ValueError):
            steward.enqueue(self.db, "run-arbitrary-shell", dedupe=False)

    def test_enqueue_is_idempotent_for_pending_jobs(self):
        first = steward.enqueue(self.db, "smoke-web")
        second = steward.enqueue(self.db, "smoke-web")
        self.assertEqual(first, second)
        third = steward.enqueue(self.db, "smoke-web", dedupe=False)
        self.assertNotEqual(first, third)

    def test_recover_interrupted_job_once(self):
        job_id = steward.enqueue(self.db, "sync-main")
        self.db.execute("UPDATE jobs SET status='running',attempts=1 WHERE id=?",
                        (job_id,))
        self.db.commit()
        steward.recover(self.db)
        state = self.db.execute("SELECT status,attempts FROM jobs WHERE id=?",
                                (job_id,)).fetchone()
        self.assertEqual(dict(state), {"status": "queued", "attempts": 1})

    def test_terminal_failure_when_retry_limit_exhausted(self):
        job_id = steward.enqueue(self.db, "sync-main")
        self.db.execute("UPDATE jobs SET status='running',attempts=2 WHERE id=?",
                        (job_id,))
        self.db.commit()
        steward.recover(self.db)
        state = self.db.execute("SELECT status,error FROM jobs WHERE id=?",
                                (job_id,)).fetchone()
        self.assertEqual(state["status"], "failed")
        self.assertIn("Interrupted too many times", state["error"])

    def test_failed_job_records_error_not_false_success(self):
        job_id = steward.enqueue(self.db, "smoke-web")
        original = steward.OPERATIONS["smoke-web"]

        def error():
            raise RuntimeError("test site unreachable")

        steward.OPERATIONS["smoke-web"] = error
        try:
            self.assertTrue(steward.run_next(self.db))
        finally:
            steward.OPERATIONS["smoke-web"] = original
        state = self.db.execute("SELECT status,error FROM jobs WHERE id=?",
                                (job_id,)).fetchone()
        self.assertEqual(state["status"], "failed")
        self.assertIn("test site unreachable", state["error"])

    def test_status_updates_preserve_prior_receipts(self):
        steward.save_status({"main_sha": "a" * 40})
        steward.save_status({"web_smoke": {"passed": True}})
        status = __import__("json").loads(steward.STATUS_FILE.read_text())
        self.assertEqual(status["main_sha"], "a" * 40)
        self.assertTrue(status["web_smoke"]["passed"])

    def test_empty_queue_is_safe(self):
        self.assertFalse(steward.run_next(self.db))


if __name__ == "__main__":
    unittest.main()
