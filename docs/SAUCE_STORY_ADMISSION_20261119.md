# Sauce source-first story admission: 2026-11-19

**Status:** Opt-in engineering guard verified on the real, owner-rejected OpenSheets source. **Creative gate remains FAILED.**

## Root cause, grounded in actual pixels

Sauce was verifying real clicks, native captures, cursor alignment, source FPS, and camera mechanics without checking whether the product change itself was visually substantial enough for a short cinematic film.

On the actual private OpenSheets 3200×1800 DPR2/60fps source, a real currency-toolbar click at source t=4.814 is followed by a browser-verified five-cell formatting result at t=4.8493. The original measured result rectangle is x1956/y446/w276/h218: just **1.045% of the source image**. Decoding actual source frames 293 (before) and 334 (after) and comparing their 640×360 downsampled, antialias-smoothed images finds **0.109% of the whole frame visibly changed** and **9.862% of the small result region** changed. This is a true but visually tiny interaction. Expensive 4K re-recording, refractive glass, cinematic cursors, or 1080p60 encoding cannot produce a good silent promo from this signal alone.

Exact private evidence:
- /var/lib/sauce-steward/qa-logs/visual-director-20261119/opensheets-before-true.png
- /var/lib/sauce-steward/qa-logs/visual-director-20261119/opensheets-after-true.png
- /var/lib/sauce-steward/qa-logs/visual-director-20261119/opensheets-source-admission-board.jpg
- /var/lib/sauce-steward/qa-logs/visual-director-20261119/opensheets-admission.json

The real OpenSheets admission returned REJECT with both RESULT_TOO_SMALL_FOR_SHORT_SILENT_FILM and WEAK_VISIBLE_TRANSFORMATION. No another full rendering was attempted.

## Source-selection research (real site/browser preflights)

- **Linear:** multiple genuine views, but remount gaps and no coherent single action/result; owner-rejected as 3/10. Earlier film tests passing did not change that.
- **tldraw:** real on-canvas interaction generated a sparse, awkward diagram. A screenshot review rejected it before recording.
- **Haikei:** colorful wave canvas, but real change from five to nine waves affects only about 1.3% of sampled frame pixels at a large-difference threshold. Its published Terms prohibit automated browser access: do not record a commercial automated demonstration without permission.
- **Realtime Colors:** source visually strong, but associated public Github material is CC BY-NC-ND; do not presume commercial rights.
- **GrapesJS:** actual editable website builder, but the current default demo template is dated and not suitable as a premium showcase. A permissive source-code license does not automatically grant rights to every sample artwork.

These cases are *creative and rights preflights*, not authorized public Sauce product samples.

## Implemented

New opt-in CLI scripts/story_viability_preflight.py compares genuine before/after source screenshots, a recorded action, a browser-observed DOM outcome, physical source-space result geometry, source URL and a declared rights scope. It never creates or retouches product pixels. For the **visually transformative short silent promo style only** it rejects when the result is under 5.5% of the original frame, fewer than 3.5% of original frame pixels change, or fewer than 7.5% of result-region pixels change. Empty/invalid proof and unsupported rights declaration fail closed.

Rights scope is supplied by the operator; it is NOT independently verified by this tool. SHA256 of both screenshot files is recorded; that alone does NOT prove provenance without a trusted collector. This is a conservative triage heuristic, NOT an automatic aesthetic score, and not a blanket verdict on legitimate low-motion instructional product demos.

Result status:
- reject_source_before_video with exit 3 (no full encode)
- candidate_first_three_seconds_only with exit 0 (no premium approval)
- malformed evidence exit 2

Integrated opt-in scripts/evidence_edl_renderer.py --visual-preflight-receipt FILE: validates source URL, real manifest clock/action, result rectangle, screenshot hashes and candidate status; refuses attempts to use this receipt for anything except an openingStudy film capped at 30–180 frames/60fps. All other rendering modes and production defaults remain unchanged.

## Independent reviewer still has veto

Passing numerical gates only allows a short candidate. Its native encoded first frame, first three seconds, cursor and result must be watched at 1080p and 390px phone width, compared with actual Screen Studio/Refs scenes, and independently approved before any longer encoded film. An ugly or generic design can pass pixel-change metrics. A subtle genuine action can be good in a different, narrated film style despite failing this **specific** cinematic-silent-source filter.

The immediate commercial film-quality gate is still OPEN. Stop after two failed visual candidates and change source/workflow instead of stacking visual effects.

## Verification

Focused regression: 13 passed. Full Phase 2: 182 passed / 10 skipped. Legacy unittest: 206 passed / 1 skipped. TypeScript not modified or rerun. No public new film, customer account, inference spend, new VM, production deployment, or production service restart.
