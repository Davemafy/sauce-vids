# Sauce — one-call action/EDL ablation, 2026-11-21

Status: research-only. No approved premium film and no successful live Gemini JSON.

## Immutable real source and deterministic input

Actual Resend public pricing UI captured with Chromium/X11 at 2880x1800 DPR2, true CFR 60fps, 960 frames / 16 seconds. Original source SHA256:
3d28c84e02406eb39822610e627613188fdc9482d8bc074fe316a58184123d58
Original verified event/real cursor manifest SHA256:
ed3b68ba6e8a9d6d4349048a9f805f312dcba4e7da3ef5743552e62906614fd3

New opt-in scripts/source_action_clip_preprocess.py verifies immutable expected hashes, actual event timing and rectangles, preserves real cursor samples and action/result windows, and uses FFmpeg source-frame trims. It does NOT fabricate page pixels, clicks, content or successes. Output explicitly denotes an EDIT of the original Chromium footage, not a new continuous browser recording. Any previously captured DOM clean plates are discarded rather than falsely retimed.

Final shortened source v4: 613 frames, 10.2166666667 seconds, 36.15% shorter than 16 seconds. Source native frames [135,308) and [366,806), in order; all three observed pricing outcomes ($35, $160, $350 per month) and 325 genuine original pointer samples retained.
Edited source SHA256:
6973a247624d514aa75b8d10c45a01a022942f2597f251c65aeb7d91a95ff586
Rebased event manifest SHA256:
efd1843cd6668b089f1fd41dfbd3db0263432a6da82e453daaf66d3d776e9168

## Live one-call provider trials

One gemini-2.5-flash generation request on earlier source v2 (11.85 seconds): HTTP 404. No model plan. One gemini-3.7-flash generation request on separate source v3 (10.2167 seconds): HTTP 503. No model plan. No retries on either, no invented output. Model-list advertised 3.7 Flash generateContent support, which did not establish live service availability. No provider token-usage metadata was returned; charges were not verified.

The existing auto_direct_studio_film.py --max-attempts 1 made those requests. New opt-in scripts/one_call_edl_ablation.py supports one model response containing 2-3 different source-hash-pinned executable film plans plus a chosen favorite. Its validator inspects each locally; no AI critic call, retry, or invented fallback. This exact multi-variant path passed mock-response/HTTP503 tests only; it has NOT succeeded on live Gemini. Not wired to Studio.

## Actual film and first visual review

Model-free control generated using existing source_event_director.py plus existing Sauce renderer on final v4 source. Genuine output H264 1920x1080 60fps, exactly 613 frames, AAC 48000Hz stereo. Film SHA256:
49e6b668c64f1d2a7f5fefec0e255d6f43f679fa653db65c9404209885d8154a

Private signed 72-hour review, not public launch:
https://devmcp.davemafy.xyz/sauce-expiring-review/tweakcn-20261120/sauce-resend-singlecall-control-20261121.mp4?md5=Ew43uiRCGAw-C9PZFzqoPQ&expires=1795557208

Signed HTTP200, unsigned HTTP403. FFmpeg full decode passed; real Chromium play and seek to 5.0s succeeded at 1280x720 and 390x844, with zero video/JS errors. Source and encoded contact frames were opened beside existing 16s baseline. Original website is dark and dense; new framing remains a plain browser crop with insufficient early visual interest. Small UI type would be difficult on mobile.

Previous 11.85s deterministic v2 was rejected for STATIC_OPENING_2S and REPEATED_OR_STATIC_FRAMES (fraction 0.559). Final 10.2167s v4 eliminated the repeated/static-frame reject but STILL FAILED STATIC_OPENING_2S (opening p80 frame delta 0.742). CREATIVE REJECT. No owner-approved premium films.

## Exact renderer and provider bug corrections

render_event_video.py previously integer-rounded native source audio duration to milliseconds while passing an exact 613/60 second duration to foley_mixer.py; this caused safe fail-closed rejection, Audio cannot end before video frame timeline. Preserving floating-point millisecond duration now passes 48kHz sample-clock alignment. auto_direct_studio_film.py classifies HTTP 500/502/503/504 as provider unavailable instead of leaving misleading pending status.

No public deployment, main-only changes, new VM, destructive overwrite, raw media in GitHub, API key in logs/repo, model-response substitution, or paid purchase. The source and all failed attempts remain private on the existing worker.

## Next test

When Gemini actually responds, invoke the single-call multi-variant R&D runner once on the unchanged v4 source and manifest. Render each strictly accepted variant and compare against premium references using actual first/action/result frames. A successful deterministic validator is never a visual quality signoff. Revisit source composition and opening editorial clarity rather than chasing static-frame numbers.
