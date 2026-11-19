# Sauce source-outcome preflight and three-second creative rejection

Date: 2026-11-19. Status: ENGINEERING CHECK VERIFIED; PREMIUM FILM STILL REJECTED.

## What changed in our assessment

Passing a source-level optical test does not mean the action communicates product value. The owner rejected the Linear and OpenSheets exports because the resulting films had no compelling opening, no clear causality and no satisfying visual payoff. In response, we added a pre-render visual admission gate on main; OpenSheets was correctly rejected before any new full video. Its real currency-formatting result occupied only 1.045% of its native source screen and changed 0.109% of sampled full-frame pixels.

### Another distinct real source: graph editor

A locally run React Node Editor checkout (source commit b6990631eee04c4b6200dd82e839464a85f35bda, Mario Tavarez; README claims MIT but the checkout has no root license file) was browser tested at physical 3200×1800 DPR2. A real browser drag moved the existing "Check User Role" condition node from CSS x854.7/y389.6 to x750.7/y227.6 while all six real edges remained present. No fake application state was created. Continuous X11/Chromium source: 350 frames at 60fps, source SHA256 fc5f22fc4447ef28f1619387b222f208e0e4e1bd284479856c7a427d353f68e5.

Real private before/after browser screenshots passed the numerical first-three-second admission: result union 6.606% of frame, 3.635% of whole-frame pixels visibly changed, 41.037% of the measured result region changed.

We used 180 consecutive verified source frames (native frame indices 85–264 inclusive), one physical source crop x610/y306/w1920/h1080, exact transformed source timestamps and geometry, and the EXISTING Sauce render_event_video.py pipeline. The output is H.264 1920×1080/60fps, 180 frames/3.0 seconds, SHA256 1cd2cb5b353965081c96382a93c72de000e5257567ead1863d3bccf28571f616; error-on-error FFmpeg full decode passed. No synthetic UI, fake click, remade product, external asset or unauthorized inference. The browser before/after and raw X11 capture remain private.

**[Actual three-second REJECTED QA playback](https://devmcp.davemafy.xyz/sauce-motion-phase2/graph-source-gate-20261119/)**; real HTTPS/player seek worked at 390×844 and 1280×720 with no video/JS error or overflow. Only the review HTML, resulting MP4 and poster were published.

**Independent creative verdict: FAIL.** The colored cards move and their connectors follow, but the film does not convey an important product result. First-frame hierarchy is weak, labels are too small at phone-feed width and the cursor lacks presence. Optical change is NOT meaningful story. No longer render was started. This is not a flagship or a passing film.

## Actual URL pipeline gap fixed (opt-in)

Before this change, backend/product_explorer.preflight() verified that chosen public controls existed. It did not verify that their actions changed anything. The full URL pipeline could record/render a harmless but non-demonstrative action and market it as an interactive demo.

New backend/source_action_preflight.py performs a bounded one-action preflight using the existing public URL safety checks and preapproved control identity. In a disposable Playwright browser it records the genuine before, no-action ambient baseline, and after-action screenshots, plus hashes of visible content/ARIA state, dialog count and path. The result distinguishes ambient motion from action-linked visible changes; no source text or screenshots appear in public receipts. It is an objective action outcome, NOT a judge of premium direction, product value or legal rights.

Opt-in use:
- SAUCE_VERIFY_VISIBLE_ACTION=1 allows a verified real visible interaction; otherwise downgrades honestly to a public-site showcase rather than claiming a working feature demo.
- SAUCE_VERIFY_VISIBLE_ACTION=1 together with SAUCE_CINEMATIC_ONLY=1 stops the cinematic job BEFORE capture/encode when no action outcome is verified.

Real public test against an explicitly vetted and reversible "Connect your agent" control at https://www.brimble.io/ gave baseline 1.564%, post-action change 89.019%, baseline-adjusted change 86.986% and a genuine observed DOM change. Status is visible_outcome_candidate, human_film_approval false. This is not evidence of film beauty.

Tests: 7 new source-action tests; 15 combined new+explorer tests; Python Phase 2 182 passed, 10 skipped; legacy unittest 215 passed, 1 skipped. TypeScript engine unchanged. All three existing Sauce production services stayed active. No paid inference, new VM, default production config change, external submission or user-facing deploy.

## Constraints and next real gate

The first three seconds need a dominant visually legible subject, a recorded action, and an unmistakable benefit to the viewer. A large pixel delta alone is insufficient; equally, a small pixel delta can support a great narrated/instructional demo. Do not convert this narrow triage into a universal veto.

Do not promote any of the currently rejected clips to launch proof. Choose a real, authorized, intrinsically meaningful workflow; critique actual first-three-second encoded pixels at 1080p and 390px alongside Screen Studio and other real references BEFORE longer rendering. Stop after two failed creative candidates rather than patching shaders into an unfilmable interaction. Sauce still needs three distinct independent premium approvals for launch.
