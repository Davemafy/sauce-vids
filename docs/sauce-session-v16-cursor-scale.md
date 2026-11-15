# Sauce v16 — cursor scale correction

**Live A/B comparison:** https://devmcp.davemafy.xyz/sauce-engine-v16/

**Corrected 1080p/60fps master:** https://devmcp.davemafy.xyz/sauce-engine-v16/master-1080p60.mp4?v=16

**Previous oversized cursor:** https://devmcp.davemafy.xyz/sauce-engine-v15/

The cursor in v15 occupied too much space relative to the web application's
controls and text. The vector silhouette did not need to be enlarged or
replaced again. Its **presentation scale** needed to be reduced.

## Implementation

In `scripts/reference_cursor_v15.py`, the actual overlay applies
`film_scale=0.56` **before** the existing `press_scale(age)`:

```python
scale=film_scale*press_scale(age)
```

This changes the cursor's visible dimensions, not the recorded mouse
coordinates or the SVG path. Both the bitmap and hotspot undergo the **same
scale**, so the point that triggers the click stays anchored.

| Style | v15 visible dimensions | v16 visible dimensions |
|---|---:|---:|
| Rounded black | 58 × 70 px | approximately **32 × 39 px** |
| White outline | 62 × 64 px | approximately **35 × 36 px** |

A new optional `--cursor-scale` switch allows future sizing without
redrawing the asset. The default is `0.56`. Values must remain between
0.35 and 1.0. The 0.88 press contraction, fixed cursor-tip hotspot, spring
trajectory, click ripple and blurred shadow remain intact. Earlier
v12–v14 presentation modes ignore the v15-specific scale parameter.

## Actual verification

- Replayed the unchanged, verified Brimble session at
  **1920 × 1080, 60fps, 252 frames**.
- Reused the recorded source events and original 2× Chromium screenshots.
- **Three semantic and three target pixel-region checks passed.**
- Original modal animation and event-driven camera remain unchanged.
- 1280 × 720, 30fps preview encoded with Lanczos downscaling.
- Reviewed side-by-side video frames at ~0.75s and ~2.17s:
  the previous 58×70 pointer was visibly too prominent;
  the new 32×39 pointer is proportionate.
- Desktop 1280×720 and mobile 390×844 player testing passed,
  including v15/v16 switching, video playback and no horizontal overflow.
- **119 local unit tests pass** including the new cursor-size regression.

The original v15 master is preserved for comparison. This is still a short
engine proof rather than a complete launch film.

## Reproduce

```bash
../.sauce-render-env/bin/python scripts/session_replay.py \
  --session studio/.tmp/brimble-reference-v16-ink \
  --workflow tests/fixtures/brimble-cinematic-workflow.json \
  --output studio/.tmp/brimble-reference-v16-ink/sauce-v16-black-1080p60.mp4 \
  --fps 60 --seconds 4.2 --har --backdrop-focus \
  --presentation-v15 --cursor-style ink --cursor-scale 0.56 \
  --presentation-hide-selector 'img[src*="bee-cutout"]'
```

Raw session files, HAR and generated videos remain on the Vultr worker.
