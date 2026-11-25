# Sauce — native60 Chromium viewport jump (2026-11-25)

## User-observed defect, verified from exact MP4

The founder reported the **same visible cut/glitch even after the previous final-frame blackout repair**. This report is based on independent decoded frame-by-frame inspection of the exact 4.718-second fixed-ending owner review film, not an inference from a QA "green" result.

- Original candidate: `../.sauce-stagehand-private/customer-native60-no-black-20261125/job-01/export/master-1080p60.mp4`; H264 1920×1080/60fps 283 frames, SHA256 **`1fb48da0b800eb9e9a8bc70de9c93f15c72fd3fbbb978044ed10d9876337c118`**. The previous exporter incorrectly claimed zero findings.
- **A second independent glitch** occurs at encoded frames **99–102** (~**1.650–1.700 s**); frame 103 (~1.7167s) snaps back. The browser content temporarily magnifies and shifts across the source aperture for four frames, although the cobalt stage stays stable. Gray-image before/altered delta ~**12.8/255**, restored frame ~**0.8/255** different from original due to ongoing camera motion.
- Independently inspected **original native60 Chromium source** from that same job: frames **249–252** (~**4.150–4.200 s**) show the temporary page geometry change, then frame **253** (~4.2167s) returns. The original source is **identical before and after** to within ~**0.2/255**, while the four anomalous frames differ by **16.3/255** at 192×108. Another identical four-frame jump occurred in the source at frames **48–51** (~0.800–0.850s), restoring at frame 52; the edited film had trimmed that first one out.
- The separate fast modal appearance at film ~**0.58–0.70s**, corresponding to genuine source frames ~185–193, fades the source overlay to gray and introduces modal content. It is an actual public website animation, **not** the capture geometry fault; it can still feel abrupt without clear pointer choreography.
- Native capture `backend/live_capture.py` invoked `page.screenshot(animations='disabled')` in `mark("opening")` and `mark("action-a25")` while FFmpeg x11grab was running. Four-frame Chrome viewport device-metric overrides coincided with those screenshot calls. This is strongly confirmed by running a **fresh true customer URL-only capture with only the in-recording screenshots disabled** and observing both jumps disappear. No prerecorded source, manually selected interaction, or invented UI was used for that validation.

## Implementation

1. `backend/live_capture.py`: `capture_public_evidence_mark` records bounded nonsecret DOM evidence (phase, time, canonical public URL, scroll), but **does not trigger Playwright screenshots while `Native60Recorder` is running**. The original 60fps source MP4 and separately measured DOM/pixel action proof remain in the receipt. Legacy Playwright mode still saves the original mark JPEGs. Every native evidence record states `evidence_medium=continuous-native60-source`; the code never silently fabricates missing screenshots.
2. `scripts/quality_preview_supervisor.py`: independent new original-frame-rate pixel inspection using FFmpeg (up to 4500 frames per candidate), in addition to existing sparse 10fps story-wide QA and final-8 terminal blackout QA. Detects short-lived **A→B→A** frame reversions of <150ms where a large full-frame change returns to the nearly identical prior page (code `TRANSIENT_FRAME_REVERSION`). The prior image only at 1.65s is no longer classified as clean merely because 10fps samples missed it. It is a reject finding, not an automatic pixel-removal or smoothing operation.
3. `tests/test_native60_screenshot_jump.py`: native no-screenshot/DOM-evidence regression, legacy screenshot branch still supported, and synthetic 4-frame reversion vs genuine persistent source state differentiation. The original source/film were separately re-read by the full-rate detector, and the new independent source/film were re-read by the same detector after the fresh run.

## Fresh customer-style proof

New entirely separate `https://mantine.dev/core/modal/` request through the real `backend.url_engine.execute(...,intent="product_demo")` path, not an old footage replay or manual film plan. Worker private job path: `../.sauce-stagehand-private/customer-no-screenshot-jump-20261125/job-01/`.

- `direction.json`: `direction_source=bounded-public-modal-search`, **ai_calls=0**; Sauce auto-selected observed real `Open modal` control, not Gemini.
- Native Chromium source: SHA256 **`163b58704d2dd9d9ae45911b4c8cc96e63ab456f67fe20788dd0d0d7471b13a0`**, **405 frames / 6.75s / genuine 60/1 H264 1920×1080**. The full-rate detector reports **no** transient reversion, and the independent last-eight original frames are valid.
- Fresh final film: SHA256 **`1d83d9ceaa71763a260744ea2d4b3e90e335934d295d8e4ba5f2204bc59dc0e4`**, **269 frames / 4.49s / 1920×1080 H264/60fps with 48kHz stereo AAC**. Film itself has **zero full-rate A→B→A findings** and full encoded QA `HUMAN_REVIEW_REQUIRED` with no automatic issues. We independently reviewed 1.2–2.3s extracted actual encoded contact frames; original four-frame viewport jump is gone and source UI remains legible.
- All three diagnostic labels from the original customer job are preserved for audit, but continuous source MP4 is authoritative. Old film **must now be scored REJECT TRANSIENT_FRAME_REVERSION**; new technical output is **still NOT creative-approved**.
- Tests on the working current-main clone before publication: **566 Phase 2 pytest passed, 10 skipped, 21 subtests** and **386 legacy unittest passed, 2 skipped**, no regressions, diff check clean.

## Outstanding risks and creative limits

`backend/curious_sequence.py` still uses screenshot-based source verification for more complex sequential interactions. This particular change removes only the demonstrated in-recording `mark()` screenshots on the native60 ordinary customer path. The new independent final-output QA will reject short reversion defects if any other active capture path produces them. Longer-term, native60 sequence shots should use non-mutating X11 pixel samples or perform proof captures off the recorded display before recording; do not blindly disable sequence proof.

The natural Mantine modal overlay still appears abruptly (~0.6s), no obvious action-before-result visual explanation exists, and the product demo is only one small docs modal. **Zero premium film approval; no live service deployment**. Do not present the successful Gemini-free deterministic fallback as autonomous Gemini direction.
