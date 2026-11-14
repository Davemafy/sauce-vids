# Sauce event-driven renderer

One tested production primitive: a real recording + an original timestamped interaction receipt can produce a 1080p product clip with conservative camera moves. Camera keys must never be invented.

## Run

Create the renderer virtual environment once if the VM doesn't have dependencies:

```bash
python3 -m venv .sauce-render-env
.sauce-render-env/bin/pip install numpy opencv-python-headless pillow cairosvg
```

Then:

```bash
.sauce-render-env/bin/python scripts/render_event_video.py \
  --video /path/to/real-browser-capture.mp4 \
  --manifest /path/to/original-interactions.json \
  --music /path/to/licensed-track.mp3 \
  --output /path/to/sauce-demo.mp4
```

Pass `--preview 6.2 --output /path/to/preview.jpg` to inspect a frame before full rendering. `--seconds 4` makes a bounded render smoke test. The legacy `scripts/render_linear_autozoom.py` remains a compatible entry point.

## Input and trust rules

The capture JSON records the actual page URL (`source` or `site`), source duration, pixel rectangle, and time-stamped DOM events on **the same capture clock**. A meaningful camera shot requires a real `click` with `semanticGoal`, a subsequent verified `state_change` with `resultRect`, and optional `interaction_complete` to end the reading hold.

```json
{
  "source": "https://your-approved-product.example",
  "source_kind": "Real browser recording",
  "duration": 14,
  "capture_rect": {"width": 1320, "height": 720},
  "events": [
    {"t": 3.7, "kind": "click", "label": "Reviews", "semanticGoal": "open reviews"},
    {"t": 4.04, "kind": "state_change", "evidence": "review panel visible",
      "resultRect": {"x": 560, "y": 97, "width": 750, "height": 616}},
    {"t": 10.65, "kind": "interaction_complete", "label": "reviews inspected"}
  ]
}
```

Do not produce this JSON by guessing clicks from video timestamps. When a source has no trusted state-change rectangles, the renderer produces a **locked wide shot**, not a fake zoom. An incompatible source resolution and manifest rectangle is rejected. Output comes with FFprobe metadata and an FFmpeg full-decode check. Sound is omitted unless a licensed track is explicitly passed for a custom project.

## Current verification and boundaries

- Linear: real official *interactive marketing preview*, not an authenticated account; event sidecar recorded with an X11 cursor. This is the positive end-to-end demonstration.
- Kiva: real public demo recording with time-stamped events but without verified state-change rectangles. The generalized renderer produces a static composition; the source is deliberately **not** a visual-quality acceptance sample.
- 1080p output is landscape. The engine is not yet an autonomous creative director, and it does not yet synthesize a strong script, create human-approved highlights, or semantically verify narration.
- Shotcandy browser frame is MIT licensed, with a retained attribution. Do not fabricate a product UI, manually invent a product action or silently upscale illegible UI to claim visual quality.
