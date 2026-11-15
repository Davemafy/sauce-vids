# Sauce v14 — online-sourced custom cursor replacement

**Live two-style comparison:** https://devmcp.davemafy.xyz/sauce-engine-v14/

**Default black pointer, 1080p/60fps:**
https://devmcp.davemafy.xyz/sauce-engine-v14/master-ink-1080p60.mp4?v=14

**White outline pointer, 1080p/60fps:**
https://devmcp.davemafy.xyz/sauce-engine-v14/master-outline-1080p60.mp4?v=14

**Previous v13 vector cursor:** https://devmcp.davemafy.xyz/sauce-engine-v13/

The requested visual references were two mouse pointers:
a filled black arrow with a high-contrast white edge, and a white-bodied
arrow with a heavy black outline. The earlier bespoke Sauce pointer and the
earlier X11 hand cursor did not match the supplied shapes.

## Licensed online sources (verbatim originals)

Both source files are copied from the official [Tabler Icons repository]
(https://github.com/tabler/tabler-icons), licensed **MIT**.
The original `LICENSE` file is preserved at
`assets/cursors/tabler/LICENSE`, with copyright Paweł Kuna.

| Source used | Original URL | Local file |
| --- | --- | --- |
| Pointer filled | https://raw.githubusercontent.com/tabler/tabler-icons/main/icons/filled/pointer.svg | `assets/cursors/tabler/pointer-filled.svg` |
| Pointer outline | https://raw.githubusercontent.com/tabler/tabler-icons/main/icons/outline/pointer.svg | `assets/cursors/tabler/pointer-outline.svg` |

SHA256 of the downloaded, unchanged sources:
- Filled: `80615e4b6980aa33a000c6dc22a976221e9fd3a1c1d9d5ba3be7f15d5ea224fa`
- Outline: `811735d187eaf6c8a7b7f06053140b8284cf4b1b2ea7ba1c8f340f1fbafbac24`

The `tests/test_tabler_cursor_assets.py` suite verifies both hashes, the
MIT grant, SVG paths and the existence of the v14 route.

## What changed in the real renderer

`scripts/online_cursor_assets.py` loads the original **Tabler** vector
geometry at render time, recoloring the actual upstream paths:

- `--cursor-style ink`: near-black filled arrow, white edge,
  **default** and closest to the first reference;
- `--cursor-style outline`: white arrow with thick graphite stroke,
  closest to the second reference;
- both render at 46×52 final-video pixels, from 4×-supersampled CairoSVG
  and a single Lanczos downscale;
- hotspots are located from the SVG tips, at (5.82, 9.27) and
  (7.48, 8.46), respectively;
- the cursor image stays visible even when the website has CSS
  `cursor: none`. No OS cursor is used in this mode;
- real `pointerdown` times still trigger the existing 85% press
  contraction and SVG ripple, and the same Spring2D path follows the
  actual sampled pointer trajectory;
- the real Brimble DOM, its modal transition and the camera remain
  unchanged from the v13 replay.

`scripts/session_replay.py` now accepts
`--presentation-v14 --cursor-style ink|outline`. This is a **separate
rendering mode**. Earlier modes are preserved.

The Brimble bee image is hidden **only** in the comparison replay using
the existing explicit `--presentation-hide-selector` option. Original
source screenshots and hashes are untouched.

## Actual video validation

Both variations are H.264 **1920×1080, 60fps, 252 frames**, generated
from real 2560×1440 Chromium screenshots, using fixed camera time and
Lanczos4 source resampling. Both have complete-decoding 1280×720/30fps
preview exports.

`scripts/verify_tabler_v14.py` checks the actual MP4 files:

- six captured source state hashes validated for both;
- both recorded clicks remain aligned to within **0.014** and
  **0.0095 CSS pixels**;
- all three semantic and three UI-region checks pass **for both styles**;
- the displayed cursor regions differ at both click frames:
  mean absolute pixel differences of **13.90** and **12.70**;
- original camera and click timing are the same in both outputs;
- complete FFmpeg decoding passes for both masters and previews;
- mobile (390×844) and desktop (1280×720) player QA passes:
  default film, switching to outline and v13, playback and no overflow;
- **111 local unit tests** pass.

No audio was added, and no unrelated Shorts or landscape flagship
footage was modified.

## Reproduce on the configured worker

```bash
../.sauce-render-env/bin/python scripts/session_replay.py \
  --session studio/.tmp/brimble-tabler-v14 \
  --workflow tests/fixtures/brimble-cinematic-workflow.json \
  --output studio/.tmp/brimble-tabler-v14/sauce-v14-ink-1080p60.mp4 \
  --fps 60 --seconds 4.2 --har --backdrop-focus \
  --presentation-v14 --cursor-style ink \
  --presentation-hide-selector 'img[src*="bee-cutout"]'

../.sauce-render-env/bin/python scripts/verify_tabler_v14.py
python3 -m unittest discover -s tests -q
```

Private screenshots, HAR session archives, and video files stay on Vultr;
only source, tests, MIT asset files and documentation are committed.

This changes the cursor's **real rendered artwork**. It does not claim
that a 4.2-second engine proof is a finished product-launch film.
