# Sauce — source-true floating UI, cursor and ripple quality recovery

Date: **2026-11-18**. Status: **VIEWABLE QUALITY STUDY; OWNER APPROVAL NOT ESTABLISHED**.

## Trigger and reference

The owner rejected the prior [action-first Linear study](https://devmcp.davemafy.xyz/sauce-motion-phase2/quality-action-first-20261118/) as a visual downgrade from the real Brimble ripple demo: the angular cursor looked unprofessional, repeatedly went offscreen, motion felt rough, there was no click refraction and the app was full-bleed rather than floating on a studio backdrop.

Inspected native encoded frames of that film, the locally retained Screen Studio demonstration and Brimble cursor optics. The real public Linear interactive marketing preview—not a Linear account—was already recorded at **2640×1440 DPR2, 60 fps**, with 1110 captured source frames, 19 events and 368 measured X11 pointer samples. Source SHA256 `7a539dd06e90257f237db0ad602301ca3fd8cc2db96ac802613904d010a8a454`. The three verified actions remain Reviews→real code diff, Agent tasks→real board, Agent Insights→real 3,389/1,128/729 metrics.

## Reusable renderer changes

- `scripts/cinematic_recorded_pointer.py` shares the existing **reference-v15 black-rounded.svg** sprite from the successful Brimble cinema pipeline. It uses ~25ms symmetric smoothing to suppress high-frequency X11 sample jitter, corrects the position to **exact recorded interpolated coordinates on each real click**, draws one pointer after all media transformations, and retains the final recorded coordinate rather than inventing an ending move.
- `scripts/floating_ui_stage.py` wraps actual decoded Chromium pixels in a physically rounded screen, soft real exterior shadow and understated charcoal neutral matte. The window scales/reframes in the native video compositor; the public web page applies **no presentation CSS** to fabricate the motion.
- Existing `scripts/click_water_ripple.py` is now reusable from `scripts/evidence_edl_renderer.py --click-water-ripple`. Every refraction center is the measured cursor position at an actual source-clock click projected through the exact film camera, **before** the pointer artwork is drawn. It never fabricates product state.
- Existing `--camera-shutter` creates three source-frame-derived motion samples on moving camera frames; stable reading holds remain sharp. New `--floating-stage`, `--premium-cursor`, `--stage-scale`, and `--click-water-ripple` remain **opt-in**.
- One new source-verified camera anchor `result-upper:<index>` favors the upper 34% of a measured result rectangle so the recorded pointer/tab and code remain in-frame. The quality gate calculates projected recorded-pointer visibility for each actual source frame and rejects absent/offscreen pointers before full encoding. The same original camera functions and outcome/overview anchors remain.
- `tests/fixtures/linear-cinematic-polish-v6.json` is the explicit **operator-selected** EDL using original real source frame ranges, not an autonomous URL director. Its first segment starts after the first actual pointer sample, and its compact 4-shot grammar preserves code, board and complete metrics. No live capture or raw browsing trace is committed.

## Attempts and evidence

A 960p comparison exposed a **real regression** in a 9-frame source-to-source dissolve: the application text doubled/ghosted across cuts. The entire proposed dissolve implementation was **rejected and removed**; deliberate hard cuts remain the truthful choice where the recorded preview has white state-remount frames. Do not ship that rejected technique.

Old flat V5 source-camera analysis: **48** output frames precede actual pointer evidence and **252** recorded pointers project outside the 1920×1080 composition. New V7 frame-provenance receipt: **0 unrecorded opening frames**, **0 offscreen frames** across **790 output frames**. The verified click hotspots remain inside all three actual DOM targets, without guessed clicks, coordinates or visual relocation.

**Viewable revised film:** https://devmcp.davemafy.xyz/sauce-motion-phase2/quality-cursor-ripple-20261118/ .
**Exact H.264 1080p60/AAC master:** https://devmcp.davemafy.xyz/sauce-motion-phase2/quality-cursor-ripple-20261118/master-1080p60.mp4 .
**Side-by-side film-frame comparison:** https://devmcp.davemafy.xyz/sauce-motion-phase2/quality-cursor-ripple-20261118/comparison.jpg .

SHA256 `c3e307d28f7d195b022be782113f23f8bbafa4b54c6e7d5fb00ede8a5e8ed14f`. H.264 **1920×1080, 60fps, 790 frames/13.166667s**, AAC stereo **48kHz**, PCM exactly **632,000 samples**. All **six** deterministic procedural Foley cues aligned to real output frames: clicks **73/293/497** and source-backed change transitions **96/321/520**. Full master and 720p preview FFmpeg `-xerror` decode succeeded. Private render receipt and source remain on the existing Vultr worker; static public files contain only player, MP4s, poster and visual QA comparison.

Public HTTPS returned **200** for page, master, preview and comparison. Playwright Chromium verified real preview **play→seek 8.4s→advance** at **1280×720 and 390×844**, `readyState=4`, no video or JS errors, no horizontal overflow. Actual full-resolution frames at first interaction, code focus, second action and final payoff were inspected; native 2× click crops show the rounded SVG pointer over the real three target rows.

## Tests, creative quality, limitations

New unit tests protect source-time click alignment, exact SVG hotspot, bounded smoothing, float shadow clipping, no fabricated state, source-geometry-only upper anchor, pointer visibility rejection, and click-water refraction. `pytest tests/phase2 tests/phase3 -q` → **130 passed, 11 skipped**; Python legacy unittest **205 passed, 1 skipped**; TS StudioMotion tests **34 passed**. Full FFmpeg decode passed.

**Visual result is stronger than the user-rejected flat cut, but NOT premium-approved. Provisional independent-of-owner quality estimate: 6/10.** Opening and closing app-on-matte shots are now professional-looking and clean, all source clicks/cursor are visible, but the Linear marketing preview remains dense/dark, the three real state-remount gaps still require editorial cuts, and the product sequence is a tour rather than a dependent user journey. Brimble-style effects alone are insufficient to establish Screen Studio/Apple/Refs parity.

Do not mistake this operator-directed opt-in EDL for automatic production of premium films from arbitrary pasted URLs. The existing untracked production StoryArc work and other agents' isolated checkouts were not reset, overwritten or deployed.
