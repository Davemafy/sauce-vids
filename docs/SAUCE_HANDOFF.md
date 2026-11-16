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

## 2026-11-16: Retain modal camera framing through nested Codex click

**Problem in previous approved 3.28s Brimble film:** At output frame 125 the AutoDirector made a source-true cut on the Codex child click, but CameraRig simultaneously retargeted from the whole dialog to the child span. The spring was snapped across the cut from `scale=1.31, focus=(640,362.59)` to `scale=1.19, focus=(614,461)`. At native resolution the modal's white bbox went from `(641,249,638,573)` on frame 114 to `(709,121,578,670)` on frame 125, so a legitimate growth looked like a disappearing/reappearing narrower modal.

**Surgical fix:** `scripts/studio-motion/src/cameraRig.ts` now retains the most recent unclosed dialog as the camera hero during the dialog itself and any *geometrically contained* child action. This holds zoom, X/Y focus and the restrained 3D angle even at the frame-125 hard cut, and continues through a source-backed result hold while the dialog remains open. An observed dialog-close releases the lock. Unrelated nonspatial feature-commit beats retain their own camera motion. No changes to the real Chromium UI, DOM contents, multi-plane composite, frozen 180/24/1 spring constants, 1200px perspective, overlay/cursor, or cut/clock code. TypeScript compiled JS and two focused behavior/close tests are checked in.

**Actual rerender and comparison:** Same six SHA-verified Brimble states, same 197-frame 1920x1080 60fps film, H.264 and AAC 48kHz, 3.283333s, same frame-125 action cut. Pixel-detected white modal rectangles: frame 114 `(641,249,638,573)`, frame 125 `(641,167,638,738)`, frame 130 `(641,157,638,760)`, frame 190 `(641,158,638,757)`. Crucially, modal X and displayed width **do not change** across the selection. The *top moves upward and height increases* because the genuine Brimble dialog expands around its centered source layout; Sauce does not fabricate or move UI content. Native bottom margin remains visible, no clipping. Full 18-frame contact sheet and old-vs-new before/after comparison visually inspected. Entire video decoded with FFmpeg. Source verification: six states, 3 semantic and 3 pixel-region checks, 152 real multi-plane frames, zero fallback, 152 terminal-concealed frames. The camera planner preserved its cut at frame 125. The audio remained 48kHz with 157,600 samples but contains four cues instead of five because a now-unnecessary camera whoosh disappeared; do not claim identical AAC bytes.

**Tests:** Studio Motion 28/28 passing, Python unittest 160/160, Phase 2/3 pytest with browser 24/24. Older rendered proofs, the untracked backup of pre-fix cameraRig.ts, and original persistent Vultr checkout remain untouched.

**New proof:** https://devmcp.davemafy.xyz/sauce-motion-phase2/modal-camera-locked/ (MP4 `master-1080p60.mp4`, SHA-256 `87db86fd67f311dc54a2b48ba91347c0d686165e725a66baf75afea068502d6f`). The earlier `codex-clean-final` proof is retained independently.

## 2026-11-16: Pryzm-inspired procedural stage and frame-zero support-widget cleanup

**Scope:** Surgical Stage/Capture upgrade on the current Phase 2 `main` baseline `7a98625ae1f949531f530202224c7b0a4528ee8e`. Existing camera springs (mass 1, stiffness 180, damping 24), 1200px perspective, H0/H60 60px elevated modal, exact clip/rim/spotlight blur, real Brimble workflow, and frame-locked 48kHz Foley are unchanged. Previous releases, source captures, and backup workspaces are untouched. An explicit backup of source files before editing is at `../sauce-phase2-backups/pryzm-backdrop-capture-2026-11-16/`.

**Root causes:** (1) Current `SaucePreset.stage` had no material field and `CinematicStage.render()` invoked the **style-blind cached** `_stage_base()`, whose sole implementation was the old flat gradient. (2) `session_capture.py` and replay only hid scrollbars, not support widgets. Actual Chatwoot bubble in a HAR-backed Brimble Chromium document is `button.woot-widget-bubble.woot-elements--right`, `title="Open chat window"`, fixed near CSS `(1196,636,64,64)`, **without** a matching `aria-label`. (3) An early init-script style can be removed during Brimble hydration. The named `preview_4_g6BmNY.mp4` was not accessible among worker/Project files this turn; frame comparisons use the last verified `modal-camera-locked` master.

**Implementation:** `scripts/studio-motion/src/types.ts` and `presets.ts` now validate/resolve `stage.backdropStyle`: `obsidian-grain` for Clean Studio, `fluted-glass` for 3D Launch, `chromatic-bloom` for Hyper-Cut. No changes to camera/foley preset properties. Dedicated `scripts/procedural_backdrops.py` generates all three deterministic BGR materials with NumPy/OpenCV and a fixed grain seed, including refracted 45px vertical glass ribs, subdued blue-violet blooms, RGB-separated frosted bloom, and matte obsidian with existing optional RMS ambient pulse. The `cinematic_stage.py` `_stage_base(backdrop_style)` cache now has **distinct style keys** (maxsize=3); all window/floor/shadow/multi-plane composition stays above the stage and original source pixels are preserved. `session_replay.py` passes the resolved actual `motionEngine.preset.stage.backdropStyle` to the stage; `produce_cinematic_demo.py` checks this agreement and records it in the release receipt.

**Support-widget cleanup:** The capture and replay import one shared `PRESENTATION_CLEANUP_STYLE` and `install_presentation_cleanup(context)`, suppressing scrollbars, `#intercom-container`, `.crisp-client`, `#hubspot-messages-iframe-container`, `[aria-label*="chat" i]`, and the specifically observed `.woot-widget-bubble`/Chatwoot holders. The CSS is inserted before navigation; a child-list MutationObserver reinstalls the style if hydration removes it. Post-hydration `add_style_tag` reinforces it. This is presentation-only, retains source actions/DOM nodes and does not block scrolling.

**Verified new 1080p master:** https://devmcp.davemafy.xyz/sauce-motion-phase2/fluted-glass-clean/ ; MP4: https://devmcp.davemafy.xyz/sauce-motion-phase2/fluted-glass-clean/master-1080p60.mp4 ; full-size frame-zero PNG: https://devmcp.davemafy.xyz/sauce-motion-phase2/fluted-glass-clean/frame-zero-full-native.png ; before/after opening: https://devmcp.davemafy.xyz/sauce-motion-phase2/fluted-glass-clean/before-after-opening.jpg ; 15-frame review contact: `qa-contact-fluted.jpg` at the same URL prefix.

**Frame-zero actual measurements:** The decoded older approved master contained **3,629 saturated Chatwoot-blue pixels** within output ROI `x=1570..1695, y=835..954`; new decoded frame zero has **zero**. Outer-stage sampled RGB/BGR mean difference is **8.16/255** from the new bands/blooms; browser UI interior mean per-channel difference is **0.0859/255** (codec/replay), so stage work does not paint over product text. Native frame zero and full 15-frame contact sheet were opened and visually inspected; ribbing is visible above/beside the browser, the blue bubble is absent, the centered white dialog and full generated command remain source-true through the Codex click. No claim that a procedural backdrop alone makes the demo a premium film.

**Stream/physics checks:** H.264 1920x1080@60fps, 197 frames, 3.283333s, AAC 48000Hz stereo; full FFmpeg decode passed. The stage receipt records `fluted-glass`, six verified source states, 152 genuine elevated-modal frames, zero fallbacks, 152 terminal-concealed frames and the same frame-125 beat cut. Foley: four cues, 157,600 PCM samples at 48kHz; original and new AAC streams have the same MD5 `2ddb5646169cc954a117d1cc22e4091b`. The release receipt's new style and cleanup metadata were populated after verification of the already encoded MP4; no media bytes were changed. New public page, master, native opening and previous baseline returned HTTP 200. Desktop 1280x720 and mobile 390x844 Playwright successfully sought to 2.09s, with no player errors or horizontal overflow.

**Tests:** TypeScript Studio Motion: 29/29; Python unittest: 160/160; Phase 2/3 pytest: 29/29 (including HAR-backed Chromium Chatwoot check, style-cache/material separation, source pixel preservation, RMS-reactive obsidian stage and original multi-plane safety). No new third-party libraries, no paid services or altered raw reference captures. The named external preview `preview_4_g6BmNY.mp4` was not directly available for byte/frame inspection. Main quality caveat remains: this is a 3.28-second verified technology demonstration, not acceptance of a longer premium product film.

## 2026-11-16: Opt-in orbital spring camera and isolated stage optics

**Scope and safety:** Worked on main per AGENTS.md, preserving baseline commit 39ea1790f09e9d86315b912f69cdfe3698de3b13 and earlier releases. Private pre-change backup: ../sauce-phase2-backups/2026-11-16-pre-orbit-optics/. Flag to enable: --preset 3d-launch --experimental-orbit-optics --optics-seed 20261116 --deterministic-frame-cache [private-dir]. Without the flag, preserve original spring 180/24/1, 1200px perspective, existing static 3D tilt and CRF 14 encode.

**Engineering:** Retained the already-real exact analytical second-order mass-spring integrator in cameraRig.ts; flagged damping is 18 (mass 1, stiffness 180) to give restrained overshoot. During genuine modal ownership, rotateX/Y target angles move on the fixed 60fps timeline with 2200ms orbital period. Angular springs persist through the actual frame-125 editorial cut; the modal remains the camera target even during the Codex child click. New stage_optics.py refracts the fluted stage/floor light bands by <=1.5px, applies deterministic frame-indexed seed-driven analog grain (<=2/255) only outside the H0 and H60 protected polygons, and disperses spectral shadow/modal rim color by <=1.5px. The unchanged H0/H60 elevation, 6px blur, 1px modal rim and 48kHz Foley remain source-true. The flagged single-thread x264 uses a 12 Mbps CBR target and rejects any finished master below 8 Mbps measured video bitrate. Default export settings unchanged.

**Determinism limitation:** Two initial full replays from the *identical private source raster cache* still differed because the live Chromium modal/overlay compositor is not fully reproducible. A separate controlled repeat of 75 frames using x264 7 threads gave differing frame hashes even with exactly identical input. Switching to one x264 thread gave byte-identical MP4s in that controlled experiment but did not remove all live Chromium differences. To establish a reproducible, versioned release proof, canonical_frame_cache.py now stores private full composited-frame PNGs with SHA-256, bound to the verified source fingerprint, full FramePlan, explicit seed, and renderer code hashes. The second complete full render used that pinned, verified cache and reported 152 live compositor differences; it nevertheless encoded precisely the pinned images. This **does not mean independent live replay is deterministic**. The source actions and semantic/visual checks were still executed, and cached frames are private and checked for tampering.

**Measurement evidence:**
- 3D Launch modal target 1.31x; new flagged spring reaches 1.3231x and settles. rotateX 0.1739 degrees at frame 110 and 0.4304 at frame 170; rotateY -0.5343 and -0.5748 respectively. Continuous orbit does not reset on the frame-125 cut.
- Stage ON/OFF at identical H0/H60 poses: synthetic browser-window SSIM 0.99999583; *real pinned Brimble source frame 114* SSIM 0.999996603, mean per-channel pixel difference approximately 0.001175/255. Both exceed the 0.999 isolation floor.
- Two full canonical-cache-backed 197-frame exports had identical MP4 SHA-256 f4d0d91a9b3408a464906f3e4d5a0839b02ad8e5e5d7c29d50c0249ba01b8924 and 197/197 identical decoded H.264 frame MD5 hashes. Pass pertains to *same verified private composited-image cache*, not two independent browser captures.
- ffprobe: H.264 1920x1080@60/1, 197 frames, measured video bitrate **12,297,037 bps**; duration 3.283333s, AAC stereo 48kHz, 4 Foley cues, 157,600 sample slots; AAC stream MD5 2ddb5646169cc954a117d1cc22e4091b. Complete FFmpeg decode passed.
- Six source-verified states; 152 elevated H0/H60 frames, zero fallback, 152 concealed terminal frames; frame-125 action cut remains. Actual film contact sheet (17 timestamps, including 0, 114, 125, 170, 196) visually inspected. These passing gates do not by themselves certify premium film direction.
- Tests: 30/30 TypeScript, 160/160 Python unittest, 32/32 Phase 2/3 browser-backed pytest. New tests cover real H0/H60 optics SSIM, seed determinism, cache tampering and source/plan binding, as well as modal orbital overshoot and baseline-off behavior.
- Independent public proof (old releases preserved): https://devmcp.davemafy.xyz/sauce-motion-phase2/orbit-optics-experimental/ ; master https://devmcp.davemafy.xyz/sauce-motion-phase2/orbit-optics-experimental/master-1080p60.mp4 ; QA contact sheet https://devmcp.davemafy.xyz/sauce-motion-phase2/orbit-optics-experimental/contact-experimental.jpg . Deployed master hash matches worker output. HTTP 200 and playback/seek on desktop 1280x720 and mobile 390x844 passed.

**Open issue:** Reproducibility without canonical composited-frame cache remains unsolved; investigate nondeterministic DOM/overlay state and never describe cache-backed output as wholly independently deterministic. Creative/quality approval of the experimental orbit remains separate from technical test success.

## 2026-11-16: Corrected sharp rectangular H60 modal edge (native film proof)

**Source and issue:** The user identified an unnaturally sharp white rectangular border around the otherwise rounded "Connect your agent" dialog in the optional orbital-optics Brimble video. Inspected the real 197-frame, 1920x1080 experiment at native frame 170, not only the user's cropped screenshot. Root cause in `scripts/multi_plane_depth.py`: the modal itself was masked with `_rounded_region_mask`, but an **additional** `cv2.polylines(..., front_quad, RIM_COLOR, 1)` drew a hard four-sided luminous rectangle over its curved corners. Two shadows also used hard rectangular projected quads. The experimental `stage_optics.py` independently reconstructed a rectangular `modal_quad` for RGB dispersion, reinforcing squared edges.

**Minimal fix:** Keep authentic Brimble source pixels, true H0/H60 homography, z=+60px, 6px background blur, 180/18/1 flagged orbital springs, original 1200px focal length and 48kHz Foley unchanged. Both H0 ambient/contact and H60 cast shadows now project the *same source-based rounded alpha* as the dialog; eliminate rectangular `cv2.polylines`. A softly feathered, low-opacity ~1px exterior-only mask follows the rounded silhouette without recoloring dialog text or interior. `CinematicStage.render()` exposes the real composited rounded coverage to the optional RGB optics, replacing its sharp H60 rectangle; stage refraction and <=1.5px chromatic edge displacement still operate off-window. The unflagged compositing path also receives the corrected rounded edge and nothing else. Original source modules backed up privately at `../sauce-phase2-backups/rounded-rim-2026-11-16/`.

**Real visual evidence:** Compared identical action/time native frame 170 of the previous `phase2-orbit-canonical-C` approved experimental video with the new `phase2-rounded-rim-experimental` render. The old bright horizontal/vertical squared hairline and corner joints disappear; rounded white corners/shadow remain, source headline, Codex word and copied command stay legible. Opened `corner-before-after-100pct.png` (1660x865) and an 8-frame master contact sheet. Public proof: https://devmcp.davemafy.xyz/sauce-motion-phase2/orbit-rounded-rim/ ; actual-native before/after image https://devmcp.davemafy.xyz/sauce-motion-phase2/orbit-rounded-rim/corner-before-after-100pct.png . The prior `orbit-optics-experimental` release is preserved.

**Verified gates:** Same 197 frames / 3.283333s, 1920x1080@60fps H.264 at **12,317,443 bps measured video bitrate**, AAC stereo 48kHz, 152 H0/H60 frames / 0 fallback, 152 terminal-concealed frames, original frame-125 cut. Complete FFmpeg decode succeeded. Stage-optics ON vs OFF with identical synthetic foreground/source geometry after the edge fix: full-browser rectangle **SSIM = 0.99999422**, above 0.999. New corner regression explicitly checks all four projected rounded H60 vertices contain no bright rectangle stroke while text-center remains authentic, the rounded coverage is deterministic, and the optional spectral fringe uses the same mask. All test suites: **30/30 TypeScript**, **160/160 Python unittest**, **34/34 Phase 2/3 browser-backed pytest**.

**Repeatability caveat, unchanged:** Two full 197-frame MP4 renders produced **identical whole-file SHA-256 `6363fedbbc223ce6b50f94dea2a28ccee1d43afa3aabf357140d130713b9c4ec`** and identical decoded video frame hashes, *using the same verified private canonical compositor cache*. Repeat-run live browser compositing still differed on 152 frames before the pinned image selection. Do not claim independent live Chromium replay determinism. The published file's checksum matches the worker copy; new public player, master and comparison returned HTTP 200 and the previous proof still returns 200. Desktop 1280x720 and mobile 390x844 Chromium playback seeked to 2.84s with no video/page errors or horizontal overflow. Engineering acceptance is separate from broader premium visual storytelling approval.

## 2026-11-16: Dynamic source-derived brand-token capture and stage lighting

**Goal:** Make Sauce capture/replay adapt dim studio light to each real target
site without hardcoding a per-domain palette or recoloring source UI. Added
`scripts/brand_extractor.py`, `docs/brand-ingestion.md`, and
`tests/phase2/test_brand_tokens.py`. A copy of all modified engine sources
from before this work is stored under
`../sauce-phase2-backups/brand-tokens-2026-11-16/`.

**Actual ingestion and renderer path:** At capture start, after browser
hydration and before state zero, `session_capture.py` evaluates a bounded
public-style-only extractor. It reads computed root/body CSS custom properties,
public theme meta tags, semantic CTA backgrounds and accent strokes, plus
body/heading typography. Chromium resolves modern CSS colors to sRGB. The
canonical `sauce.brand.v1` snapshot records color provenance and whether
colors are observed or neutral fallback. `session_contract.verify_package`
rejects malformed snapshots; `session_replay.py` maps them to
`CinematicStage` and its cached `_stage_base(style,primary,accent)`,
audio pulse and 1px rounded modal rim. The opt-in spectral edge uses bounded
brand-derived channel weights. Normal stage darkness remains limited; no
overlays or colored pixels are applied over real UI. Private raw-raster
cache identities now incorporate brand snapshot when present. Existing
session JSON without a snapshot receives **exact original neutral style**.
No camera, H0/H60 geometry, spring constant, cut, source cursor or Foley change.

**Evidence:** Two browser-backed fixtures at distinct origins, with genuinely
different CSS and theme-color sources, resolved to Cobalt
`#2872d7/#24a896` and Copper `#eb6c18/#b52c69` and produced distinct
cached fluted materials while source browser content stayed pixel-identical.
Separate test covers Chromium conversion of OKLCH and HSL token forms.
Observed live Brimble from its existing pinned HAR has source-visible
accent stroke `#006fff`; no reliable explicit primary, so primary is
derived from the **same** accent. Observed Brimble type was
`IBM Plex Sans` body and `Lora` heading. The original old Brimble session
had no brand snapshot and remains unmodified. An isolated private
evidence-derived session using the *same existing HAR and state SHA checks*
was created solely to prove the new renderer mapping; do not present that
as a newly independently captured original trace.

**Actual encoded proof:** Separate public release
https://devmcp.davemafy.xyz/sauce-motion-phase2/brand-aware-ingestion/
and master
https://devmcp.davemafy.xyz/sauce-motion-phase2/brand-aware-ingestion/master-1080p60.mp4 .
Two palette material comparison:
https://devmcp.davemafy.xyz/sauce-motion-phase2/brand-aware-ingestion/two-brand-materials.jpg .
Brimble blue-lit 10-frame contact:
https://devmcp.davemafy.xyz/sauce-motion-phase2/brand-aware-ingestion/brand-brimble-contact.jpg .
SHA-256 of deployed and worker master:
`731333e92a55871b989ec7e78aed4061172a0e7e864d1a9ad3374606e528dc68`.
Measured from actual 0.00s encoded frame versus earlier neutral
`fluted-glass-clean` master: outer-stage 185x105 ROI mean absolute
channel change **2.796/255**, with extracted color visibly steering
the fluted lighting. The full contact sheet and native key frames
0/114/125/170/196 were reviewed. H.264 1920x1080@60fps,
197 frames / 3.283333s, AAC 48kHz stereo, 152 genuine multi-plane frames,
zero fallback and same frame-125 action cut. Full FFmpeg decode passed.
New page/master/material image and previous release returned HTTP 200;
public desktop 1280x720 and mobile 390x844 player both sought to 2.85s
without page/media errors or horizontal overflow. Prior releases remain
untouched. Stage color effect is restrained; visual-quality certification
still needs independent creative review.

**Regression suites:** TypeScript StudioMotion **30/30**; Python unittest
**160/160**; Phase 2/3 pytest including live Chromium **40/40**.
Token tests validate canonical serialization, CSS priority, color fallback,
theme-tag parsing, font capture, source pixel invariance, LRU key separation
and malformed input rejection. Existing 3D camera and audio sync tests pass.

**Known limits:** No canvas/WebGL palette extraction, cross-origin iframe
traversal or independent nondeterministic live-replay fix. Font tokens are
captured for future typography-aware decisions, but the renderer does not
replace source typography. Never claim that every website exposes a
trustworthy brand palette; neutral fallback is intentional.
