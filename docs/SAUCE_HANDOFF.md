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

## Verified 2026-11-16 Phase 2 extension: H0/H60 planes and beat-locked edit

**Preservation:** GitHub main began at 6fcd4fafceb02973da4bcbba91fdb4e1fed54d5a. Before editing, the existing Vultr release checkout at 5e32cde36e7759a1ad6f1beb2f864d75a02c694a had 44 untracked motion files backed up to ../sauce-phase2-backups/snapshot-2026-11-16-pre-zparallax/ (archive SHA-256: 755fe536f2343df6a1903ebd6821571d3181ff50cce257347a1b4c2c290338a6). Its working tree and original published Phase 2 proofs remain untouched.

**Commit 1 on main:** a87b8051dbace61a2be64da52c42314d23790028. The existing 1200px H0 projection is preserved and H60 adds a verified z=+60px plane. Chromium replay temporarily hides a geometry-matched live dialog for the background pass, restores the element even after capture failure, then composites authentic modal pixels above the blurred background. If no clean plate is available, the original Phase 2 single-plane spotlight remains the fallback. The luminous 1px rim and plane-aware vector pointer are retained.

**Beat-lock implementation in the accompanying main commit:** 3d-launch now uses executed source-true edit decisions, with hard cuts on actual hero-action frames, never speculative pre-action zooms. The existing 180 / 24 / 1 spring constants remain unchanged. Foley is remapped onto the same 60fps / 48kHz timeline at 800 samples/frame. Modal owner IDs remain stable through nested child clicks, up to the explicit 2400ms ownership window or an earlier recorded close.

**Verified public film:** https://devmcp.davemafy.xyz/sauce-motion-phase2/z60-beats/ ; master: https://devmcp.davemafy.xyz/sauce-motion-phase2/z60-beats/master-1080p60.mp4 . Master SHA-256: 35ef68e22c842eb28cb90ccda92a3961af770ed6352c716c609693648fa2a48c. This is a new proof directory under the existing Nginx alias, not a replacement of either original Phase 2 URL.

**Technical evidence:** H.264 1920×1080, 60fps, 197 frames, 3.283333s, AAC stereo 48000Hz; 2× source DPR; six SHA-verified source states; three semantic and three pixel-region checks. There were 134 spotlight frames, 120 true elevated-modal frames and zero attempted multi-plane fallbacks. The source-true cut at output frame 125 creates shots of 125 and 72 frames (2.083s and 1.200s), both below the strict 150-frame maximum. All seven Foley cues land on exact 800-sample boundaries. Decoded AAC versus reference WAV correlation measured 0-sample lag for clicks before and after the cut (output samples 38400 and 100000). The PCM is 157,600 samples; decoded AAC contains 96 end-padding samples, not a timing shift. FFmpeg decoded the complete film without error.

**Tests and visual QA:** TypeScript 25/25; Python unittest 160/160; SAUCE_BROWSER_TEST=1 pytest 17/17 using the preserved Brimble fixture and encoded baseline without altering either. Inspected the actual 12-frame montage and full-resolution frame 125, including before/after-cut geometry, legibility, pointer and shadows. Live HTML and master returned HTTP 200. Playwright sought the real video at desktop 1280×720 and mobile 390×844 with no browser errors, video error or horizontal overflow. Public output includes only the player, preview, poster, master and non-private receipt.

**Creative acceptance: not yet a finished premium film.** This is a technically sound 3.28-second Brimble example, not a 30–90-second directed product film or evidence that arbitrary websites are handled well. Minor original-source secondary text remains low contrast, and long-running modal closes/reopens, longer shot arcs and different source applications remain to be evaluated against real reference footage. Preserve this quality floor; do not call tests alone premium film approval.

## 2026-11-16: Surgical Phase 2 "Connect Agent" oval fix

**Cause:** inspected original native frame 75; the white horseshoe inside the floating dark callout pill came from ImageDraw.arc() and a separate top highlight line in scripts/studio_motion_callouts.py. Removed only those two strokes, preserving its rounded border, text, leader, camera and source UI. Backup of original code: ../sauce-phase2-backups/oval-callout-2026-11-16/studio_motion_callouts.py.before.

**Evidence:** the new native-pixel test in tests/phase3/test_sauce_studio_phase3.py asserts the retained rim and dark top interior. Reran TypeScript 25/25, Python unittest 160/160 and Phase 2+3 pytest 23/23. The rerender uses the same six SHA-verified Brimble states: H.264 1920x1080@60, AAC 48kHz, 197 frames / 3.283333s, 120 true modal-plane frames, zero fallback, cut frame 125. Frame 75 before/after was opened at 100% in callout-before-after-100pct.png; original and fixed AAC elementary streams are MD5-identical (a9d78a5821d4592d3af3210deb53f8ad). Full video decoded. Other replay pixels can differ slightly due to actual Chromium rerender; mean absolute outside a generous pill region is 0.155/255.

**Corrected film:** https://devmcp.davemafy.xyz/sauce-motion-phase2/z60-beats-oval-clean/ ; master SHA-256 2cc54b2935dac405ec2c53185d454703c2742bd12434c53ec4051438ea830771. Original z60-beats URL preserved and not overwritten.

## 2026-11-16: Brimble Phase 2 final visual correction and verified 3.28s release

**Release:** https://devmcp.davemafy.xyz/sauce-motion-phase2/codex-clean-final/ ; master https://devmcp.davemafy.xyz/sauce-motion-phase2/codex-clean-final/master-1080p60.mp4 . Verified master SHA-256: `37ee66b27627c1e663897be6d9ff96d5a0f81792aaa63b482b8d6d05e0549fe7`. The earlier `z60-beats-oval-clean` proof remains published and unchanged.

**Visual inspection, including a defect caught during the final QA:** sampled 21 real master frames from 0.00 to 3.27 seconds; checked native-resolution frames 114 (Codex), 125 (action cut), 170/175/180 (copied-command transition), 190 and 196 (ending). The black terminal was initially concealed only during foreground ownership; at frames 170–183 the feature spotlight dropped modal ownership and exposed the dark panel. Fixed `session_replay.py` to honor the still-visible Chromium dialog even while a copy-confirmation feature spotlight is active. The dark 440x380px inspection area had roughly 103,000 near-black pixels during the faulty frames and at most 108 near-black pixels across corrected frames 170–183. Also suppresses an unrelated generated code-diff peel while Brimble's real dialog is open, retaining the source-true copied command. This exception is specific to the verified Brimble session; the general code-diff pipeline stays available.

**Other corrections:** `modal_depth_capture.py` hides only the geometry- and CSS-verified dark Brimble terminal in the true modal-free background pass, restoring its exact original DOM style in `finally`. `cinematic_stage.py` offsets only the *drawn cursor glyph* away from the measured Codex text range, leaving click/ripple coordinates unchanged. `cameraRig.ts` keeps the approved 180/24/1 spring parameters and 1200px perspective while leveling the opening and holding one restrained modal angle rather than oscillating with pointer velocity. No renderer rebuild and no source-media substitution.

**Engineering gates:** Full H.264 video decode passed. ffprobe: 1920x1080 at 60fps, 197 frames, 3.283333s, AAC at 48000 Hz. Receipt: six source-verified states, 152 elevated-modal frames, 37 live-modal hold frames, 152 actual terminal-concealment frames, zero multi-plane fallbacks, and the original action-aligned cut at output frame 125. Passed TypeScript 26/26, Python unittest 160/160, and Phase 2/3 pytest 24/24. Public new page, master and prior proof returned HTTP 200. The QA contact sheet and key native frames are retained in the release's directory; previous release is not overwritten. This film meets this narrow defect-remediation gate, not a general premium film certification.
