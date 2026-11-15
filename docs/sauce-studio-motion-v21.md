# Sauce StudioMotion v21 — silent deterministic film proof

**Verified live film:** https://devmcp.davemafy.xyz/sauce-studio-v21/

**Repository:** `Davemafy/sauce-vids`

This release is **video only**. No audio files are read, analysed, generated or
muxed in the StudioMotion run. The encoded master and preview have a single
H.264 video stream and **zero audio streams**.

## Three modular systems

| TypeScript module | Runtime integration |
| --- | --- |
| `scripts/studio-motion/src/timeWarp.ts` | `studio_motion_bridge.py` plans monotonic output-frame → source-ms timestamps; `session_replay.py` advances Chromium, cursor and camera on that source clock |
| `scripts/studio-motion/src/StudioStage.ts` | Typed projection contract; actual perspective homography, floor reflection and two soft floor shadows rendered by `cinematic_stage.py` |
| `scripts/studio-motion/src/KineticCallouts.ts` | Evidence-backed labels, output-time cooldowns; actual filmed pills and anchors rendered by `studio_motion_callouts.py` |

Shared strict TypeScript contracts live in `types.ts`, with Node stdin/stdout
integration in `bridge.ts`. The main entrypoint is
`scripts/produce_cinematic_demo.py`.

Unlike a React template-only demonstration, the visual passes are baked into
the output MP4. The existing Sauce renderer is Python/OpenCV/Chromium rather
than React; TypeScript is used for deterministic planning and metadata
contracts, while Python performs per-frame raster composition.

## Guarantees and adjustments

- Protected high-intent events receive **400ms pre-roll and 300ms post-roll**.
  Playback remains 1x throughout these merged windows. Only the *first*
  focus event for each field is protected (repeated focus cannot prolong
  the 1x lock).
- Idle spans longer than 800ms and evidenced loading/static-scroll regions
  use cubic Hermite speed ramps up to the configurable `maxWarpSpeed=4`.
  The map remains strictly increasing.
- Directional blur is gated by both motion and accelerated playback; its
  shutter displacement now explicitly scales with `speed - 1`.
- The floor retains a subtle `floorReflectionIntensity=0.25` under the
  perspective window and uses directional contact and wide cast shadows.
  This is a raster approximation of a rough reflective studio floor,
  **not** a path-traced physically based material.
- Callouts require verifiable high-intent events, safe short labels and
  real target bounds. Default cooldown is **2500ms**, maximum lifetime
  is **1800ms**. Even if a shorter cooldown is configured, callouts will
  not overlap.
- Callout anchors follow the same perspective homography as the actual
  browser window, with a mass 0.8, stiffness 220, damping 20 spring
  applied at the actual output framerate.
- Replayed source capture is DPR 2; the silent master is
  1920×1080/60fps, the preview is 1280×720/30fps with Lanczos scaling.

## Configurable command (silent)

```bash
cd scripts/studio-motion
npm ci
npm test                 # strict TypeScript compilation and 9 Node tests
cd ../..

../.sauce-render-env/bin/python scripts/produce_cinematic_demo.py \
  --session studio/.tmp/brimble-reference-v16-ink \
  --workflow tests/fixtures/brimble-cinematic-workflow.json \
  --out studio/.tmp/sauce-studio-motion-v21-verified \
  --seconds 4.2 \
  --enable-time-warp --max-warp-speed 4 \
  --enable-studio-floor --floor-reflection-intensity 0.25 \
  --enable-callouts --callout-cooldown-ms 2500 \
  --deterministic-frame-cache studio/.tmp/sauce-studio-motion-v20-source-cache \
  --no-webgl-optics \
  --presentation-hide-selector 'img[src*="bee-cutout"]'
```

To verify a repeat under a different output directory but the **same
private canonical source cache**:

```bash
../.sauce-render-env/bin/python scripts/verify_studio_motion_export.py \
  studio/.tmp/sauce-studio-motion-v21-verified \
  studio/.tmp/sauce-studio-motion-v21-repeat
```

Only the compiled planner runs on Node. The private cache is guarded by
source-event/state hashes and is **never published** with the finished film.

## Observed sample result

- Actual Brimble trace: 56 recorded events, 6 independently hashed capture
  states, 2 interaction windows.
- 4200ms source → **3004.92326ms mapped output**, encoded as **181 frames**.
- Peak warp speed 4x; one qualifying idle dead zone in this sample.
- One high-intent callout, **Connect Agent**; no overlapping pills.
- Floor reflection intensity 0.25; window tilt remains restrained.
- Three semantic checks and three source pixel-region checks passed.
- Both separately rendered masters and previews contain **video only**.
- The two masters' file SHA-256 hashes match exactly, and **181/181
  decoded-frame hashes match** with the same canonical source cache.
- Strict TypeScript compilation reports zero errors; **9 Node tests pass**.
- Python suite and native rendering checks pass. See CI for portable
  checks and the local verifier for actual MP4 assertions.

Determinism applies to the **same inputs, environment and pinned source
frame cache**. It cannot be guaranteed across arbitrarily changing live
websites without capturing or pinning their raster inputs.

This is a short silent rendering proof, not a full-length film quality
comparison with a professional studio. The example does not contain a
long continuous scrolling interval; that classification is covered by
the synthetic TypeScript tests rather than the Brimble film.
