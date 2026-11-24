"""Regression: source integrity after native Chromium/Xvfb shutdown."""
import tempfile,unittest
from pathlib import Path
import cv2
import numpy as np

from backend.native60_capture import verify_live_terminal_frames
from scripts.quality_preview_supervisor import (
    terminal_frames,terminal_blackout_finding,probe)


def source_video(path:Path,*,end_black:bool):
    encoder=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'mp4v'),
                            60.0,(192,108))
    if not encoder.isOpened():
        raise RuntimeError('Test ffmpeg encoder unavailable')
    try:
        for i in range(24):
            # Live browser-like page with actual variation/contrast.
            img=np.full((108,192,3),215,np.uint8)
            cv2.rectangle(img,(8,10),(55,94),(36,55,80),-1)
            cv2.putText(img,'UI %d'%i,(66,50),cv2.FONT_HERSHEY_SIMPLEX,
                        .6,(12,15,30),2,cv2.LINE_AA)
            if end_black and i==23:img[:]=0
            encoder.write(img)
    finally:
        encoder.release()


class Native60TerminalIntegrityTests(unittest.TestCase):
    def test_reject_chromium_disappearing_on_final_source_frame(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'source.mp4'
            source_video(f,end_black=True)
            with self.assertRaisesRegex(RuntimeError,'black terminal frame'):
                verify_live_terminal_frames(f,24)

    def test_preserve_real_final_browser_page_and_genuine_frames(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'source.mp4'
            source_video(f,end_black=False)
            receipt=verify_live_terminal_frames(f,24)
            self.assertEqual(receipt['terminal_original_frames_checked'],8)
            self.assertTrue(receipt['terminal_source_integrity_verified'])

    def test_encoded_qa_detects_one_black_frame_missed_by_ten_fps(self):
        with tempfile.TemporaryDirectory() as d:
            bad=Path(d)/'bad.mp4'
            good=Path(d)/'good.mp4'
            source_video(bad,end_black=True)
            source_video(good,end_black=False)
            for video,expect_bad in ((bad,True),(good,False)):
                stream=next(s for s in probe(video)["streams"]
                            if s["codec_type"]=="video")
                last=terminal_frames(video,stream)
                defect=terminal_blackout_finding(last)
                self.assertEqual(defect is not None,expect_bad)
                if defect:
                    self.assertEqual(defect["code"],"TERMINAL_BROWSER_BLACKOUT")
                    self.assertEqual(defect["detail"]["affected_final_frames"],1)

    def test_short_or_missing_video_fails_closed(self):
        with self.assertRaises(RuntimeError):
            verify_live_terminal_frames(Path('/not-there.mp4'),4)
        with self.assertRaises(RuntimeError):
            verify_live_terminal_frames(Path('/not-there.mp4'),32)


if __name__=='__main__':
    unittest.main()
