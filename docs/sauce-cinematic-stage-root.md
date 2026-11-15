# Sauce v18 — root cinematic stage

**Live:** https://devmcp.davemafy.xyz/sauce-engine-v18/

**1080p master:** https://devmcp.davemafy.xyz/sauce-engine-v18/master-1080p60.mp4

**Prior film:** https://devmcp.davemafy.xyz/sauce-engine-v17/

## Architecture

Sauce's verified renderer is **Python + Playwright + OpenCV + FFmpeg**.
It is not a React composition. Adding a JSX `CinematicStage` in the
web player would **not** change the actual MP4. Instead,
`scripts/cinematic_stage.py` defines the compositing root
`CinematicStage` and its final overlay child `CinematicCursor`.
`scripts/session_replay.py` uses them to create every output frame in
the default v15/production mode:

```text
Recorded user workflow + verified JSON events
  → Spring2D cursor path + camera track (60fps fixed clock)
  → Chromium actual DOM at DPR 2 (2560×1440 source pixels)
  → Lanczos4 projection to 1480×832 frame content
  → CinematicStage.render(website_frame, CinematicCursor)
      → #090a0f canvas + 140px ambient light
      → window backing + 24px backdrop blur
      → wide soft shadows + highlight + 16px rounded clip
      → actual website pixels
      → topmost SVG cursor + pointerdown ripple
  → FFmpeg H.264 1920×1080 60fps master
  → FFmpeg Lanczos 1280×720 30fps preview
  → single HTML player + export receipt
```

`CinematicStage.render` rejects incorrectly sized website frames.
It is mandatory in production: `produce_cinematic_demo.py` raises an
error if the replay report does not confirm the root or its geometry.

The original source screenshots and HAR are **not** modified or
published. The older v12–v14 presentations and explicitly requested raw
replay remain separate debugging/comparison paths.

## Stage contract

- Master: 1920 × 1080, BGR frame for the encoder.
- Centered window: x=220, y=124, width=1480, height=832.
- Canvas: `#090a0f`.
- Ambient: three restrained colored blooms, Gaussian blur **140px**,
  drawn behind the window, never over source UI pixels.
- Window backing: `rgba(18,18,24,0.90)`, with precomposited
  Gaussian backdrop blur radius **24px**.
- Corners: **16px** rounded clipping mask.
- Border and highlight: white at 12% and 8% opacity.
- Shadow tiers, computed once under the stage:
  - `0 40px 80px -20px rgba(0,0,0,0.7)`
  - `0 80px 160px -40px rgba(0,0,0,0.5)`

The CSS equivalents are mirrored in
`docs/sauce-premium-player-template.html`, where
`<div class="CinematicStage">` wraps the **entire page**. The CSS
does not replace the film-level compositor.

## Cursor contract

The final video contains **one** cursor. The browser CSS hides OS and
DOM default cursor glyphs, and no X11 assets are loaded in this mode.

`CinematicCursor` uses the original reference-traced SVG asset,
a `#111113` black fill, 2.2px white outline and an alpha drop shadow
(0,12,24,0.35), rasterized at 4×. It retains the user's approved
**0.56 scale**, roughly 32×39px instead of the earlier oversized 58×70.

The source mouse positions are passed through the existing
`Spring2D`-based `cursor_track` at a fixed 60fps. The true click
coordinates remain anchored to the captured `pointerdown` events.
At mousedown the pointer reaches **0.88×** scale and shows a short
fading vector ring. The cursor is composited last, above the UI.

## Actual verification

- Live export: 1920×1080 at 60fps, exactly 252 frames.
- Source capture: DPR 2; 6 source-state SHA256 checks.
- 3 semantic action checks and 3 focused pixel-region matches passed.
- H.264 master and Lanczos-downscaled 1280×720/30fps preview decoded.
- Pixel QA verified the dark outer canvas (white-margin regression),
  the different colors of the glows, the white website content inside
  the window, the window dimensions and cursor pixels above the site.
- Source website pixels remained unchanged by the compositor.
- Player has a real root `CinematicStage` element, no horizontal overflow,
  and plays on desktop (1280×720) and mobile (390×844).
- **133 local unit tests pass**, including five new root-composition
  regression checks. A separate export-level verification script,
  `scripts/verify_cinematic_stage.py`, inspects the actual MP4 and
  synthetic cursor layering.

## Run

```bash
../.sauce-render-env/bin/python scripts/produce_cinematic_demo.py \
 --session studio/.tmp/brimble-reference-v16-ink \
 --workflow tests/fixtures/brimble-cinematic-workflow.json \
 --out studio/.tmp/sauce-cinematic-stage-v18 \
 --seconds 4.2 --title "Connect your agent" \
 --cursor-style ink --cursor-scale .56 \
 --presentation-hide-selector 'img[src*="bee-cutout"]'

python3 -m unittest discover -s tests -q
../.sauce-render-env/bin/python scripts/verify_cinematic_stage.py
```

Limitations: the present verified proof pipeline supports a 1280×720 CSS
capture, 10-second maximum replay, and network/application states that
can be restored through Playwright and optionally HAR. This is a short
rendering-quality proof, not a finished long-form launch advertisement.
