"""Value indicators must be evidence-backed, not fabricated revenue."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

FILE=Path(__file__).resolve().parents[1]/"ops"/"sauce_value_report.py"
spec=importlib.util.spec_from_file_location("sauce_value_report", FILE)
reports=importlib.util.module_from_spec(spec)
spec.loader.exec_module(reports)


class ValueReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.root=Path(self.tmp.name)/"jobs"
        self.root.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def job(self,ident:str,status:str,*,release:dict|None=None,feedback=None):
        folder=self.root/ident
        folder.mkdir()
        row={"id":ident,"status":status,"created_at":9000.0}
        if feedback is not None: row["feedback"]=feedback
        (folder/"status.json").write_text(json.dumps(row))
        if release is not None:
            out=folder/"export"
            out.mkdir()
            (out/"release.json").write_text(json.dumps(release))
            (out/"preview.mp4").write_bytes(b"\x00"*1200)

    def test_only_verified_continuous_film_counts_as_delivered(self):
        self.job("a"*24,"needs_review",release={
            "continuous_motion":True,"source_verified":True,
            "render_mode":"continuous-browser-capture","duration_seconds":7.5},
            feedback={"rating":5,"notes":"Nice"})
        self.job("b"*24,"needs_review",release={
            "render_mode":"sha-verified-source-states","duration_seconds":11})
        self.job("c"*24,"failed")
        report=reports.calculate(self.root,clock=10000)
        self.assertEqual(report["all_time"]["accepted"],3)
        self.assertEqual(report["all_time"]["ready_for_review"],2)
        self.assertEqual(report["all_time"]["verified_continuous_outputs"],1)
        self.assertEqual(report["all_time"]["failed"],1)
        self.assertEqual(report["review_count"],1)
        self.assertEqual(report["positive_review_count"],1)
        self.assertEqual(report["average_review_rating"],5)
        self.assertEqual(report["verified_continuous_seconds"],7.5)
        self.assertEqual(report["last_24h"]["verified_continuous_outputs"],1)
        self.assertIsNone(report["revenue"])
        self.assertFalse(report["payments_integrated"])
        raw=json.dumps(report)
        self.assertNotIn("Nice",raw)
        self.assertNotIn("a"*24,raw)

    def test_invalid_or_unverified_previews_not_counted(self):
        self.job("d"*24,"needs_review",release={
            "continuous_motion":True,"source_verified":False,
            "render_mode":"continuous-browser-capture"})
        self.job("e"*24,"needs_access")
        report=reports.calculate(self.root,clock=10000)
        self.assertEqual(report["all_time"]["ready_for_review"],1)
        self.assertNotIn("verified_continuous_outputs",report["all_time"])
        self.assertEqual(report["all_time"]["unsupported_access"],1)
        self.assertEqual(report["review_count"],0)

    def test_expired_and_inflight_visible_in_distinct_counts(self):
        self.job("f"*24,"queued")
        self.job("0"*24,"failed")
        report=reports.calculate(self.root,clock=10000+90000)
        self.assertEqual(report["all_time"]["queued_or_running"],1)
        self.assertEqual(report["last_24h"],{})

    def test_report_atomic_and_private(self):
        path=Path(self.tmp.name)/"private"/"value-report.json"
        reports.write_report({"verified_continuous_outputs":1},path)
        self.assertEqual(json.loads(path.read_text())["verified_continuous_outputs"],1)
        self.assertEqual(path.stat().st_mode & 0o777,0o600)


if __name__=="__main__": unittest.main()
