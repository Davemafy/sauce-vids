# Sauce Phase 2 — source-continuity scan and bounded automatic director

Date: **2026-11-18**. Status: **VERIFIED ENGINEERING TECHNIQUE, STILL NOT AN OWNER-APPROVED PREMIUM FILM**.

## What was actually wrong

The owner correctly rejected the manually directed Linear study as much weaker than the original Brimble proof. The 13-second revision fixed the giant/invisible cursor and floating-stage absence but remained an incoherent set of dense application states connected by edits. The root cause was not FFmpeg encoding: the **actual source browser recording** contains three large, light-colored page-remount intervals while the public interactive Linear preview changes state.

Full OpenCV scan of the original **1110-frame 2640×1440/60fps** capture from `https://linear.app/` (public marketing preview, not authenticated) found suspicious raw source ranges `[0,0], [185,257], [484,533], [733,778]` (170 frames total, about **15.3%** of captured footage). These **exactly match** the earlier manually excluded source ranges, discovered independently from decoded pixel data using unusually bright *border* and *interior* fractions relative to the source median. Both a light-themed stable source and isolated white controls avoid false positives in dedicated tests. This detector is conservative: other forms of corrupted UI can still escape it.

## The reusable changes

- **`scripts/source_continuity_scan.py`** streams real 60fps source frames (downsamples for measurement, never changes originals), checks optional pinned source SHA256, detects persistent relative-white remounts and emits exclusive safe source segments, with a one-frame post-remount stabilization margin. A separate validation function rejects a rendered EDL if it claims to use any unsafe segment or if its source hash/geometry/discontinuity receipt disagrees with actual captured video.
- **`scripts/source_true_director.py`** constructs a **bounded real-event shot plan without inference** from the scan and verifiable capture provenance: each recorded click must land inside its original target rectangle, each source-timestamped action must precede a genuinely observed DOM outcome, and each scene is clipped to verified stable source footage. No fabricated success states, clicks, pointer paths or screenshot rendering. It supports the *specific studied grammar* of 3 real clicks, 3 real outcomes and 3 remount gaps; other capture shapes fail closed rather than being wrongly classified as premium. Camera focus is chosen from observed result semantics and DOM geometry, including a broad verified overview of multi-metric results. Before rendering, it runs the shared actual-cursor projection check and permits limited zoom reductions only, never moving the recorded pointer.
- **`scripts/source_verified_whip.py`** provides an optional **5 source-frame directional camera cut** on either side of an actual shot boundary. Unlike the previously **rejected crossfade** (which ghosted two separate source UIs), every output frame contains **only one genuine browser source state**, translated and lightly directionally blurred for an instant. The original cursor is drawn *afterward* through the same camera projection. The viewable full film uses this technique, but the source still legitimately switches views at three cuts.
- **`scripts/evidence_edl_renderer.py`** adds `--continuity-receipt` for source-hash-matched proof and `--source-verified-whip` as opt-ins. Existing non-EDL workflows and default options remain unchanged. `scripts/cinematic_recorded_pointer.py` now reports **all affected shot indices** to avoid repairing only the first few offscreen frames while missing later violations.
- **`tests/phase2/test_source_continuity_director.py`** exercises synthetic video scanning, light-source false-positive resistance, frame-exclusive gap boundaries, fail-closed action/outcome/target validation, board-vs-code destination semantics, deterministic camera storyboarding, per-clip source-provenance checks and single-source camera cut behavior.

The first automatically generated edit was rejected for a real semantic error: the second result was misclassified as code because its evidence reads **"from code diff to agent task columns"**. Classification was corrected to prefer the verified destination (board) over the previous view; the corrected result was rerendered. A subsequent native-sized A/B exposed excessive matte around tiny UI. At **86% floating screen scale** (rather than 79%), the real code diff, task board and counters are perceptibly larger, with source-frame cursor visibility still **0 offscreen / 0 unrecorded frames**.

## Actual proof

[New 13.17-second source-directed Linear film](https://devmcp.davemafy.xyz/sauce-motion-phase2/quality-source-director-20261118/) · [original master MP4](https://devmcp.davemafy.xyz/sauce-motion-phase2/quality-source-director-20261118/master-1080p60.mp4) · [native-source before/after comparison](https://devmcp.davemafy.xyz/sauce-motion-phase2/quality-source-director-20261118/comparison.jpg).

H.264 1920×1080, 60fps, **790 frames**, duration **13.166667 seconds**, 48kHz stereo AAC. **Master SHA256:** `9b661e9b0eb0c9cde8b21da95e0d979b4f7e6e8d8ef71e50ccda4ae09fa8e475`. Export was built from the original pinned source SHA256 `7a539dd06e90257f237db0ad602301ca3fd8cc2db96ac802613904d010a8a454` and the fully validated source continuity receipt, with **no manually authored shot EDL**. Three true recorded interactions: Reviews → code diff, Agent tasks → board, Agent Insights → chart and original verified counters **3,389 / 1,128 / 729**.

Actual output cue frames: clicks **73 / 294 / 497**, source-backed state transition whooshes **97 / 322 / 520**; procedural Foley peak 0.1296 with no unlicensed samples or paid inference. Full master and 720p preview decoded with FFmpeg `-xerror`; scanned **790 encoded video frames** and detected **zero** near-white flash violations under the existing >3.5%-white frame criterion (maximum 0.001824). Output receipt verifies `sourceVerifiedWhip=true`, `continuityReceiptChecked=true`, floating `stageScale=0.86`, real cursor `offscreenFrames=0` and `unrecordedOpeningFrames=0`.

Live HTTPS returned **200** for watch page, master, 720p preview and comparison. Headless Playwright Chromium at **1280×720** and **390×844** genuinely played, sought to 9.72 seconds and advanced; media `readyState=4`, no video error, no JS errors and no horizontal overflow. Only approved public output artifacts (rendered MP4s, comparison, poster, player HTML) were exposed—no HAR, recordings of private sessions, raw source, event traces, keys or unpublished internal reference footage. The working source remains on the existing persistent Vultr worker in an isolated checkout of `main` and was never deployed to the application service.

### Reproduce on the existing worker

```bash
cd sauce-phase2-quality-main
PYTHONPATH=scripts ../.sauce-render-env/bin/python scripts/source_continuity_scan.py \
  --video /private/captured-source.mp4 --source-hash '<verified-sha256>' \
  --out /private/continuity.json

PYTHONPATH=scripts ../.sauce-render-env/bin/python scripts/source_true_director.py \
  --manifest /private/events.json --continuity /private/continuity.json \
  --out-edl /private/automatic-edl.json --out-report /private/direction-proof.json

PYTHONPATH=scripts ../.sauce-render-env/bin/python scripts/evidence_edl_renderer.py \
  --video /private/captured-source.mp4 --manifest /private/events.json \
  --edl /private/automatic-edl.json --continuity-receipt /private/continuity.json \
  --out /private/film-silent.mp4 --quality-gate --floating-stage \
  --stage-scale .86 --premium-cursor --click-water-ripple \
  --camera-shutter --source-verified-whip
```

Tests: `../.sauce-render-env/bin/python -m pytest tests/phase2 tests/phase3 -q` → **140 passed, 11 skipped**. Also run legacy unittest and TypeScript planner as part of coordinator verification.

## Remaining creative defects / stop-loss

This is **not a 10/10 film** or a universal zero-configuration URL→commercial-video product. This capture is a dark, detailed public marketing preview, not one continuous dependent workflow; three substantial original remount gaps remain, though the renderer no longer shows their white pixels. The rapid editorial cut preserves one genuine state at a time but cannot create true continuity that the website never recorded. Long code and board holds are still small on phone; a fresh unbroken product action with live scrolling/motion would be a better production reference.

**Provisional self-critique ~6.5/10**, not owner/independent approval. The key improvement is that Sauce can now *detect and refuse compromised footage and produce a bounded source-verified motion plan without a human-written EDL*, while preserving all high-quality existing cursor/compositor work. This experiment is deliberately **not wired into the untracked production StoryArc pipeline** until a second actual product capture and independent aesthetic quality gate pass. Next useful work is to capture a **continuous second product workflow** with actual smooth scrolling and a meaningful result, then compare its film to premium reference motion and fix the lowest-quality scene, not stack more cosmetic filters over broken input.
