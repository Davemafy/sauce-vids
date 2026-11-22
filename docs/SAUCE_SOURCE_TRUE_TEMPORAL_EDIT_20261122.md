# Sauce — Source-true beat-locked temporal edits (2026-11-22)

**Status:** verified engine capability, owner-only experiment, CREATIVE REJECT. The 6.33-second edit is **not** a premium film, a self-serve URL demo, or a new site-agnostic content director.

## Problem and actual hypothesis

The existing compositor can produce valid JSON camera instructions, but it is asked to rescue boring continuous screen recordings. We tested a film-level change: make the original verified source's action/result clock drive a **short, native-frame edit list** rather than only moving the camera. Reuse existing Sauce Phase 1 TypeScript `buildTimeWarp`/`beatLockTimeWarp` instead of implementing another timeline engine. The original source and renderer are immutable.

## Implementation

- `scripts/studio-motion/src/timeWarp.ts` admits `verified-result` as a protected time-warp intent **only** with an independently asserted `verifiedSource: true` flag. An unverified model marker cannot declare an outcome. Existing behavior for earlier trace types remains the same.
- `scripts/studio-motion/src/sourceTrueRecut.ts` is a small bounded CLI adapter from *already verified* original source-manifest clicks/releases/results into the preexisting 60Hz beat-lock engine. It protects a real opening and the real press-to-result interval and >=0.65s of genuine result frames; edits only source-true idle gaps. Never duplicate, reorder, freeze, resynthesize, change state, change cursor or invent timing. A continuous workflow with no genuine gap is **rejected** rather than forcing edits. No user URL/browser navigation is performed here.
- `scripts/source_true_film_recut.py` accepts actual SHA256-bound source/manifest/film JSON/full-render receipt/prior mastered video. Fails closed unless the original 720 native 60fps source frames and verified rendered 1920x1080/60 H264/AAC48k master match. Compiles a JSON source-frame edit, trims original master video by frame and audio by the corresponding integer 800 samples per frame, concatenates and transcodes to 1920x1080/60 H264/AAC48k, full-decodes the result, and verifies sampled output pixels are the corresponding original rendered frames, within a small H264 re-encode tolerance. Produces an auditable private receipt. **This is a bounded post-render proof tool, not yet the default public Studio workflow.**
- `scripts/studio-motion/src/tests/sourceTrueRecut.test.ts` and `tests/phase2/test_source_true_film_recut.py` cover positive/negative original event evidence, no invented marker, 1x source frame continuity and post-result hold, source frame provenance, audio trim sample math, no overwriting old work, and no forced discontinuities in a dense Resend workflow.
- The source/current UIColors director plan for the visual proof was a private source-hash-bound variant (contrast modal scale1.15, result visible1.0, output source context0.671, 0.42-frame camera shutter), **not a hardcoded app template committed to production**.

## Genuine browser evidence

Reused an existing owner-only authenticated-in-no-way anonymous public Chromium recording of the actual UI Colors generator. Two independently verified source interactions: **Switch to dark mode**, then **Contrast matrix**. Both from original browser state and actual changed pixels. No fake controls, synthetic source screenshots, form submissions or cross-origin actions.

- Original 2880x1800 DPR2, 60fps/720f/12s Chromium MP4 SHA256 **`dc1c48559b7bc842eba3ad405c44724dbf06bdc9e2d748da7495cfb0384a1dbd`**.
- Verified event/recorded cursor manifest SHA256 **`90dddc0468c41e87fcf1b1f5bd58dbf11f9f7499b7c65ddcb26d066c143bde87`**; 92 genuine recorded pointer samples.
- Source-native timeline edit: **380 frames/6.333333s** at 60fps:
  - source frames **[0,42), [108,270), [350,526)**; cut at output frames **42,204**.
  - press event0 source frame132 => output66; original verified result source191 => output125.
  - press event1 source frame374 => output228; original verified result source447 => output301.
  - every original click-to-confirmed-result frame and >=39 post-result source frames retained; all output frames strictly increase in source clock with no duplication.
- Actual full 12s source-locked directed film, owner-only protected: [watch original](https://devmcp.davemafy.xyz/sauce-expiring-review/tweakcn-20261120/sauce-ui-colors-directed-original-20261122.mp4?md5=rwySK4G4MkqcqfRZL0pkFA&expires=1795641377).
- Actual compiled 6.33s source-locked recut, SHA256 **`2783c25ca63b912d04c1377591dc8c149cb687ad3a86564978d059c0cdca3c68`**: [watch recut](https://devmcp.davemafy.xyz/sauce-expiring-review/tweakcn-20261120/sauce-ui-colors-beat-locked-20261122.mp4?md5=GwCnm9ygzMJQEU1vS2olfg&expires=1795641377). Temporary 72h signed 200/unsigned 403, no public release.
- Independent video verification: 1920x1080/60fps H264, 380 frames, 6.333333s, 48kHz AAC stereo, strict full video/audio FFmpeg decode. Pixel lineage: 46 time-indexed samples including both real presses, results, and both cut boundaries; maximum downscaled grayscale mean absolute difference **0.2675/255**, median **0.1219/255**. No fabricated browser content, giant generated cursor or invented UI.
- Independent sample-exact cue audit compared decoded original and recut audio near both genuine recorded click frames. Original event0 frame132→output66, offset **0 samples**, normalized correlation **0.999**; event1 frame374→output228, offset **0 samples**, correlation **1.000** (at 48kHz), measured via cross correlation on original AAC and new AAC.
- Real signed video HTTP200 (unsigned HTTP403), Chromium desktop1280x720 and phone390x844 **play+seek** tests passed for both original and recut with zero JS/media errors.
- In an earlier cold discovery pass against **featuredrop.dev, HeroUI tabs, Radix UI tabs, realtimecolors.com, coolors.co and tints.dev**, no safe strongly visual two-event workflow was admitted by the existing strict anonymous scouts. This is a genuine generality limitation, not a reason to fabricate a showcase.

## Honest negative visual comparison

Viewed actual contact frames from both real encoded videos and the genuine original browser contrast-matrix screenshot. The new shorter cut has a clearer actual light→dark→matrix sequence, but is still **CREATIVE REJECT**: the 6.33s film is a largely static UI tour, the contrast matrix is dark and visually dense, the opening spends too long on uninformative page context and is not premium mobile-legible. Existing encoded technical QA reports **STATIC_OPENING_2S** and **REPEATED_OR_STATIC_FRAMES** (72.6% quiet samples on the recut), along with abrupt cut candidates because the general QA does not yet consume this new explicit edit-map receipt; the known original source theme change is real, not a fake edit. The film is **not** approved by the owner, and no quality score is inflated.

An earlier 6.68s manual edit and a beat-locked variant using the legacy film were also tried and visually rejected, not promoted into templates. The new source-true proof does not implement an automatic customer-director reshoot or premium reference match; the next improvement needs a *source-discovery/semantic-payoff quality decision* before capture rather than polishing an unreadable matrix.

## Tests and preservation

Full Python Phase 2 + concurrent model-shootout regression: **478 passed, 10 skipped, 29 subtests passed** before GitHub commit. TypeScript `npm test`: **38 passed**. Source files, test fixtures and this text only are committed to main; no private MP4s, images, user sessions, APIs, secrets, browser profiles, raw source captures, research references, new infrastructure, branch or deployment.

**Zero premium/paid-client quality approvals.** This is a concrete reusable *timeline editing capability*, not the larger autonomously art-directed product breakthrough.
