# Sauce — full-window cloud-glass correction (2026-11-24)

## Owner's visual correction

The owner showed actual Brimble film playback and rejected the previous `cloud_window_sky_v1` composition: the video had a small grey browser inside an oversized, nonrectangular glass body with an arbitrary lower-right extension. The owner's stated requirement was to **keep the existing cloud background** while letting the **large genuine browser itself be the floating glass window**; no extra object around the application.

## Code on main, scoped

- `scripts/cloud_window_sky_stage.py`: the same approved sky background `cloud_shadow_v2_1536x864.jpg`, the same source projection/camera, and the same existing `cloud_window_sky_v1` selectable preset. Replaced the separate Bézier art-body with a single conventional rounded-rectangle `object_mask` following the true source window perimeter.
- Original recorded Chromium source now fills **1547×967 px** at 1920×1080 for 2880×1800 DPR2 capture. Bounds **(187,57)–(1734,1024)**; **72.2% of the total frame** is genuine browser pixels, versus the prior ~43%. Glass extends only **18 px** outside the page, with a quiet acrylic bevel, horizontal studio highlight and soft contact/elevation shadow.
- No lower-right sculpture/cutout, no second decorative glass body, no fake browser toolbar, no generated app UI, no cloud texture over the real source. The sky stays spatially fixed while the window/source move during the verified post-click camera dolly.
- `tests/phase2/test_cloud_window_sky_stage.py` locks the full-sized centered window, continuous symmetric rounded rectangle (without an asymmetric tail), browser-to-frame ratio, separate cloud background, source color purity and legacy preset compatibility.
- Existing old `cloud_shadow_v1` and `cloud_glass_v1` are retained; no user-facing Studio redeploy.

## Actual encoded film verification

Reused independently verified real Brimble source capture 2880×1800 DPR2 native60, with source SHA256 `859392c3594a71069806fc1b51fbb8cb487b04d581d6e57de4d3f33a304d5453` and original event manifest unchanged. Generated new source-bound plan through current `scripts/plan_stagehand_phase2.py` / `source_event_director.py`, passed exact real action/camera/shell coverage checks, and re-encoded the actual master. Current private worker artifact: `../.sauce-stagehand-private/sky-window-rect-20261124/brimble-large-rounded-glass-1080p60.mp4`, SHA256 **`76cca4a33e531c61a3eadddca9ffb04f76cee5f2cf63ca51f835af1a3a2e31b4`**, 6.500s, 390 frames H264 1920×1080/60fps, AAC stereo48kHz. **Full FFmpeg decode passed.** Contact sheet reviewed across entire film; full-resolution Brimble wide frame t0.3s, dialog-focused t3.5s, and release t5.9s checked. Product text appears larger in the wide shot; closeup still fills frame for result readability. Visual composition now has only the cloud stage behind the round rectangular browser.

Encoded QA **`HUMAN_REVIEW_REQUIRED` with zero automatic findings**: technical admission only, not owner creative approval. Protected signed review link was tested (HTTP206 authenticated byte-range, unsigned HTTP403), and actual Chromium playback/seek was verified at desktop1280×720 and phone390×844, zero JS/media errors.

Regression on latest then-current main `2562505048f01dd4781a6132826135adabe74a6b`: **523 Phase2 passed, 10 skipped, 21 subtests; 309 legacy unittest run, 2 skipped, no failures**, `git diff --check` passed. Preserve concurrent Gemini/curious-director work on that main; only the two source/test files changed.

## Remaining quality truth

The sky still uses the owner's existing cobalt-halftone cloud artwork (mildly diffused) rather than the brighter photorealistic clouds in the generated mockup. That is an asset issue rather than placement. The Brimble public click still proves only the setup dialog, not the compelling product outcome, and during the deliberate detail zoom part of the page leaves the frame. **Zero owner-approved premium Sauce films.** Do not describe this film as fully matched, premium approved, launched or deployed.
