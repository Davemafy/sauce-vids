# Sauce — Source-true reference-paced motion (2026-11-22)

Status: owner-only experiment, no premium creative approval and no public deployment.

## Root defect

The existing Resend source-true coverage film had genuinely too-fast continuous camera returns: 44.25 output pixels per 60fps frame, p95 34.37. A first experiment that changed ONLY classic symmetric quintic motion to asymmetric minimum-jerk easing plus same-frame shutter still peaked at 44.57 pixels/frame; blur did not cure the too-short transition. The private official Screen Studio 10.3667s motion study estimated pushes of about 0.84–0.96s and releases about 1.2s, though these are visual estimates, not proprietary implementation parameters.

## Reusable correction, no handcrafted customer EDL

- scripts/spatial_studio_stage.py now accepts opt-in studioStage.motion profile cinematic and shutter 0..0.75. Preserves the default classic film output unchanged. Cinematic transitions use monotonic bounded asymmetric minimum-jerk easing: no keyframe displacement, no re-timed source result, no overshoot. Shutter exposures are multiple projections of the SAME genuine browser frame; never read another source frame or cross a source-aligned editorial hard cut. Stationary text remains sharp.
- scripts/render_event_video.py draws the genuine recorded source cursor ONCE over the camera projection in cinematic mode, preserving exact screen/hotspot coordinates and not smearing its shape. Existing classic cursor path unchanged. Independent DOM-plane compositions fail closed if shutter is requested, rather than claiming unsupported spatial blur. Encoded receipt identifies motion style and active source-frame shutter samples.
- scripts/autonomous_shot_coverage.py automatically produces a new cinematic_paced variant using only real event times/DOM geometry: ~0.82s result pushes, natural hold and the source-safe longest release before the next real observed result. Release can finish during the NEXT genuine slider action only if the actual pointer and target stay on-screen. A stricter max 32px/native60-frame motion gate rejects the paced variant if the real event clock cannot safely accommodate it. It also offers a same-keyframe cinematic interpolation A/B against classic restrained. The existing owner-only coverage CLI generates, validates and renders variants autonomously without a model request or manual per-site JSON.

## Actual immutable Resend evidence and results

Original screenshot video is a verified Chromium capture, editorially trimmed to 613 authentic original frames / 10.2166667 seconds, 2880x1800 DPR2, native 60fps. Three actual slider-to-price outcomes retained ($35, $160, $350 per month), with 325 original recorded pointer samples. Input source SHA256: 6973a247624d514aa75b8d10c45a01a022942f2597f251c65aeb7d91a95ff586. Original rebased event manifest SHA256: efd1843cd6668b089f1fd41dfbd3db0263432a6da82e453daaf66d3d776e9168.

Frame-by-frame native 60fps camera quad speeds:
- Existing classic restrained: max 44.25px/frame, p95 34.37, 81 >25px intervals.
- Easing/shutter ONLY, identical source and camera keys: max 44.57, p95 35.84. Not sufficient.
- New source-aware cinematic_paced: max 30.67px/frame, p95 26.46, 37 >25px intervals. This is 31.2% lower peak than easing/shutter only; the original click times and all native pointer/DOM targets remain visible. Pushes ~0.83s; two releases ~0.98s and ~1.17s, which approach the measured reference pacing.

Actual autonomous director (zero model calls) generated and rendered two independently verified versions with identical original source capture and sound:
- Classic restrained film SHA256: 6c2ba57680f58e0e62bb58f044120a15e1e10c49474d7c65e1ceae0f93e64b6c
- Cinematic paced film SHA256: 60dc30af5068d1e50a6307ac92dd329d8c7a5cc849831d4aa1fc9bf122e32d30

Both true 1920x1080 H264/60fps, 613 frames, AAC48kHz, full strict FFmpeg decode; source-relative encoded QA HUMAN_REVIEW_REQUIRED with no objective findings. Actual protected Chromium playback and seek at desktop1280x720 and mobile390x844 succeeded; 0 JS/media errors. Signed review HTTP200 and unsigned403:
- Classic: https://devmcp.davemafy.xyz/sauce-expiring-review/tweakcn-20261120/sauce-resend-motion-classic-20261122.mp4?md5=nkuZ_jRN0JxNNEGp1kOPWg&expires=1795596626
- Cinematic paced: https://devmcp.davemafy.xyz/sauce-expiring-review/tweakcn-20261120/sauce-resend-motion-cinematic-paced-20261122.mp4?md5=GCOjuXNtgQc0t3pTysqWUA&expires=1795596626
Private 72-hour links, no public film release.

## Visual assessment

Inspected encoded first/action/result and transition frames, compared with unchanged prior Resend film and private actual Screen Studio motion-study reference. Pace is visibly more controlled during result release; individual results and real cursor stay source-aligned. Nonetheless the original webpage is dark and secondary text remains too small for a phone. The existing source consists only of pricing slider changes, not a complete compelling product story. This is an objective motion improvement, NOT a premium studio film, nor a general unknown-website proof. Existing Screen Studio sample is diagnostic, not a gold few-shot reference. Approved premium films remain ZERO.

Production use remains opt-in owner-only source-verified coverage; public Studio default is unchanged. No new VM, branch, manual source fabrication, credentials, raw media in Git, purchases or published artifacts.

## Verification

New deterministic tests of exact source time/keyframe invariance, monotone endpoint motion, no cut-crossing blur, independent cursor optics, geometry-informed longer releases and autonomous A/B selection. Full Phase2 plus model shootout suites on matching current main before commit: 468 passed, 10 skipped, 29 subtests passed. Handoff updated with exact proof and outstanding visual weaknesses.
