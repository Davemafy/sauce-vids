# Sauce Phase 2 — Arcade motion transfer experiment (2026-11-19)

**Decision: FAILED as a gold reference / Gemini-superiority experiment. PARTIALLY PASSED as a measured, source-true compositing primitive.** Do not make this a production preset or advertise the films as approved.

## Research question and strict boundaries

Can a genuinely measured Arcade motion recipe make two different software recordings more compelling than (A) plain source footage or (B) ordinary instruction-guided camera movement? Does this prove supplying verified reference pairs to Gemini improves first-pass film quality?

**Experiment executed:** 3 deterministic/manual Sauce-film-plan-v1 composition arms on two real, event-verified public browsers. All six real 4-second MP4s encoded and fully decoded, and a reference-normalized fitted HeroUI shot was independently rerendered from a freshly generated plan **byte-for-byte identically**. This is an ablation of the **rendering and reference-transfer pipeline**, NOT a blind comparison of three Gemini outputs. **No Gemini model was called, no paid inference or API credentials used, no customer film shipped, no rights to reproduce the original Arcade product UI assumed.** No independent creative approval was obtained.

The result **does not establish** that Gemini with an executable example outperforms Gemini with style prose or no reference; that causal model comparison remains undone. The ablation answers a narrower question first: *can an accurate measured cinematic motion shot transfer safely to these products?*

## Original reference: measured frame evidence, not invented keyframes

Public Arcade **Stack by Ramp**, encoded source SHA256 \`7d22a17f97d3183cae73df90321f7be7943006d9bf7f4ecd7c2a79f15215bbbf\`, 67.2s H.264, 1920×1080/30fps, 2,016 frames. Its isolated "Post to QuickBooks" shot spans **frames 1392–1437 inclusive (46 frames)**. Actual bright-panel boundaries were measured from **every original decoded frame** by thresholding original BGR channels ≥243 and taking the largest connected region with area >25,000px. The numerical track is in \`references/arcade-posting-panel-46frame.research.json\`. Only numeric data is committed; third-party media remains private.

The real reference panel moves from **(x=200,y=300,w=1520,h=480)** at frame 1392 to **(185,295,1550,489)** at frame 1437. It remains horizontally centered; panel width increases **30px / ~1.97%** over exactly 46 sampled frames. A literal \`holdScaleEnd=1550/1520\` would **undershoot the final sampled frame** because the shot's endpoint is *exclusive*. The generalized \`scale_end_for_frames\` compensates for the 46-frame clock, producing first width 1520 and last width 1550. The renderer now supports a bounded \`holdScaleEnd\` (0.90–1.10) and \`enterSeconds=0\` for a real hard cut rather than a synthetic first-two-frame fade. No reference MP4 frame is used in the output video.

## Two genuine recorded products

| Source | Verified before → after | Full source component | Distinct browser source |
| --- | --- | --- | --- |
| Public Resend pricing | Dragged slider changes monthly Pro price $20 → $35; 26 recorded pointer samples | Real complete Pro card at (655,368.797,299,658.313), in frame | 7.68s native Chromium VP9/25fps, verified event clock |
| Public HeroUI Theme Builder | Dashboard hue range 208 → **50** through actual native keyboard input; verified large chart group pixel change **5.31%** at channel difference >20 | Actual two-chart group at (521,348.5,1118,316), measured from rendered iframe DOM | 6.80s native Chromium VP9/25fps, visible loaded dashboard after preflight and real outcome screenshots |

Both authorized public page recordings were trimmed to the same genuine **four-second** study interval and encoded as H.264/1920×1080/30fps. **30fps is a temporal resample from real 25fps source, not native browser 30/60fps.** Each input and capture sidecar is SHA256-pinned independently; project source controls camera and output, never synthesizes the product's state.

## Experiment arms and actual output

- **A — No reference:** verified source video with a static wide camera (product context intact).
- **B — Style description translated manually:** bounded camera push after the observed result; no anticipation of future UI.
- **C — Measured Arcade shape/motion:** genuine post-event, source-frozen component isolated on a neutral stage, sample-clock-corrected 46-frame linear micro-zoom, hard cut. This is a **manual executable reference pair**, not Gemini output. Variant rejected where component shape cannot match.

| Subject | Arm | Encoded MP4 SHA256 | Editorial review |
| --- | --- | --- | --- |
| Resend | A | \`e7ef5a793ad70823e5df886b9e945f87606ecd55e14fc8c1501ccf864358713e\` | FAIL: actual pricing cards very small in wide frame, dark idle space |
| Resend | B | \`1005fa48b27640133dc1aadb2cc9daaf2209e4bf5e4129a813298d9622da3239\` | FAIL: mild focus increase; action/result still too small and unmotivated |
| Resend | C (rejected mismatch kept for negative evidence) | \`1073a7994f840d6c5a2f7c4674b11c90ec0b8f266c70f1950d07a940eac9943f\` | FAIL: narrow vertical card on mostly empty stage, wrong cinematic shape |
| HeroUI | A | \`1287939255990f78bf2f555bd4c87eb67c91050432f6ef496f9d2af94c1b5535\` | FAIL: genuine palette shift, but entire dashboard is too small |
| HeroUI | B | \`1bf094899fb8c65d8f3f77ffd49b4623ed4ae316358c7d8f265ffcdb5535dc78\` | FAIL: camera push improves prominence slightly; no directed clear focal payoff |
| HeroUI | C (geometry-fitted) | \`7d5b310b2d2e272c1666e3d7cc13dc3710004dcc2918f7a9d3ccd8fc0c1e0d8a\` | GEOMETRY PASS / FILM FAIL: focused charts, but dense text too small at 390px, adjacent UI edge fragments and no corresponding posting/cursor narrative |

Source images, all six private MP4s, experimental plans, full decode logs and two contact sheets reside **only in the isolated Vultr workspace** \`sauce-reference-transfer-experiment/.tmp-transfer/\`. No copyrighted third-party film, private customer media or failed renders were publicly deployed or added to Git. The old invalid Resend/C plan and output remain negative-test evidence, but the **generic reproducible generator fails closed** rather than offering that mismatched recipe as an eligible selection.

## 46-frame reference-to-output geometry comparison

A conservative geometry matcher only expands the verified source rectangle into genuinely recorded surrounding pixels. It **does not stretch** the UI, invent extra product interface or silently crop a critical component. For the Arcade aspect ratio 1520/480 ≈3.167:

- Resend complete card aspect ratio 299/658 ≈**0.454**: **REJECT** (irreconcilably tall), even though we retained the earlier deliberately forced bad cut as negative evidence.
- HeroUI two-chart group aspect ratio 1118/316 ≈**3.538**: source-true **26px** symmetric neighboring padding gives a frame-compatible (1170×369) source region. The output JSON starts at exact frame 74/30 and holds through frame 119, with 1520→1550px nominal panel width and mathematically corrected scale.
- **All 46 aligned frames** from Arcade original 1392–1437 and Sauce result 74–119 were independently compared for thresholded reference-panel bounding geometry versus the rendered plan's actual pixel crop rectangle. Mean absolute errors (x,y,width,height) **(0.196, 0.304, 0.609, 0.435) px**; each coordinate's maximum absolute error **1px**. First frame reference (200,300,1520,480) versus Sauce crop (200,301,1520,479); last reference (185,295,1550,489) versus Sauce crop (185,296,1550,489). Exact 30px width change matches.
- This is a **very narrow 2D panel-bbox motion match**, **not** a 1:1 reconstruction of the reference film. Bright-area thresholding isn't a true reference mask. The cursor, content semantics, art direction, shadows, typography, source effects and click/posting state have **not** been matched. The stage contains two HeroUI charts, not one approval button. It cannot be promoted as gold data.

The side-by-side also reveals an important failure even after geometry succeeds: the charts' small axis legends and controls become unreadable at **390px mobile video width**. A perfectly placed UI panel can remain a bad shot when the source density differs. Therefore selection must match **interaction shape + payoff shape + readable source typography + genuine outcome evidence**, not just color, aspect ratio or reference score.

## Reproducibility bug discovered and fixed during the experiment

Existing \`scripts/render_event_video.py\` wrote receipts with \`output.with_suffix(".json")\`. When \`--film-plan /path/take.json\` and \`--output /path/take.mp4\` shared a stem, **the receipt overwrote the executable film plan**. This happened on the first experimental batch. Plans were then **restored from the deterministic original authoring logic**, with A/B reconstructed plan SHA256 values matching the original render receipts exactly. A guard now diverts collision receipts to \`<stem>.receipt.json\` while preserving existing legacy receipt behavior in other cases. Real end-to-end replay proved the input plan's SHA unchanged after output, separate receipt existed, and the result fully decoded. A new fitted HeroUI plan from the reusable reference-transfer generator produced the **same 4-second MP4 byte-for-byte**, SHA256 \`7d5b310b2d2e272c1666e3d7cc3710004dcc2918f7a9d3ccd8fc0c1e0d8a\`.

## Reuse, tests and strict production status

- \`scripts/reference_shot_fit.py\`: measured reference-panel aspect matcher with safe real-pixel padding, fail-closed mismatches, and exact sample-clock scale compensation.
- \`scripts/reference_transfer_ablation.py\`: emits directly executable **sauce-film-plan-v1** variants from source/manifest/hash and an **analysis-only** measured panel track; its output states \`productionGeminiEligible:false\`, never silently creates an ineligible reference arm and never contacts a model.
- \`scripts/render_receipt_paths.py\`: prevents film-plan destruction and includes direct real-media CLI replay proof.
- Existing isolation compositor supports \`holdScaleEnd\` and a zero-duration hard cut with bounded validation, without a new video framework.
- Source evidence still fails closed on an unverified event, missing complete component, future result reveal, off-viewport padding or exaggerated zoom. Video remains authentic browser source.
- Final Phase 2 + URL/live edit + browser geometry tests: **343 passed, 10 skipped, 31 subtests passed**, with the six newly authored ablation tests and source-true isolation/receipt tests; all six four-second film variants fully FFmpeg-decoded.

**No independent blinded judge panel** occurred. No basis exists to rank the three prompt conditions or infer an LLM benchmark. The first real Gemini test requires an approved/no-charge model connection and should use **a reference that has already passed the source-true shot reconstruction AND target-event shape match**. Current Arcade recipe remains research-only and the existing Gemini production gate stays blocked.

**Next bounded creative action:** obtain a real, authorized consequential approval/posting workflow or another matching reference for each target. Rebuild *one* full action→result shot with mobile-readable text and correct pointer state, and independently review its actual MP4. Only then try model A/B/C under equal prompts, fixed source capture, cost budget and a blind reviewer. More unverified reference JSON would be noise.
