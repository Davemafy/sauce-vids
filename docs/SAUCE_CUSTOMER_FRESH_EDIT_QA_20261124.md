# Sauce — fresh customer URL-only editorial and QA hardening (2026-11-24)

## Goal and invariant

The founder explicitly requires testing Sauce **as a customer does**: enter one public URL, allow Sauce to discover, verify, capture, direct and render, then criticise the real encoded film and improve. **No reused source recording, hand-picked action/JSON or fabricated product pixels in the customer run.** Only current GitHub `main` and the existing persistent Vultr DevMCP worker. This experiment was run on an isolated clone/API without redeploying the older production service.

## Observed customer defects

- Existing production `sauce-url2video.service` at `/opt/sauce-vids` remains on the older November 17 path and previously failed a fresh Dub URL on Gemini HTTP 503. The latest `main` fixes do not magically update that service.
- A fresh `POST /v1/jobs {"url":"https://www.heroui.com/docs/components/slider"}` to latest-main isolated API yielded `needs_product_demo_url`, though HeroUI has four discoverable real sliders. The ordinary slider's output numeral was too small to satisfy the existing *premium product-film* payoff area admission. This is **not** a completed customer film. The same fresh live browser confirmed genuine drag and visible dependent numeric change, which is captured by generalized slider detection, but the default strict gate must not falsely approve the tiny output.
- A previously completed **fresh customer-only Mantine** film proved a real source modal and yielded 5.77s source-true MP4, but lacked soundtrack, had a static 2s introduction and 0.684 repeated/static sample fraction. Visible popup was small on a documentation site.

## Applied editorial improvements — verified through two NEW customer submissions

The latest-main isolated customer API was invoked twice with **only** `{"url":"https://mantine.dev/core/modal/"}` and independent job IDs. Sauce autonomously probed actual page controls in disposable browsers, declined auth-bound and undersized outcomes, selected the real `Open modal` control `a25`, then performed and recorded the real click. The source proof for both fresh jobs independently measured: result area **0.06797** of probe viewport, changed result fraction **0.31849**, source pixel change above baseline **0.95372**, viewport shift **0**; recorded real click+state-change events, no private data or generated UI.

**First new fresh film, job `7f64844016e9b811411c5ddd`:** Shortened only the original contiguous Chromium source's pre-click idle hold from 1.05s to 0.55s before the independently proven click (based on genuine source timestamps). No altered event timing or inserted frames. Actual MP4 SHA256 `0d4c8f3d7d141a0a486e817e23992fec79333402fbe0fcd00d307d6524cddd18`, 1920×1080 H264 60fps, ~5.15s, actual Chromium source 25fps. Encoded QA: **REJECT** `ABRUPT_CUT_CANDIDATE` (later shown to be a *false positive from a real source popup*), `REPEATED_OR_STATIC_FRAMES` **0.667**, `NO_AUDIO_STREAM`. `STATIC_OPENING_2S` no longer triggered.

**Second completely fresh URL-only film, job `370e6067525d11b9df57356f`:** Generalized compact-result shot planner to visually substantial verified dialogs occupying **2%–16%** of recorded source frame; eased whole source camera detail from 1.62× to **2.1×** (source-true no fake UI) and extended settle/release to **1.05s / 1.02s**. A 0.55s real click lead-in was preserved. Genuine modal click, accepted independent outcome and real Chromium action footage were all re-recorded for this job; no source recording reused from the first job. Master `../.sauce-stagehand-private/customer-fresh-mantine-optical-v2-20261124/jobs/370e6067525d11b9df57356f/export/master-1080p60.mp4`, SHA256 **`3ca716b0b0098e6fd093820f0ef1ce4e531e4bd64ed909a073f995d95a3ff16e`**, 314 frames / **5.233333 seconds** H264 **1920×1080/60**, fresh original Chromium capture **25/1 fps** with DPR2 CSS viewport 1920×1080; full FFmpeg strict decode passed. Actual encoded contact sheet visually inspected. Camera metrics max continuous per-frame source translation **26.8255px** (below 45px bound); one verified camera shot, no clipping of modal in selected sample frames.

**QA of second fresh film:** `encoded_quality_verdict=REJECT`; `REPEATED_OR_STATIC_FRAMES` fraction **0.569** and `NO_AUDIO_STREAM`. **No** `STATIC_OPENING_2S` and no unproven abrupt cut. The original result was still very small in the overview, and document chrome competes with it. This was an editorial/source-gate experiment, **not a sellable or creatively approved film**.

## Source-aligned QA correction (not suppressing real errors)

A popup can legitimately change many original Chromium pixels in one source frame. `scripts/quality_preview_supervisor.py` originally assumed source and output began at the same timestamp and recognized only a native `events[]` manifest. The customer pipeline uses `editorial_events[]` with separate independently grounded `click` and `state_change` items, plus a verified source trim. That mismatch created a spurious `ABRUPT_CUT_CANDIDATE`.

Added a bounded `source_trim_seconds` path from `backend/live_render.py` to the independent QA analyzer, exact source-frame sampling with trim, and verification of paired real browser click + visible result within 1.8s. The source MP4/WebM and manifest SHA256 are still checked; only abrupt changes that match **the original decoded, hash-verified source pixels at the same actual source timestamp** can be classified `verifiedRealUiTransition`. For the first fresh film, the previously false abrupt at film t=0.7s matched original Chromium t=4.27s, source mean frame delta 127.823 versus encoded 84.744. **Neither missing evidence nor an invented source cut can be cleared by this rule.** QA still rejected repeated/static frames and silence.

Added `tests/test_customer_action_first_motion.py` (3 tests) and `tests/phase2/test_customer_trim_source_alignment.py` (2 tests) verifying precise source trimming, source-proven dialog closeups, matching real UI transition suppression, missing-action fail-closed behavior, and unchanged no-audio rejection.

Full pre-publication local tests: **544 Phase 2 passed, 10 skipped, 21 subtests passed**; **362 legacy unittest run, 2 skipped, 0 failures**; `git diff --check` clean. Original customer films, source receipts and audit trails preserved.

## Critical remaining blockers

1. Generic public Chromium recorder is **25fps**, and 60fps H264 is resampled; source-native60 is **not achieved**. No test-green claim can change that.
2. More than half the 10fps visual QA samples are still static/repeated. One small documentation modal is simply too weak a product story.
3. No audio. No licensed music source or product-grounded narration was available for this generic modal; do not invent voiceover or generic synthetic clicks.
4. Customer path still defaults to a Shotcandy framed browser on a neutral background; connecting the current owner-approved cobalt-cloud **large clear floating browser** stage to actual autonomous customer jobs remains to be done.
5. The live November 17 customer service has **not been redeployed**. No premium owner-approved films and no public launch clearance.

**Recommendation:** next focus should be native60 browser capture, real result selection/film-story quality and genuine licensed audio, then a fully automated new public URL run under deployment controls. Preserve strict product-demo vs website-preview distinction; a verified UI action is a technical candidate, never itself creative approval.
