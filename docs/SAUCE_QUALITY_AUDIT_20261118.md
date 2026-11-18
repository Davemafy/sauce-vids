# Sauce Phase 2 — action-first Linear quality audit (2026-11-18)

Status: **A BETTER VIEWABLE CANDIDATE, NOT AN APPROVED COMMERCIAL FILM**. Actual encoded video, real browser session, honest source evidence. Current verified source is the **public Linear interactive marketing preview**, not an authenticated account, Linear partnership or fabricated UI.

## Reference study and what transferred

- Locally opened the actual 10.3667-second official Screen Studio product demonstration (private reference media under the preserved Vultr worker; no republication). Its measured ~1.62× zooms move quickly, then settle for a readable hold and release; the frame begins with recognizable application context, not a random zoomed-in statistic. See [screenstudio-study.md](screenstudio-study.md).
- Consulted the previously documented [Refs product-demo study](SAUCE_REFS_MARKET_FILM_20261118.md): public Loom REF-3721 editing blueprint, action-causal cuts and relatively long stable shots; its restricted full media was not acquired. Refs and Screen Studio source content was not reused.
- Screen Studio's [official animation guide](https://preview.screen.studio/guide/animations) independently documents camera-motion shutter blur and stable reading holds, not unrestricted motion blur on every pixel.

## Source and starting defect

Real original Chromium/X11 capture: https://linear.app/ public interactive preview, DPR2 **2640×1440 @60fps**, 1110 original frames, source SHA256 `7a539dd06e90257f237db0ad602301ca3fd8cc2db96ac802613904d010a8a454`. The 19 original events / 368 real pointer samples were unchanged. Click targets: Reviews, Agent tasks, Agent Insights; their actual DOM state results include a code diff, a task board and measured metric cards for **3,389, 1,128 and 729**.

Prior [15.27s candidate](https://devmcp.davemafy.xyz/sauce-motion-phase2/linear-refs-market-20261118/) SHA `ed53e8ff8a1120eae23e86f0bb01f6db8f6437ed6d132bd12266e838256e831b`: first frame zoomed **2.55× into a future state**, hiding the actual product context before any action. The last camera ended **2.3× into the lower chart**; projection of the three actual first-row summary cards at its final encoded camera yielded **0%, 0%, 0%** visible source-rectangle coverage. The original 916-frame edit was watchable and technically valid, but misleadingly fragmented and poorly resolved at its opening and payoff.

## Rejection, repair, rerender, comparison

- Initial strict preflight rejected original EDL: `NONCHRONOLOGICAL_OPENER`, `NO_ESTABLISHING_SHOT`. A bounded mechanical recovery can drop that unsupported *editorial future teaser* (78 output frames) only if at least three source-true shots and seven seconds remain; it never fabricates/reorders pointer events, extrapolates UI or invents camera targets. Other failures stay rejected.
- v2 real 960×540 encode: action-first source states worked, but final reading hold was too short. Quality gate emitted `NO_FINAL_READING_HOLD`.
- v3 1080p encode: tested slower ending, but inspected frames exposed a clipped initial digit of 3,389. Rejected.
- v4 1080p encode: trialed subtle 3-sample camera-only shutter blur on movement. Stable holds remained byte-identical in the source compositor; moving-frame decoded changes were measurable (~1–4.3/255 MAE at selected edit movement frames), without source repainting. However, the original `wide` camera still clipped the third metric card. Rejected.
- v5 1080p encode: actual `summaryRects` provide an **overview group anchor** that frames *all three verified metric cards*. Final camera at **1.12×** covers **100%, 100%, 100%** of their projected source rectangles. The final shot begins wide, pushes to a **1.72× source-verified 3,389 card**, then releases to the intact three-card chart. The code, board and metric camera treatment remains opt-in, honest and legible at full desktop resolution. No fake UI or synthetic click was introduced.
- **Reused proven edit-clock machinery:** four real footage ranges 40–184, 259–484, 534–733 and 780–1050. Gapped source frames are omitted because the raw Linear preview contained white transition artifacts. This is a source-true editorial cut, not continuous-live replay.

## Final artifact and objective evidence

[Watch new 13.97-second film](https://devmcp.davemafy.xyz/sauce-motion-phase2/quality-action-first-20261118/) · [H.264 1080p60 master](https://devmcp.davemafy.xyz/sauce-motion-phase2/quality-action-first-20261118/master-1080p60.mp4) · [Source-aligned before/after frames](https://devmcp.davemafy.xyz/sauce-motion-phase2/quality-action-first-20261118/comparison-source-true.jpg) · [Full-film contact sheet](https://devmcp.davemafy.xyz/sauce-motion-phase2/quality-action-first-20261118/contact-sheet.jpg).

- Exact master SHA256 `834c13683c2a2171f0a1017fc05c1d4b29f5a89b227817830af844ff74236770`; FFmpeg full decode passed. **838 frames / 13.966667 s**, H.264 1920×1080 / 60fps with 48kHz stereo AAC. Private receipt: `studio/.tmp/quality-20261118/linear-v5-1080p60-shutter-silent.receipt.json` (not published).
- Three measured source click positions are inside their actual recorded `targetRect` (0px outside); output click cues at frames **121 / 341 / 545**, source-change whooshes **144 / 369 / 568**. PCM **670,400 samples** at 48kHz. AAC-decoded **670,720** samples includes end padding; sampled click transients peak on their intended frame. No paid inference or unlicensed music used.
- 280 regularly sampled encoded frames (every third frame): zero near-white flash violations using >3.5% near-white-pixels criterion; maximum measured near-white fraction **0.0028154**. Not a universal glitch-free guarantee.
- Inspected encoded contact at t=0, 1.55, 2.17, 3.48, 5.8, 7.25, 9.52, 9.9, 10.45, 10.95, 11.35, 11.85, 12.45, 12.95, 13.45, 13.80 seconds, and native 1920px and 390px output frames in payoff range.
- Live HTTPS returned 200 for review page, MP4 master, preview and poster. Playwright Chromium **1280×720 and 390×844**: 720p preview played, sought to 11.5s and advanced further, `readyState=4`, no media/JS errors or horizontal overflow.
- Existing unrelated dirty production and historical worker directories were not reset/deleted/overwritten. Only finalized public media/proof images are under the preexisting Nginx alias; private raw X11 video, event manifest, source screenshots, WAV and scripts stay on Vultr.

## Code, tests and limits

Reusable source changes: `scripts/editorial_quality_gate.py` with optional `--quality-gate` / `--bounded-repair`; `scripts/evidence_edl_renderer.py` authentic `overview:<state_index>` group camera and optional `--camera-shutter`; `scripts/camera_shutter.py` 3-source-warp shutter samples only while the verified camera is in motion. No changes to standard/non-EDL rendering defaults. Source rect and out-of-bounds checks fail closed.

Testing: **124 passed / 11 skipped** across Phase 2+3, **205 passed / 1 skipped** legacy unittest, **33 passed** TypeScript planner after npm ci, targeted camera/edit gate tests green. No code/project dependency rebuild, new external service, GPU or paid calls. Exact source commit is recorded in the living handoff after the source is committed to main.

## Creative judgment and stop-loss

**Provisional in-house film score: 6.5/10, NOT an independent human approval.** Truth 9/10; intentional camera and editing 6.5/10; mobile legibility 6/10; cursor clarity 7/10; optical movement 6.5/10; audio 6/10. Improvement is real and demonstrable, but the source interface is naturally dark/dense, the marketing preview switches between unrelated feature states, and source-remount flashes force three hard editorial cuts. There is no full narrated, dependent workflow, no bespoke object animation, no independent human review, and no second-app proof of this EDL recipe. Do not claim Apple/Linear/Screen Studio parity or launch/sale readiness.

**Most important unsolved product gap:** `backend/url_film_recovery.py` has a bounded rejected-film policy, but the deployed URL→video StoryArc still has unreconciled untracked modules and prior owner-rejected CMOkit work. This EDL preflight does **not** automatically direct arbitrary pasted URLs. Next highest-value quality loop is to reconcile that pipeline safely, test automatic action discovery against a second verified public app and enforce a source/outcome/visual rejection before generating a full expensive film. Record the actual MP4 and seek human approval before commercial exposure.
