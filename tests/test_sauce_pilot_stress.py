"""Stress harness safety and numerical reporting tests; no network calls."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import unittest

FILE=Path(__file__).resolve().parents[1]/"ops"/"stress_sauce_pilot.py"
spec=importlib.util.spec_from_file_location("sauce_stress",FILE)
stress=importlib.util.module_from_spec(spec)
spec.loader.exec_module(stress)


class BoundedStressTests(unittest.TestCase):
    def test_defaults_are_pure_reads_and_bounded(self):
        tasks=stress.make_tasks(100,120,24)
        self.assertEqual(len(tasks),244)
        self.assertEqual({kind for kind,_ in tasks},{"health","status","media"})
        self.assertEqual(tasks,stress.make_tasks(100,120,24))

    def test_invalid_counts_are_rejected(self):
        for counts in ((0,0,0),(600,2,0),(-1,2,3),(1.0,2,3)):
            with self.subTest(counts=counts),self.assertRaises(ValueError):
                stress.make_tasks(*counts)

    def test_unsafe_concurrency_rejected_before_network(self):
        for n in (0,33,100):
            with self.subTest(n=n),self.assertRaises(ValueError):
                stress.run_profile(n,1,1,1)

    def test_summary_counts_failed_connections(self):
        samples=[
            {"kind":"status","ok":True,"elapsed_ms":4.2,"error":None},
            {"kind":"status","ok":False,"elapsed_ms":6.2,"error":"BlockingIOError"},
            {"kind":"media","ok":True,"elapsed_ms":12.1,"error":None},
            {"kind":"health","ok":True,"elapsed_ms":2.3,"error":None},
        ]
        report=stress.summarize(samples,12)
        self.assertEqual(report["requests"],4)
        self.assertEqual(report["errors"],1)
        self.assertEqual(report["endpoints"]["status"]["errors"],1)
        self.assertEqual(report["endpoints"]["status"]["error_types"]["BlockingIOError"],1)
        self.assertEqual(report["endpoints"]["status"]["p50_ms"],5.2)


if __name__=="__main__":unittest.main()
