# Sauce Phase 2 — first-three-second composition gate and rejected Excalidraw source

**Date:** 2026-11-19. **Status:** Reusable opt-in QA improved and verified against two true application videos. **Premium film acceptance: FAIL.** No producer or independent critic has approved a 10/10 film.

## Why this experiment was needed

Previous native/green Phase 2 films were rejected visually despite frame-count, source-hash, real pointer and codec correctness. The 900-frame Resend pricing film was independently rated approximately 5/10 by the coordinator: oversized cropped "Pricing" heading, cut-off adjacent cards, dark static areas and repetitive pricing increments. Its original H.264/AAC master SHA256 is `181d28043154ec805e4b0aadd96c5b2bdd3b7662decd6c4c9c056988cdc0d5ca` — [watch it and its genuine older-film comparison](https://devmcp.davemafy.xyz/sauce-motion-phase2/resend-15s-20261119/). Passing tests did not change that verdict.

Source-first editorial decisions matter more than water-ripple quantity. The candidate's main visual focus must be large enough to recognize and its critical labels readable on a ~390px landscape feed. Existing Sauce continuity, motion, pointer, source hashing and refraction remain intact; no template or model was introduced.

## Actual alternate source, original real browser motion, and acceptance decision

Tested an anonymous **public Excalidraw** workflow in isolated Chromium/Xvfb; no sign-in or private customer document. The source was a genuine **2880×1800 native DPR2 60fps, 960-frame/16s** recorded browser session. Source SHA256: `66c0f500671c2b9e3ccdb02fab0f5e794391eea11548d49e212684d9c74da538`.

Original real mouse/keyboard interactions built a three-stage diagram on the native canvas: blue "Capture" rectangle → real arrow → green "Direct" rectangle → real arrow → yellow "Publish" rectangle → heading → actual Excalidraw **Export image** menu/dialog. Recorded per-action physical cursor samples, button target rectangles, three real intermediate scene-state receipts (rectangle/arrow/text types and persisted colors), and actual visible export dialog. A first capture failed its scene-state timing check because Excalidraw persists local state asynchronously. Rather than falsely "repair" the scene in a compositor, the bounded recorder waited for the actual browser state to persist. The corrected real capture was repeated with a speed-limited physical mouse traversal, because the original source cursor moved too abruptly between canvas and palette.

Original two-stage/three-stage browser source frame comparisons passed the opt-in visual-change preflight: third-stage result represented approximately **8.4% of original full-frame area**, **5.3% whole-image pixels changed**, **46.1% of the result area changed**. This allowed examination of a three-second candidate, **not** a full film and not rights/licensing approval. The final candidate was rendered from **180 consecutive native real browser frames**, exact H.264 **1920×1080, 60fps, 3.000s**, using existing Sauce Brimble professional recorded cursor, existing camera shutter and water refraction, and a neutral floating-window composition. Original source UI remained unchanged. **No 900-frame Excalidraw film was rendered or approved.**

**[Watch the rejected real 3-second MP4](https://devmcp.davemafy.xyz/sauce-motion-phase2/excalidraw-opening-review-20261119/opening-3s-1080p60.mp4)** · [review player, actual encoded-frame contact](https://devmcp.davemafy.xyz/sauce-motion-phase2/excalidraw-opening-review-20261119/). Master SHA256 `82cdc90291ecbbfed9d035326916d5615fb6644dbb7f1577dbb28156bdef0860`. Strict FFmpeg full decode passed; browser playback, seek and frame advance at 1280×720 and 390×844 passed (HTTP 200, `readyState=4`, no JavaScript/media errors or horizontal overflow).

**Creative rejection:** Examining actual 3-second video frames side-by-side with the private authentic Screen Studio demonstration showed a mostly blank canvas, one small rectangular object, prolonged low-energy establishing time, and a simplistic push that did not establish product value. The existing supervisor independently flagged `STATIC_OPENING_2S` (80th-percentile sampled motion delta **0.49**), `REPEATED_OR_STATIC_FRAMES` (**55.2%** low-motion samples). The video is silent because it was a failed short candidate, never a claimed final commercial film. No need to add Foley to a rejected opening.

## New reusable opt-in engineering correction

Only the production-independent QA path `scripts/quality_preview_supervisor.py` and focused tests are proposed for integration into `main`. The unrelated rejected experimental one-off Excalidraw capture/director and fixed-stage camera code remain **unmerged, private, and clearly unapproved**.

`verified_focal_geometry(source_evidence, output_size)` accepts source-measured subject rectangle, source video dimensions, the actual 2×3 compositing matrix, and the measured output stage-window bounds. It checks:

- `SMALL_VERIFIED_PRIMARY_SUBJECT`: visible principal action/subject area under **8%** of output (conservative rule for explicitly **selected primary-subject silent cinematic studies**, not every SaaS demo).
- `FOCAL_TARGET_CLIPPED`: less than **97.5%** of the measured selected subject remains visible.
- `PARTIALLY_CROPPED_SOURCE_TEXT`: an explicitly marked critical source UI text rectangle is neither essentially completely hidden nor entirely visible. This is the class of defect that repeatedly spoiled actual Resend shots.
- `UNREADABLE_CRITICAL_TEXT_AT_390PX`: source-measured and explicitly protected title/price text, projected through the affine camera, becomes under **8.5px** at a 390px landscape player. Requires physically measured source font size (not guessed); no claims about unmarked body copy.

`verified_focal_sequence` verifies frame-indexed **contiguous** 1–900 camera matrices starting at 0, not a hand-selected single frame that could hide a moving shot's text crop. It groups issues into `first_frame` and `affected_frames`. Optional critical-text visibility intervals `start_frame/end_frame` ensure it never reports text as cropped on frames before it genuinely exists. Bad/NaN/out-of-source geometry, invalid stage windows, missing matrices and malformed event frame indices fail closed. These opt-ins append findings to the existing `analyze(..., evidence=...)` receipt and force a REJECT rather than claiming an automated aesthetic score. Defaults, existing complete scripts, production URL handler and compositor behavior remain unchanged.

### Actual encoded two-application verification

1. **Excalidraw 3s/180f**: source rectangle from the persisted real Excalidraw rectangle (source x730, y740, w450, h430), original film and every actual camera matrix checked. Its sampled main shape occupies **~2.5%** of the output in the initial establishing shot, and less than 8% in **all 180 frames**, including max zoom closeup (~7.6%). Real encoded film receipt: `STATIC_OPENING_2S`, `REPEATED_OR_STATIC_FRAMES`, `SMALL_VERIFIED_PRIMARY_SUBJECT` (**180/180**); **REJECT**. A simple source-true text clock example was tested synthetically but not claimed as Excalidraw DOM provenance.
2. **Resend 15s/900f**: independent original genuine price DOM rectangle x870, y1157.59, w498, h122.39 from its real source manifest; exact source-hash verified and all **900 actual affine camera matrices** loaded from the committed documented Resend director. When this recorded price result is designated as the primary focal subject, the same QA detected `SMALL_VERIFIED_PRIMARY_SUBJECT` (**900/900**), plus the original supervisor's `REPEATED_OR_STATIC_FRAMES` and `LOW_VISUAL_DETAIL` signals: **REJECT**. A price label alone is *not* all the context a narrated calculator film needs; this is a deliberately narrow silent-hero heuristic.

Both encoded analyses used real source SHA256, manifest SHA256 and existing original public film decode, not invented UI or post-processed source images. Raw source/browser trace is never publicly served. No independent film signoff was obtained for this attempted alternate product.

## Practical reference-to-engine acceptance contract

Actual observed 10.37-second / 60fps Screen Studio reference shows a decisive deliberate crop into the meaningful on-screen task, clear before/action/result sequencing and relatively little empty frame area. The Sauce Excalidraw 3-second candidate remains white, sparse and low-contrast; a 1.73× zoom does not solve the underlying storytelling weakness. Our acceptance rule is: **verify source and real outcome → check actual focal coverage on *every camera frame* → protect measured critical labels during their real visible intervals → reject incoherent/illegible clip → review full encoded video at normal speed and mobile size.** No 95%-match claim or source footage reproduction.

The editor must choose a genuinely high-impact, rights-cleared SaaS feature journey with a visible consequence; using more water/blur/3D effects on empty canvas is a stop-loss failure. A small data widget can still make an excellent tutorial with narration and a different format; it is not automatically excluded from Sauce as a product class.

## Verified commands and scope

```bash
# On existing Vultr worker, in isolated clean main checkout only
../.sauce-render-env/bin/python -m pytest \
  tests/phase2/test_verified_opening_focal_geometry.py \
  tests/test_quality_preview_supervisor.py -q
../.sauce-render-env/bin/python -m pytest tests/phase2 tests/phase3 -q
../.sauce-render-env/bin/python -m unittest discover -s tests -q
cd scripts/studio-motion && npm ci --offline --no-audit --no-fund && npm test
```

No new VM, paid inference, customer session, destructive operation, fake application screenshot, production deployment, or forced GitHub update. **Current flagship acceptance remains blocked:** past 900-frame films exist and play, but no outstanding owner/independently approved 15-second film was demonstrated; generic URL→premium 900f workflow has **not** passed. Future reports must preserve the honest quality score and independent-vs-producer disagreement.
