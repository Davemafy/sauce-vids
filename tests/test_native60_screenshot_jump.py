"""Native60 screenshots must not mutate Chromium while FFmpeg is recording."""
import tempfile
import time
import unittest
from pathlib import Path

import numpy as np

from backend.live_capture import capture_public_evidence_mark
from scripts.quality_preview_supervisor import transient_frame_reversion_finding


class _Page:
    url="https://example.com/demo"
    def __init__(self):
        self.screenshots=0
        self.calls=0
    def screenshot(self,**kwargs):
        self.screenshots+=1
        Path(kwargs["path"]).write_bytes(b"test")
    def evaluate(self,expr):
        self.calls+=1
        if expr!='Math.round(window.scrollY)':
            raise AssertionError("Unexpected DOM data")
        return 19


class Native60ScreenshotSafetyTests(unittest.TestCase):
    def test_native_mark_has_dom_receipt_but_no_playwright_screenshot(self):
        page=_Page()
        with tempfile.TemporaryDirectory() as d:
            evidence=[]
            capture_public_evidence_mark(page,Path(d),evidence,
                                         "source-result",time.monotonic(),native60=True)
            self.assertEqual(page.screenshots,0)
            self.assertEqual(page.calls,1)
            self.assertEqual(evidence[0]["scroll"],19)
            self.assertEqual(evidence[0]["evidence_medium"],
                             "continuous-native60-source")
            self.assertEqual(list(Path(d).iterdir()),[])

    def test_legacy_mark_preserves_original_screenshot(self):
        page=_Page()
        with tempfile.TemporaryDirectory() as d:
            evidence=[]
            capture_public_evidence_mark(page,Path(d),evidence,
                                         "opening",time.monotonic(),native60=False)
            self.assertEqual(page.screenshots,1)
            self.assertEqual([f.name for f in Path(d).iterdir()],["mark-0.jpg"])

    def test_transient_scale_reversion_rejected_not_stable_ui_change(self):
        base=np.full((90,160),205,np.uint8)
        base[10:70,15:145]=40
        base[28:45,45:100]=241
        jump=np.roll(base,25,axis=1)
        frames=np.stack([base.copy() for _ in range(180)])
        frames[95:99]=jump
        issue=transient_frame_reversion_finding(frames,fps=60)
        self.assertEqual(issue["code"],"TRANSIENT_FRAME_REVERSION")
        self.assertEqual(issue["detail"]["onset_frame"],95)
        self.assertEqual(issue["detail"]["restored_frame"],99)
        stable=np.stack([base.copy() for _ in range(180)])
        stable[95:]=jump
        self.assertIsNone(transient_frame_reversion_finding(stable,fps=60))


if __name__=="__main__":
    unittest.main()
