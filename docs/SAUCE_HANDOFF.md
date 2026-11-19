# Sauce — living handoff for new agents and new chats

**Reviewed:** 2026-11-17. This is a checkpoint, not an assertion that the service or GitHub CI is always healthy. Check `origin/main` and current public output before acting. More recent commits and live evidence supersede these notes.



## 2026-11-19 — URL-to-demo coverage on three additional public URLs

Submitted three real jobs to isolated instances of the same Sauce URL API used for the Resend proof. The URL engine and effects code match main at `f03594e`. No site-specific manual directions or AI calls. All three previews reached `needs_review`, were inspected from the encoded output, passed full FFmpeg decode, and played and sought at 1280×720 and 390×844. HTTPS returns byte-identical MP4s.

- [Bootstrap Collapse](https://devmcp.davemafy.xyz/sauce-motion-phase2/url-sites-20261119/bootstrap.mp4) — 7.47s. Sauce opened the second example panel and framed the visible result with one automatic camera push. Dense documentation gives the opening little visual focus. Job `6b41283b23179ad5facdc112`.
- [Brimble homepage](https://devmcp.davemafy.xyz/sauce-motion-phase2/url-sites-20261119/brimble.mp4) — 9.47s. Source-verified showcase. The scroll moves into “Push to deploy,” with no verified product interaction. Job `8de7ff1554578abe0a698ba4`.
- [Linear homepage](https://devmcp.davemafy.xyz/sauce-motion-phase2/url-sites-20261119/linear.mp4) — 11.50s. Source-verified showcase. The clip spends too long in the hero and product text is small. Job `b7ef2d198f89718b377456de`.

The Bootstrap example verifies a second interaction pattern beyond Resend's slider. Brimble and Linear demonstrate the current fallback. Public homepage URLs often need deeper product-aware direction or a URL landing on a runnable demo. None of these review artifacts constitutes film approval.


## 2026-11-19 — URL jobs use the cinematic compositor

[Implementation on main](https://github.com/Davemafy/sauce-vids/commit/f314b202f37b36cb37e6c75b311a96a29949b6c9) routes the normal URL job through `scripts/render_event_video.py`. The compositor now supplies the floating browser window for URL films. A real public range drag can invoke the established glass optics and rounded cursor when the browser confirms a changed range and a nearby visible numeric result. A verified expanded panel can trigger a camera push. The showcase remains available when the page offers no qualifying interaction. Eligible range takes use local direction and zero inference calls.

**Verified job.** Submitted [Resend pricing](https://resend.com/pricing) through `POST /v1/jobs` on the existing Vultr worker using an isolated Sauce API instance. Job `c01817e5007497a9ffdfe822` reached `needs_review`, and the authenticated preview route returned bytes identical to the on-disk preview. The real range moves to 100,000 emails and reveals $35/mo. The renderer used 26 recorded pointer samples, one glass shot and no additional camera push. The 1920×1080 DPR 2 capture is 25 fps. The 327-frame 1080p60 H.264 master is 5.45 seconds and passed full decode. Master SHA-256 `4b739b8e269f001540e41b2cda3c71f2f213940c5bad44564493d378e23c4b2a`. Preview SHA-256 `2e6466a6b3c8ba196b07342e83ca711a4781c501715a515ab495734cccbee190`. [Review the generated MP4](https://chatgpt.com/library?file_id=libfile_50da2306d8b08191bf78215371a12288&account_id=personal).

**Visual review.** Checked encoded opening, glass entry, drag, release and final hold at approximately 0.00, 1.17, 1.63, 2.23, 3.47 and 5.30 seconds against the reference and earlier rounded-cursor shot. The final framing holds both price cards. The arrow stays crisp with the refraction concentrated at the glass edge. The drag can sit briefly ahead of the discrete thumb steps, and the neutral matte replaces the landscape from the reference. This proof is silent. The preview played and sought without overflow at 1280×720 and 390×844. A separate Bootstrap capture verified one real panel-reveal camera shot. A Resend showcase control run confirmed the framed fallback.

**Regression and rollout.** 58 targeted tests and 12 subtests passed across capture, URL direction, camera, glass and job persistence. The live service still runs its locally modified `/opt/sauce-vids` tree. Its API passes a `duration_seconds` argument absent from main, so replacing that tree would regress live behavior. Reconcile that contract in a staged release before switching the service. This review build leaves production and the public launch approval gate intact. The examples establish the effect and fallback paths on two sites. Automatic direction and legibility across a wider set of URLs remain open.


## 2026-11-18 — Phase 2 action-first film QA, source-verified group framing, bounded rejection

**Verified source implementation:** main commit [`465e1882f60dff9200e835637c4565a7d198924c`](https://github.com/Davemafy/sauce-vids/commit/465e1882f60dff9200e835637c4565a7d198924c); kept prior main and all dirty production worktrees untouched. Full frame-by-frame A/B, exact film evidence, preflight rejections and creative defects: [SAUCE_QUALITY_AUDIT_20261118.md](SAUCE_QUALITY_AUDIT_20261118.md).

**Public film:** [13.97s action-first Linear study](https://devmcp.davemafy.xyz/sauce-motion-phase2/quality-action-first-20261118/) · [H.264/AAC 1080p60 master](https://devmcp.davemafy.xyz/sauce-motion-phase2/quality-action-first-20261118/master-1080p60.mp4) SHA256 `834c13683c2a2171f0a1017fc05c1d4b29f5a89b227817830af844ff74236770` · [Actual before/after frames](https://devmcp.davemafy.xyz/sauce-motion-phase2/quality-action-first-20261118/comparison-source-true.jpg). Source is Linear's genuine public interactive marketing preview, not authenticated customer data. Four recorded action/outcome scenes, 838 output frames, 1920×1080/60fps, 48kHz AAC, full FFmpeg decode. Original 15.27s film is preserved at `linear-refs-market-20261118/`.

**Defects and engineering correction:** first frame originally jumped to a 2.55× future metric teaser and the final crop displayed **none** of three genuine summary-card source rectangles. v2-v4 candidate rerenders were rejected for inadequate final hold, clipped 3,389 or incomplete metric group. v5 opens with recognizable workspace context, focuses the verified first metric at 1.72×, then uses the new `overview:2` DOM-measured group anchor to keep **100% / 100% / 100%** of the three verified cards in the final frame. Source-timed recorded cursor and procedural Foley remain truthful. Three output click cues f121/341/545; measured live pointer coordinates are within all three recorded targets. No white source flashes found in 280 sampled encoded frames.

**Reusable opt-in improvements:** `evidence_edl_renderer.py --quality-gate` rejects future-result editorial openers, absent product context, missing source-verified outcomes and unsafe group crops. `--bounded-repair` can *only* discard a verified unnecessary teaser when the remaining film is long enough, never inventing UI or retiming clicks. `--camera-shutter` uses a 3-sample motion exposure with existing real source pixels only while the camera moves; static holds are unmodified. The normal renderer and existing signature effects remain unchanged.

**Verification:** 124 passed / 11 skipped Phase 2+3, 205 passed / 1 skipped unittest, 33 TS planner passing after `npm ci` restored local build tools. Public HTTPS page, master, preview, poster and comparison returned 200; Playwright desktop 1280×720 and phone 390×844 streamed, sought and played the actual preview without errors or overflow.

**Quality judgment:** **6.5/10 provisional in-house**, **not owner/human-approved**, no independent outside creative signoff. Still a tour of the public marketing preview, not an end-to-end customer task. Dark/dense UI harms phone-readability, three cuts mask real preview remount flashes, sound remains sparse and the EDL is still operator-authored. This is an evidence-backed improvement to the existing engine, **not proof that paste-any-URL auto-direction is solved**. Existing rejected CMOkit/Studio URL path and self-repair integration remain highest-priority next work. Preserve private source capture and event manifests outside public assets.


## 2026-11-18 — click-water refraction on genuine Brimble events (opt-in technique, NOT approved film)

**Source:** current GitHub main was `9bfd5ff6bda1de737edd503a8be8214b8a9a55b7` at the start. Implemented in a fresh isolated **main** checkout on the existing persistent Vultr DevMCP worker, not in the dirty `sauce-v05-release` or `sauce-effects-20261118` directories. Those prior working trees were preserved. The commit adding this section contains the feature; inspect that commit's SHA from `main` rather than assuming the bootstrap SHA remains current.

**Opt-in flag:** `scripts/produce_cinematic_demo.py --click-water-ripple`. `scripts/session_replay.py` also exposes the flag. No additional listener is needed: existing, verified `session.json` `pointerdown` entries supply source-clock timestamp and CSS click position. The existing `CinematicCursor` projects it through the actual moving H0/H60 camera and invokes `scripts/click_water_ripple.py` *before* rendering the sole cursor. The old graphic click ring remains the default; users never see both simultaneously. Water refraction uses a bounded NumPy radial wave + `cv2.remap` on a local region of the **encoded film compositor**, not a CSS/web-player filter. Non-wave pixels are restored byte-exactly; the BGR source capture is not modified.

**Modal quality correction:** the initial encoded run showed the waterwave distorting the real Brimble dialog/result text. Its follow-up uses the genuine projected H60 quadrilateral as an occlusion matte for underlying H0 clicks; clicks actually on H60 use a softer, 0.27-second wave instead of the larger 0.56-second ambient wave. Corrected full-resolution frame review at **0.95, 2.19, and 2.36 seconds** showed the dialog copy remained readable and the pointer remained visible, while the earlier run visibly bent its text.

**Verified offline render:** existing private verified Brimble fixture `../sauce-v05-release/studio/.tmp/brimble-reference-v16-ink`, source `https://www.brimble.io/`, source real clicks at approx **0.786s** and **2.069s**. Output is private in this worker's scratch checkout: `sauce-click-ripple-1118/studio/.tmp/water-ripple-occluded-1118/master-1080p60.mp4`; **1920×1080, H.264, 60 fps, AAC, 3.283333 seconds, 197 frames**. QA sheet `.../water-ripple-occluded-1118/ripple-qa.jpg` compares initial/occluded refraction at the three timestamps. Existing 3D Launch frame/Foley engine was used; no paid inference. `release.json` records `click_water_ripple=true`.

**Tests:** `../.sauce-render-env/bin/python -m pytest tests/phase2 tests/test_cinematic_stage_root.py -q` → **109 passed, 10 skipped**; unit tests cover onset/expiry, local displacement, deterministic reproduction, byte-exact unaffected pixels, modal occlusion, UI-safe short foreground wave, and opt-in engine wiring.

**Still unapproved:** this is a source-true *technique proof*, not a premium film or a deployed paid feature. It does not implement the previously explored **full-screen convex CRT base distortion**; that prior shot was a separate still experiment. The second-click wave is intentionally understated to preserve text, and visual impact needs further owner/reference review. Do not publicly publish this private scratch render, claim quality approval, or expand access based only on green tests.

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


## Private URL-to-video backend alpha, 16 November 2026

The owner requested an incremental backend URL -> film pipeline using the
**existing** Sauce renderer, one optional Gemini vision call, and feedback
for subsequent decisions. Implemented in backend/url2video.py and
backend/sauce_api.py, with public network guard under scripts/capture_safety.py.
A localhost-only systemd service is running on the Vultr host at
127.0.0.1:8767; authentication is a strong per-host bearer token, stored
outside Git. The configured AI secret GEMINI_API_KEY is **not present**,
so no live AI-directed film has been produced or claimed. The GET-only
Paldey inspector returned 17 headings and 45 visible controls.
The old VM code at 77a5311 was used for that deployment and differs from
the newer remote main; source publication is rebased onto latest remote main
without clobbering its brand-extraction, motion, or depth changes.
Run /opt/sauce-vids/.venv/bin/python -m pytest -q tests for the VM state:
176 passed, 5 skipped, 43 subtests passed (plus separate API/Paldey probes).
No creative quality signoff; every future MP4 is gated on human review and
the current auto workflow supports only non-mutating scroll/hover.
See docs/url-to-video-backend.md for key setup, API paths, privacy and limits.


## Studio loading-state production monitor (16 November 2026)

Owner requested a living, modern loading screen instead of a stalled spinner.

- Source commit on main: f3f1b90f6d071addd9738ca9284006489f898580
- Live URL: https://devmcp.davemafy.xyz/sauce-app/studio
- Implementation: apps/web/app/studio/render-progress.tsx,
  render-progress.module.css, studio-client.tsx and
  apps/web/lib/studio-renderer.ts.
- Measured REPLAY n of total frame counts from the real compositor,
  no invented total-job percentage. Display queued/compositing/export phases,
  elapsed time, gentle film-strip motion, reduced-motion accessibility,
  reconnection messaging, session job reattachment, and failed-job retry.
- Live browser checked at 1280x720 and 390x844 with no page errors or overflow.
  E2E verified queued, compositor frames, refresh restoration, ready and mobile.
- Real render smoke job sauce-hyper-cut-silent observed 0/140, 60/140,
  120/140 frames, then ready. Encoded preview is H.264 1280x720 30fps
  with AAC, and passed full FFmpeg decode.
- Deployment via a separately built Studio application directory under
  the existing systemd service, preserving the original render workspace.
- Current scope is the bounded-catalog Studio UI. The private URL-to-video
  backend is not yet exposed as a public user URL-generation form.
  A technically complete render still needs visual-quality review.


## URL-first Studio pilot (16 November 2026)

The URL-to-film flow, not the bounded sample renderer, is now the
primary Studio page at https://devmcp.davemafy.xyz/sauce-app/studio.
Legacy sample recordings are at /sauce-app/studio/samples.

The web UI has a permission-gated private pilot URL form and renders
actual stages: inspecting, directing (exactly one vision call), capturing,
rendering (actual compositor REPLAY n/total), needs_access, failed,
and needs_review. It preserves job identity across refresh, reconnects
status polling, honors reduced motion, and offers human rating/feedback.
Private MP4 preview uses a signed HttpOnly, SameSite Strict, HTTPS cookie.

The Next proxy uses a private Unix socket owned by devmcp with mode
0600 inside a 0700 directory, not a bearer token copied into the
web process. The existing loopback Bearer API remains separately
protected. Arbitrary untrusted public submissions require a strong
private pilot access code held outside Git, plus same-origin checks.
Source: apps/web/app/studio/url-flow.tsx, url-flow.module.css,
apps/web/app/api/studio/url/[...parts]/route.ts, and backend/sauce_api.py.

Technical tests: 13 Next unit tests, 10 Playwright browser tests,
176 Python pytest tests (5 skipped, 51 subtests) and 6 backend unittest
tests passed. Live HTTPS /studio and /auth return HTTP 200; unauthenticated
media returns 401, incorrect pilot code and cross-site POST return 403.
Desktop 1280x720 and mobile 390x844 passed no-overflow checks.

AI model verified for multimodal direction: gemini-3.1-flash-lite.
The prior 3.5 Flash Lite intermittently returned HTTP 503 for image
direction. The Paldey public site was inspected and one vision call
correctly returned needs_access (no private scholarship workflow
invented). Its initial attempt was blocked by provider unavailability,
then the model was changed and retested.

IMPORTANT UNFINISHED QUALITY GATE: a public site that the AI approved
advanced to real capture and frame rendering, but its output failed
the existing replay semantic/visual-region QA. This must NOT be
claimed as a successful premium URL-to-video export. The workflow
now includes observed expect_selector assertions and trace-derived
duration; strict visual comparison remains enabled. The director's
current public-site workflow supports hover/scroll only and should
not claim to demonstrate interactive product actions. A verified
full URL -> MP4 outcome remains a next technical acceptance milestone.

Rollback: remove the separate URL Studio systemd WorkingDirectory
override and restore the previous isolated Sauce Studio build.
No worker sessions, credentials or raw captures were committed.

## Continuous-browser URL film engine — 17 November 2026

The owner rejected the screenshot-montage URL output as a slideshow. The
active pipeline is backend/url_engine.py -> backend/product_explorer.py ->
backend/live_capture.py -> backend/live_render.py, NOT backend/state_film.py.
Never restore still-frame montage as the default URL output.

Live capture records an actual Chromium WebM stream with pointer motion,
scrolling and visible application changes. A publicly accessible paste-text
control may type one benign demo fixture; no submission is performed.
Showcases use paced frame-driven DOM scrolling. Rendering trims browser
loading dead air, validates the input SHA-256, and exports H.264 1080p master
and 720p preview. It reports real encoder frames. Receipt properties
continuous_motion=true and replay_verified=false are intentional and
different: an original recording is NOT an independent browser replay.

Real end-to-end smoke:
- SEAL (seal-verify.vercel.app): ~7.97-second film, opens the public
  paste-text interface and types non-submitted example text.
- Igor (igor-taste.vercel.app): continuous hero-to-product preview scroll.
- Paldey (paldey.com): continuous public-site showcase, never a claim of
  accessing the private scholarship matching workflow.
- A separate paced-scroll Igor capture passed after scroll easing updates.

Studio live: https://devmcp.davemafy.xyz/sauce-app/studio
Old still-frame drafts are clearly labelled historical. On public HTTPS,
a 390x844 authenticated Chromium session accessed the protected SEAL MP4
with HTTP 200; no JavaScript page errors or horizontal overflow.

Verification: 184 Python tests passed, 5 skipped, 56 subtests; 13 web unit
tests; 11 Playwright browser tests; Next production build passed.
Explorer safety tests protect against arbitrary model CSS, cross-origin
navigation, mutation controls and form submit. Source and credentials
remain private.

Remaining: these are authentic recordings, not yet world-class editorial
product films. Better focal framing, app-specific motion and deeper
multistep safe exploration are needed before creative quality signoff.

## 2026-11-17 — Modal-first camera and result-aware final readability

**Source of truth:** Continued on current GitHub `main` after a safe
fast-forward from `4310b19` to the newer upstream `a536e93`; preserved
all intervening URL-to-video backend and Studio changes. Pre-edit copies
of the touched files are in
`../sauce-phase2-backups/2026-11-17-result-aware-editorial/`.
Feature implementation and acceptance contract: `docs/result-aware-editorial.md`.

**Defect 1, double zoom:** The real Brimble trigger click occurred at
2232.9ms, with the newly mounted dialog observed at 2362.7ms (129.8ms).
The previous rig briefly aimed at the left-side trigger, then sprang
to the dialog. `scripts/studio-motion/src/cameraRig.ts` now suppresses
trigger-button zoom only for a **verified** modal HeroMoment within 300ms
and begins its existing 180/24/1 spring on the modal once visible.
`scripts/session_capture.py` now correlates actual click events to
role-based and genuinely floating high-z overlays (not Radix backdrops
or chat widgets) and includes the real latency and box. Numerical
Brimble camera QA: frames 45–53 stay at (640,360), scale exactly 1.0;
frame 55 scale 1.00679, frame 65 1.23320, frame 90 1.31041 and settled
modal focus at (640,362.59), no sideways trigger zoom.

**Defect 2, abrupt final result:** New `scripts/result_reveal.py` runs
a transient Chromium-local visible-text/geometry comparison before and
after actual replayed/captured clicks; only boolean changed text, node
count and container growth become metadata, not product/command strings,
credentials or content digests. A Radix full-page `data-state=open`
backdrop was initially misidentified as the dialog; this was found in
a real Brimble A/B probe and corrected to prioritize semantic dialogs.
The genuine Codex click revealed 5 new text nodes and enlarged the
dialog by 116px. With explicit `--result-aware-editorial`, the renderer
now appends **96 sharp 60fps copies of the real final state (1.6s)** and
**21 cosine-eased fade frames (0.35s)** directly to its raw-frame encoder.
Without observed qualifying final-click evidence, no tail is added.
The original published master remains unchanged; new default re-renders
receive the modal-first camera fix, but the extra result tail is opt-in.
There is no second-lossy-encode text softening.

**Actual output:** https://devmcp.davemafy.xyz/sauce-motion-phase2/modal-first-result-dwell/
with unchanged original baseline still accessible at
https://devmcp.davemafy.xyz/sauce-motion-phase2/brand-aware-ingestion/ .
Master SHA256
`c1b6be87cc7ef4d43643027f8148623ccc9bb553a7b0db80b13401b54262a806`,
verified identical between published and worker file. The full MP4
decodes with FFmpeg. `ffprobe` confirmed H.264 1920×1080@60fps,
314 frames/5.233333s, 48kHz stereo AAC; 197 source planned frames plus
117 result-tail frames. Foley report confirms **251,200 samples** =
314*800 exactly. Previously verified six source states, frame-125
action cut, 152 H0/H60 multi-plane frames and zero fallbacks preserved.
Native frame 215 exposes the Codex command clearly. Contact review at
0/30/45/50/55/65/75/90/114/125/155/170/196/215/255/292/293/303/
305/313; original source-and-cursor presentation remains legible.
Decoded frames 210 vs 290 during the hold differ by only 0.17968 average
8-bit channel levels due to H.264 quantization (raw hold input identical);
the final fades to the dark stage. The published page/master/contact sheet
returned HTTP 200; desktop 1280×720 and mobile 390×844 Playwright
successfully seeked to 4.68s with no media/page errors or scroll overflow.

**Tests:** Studio Motion TypeScript 31/31, Python unittest 174/174,
Phase 2/3 plus URL-backend pytest 57/57 (13 nested subtests);
new role-based and high-z capture cases, fast-vs-late dialog camera
triggering, sensitive-data exclusion, actual result classification,
zero-padding negative case and raw-frame/fade timing passed.
The latest standalone high-z capture test also passed 4/4 in the
targeted result-editorial file. Confirm full suite after this file
addition before publishing the commit.

**Outstanding:** The brief Brimble source terminal/window overlap near
0.72–0.82s is visible in the earlier baseline and in this new render;
the two requested edits did not introduce or resolve it. Do not report
it as fixed. Independent live browser replay determinism remains a
separate known limitation; film technical gates alone are not premium
creative signoff.

## 2026-11-17 — Cursor H0/H60 edge-crossing discontinuity eliminated

**User visual report:** The pointer appeared to crack/jerk when gliding from
the Connect Agent trigger into the opened Brimble dialog, roughly 1.6s into
the new 5.23s result-aware film. Reopened and inspected the actual
`phase2-modal-first-result-dwell-v2` MP4 and the source cursor samples
around frames 92–107, not just the player UI. The original CSS pointer
recording remains continuous; the compositor was switching the *rendered
pointer hotspot* instantaneously between the background H0 projection
and foreground H60 homography based on a rectangular in-modal hit test.
At source t=1.617s, the two projected locations were 16.63px apart.
Old motion fell from 27.41 to 17.73 pixels in one frame, then jumped
to 30.24px on the next. This was an artificial depth switch, not real
hand movement.

**Fix (main only, no baseline overwrite):** Added
`scripts/cursor_plane_motion.py` with a deterministic 0.14-second
quintic-eased single-pointer depth transition. In
`scripts/cinematic_stage.py` the actual pointer position is projected
onto both H0 and H60, then interpolated using that state only where
real DOM foreground coverage/recorded cursor coordinates identify
modal entry or exit. Unlike a hard Boolean switch, the new depth
projection preserves continuous velocity and acceleration at each
endpoint. It changes neither the CSS input/Playwright click path nor
actual source UI, camera spring parameters, multi-plane compositing,
spotlight, brand tint, Codex cursor text-protection, shot cut, or Foley.
Discontinuous >200ms source-clock cuts reset the transition instead of
adding a fake tween over omitted frames. Original compositor backed up
privately under
`../sauce-phase2-backups/cursor-plane-glide-2026-11-17/`.

**Frame-specific proof:** Derived all projected pixel locations from
the actual source events, exact spring cursor-track, recorded Brimble
modal rectangle and exported 3D Launch camera plan. At frame 97 (1.617s),
old pointer step was 17.73px vs new 27.71px, following the previous
27.41px step. At frames 98/99/100 the old path was
30.24/31.65/32.16px per frame versus 28.56/29.26/29.23px after fix.
The absolute speed discontinuity at the crossing dropped from
**9.68px/frame to 0.30px/frame**. New depth weight increases smoothly
from zero at frame 97 to fully H60 by frame 106, well before the
actual source Codex click. Re-rendered the exact Brimble HAR-derived,
brand-aware session with
`--preset 3d-launch --result-aware-editorial --no-webgl-optics`;
inspected genuine decoded frames 92/94/96/97/98/99/101/104/107
side-by-side with the previous master (including original-size frames).
Public comparison:
https://devmcp.davemafy.xyz/sauce-motion-phase2/cursor-depth-glide/cursor-plane-glide-before-after.jpg .
Public review:
https://devmcp.davemafy.xyz/sauce-motion-phase2/cursor-depth-glide/ .
Master:
https://devmcp.davemafy.xyz/sauce-motion-phase2/cursor-depth-glide/master-1080p60.mp4 .
Its SHA-256 from both worker and deployed copy is
`3cdd250c25ec0b411dba8bbe8a741c529748c4d508719bcf94e354391112715a`.
Old public release remains online.

**Checked:** 1920x1080 H.264 60fps, 314 frames / 5.233333s;
AAC stereo 48kHz, exactly 251,200 Foley samples (800/frame);
96 unchanged-source-sharp result-hold frames + 21 fade frames;
152 real H0/H60 frames, no single-plane fallbacks, action cut 125
unchanged. Full FFmpeg decode completed. Desktop player 1280x720
and mobile 390x844 both returned HTTP 200 and correctly seeked into
the transition at 1.68s; no page/media errors or horizontal overflow.
Test gates: 31/31 StudioMotion TypeScript, 174/174 Python unittest,
62/62 pytest, plus 13 nested subtests. Four new depth-specific tests
cover the exact Brimble entry, graceful exit, beat-cut reset,
determinism. No general independent-live-Chromium frame-hash
repeatability claim: this known separate limitation remains.

**Creative review:** The post-click glide no longer makes an unintended
3D jump; real trace speed still determines how quickly the cursor moves.
The pre-existing cropped terminal/wedge during early modal entrance
(~0.72–0.82s) is unrelated and remains unresolved. Do not call this
entire product film premium-approved on green tests alone.

## 2026-11-17 — Rejected 140ms cursor tween; preferred motion restored with one-frame repair

**User quality feedback:** The long CursorPlaneGlide from commit 2a0d4a8 was technically continuous but made cursor motion feel robotic. The owner preferred the older native spring cursor flight, except for a very thin glitch where it crossed into the modal. Passing mathematical continuity tests was not creative approval.

**Scoped correction on main:** The source mouse trajectory, spring, actual click timing, source DOM/H0/H60 planes, camera, cursor glyph, spotlight and Foley remain unchanged. Replaced the 140ms/8-frame depth glide with CursorPlaneSeamRepair in scripts/cursor_plane_motion.py. It uses the original projected H0 or H60 position on every frame except a single recorded-modal-boundary crossing frame. On that one frame only, the visual pointer hotspot is the midpoint of the exact H0/H60 projections; the following frame returns to the original target plane. Actual pointerdown frames always use their precise target-plane hotspot. Explicit editorial source-clock jumps >200ms reset directly. Private backup prior to edit: ../sauce-phase2-backups/2026-11-17-cursor-seam-narrow/.

**Real Brimble proof:** Frame 97 (1.617s) is the only cursor hotspot changed among the first 111 planned frames. Measured projected screen-frame displacement across frames 96/97/98 changed from 17.73/30.24 px per frame to 21.73/23.91 px per frame; movement before and after that single-frame correction matches the owner's preferred version. Inspected native decoded frames 94,96,97,98,99,100 from the original preferred, rejected long-tween, and new repaired full videos. Side-by-side:
https://devmcp.davemafy.xyz/sauce-motion-phase2/cursor-seam-minimal/cursor-preferred-rejected-revised.jpg .
Public review:
https://devmcp.davemafy.xyz/sauce-motion-phase2/cursor-seam-minimal/ .
Master:
https://devmcp.davemafy.xyz/sauce-motion-phase2/cursor-seam-minimal/master-1080p60.mp4 .
Worker/deployed SHA-256 equal:
3ac748be68a0bc52c562b05ae07e783ceaa798976b16f83153eb646e8dc6481e .
Previously approved and rejected proof URLs remain accessible, unchanged.

**Gates:** FFmpeg full decode passed; ffprobe H.264 1920x1080 at 60fps, 314 frames / 5.233333 seconds, AAC stereo 48kHz. Same 96 sharp result-hold frames, 21 fade frames, 251200 Foley samples, 152 actual H0/H60 frames, zero fallback and cut at frame 125. Public desktop 1280x720 and mobile 390x844 players each sought to 1.62s with no page/media errors or overflow. Regression tests: 31/31 TypeScript, 174/174 Python unittest, 62/62 pytest plus 13 nested subtests. Four targeted tests cover one-frame-only change, immediate restoration, pointerdown exactness, edit-cut reset and reproducibility.

**Limits:** The revised motion is available for the owner's subjective review, not yet premium approved. A separate pre-existing black terminal overlap at the start of modal entrance remains unresolved. Independent live-browser frame determinism is still a separate known limitation.

## 2026-11-17 — Replace the 1.6-second frozen Codex ending with a source-true payoff

**User's critique:** The previous 5.233-second Brimble film felt empty:
197 real-action frames were followed by 96 copies of one static frame and
21 fade frames. The clip was technically green but badly paced.

**Change:** Introduced opt-in `--result-payoff-push` (requires existing
`--result-aware-editorial`), implemented in
`scripts/result_payoff.py` and wired through
`scripts/session_replay.py` / `scripts/produce_cinematic_demo.py`.
The stage does not introduce a fictitious action, extra copied message,
new code or giant callout. It queries a real visible non-private source
result rectangle and the open dialog geometry at the verified end state.
Brimble's observed `pre` box was (487,471,334,52) CSS pixels in the
dialog (440,122,400,476). The focal shot zooms the **existing** H0/H60
compositor from 1.31x to 1.7554x, moves the focus toward (649.1,449.05),
reprojects the unaltered original DPR2 Chromium screenshot and modal-free
background at each frame via Lanczos4, and briefly fades the pointer
during the post-action dolly. This remains true elevated multi-plane
rendering, not zooming an encoded thumbnail or painting new UI.

**Actual editorial change:** The previously static 96-frame hold is
replaced with 8 original composition frames + 36 active camera-move
frames + 42 sharp *close-up* reading frames + 12 eased fade frames.
Thus 197+98 = **295 frames / 4.916667s**, compared with the former
314 / 5.233333s. The source action frame plan, original 180/24/1
spring, real cursor flight and one-frame H0/H60 seam correction,
frame-125 action cut and 152 genuine multi-plane frames are untouched.
Audio receipt: AAC stereo 48kHz, Foley WAV **236,000 samples = 295×800**
with four original event cues; no music or fake copy sound added.
The flat-tail version stays accessible. Non-result DOM flows fall back to
the conservative prior hold.

**Visual and technical verification:** Opened native encoded frame 250
at actual pixel resolution and read the genuine Codex command and
confirmation. Contact sheet shows the camera is actively reframing at
frames 209/218/227/236/241, settled and holding at 250/260/275,
then fading by 284/294. Mean pixel difference between source frame 196
and moving frame 218: 8.98/255 across the composition. Mean difference
between encoded locked close-up frames 250 and 275: ~0.00084/255.
The original browser text remains legible; no synthetic card or zoomed
low-res player pixels were introduced. Full FFmpeg decode passed;
`ffprobe`: H.264, **1920×1080, 60fps, 295 frames, 4.916667s**;
stereo AAC 48kHz. Exact master SHA-256:
`ef297669e8fc0c1599a59e35b7dcff5a662773ce63c99789585e18d19f6c9e9a`,
matching the independently installed public file.

**Proof:** https://devmcp.davemafy.xyz/sauce-motion-phase2/result-payoff-camera/
with master and contact/native source-backed close-up links in
`docs/result-aware-editorial.md`. Public page, master, contact and
native close-up returned HTTP 200; Chromium desktop 1280x720 and
mobile 390x844 both loaded, sought to 4.26s, and had no media error,
page error or horizontal overflow. The distinct downscaled preview
reported 4.933s; **do not confuse this with authoritative 1080p master
duration**.

**Tests:** Studio Motion 31/31; Python unittest 174/174; Phase 2/3
plus URL backend pytest 66/66, 13 nested subtests. Four new payoff
tests cover verified live Brimble HAR DOM result geometry, shot profile,
negative cases that may not fabricate output, and stable, sharp raw
frame output clock. No untracked footage, private HAR or session data
was committed.

**Limits:** The film still retains its real original 197-frame source
section (including some source idle around the result). The camera push
makes the added ending purposeful, but this is not a complete beat-level
re-edit of earlier source waiting. The previously documented brief
terminal overlap during initial modal entry and independent arbitrary
live Chromium replay nondeterminism remain separate issues. Creative
approval and broad generalized-quality validation are still outstanding.


## 2026-11-17 — Research-only launch-quality build contract (no renderer changes)

**Research artifact on main:** [docs/SAUCE_LAUNCH_RESEARCH_BRIEF.md](SAUCE_LAUNCH_RESEARCH_BRIEF.md), authored after checking the latest main repository, the separate URL pilot pipeline, primary Playwright/Screen Studio/OpenCV/OWASP documentation, and an independent live MP4 probe. This is a builder specification, not a film quality approval or claim of completed implementation.

**Independent proof inspected:** https://devmcp.davemafy.xyz/sauce-motion-phase2/result-payoff-camera/master-1080p60.mp4 — SHA256 `ef297669e8fc0c1599a59e35b7dcff5a662773ce63c99789585e18d19f6c9e9a` as fetched onto the existing Vultr workspace. `ffprobe` confirmed H.264 1920x1080/60fps, 295 frames/4.916667s and AAC 48kHz; full `ffmpeg -v error -xerror` decode passed. Actually opened the 12-panel encoded contact sheet, the frame-32–76 opening montage, and full-size frame 44 (0.733s), 48 (0.800s), and 250 (4.167s). **Frame 48 still has a gray rectangular overlap obscuring the right-hand portion of the genuine dialog.** Frame 250 has legible genuine Codex command but an offscreen-cropped dialog header and wrapped URL. The 42-frame reading hold may be too brief; this is a visual editorial hypothesis requiring A/B owner review, not a completed defect fix. The underlying original-vs-compositor root cause of the rectangle is not proven.

**Current server surface checked:** HTTPS `/sauce-app/studio`, `/sauce-app/studio/samples`, `/sauce-motion-phase2/result-payoff-camera/` and `/sauce-app/api/studio/url/auth` returned HTTP 200 on read-only probes. That does **not** prove a new end-to-end URL render in this research pass.

**Structural quality split:** Phase 2 flagship compositor is still distinct from active URL pilot `backend/live_capture.py` → `backend/live_render.py` (1280x720 DPR1 Playwright WebM with a circular in-page pointer, then upscaled to 1080p and resampled at 60fps). The real source video is authentic continuous motion, but resolution and editorial language do not yet equal flagship Phase 2. Pilot remains permission-gated. No code/tests were changed or re-run in this research-only pass. This milestone commits documentation only.

**Next builder sequence:** independently isolate and remove the exact modal entry occluder without inventing pixels → constrain payoff crop/hold to real result and context → benchmark genuine high-density URL source capture → unify the justified camera/pointer/editorial primitives while keeping video provenance distinctions → inspect three different public-site outputs with full film QA → invite-only beta gate. Each improvement must render, be visually compared against source and references, and record SHA/test/URL and remaining failures here. Do not reopen broad access or claim premium quality because HTTP/tests are green.


## 2026-11-17 — Persistent Sauce Steward installed and restart verified

**Request:** Preserve work across ChatGPT logout; leave the existing production services and dirty code untouched. Implemented a *bounded read-only verification supervisor*, not an autonomous AI coding agent. The latter requires separate model runtime/authorization, cost budget, and guardrails before unattended edits.

**GitHub source:** \`ops/sauce_steward.py\`, \`ops/systemd/sauce-steward.service\`, \`tests/test_sauce_steward.py\`, and \`docs/SAUCE_STEWARD.md\`, committed directly to main. Service code was installed root-owned at \`/usr/local/lib/sauce-steward/sauce_steward.py\`; the systemd unit is \`sauce-steward.service\`. The worker runs as unprivileged \`devmcp\` in a limited read-write state directory \`/var/lib/sauce-steward\`, with no AI API calls, public endpoint, automatic source edits, paid inference or release actions. It checks GitHub main every 10 minutes, periodically probes public Sauce URLs, records a daily full-decode check of the known 4.916667s reference MP4, and accepts only allowlisted queued jobs. A separate \`source-main\` checkout safely fast-forwards; existing \`/opt/sauce-vids\` is NOT reset, cleaned or modified.

**Live checks on Vultr:** \`systemctl is-active\` = active; \`systemctl is-enabled\` = enabled. Explicit \`systemctl restart sauce-steward.service\` succeeded and the persisted queued \`test-main\` job completed after restart. That bounded URL pilot suite passed **14 tests plus 13 subtests**. The initial \`sync-main\`, \`smoke-web\`, \`audit-proof\` jobs all completed. After the restart, the same three jobs completed again. HTTP checks passed for \`/sauce-app/studio\`, \`/sauce-app/studio/samples\`, and the Phase 2 proof page. Reference MP4 audited SHA-256 \`ef297669e8fc0c1599a59e35b7dcff5a662773ce63c99789585e18d19f6c9e9a\`, 295 frames/1920x1080/60fps, full FFmpeg decode; private diagnostic frame 48 retained. A separate clean checkout updated to commit \`05699df0a7dc6af11adc1c020ef2866c89dbac3d\`; seven dedicated steward unit tests passed. The pre-existing production checkout remained at \`d78dde2\` with 27 modified/untracked paths, preserved intentionally. Both \`sauce-studio.service\` and \`sauce-url2video.service\` remained active.

**Limitations:** A systemd-enabled service will run independent of ChatGPT login and restart with the host, but an actual machine reboot was not initiated to avoid disrupting the existing production workload. This is **persistent QA/monitoring infrastructure**, not a self-directed coding agent; it cannot independently repair modal occlusion or ship code. The known reference video remains visually flawed. Keep owner review mandatory and do not claim an autonomous builder or creative release signoff.


## 2026-11-17 — Unattended Sauce customer job value loop deployed (private pilot)

**User clarification:** "Keep running when I log out" means Sauce as an unattended business/product doing valuable work, not a coding-agent daemon or green uptime monitor. Implemented the highest-leverage bounded customer workflow: persistent independent URL jobs, safe restart behavior, device-local reopening of past films and private actual-output metrics. Design/ops details and limitations: [docs/SAUCE_OFFLINE_VALUE.md](SAUCE_OFFLINE_VALUE.md).

**Source committed to main:** \`backend/job_store.py\` adds fsync/atomic private job statuses, recovery of untouched queued jobs without repeat AI bills, honest terminal errors for interrupted in-progress jobs, and source-true repair of legacy successful output labels when the real video and release receipt exist. \`backend/sauce_api.py\` now loads those persisted records and reschedules untouched jobs. \`apps/web/app/studio/film-library.tsx\`, \`film-library.module.css\`, \`url-flow.tsx\` make up to 12 opaque job IDs available on the same device after the browser closes, with gated server lookups and support for authorized direct review links. \`ops/sauce_value_report.py\` plus \`ops/sauce_steward.py\` write hourly private aggregate evidence, without exposing job IDs or private URLs. Dedicated Python and Playwright regression coverage added.

**Deployment:** Versioned Next web build \`sauce-studio-offline-value-v2-20261117/apps/web\` selected using isolated systemd \`30-offline-value.conf\`; production backend only gained bounded \`sauce_api.py\`/\`job_store.py\` changes and original files were backed up under \`/var/lib/sauce-steward/deploy-backups/offline-value-20261117\`. All three existing services remain active; the original production Git worktree and untracked files were not reset. The separate steward source checkout is clean after moving ONLY our E2E test artifacts to private \`/var/lib/sauce-steward/qa-logs\` and unlinking our temporary \`node_modules\` symlink. No broad deployment, new authentication system or payments.

**Actual verification:** 35 Python tests plus 17 nested subtests passed, 13 frontend unit tests passed, Next TypeScript typecheck and optimized production build passed, and 6 real Chromium URL-flow tests passed (new one confirms finished film return after closing the tab). After live service restart, Studio and samples HTTPS returned 200 and unauthenticated job create returned 403. Verified \`GET\` status and MP4 bytes of a prior completed continuous film through the private Unix backend; verified all four existing continuous-film output records recovered truthful labels. On the actual public HTTPS Studio, pilot-authorized existing completed film opened at both desktop 1280×720 and mobile 390×844. Authenticated protected media returned 200; Chromium media reached readyState 4, \`video.play()\` succeeded and had error=0, with history visible and no overflow. Private captured QA images retained, not published. No paid inference call made during this QA.

**Initial private value report:** From 28 development/pilot job records: 15 ready-for-review (includes older still-state outputs), 9 failed, 4 require access; just **4** genuinely source-verified continuous films (28.3 seconds); **0 submitted quality ratings**. No verified paying customers, monetization, account-level retention or demand. Report refreshed hourly in \`/var/lib/sauce-steward/value-report.json\`. Do NOT equate all 15 ready jobs with premium clips, or 28 records with 28 customers.

**Remaining:** This is a reliable bounded product execution/return loop, not yet an automated cash-flow business. No paid checkout, customer acquisition, production tenant isolation, cross-device account library, email delivery or native high-resolution URL capture. Service restart does not safely resume work that may already have spent an AI call (terminates with honest error instead); no VM reboot was performed. Known Phase 2 modal occlusion/result crop persist. Next gate is three distinct premium-quality real-source demos, 5 genuine buyer reviews, and measured conversion before contemplating self-serve paid launch. Historical proof remains at https://devmcp.davemafy.xyz/sauce-motion-phase2/result-payoff-camera/ ; new customer-facing Studio is https://devmcp.davemafy.xyz/sauce-app/studio .


## 2026-11-17 — Real burst stress exposed backend socket failures; corrected and verified

**Full benchmark and safe replay:** [docs/SAUCE_STRESS_GATE.md](SAUCE_STRESS_GATE.md). Stress testing performed without opening real paid URL jobs or generating AI calls. The protected pilot and original production working tree were preserved.

**Pre-fix:** With only 12 simultaneous localhost clients on the *actual deployed* Sauce backend, 244 GET-only health/status/existing-video requests resulted in 13 failed Unix socket connections (6 status + 7 video; \`BlockingIOError\`); 100 health checks passed. The default Unix \`request_queue_size=5\` was insufficient for a brief parallel burst.

**Fix on GitHub main and deployed:** \`backend/sauce_api.py\` now sets \`PrivateUnixServer.request_queue_size=64\` and loopback TCP server backlog 64, without modifying the one-worker film queue, auth model, source truth or rendering. Previous file backed up under \`/var/lib/sauce-steward/deploy-backups/stress-20261117/\`; after zero live capture jobs were confirmed, the backend service was restarted. \`ops/stress_sauce_pilot.py\` is a bounded read-only harness; \`tests/test_sauce_pilot_stress.py\` protects its limits. Separately, \`tests/test_sauce_api_load.py\` verifies artificial admission concurrency with a fake no-network executor, not paid inference.

**Post-fix actual worker reads:** 12 clients/244 GETs, 24 clients/320 GETs, 32 clients/348 GETs, **zero failures in each**. Actual 32-client p95: status 21.17 ms; real stored-preview media 32.54 ms (VM-local, <=1.34 MB source videos). Private aggregate receipts \`/var/lib/sauce-steward/stress-{12,24,32}.json\`. The isolated 24-client admission exercise accepted two jobs and rejected 22 with 429; 200 synthetic status reads and 40 synthetic media reads passed; unauthenticated requests returned 401. Zero external site actions or inference. Full targeted suite: **40 Python tests passed plus 24 nested subtests**, service memory 26,943,488 bytes after load and all three Sauce services remained active. Studio HTTPS 200; unauthenticated public POST 403.

**Public edge nuance:** Default Python HTTP traffic hit edge error 1010; genuine Chromium pilot authentication and media requests succeeded. An authenticated eight-client Playwright probe returned HTTP 200 for 40 status and 10 media requests, but its status-body assertion used the wrong JSON wrapper; do NOT claim its entire assertion suite passed. This was a *test harness* problem, not independently verified API corruption.

**Still blocking broad launch:** Node media proxy buffers full MP4 and sends \`Accept-Ranges: none\`, so genuine byte-range streaming, seeks and low-network behavior remain untested/unimplemented. This burst test did not execute multiple real renders or quantify inference, CPU/disk capacity, authenticated multi-user isolation or revenue. Existing Phase 2 cinematic defects remain. **Invite-only pilot remains the launch boundary; no premium or production-scale traffic claim.**


## 2026-11-17 — Real Chromium + FFmpeg end-to-end stress, and production recorder recovery

**Benchmark/source/evidence:** [docs/SAUCE_REAL_RENDER_STRESS.md](SAUCE_REAL_RENDER_STRESS.md), \`ops/stress_sauce_render_pipeline.py\`, \`backend/live_capture.py\`, and \`tests/test_live_capture_env.py\`. The actual page was Sauce's public own sample studio, inspected independently with the source-true product explorer: \`https://devmcp.davemafy.xyz/sauce-app/studio/samples\`, real headings h0/h3, showcase-only and no invented product action. True separate Playwright Chromium recordings were fed into the actual \`backend.live_render\` production encoder, without AI direction calls, customer job POSTs, external-site interaction or paid inference. The test ran under unprivileged \`devmcp\` with resource guards, using the separate source-main checkout; original production work remains preserved.

**Failure found before first successful run:** Playwright video recording needed its \`ffmpeg-1013/ffmpeg-linux\` helper, but the service user's home lacked it. Shared \`/opt/devmcp-browsers/ffmpeg-1013/ffmpeg-linux\` existed; the backend service lacked an explicit Playwright browser cache environment. A first actual capture died at \`BrowserContext.new_page\`, although earlier mocked and GET-only tests were green. The existing missing-helper failure log was retained private. \`backend/live_capture.py\` now selects the already-installed shared helper only when an explicit operator path is absent; three regression tests added. Diff verification confirmed the original production source differed only by this helper; **only** \`/opt/sauce-vids/backend/live_capture.py\` was surgically updated after backing up its original to \`/var/lib/sauce-steward/deploy-backups/real-pipeline-20261117/\`. It had been an untracked file in the dirty production checkout; no other code/file reset, systemd restart or secret touched.

**Verified real render workload (8 vCPU, ~16 GiB VM):** One concurrent full job: **1/1** completed in **9.765 s**, peak total VM CPU **87.0%**. Two concurrent full jobs: **2/2** in **12.018 s**, peak CPU **97.7%**. Four concurrent full jobs: **4/4** in **17.799 s**, peak CPU **99.8%**. Minimum available system RAM across waves: 13,071.9, 12,358.1 and 11,055.2 MiB respectively. All seven staging jobs generated real continuous source WebM with matching SHA ledger plus 1920x1080 60fps masters. Four-job per-film encoder time rose to ~11 seconds versus 4.26 seconds for one job. **Full FFmpeg -xerror decode passed 8/8 masters** including an eighth real production-checkout capture+render with the browser cache environment unset; latter MP4 257 frames / 4.283 s / 1920x1080 60fps, production \`release.json\` source_verified/continuous_motion true. Three existing Sauce services stayed active. Focused follow-up tests: **14 passed, 15 nested subtests passed**.

**Actual frame inspection:** Opened a 0.3/1.2/2.3/3.6 s contact sheet from the final encoded *production-checkout* 1080p output; it depicts genuine Sauce sample-page panels with limited visual movement, no false product claims. This is a short, dense **performance fixture**, not visually premium footage. The public-URL recorder still starts with 1280x720 DPR1 WebM and resamples/upscales to 1080p/60fps; the 60fps container does not establish 60 unique source UI frames/s. Old Phase 2 modal rectangle and result-payoff crop remain unresolved. No Screen Studio-grade creative acceptance asserted.

**What is and is not proven:** Parallel isolated Chromium+FFmpeg production modules ran successfully for **1,2,4 simultaneous test jobs**; the deployed Sauce API still intentionally enforces \`ThreadPoolExecutor(max_workers=1)\` for real customer jobs. CPU saturation at two/four means this test does **not** justify raising concurrent paid workers. The tests did not stress 30–60s recordings, 100+MB videos, 4G packet loss, sustained load, VM reboot or real in-progress recovery. Do not mistake staged parallel job results for customer queue throughput or commercial demand. Keep invite-only pilot; next hard gates are real longer captures, bounded FFmpeg threads, streaming byte ranges, and customer-validated film craft.


## 2026-11-17 — 4 GB / 2-vCPU feasibility probe; no downsizing performed

**Owner hypothesis:** Replace the expensive shared 16 GiB/8-vCPU VPS with a cheaper 4 GiB instance to extend credit runway. Bounded zero-inference experiment on the existing Vultr VM, using a transient systemd cgroup scope (`MemoryMax=3G`, `CPUQuota=200%`) and `taskset -c 0,1`, preserving ~1 GiB in the hypothetical 4 GiB budget for OS/Studio/other services. This *only* constrains the test process, not the host and its other running applications.

**Verified outcome:** Production `backend.live_capture` → `backend.live_render` on a genuine Sauce-owned public sample page finished capture in **6.014s**, render in **8.349s**, total with stream probe/full decode **15.067s**. The actual master was **312 frames, 5.2s, 1920×1080 H.264 at 60fps**, source-verified, 0 paid inference calls, **473.6 MiB peak** render-scope memory, 0 swap and 0 OOM, no customer job POST. Private benchmark log/export `/var/lib/sauce-steward/qa-logs/render-4gb-simulation-20261117/`; full methodology [docs/SAUCE_REAL_RENDER_STRESS.md](SAUCE_REAL_RENDER_STRESS.md). All three production services remained active; no resize/reboot or other file mutations.

**Important limiting factor — storage:** Actual shared VM root disk is 328 GiB, with **79 GiB in use**; `/srv/devmcp-workspaces` alone ~38 GiB. A common Vultr regular shared-CPU 4 GiB/2-vCPU offering has **80 GiB disk**, which cannot safely host the complete current workload plus room for exports, backups and temporary renders. Do not discard other project data casually. Vultr states compute instances cannot directly downgrade with disk shrink: migrate selectively to a newly provisioned instance, cut over after a controlled test. Idle service cgroup memory was ~222 MB across API/Studio/steward, but other services and large web pages still require headroom. This test supports **plausibility for Sauce-only single short captures**, not general launch headroom or a full live VM move.

**Commercial caution:** `~$20/month` is an indicative regular shared-CPU 2vCPU/4GiB list price, subject to region, backups, reserved IPv4 and account terms. Promotional credits may expire. No authenticated balance/expiry check performed; **do not claim six months of coverage**. Next decision: choose whether to run a separate 4 GiB staging VM, then audit data migration/retention, test realistic long clips, and prove save/return/signed download on actual network and device before changing production.


## 2026-11-17 — Owner prioritization: saleable output first, runway protected

**Decision:** From here, optimize engineering for a credible first paying customer within **seven days after quality-approved launch**, while planning cash survival for **six months without revenue**. Neither outcome is guaranteed. The commercial priority has been added to [AGENTS.md](../AGENTS.md) so future coding agents do not revert to polishing infrastructure while known film defects persist.

**Read-only reality check:** Current live private `value-report.json` (generated 2026-11-17T21:51:09Z) recorded **44 development/pilot job records**, **24 `ready_for_review`** including older still-state outputs, **16 failed**, **4 real source-verified continuous outputs** totaling **28.3 seconds**, **0 submitted reviews**, and **no payments integration/revenue evidence**. Never treat these as 44 customers or 24 acceptable films. All three services active; the existing production checkout is dirty/behind main and must not be reset. No paid service, pricing, payment endpoint or outside outreach was initiated during this planning pass.

**Hard engineering order (do not reorder to chase easy green tests):**
1. Fix *actual encoded film pixels*: Brimble gray modal occluder at master frame 48 (~0.80s) and clipped payoff at frame ~250 (~4.17s); re-render and inspect at full resolution + desktop/mobile playback against selected references. Remaining cursor movement should not regress.
2. Lift the continuous public-URL output from DPR1 1280×720 source upscale and circular pointer to source-true, legible, premium narrative language. Create **three distinct** visually reviewed landscape software films and document each one's meaningful action/result, source provenance, camera/hold quality and gaps. Do not present a marketing-only site tour as an authenticated product demo.
3. Only after those samples are actually worth showing: assemble a **limited paid pilot** with one clear customer outcome, honest pricing/proof, protected downloads, low-friction manual or hosted legitimate payment method, bounded queue/usage and opt-in feedback. Avoid building an elaborate billing engine or open registration before demand. First-week target: **one genuine paying buyer**, not simulated job count.
4. Runway: hold one production render worker, avoid speculative GPU/inference expenditure or a full 16GB→4GB VM migration before longer 30–60s render tests, 4G playback and disk-preserving Sauce-only deployment assessment. Keep six-month no-revenue scenario in cost decisions.

**Stop rule:** No new dashboards, general agent orchestration, design systems, growth automation or stress-test loops unless they remove a measured blocker on the path to accepted footage, first sale or cost survival. The next executable deliverable is **one approved real Brimble film**, not another status page.



## 2026-11-17 — Saleable-film P0: Brimble native modal glitch removed in a source-true review cut

**Commercial objective carried forward:** Aim for one genuine paying customer within seven days **after** a quality-approved launch, while containing fixed costs to survive six months without revenue. This pass addressed **encoded film quality first**, not growth tools, accounts, billing, more load tests, a VM resize or unapproved customer outreach.

**Actual original artifact inspected:** https://devmcp.davemafy.xyz/sauce-motion-phase2/result-payoff-camera/master-1080p60.mp4 (295 frames/4.9167 s). Source-true HAR-derived Brimble capture at private \`.../sauce-v05-release/studio/.tmp/brimble-reference-v16-ink\`; full replay re-rendered using current main, \`--preset 3d-launch --result-aware-editorial --result-payoff-push --no-webgl-optics --seconds 4.2 --presentation-hide-selector 'img[src*="bee-cutout"]' --deterministic-frame-cache\`, with no inference. Original Chromium raw screenshot cache created for 197 action frames. **Proven root cause:** the gray right-hand rectangle is already in *raw Chromium source*, not newly drawn by the compositor. The public modal animates its opacity over the dark terminal. Pixel at CSS (740,260) over that real terminal moved from RGB (136,139,141) at source frame 47 to RGB (244,246,246) at frame 55 and (245,247,247) by 57; the recorded first pointerdown occurred at 0.7859s (~frame 47). The older video emphasized this native 0.15s translucency; we did **not** paint over it, clone fictitious dialogs, or alter the site DOM.

**Pixel-level/source-true improvements in main:**
- \`scripts/result_payoff.py\` uses observed dialog-heading-to-result bounds to cap its close-up camera scale and re-center the **actual** foreground modal pixels, rather than zooming the command until the dialog header disappears. Source geometry target CSS x487/y471/w334/h52 in dialog x440/y122/w400/h476. A 32px safe margin in the native 832px stage determines the maximum zoom. End frame now keeps authentic “Connect your agent” heading and Codex command readable. The sharp command-reading hold grew from **42 frames / 0.7 s** to **66 frames / 1.1 s**. New source-true base master 319 frames / 5.3167 s, 1920×1080/60fps H.264 + 48k AAC. \`tests/phase2/test_result_payoff.py\` updated for header/result framing and longer hold.
- \`scripts/source_true_reveal_cut.py\` applies a **bounded, opt-in source-backed editorial cut**, only after verifying an actual pointerdown at the selected first frame in the original Sauce session. Brimble proof drops **source frames 47–55**, bringing the **actual settled source frame 56** forward. The underlying DOM interaction was truly recorded; source frames before and after the cut are still the genuine compositor output, not synthetic screenshots. The original 319-frame H.264 movie is preserved privately; the separate review cut is re-encoded at CRF16 with new frame-accurate 48k AAC and no new UI content. First audio splice attempt cut the click decay; corrected algorithm retains **five recorded audio frames after pointerdown**, then removes an equal nine-frame audio interval before resuming the matching source clock. Actual first-click PCM amplitude before/after: **0.2597 → 0.2600** peak; second click **0.2605 → 0.2568**. No synthetic sound or new Foley generated. \`tests/phase2/test_source_true_reveal_cut.py\` covers click provenance, 12-frame maximum, bad cut rejection and 800-sample clock.
- Resulting review master: **310 frames / 5.166667 s**, H.264 1920×1080 at 60fps, AAC at 48 kHz. Final SHA256 \`96c9a4a31196b3cb9ac412f30f92a24fcd81736f8cf20a8e8f09467d5779a8e9\`, equal on private worker and public host. Full FFmpeg \`-xerror\` decode passed and actual 1280×720/30fps preview produced with retained audio. Inspected before/after encoded frame pairs 42,46,47,48,50,56,100 and payoff 250; verified no mid-gray terminal overlap at the new frame 47 while the original preferred cursor path outside those removed frames remains.
- **Public, distinct review URL (not a commercial launch):** https://devmcp.davemafy.xyz/sauce-motion-phase2/launch-quality-review-20261117/ ; master https://devmcp.davemafy.xyz/sauce-motion-phase2/launch-quality-review-20261117/master-1080p60.mp4 . Original public proof and prior baseline remain untouched. Reviewer page explicitly marks “not quality approved”; no ads, checkout, registration or external claims. Actual public HTTP 200 for index, master, preview and poster. Real public HTTPS Chromium at **1280×720** and **390×844** both loaded, played and sought to 4.15s; \`readyState=4\`, duration 5.166667s, no media error, page JS error or horizontal overflow. Private screenshots saved \`/var/lib/sauce-steward/qa-logs/launch-quality-20261117/public-proof-{desktop,mobile}.png\`.
- Full \`tests/phase2/\` suite: **49 passed, 10 skipped** (the optional live/HAR browser tests skip in a clean checkout), with the actual complete source-backed browser rerender independently executed successfully. All three existing Sauce services remain active; isolated source-main checkout clean after tests, production dirty worktree preserved. Zero AI direction calls, new customer capture jobs, purchases, sign-ins, VM changes or email outreach.

**Creative gate remains open:** The new nine-frame jump cut is an *editorial candidate*; owner's subjective review must confirm it feels intentional rather than abrupt. The command text remains small when viewed on a phone, and bottom-of-dialog footer is deliberately less prominent than the actual heading/command. This is **one** public UI source-backed film, not three distinct approved product workflows and not an automated arbitrary-site guarantee. The live public URL pipeline remains separate and lower-fidelity (1280×720 DPR1 upscaled 1080p and circular pointer), not premium-director quality yet. No paying customers or validated conversion. Next decisive work is reviewing this actual cut with the owner, improving general continuous URL footage and producing two **different** source-true, meaningfully interactive, human-acceptable demos before a tightly bounded paid pilot. Do not call it shipped as a premium commercial product.


## 2026-11-17 — Saleability-first Phase 2 Brimble: real opacity-overlap defect corrected in a review candidate

**Owner's commercial filter:** One *genuine* paying buyer within seven days **after** quality-approved launch, and runway planned for six months with zero revenue. This pass attacked the known flagship **P0 film pixels**, rather than billing dashboards or additional capacity. **No payments, external outreach, paid AI calls or general launch were initiated.** Existing dirty production checkout \`/opt/sauce-vids\` and all three running services were preserved; source and tests were committed to current GitHub **main only**. Private isolated source checkout remained clean.

**Root cause independently established in actual pinned Chromium source:** Existing published reference \`https://devmcp.davemafy.xyz/sauce-motion-phase2/result-payoff-camera/master-1080p60.mp4\` SHA256 \`ef297669e8fc0c1599a59e35b7dcff5a662773ce63c99789585e18d19f6c9e9a\`, 295 frames at 1080p60. Frame 48/0.800s has a gray rectangle over the right-hand side of the visible Connect your agent modal. Using the existing private pinned Brimble HAR/6-state session, the real dialog was observed at CSS box x440,y180,w400,h360, with a **separate dark decorative terminal behind it** x690,y223.625,w460,h273.5. Exact source-frame replay found the dialog's genuine opening CSS opacity: frame47 **0.452733**, frame48 **0.721089**, frame49 **0.856464**, frame50 **0.923367**, frame52 **0.982148**, frame54 **0.99731**. The dark terminal shows through the partially translucent real dialog. The H60 two-plane compositor had **not yet engaged** at frame48 (frame-plan foregroundId none / spotlight false). This corrects the earlier unproven hypothesis that the gray defect originated in the compositing matte.

**Minimal reversible editorial correction:** \`scripts/modal_depth_capture.py\` now offers \`stabilized_verified_dialog_opening\`, called from \`scripts/session_replay.py\` only for the verified Brimble dialog during opted-in presentation frames. It checks unique live dialog bounds, a unique DOM-verified decorative terminal with exact geometry/class/background and an opacity between .25 and .995. For that specific captured source frame, the real Chromium dialog's CSS opacity is temporarily made 1, preserving its actual browser text, size, layout and controls; the previous inline opacity declaration/priority is restored in a \`finally\` path even on screenshot failure. **This is a documented presentation-only fade edit, not byte-identical untouched website footage**; raw underlying session/HAR remains unchanged, and no fictional interface, fabricated state, pixel inpainting or cursor movement is introduced. Raster-cache identity was updated to avoid stale source pixels. Main commits \`07ac884\`, \`f691d1d\`, \`d5a8995\`. Concurrent main commits already delivered a separate payoff crop/hold improvement (\`0711e97\`/\`25765bd\`); this render incorporates that source rather than overwriting it. A separate optional frame-accurate \`source_true_reveal_cut.py\` landed on main subsequently; it was **not applied** to this review candidate.

**Actually re-encoded and pixel reviewed:** Using the exact existing 6-state Brimble fixture, the current-main \`scripts/produce_cinematic_demo.py\` and \`3d-launch --result-aware-editorial --result-payoff-push\`, rendered an independent candidate without touching the previous proof. Private work: \`/var/lib/sauce-steward/qa-logs/film-quality-20261117/\`. Candidate master \`319 frames / 5.316667s / 1920×1080 H.264 60fps + AAC 48kHz\`, SHA256 \`8d4259ff29a3fd4980fb3457ed884ed850de17d4c1e3640deb1b8903550d3ac5\`; full FFmpeg \`-xerror\` decode passed. Release receipt confirms 6 verified source states, real two click actions, 152 multi-plane frames, action cut still at 125, plus \`stabilized_opening_frames=7\` in the private replay report. Direct encoded baseline/candidate comparison at f48: modal-overlap ROI mean luminance **184.4 → 234.4**, with f47 **138.4 → 234.8**. By f54 the ROI is essentially unchanged, and only f47–f48 exceed **1.4/255 full-frame MAE** in the opening's original 197 action frames. Actual f250 rendered image now includes the source's “Connect your agent” header, the Codex row and genuine naturally wrapped command, unlike the earlier clipped header. Result payoff receipt: **36 camera-move frames, 74 total anticipation+read hold frames, 12 fade frames**; total 122 appended frames. No claim of artistic perfection: editorial hold and source fidelity still require owner viewing.

**Public, safe review-only URL (verified actually serving new bytes):**
- https://devmcp.davemafy.xyz/sauce-motion-phase2/brimble-quality-review-20261117/
- https://devmcp.davemafy.xyz/sauce-motion-phase2/brimble-quality-review-20261117/master-1080p60.mp4

Only safe player, H.264 master, 720p preview and poster were placed in the distinct static review directory; private HAR, source session, screenshots, receipts and logs remain private. All four safe files received HTTP **200**, public master checksum matched private output exactly. Real Chromium on that URL played actual preview at **1280×720 desktop and 390×844 mobile**, video \`readyState=4\`, \`play()\` succeeded, \`video.error=null\`, and **no page horizontal overflow** at either viewport. Private QA screenshots retained. Phase 2 focused tests: **25 passed, 1 intentionally skipped** (real HAR browser fixture test separately exercised with manual pinned replay and visual A/B). Systemd job finished successfully and shut down; all three existing Sauce services stayed active. Production API and public Studio customer-facing URL pipeline were not changed by this film-only pass.

**Commercial/quality judgment:** P0 gray intrusion and P1 payoff clipping visibly improve **this one Brimble showcase film**. The 5.3-second sample is **a review candidate only**, not independently quality-approved or evidence of a sale. It does not solve the separate **public URL engine's DPR1 1280×720 → upscaled 1080p, circular cursor, generic showcase scroll, or weak shot direction**. Three distinct usable software films, buyer-aligned footage value, protected customer ownership/usage and a legitimate paid pilot remain gates before broadened launch. Continue with a second, distinct real public software interaction and native source-resolution/editorial uplift; protect one-worker budget and do not claim six-month credit runway until credit expiry/balance verified.


## 2026-11-17 — Opt-in genuine 1080p URL capture investigated; padding trap fixed, not promoted to customer default

**Priority and scope:** Follow the 7-day-first-paid-buyer/6-month-runway decision in AGENTS.md; quality-first, single-worker private pilot. This is a limited **source-quality experiment** undertaken after the improved Brimble paid-launch review candidate. No money, migration, external outreach, new paid inference, public signups or production URL-engine switch occurred.

**Source change on GitHub main only:** \`backend/live_capture.py\` now accepts \`SAUCE_CAPTURE_QUALITY=high\` (otherwise \`standard\` unchanged). In high mode Chromium records a **real CSS viewport 1920×1080 at DPR2**, and writes 1920×1080 continuous WebM instead of the old 1280×720 DPR1 source. It also allows \`SAUCE_CAPTURE_CURSOR=arrow\` as an explicit opt-in SVG pointer driven by real mouse events, while legacy circular pointer remains the default. \`backend/live_render.py\` validates the source receipt (recorded dimensions, DPR, *actual viewport geometry*) and encodes verified 1920×1080 source **without spatial upscaling**, while still supporting and truthfully labeling legacy 720p-to-1080p conversions. Source receipts distinguish \`source_dpr\`, \`requested_video_size\`, \`viewport_css_size\`, \`presentation_cursor\`; release receipts include source dimensions/fps and \`native_1080p_source\`. \`tests/test_native_source_capture.py\` covers opt-in, default backward compatibility, false high-resolution claims and missing/wrong viewport.

**A real quality failure detected, not hidden:** An initial Chromium DPR2 experiment produced a file probed as 1920×1080, but because the **CSS viewport remained 1280×720** the real UI occupied just the upper-left 1280×720 area and the remainder was blank *Playwright recording padding*. The data receipt had been misleading. An actual old-versus-new decoded-frame comparison exposed this; file dimensions and 60fps transcode alone were not sufficient proof. A separate Playwright proof with 1920px CSS viewport showed full-frame recording is possible. High mode was corrected to use \`viewport={'width':1920,'height':1080}\`, not just \`record_video_size\`. The renderer now **rejects** 1920×1080 source recordings whose receipt shows a smaller/missing CSS viewport; dedicated negative tests lock out this false positive.

**Fresh verified actual source:** Isolated on-Vultr run against Sauce-owned public URL \`https://devmcp.davemafy.xyz/sauce-app/studio/samples\`, read-only showcase of real observed page headings (not an authenticated product demo): actual 1920×1080 WebM, DPR2, CSS viewport1920×1080, opt-in genuine semantic arrow, source WebM stream \`r_frame_rate=25/1\`, SHA-verified capture + release. Verified resulting master 1920×1080 H264 **423 frames / 7.05 s** in 60fps container, complete FFmpeg \`-xerror\` decode passed. Important: the input captures **25fps actual source**; 60fps is an output resample, not 60 distinct source animation frames. Opened actual encoded comparison frame pairs at 1.5s and 3s: corrected full-frame image contains real web content across the viewport rather than Playwright gray/blank padding. It has considerable **genuine site whitespace**, with small text/limited cinematic motion; this is still a performance/quality fixture, **not** a premium film or external buyer sample. Private evidence/logs at \`/var/lib/sauce-steward/qa-logs/launch-quality-20261117/high-res-url-arrow-fullframe/\`, pre-fix padded vs corrected comparison \`recording-fix-before-after.jpg\`, native source evidence retained privately.

**Engineering gates:** \`83 passed, 10 skipped, 13 nested subtests\` from focused native capture, video recorder, product explorer, backend URL and full Phase 2 pytest suites; actual browser capture+render executed independently, master fully decoded. All 3 existing Sauce services remained active. GitHub main clean isolated checkout; production dirty checkout preserved. Brimble review proof still HTTPS200: \`https://devmcp.davemafy.xyz/sauce-motion-phase2/launch-quality-review-20261117/\`.

**Not yet commercial acceptance:** The corrected high mode was **not deployed into or enabled on the live customer API**. The Playwright recorder remains 25fps, and a literal 1920px layout may show more source-page whitespace than a directed shot; the 4GiB/2-vCPU cost case was verified only for one short 720p sample. Extra source pixels do not, by themselves, create editorial direction, readable result holds or willingness to pay. Next: subjective review of the Brimble candidate; then produce two more distinct genuine product-action films with actual cinematic direction and approval. Only after the outputs are saleable should Sauce expose a bounded paid pilot and seek a genuine first customer. Do not present native DPR2 as a premium-quality certificate or quietly broaden access.


## 2026-11-17 — Linear: second-site action-first source-true review film (not commercial approval)

**Commercial focus:** Continue toward one paying buyer after a quality-approved launch, without exposing unfinished footage or rebuilding finished infrastructure. At kickoff, current GitHub main already contained verified Brimble modal-overlap and payoff improvements (public [Brimble review](https://devmcp.davemafy.xyz/sauce-motion-phase2/brimble-quality-review-20261117/)), plus an isolated native-source URL experiment. Those were **preserved, not reimplemented**. The existing live URL pilot remains on its prior defaults and single-worker executor; three services remained active.

**Next gap actually executed:** Reuse the established real, 12-second 60fps continuous Chromium/X11 recording of **Linear's official public interactive marketing preview**, with its pinned two real clicks and independently observed DOM changes. This is **not an authenticated Linear workspace**. Source SHA256 \`0e6a864365f91e7931565454c1b0ad9f98d9a78b77c0f49ac7b849321f58be69\`, original real source 1320×720 60fps. The previous reference-study \`screenstudio\` camera was at 1.16× before click 1 and 1.20× before click 2, contrary to the owner's action-following direction preference.

**Main-only scoped source:** Added opt-in \`action-first\` profile in \`scripts/autozoom_event_planner.py\` and \`scripts/render_event_video.py\`, preserving default and existing Screen Studio study behavior. It refuses to zoom without a **real** click, within-window observed DOM state change and visible result box, nonempty evidence, plus actual \`interaction_complete\` event. It waits through the actual result, moves to source-derived focus, holds legibly, then releases. Observed clicks: 2.238s and 6.3612s; results: 2.5871s and 6.6551s; new pushes start only at **2.6471s and 6.7151s**, settle at **3.3671s and 7.4351s**, 1.62×, return wide by 5.6301s and 10.3601s. \`tests/test_autozoom_event_planner.py\` adds absence-of-evidence and action-order regressions. Tests **14/14** focused, **34/34** combined with native source recorder tests.

**Actual encoded output and proof:** [Linear action-first review player](https://devmcp.davemafy.xyz/sauce-motion-phase2/linear-action-first-review-20261117/) and [exact 1080p master](https://devmcp.davemafy.xyz/sauce-motion-phase2/linear-action-first-review-20261117/master-1080p60.mp4), **1920×1080 H.264 / 60fps / 720 frames / 12.0 seconds**, master SHA256 \`9414f4507332017ea2d86ca1f6c73e189c3ee5ba86bfaa3fd73b2a5fad734e86\` matched private and public files. Full FFmpeg \`-xerror\` decode passed. Inspected actual old/new encoded frame contacts at 2.4/2.8/3.55/6.5/7.0/8.2s and native output close-ups at 3.8/8.2s: click/result established before new camera movement; real code review and task body still present, but dense and sourced from a 720px-original capture. Player and all safe assets served HTTPS200. Live Chromium desktop 1280×720 and mobile 390×844 playback succeeded (\`readyState=4\`, media error null, elapsed playback >0.8s, no horizontal overflow), QA images private.

**Private evidence:** \`/var/lib/sauce-steward/qa-logs/new-buyer-quality-20261117/\` contains source comparison/encoded stills, source-grounded camera-plan, logs, safe media. Only self-created player, preview, poster and new master were published in the isolated new static review directory. No customer job was posted, no paid inference, sign-in, outreach or server resize. GitHub source checkout clean, production dirty checkout unreset.

**Honest status:** Second **review candidate**, not second approved premium film. Linear's recording is a public marketing-site interactive preview and an older 1320×720 source, so 1080p output is resampled; code/text density, absence of narration and editorial polish still need owner review. Brimble remains a first review candidate. **Next gate:** one newly captured *genuinely usable software workflow* at sharp native resolution with source-grounded result camera, plus owner visual evaluation across three distinct examples. Don't build checkout or mass-promote until outputs are worth paying for. Complete source and comparison details: [docs/SAUCE_LINEAR_ACTION_FIRST.md](SAUCE_LINEAR_ACTION_FIRST.md).


## 2026-11-18 — Brimble engine visual exploration

Recovered the existing Vultr worker. Its `sauce-v05-release` checkout was dirty, so the experiments ran in an isolated main-only checkout of `fac61c78afc0a892feb0bb25e2d9f664edddb1c5`. Both renders used the pinned six-state Brimble Chromium session at DPR2. The [published 3D Launch master](https://devmcp.davemafy.xyz/sauce-motion-phase2/brimble-quality-review-20261117/master-1080p60.mp4) matched its documented checksum and decoded in full.

- **Clean Studio**, existing preset, 252 frames / 4.2s, master SHA256 `d662d2865d1c5aac29e31df722abc60d5b2c933a0ec02b7fd832dca00adb3fd9`. The subdued stage helps. The wider late frame makes the command harder to read.
- **3D Launch with Obsidian**, isolated material-only override with the existing result push and hold, 319 frames / 5.316667s, master SHA256 `892dbcb10726cbe9fc4a2739cd01f98f0b554dd71d69df7eb9b17486accf5b40`. The wrapper's preset/material consistency check rejected formal export after encoding the video and before Foley mux. The resulting silent video was independently fully decoded and used only for visual review. Both review files played in Chromium at 1280×720 desktop and 390×844 mobile without media errors or horizontal overflow. Worker evidence is in `sauce-visual-lab-20261118/studio/.tmp/visual-lab/`.

Opened encoded frames at opening, dialog reveal (f48), pointer handoff (f97), command reveal (f125), and late result (f245–250). Compared with the private Screen Studio product reference and the owner's Connect your agent stills. The quiet stage improves the opening, and 3D Launch holds the actual command at a larger scale. The opening subject is still small, the gray backing plate reads as a large rectangle, and phone-size command readability is unapproved. The next camera experiment is a tighter action-led composition with a hold on the real Codex command and less backing plate in frame. No production render settings or published films were changed.

## 2026-11-18 — Signature effects reference review

Reviewed the encoded Brimble quality-review master again from the published URL above. SHA-256 matched `8d4259ff29a3fd4980fb3457ed884ed850de17d4c1e3640deb1b8903550d3ac5` and a full FFmpeg `-xerror` decode passed. Encoded frames at 0.5 s, 1.0 s and 4.5 s show a small opening target, a persistent gray backing plate and a larger result that still uses much of the composition for surrounding UI. Local release HEAD `5e32cde` is dirty and was preserved. Remote main at review was `db62aab`.

First visual candidate: action-locked result reveal. At the observed Codex expansion, use a match cut anchored to the Codex row, changing to a close composition that includes the modal title, full command and Copy affordance. Reduce surrounding backing plate through framing. Keep the settle sharp and hold for reading. Compare the same source state against the baseline in 16:9 and at phone feed size, then test the mechanism against the real inventory filter result. Figma Slides supplies the close-up/editing reference, Ordinary Folk's Webflow film supplies the 2D/3D staging reference, and Screen Studio supplies the movement-specific blur baseline. Research and encoded baseline review only. Candidate footage and visual acceptance are pending.


## 2026-11-18 — Directional light and anchored match-cut studies

Ran two isolated experiments on the existing Vultr worker using main at `db62aabe20b74ac6cfc6a44cf76d7a4839f3d746`. The production checkout and published proofs were preserved. Experiment files and receipts are in `sauce-effects-20261118/studio/.tmp/effects/`; relighting source changes live only in the isolated checkout.

- [Brimble directional light](https://chatgpt.com/library?file_id=libfile_b6309edbc5908191af319a58f8546aff&account_id=personal). The opt-in H60 pass derives a narrow exterior glint from the gradient of the actual projected rounded mask, and biases the H0 cast shadow from the same tilt-dependent direction. The existing verified six-state source, camera, command payoff and 48 kHz Foley were retained. Decoded H.264 master: 1920×1080/60, 319 frames, 5.316667 s, SHA256 `f6a79f923c9aca7db6425c4f03694dc8c91d3c83474561d91ed2baac354956eb`. Inspected frames 54/97/125/246 and a detailed crop of f125. The glint is too subtle against the pale dialog and gray backing to carry the shot by itself.
- [OpenSheets match cut](https://chatgpt.com/library?file_id=libfile_468316e305248191aa638602148cb010&account_id=personal). Reused the recorded Chromium/X11 OpenSheets currency-formatting action as the available real table workflow. The capture manifest proves five formatted cells, and actual source frame 308 is the first decoded frame with dollar amounts. At output frame 150, a 1.39× crop anchored to the amount range preserves all four column labels and holds the result for roughly 2 s. The table remains small on a phone. This is a silent, controlled editorial prototype with a visually verified reveal frame. Master: H.264 1920×1080/60, 268 frames, 4.466667 s, SHA256 `fe838afb974a133e178ec036374b5f4c2ebd02a19682e8b29b3cb1dba09c024c`.

[Encoded-frame comparison](https://chatgpt.com/library?file_id=libfile_e0963df51270819190a4811343cbd628&account_id=personal). Fully decoded both masters and played both previews in Chromium at 1280×720 and 390×844 without playback errors or horizontal overflow. Phase 2 tests: 25 passed, 1 skipped. Pixel probe at two angles confirmed deterministic changes outside the fully opaque foreground and exact equality inside it. Compared the experiments with the earlier GMUNK layer and Stripe Treasury transition references. Advance the anchored cut into a reusable shot rule once it can keep text legible at phone size; keep directional lighting experimental pending a stronger visible result. Production renderer and defaults were left as deployed.

### Figma-led OpenSheets editorial study

Owner selected Figma Slides as the primary reference and passed on Webflow’s abstract staging for this direction. Recut the existing OpenSheets review MP4 as a 4.07s landscape study. Trimmed the first 24 frames, punched in on the actual range selection and toolbar, and kept the cut on source frame 150 (now 2.10s) and the genuine dollar-formatted result. Full FFmpeg decode passed and inspected half-second samples across both shots. The edit uses a previously encoded 720p review source; the toolbar is still small and the grid still has excess negative space. This is a review experiment outside the runtime. A native-source two-shot planner should frame the control and anchor the shared result column through the cut. [Review MP4](https://chatgpt.com/library?file_id=libfile_87096139da2c8191a07b7880b44a1245&account_id=personal).

## 2026-11-18 — High-effort signature UI-effects research + source-true OpenSheets result-lift proof

**Scope:** Read current GitHub main governing docs and inspected the existing Vultr Phase 2 rendered Brimble/OpenSheets frame contacts. Recovered persistent DevMCP, with original release worktree (171+ uncommitted entries), prior effects experiment and all proofs preserved. A fresh **main-only isolated checkout** `sauce-high-effort-main` was used for this experiment; no changes to production compositor, preset defaults, services, capture API, billing or infrastructure. Research and technical contract added in [docs/SAUCE_SIGNATURE_EFFECTS_RESEARCH.md](SAUCE_SIGNATURE_EFFECTS_RESEARCH.md).

**Reference-driven finding:** Current H0/H60 depth, camera, result payoff and Foley already work as a narrow technical baseline; inventing more materials will not fix undersized heroes, gray backing plate, or phone-size result readability. Studied official Figma 3D-transforms composition case study (2026-11-12), Figma Slides screen-led launch film, Codrops persistent WebGPU/DOM-bound transitions and Atelier UI, and Ordinary Folk/Webflow as a motion/art-direction reference only. Highest-value unproved signature system is evidence-anchored **persistent UI region identity and spatial handoff**, with background optics subordinate to real source pixels.

**Actual visual study on real MIT OpenSheets source:** Existing authentic 1600x900/60 X11 Chrome recording SHA256 `69800f09767840b54334d09f6006ad4c53c3edd519a9ea27a4460aae540c8eca`; genuine currency formatting click t=4.9487s, observed changed result t=4.9755s and verified result rectangle CSS x1200/y223/w193/h109. Built a separate *scratch-only* `studio/.tmp/effects-lab/study.py` rendering full-width real context then promoting a crop from genuine settled frame 330 to a large reading plane. First draft inadvertently included a pointer cross from source frame 535; checked real source frames and corrected to the cursor-free original frame 330, **not** an invented retouched cursor. The crop shows all five authentic formatted amounts. No fake UI, typed replacement or custom Foley.

**Verified deliverable:** [public isolated visual study](https://devmcp.davemafy.xyz/sauce-motion-phase2/semantic-result-lift-study-20261118/) and [MP4 master](https://devmcp.davemafy.xyz/sauce-motion-phase2/semantic-result-lift-study-20261118/master-1080p60.mp4). SHA256 `3a10c4813f331ff37a35f8c18e3002698c29540ca4cf7bdd30cbe1dbd8fc8d39`, 1920x1080 H.264 60fps, **267 frames/4.45s silent**. Full FFmpeg `-xerror` decode passed. Opened real encoded montage, a native full-frame and 390px downscale: numbers markedly larger but native source low resolution remains visible. Live HTTPS page/video/poster return HTTP 200. Chromium Playwright at **1280x720** and **390x844** on the public review page achieved `readyState=4`, `video.error=null`, `duration=4.45`, currentTime progressing, no JS errors or page overflow. Only safe player/poster/MP4 published, private source recording and capture metadata remain on worker. No new compute spend.

**Creative gate remains OPEN:** This is an isolated source-true compositing feasibility proof, not integrated preset or cinematic-quality approval. Current motion begins with a hard cut into a detached rectangular crop; shot choreography and source-resolution crispness need improvement, and the dimmed spreadsheet context is still visually bland. Next gate: add DOM-identity-verified common-element continuity on **Brimble and a second workflow**, keep one pointer and source UI pixels, use effective safe scaling and native sharp capture, compare entire actual encoded videos at desktop and 390px width, secure owner review. Do not build a shader catalogue or release default effects prematurely.

## 2026-11-18 — Evidence-triggered dialog lift integrated into 3D Launch

Engine commit `21983cae875de8cfa6c13ec84e6e777c9fa6e89c` on main. `scripts/produce_cinematic_demo.py --preset 3d-launch --modal-lift` enables the lift in the actual replay compositor. A verified modal and a clean underlying browser plate unlock a 300ms eased move from H0 to H60. The rounded dialog matte, projected pointer, cast shadow and background defocus share that output-frame timing. The existing single-plane fallback covers shots without verified isolation. The new setting is opt-in. Recovered the existing Vultr host, fast-forwarded a fresh isolated checkout from `316c84e`, and preserved the dirty release tree and other experiments.

Rendered the pinned six-state Brimble fixture with result-aware editorial, result payoff push and WebGL optics off. The receipt reports 18 transition frames and 152 verified multi-plane frames with zero attempted isolation fallbacks. Master: 319 frames / 5.316667s, 1920×1080/60 H.264 with 48kHz AAC, SHA-256 `9cfa9f6af19adb12ed39d395c4e69a0cc004084dc9df131f2ed21a37deea0849`. Full FFmpeg decode passed and public master checksum matched. Verified Chromium playback and no horizontal overflow at 1280×720 and 390×844. Phase 2 suite before the added projection test: 59 passed, 10 skipped. Final targeted multi-plane and cursor suite: 17 passed, including exact opaque source pixels at intermediate depths.

Compared decoded frames 48, 54, 60 and 66 with the prior Brimble review master. The initial background is more readable, then the shadow and focus build around the dialog. This comparison retains existing editorial camera motion and the two exports have different stage color. The depth change is restrained and the wide, gray backing plate still dominates at small sizes. This is not a controlled fixed-camera A/B or visual approval. Generalization to a second genuine dialog workflow remains unverified. The public Linear launch film is a focus reference without a claim that it matches the private reference. [Review player](https://devmcp.davemafy.xyz/sauce-motion-phase2/modal-lift-review-20261118/) · [Master MP4](https://devmcp.davemafy.xyz/sauce-motion-phase2/modal-lift-review-20261118/master-1080p60.mp4).


## 2026-11-18 — Glass loupe in the event-video renderer

Main implementation: `c9661376d79bf1d4f0785b55222e1925c5c55a3c`. Added opt-in `--glass-loupe` to `scripts/render_event_video.py`. The planner consumes a verified slider event, ordered pointer samples and changed DOM bounds, then renders a sharp center directly from the original source and confines radial bending and color separation to the outer lens. Missing or malformed evidence falls back to regular composition. No site-specific URLs, prices, crop coordinates, or cue timestamps are embedded in the renderer. The existing one-off Resend renderer remains separate.

Captured a fresh actual Resend pricing drag in Chromium, sampled at 2880×1800 (DPR2), with source frames serialized at 60fps. Browser evidence verified input value .125→.25 and visible Pro price $20→$35. The producer for this proof used a checked live DOM capture script in the isolated worker checkout (`sauce-loupe-20261118/studio/.tmp/loupe/capture.py`). The web editor has no automatic capture adapter or loupe toggle yet. Cross-app visual generalization has not been verified.

[Review player](https://devmcp.davemafy.xyz/sauce-motion-phase2/glass-loupe-review-20261118/) · [Effect on](https://devmcp.davemafy.xyz/sauce-motion-phase2/glass-loupe-review-20261118/glass-loupe.mp4) · [Effect off](https://devmcp.davemafy.xyz/sauce-motion-phase2/glass-loupe-review-20261118/comparison.mp4). Both use the same source and locked camera. The effect-on pass draws the tracked cursor from the cursorless source sidecar; the baseline is cursorless. Both masters: silent H.264 1920×1080/60, 276 frames, 4.6 seconds, full FFmpeg decode passed. Effect-on SHA256 `e21eaf0e2f749d2ca20c7077e346960875de3885d003cd1941e4152280a3ca5b`. Chromium playback and no page overflow verified at 1280×720 and 390×844. Focused tests: 16 passed. Inspected encoded frames 38/57/80/104/155/235 and sampled the supplied reference. The effect stays visible at small sizes and the changed price reads in the lens. The adjoining Scale price, which did not change, enters the refracted rim. The neutral stage and short expansion may still need art direction review before this becomes a default.

## 2026-11-18 — Padey added to the Phase 2 test subjects

Add [padey.com](https://padey.com/) to the internal visual test rotation alongside Brimble, OpenSheets, and Resend. Status: candidate awaiting capture. Use a genuine, accessible product interaction with a visible result to test whether the shared renderer can choose and compose a fitting effect on a new source. Compare the effect-on and effect-off exports from the same capture. Select the effect after inspecting the actual workflow.

## 2026-11-18 — Owner screenshot rejection, 16 GiB worker experiments and action-led single-plane correction

**Owner's visual feedback:** The published experiments appeared as small screen recordings with poorly motivated floating UI layers. This was treated as a **creative rejection**, not an invitation to describe green CI as success. The generic gray backdrop, stacked modal and detached white spreadsheet strips failed to establish an attractive source-true product composition. The next experiment was explicitly directed at the actual pixels, not another filter.

**Worker provenance:** Recovered existing DevMCP direct Vultr worker, approximately 15 GiB physical RAM (8 vCPU, ~13 GiB available when checked), FFmpeg, Blender and existing isolated release/test worktrees. Main at recovery was `e716426`; preserved the heavily dirty `sauce-v05-release`, existing servers and every prior proof. All new scratch experiments ran in `sauce-high-effort-main/studio/.tmp/effects-lab/` from a clean isolated checkout of main, with source and regression modules committed **to GitHub main only**, not deployed as automatic customer presets. No extra VM, GPU, paid AI or customer render was added.

**Synchronization discrepancy caught by inspecting actual encoded source:** OpenSheets real 1600×900/60 source SHA `69800f09767840b54334d09f6006ad4c53c3edd519a9ea27a4460aae540c8eca` first exhibits sustained currency-formatting result change at decoded **source frame 308**. The capture manifest + stated lead offset maps click to ~frame 313 and DOM change to ~frame 315, a difference of **5–7 frames (83–117 ms)**; this is an empirically observed inconsistency, NOT proof that the DOM changed before the real click. The exact clock-origin/concurrency cause remains unverified. New `scripts/semantic_spatial_handoff.py` provides bounded verified patches, geometry transforms, source-frame sustained-change detection and a 60fps/48kHz sample clock. Automated tests include invalid geometry, unsustained flash rejection, source-pixel identity and shared plane projection; no generalized live-browser timestamp calibration is claimed.

**Actually rendered, inspected and published experiments (all separate static review URLs):**
- [OpenSheets full-scene spatial handoff](https://devmcp.davemafy.xyz/sauce-motion-phase2/spatial-handoff-sync-review-20261118/) — 1920×1080/60, 304 frames, 5.066667s, H.264/AAC 48k, SHA `c507509caf0f910de0a329bdc99997f8dd99b484bcee58c28b8d8ede744b2cbc`. Four shutter samples on the 54 moving frames; genuine cropped five-value result from settled source frame 330 with original source coordinates at transition start, then 100-frame read hold. Readability improves but foreground remains a rectangular card.
- [Brimble nested interface depth (corrected cut)](https://devmcp.davemafy.xyz/sauce-motion-phase2/brimble-nested-depth-study-20261118/) — 1920×1080/60, 409 frames, 6.816667s, H.264/AAC 48k, SHA `83142210c1261302238fa2d86acfdbfa8862b7fed8af65c15b8015c10405942c`. Brimble baseline real source SHA `8d4259ff29a3fd4980fb3457ed884ed850de17d4c1e3640deb1b8903550d3ac5`; actual f210 modal connected-component bbox x639/y157/w641/h763, nested crop x711/y575/w553/h276. Duplicated large gray backing slab from the first cut was removed in a second full re-encode; still visually inferior and too much like stacked card compositing.
- [OpenSheets six-plane cell cascade](https://devmcp.davemafy.xyz/sauce-motion-phase2/currency-cell-cascade-20261118/) — 1920×1080/60, 304 frames, 5.066667s, H.264/AAC, SHA `3359211f04a2e1eb814109d462622ac441e189aecfb0ffdf8b249350b0ba4e12`. Actual source column heading + five recorded currency amounts separately project and stagger. At 390px the values are legible, but the detached bright strips read like a UI motion effect test, NOT a premium film. Do not promote it to default.
- **Action-led control correction:** [Brimble *one continuous interface plane*](https://devmcp.davemafy.xyz/sauce-motion-phase2/one-plane-editorial-review-20261118/) — [actual master MP4](https://devmcp.davemafy.xyz/sauce-motion-phase2/one-plane-editorial-review-20261118/master-1080p60.mp4). 373 encoded frames, 6.216667s, 1920×1080/60 H.264 + AAC 48k, SHA256 `09e9d669f8cabcc3cfa0e1152022235e655c68561e921c9535ffcdec35a9491a`. Original recorded Brimble source frames **0–160** preserved byte-for-byte before the added camera. Actual Codex result is already observed by source f125; the camera starts only after source f160. An intermediate 1.34× full-modal shot is followed by a smooth 2.92× source-backed close-up of actual Codex and command within x711/y575/w553/h276; 104-frame readable hold, output-frame-aligned quiet procedural whooshes and original Foley retained through the observed interaction. **No second command panel, synthetic cursor, retyped text or newly invented website state.** Four temporal shutter samples only during camera movement, genuine sharp source pixels during reads. Opened encoded 14-frame montage and a 390px wide final image: the command occupies far more of the composition, is comparatively readable, and scene continuity is superior. Still a **control/experimental shot**, not proof of premium visual quality.
  
**Video QA:** All four masters were fully FFmpeg `-xerror` decoded. Published source and server SHA matched for reviewed movies. Playwright real HTTPS video playback on all first three at both **1280×720 and 390×844** returned `readyState=4`, no video errors, real time progression, JS errors or horizontal overflow. Single-plane desktop/mobile player returned HTTP 200, `readyState=4`, `duration=6.216667s`, successful seek to 4.88s, `video.error=null`, no overflow/errors. Decoded AAC to original procedural Foley cross-correlation offset **0 samples** on all four; AAC padding at the file tail is normal. The new `scripts/semantic_editorial_camera.py` + seven single-plane tests were committed to main. `tests/phase2/`: **66 passed, 10 skipped**. Full unittests from the configured render env: **205 passed, 1 skipped**. TypeScript Studio-motion tests: **31/31 passed**. A prior attempt to run Python unittest using system `python3` failed because `pytest` is not installed there; re-running in the project render environment passed, no production fault claimed.

**Creative gate STILL OPEN:** The new one-plane zoom solves obvious duplicate-panel artifacts but remains visually plain. Its source capture is only an already-encoded Brimble film, so sharpness and opening composition still fall short of premium. The two-plane experimental styles lack restraint, and the spreadsheet sample looks like floating white strips. Need genuinely new sharp source capture and **reference-led shot composition**, then actual user approval of full playback, before engineering opt-in effects into customer defaults or claiming differentiation. The source/test modules are reusable technical foundations, NOT newly deployed or user-approved effect families.

### Brimble modal focus hold

The first opt-in modal lift converged onto the original blur/dim settings after the 300ms transition, and the Codex close-up separately recreated those settings. Commit `71424e4b42a6f43875190ba8cd21b6e3d03b2732` gives the opt-in composition stronger sustained background defocus and passes the last verified depth, blur and dim into the source-resolution payoff render. Standard rendering retains its existing parameters. This is a continuity correction within the opt-in treatment; the single-plane editorial baseline and owner visual rejection remain as recorded above.

Compared encoded frames 72, 190 and 250 with the first modal-lift master. The difference persists through the close-up but reads subtly at feed size; the backing plate is still prominent. The same six-state Brimble replay yielded 319 frames, H.264 1920×1080 at 60fps with 48kHz AAC, 18 lift frames, 152 verified multi-plane frames, zero isolation fallbacks. Full FFmpeg decode passed and public SHA-256 matched `8856a7df5649d606a15861a98fe9c03427972a54418245817b5a170d1abc1656`. Chromium played through 4.2s at 1280×720 and 390×844. Target checkout Phase 2 suite: 61 passed, 10 skipped, including exact opaque dialog pixel equality between defocus strengths. [Review player](https://devmcp.davemafy.xyz/sauce-motion-phase2/modal-focus-hold-20261118/) · [Master](https://devmcp.davemafy.xyz/sauce-motion-phase2/modal-focus-hold-20261118/master-1080p60.mp4).


### Glass loupe motion and cursor revision

Main `42f52383ab3ef6018fb9652c7eaa1196e98ddb9b` smooths the recorded slider path with monotone Hermite interpolation, separates entry and result reframing, and projects one high-contrast subpixel cursor through the same radial map. Short clips retain the settled loupe and last recorded cursor position through the final frame. Rendered the same verified Resend capture at 1080p60, 276 frames / 4.6s. Full decode and 18 focused tests passed. Inspected encoded frames 47/67/88/110/210/275 at 390px. The cursor is visible at the final hold and the $35 result is readable. The white glyph sits over the white slider knob when the drag lands. Desktop and mobile Chromium playback verified. [Revised and prior renders](https://devmcp.davemafy.xyz/sauce-motion-phase2/glass-loupe-motion-20261118/). Revised master SHA-256 `4e98a15ec2f905ed6bc1a71b3bb18fc805d4b3919f183300c50f11a4a8ee4ce9`.

## 2026-11-18 — Composable effect timeline seam, existing modal lift preserved

**Scope:** Integrated a small source-bound scheduling seam rather than adding another shader or replacing the existing H0/H60 renderer. Used the recovered persistent Vultr worker and an isolated *main-only* `sauce-semantic-fx-integration` checkout. The dirty `sauce-v05-release`, concurrent experiments, deployed Studio and old published films were untouched. Starting main was `f75fec3`.

**Code:** `scripts/semantic_effect_timeline.py` defines a bounded, immutable effect sample, source-verified evidence contract, mask/composition ordering and one per-target integer-frame clock. The first and **only** enabled family is `semantic-layer-separation`: `scripts/session_replay.py` now samples it in the existing opt-in `--preset 3d-launch --modal-lift` path. The previous ease formula `eased((frame-firstVerifiedFrame)/(fps*0.30))`, existing H0/H60 compositing, modal capture, single cursor and editorial/Foley code remain unchanged. Missing verified modal/clean plate releases the effect and leaves the previous single-plane fallback in charge. Unimplemented metamorphosis, optics and kinetic effects explicitly fail closed. Full status and next-family requirements: [docs/SAUCE_EFFECTS_ENGINE.md](SAUCE_EFFECTS_ENGINE.md).

**Actual on-Vultr re-render and comparison:** Used the *same existing* private six-state Brimble Chromium session and workflow with `--modal-lift --preset 3d-launch --result-aware-editorial --result-payoff-push --no-webgl-optics`, 4.2s source timeline. The new private master `sauce-semantic-fx-integration/studio/.tmp/semantic-effect-qa/render/master-1080p60.mp4` has SHA-256 `22e6ee7fcb75b6bf09cd0ac7ba4c8cf12e545e5f338fc73384f5c698e2301757`. ffprobe: H.264 1920×1080 60fps, 319 frames/5.316667s, AAC 48kHz stereo; full FFmpeg `-xerror` decode passed. Private receipt reports six source-verified states, 18 lift transition frames, 152 true two-plane frames, zero single-plane fallbacks, original cut at frame 125, four procedural Foley cues, peak 0.2108. Compared to existing public [modal-lift review](https://devmcp.davemafy.xyz/sauce-motion-phase2/modal-lift-review-20261118/) (SHA `9cfa9f6af19adb12ed39d395c4e69a0cc004084dc9df131f2ed21a37deea0849`), encoded full-frame MAE at frames 0,48,54,60,66,97,125,246,310 was between **0.0596 and 0.3864 / 255**. These are close visual results, **not identical files**; live Chromium replay remains non-bit-deterministic without a pinned canonical raster cache. Opened the original encoded 7-frame contact and the new encoded f54/f66/f125/f246 native-derived contact; no new overlay, clipping or changed source UI was observed.

**Tests and limits:** New effect scheduler 7 passing; combined scheduler, multi-plane and semantic projection tests 30 passing; whole Phase 2 suite **67 passed, 10 skipped**, Python syntax compilation passed. New review master is **private only** and was not published or deployed. No new AI inference, customer job, payment, VM or service changes. This milestone is a reusable clock/provenance seam, **not** a new visible signature effect or visual approval. The initial modal is still small, the gray backing dominates and command text is still too small at phone feed width. Next: compose and visually compare a source-verified persistent-common-element handoff on Brimble and OpenSheets before enabling state morphs or optical filters.

### Reconciled against new main and independently re-encoded

During this work, main advanced to `590d4a9`, adding an opt-in Resend glass loupe in the **separate** event-video renderer and source-true single-plane editorial camera work following an explicit owner rejection of floating slabs. Our staged change was reconciled without force-pushing or discarding these commits. The timeline-backed replay retains **their new sustained-focus settings** (`MAX_BACKGROUND_BLUR` and `0.18` dim at settled lift), `payoff_lift_factors` continuity through the result tail and foreground cursor depth. See the revised [effects engine contract](SAUCE_EFFECTS_ENGINE.md); the Resend optical effect is not yet unified under the new timeline.

**Fresh exact-main integration render:** Same six-state real Brimble fixture, `--preset 3d-launch --modal-lift --result-aware-editorial --result-payoff-push --no-webgl-optics`. Private `sauce-semantic-fx-integration/studio/.tmp/semantic-effect-qa/render-current-main/master-1080p60.mp4`, SHA256 `2e293825a8f8f64eacb52c4c481ac3fbaf46c027ba23d0c6301f620c6b41c357`. 319 frames, 5.316667 seconds, 1920×1080/60fps H.264, 48kHz AAC stereo, 4 real-event-aligned procedural Foley cues. Full FFmpeg error-on-error decode passed. Six verified captured states, 18 lift transition frames, 152 valid two-plane frames and **zero single-plane fallbacks** in the receipt; no canonical frame cache, so no claim of independent live Chromium byte-repeatability.

**Observed visual QA:** Opened private native-derived encoded contacts at output f48, f66, f125, f246 and a **390px-wide** f246 result. Brimble's genuine command remains in its original dialog but is **too small on a phone**; the generic gray backing is still over-dominant. Private `file://` review page played and sought successfully in Chromium at **1280×720 and 390×844**; after seek, `readyState=4`, `video.error=null`, actual time progressed beyond 4.1s, no page errors or horizontal overflow. **This work is infrastructure for future context-aware effects, not a visually superior film or an owner-approved sample.** The earlier f75f frame-MAE comparison above pertains to the pre-concurrent-focus baseline, not this new commit's altered blur/dim policy.

**Current tests after incoming changes:** Phase 2 **77 passed, 10 skipped**; Python unittest **205 passed, 1 skipped**; new timeline tests **7 passed**. No production deploy, public publication, buyer outreach, spend or source-file leak. Next implement identity-verified match movement and compare it with the *one-plane action-led* film and the Resend optical A/B, rejecting stacked UI layers that fail a full-size and 390px visual review.

## 2026-11-18 — Anchored result cut in the event-video renderer

The opt-in `render_event_video.py --presentation fullscreen --anchored-result-cut` path holds the source-wide camera until verified click/result evidence, then cuts to a bounded closer composition around the same recorded result rectangle. The target center has the same output coordinates on each side, and the entire rectangle stays in view. The cut reserves at least 1.25 seconds for the payoff. Unsupported aspect ratio, inadequate margin, timing or missing evidence retains the ordinary camera. The loupe and the cut take separate opt-in paths while their camera behavior is evaluated.

Paired Vultr renders used the same real OpenSheets source and exact seven-second excerpt. Both silent H.264 1920×1080/60fps outputs have 420 frames and passed full FFmpeg decode. Effect-on SHA-256 `715282b69f009c9760505318c0e0a70733844a96fd1ff853b27258b8b36f63fe`; wide control `4514b32eee34476c220dab19f41905127129b7e6f2977d38d1a1a35440205eb5`. At frame 314 (5.233s), the camera cuts to 1.85× with the amount range centered at the same (1555.8, 333.0) output coordinate. Inspected frames 313/314 at 390px: amounts and adjacent labels are clearer, but the opening holds wide for over five seconds and the result still sits far to the right. This proves the cut geometry and compositor path, with one verified site. Feed impact, normal-speed desktop/mobile review, cross-site transfer and owner approval remain open. Private masters are under `studio/.tmp/anchored-cut-review/` in the `sauce-layer-editorial-1118` worker checkout.

Phase 2 suite: **80 passed, 10 skipped**. The inherited modal timeline is committed separately. Generalized result lift, cross-renderer effect selection, directional lighting and motion blur remain outside this change.


## 2026-11-18 — Public offline Kokoro voice audition, four shortlist voices

**Owner request:** Put actual voice samples on a single link so they can be heard on their phone; do not present theoretical voice-quality claims as auditioned audio. Confirmed the shared Vultr worker already holds `kokoro-v1.0.int8.onnx` (114,119,327 bytes), `voices-v1.0.bin` (28,214,398 bytes), and a separate Python environment with `kokoro-onnx 0.6.1`, whose `get_voices()` returns 54 names. No download, key or outside inference was required.

**Delivered:** [Public Sauce voice audition](https://devmcp.davemafy.xyz/sauce-motion-phase2/voices/) with the four previously recommended **American English** samples `af_heart`, `af_bella`, `af_nova`, `am_michael` (the shared comparison script is rendered at 1.04× speed in all four). Real locally synthesized mono MP3s, respectively 7.344, 7.512, 7.128 and 8.088 seconds, each 70–81 KB at 80 kbps. The self-contained static listening page provides four accessible native audio players and an optional sequential Play All action, with no browser app/backend changes. Static files are deployed only under the existing Nginx `/sauce-motion-phase2/` alias at `/var/www/sauce-motion-phase2/voices/`; source model, runtime, generation script/logs and all private project captures stay outside this public directory. Reproduction script/attempt logs are private in `/var/lib/sauce-steward/qa-logs/voice-audition-20261118/`. This is a **four-voice audition**, not a claim that all 54 installed voice types have been rendered.

**Validated:** HTTPS listening page **200 text/html**, each MP3 HTTPS **200 audio/mpeg** and **Accept-Ranges: bytes**, all four full FFmpeg strict decodes passed. Independent Playwright Chromium opened the live URL at **1280×720** and **390×844**; no horizontal overflow or script errors; first audio advanced beyond 0.09s with `readyState=4` and null media error on both. API, Studio and steward services remained active. The files are genuinely generated but have not received subjective user listening approval; whether local narration is better than commercial voices is *not* established.

**Scope control:** This was a standalone requested audio audition; it does not modify Phase 2 compositor pixels, cinematic playback, speech synchronization or Studio production rendering. Visual defects and the three-film quality gate remain open. No new public user-access flow, VM, paid API, licence transfer, commercial billing or customer outreach. Do not confuse audition samples with approved narration or a new Sauce monetization feature.


## 2026-11-18 — Verified local Kokoro audition gallery (not narration integration)

**Owner request:** One direct mobile listening link for all installed local voices, without ElevenLabs or new paid infrastructure. The existing Vultr workspace contains **Kokoro 1.0 INT8** at `.../studio/.tmp/educational-pilot/kokoro-v1.0.int8.onnx` (~114 MB), its 54 installed voices (~28 MB) and an existing isolated `kokoro_onnx` Python environment. The standard Sauce backend environment does not include the model runtime; that is unchanged.

**Executed:** Used the existing model to generate **54/54 original local speech auditions** in nine language groups (US and UK English, Spanish, French, Hindi, Italian, Japanese, Portuguese, Mandarin), with consistent original/translated Sauce narration within each group. Encode 24 kHz mono MP3 at 96 kbps, ~4.92 MB total. Rendered files privately under `/var/lib/sauce-steward/qa-logs/voice-auditions-20261118/`, published **only** the curated MP3 files + a static HTML catalog to the pre-existing public Nginx alias `/var/www/sauce-motion-phase2/voice-auditions/`; no web server config edit, systemd restart, new persistent service, paid API, customer action, model download or repo code changes.

**Opened proof:** https://devmcp.davemafy.xyz/sauce-motion-phase2/voice-auditions/ . HTTP 200 for the page, full 54-voice JSON catalog and sampled English/Japanese/Mandarin audio files, Content-Type audio/mpeg for MP3s. Selected MP3 files passed FFmpeg `-xerror` full decoding. Playwright validated **54 real audio players**, keyword filtering, British-English grouping (8 voices), zero JS page errors and zero horizontal overflow at both 390×844 and 1280×720. All three existing Sauce services remain active.

**Creative limitation:** This is an audition gallery, **not** a listener-accepted voice ranking, a proof of human-quality speech in every language, or synchronized narration in the production renderer. Some Japanese voice samples are unusually long for the script; non-English prosody and pronunciation still require human listening. Do not infer that voice narration solves existing Brimble film defects or that any paid voice provider has been equivalently matched. Continue Phase 2 source-true film quality hardening as priority.


## 2026-11-18 — Independent low-bandwidth 54-voice audition mirror

At the owner's request for **one URL to listen to the locally installed voices**, published a second lightweight, read-only audition at **https://devmcp.davemafy.xyz/sauce-motion-phase2/voice-gallery/**, separate from the already documented `voice-auditions/` gallery. It contains **54 Kokoro 1.0 INT8 local generations** spanning nine native-language/English-accent groupings, with featured `af_heart`, `af_bella`, `af_nova`, `am_michael`. These are static **64 kbps MP3** voice-tone tests, not final narrated video or a subjective quality signoff. A local generator and data-only samples live at `/var/lib/sauce-steward/qa-logs/voice-gallery-20261118/`; only safe sample MP3s and a simple HTML index were published into the **existing** `/var/www/sauce-motion-phase2/` Nginx alias. No Nginx edit, SaaS worker restart, new dependencies on production, new models or paid inference. One early Mandarin `zh` phonemizer rejection was fixed by using installed eSpeak Mandarin locale `cmn`; all eight Mandarin voice clips then generated. **Full FFmpeg `-xerror` decoding 54/54 passed**; public page and three sampled audio URLs HTTP 200, MP3 byte ranges HTTP 206, Playwright at phone 390×844 verified **54 audio controls**, search, language filter, actual 0.78s playing, zero page errors. All three Sauce services remain active. Approximate public preview library 3.8 MiB, on-demand load. Do not infer premium narration from raw generated samples; owner must listen and rank voices. This does not change the cinematic film quality gate.


### Reference-led glass loupe take

Main `9a390dc33efee9f1d1773201279d84ffc6c64867` restores the original 340ms lens entry and 380ms result reframe, keeps the refracted cursor, and enlarges/repositions the lens and changed price to keep the adjacent plan in view. `--stage-image` accepts an operator-provided backdrop for window renders; this review uses the licensed alpine-lake image already credited in `docs/sauce-film04-quality-review.md`. The same original Resend source and observed drag still drive the Sauce event renderer. The review's visual framing was manually tuned as reusable viewport proportions; the stage was explicitly selected for this comparison. A second-app verification remains open.

[New take and original](https://devmcp.davemafy.xyz/sauce-motion-phase2/glass-loupe-reference-20261118/). 276 frames, silent H.264 1080p60, 4.6s, full decode passed. Inspected the two prices and cursor at 2.4s and tested Chromium playback at 1280x720 and 390x844. 18 focused tests passed. SHA-256 `991df8d049f4a2aaf83b69589d2cf8075a2aefadbcbbb3bd696c07af381a5a87`.

## 2026-11-18 — Shared source coverage and opt-in result focus

The perspective dialog compositor and fullscreen anchored-result pass share rounded source coverage and alpha compositing in `scripts/source_region_mask.py`. Dialog shadows, warped coverage and cursor order retain the established compositor path. The event-video command `--presentation fullscreen --anchored-result-cut --result-focus` uses the result rectangle already admitted by the cut planner, projects it with the same camera matrix, then eases in a feathered 8% context dim over 250ms. The protected result is pixel-exact before encoding. Missing cut evidence keeps the normal camera and skips the focus pass. The concurrent reference-led loupe update was retained.

Vultr proof on real OpenSheets footage: seven-second H.264 1920×1080/60, 420 frames, full decode passed, SHA-256 `9989a4d6645c556c2629666aaeeb979f5bba00135238c697ac76478a6f7e0b0a`. Compared decoded frame 374 at 390px against the identical anchored cut with focus off. Rejected 12% dim with a narrow edge and rerendered using the wider 48px margin. Amounts remain legible, and the focus is subtle; the source-wide opening remains long. [Short review excerpt](https://chatgpt.com/library?file_id=libfile_90c10a4ee87c81918971909d6a04cf84&account_id=personal).

Brimble replay with the shared coverage composited 319 frames at 1920×1080/60 with AAC, passed full FFmpeg decode, and retained the rounded foreground through the inspected 4.3s payoff frame. The command remains small at 390px. Rendered proofs stayed on the worker. Suite after integrating upstream loupe changes: **81 passed, 10 skipped**. No creative approval, Padey capture, general result lift or shared optical/motion-effect rollout in this pass. General lift still needs a verified clean underlay and an explicit occlusion owner.


### Glass loupe optics and timing review

Main `e5f8fa18850d642c78901d2ca24a78fb9a1b4bf0`. Compared the supplied 279-frame reference and encoded Sauce frames 20, 82, 102, 150, 200 and 267. Re-captured the real Resend slider moving out and back, with Chromium confirming $20 at frame 94, $35 at frame 149, and $20 at frames 205/222. The evidence-backed loupe starts small, grows from the recorded long drag, and returns wide before the end with the cursor still visible. The cursor is a dark outlined arrow, and its hotspot is solved against the same radial map used for the footage. Added stronger outer radial warp and dispersion, a grazing reflection, and synthetic radial shutter samples only during the lens moves. Prices stay sharp during holds. The effect is rendered by Sauce; the capture and backdrop grade were directed for this review. The browser window remains wider than the supplied reference and the landscape differs.

[Optics pass and prior take](https://devmcp.davemafy.xyz/sauce-motion-phase2/glass-loupe-optics-20261118/). 279 frames, 1080p60 H.264, 4.65s, full decode passed. 19 focused tests passed. Chromium playback verified at 1280x720 and 390x844. SHA-256 `08fcc11cfc4b6ec516ed8902bf16edb568d99fd87cc73318a1cd5b9aa8076c18`.

## 2026-11-18 — Continuous guided result shot

After owner feedback on the hard cut, added opt-in `--guided-result --presentation fullscreen` to the event-video renderer. The opening crop fits the verified click and result rectangles, and a 780 ms eased push starts after the recorded state-change cue and a short settling allowance. It retains the cursor already recorded by Chromium/X11. The capture lacks a verified cursorless plate for a custom pointer. Applied no dimming. Scope is one verified click/result beat. The other camera and loupe paths retain their own flags.

OpenSheets render on Vultr: actual decoded amounts appear at roughly 5.13s source time. Guided motion starts at 5.22s and settles near 6.00s. The 1080p60 H.264 master fully decoded, 492 frames, SHA-256 `06f1deafe3ee065c5afe75a780fc3c8ac3bf47375efc039d3064d1e5b1abb908`. Checked encoded approach, toolbar action, push and payoff frames at 390px. The native arrow is still small and the spreadsheet context remains plain. The 3.5s review excerpt trims the lead-in. [Review clip](https://chatgpt.com/library?file_id=libfile_bf9839fe227c81919064f9910db252ac&account_id=personal). Phase 2 suite on the render checkout: 82 passed, 10 skipped.


## 2026-11-18 — Refs.video source-true UI editorial grammar integrated (opt-in)

**Main source commit:** `f58092ce2cd95be8c8b73756199798cef0c53145`; preserved intervening commits and the heavily dirty production/legacy worktrees. Research/implementation contract: [docs/SAUCE_REFS_PRODUCT_DEMO_STUDY.md](SAUCE_REFS_PRODUCT_DEMO_STUDY.md). Public sources were Refs.video's Loom, Framer and Raycast *written/visible* analyses; full gated reference footage was not acquired, and their original artwork was not copied.

**Implemented in the existing engine, not a visual preset collection:**
- The `3d-launch` camera holds a still establishing composition until a **verified product event**. Saliency-only metadata no longer triggers premature pushes/pans in this cinematic preset; Hyper-Cut retains its prior ambient gaze treatment. A real feature commit may own its camera beat up to 2600 ms (generic click 1800 ms), with existing verified modal ownership and physical 180/24/1 spring untouched.
- Existing opt-in `--result-aware-editorial --result-payoff-push` now determines result-reading duration from the **actual DOM element type**: code/pre 108 frames, output 84 frames, other verified results 66 frames. For code/pre only, the verified real result rectangle may support a 12-frame context hold plus a bounded 24-frame second dolly (up to 2.9×) into the **same original DPR2 source pixels**. No duplicated white card, synthetic command text or fake click. Malformed geometry/timing is rejected. Source and tests updated in `scripts/result_payoff.py`, `scripts/studio-motion/src/cameraRig.ts`, tests and the versioned built JS.

**Real encoded film, not just green CI:** Published [Refs editorial Brimble review](https://devmcp.davemafy.xyz/sauce-motion-phase2/refs-editorial-study-20261118/) and [exact master MP4](https://devmcp.davemafy.xyz/sauce-motion-phase2/refs-editorial-study-20261118/master-1080p60.mp4). Private render SHA-256 `f7863d6058cee63e3436600d8e845aa64acc9139e5d0557ea53f1f73d9250834`; H.264 1920×1080, 60 fps, **397 frames/6.616667 seconds**, AAC stereo 48 kHz, full FFmpeg error-on-error decode passed. Six SHA-verified Brimble session source states; three semantic and three pixel checks; 152 true H0/H60 multi-plane frames, zero isolation fallbacks; four procedural event-synced Foley cues. The new payoff receipt reports 60 combined camera-move frames (36+24), 12 context-hold frames, 108 code-reading frames and 12 fade frames. The earlier [modal-focus-hold](https://devmcp.davemafy.xyz/sauce-motion-phase2/modal-focus-hold-20261118/) film at 319 frames remains intact as a visual comparison.

**Actual visual QA:** Opened the native-derived encoded frame 310 and its 390px version, plus a multi-timestamp old/new comparison. The genuine Codex heading, two-line real command and Copy affordance are present and markedly larger in the new final shot. **Not premium/quality-approved:** opening window/hero remains too small, its gray backing slab and bland stage still dominate too much of the composition, and underlying page design/source text remain limitations. No proof on a second product with this new opt-in shot, no claim of 30-second polished film or automated high-quality arbitrary-site generation.

**Checks:** TypeScript motion engine **33/33 passed**; Python Phase 2 **82 passed, 10 skipped** (browser gated); legacy unittest **205 passed, 1 skipped**; focused payoff **5 passed, 1 browser skipped**. Real production HTTPS player and media all returned HTTP 200 with appropriate types; Chromium Playwright at **390×844 and 1280×720** had `readyState=4`, video error null, successful 5.15s seeking, no JS errors or horizontal overflow. Public directory contains only player, poster, preview and master; HAR, raw source/session, trace and test images remain private on VM. Original production services all three still active. No new paid inference, new VM, source substitution, app UI deployment or change to customer-facing preset defaults.

**Next acceptance gate:** Render a second genuine *non-Brimble* workflow with the same reviewed editorial grammar and verified source outcome; evaluate native source sharpness, opening size, read-time at phone feed width and actual source-true film direction. If tests pass but the full output remains aesthetically generic, reject the default and iterate on composition, not arbitrary shaders.

## 2026-11-18 — Visible recorded pointer and guided payoff

Added opt-in `--recorded-pointer` to the fullscreen event renderer. Requires an explicitly cursorless plate and monotonic, in-bounds source-time samples. Interpolates the recorded path and projects the arrow hotspot through the same affine transform as the browser image. Loupe shares the existing outline glyph and retains its optical projection. The guided payoff shifts the target slightly right to leave room for adjacent column labels.

Fresh local OpenSheets capture on Vultr used the actual native X11 range selection and currency click with cursor capture disabled. 187 pointer samples and five verified currency values. The worker proof used a scratch capture runner adapted from `record_opensheets_story.py`. Applied its nominal 270 ms recording lead to the manifest and verified that the result was already visible at decoded frame 310 before the camera push. This is not a frame-exact click-clock calibration. The 1080p60 master has 504 frames, SHA-256 `9918be4ed409e1a78e7a1595a09981f6f7b41e3de380e35b029a8f67a02d365a`. FFmpeg full decode and local Chromium playback of the excerpt interval at 390×844 and 1280×720 passed. Inspected encoded approach, click, change and payoff frames, and rerendered to remove a clipped supporting heading. Phase 2 suite: 85 passed, 10 skipped. [3.5-second review excerpt](https://chatgpt.com/library?file_id=libfile_aaef5d520608819181624e5b75c0a3b9&account_id=personal). The source is a plain spreadsheet and the proof is silent. Creative approval remains open.

## 2026-11-18 — More legible guided cursor

Compared the owner-supplied lens reference. Increased the guided recorded arrow to 1.6× screen-space scale and added a small hotspot-locked press response at recorded button-down cues. Existing loupe rendering retains its default glyph scale. Vulkan/GPU rendering is not required. Fresh OpenSheets master fully decoded at 1080p60, 504 frames, SHA-256 `296893df477f685ff47b30f6dc65a65b06b3aaf17e2a243df1e34a92af116266`. Checked the encoded toolbar frame. Phase 2 suite: 85 passed, 10 skipped. The click clock still uses nominal capture lead and cursor styling is inspired by the reference.


## 2026-11-18 — OpenSheets real DPR2 second-product Refs directing gate

**Second-product transfer is technically demonstrated, creative signoff remains OPEN.** Main-only source commit: `c7c2f6b9a2c5ecaf9655e78c3d77c1b5f022683e`. Existing dirty production and previous reference/movie experiments were preserved. This proof was made in isolated Vultr checkout `/var/lib/sauce-steward/refs-product-gate-main`, fast-forwarded to current main and manually 3-way reconciled with concurrent `recorded_pointer.py`/loupe work. Nothing was reset, force-pushed, migrated or deployed as a default production preset.

**Different real product and actual capture:** Local running MIT OpenSheets 2.1.0 source from `w0h1v/OpenSheets` (existing repo), fictional sample expenses but **real editor controls**. Captured a new real Chromium/X11 browser workflow at physical **3200×1800, DPR2, 60fps, 720 source frames/12s**. Source media SHA256 `ad4f01f6a94ca2b072b1aba21c864a9f59b7ce2fac118966471bf66aed920da6`. The real user event is H5:H9 range selection, actual Currency toolbar click and observed gridcell state change: **$320.00, $75.00, $150.00, $24.00, $45.00**. Captured 10 browser/DOM events and 186 pointer samples with measured 0.27s encoder lead. Independently opened original 3200px screenshot and source recorded pointer frame crops: single native spreadsheet crosshair on the selected cells, native pointer at currency toolbar, no drawn replacement pointer. Across 75 source frames in pointer-action window, 62 of 74 consecutive 320×180 decimated samples differed, supporting authentic temporal change; 60fps container is not asserted to mean every static frame is distinct. Raw video/sidecar/quality screenshots/capture script remain private under `/var/lib/sauce-steward/qa-logs/opensheets-refs-gate-20261118/`.

**Engine change, limited and opt-in:** `scripts/verified_workflow_editorial.py` is a pure geometry/source-evidence camera planner. `scripts/render_event_video.py --presentation fullscreen --verified-workflow-editorial --trim-real-idle-intro` requires a verified selection, button approach, semantic click, changed result and completion, and only then creates an establishing view, action-following toolbar push, one cut at the verified result followed by a C2 quintic close push, a reading hold and a controlled release. The cut and zoom use only actual recorded source pixels, no floating duplicate cards, HTML reconstruction, fake UI/cursor, redrawn text or invented result. Missing/malformed proof fails closed. The intro trim removed **124 genuinely idle source frames** before real recorded pointer action without time-warping the interaction. The film maps source frames 124–620 onto output frames 0–496. Post-upstream merge metrics separate the intentional source-verified hard cut (1050 px offset) from continuous camera movement (**43.7145 px maximum single-frame translation** in affine matrix parameters; not a perceptual-speed approval). Upstream `--recorded-pointer` for *cursorless* sources is retained separately and was **not** used on this source with native pointer.

**Published real film:** [Watch the OpenSheets Refs-led product film](https://devmcp.davemafy.xyz/sauce-motion-phase2/opensheets-refs-gate-20261118/). [H.264/AAC 1080p60 master](https://devmcp.davemafy.xyz/sauce-motion-phase2/opensheets-refs-gate-20261118/master-1080p60.mp4), SHA256 `aad460b8621c36ff50694f9ac6da3df0bbc6612a450a087d615594db9fbe5ae0`: **497 frames, 8.283333s, 1920×1080/60**, 48kHz stereo AAC. An actual clean [silent master](https://devmcp.davemafy.xyz/sauce-motion-phase2/opensheets-refs-gate-20261118/silent-1080p60.mp4), 720p60 Lanczos preview, safe poster and neutral HTTPS watch page also verified. All public endpoints returned HTTP 200 with expected content types; raw source, event receipts and QA images are not published. Whole-film FFmpeg `-xerror` decode passed. Original local Foley synth placed 3 restrained cues at real source pointer-down (output f76), real click (f181) and source-verified result edit (f188); AAC-to-original waveform lag **0 samples** for each, output peak 0.156, no external samples/music/voice or paid inference.

**Visual evidence and limits:** Viewed actual encoded 13-timestamp contact sheet and 390px outputs, plus full-derived 1080p frames at opening/drag, button, result cut, sustained readable hold, final release. Crucially, five dollar amounts and adjacent TYPE labels remain together and legible at phone feed width in the DPR2 close shot; original prior 1600×900 rendered guided baseline had longer blank lead-in and softer, less coherent outcome. Native source optical clarity materially improved; the actual UI is still a sparse spreadsheet and the wide opening does not equal Linear/Apple-level directing. This counts as **a technically successful second distinct product workflow, NOT human-approved film quality or a general 30–90s arbitrary-URL production demo**. The feature currently specializes in recorded selection → button → result sequences and does not imply broad semantic action discovery.

**Verification after reconciling intervening main:** Python Phase 2 **91 passed, 10 skipped** (browser gated), legacy unittest **205 passed, 1 skipped**, Studio-motion TS **33/33 passed**; opt-in four planner regression checks passed; merged renderer PY compile and CLI preview passed. Chromium verified the **actual public film** at 390×844 and 1280×720, native decoder 1920×1080, duration 8.2833s, seek and progression on play, no video/JS errors or page overflow. Git diff checked clean of whitespace errors. Production `sauce-url2video`, `sauce-studio`, `sauce-steward` stayed active. No customer job, customer approval, revenue or change to default film preset was claimed.

**Next creative gate:** Further reduce whitespace and improve first-second meaning across multiple unrelated real applications, audit source-native zoom sharpness and correct pointer geometry at small sizes, then collect owner's visual approval. Do not reintroduce gray backing slabs or confuse source-verified frame tests with premium cinematic quality.


## 2026-11-18 — Owner rejected OpenSheets 8.28s output: film quality FAIL

**Supersedes any implied creative approval in the earlier OpenSheets handoff.** The owner watched the actual 8.283-second export and called it a poor use of 36 minutes. The same encoded upload was independently frame-reviewed at 0, 0.5, 1.25, 2.0, 2.67, 3.0, 3.13, 3.33, 4, 5, 6.08, 7 and 7.92 seconds. **QUALITY GATE: FAIL. Do not use this video as a flagship, sales demo, reference-quality proof, or example of a passed premium-film gate.** Technically verified source truth/stream/frame rate and tests are real but irrelevant to aesthetic approval.

Observed failures: (1) ~0–2.7 seconds opens on mostly empty spreadsheet with tiny subject and no useful immediate hook; (2) ~3.1 seconds hard camera cut reads as a discontinuity, abruptly shifting the workspace; (3) ~3.33–7.2 seconds remains on the same five currency cells with little evolving story, a prolonged static closeup; (4) final pullback returns to the same weak, largely empty wide stage; (5) native pointer may exist but is visually negligible in the film, and the basic table/toolbar interaction never acquires premium rhythm or art direction. Zero compelling scene construction. The prior congratulatory language about the technical second-product gate was misleading: the visual gate is **not broken**.

**Corrective process / stop loss:** Before any further long capture, automation, 4K/DPR work, or Foley polish: create and view low-cost film boards/3–5 decisive shots, then a draft first-3-seconds review. Compare specific shot timing/composition against actual product-demo references and require owner visual signoff before full render. Prioritize product-story selection and shot composition over resolution, codecs, shader additions, self-referential metrics, or rerunning full CI. If the underlying product/UI cannot support a striking, honest sequence, pick a stronger interface rather than trying to mask it with camera motion. Do not commit another 30+ minute experiment to cosmetically refine the rejected spreadsheet concept. Preserve existing source/capture/proof; don't delete existing output or revert unrelated code.

## 2026-11-18 — CMOkit URL-produced film rejected by owner; navigation is not product proof

Owner supplied the live Sauce Studio review screen and launch-post reference for CMOkit. Independently found and decoded the exact existing 30s scene-aware MP4 and opened an encoded 12-timestamp contact; browsed the actual public CMOkit website and analyzed its saved source inspection and scene receipts. **QUALITY FAIL:** the film repeats a small hero for ~7.5s, zooms into a navbar link rather than the destination section, holds static instruction cards and finishes on pricing. Two true anchor clicks are mislabeled as meaningful 'interactive' actions; zero verified H60 lifts. True source is 1280×720/~25fps but master is upscaled/resampled to 1920×1080/60fps. The site's stronger original cost/team/example regions were missed. The two screenshots are from different actual website sections, not comparable pixel-matched frames.

Critical architecture gap: the deployed StoryArc modules (`backend/story_arc_pipeline.py`, `scripts/story_arc_capture.py`, `backend/story_arc_render.py`) are **untracked on a dirty production checkout and absent from versioned GitHub main**; the new Phase 2 effects cannot automatically improve those outputs. Dirty work, production, media, and credentials were left untouched. Added a **non-wired** source-evidence diagnostic `backend/url_film_quality.py` and six tests on main; the checker correctly rejects the saved CMOkit capture as `navigation_only`, `bad_camera_targets=3`, `eligible_product_demo=false`. This is not deployed or an improvement to current video pixels. Read the full [CMOkit visual failure audit](SAUCE_CMOKIT_QUALITY_AUDIT.md). Next: reconcile current live StoryArc safely, classify public website vs verified product workflow before paid direction, fix post-anchor target geometry/scroll settlement, and have the owner approve a source-true opening 3-second shot board *before* any long rerender. Do not repeat the rejected '30 seconds of website scrolls' failure.


## 2026-11-18 — Refs-directed real Linear UI study, owner review pending

**New viewable candidate, NOT a passed premium-film gate.** Refs-led source engineering committed to main at `fe757a43b0e890398e7302c56101720b2993d0fc`, with [study](SAUCE_REFS_MARKET_FILM_20261118.md), `scripts/evidence_edl_renderer.py` and 5 targeted regression tests. Concurrent CMOKIT URL quality work on main was preserved; existing dirty `/opt/sauce-vids` and earlier workspaces were not reset.

**Observed references:** Inspected Refs.video's public Loom REF-3721 shot/timeline/transition frame sheets (21.8s/8 shots, first cut 5.5s, ~1.99x meaningful reframe, four-frame proof-transfer whip), public summaries for Framer REF-0542 and Raycast REF-3058 (full blueprints gated), and the locally saved original Screen Studio reference study. Film borrows editorial logic, not reference footage, graphics, branding or source scripts.

**Real browser proof:** DPR2 2640×1440/60fps/1110f X11/Chromium capture from the *public interactive marketing preview* at `linear.app` (**NOT** a signed-in account), raw source SHA-256 `7a539dd06e90257f237db0ad602301ca3fd8cc2db96ac802613904d010a8a454`. Three actual verified click-and-change pairs: Reviews→HomeScreen.tsx diff, Agent tasks→board, Agent Insights→actual 3,389/1,128/729 metrics/chart. 19 real trace events, 368 pointer samples; original capture is cursorless and Sauce projects exactly one trace-backed vector pointer. Private source/manifest/screenshots under `/var/lib/sauce-steward/qa-logs/market-film-20261118/` remain off public web/GitHub. Actual raw source had transient white preview edges (3.083–4.283s, 8.067–8.883s, 12.217–12.967s); the operator-authored EDL cuts out those frames rather than painting new UI.

**Film and actual browser output:** [Watch 15.27-second Linear UI study](https://devmcp.davemafy.xyz/sauce-motion-phase2/linear-refs-market-20261118/). [Exact H.264/AAC master](https://devmcp.davemafy.xyz/sauce-motion-phase2/linear-refs-market-20261118/master-1080p60.mp4) SHA256 `ed53e8ff8a1120eae23e86f0bb01f6db8f6437ed6d132bd12266e838256e831b`, 1920×1080/60fps, **916 frames/15.266667s**, 48kHz stereo AAC. Five source-backed shots: genuine final metric teaser, real issue/Review, real code diff/task action, real agent board/insights action, real insight metrics/chart payoff. Source backed after-the-fact proof teaser reorders real footage editorially, with no invented UI. Six original procedural Foley cues (actual click f199/f419/f623; verified result edit f222/f447/f646), peak 0.1296. Clean silent full-res export and 720p60 Lanczos mobile preview linked, with neutral watch page. Full FFmpeg error-on-error decode passes. Sampled output frames showed **zero measured white-source glitches** above preset near-white threshold. Opened frame contact sheets, selected 1080p film shots and 390px code/card/insight images. Both public browser layouts **390×844 and 1280×720**: HTTP 200, 15.274s preview playback, successful seek/play, no video/JS errors, no overflow. Production services `sauce-url2video`, `sauce-studio`, `sauce-steward` active.

**Tests:** Isolated working main with the new renderer: Phase 2 **96 passed / 10 skipped**, legacy unittest **205 passed / 1 skipped**, targeted EDL **5 passed**. TypeScript planner was not changed in this pass; do not imply it was retested here. Source hash and camera bounds checked. Do not count this as commercial validation, or a fully automatic director on arbitrary URLs.

**Creative status:** This is meaningfully stronger than the owner-rejected white OpenSheets 8.28s clip but **owner acceptance is unknown**. It is still a relatively straightforward operator-directed edit of Linear's public marketing UI, not a proprietary Linear partnership, not a complete Motion Design tool, and not equivalent to bespoke Loom/Apple animation. The new engine can replay a validated EDL using real result rectangles and source-timed cursor, but no reliable automatic authoring of the shot choices or per-site visual-quality judgment has been demonstrated. The white-glitch cuts are source-verified, not a general solution to all broken transitions. **Do not launch or sell this as premium without owner's actual viewing approval.**

## 2026-11-18 — CMOkit rejected-film self-repair policy, source verification, and stop-loss

New on `main`: `backend/url_film_recovery.py`, `tests/test_url_film_recovery.py` and [docs/SAUCE_SELF_HEALING.md](SAUCE_SELF_HEALING.md). Based on the already recorded CMOkit 30-second job and the prior diagnosis in [SAUCE_CMOKIT_QUALITY_AUDIT.md](SAUCE_CMOKIT_QUALITY_AUDIT.md), implemented a bounded **recovery decision**: navigation-only evidence downgrades the candidate to an honest public-website showcase; undersized navbar-camera targets require fresh source-verified destination geometry; late opening, non-native source resolution/FPS require rework; only a 3-second storyboard may proceed for human quality review. Failed repeated diagnoses or two attempts stop; no automatic paid inference. The decision is machine-readable but **not yet wired to the unversioned live StoryArc pipeline**.

Verified actual post-click CMOkit page in fresh public Chromium: #how section x0/y3.70/w1280/h671.02 (headline 'Two minutes, start to first campaign.') and #pricing x0/y-0.28/w1280/h548.16 (headline 'No subscription.'). This is real page geometry, replacing the previous tiny navbar-link focus geometry as the next *proposed* source. 16 focused combined quality + recovery tests passed. No new render or deployment occurred. No private CMOkit job/source artifacts published. **Owner visual-quality gate remains FAILED.** Next: reconcile existing untracked live StoryArc modules into versioned main without deleting work; connect this repair policy and verify a genuinely improved 3-second rendered opening, then require owner approval before expensive full rerenders.

### CMOkit self-recovery: browser capture timing and provenance check

Hardened the shared `backend/url_film_recovery.py` (without replacing its concurrent main implementation): `capture_verified_destination` waits for two stable geometry samples with a finite 1.8s cap, verifies that actual post-scroll section and heading coordinates hold across a Chromium screenshot, checks PNG source dimensions against the viewport/DPR, and returns the private source pixels plus their SHA256 receipt. Live CMOkit `#how` and `#pricing` both passed at DPR2/2560×1440 after the original eager attempt failed on an animating section. This specifically blocks the old 82px navbar-link camera-target mistake and avoids drawing from unverified mid-scroll frames. This is adapter groundwork only; StoryArc production remains dirty/untracked and no new full-length film is rendered or claimed. Existing film quality FAIL stands.

## 2026-11-18 — Regular ChatGPT parallel delegation; source clock corrected, URL film still rejected

Used existing Continuity Cloud Chromium UI and private VNC relay to successfully create **two separate ordinary ChatGPT chats** (Capture Engineer, Cinematic Director), each with an isolated main-only Vultr checkout and no push/deploy authority. A third Quality Critic ChatGPT tab repeatedly became unresponsive and was **not counted as launched**. Read the coordination receipt [Parallel Coordination](SAUCE_PARALLEL_COORDINATION_20261118.md); Capture and Film Director detailed reports remain in their isolated worktrees until reviewed for merge. The Film Director rendered two source-true CMOkit clips and correctly judged both creatively **FAIL**.

The coordinator identified the 3d-launch `idleStrategy=hold` beat-lock bug and **pushed only the independently verified frame-clock fix to GitHub main**, commit `78bff32`: actual 15s source now plans 900/900 output frames, retains genuine full-duration browser pixels, and the default ramp mode still makes its existing 206-frame edit. Tests passed (StudioMotion TS 34, combined Phase 2/QA 139 initially; integrated full local 144 passed/10 skipped). A's pilot source code was cherry-picked **locally only** and never deployed. It now produces a private QA-only 180-frame/3s 1920×1080/60fps CMOkit MP4 from the real recorded browser session, SHA256 `900db835606ad23f2c3fa5aa50ff2bd320710793a0b9f1be5bf9ecf33696b2b5`. Actual encoded frame review found an inert hero with no meaningful payoff: **VISUAL FAIL**. No quality pass, product-demo claim, production flag, or new public release; dirty live source preserved. Independent tests did not justify shipping this pilot.

## 2026-11-18 — Owner-rejected flat Linear cut corrected with floating UI and source-timed Brimble cursor

Owner explicitly rejected the earlier 13.97s flat Linear cut: awkward nonprofessional cursor, repeated disappearances, mechanical motion, no ripple and no floating background. New **opt-in** source-true compositor changes in `scripts/evidence_edl_renderer.py`, `scripts/cinematic_recorded_pointer.py`, `scripts/floating_ui_stage.py` reuse the actual Brimble reference-v15 SVG cursor, smooth X11 samples while locking real click hotspots, reintroduce a bounded neutral floating stage, and call the already-versioned real-click water refraction pass. A measured `result-upper` anchor keeps real code/tab focus in view; cinematic-pointer visibility preflight rejects offscreen/unrecorded pixels before full encoding. The 9-frame cross-source dissolve experiment ghosted real UI text and **was rejected and removed**, not shipped. All older releases and dirty concurrent worktrees preserved.

**Verified film:** [new 13.17s Linear review player](https://devmcp.davemafy.xyz/sauce-motion-phase2/quality-cursor-ripple-20261118/) · [1080p60 H.264/AAC master](https://devmcp.davemafy.xyz/sauce-motion-phase2/quality-cursor-ripple-20261118/master-1080p60.mp4) SHA256 `c3e307d28f7d195b022be782113f23f8bbafa4b54c6e7d5fb00ede8a5e8ed14f` · [before/after native frames](https://devmcp.davemafy.xyz/sauce-motion-phase2/quality-cursor-ripple-20261118/comparison.jpg). DPR2 original public Linear source and three verified real clicks preserved. **790 frames/13.166667s**, no fake UI. Prior EDL had **48 missing-source opening cursor frames plus 252 out-of-frame pointer frames**; new measured camera/cursor envelope yields **0 and 0**. All six Foley cues source-aligned; full master/preview FFmpeg decode passed; HTTPS and playback/seek verified at desktop 1280×720 and phone 390×844 with no media/JS errors or overflow. New Phase2+3 tests: **130 passed / 11 skipped**, legacy **205 passed / 1 skipped**, TypeScript **34 passed**.

**Creative gate still OPEN**: provisional engineering visual score **6/10**, not owner-approved or market parity; dark dense public preview, hard cuts across raw white remount gaps and manual 4-shot EDL remain. The user explicitly wants Brimble-level source-true visual polish; this improves a rejected study but **does not yet make arbitrary URL→premium film automatic**. Full study, exact command contracts and limitations: [2026-11-18 cursor/ripple review](SAUCE_CURSOR_RIPPLE_QUALITY_REVIEW_20261118.md).

## 2026-11-18 — Source continuity auto-director and 86%-stage Linear film (review only)

After rejecting the previous 6/10 Linear edit as a weak foundation, decoded the **original** DPR2 public Linear preview (2640×1440, 60fps, 1110 frames). New `scripts/source_continuity_scan.py` independently detected the actual white remount windows **[0,0], [185,257], [484,533], [733,778]** (170 unusable source frames, 15.3% of the capture). These exact recorded frames had previously been skipped manually. The new bounded **`scripts/source_true_director.py`** produces a four-shot EDL from genuine paired DOM clicks/outcomes and source-stable segments, with zero invented interface/actions or AI inference; all unknown capture shapes fail closed. Its first edit was corrected because the state text "from code diff to task columns" must target the **current board**, not the previous code diff. Quality gate reuses source hash + continuity receipt, real DOM result geometry and full per-shot recorded pointer visibility.

New opt-in `scripts/source_verified_whip.py` briefly shifts/blurs **one real source state per output frame** at capture-remount cuts; unlike the rejected crossfade, it never ghosts two UI states. A source-true A/B at floating screen scales 0.79 vs **0.86** demonstrated that the larger stage substantially improves source UI legibility without losing margins or cutting off the real pointer. Existing non-EDL behavior, previous public films, heavy production dirty worktree and all independent agent checkouts preserved.

**Verified viewable film:** https://devmcp.davemafy.xyz/sauce-motion-phase2/quality-source-director-20261118/ ; exact H.264 1080p/60fps/AAC master: https://devmcp.davemafy.xyz/sauce-motion-phase2/quality-source-director-20261118/master-1080p60.mp4 ; native-frame comparison: https://devmcp.davemafy.xyz/sauce-motion-phase2/quality-source-director-20261118/comparison.jpg . Master SHA256 `9b661e9b0eb0c9cde8b21da95e0d979b4f7e6e8d8ef71e50ccda4ae09fa8e475`; **790 frames, 13.166667s**, exactly **3** recorded clicks, **3** genuine observed outcomes, **0** missing/offscreen cursor frames, **0** encoded white flashes, original source SHA pinned, original **3,389/1,128/729** UI metrics intact. Six genuine-event Foley cues (click frames 73/294/497, transition frames 97/322/520). Full FFmpeg master/preview decode passed; real public HTTPS 200 and Chromium play/seek at 1280×720 and 390×844 with `readyState=4`, no media/JS errors or horizontal overflow. Only authored player + finished MP4s/poster/comparison published; raw X11 capture, private events and internal references remain private.

**Tested:** Phase 2+3 Python **140 passed, 11 skipped** (including 10 new continuity, planner, provenance and transition tests). The edited film was viewed at 16 timestamps, native full-resolution comparative stills and cut-frame sequences. Full method, CLI and rejection notes in [docs/SAUCE_SOURCE_CONTINUITY_DIRECTOR_20261118.md](SAUCE_SOURCE_CONTINUITY_DIRECTOR_20261118.md).

**Creative gate STILL FAILED for launch, provisional 6.5/10.** The dark detailed preview and three long real state-remount gaps remain impossible to transform into truly continuous product action; the whip is only an honest transition between real states. The automatic director currently supports exactly this **3 click / 3 outcome / 3 gap** captured grammar; no claim of robust arbitrary URL→premium film or of owner approval. Next priority: a **second actual continuous interactive product capture** with real scrolling and a coherent user journey, then compare the encoded film with Screen Studio/Refs before any wider release. No paid inference or new infrastructure.


### Liquid glass reference refinement

Main `60bfc92`. Compared the supplied reference and the rendered wides, small-lens hold, expansion, $35 payoff, return drag and cursor exit. The smaller lens now places the slider thumb left of its optical center. Cursor scale changes with the lens, while the hotspot follows the same inverse distortion as the UI. The rolling radial profile concentrates curvature and color separation at the glass lip. Bezel and scenery now participate in refraction outside the high-resolution page sample. The lens stays composed when the pointer leaves the slider, using actual browser pointer samples after release. Narrowed the floating browser frame to match the reference proportions. Reused the earlier manually graded lake asset. Remaining visible differences include the landscape and large Pricing title in the upper lens.

[Liquid glass and previous render](https://devmcp.davemafy.xyz/sauce-motion-phase2/glass-loupe-liquid-20261118/). 279 frames, 4.65s, 1080p60 H.264, full decode passed. Inspected encoded f75/f101/f150/f234/f258/f272. Desktop and mobile playback confirmed. Phase 2 tests 87 passed/10 skipped before integrating the concurrent shared pointer scale, 21 focused tests passed with the shared pointer code. MP4 SHA-256 `3df5b2391ef933a92b8198541ec9981649f115035d9e38dbd45991588653b10f`.


### Loupe cursor silhouette correction

Main `09759cc255e0f17f21c48d941245bfb38d7bebae`. Compared the supplied clip and prior export at 2.5s using native pixel crops. The previous loupe arrow had a polygonal, sharply angled stem and a heavy outline that fused visually with the white slider thumb. The loupe projects the hotspot through its inverse radial map and draws the arrow afterward. The new cursor asset uses a rounded stem and thinner outline, pre-rasterized at 4× and composited with premultiplied alpha. Reduced the lens-stage scale boost and retained the same hotspot and pointer samples. The non-loupe pointer keeps its existing drawing path.

[Revised cursor and previous pass](https://devmcp.davemafy.xyz/sauce-motion-phase2/glass-loupe-cursor-20261119/). Examined the encoded 2.5s cursor crop, verified desktop and phone playback, 21 focused tests passed. 279 frames, silent 1080p60 H.264, full decode verified. SHA-256 `920d2a5ea7658cba735b13f14adf5a045e4236614b66cb2054d0c86dedeb09b0`.

## 2026-11-19 — Cinematic breakthrough gate: new 4s action-first opening, STILL FAIL

**Viewable, password-free 4s source-true film**: https://devmcp.davemafy.xyz/sauce-motion-phase2/linear-action-opening-20261119/ . Original encoded H.264 1920×1080/60fps **240 frames, exactly 4.000s**, AAC 48kHz stereo; SHA256 `92210560f4dc99695ddad25858b3c1ff02797a0ee0bde76488a65080069d9f69`. Real Linear public interactive preview DPR2/60 source SHA `7a539dd06e90257f237db0ad602301ca3fd8cc2db96ac802613904d010a8a454` (not authenticated). Genuine Reviews click at output **f45 / 0.750s**, actual code-diff result **f71 / 1.183s**, clean *single-original-source* edit excluding observed white-remount frames at f68, 2.25x source-grounded close-up, single genuine cursor (0 unrecorded/0 offscreen), original 48kHz sample-locked Foley. The complete MP4 fully decoded; public MP4/player returned HTTP 200; Chromium actually played at 1280×720 and 390×844 without media/JS errors or overflow. Private raw source, events and production worktrees are not public or changed.

**Independent Continuity Cloud workstreams**: film short-opening guard, capture timing/DOM evidence, optical summary crop protection and bounded quality self-healing were all done in separate ordinary ChatGPT main-only checkouts with no individual pushes; safe opt-ins integrated by the coordinator, including source-clock negative checks and bounded reject/repair. Original CMOkit 15s remains rejected **3/10**; the new Linear first-click cut improves pacing and sharpness but still **FAILS premium creative gate (~5/10)**: overly dense/dark code at phone width, visible source edit, small contextual pointer, no unmistakable business payoff, simple Foley not premium sound. Two 4s opening attempts exhausted. **No 900f/15s master was extended from this rejected Linear opening**; a separate concurrent real 900f Resend master exists below and also fails independent premium review. No misleading 10/10, no new VM, paid inference, fabricated private product behavior, or changes to dirty production. See [full source, code, test, worker, visual and acceptance evidence](SAUCE_BREAKTHROUGH_20261119.md), [CMOkit final baseline](SAUCE_CMOKIT_900_FINAL_RENDER.md), and per-lane reports `docs/PARALLEL_BREAKTHROUGH_{FILM,CAPTURE,MOTION,QUALITY}.md`. Next: capture a new authentic product interaction with a strong, stable, visibly meaningful before/after within about a second, then reattempt a bounded opening.

**Integration verification (2026-11-19):** Python phase2/phase3/source/QA **209 passed, 11 skipped**; legacy unittest **205 passed, 1 skipped**; TypeScript motion **34 passed** after npm ci --offline; focused audio/encoded frame/capture/quality/summary/camera checks **55 passed**; git diff --check clean. The published 4s asset decoded end-to-end and played on real Chromium desktop+390px phone. These test results DO NOT override premium-quality FAIL.

## 2026-11-19 — Independent film critic overrules Linear technical success: REJECT

The owner explicitly rejected the latest Linear technical film (`quality-source-director-20261118`) and instructed Sauce's coordinator to act as a **harsh independent film critic, not just a coder**. A new exact-media review in [docs/SAUCE_FILM_CRITIC_REJECTION_20261119.md](SAUCE_FILM_CRITIC_REJECTION_20261119.md) identifies encoded defects at 0, 1, 2.5, 3.8, 5.8, 7.8, 10.2 and 12.5 seconds against a privately retained Screen Studio reference. Subjective market-film rating ~3/10; **creative quality FAIL**, notwithstanding 790 valid frames, true source, synchronized cursor, good tests and accessible playback. First source second was nearly static (0.25/255 mean grayscale frame difference, 0% pixels changed by 15+), while reference activity at the analogous moment was materially higher; this is supporting evidence of *inert footage*, not a general film-quality algorithm. Dark UI palette alone isn't the problem; the lack of a dominant subject, unclear cause/effect across code review/task board, and delayed chart payoff are.

**Enforced next-work instruction:** Before further costly rendering or effects work, independently critique an actual three-shot picture board and the first three encoded seconds against live references. Require a dominant hero, visible authentic action, clear outcome and phone-width legibility. After two failed passes, change source/workflow rather than decorate weak footage. Do not market the currently linked Linear film, and do not call an engineering/test gate a cinematic-quality gate. Favor a continuous visually transformative authorized product workflow over the source-preview's disjoint remounts. No production code, media, systemd services, secrets or private working trees changed by this critic pass. The rejection document was committed to main as `4fe68cd35598f22fe1fcc47b91cf602ca54c5467`.

## 2026-11-19 — Verified native-DPR2 15-second Resend interaction film (creative gate OPEN)

**Main source/quality commit:** [`21b5bf02633b3fcc8ced7bd4f3e8661338275ea8`](https://github.com/Davemafy/sauce-vids/commit/21b5bf02633b3fcc8ced7bd4f3e8661338275ea8). Full source, reference and quality audit: [`docs/SAUCE_15S_RESCUE_AUDIT_20261119.md`](SAUCE_15S_RESCUE_AUDIT_20261119.md). Existing worker, other contributors' `main` commits, dirty `/opt/sauce-vids`, private browser profiles and earlier public films were preserved; no production deployment or paid inference.

**Playable true 900-frame film:** [watch 15-second Resend UI pricing study and real old/new video comparison](https://devmcp.davemafy.xyz/sauce-motion-phase2/resend-15s-20261119/) · [full 1080p60 H.264/AAC master](https://devmcp.davemafy.xyz/sauce-motion-phase2/resend-15s-20261119/master-1080p60.mp4) · [720p60 mobile preview](https://devmcp.davemafy.xyz/sauce-motion-phase2/resend-15s-20261119/preview-720p60.mp4). Master SHA256 `181d28043154ec805e4b0aadd96c5b2bdd3b7662decd6c4c9c056988cdc0d5ca`, 1920×1080/60fps, **900 H.264 frames/15.000 seconds**, AAC stereo48kHz. Original **genuine public Chromium/X11** Resend pricing footage at **2880×1800 DPR2,60fps,960 frames**, raw private source SHA256 `3d28c84e02406eb39822610e627613188fdc9482d8bc074fe316a58184123d58`; selected **source frames [51,951)**, no filler/repeated synthetic source states. The real slider is **discrete tier-snapped**, so do not claim every source frame is unique or that browser animation itself is 60 distinct steps. Price/DOM ROI change in actual source footage: Pro $20→$35 (2.925% region pixels), Scale $90→$160 (13.181%), Scale $160→$350 (14.356%). All three price-box output ROIs were 100% visible at their intended reading frames.

**Source/render corrections:** `scripts/capture_verified_slider_dpr2.py` records a real source-clock pointer sample **before** the first movement (the first pass lacked it and made the cursor materialize). `scripts/verify_native_slider_source.py` checks independently decoded slider component motion, actual price-pixel deltas, SHA and approximate +5-frame clock calibration. `scripts/verified_slider_cinema.py` creates a bounded 3-drag, source-true **15s 900-frame** shot plan from actual pointerdown/up and DOM price rectangles, using the existing Brimble-v15 rounded cursor, floating stage, camera shutter, water ripple and procedural Foley components. The first rendered pass was rejected for a clipped oversized 'Pricing' heading; second real DPR2 source and corrected framing inspected at 20 encoded timestamps and native source-price crops. No giant loupe, fabricated UI or unrelated montage. Strict full FFmpeg master/preview decode and 900 encoded-frame QA: **0 near-white flash violations**. **0** projected cursor-missing/offscreen frames. Six actual event-locked Foley cues at output frames **124,198,355,426,535,606**; original PCM→decoded AAC sample-correlation measured **0-sample lag for all six cues** (not sub-frame X11 capture accuracy). Playwright actual public HTTPS watch page, full/new/old MP4s and phone/desktop playback/seek at 390×844 and1280×720 all passed, no console/media/network failures or overflow after lazy comparison video loading.

**Second application:** shared `source_continuity_scan.py` classified real Resend as one uninterrupted 960-frame source, versus 170 actual raw glitch frames in the much different Linear public preview. `source_true_director.py` still passes the real Linear 790-frame evidence EDL; the shared renderer made an independently decoded **180-frame/1080p60** Linear smoke excerpt SHA `a17da80c1794379eaf8fb9021e5990078614fd1f92b2954ea8c879f`. The independently owner-rejected full Linear film remains **creatively FAIL**. New Phase2+3: **148 passed/11 skipped**; legacy unittest **205 passed/1 skipped**; StudioMotion TS **34 passed** after npm ci. Source code and new tests committed to GitHub main, not served as application deployment.

**Automatic URL workflow:** A concurrent isolated API run on current `main` genuinely generated a short **5.45s/327-frame** real Resend glass shot using `POST /v1/jobs` and bounded local direction, no additional inference; see earlier [URL-job handoff](SAUCE_HANDOFF.md). This 15s native 60fps film, however, used a **documented curated JSON action fixture** and was rendered privately via CLI, **not** the dirty production API. Generic, zero-touch paste-URL→15s premium-demo acceptance **NOT PASSED**. Its production `duration_seconds` argument is unreconciled; do not reset/deploy the production worker. No universal auto-director or owner/independent human approval was shown.

**Creative verdict:** provisional **6.9/10**, not publish-quality approval and not Screen Studio/Apple parity. Smooth, source-true, better than the preceding giant-lens Resend and disjointed Linear cuts; still a somewhat repetitive three-tier pricing slide on a naturally very dark page, with camera cropping peripheral cards and limited distinctive optical finishes. Needs a more compelling varied real feature journey, a generalized and visually checked URL workflow, and independent creative review before calling it 10/10. **Future work should improve the first 3 seconds' subject and legibility before buying more full renders; never mark a green encode as a cinematic quality pass.**


## 2026-11-19 — Coordinator independent COLD review of concurrent native Resend 900f film

Preserved concurrent main producer work `21b5bf0`/`f14b63f` and exact password-free [15s Resend master](https://devmcp.davemafy.xyz/sauce-motion-phase2/resend-15s-20261119/master-1080p60.mp4), SHA256 `181d28043154ec805e4b0aadd96c5b2bdd3b7662decd6c4c9c056988cdc0d5ca`. Original real DPR2 2880×1800/60 public pricing source with 3 actual value-delta proofs: **900 frames/15.000s, 1920×1080/60 H.264/AAC 48kHz** technically verified. Independent coordinator inspected actual encoded 1080p and 390px shots at 18 timestamps, not just render receipts. **Creative FAIL (~5/10, vs producer's provisional 6.9/10):** first ~1s still largely static; at **1.4s the enlarged 'Pricing' heading is actually cut at the upper edge**; 6.2–11.7s repeated focus shots slice inactive neighbor-card text including 'Enterprise'; multiple dark empty areas remain; final 12.8–15s becomes a tiny static wide view. Prices are clearly readable at 390px but body copy isn't. Independent audio evidence: 85% of 250ms windows below near-silent diagnostic threshold, notwithstanding correctly aligned six verified Foley events. Optional decoded-frame QA sees no blank/flash but no metric overturns the visual defects. No customer-value arc beyond repeated pricing-tier changes, and the 15s CLI fixture has NOT been demonstrated as the default production URL-to-video automation. **Not premium approved, not 10/10, no promotional launch signoff.** Full comparison and source proof: [docs/SAUCE_BREAKTHROUGH_20261119.md](SAUCE_BREAKTHROUGH_20261119.md) plus [producer original source audit](SAUCE_15S_RESCUE_AUDIT_20261119.md). Preserve source and existing unapproved films; choose a more visually transformative real workflow rather than endless slider adjustments.

**Post-merge independent suite, exact final combined checkout (2026-11-19):** pytest Phase 2/3 + source/QA **217 passed, 11 skipped**, legacy unittest **206 passed, 1 skipped**, TS StudioMotion **34 passed** after offline npm dependency restoration, diff check clean. Worktree is isolated main only; production dirty checkout and worker workspaces preserved. Visual verdict remains FAIL for both four-second Linear opener and full native 900f Resend film.
