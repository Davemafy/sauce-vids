# Sauce v15 — reference-shaped cinematic pointer

**Live film and comparison:** https://devmcp.davemafy.xyz/sauce-engine-v15/

**Black SVG cursor master:** https://devmcp.davemafy.xyz/sauce-engine-v15/master-ink-1080p60.mp4?v=15

**White SVG cursor master:** https://devmcp.davemafy.xyz/sauce-engine-v15/master-outline-1080p60.mp4?v=15

**Previous Tabler attempt:** https://devmcp.davemafy.xyz/sauce-engine-v14/

## Design correction

The earlier v14 cursor used a generic Tabler pointer, giving it the wrong
silhouette and wrong wing angle compared with the user's attached images.
v15 uses **two independently drawn SVG paths based on the actual provided
reference images**. It does not rotate the old icon or use an embedded PNG.

- `assets/cursors/reference-v15/black-rounded.svg`: long upright left
  edge, broad horizontal right wing, rounded corners, fill `#111113`,
  white `stroke-width="2.2"`.
- `assets/cursors/reference-v15/white-outline.svg`: the independently
  traced, wide, diagonal white pointer with bold graphite outline.

Source images are not committed to GitHub. The SVG silhouettes are standalone
editable vector files, with independent top-left tip hotspots.

## The film compositor

`scripts/reference_cursor_v15.py`:

- Rasterizes the SVG source at **4×** and uses one Lanczos downsample.
- Composites a shadow with **0px x, 12px y, 24px Gaussian blur and 0.35
  black opacity** outside the actual browser screenshot.
- Keeps the *hotspot* at the source SVG tip, including through press scaling;
  the large shadow padding does not shift the click coordinates.
- Uses the exact existing recorded browser pointer path and critically
  damped `Spring2D` trace.
- Presses to **0.88×** at 75ms after the recorded `pointerdown`, then
  settles back without arbitrary wobble or a fake click timestamp.
- Renders the existing subtle, 22-frame SVG ripple behind the cursor.
- Suppresses the page/native cursor in presentation mode, so the video
  contains exactly one designed cursor, including under CSS `cursor:none`.

`scripts/session_replay.py` now defaults to `--presentation-v15` for
normal CLI runs. Use `--cursor-style ink` (default) or `outline`.
Previous v12–v14 presets remain explicitly selectable; `--raw-replay`
preserves the old unstyled capture for debugging.

The existing 16:9 stage remains: a genuine dark gradient, broad
120px-blurred light fields behind the main window, layered shadows
equivalent to
`0 0 0 1px rgba(255,255,255,.08),
0 25px 50px -12px rgba(0,0,0,.5),
0 50px 100px -20px rgba(0,0,0,.3)`,
and a subtle inner highlight around the rounded browser frame.

The source page is still rendered at DPR **2×** in Chromium,
then composited with Lanczos4 resampling. The final H.264 master uses
`libx264 -preset medium -crf 14`, 1920×1080 at 60fps; the
1280×720 at 30fps browser preview uses FFmpeg
`scale=1280:720:flags=lanczos`.

## Concrete checks

`scripts/verify_reference_v15.py` examines *both actual MP4 files* and
their original verified capture manifests:

- Both masters: 252 frames, 60fps, 1920×1080, complete decode passed.
- Both previews: 1280×720, 30fps, full decode passed.
- Six original source state hashes validated per version.
- Three semantic checks and three focused pixel-region checks per version.
- Two click events from the recording; pointer/click alignment errors:
  **0.014px and 0.0095 CSS px**.
- Actual cursor pixels differ between the black and white renders at
  both click frames (regional MAE **22.26** and **22.35**).
- DPR 2, Lanczos4 source warping, app cursor suppressed, real modal
  transition preserved, background focus and cinematic shadows active.
- Desktop 1280×720 and mobile 390×844 browser-player acceptance:
  all three video modes loaded, playback worked, no horizontal overflow,
  no JavaScript errors.
- **118 local unit tests** passed, including v15 SVG geometry/hotspot,
  shadow parameters and default-mode contracts.

These checks establish reproducible rendering and correct click semantics.
They do not by themselves establish parity with a professional film editor
across long, narrated or authenticated sessions.

## Run on the Vultr worker

```bash
../.sauce-render-env/bin/python scripts/session_replay.py \
 --session studio/.tmp/brimble-reference-v15-ink \
 --workflow tests/fixtures/brimble-cinematic-workflow.json \
 --output studio/.tmp/brimble-reference-v15-ink/sauce-v15-black-1080p60.mp4 \
 --fps 60 --seconds 4.2 --har --backdrop-focus \
 --cursor-style ink \
 --presentation-hide-selector 'img[src*="bee-cutout"]'

../.sauce-render-env/bin/python scripts/verify_reference_v15.py
python3 -m unittest discover -s tests -q
```

Raw HAR, screenshots and recorded videos remain private on the worker;
only source, SVGs, unit tests, player template and documentation are
committed to main. The previous film and older tests remain available.
