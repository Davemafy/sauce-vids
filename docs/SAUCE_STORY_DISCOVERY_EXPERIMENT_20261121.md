# Sauce — grounded product-story director experiment (2026-11-21)

**Verdict: research/story selection improved; premium film gate still FAIL.**
Isolated clean `main` checkout on the existing persistent Vultr worker. No new VM, branch, account sign-in, paid purchase, public video publication, or mutation of a target product. Gemini inference consumed the owner's previously authorized experimental credential. All source images, HAR, private traces and MP4s remain private.

## Hypothesis and test

A director should first understand a product from public DOM text, screenshots and source-labelled evidence, then plan a useful demonstration. It must *see* risky actions without receiving authority to *execute* them. A site claim or mock terminal is never proof of a live product action.

Existing `backend/product_explorer.py` silently excluded Refit's “Run refund agent” button because the generic unsafe-label filter included `refund`; thus the existing one-page URL director could not pick Refit's strongest real action. Preserve that execution restriction. New **opt-in** `backend/story_discovery.py` separately inventories controls with explicit read-only, reversible, costly/nondeterministic, sensitive/destructive, external and unknown classes. Read-only research only navigates already observed same-origin public links (max 4 pages); it clicks **zero** buttons. Any proposed risky action remains `proposed_only`. An observed page element ID and verbatim observed quote are required for each storyboard beat. Claim status remains `site_claim_not_independently_verified`.

`scripts/experiment_story_discovery.py` is an operator-side diagnostic, **not wired to self-serve URL production**. One bounded Gemini 3.1 Flash Lite request (max 2400 response tokens, 58-second network timeout) receives compact observed text/control IDs and optional source screenshots; no custom browser tools or privileged requests are exposed to the model. Browser redirects, cross-origin navigation and unsafe paths are blocked; source text is treated as untrusted data. Outputs cannot authorize any action or cinematic export. No automatic narration is admitted from the unverified free-form storyboard.

### Actual model experiments (one model request per successful row)

| Source | Observation | Gemini result | Tokens |
| --- | --- | --- | ---: |
| Refit initial director | 4 real public pages incl. workspace/evidence | **FAIL**: chose generic Import your agent as the main action | 7,331 |
| Refit outcome-first direction | Same source evidence | Selected real Run refund agent, but missed numeric proof in the hook | 7,528 |
| Refit evidence-signalled direction | Same site, compact complete JSON packet, numeric snippets derived from DOM | **Story-candidate PASS**: selected published 24/24 → 13/24 → 24/24 hook, proposed Run refund agent (NOT executed), used Evidence as proof, preserved historical/live distinction | 6,869 |
| Brimble text-only | Public homepage | **Creative FAIL**: described a marketing mock CLI terminal as though it were the real product demo; no observed browser action selected | 4,056 |
| HeroUI themes text-only | Public theme-builder page with overlay | No observed action selected; source landing insufficient for genuine demonstration | 1,683 |
| Brimble text + screenshot | Same source | **Creative FAIL**: still preferred a static mock CLI sequence; output remains explicitly showcase-only | 5,178 |
| HeroUI themes visual retry | Source intermittently inaccessible under browser route restrictions; later public read-only retry found 25 controls | No further Gemini request counted; no action or film approved | 0 |

**Total measured usage:** 6 Gemini 3.1 Flash Lite requests, 32,645 total tokens. Provider billing charge was not independently retrieved; do not invent a USD cost. Research uses live page text, not Google indexing. Refit quantitative values are **site-published historical results**, not measurements from these experiments. The Refit live refund action was never triggered.

### Real Refit capture and encoded videos

1. **Recorded-evidence walkthrough:** read-only recorded Evidence → existing synthetic classification migration → Trace → Evidence. 30 browser events, 8 Chromium screenshot states, 1280×720 CSS viewport at DPR2. Initially a genuine replay was falsely rejected: a hover semantic assertion was evaluated **after** the next click had navigated away, when both source events landed within the same output frame. `scripts/session_replay.py` now verifies completed earlier actions immediately *before* the following action. Previously failing source replay and new regression passed.
   - Actual MP4: `./.tmp-director-refit/encoded-verified-sequence/master-1080p60.mp4` in isolated worker checkout.
   - H.264, 1920×1080, 60fps, **360 frames, 6.000s**, full FFmpeg decode pass.
   - **Creative FAIL** after opening eight actual frames: initial tiny evidence list dominates; important text unreadable at phone scale; final payoff is undersized and stage margins waste visual area. Not publicly hosted.
2. **Published-number hook:** real browser anchor click from Refit landing hero to the visible recorded comparison. 39 browser events and 5 source states; numbers genuinely visible after click. No fabricated result.
   - Actual MP4: `./.tmp-director-refit/metric-hook-render/master-1080p60.mp4` in isolated worker checkout.
   - H.264, 1920×1080, 60fps, **125 frames, 2.0833s**, full FFmpeg decode pass.
   - **More relevant editorial source**, but still **creative FAIL**: too short, too much empty stage, no decisive post-action close-up or sufficient reading hold. Historical result label still required on distribution.

QA montages, privately held on worker:
- `./.tmp-director-refit/qa-contact.jpg` (8 actual Refit recorded-evidence frames)
- `./.tmp-director-refit/qa-metric-contact.jpg` (6 actual Refit metric-hook frames)
- `./.tmp-director-refit/research-montage.jpg` (live Refit and HeroUI screenshots)

The video issue is **not solved** by passing source or replay tests. Compared with the retained Screen Studio study, the result lacks decisive action-following pushes, source-focused readability and a satisfying outcome hold. Do not ingest these diagnostic films as verified premium references.

### Tests and boundaries

- `pytest tests/test_replay_semantic_order.py tests/test_story_discovery.py tests/test_session_contract.py tests/phase2/test_sauce_motion_phase2.py -q`: **28 passed, 3 skipped, 3 subtests passed**.
- Source-true Refit capture + encoded replay verified independently of unit tests. No unauthorized requests, downloads, exports or live inferred outcomes occurred.
- Refit `Run refund agent` remains blocked pending **specific authorization plus a one-shot recording budget**. The new director reports `requires_explicitly_authorized_action_capture`, and makes no claim that two-pass replay is reliable for nondeterministic/costly actions.
- Held-out Brimble output is classified `public_site_showcase_only_not_a_product_demo`: observed terminal examples cannot become narrated proof merely because the model described them.
- Current flagship is still landscape 1920×1080/60; no portrait/Shorts default, no music, and no fake success.

## Next controlled milestone

**Do not start another generalized agent framework.** For one owned/authorized product, select the actual high-payoff action, record it once when costly, preserve the recorded/live provenance, then direct the first 3–5 encoded seconds using measured **source-result geometry**, not just a CSS stage or a camera following the cursor. Require mobile readability, preserved evidence, clear causal pointer interaction and an independently reviewed opening before rendering a longer commercial cut. Compare existing rule-based cinema with Gemini-authored camera decisions *only after* the storytelling source passes.

Retain the original production engine, rejected clips and reference QA artifacts. No premium film or self-serve deployment is approved by this experiment.
