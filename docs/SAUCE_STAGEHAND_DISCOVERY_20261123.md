# Stagehand v4 read-only discovery experiment — 2026-11-23

**Status:** Opt-in adapter connected to the Sauce URL direction path. Not enabled in running Studio and not a production/demo-quality approval. Main only; no existing renderer, Foley, capture, cursor, camera or cloud-stage output changed.

## Implementation

- scripts/stagehand_public_discovery.py: Stagehand v4 read-only scout. Opens the already-authorized public site and calls observe once. Never calls act, clicks, fills, submits or navigates to AI-suggested links.
- backend/stagehand_discovery.py: Bounded subprocess only when SAUCE_STAGEHAND_DISCOVERY=1. AI descriptions may select a control only when its complete label uniquely matches a separately observed and allowlisted Sauce report.control. AI selectors, coordinates, URLs and result claims are discarded. Otherwise the current director remains in control.
- backend/url_engine.py: After the existing independent inspect step, opt-in Stagehand suggestions can propose one aN control ID. A proposal always goes through the existing real-browser visible-action probe before recording, even without SAUCE_VERIFY_VISIBLE_ACTION. Unverified results are downgraded to showcase or rejected in cinematic-only mode.
- scripts/requirements-stagehand.txt pins Python Stagehand 4.4.0 separately; the default production path imports no Stagehand dependency. Secrets are environment-only.

## Live proof

GitHub starting main: 7ada57f457f7a93b9d2839bd3738a8fe266192e7. Isolated clean local checkout used; existing dirty Cloud Hi-Fi experiments preserved.

Stagehand 4.4.0 installed in a separate Vultr Python virtualenv. The separate scout browser applies a fail-closed Stagehand domain allowlist to the inspected first-party hostname before navigation; third-party CDNs may be unavailable and no browser profile/cookies are reused. It launched real local Chromium, visited https://example.com/, returned SDK browser_ready status and closed without error. Three different public sites independently inspected through Sauce and opened through Stagehand:
- https://animista.net/: 35 controls and 2 headings, Stagehand browser PASS
- https://cssgradient.io/: 31 controls and 15 headings, Stagehand browser PASS
- https://neumorphism.io/: 1 control and 7 headings, Stagehand browser PASS

New unit cases test exact-match allowlisting, ignored model selectors, wrong URL/schema, ambiguous or unsafe controls, no-credentials fallback, private metadata receipts and the URL pipeline rejecting an unverified Stagehand-selected click. Existing legacy and Phase 2 suites were run after changes; see living handoff for final counts.

Existing encoded baseline opened and six-frame contact inspected: sauce-cloud-stage-20261123/.tmp-cloud-stage/cloud-beat-6s.mp4, 6.333 seconds, 1920x1080/60 H.264 and AAC. Cobalt cloud stage is visible; the source UI remains small and dark, result matrix is dense, payoff weak. **No new film was produced by this change; 0 premium creative approvals.**

## How to run (on existing worker only)

Install isolated dependency: python3 -m venv ../.sauce-stagehand-venv; ../.sauce-stagehand-venv/bin/python -m pip install -r scripts/requirements-stagehand.txt

Set SAUCE_STAGEHAND_DISCOVERY=1 and SAUCE_STAGEHAND_PYTHON to the absolute path of the isolated Python. Provide an existing GEMINI_API_KEY or GOOGLE_GENERATIVE_AI_API_KEY to make AI observe work. Optional SAUCE_STAGEHAND_BROWSER=browserbase and BROWSERBASE_API_KEY use the existing Browserbase service. Then invoke the unchanged URL job pipeline; the opt-in scout runs before source capture. No new app controls were exposed.

## Limitations / next proof

The authenticated Vultr worker process currently exposes **no Gemini or Browserbase key**. Therefore AI Stagehand observe DID NOT RUN; there is no observed model ranking or new Stagehand-led MP4. All three public-site tests were real browser/SDK smoke, not AI discovery. The end-to-end pipeline guard is mock-tested only. With an existing inference credential, next run should actually observe three real products, choose verified interactions, render source-true 1080p/60 MP4, inspect frames and reject unsaleable films. Do not confuse this SDK integration with a full autonomous agent, production deployment, or approved film.

No new VM, branch, paid service signup, sign-in to third-party sites, user content publication, or secret/media commit.
