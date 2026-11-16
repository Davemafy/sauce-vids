# Sauce — living handoff for new agents and new chats

**Reviewed:** 2026-11-16. This is a checkpoint, not an assertion that the service or GitHub CI is always healthy. Check `origin/main` and current public output before acting. More recent commits and live evidence supersede these notes.

## Read in this order

1. `AGENTS.md` — enforced project behavior.
2. `docs/SAUCE_STANDARDS.md` — source fidelity, creative quality, acceptance checks.
3. This handoff.
4. Relevant latest phase doc and actual source/tests. Use `git status` and compare local HEAD with GitHub `main` **before writing**. Vultr's persistent `sauce-v05-release` working tree can lag GitHub and contains unrelated untracked artifacts. Never overwrite/reset that work blindly.

## Product and engineering architecture

Product: **Sauce**, "A screen recording is not a demo." Film quality, correctness and genuinely human art direction are product differentiators.

Repository: https://github.com/Davemafy/sauce-vids

- Capture: `scripts/session_capture.py` records `sauce.session.v1` browser/DOM events and private pixel states, with bounds and SHA256 verification.
- Deterministic planning: `scripts/studio-motion/src/` TypeScript presets (Clean Studio, 3D Launch, Hyper-Cut), TimeWarp, AutoDirector, CameraRig, kinetic callouts and `FoleyPlan`. `scripts/studio_motion_bridge.py` connects planning to Python.
- MP4 production: Playwright/Chromium, `scripts/session_replay.py`, `scripts/cinematic_stage.py`, `scripts/foley_mixer.py`, FFmpeg; `scripts/produce_cinematic_demo.py` is the production CLI.
- Studio app: Next.js/React under `apps/web/app/studio/` with bounded render API/queue (not an arbitrary untrusted browser agent). The current flow is a fixed catalog, not unlimited consumer uploads.

## Status: what remote main's documentation currently establishes

**Do not pin work to an old SHA.** The public `main` HEAD was verified on 2026-11-16 before this documentation update as `01a2801149154e77a0df064820425398afc145d1`; subsequent commits supersede it. At the beginning of each new chat, query the current GitHub `main` and compare it to the persistent worker's `git status`/HEAD. The remote documentation is the reference until the actual working code and deployed film are inspected.

- **Phase 1 completed:** strict TypeScript preset contracts, deterministic director/camera/Foley plan and tests. `docs/sauce-motion-phase1.md`.
- **Phase 2 completed as bounded technical proof:** real 3D Launch Brimble H.264/60fps output with 48kHz AAC Foley, procedural WAV/OGG fallback, active-region spotlight and 1px projected rim, redacted copy/paste/submit trace events. `docs/sauce-motion-phase2.md`. This is not autonomous launch-film parity.
- **Phase 3 completed as a bounded Studio UI:** selectable recording from **Brimble** and **Sauce** fixtures, three presets, Foley toggle, job queue, secure origin handling and preview/master download. `docs/sauce-studio-phase3.md`. Does **not** accept arbitrary per-user uploads or claim general authenticated workflows.

### Grounded public reference links (verify before repeating their status)

- Studio: https://devmcp.davemafy.xyz/sauce-app/studio
- Landing: https://devmcp.davemafy.xyz/sauce-app
- Phase 2 3D Launch proof: https://devmcp.davemafy.xyz/sauce-motion-phase2/
- Independently re-rendered Phase 2 proof: https://devmcp.davemafy.xyz/sauce-motion-phase2-verified/
- Earlier silent time-warp proof: https://devmcp.davemafy.xyz/sauce-studio-v21/
- Screen Studio camera reference study: `docs/screenstudio-study.md`.

## Active next focus: Phase 2 quality hardening (requested 2026-11-16)

**The user's current working phase is Phase 2.** Interpret this as improving and proving the *visual and editorial quality* of the already-functioning Phase 2 3D Launch engine. Do **not** reset the roadmap or delete/reimplement completed Phase 2 code. The repository also contains a later *bounded* Phase 3 Studio UI; that historical release does not turn Sauce into a finished, general-purpose premium demo product.

For every new-chat handoff: start at [docs/SAUCE_NEW_CHAT.md](SAUCE_NEW_CHAT.md), then re-read `docs/SAUCE_STANDARDS.md` and the actual code. Treat the older "Phase 3 boundary" in `docs/sauce-motion-phase2.md` as historical; `docs/sauce-studio-phase3.md` records the subsequent limited UI implementation.

**Immediate quality loop (not yet a product sign-off):**

1. Inspect current Phase 2 master and release receipt; extract actual 1080p frames for the opening, cursor approach, contact, modal spotlight, callout, and final hold. Compare the film with concrete Screen Studio/reference frames at normal playback size.
2. List the remaining visual defects with frame timestamps before making edits. Use real product actions; keep 16:9 landscape, readable UI, rounded correctly-sized visible pointer, action-caused camera movement, proportionate typography, restrained spatial effects.
3. Where needed, refine the *actual compositing/render path* in `scripts/session_replay.py`, `scripts/cinematic_stage.py`, `scripts/studio_motion_callouts.py`, `scripts/foley_mixer.py`, and the TS planner. Do not hide weak footage behind player CSS.
4. Repeat the existing Phase 2 gates: source-state hashes, semantic + pixel checks, 1920×1080/60fps H.264, actual 48kHz AAC Foley alignment within one frame, verified mute, complete FFmpeg decode, desktop/mobile playback and privacy of HAR/screenshots.
5. Mark an output **technically passed / visually not yet accepted** until the actual exported film meets the referenced quality bar. Record the published URL, frame evidence, defects still present and current `main` commit in this handoff.

**Proofs verified as reachable on 2026-11-16:** `/sauce-motion-phase2/`, `/sauce-motion-phase2-verified/`, and `/sauce-app/studio` returned HTTP 200. HTTP 200 alone is **not** an up-to-date verification of rendered content quality or CI.

## What is *not* finished

- No proof of consistent Screen Studio/Linear/Apple-level creative quality on arbitrary user recordings.
- No public, secure, authenticated, arbitrary recording upload workflow; need tenant isolation, quotas, malware checks, storage retention and privacy controls.
- No guaranteed intelligent editor for long 30–90s narrated film across diverse SaaS websites.
- A short proof, even if deterministic, must never be marketed as a complete product launch film.
- Product-quality visual signoff still requires contact sheets and manual viewing at actual playback size.

## Next work protocol

1. Identify the **specific user request**, then inspect matching source/release; don't restart infrastructure or revive retired approaches.
2. Inspect actual screenshots and MP4. Bring reference frames into the review, and document observed defects before designing a solution.
3. Make the smallest coherent architecture change within current main, preserving browser functionality and privacy.
4. Run tests targeted to the change:
   - `cd scripts/studio-motion && npm ci && npm test`
   - `python3 -m unittest discover -s tests -q`
   - `../.sauce-render-env/bin/python -m pytest tests/phase2/test_sauce_motion_phase2.py -q` (worker environment only)
   - `cd apps/web && npm run build && npm run test && npm run test:e2e` (supported environment and configured service required)
   - `ffprobe`, full FFmpeg decode, real Playwright playback and relevant screenshot inspection.
5. Always update this handoff with **actual commit hash, test evidence, published proof URL and creative gaps**. Do not replace everything with an unsupported "done" report.

## New-chat starter prompt

Use the shorter, copy-ready prompt and ChatGPT Project instructions in [docs/SAUCE_NEW_CHAT.md](SAUCE_NEW_CHAT.md). This existing starter is retained as a fallback.

> Continue Sauce in https://github.com/Davemafy/sauce-vids, **main only**. Connect GitHub and the existing persistent Vultr DevMCP worker. Read `AGENTS.md`, `docs/SAUCE_STANDARDS.md`, and `docs/SAUCE_HANDOFF.md` first; compare local state to current GitHub `main`, then inspect the current production output. Apply the same evidence-first cinematic quality bar. Preserve all existing work and do not confuse a passing test suite with a premium film. My next request is: [insert task].

If there is no working DevMCP connection in a new chat, first reconnect it rather than inventing execution results.
