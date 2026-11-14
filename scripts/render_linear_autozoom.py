#!/usr/bin/env python3
"""Backward-compatible Linear entry point. Production renderer: render_event_video.py."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name("render_event_video.py")),run_name="__main__")
