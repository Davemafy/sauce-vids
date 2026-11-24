# Floating glass browser over cloud background — 2026-11-24

**Owner correction:** The previous `cloud_glass_v1` stage filled the glass object with clouds against a white exterior. The requested layout is the opposite: the **clouds form the entire environment**, and a translucent, softly refractive **floating browser window** sits above them. The latest user-supplied/generated mockup is the composition and material reference, not a fake page asset.

## Implemented

- `scripts/cloud_window_sky_stage.py` provides approved **`cloud_window_sky_v1`**: a full-frame cloud backdrop with a small amount of daylight softening, a separate organically rounded transparent acrylic window with the lower-right sculpted recess, physical elevation/contact shadow, broad top white softbox reflections, layered Fresnel/meniscus highlights, and a separate crisp original-source browser aperture. It introduces no fake browser widgets, cursor, UI text or clickable controls.
- Sky imagery comes only from the existing owner-approved `cloud_shadow_v2_1536x864.jpg`, reused as the new **background**, never the window fill. This is a brightened/de-screened adaptation, **not** a new 1:1 photographic cloud asset.
- `scripts/cloud_shadow_stage.py` now routes the new material through the already-verified perspective projection, original DPR2 source screen and aperture mask. In immersive camera movement, the **sky remains stationary**; only the signed glass-and-shadow foreground delta, browser plane and real source event/cursor move. The source UI remains completely opaque, original-coloured, and is composited last.
- `scripts/spatial_studio_stage.py` permits the new preset and its independently verified source geometry. The previously verified `classic`, `cloud_shadow_v1` and `cloud_glass_v1` presets stay supported and unchanged.
- `scripts/source_event_director.py` now selects `cloud_window_sky_v1` for **new** native source-directed films. Existing saved plans retain their explicit preset. `scripts/plan_stagehand_phase2.py` chooses matching aperture geometry for its original-source 60fps shell coverage gate. `scripts/studio_plan_bounded_repair.py` retains an explicitly selected new preset when enforcing approved cloud stages; legacy fallback is unchanged.
- `tests/phase2/test_cloud_window_sky_stage.py`: 5 new regressions for background-vs-window placement, source-pixel integrity, sky stability, landscape geometry, nonoverlapping sculpted recess, and preservation of older stage defaults.

## Real encoded proof

Previously verified Brimble 6.5s native DPR2 2880×1800 /60fps source video, original source event manifest and real cursor track preserved. Fresh new director film plan at private path `../.sauce-stagehand-private/sky-window-study-20261124/new-director-plan.json`, independently validated with original source timing, camera motion limit **37.0847px/frame** (allowed ≤45), real result visibility 1.0, context release 1.0, original source proof.

Real encoded film `../.sauce-stagehand-private/sky-window-study-20261124/brimble-cloud-background-glass-window-1080p60.mp4` SHA256 **`4f1c966b5936366e28935e60c3028d0ec6a2de27c169002e905a7879cf1938ad`**, 6.500s, 390 source-lineage frames, H.264 1920×1080/60fps, 48kHz AAC, 3,944,833 bytes. **Strict FFmpeg complete decode PASS.** Inspected actual encoded 10-frame contact sheet and first/result/release source frames. Existing encoded supervisor says **`HUMAN_REVIEW_REQUIRED`**, **zero automatic findings**; **not owner premium approval**.

The same private signed HTTPS review link provided in the conversation (not committed to public Git) returns 206 for a valid Range request, 403 without signature; actual Chromium decoded and sought to t=3.5s on desktop **1280×720** and mobile **390×844**, source dimensions 1920×1080, **zero media/JS errors**.

Full test results on pre-publish worktree: **522 Phase 2 passed, 10 skipped, 21 subtests passed**; **302 unittest run, 2 skipped, zero failures**; `git diff --check` passed.

## Remaining quality gaps

The user's generated reference uses highly photographic fluffy clouds and a brighter almost colorless glass. The shipped render uses the existing cobalt-halftone approved cloud asset, so **the sky is not photographic 1:1**. A clean, properly licensed high-resolution cloud background would materially improve reference likeness without altering real product UI. Also, in a very deep source-closeup the floating shell may move partly outside the frame as the real interface becomes dominant; this is an editorial tradeoff, not a data corruption. The verified Brimble action only reveals setup choices, not a premium business payoff.

**No new VM/branch, no credential import, no fake UI, no overwrite of earlier films. No running Studio deployment. Zero owner-approved premium Sauce films.**
