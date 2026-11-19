# Sauce Phase 2 — cinematic URL admission must precede capture

Date: **2026-11-19**. Status: **source-first control proven on two live public product URLs; 10/10 film acceptance still FAILED**. This is a narrow opt-in URL orchestration fix, not a creative sign-off or production deployment.

## Root cause

The existing `backend/url_engine.py` selected simple available controls (slider, known dialog, tab) before proving product value, and `SAUCE_VERIFY_VISIBLE_ACTION` was optional. When a chosen action failed, the system was allowed to downgrade to a public-page showcase and still produce a video. This is a sensible baseline-preview fallback, but directly conflicts with a premium-film promise.

Independently testing the actual Brimble public modal exposed a second problem: `Playwright.locator.click()` scrolls its control into the viewport. Comparing a screenshot taken at the top of a page against a screenshot taken at the button confounds scrolling with product change. Before fixing viewport alignment the probe called **88.664% of the viewport changed** a successful action. With the viewport aligned, raw change still measured **80.571%** because the genuine dialog dimmed the whole page. That is not 80% new feature content.

## Bounded changes (explicit cinematic mode only)

- In `backend/url_engine.py`, `SAUCE_CINEMATIC_ONLY=1` now always performs a safe independent public action probe, regardless of the optional `SAUCE_VERIFY_VISIBLE_ACTION` setting. A showcase, unverified chosen control, stale/mismatched source receipt, bad capture, or missing real action **fails closed** instead of becoming a generic promotional MP4. Default/basic-preview behavior remains as before.
- `require_cinematic_story_proof()` verifies real one-control interaction, source URL/control ID and screenshot SHA256 receipt, stable camera viewport and meaningful visual-change evidence. The candidate must exceed **3.5% source-frame changed pixels**, have a **browser-observed real result region** covering at least **5.5% of viewport**, and have at least **7.5% changed pixels inside that genuine result**, reusing Sauce's existing conservative silent-hero source-triage thresholds. The rule cannot certify artistic taste; it also deliberately cannot verify arbitrary freehand/drag gestures using a click-only probe.
- In `backend/source_action_preflight.py`, physically scroll the real control into view **before baseline screenshots**, wait for stabilization, and compare source window coordinates and target element position before/after action. If the viewport itself moves over 4px, mark the evidence `viewport_shift_ambiguous` rather than use the frame-wide delta as payoff.
- `visible_result_box()` reads a real visible `role=dialog`, HTML dialog, tabpanel or observed `aria-controls` panel rectangle *after the real click*. `measured_result_region()` measures the actual source pixel change within that DOM result. A full-screen dimming backdrop or CSS animation without a demonstrable semantic result node never qualifies a premium silent UI film. Sensitive form clicks and private routes remain prohibited by the existing product explorer/capture safety.
- The pipeline's user-facing `capturing` stage begins **after** the source-proof checks, not before them.

**This is pre-capture film-admission triage, not an automated 3-second cinematic critic.** A passing proof means `short opening candidate can be studied`, never `saleable film approved`. The opt-in flag has not been wired to the public SaaS UI or deployed to production. The source checks require a semantic panel; valuable interactions lacking one need a separate source-truth receipt/verification route, not a fabricated panel or disabled gate.

## Real-browser evidence

Actual public, anonymous sites checked on the existing persistent Vultr DevMCP worker using the isolated `sauce-director-admission-1119` main checkout. `GEMINI_API_KEY=''` avoided any inference request. All raw browser screenshots and control traces remain private in the worker.

| Real site | Chosen original control | Outcome |
| --- | --- | --- |
| `https://resend.com/pricing` | Real public slider; current independent probe only supports non-submitting safe clicks, not native drag proof | **REJECT** in **3.8s**, `unsupported_action_requires_separate_verification`; **zero native capture videos and zero rendered MP4s** in the job folder |
| `https://www.brimble.io/` | Real `Connect your agent` button, original observed source control `a1` | **SHORT OPENING CANDIDATE only**. Genuine **400×360** browser dialog, **15.625% of 1280×720 viewport**, **39.177%** visual changes *inside dialog*, zero viewport shift; raw frame-wide backdrop/dim amount **80.571%** explicitly not mistaken for meaningful feature area |

The underlying Brimble screenshots before/steady/after were opened for visual inspection. The real modal contains agent-connection setup options and is a browser-visible product state. This **does not approve** the existing short Brimble launch cut or claim authenticated integration.

## Regression verification

- Focused `tests/test_cinematic_story_admission.py` and existing `tests/test_source_action_preflight.py`: **21 passed, 15 subtests**. Includes unsupported button/slider or wrong URL, spoofed/missing source hashes, tiny DOM-only deltas, full-screen backdrop with tiny result, nested scroll, missing viewport timestamps, no-showcase fallback, missing selector, and forced probe when `SAUCE_VERIFY_VISIBLE_ACTION=0`.
- Phase 2 + Phase 3 + source-action/API admission tests: **242 passed, 11 skipped, 25 subtests**.
- Legacy `python -m unittest discover -s tests -q`: **239 run, 2 skipped**. No TypeScript subsystem modified.
- `git diff --check` clean, original cinematic compositor/Brimble/Linear/Resend films untouched.

## Next creative task and stop-loss

The work above **eliminates one class of false positive**; it cannot manufacture a good film. The independent coordinator remains correct that films need a **visually meaningful product story before camera engineering**. A separate director study on current main tested HeroUI's real Theme Builder (blue→orange Dashboard), but a storyboard alone does not grant commercial source rights or guarantee good moving footage. Obtain suitable rights/authorization or use an owned app, direct a visible native 2–3-second opening and critique its **actual encoded 60fps footage**, then only continue the approved scene into a 15s film and reusable automation.

**Current acceptances:** premium film **FAIL**; arbitrary URL→excellent 900-frame film **NOT demonstrated**. Do not advertise this gate as 10/10.
