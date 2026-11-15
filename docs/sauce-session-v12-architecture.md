# Sauce v12 — Persistent cursor and cinematic presentation compositor

**Live 16:9 comparison:** https://devmcp.davemafy.xyz/sauce-engine-v12/

**1080p / 60fps master:** https://devmcp.davemafy.xyz/sauce-engine-v12/master-1080p60.mp4?v=12

**Previous v11 for A/B:** https://devmcp.davemafy.xyz/sauce-engine-v11/

**Existing longer Film 05:** https://devmcp.davemafy.xyz/sauce-film-05/

November 15, 2026. These changes apply to the real offscreen *landscape*
renderer. No portrait/Shorts changes. v12 is a short proof of the new motion
and presentation treatment; it is not a final launch film.

## Root cause: visually missing clicks

The real Brimble website reports `cursor: none` over much of the hero and
dialog. In v11, the compositor treated that as an instruction to **omit the
presentation cursor**, leaving clicks apparently uncaused.

The black insect-like artifact crossing the Connect button was not
a defective Sauce cursor. It was Brimble's animated bee asset
(`img[src*="bee-cutout"]`). It intermittently obscured the clickable
text and made the capture appear to have a chaotic scribbled pointer.
This was confirmed by comparing the original 2× screenshot states.
Source screenshots, interaction logs and HAR are **preserved unmodified**.

The new renderer adds explicit film-mode cursor rules:

- `pointer` / `grab` → actual native Linux hand cursor.
- `text` / `vertical-text` → actual X11 I-beam.
- `none` → hand if over a **recorded clickable rectangle**, otherwise arrow.
- Cursor hotspot remains anchored at the real position even when the
  cursor image scales during a press.
- Cursor rendered from the first available telemetry position through
  the entire film; it does not disappear over the dialog.
- Only verified `pointerdown` events trigger press feedback and rings.
  Press reaches 0.89× over 65ms; release returns smoothly through
  ~220ms. The anti-aliased ring grows from 8px to ~31px in ~310ms,
  under the cursor and without a giant spotlight.

This is a **presentation overlay**, not a claim that CSS cursor:none
was not part of the original website.

## New reusable modules

`scripts/presentation_contract.py` contains dependency-free pointer,
press and modal spring timing policies. It is tested in GitHub CI.

`scripts/cinematic_presentation_v12.py` contains the precomputed stage
and per-frame film composition:

- 1920×1080 canvas, 1600×900 clipped browser window at (160, 50).
- Three background light fields using broad 120px Gaussian blur,
  restricted behind the browser window and deliberately desaturated.
- Three-tier window shadows approximating (x=0):
  - y=50px / blur=98px / spread=-20px / opacity .30
  - y=25px / blur=48px / spread=-12px / opacity .48
  - y=7px / blur=19px / spread=-2px / opacity .18
- 1–2px outline and inner light edge, 21px corner radius.
- Real Linux X11 arrow, hand and I-beam glyphs remain independently
  composited at their original image-handle hotspots.

`scripts/session_replay.py` supports `--presentation-v12` and an
independent optional `--presentation-hide-selector`. The latter can
hide an identified **decorative** element *only in the filmed replay*,
without changing capture evidence or the application's action workflow.

For this Brimble film only:
`--presentation-hide-selector 'img[src*="bee-cutout"]'`.

Suppression is explicit and validated: the selector must exist, and a
resolved CSS visibility check must confirm that it was hidden. The default
renderer does not remove anything from other websites.

## Actual native modal plus editorial spring

The modal still comes from the real Brimble DOM. The existing virtual
clock drives original finite Web Animations and CSS animations.

v12 adds a **small independent CSS scale** of 0.95 → 1.0 using the
critical-damping response `1 - 0.05(1+23t)e^(-23t)`.
This affects only the visible real modal during its entrance, not an
invented clone of the UI. It is essentially settled after ~300ms.
Once the modal is stable, the element's scale is set to 1.

The existing event-driven spring camera remains: no zoom before
intentional pointer motion, focus goes from Connect to the modal after
it is observed, and maximum camera zoom stays **1.398×**.

## Resolution and export

- Source capture: Chromium 1280×720 CSS, **deviceScaleFactor=2**
  (2560×1440 source pixels per screenshot).
- Master canvas: 1920×1080, 60fps, 252 frames.
- Camera raster resampling: OpenCV `INTER_LANCZOS4` rather than linear
  for the v12 mode.
- Master: H.264 yuv420p, FFmpeg `libx264 -preset medium -crf 14`,
  `+faststart`. Actual size ~1.6 MB, 4.2 seconds.
- Preview: 1280×720, 30fps, FFmpeg `scale=1280:720:flags=lanczos`,
  `libx264 -preset slow -crf 16`.
- Website player: layered soft shadows and a *separate*, highly restrained
  ambient background glow. All the main shadows and glows are already
  encoded in the video, not just added by CSS outside it.

Supersampling is useful here because the image source is larger than the
final window, even at the maximum zoom. It doesn't make nonexistent
source details recoverable on an arbitrary lower-resolution recording.

## Verification

`scripts/verify_cinematic_v12.py` verifies the actual MP4 and manifest:

- Six original captured Chromium states with verified SHA256 hashes.
- 56 recorded browser events, two physical click events.
- Both recorded clicks retain their native cursor overlays;
  click location differences were **0.014px** and **0.009px**.
- Three semantic state checks and three focused image-region comparisons
  passed; the tested ROI mean error was 0.0 in this same-browser run.
- Original web animations advanced for 576 frame-effects.
- Full MP4 decode succeeded, 1920×1080 at 60fps, exactly 252 frames.
- All 23 sampled adjacent frames in the active camera push changed.
- Modal stays in frame and maximum zoom is capped below 1.4×.
- Real bee art is suppressed *only* in this separate presentation export.
- **100 local unit tests passed**, including eight added presentation rules.
- Desktop and 390×844 mobile player tested: video loads and plays,
  comparison to v11 works, no horizontal overflow or page errors.

The pixel-region checks intentionally cover specific target UI rectangles,
**not** all pixels in the full frame. They are not a universal guarantee
for arbitrary websites or GPU/browser configurations.

## Reproduce on the Vultr worker

Requires Playwright, Pillow, OpenCV, NumPy, FFmpeg, Xvfb and the local
session files. The session archive may contain sensitive network data:
do not upload HAR, raw screenshots or unreviewed captures to public GitHub.

```bash
../.sauce-render-env/bin/python scripts/session_replay.py \
  --session studio/.tmp/brimble-cinematic-v11-release \
  --workflow tests/fixtures/brimble-cinematic-workflow.json \
  --output studio/.tmp/brimble-cinematic-v11-release/sauce-v12-1080p60.mp4 \
  --fps 60 --seconds 4.2 --har --backdrop-focus \
  --presentation-v12 \
  --presentation-hide-selector 'img[src*="bee-cutout"]'

../.sauce-render-env/bin/python scripts/verify_cinematic_v12.py
python3 -m unittest discover -s tests -q
```

## Remaining work

This verifies a real, short product interaction. The renderer still needs
a generalized shot planner, narrated long-form film timeline, authenticated
state restoration and QA across more websites before Sauce can claim
professional equivalence to Screen Studio or a release-grade autonomous
video editor. The 13-second landscape flagship was deliberately not
overwritten during this visual experiment.
