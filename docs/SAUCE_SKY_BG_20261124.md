# Sauce — clean cobalt halftone sky background (2026-11-24)

## Owner decision

After previewing the user's blue-cloud/ProductStudio concept, the owner clarified **"yeah for the bg"**: use the vivid cobalt-and-white halftone cloud sky as the **background only**. No fake browser, fictional ProductStudio UI, duplicate cursor, or generated product content should enter Sauce. The actual screen stays an independently recorded Chromium source.

## Implemented on current `main`

- Asset: `assets/stages/sauce_sky_halftone_1536x864.webp` — 1536×864 optimised WebP, clean full-bleed sky, reconstructed from the same visual direction as the reference, **no fake browser/UI**. File SHA256 `359bf6d37f2820b303606c2c6e4e897f6445fdd740ab46a449f1195376b55096`. It is a clean generated companion plate, not an exact extraction of pixels hidden under the concept's mock browser.
- `scripts/cloud_window_sky_stage.py` loads exactly this plate, validates its dimensions, and resizes it in BGR with a cache. The earlier artificial Gaussian blur and pastel blue tint are removed; the new asset's bright cobalt, clouds and halftone dots survive. A missing asset fails closed rather than silently falling back to the older background.
- The existing `cloud_window_sky_v1` geometry remains a single large rounded source-true floating browser (~72% viewport coverage at 1920×1080). Sky behind it is spatially stationary during cinematic camera movement; only browser glass and real source move. Every real UI/source pixel is composited last without cloud tint, blur, invented buttons or text.
- `scripts/cloud_shadow_stage.py` extends the passive overview compositor with explicit `stage_preset="cloud_window_sky_v1"`, preserving original `cloud_shadow_v1` behaviour for existing callers.
- `backend/native_subject_showcase.py` uses the new preset for *future* native continuous Paldey-style showcases, without reverting recent concurrent main's single-continuous-recording/no-cut camera change. New full-frame asset never substitutes original source product artwork.
- `tests/phase2/test_cloud_window_sky_stage.py` verifies asset hash, exact image pixels at native dimensions, separate sky / foreground geometry, real source pixel preservation, and passive showcase composition.

## Real rendered proof, no fresh inference

Existing authorized public Paldey three-segment native DPR2/60fps source from `../.sauce-stagehand-private/paldey-subject-native-v2-20261124` was reused unchanged with its verified model-selected shots. No additional Gemini request or fake UI was introduced. The sky-only update was rendered from the true recordings in the prior end-to-end `backend.native_subject_showcase.render` implementation before reconciliation with concurrent continuity work. Real film: `../.sauce-stagehand-private/paldey-generated-sky-20261124/master-1080p60.mp4`; SHA256 `565cd55d535222e2d8dea744c316714772eb828c1dc17720d32386373fe3f2b5`, **9.6s/576 frames 1920×1080 H264 60fps**, strict FFmpeg full decode passed. Contact sheet physically inspected (hero, actual page graphics, product cards) showing high-contrast vivid blue halftone cloud sky around real Paldey interface. No fake ProductStudio screenshot was used.

**Creative QA still REJECTS** this film for `STATIC_OPENING_2S`, `REPEATED_OR_STATIC_FRAMES`, `NO_AUDIO_STREAM`. This background improvement does not claim to cure camera pacing, motion/shot quality, or audio. No premium sign-off.

**Merge and tests:** Concurrent current main `a1a0961` added single-continuous-native Paldey capture and camera travel. Rebased background changes over it; preserved the continuous capture/render API and changed only its cloud stage argument. Full current merged worktree: **524 Phase 2 passed, 10 skipped, 21 subtests; 314 unittest run, 2 skipped; 0 failures**; `git diff --check` clean. No VM/branch changes, no production Studio deployment or video overwrite. Source footage and private generated review evidence were not committed.

## Remaining

The user-generated sky's cloud shapes and cobalt-white halftone match the stated direction, but this is a new clean plate and **not pixel-for-pixel extraction from the occluded concept screenshot**. The original approved `cloud_shadow_v2_1536x864.jpg` remains available for older stage presets. Future Paldey continuous films will use the new image but the 9.6s proof is from previous valid continuous-independent source segments, not a fresh full continuous re-recording. Keep owner creative approval separate from green code tests.
