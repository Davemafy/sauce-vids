# Sauce URL film self-repair — source-truth contract

**Status (2026-11-18):** A versioned, tested, non-deployed deterministic repair **decision and source-region verification layer**. It is **not** an automatic finished-video rerenderer. The dirty production StoryArc implementation remains outside GitHub main, and merging it safely is a prerequisite to connecting this layer.

## Why CMOkit passed technical checks but failed visually

The user-requested 30-second CMOkit job had four generated scenes, two browser clicks and a valid encoded MP4. Both clicks were same-document navbar anchors, **not operations of the CMO software**. The camera followed the navbar links themselves (82×21.59 and 44×21.59 CSS pixels), creating badly cropped, unfocused shots. Native 1280×720/25fps browser footage was delivered as a 1920×1080/60fps export, which doesn't increase original pixel or temporal detail. The opening remained almost unchanged for ~7.5 seconds. It was not a convincing software product demonstration.

Our earlier source-quality gate in `backend/url_film_quality.py` correctly calls this film ineligible. It did not yet prescribe or implement any repair.

## New recovery decision

`backend/url_film_recovery.py` introduces the immutable `RepairDecision` and `RepairStep` receipts, with a maximum of **two** bounded revision attempts and no automatic paid AI re-query.

1. **Diagnose** using existing verified browser inspection + scene outcomes. A successful section jump is not a software operation.
2. **Choose an honest film type.** If no observed non-navigation product action exists, the next draft is explicitly a *public website showcase*, not a verified product demo. Do not claim private product capabilities.
3. **Retarget verified source geometry.** For anchor clicks, take only observed, same-document fragments and re-check the real **destination section after scroll settles**. Never use the tiny clicked navbar element as the post-action camera subject. The `verify_visible_destination(page, fragment)` helper fails closed when a section or headline is missing, too small or offscreen.
4. **Rework the opening.** Use real first-party content, show the subject in the first three seconds, and avoid long inert hero holds. No invented before/after states.
5. **Address native fidelity.** Re-capture verified browser pixels at native DPR2 where possible, and don't label 25fps source frames as native 60fps motion.
6. **Produce only a three-second storyboard initially.** Check source visuals, shot scale, cursor semantics, clipping, and 390px readability. Require owner approval before a longer encode.
7. **Stop loss.** If the same defects recur, or two attempts are exhausted, stop, preserve the original, and mark the job rejected. No infinite Gemini calls, paid model retries, or fabricated results.

### Actual CMOkit check

Applied the pure decision layer to the exact saved CMOkit inspection and scene metadata on the existing Vultr worker:

- `film_kind=public-website-showcase`, `status=draft_required`, `attempt=1`, `draft_seconds=3`.
- Identified source-verified anchor fragments `how` and `pricing`.
- A fresh safe Chromium check resolved **#how** to a real 1280×671 pixel visible section with genuine heading *Two minutes, start to first campaign.*; **#pricing** to 1280×548 with genuine heading *No subscription.* These measurements belong to CMOkit only. They are not invented outcomes or a ready-to-publish film.
- Gate + recovery regression tests: **16 passed**. Unverified actions, missing/offscreen elements, bad identities, repeated failure signatures and exhausted attempt budgets are rejected.
- No new 30-second render, AI billing, customer requests or production mutations were executed.

## Integration gate (not done)

The production path currently imports uncommitted `backend/story_arc_pipeline.py`, `scripts/story_arc_capture.py` and `backend/story_arc_render.py` from a heavily dirty live checkout. These are not in `main`. Preserve them and their job records, reconcile explicitly into version control with appropriate tests, then connect the decision **before** expensive/full output and use an authorized browser adapter to execute source checks and produce the short revised draft. Record every attempt and evidence in a private receipt. Only promote verified product demos when real functionality and creative quality have actually been demonstrated. Never claim the self-repair is deployed until a live opt-in job completes it end-to-end.

Current owner creative gate remains **FAILED** for the 30-second CMOkit film and prior rejected OpenSheets work. Code and browser geometry correctness do not equal a premium film.
