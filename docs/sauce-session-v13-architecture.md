# Sauce v13 — vector cursor and dark film compositor

**Live comparison:** https://devmcp.davemafy.xyz/sauce-engine-v13/

**1920×1080 / 60fps master:** https://devmcp.davemafy.xyz/sauce-engine-v13/master-1080p60.mp4?v=13

**Previous v12:** https://devmcp.davemafy.xyz/sauce-engine-v12/

**Longer flagship preserved:** https://devmcp.davemafy.xyz/sauce-film-05/

Date: November 15, 2026. The target is the working landscape offscreen
rendering pipeline. This film is a 4.2-second proof of rendering and cursor
quality, **not** the complete Sauce launch film.

## Root cause and fix

The previous v12 compositor used the host's X11 `hand2` cursor glyph.
That produced a dated hand icon that looked nothing like a premium screen
recording cursor. Its appearance wasn't a spring physics problem. It was
the wrong graphic asset.

In v13, **no X11 cursor is loaded or composed**. Chromium runs the real
website, but CSS native cursor visuals are forcibly hidden using a
presentation-only style sheet. The cursor is drawn as a separate vector
compositing layer above the finished browser crop.

The SVG pointer:
- lives in `assets/cursors/sauce-pointer.svg`;
- uses a clean white arrow with fine graphite outline;
- is rendered by CairoSVG at **4×** and Lanczos-downsampled once before
  per-frame composition;
- uses the actual SVG tip offset as its cursor hotspot;
- never switches to the system's hand cursor; it remains a precise
  arrow over both clickable elements;
- uses the existing deterministic `Spring2D` cursor trajectory, derived
  from the time-stamped Playwright pointer positions;
- stays visible while the real site reports `cursor: none`.

The animated click feedback:
- lives as editable SVG source in `assets/cursors/sauce-click-ripple.svg`;
- is rasterized from **22 different SVG frames** with smoothly increasing
  radius and fading stroke opacity;
- starts on the *recorded* `pointerdown`, not a guessed timestamp;
- lies **behind** the pointer and never covers text or DOM content;
- shrinks the SVG arrow to **85%** at press peak and releases with a
  critically damped settle.

The original captured interaction events and page pixels are not
modified by the editorial cursor layer.

## Cinematic stage / video output

`scripts/cinematic_presentation_v13.py` produces a real dark,
studio-like **1920×1080 background inside every encoded film frame**:

- Graphite gradient from approximately RGB (15,17,26) at the top to
  RGB (24,27,39) lower on the stage.
- Three broad ambient highlights (cool indigo, plum, subdued cobalt)
  with a **120px Gaussian blur**, placed behind the browser.
- Wide-diffusion window shadow tiers:
  `0 25px 50px -12px rgba(0,0,0,.5)` and
  `0 50px 100px -20px rgba(0,0,0,.3)`,
  plus a short contact shadow.
- Fine inner highlight rim, real rounded-rectangle browser clip at
  1600×900, and a wide cinematic margin.
- No synthetic macOS toolbar, re-created webpage, or fake modal.
- The original Brimble modal animation and Sauce's small critically
  damped emphasis remain in place.

`docs/sauce-session-v13-player.html` adopts the same dark language
without pretending a CSS-only glow counts as a successful film edit.
Its controls compare v13 with the old v12 directly.

## Supersampling, rendering and quality

- Actual browser viewport is 1280×720 CSS pixels at **deviceScaleFactor=2**,
  producing real 2560×1440 Chromium source frames.
- For film mode `--presentation-v13`, DPR below 2 is **rejected**.
- Camera and cursor trajectories use `Spring2D`; there is no
  frame-to-frame linear camera cut.
- Browser source camera projection uses Lanczos4.
- Master: 1920×1080, 60fps, H.264, `libx264` medium preset, CRF 14.
- Preview: 1280×720, 30fps,
  `scale=1280:720:flags=lanczos`, H.264 slow preset, CRF 16.
- All 252 master frames and 126 preview frames decoded successfully.

## Preserved real application behavior

For the public Brimble interaction only, the opt-in selector
`img[src*="bee-cutout"]` hides a *decorative bee mascot* that otherwise
flies over the Connect click. The suppression is presentation-only.
The six captured original screenshots and HAR remain unchanged and
are kept off public GitHub.

The same three verified app-state assertions and three focused source-pixel
comparisons still pass. Exact pixel-region MAE was 0.0 with the replay's
same browser/resources. This does **not** assert that every full screen
pixel on any website will reproduce identically.

## Regression gates and reproduction

`tests/test_vector_cursor_assets.py` checks the editable SVG source,
the ripple source and deterministic Spring2D path. The repository's
**104 tests pass**.

`scripts/verify_cinematic_v13.py` inspects the actual exported MP4,
session manifest, SVG assets, camera and click coordinates, real encoded
stage brightness, codec, frame count and successful FFmpeg decode.

To reproduce on the existing worker (with the private authorized source
session already present), install the Python packages listed in
`scripts/requirements-render.txt` and ensure Chromium and FFmpeg are
available. The production worker uses `../.sauce-render-env` and the
already configured Chromium executable:

```bash
../.sauce-render-env/bin/python scripts/session_replay.py \
  --session studio/.tmp/brimble-cinematic-v11-release \
  --workflow tests/fixtures/brimble-cinematic-workflow.json \
  --output studio/.tmp/brimble-cinematic-v11-release/sauce-v13-1080p60.mp4 \
  --fps 60 --seconds 4.2 --har --backdrop-focus \
  --presentation-v13 \
  --presentation-hide-selector 'img[src*="bee-cutout"]'

../.sauce-render-env/bin/python scripts/verify_cinematic_v13.py
python3 -m unittest discover -s tests -q
```

The raw HAR, source screenshots, and video assets are not committed:
those remain on the Vultr worker. HAR data must be reviewed before
sharing because it can contain cookies, request payloads or tokens.

## Scope still open

This is a much more cohesive cursor and presentation treatment, but a
4.2-second engineering proof does not establish that Sauce can already
produce market-leading, narrated long-form product films automatically.
Shot direction, narration timing, editorial pacing, authenticated product
sessions, and cross-site compatibility remain separate acceptance goals.

The v13 video-first player also limits its 16:9 frame height to the viewport
so users at 1280×720 can see the full video without an initial scroll.
