"""Playwright shared-video-helper regression; requires no browser or network."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from backend.live_capture import ensure_video_helper


class VideoRecorderCacheTests(unittest.TestCase):
    def test_discovers_preinstalled_helper_when_home_cache_empty(self):
        with TemporaryDirectory() as folder:
            root=Path(folder)
            helper=root/"ffmpeg-1013"/"ffmpeg-linux"
            helper.parent.mkdir()
            helper.write_bytes(b"preexisting-helper")
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(ensure_video_helper(root),str(root))
                self.assertEqual(os.environ["PLAYWRIGHT_BROWSERS_PATH"],str(root))

    def test_respects_existing_browser_cache(self):
        with TemporaryDirectory() as folder:
            with patch.dict(os.environ, {"PLAYWRIGHT_BROWSERS_PATH":"/explicit/cache"}, clear=True):
                self.assertEqual(ensure_video_helper(Path(folder)),"/explicit/cache")
                self.assertEqual(os.environ["PLAYWRIGHT_BROWSERS_PATH"],"/explicit/cache")

    def test_does_not_invent_cache_without_helper(self):
        with TemporaryDirectory() as folder:
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(ensure_video_helper(Path(folder)),"")
                self.assertNotIn("PLAYWRIGHT_BROWSERS_PATH",os.environ)


if __name__=="__main__":
    unittest.main()
