"""Encoded Sauce Basic QA tests; synthetic pixels are test fixtures, not demos."""
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from basic_tour_media_qa import analyse_master


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "FFmpeg/FFprobe unavailable")
class BasicMediaQATests(unittest.TestCase):
    def test_rejects_wrong_geometry_clock_and_missing_chapters(self):
        with TemporaryDirectory() as t:
            root=Path(t)
            bad=root/"bad.mp4"
            subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
                "-f","lavfi","-i","color=c=white:s=320x180:r=24",
                "-t","1","-c:v","libx264","-pix_fmt","yuv420p",str(bad)],
                check=True,timeout=30)
            result=analyse_master(bad,root,chapters=2,source_rates=["24/1"],sample_count=4)
            self.assertEqual(result["status"],"technical_reject")
            self.assertIn("master_codec_resolution_or_clock_wrong",result["issues"])
            self.assertIn("wrong_chapter_count",result["issues"])

    def test_real_1080p60_with_chapter_metadata_passes_technical_gates(self):
        with TemporaryDirectory() as t:
            root=Path(t);raw=root/"raw.mp4";meta=root/"chapters.ffmeta"
            final=root/"out.mp4"
            subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
                "-f","lavfi","-i","testsrc2=size=1920x1080:rate=60",
                "-t","1.5","-c:v","libx264","-preset","ultrafast",
                "-pix_fmt","yuv420p",str(raw)],
                check=True,timeout=40)
            meta.write_text(";FFMETADATA1\n[CHAPTER]\nTIMEBASE=1/1000\n"
                "START=0\nEND=1500\ntitle=Verified fixture\n")
            subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
                "-i",str(raw),"-f","ffmetadata","-i",str(meta),
                "-map","0:v:0","-map_metadata","1","-c:v","copy",str(final)],
                check=True,timeout=40)
            result=analyse_master(final,root/"qa",chapters=1,
                                  source_rates=["25/1"],sample_count=4)
            self.assertEqual(result["status"],"technical_pass_creative_pending")
            self.assertEqual(result["chapters"],1)
            self.assertIn("source_not_native_60fps",result["warnings"])

if __name__=="__main__":
    unittest.main()
