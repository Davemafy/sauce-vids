# Sauce — Launch-quality implementation research and builder contract

Date: 2026-11-17
Status: research and independently inspected proof; **not an implementation signoff**
Target: Davemafy/sauce-vids, main only
Reference main at research time: 7f2102e0bf56090563730720cc45f8a96bb0a03c
Owner priority: exceptional, source-true 16:9 product-demo clips that reduce recording/retake labor. Sauce is not a general launch-film director.

## 0. Non-negotiable bootstrap

Before code, read AGENTS.md, docs/SAUCE_NEW_CHAT.md, docs/SAUCE_STANDARDS.md, docs/SAUCE_HANDOFF.md, docs/sauce-motion-phase2.md, docs/url-to-video-backend.md, and the actual source/tests. Re-query GitHub main and recover the persistent Vultr worker. Preserve local dirty/untracked files and private media. Do not checkout/reset the old release tree to current main, create a branch, or rebuild already-complete systems. A previous worker checkout is at an old SHA with extensive unrelated changes. The latest GitHub main supersedes any SHA in this document.

## 1. Verified reality and precise remaining defects

The flagship Phase 2 is an existing source-true Chromium/TypeScript FramePlan/Python OpenCV/FFmpeg compositor. It already has real H0/H60 depth, a verified modal-first camera response, the user's preferred native cursor with a **one-frame** depth seam repair, action-aligned cut, deterministic Foley and optional source-backed result payoff. Preserve these.

The public URL-first pilot is already deployed at https://devmcp.davemafy.xyz/sauce-app/studio, with private permission gating and a real continuous Chromium recording path. It is **not** the same renderer. Active URL code is backend/product_explorer.py → backend/url_engine.py → backend/live_capture.py → backend/live_render.py. The old backend/state_film.py montage is retired. URL capture currently uses Playwright record_video at 1280×720, DPR 1, an injected **16px circular marker**, source WebM, and FFmpeg upscaling plus 60fps resampling to the master. The receipt correctly says replay_verified=false. Never call that a native high-density 60fps capture.

On 2026-11-17 independently fetched and fully decoded:
https://devmcp.davemafy.xyz/sauce-motion-phase2/result-payoff-camera/master-1080p60.mp4
- SHA256 ef297669e8fc0c1599a59e35b7dcff5a662773ce63c99789585e18d19f6c9e9a
- 1920×1080 H.264, 60fps, 295 frames/4.916667 seconds, AAC 48kHz.
- Actual full-size encoded frame 44 (~0.733s): source Brimble page and dark terminal shell still visible.
- Actual encoded frame 48 (~0.800s): **large gray rectangular occluder visibly covers the right side of the opening Connect your agent dialog**, including portions of real text/choices. The surrounding browser has been dimmed. This is a P0 visual failure, not a player CSS problem.
- Encoded frame 250 (~4.167s): the source-true Codex command is legible, but the top of the modal is cropped beyond the stage top, leaving a partially cut off Claude row. The real command line naturally wraps within the original DOM width, splitting the host name. The final sharp reading hold is 42 frames (~0.7s), which may be too little for that result.
- Contact review shows a coherent end-shot camera move but opening product/action is still tiny before the click and the resulting film remains only a 4.9-second technique case, not general quality proof.
- HTTP 200 independently checked for Studio, /studio/samples, Phase 2 result-payoff page, and URL auth endpoint.

Prior handoff already acknowledged the ~0.72–0.82s terminal/modal conflict, and the current screenshot confirms it remains. Exact root cause is **not established**: must distinguish original Chromium foreground pixels, source-site stacking order, modal animation, clean-plate capture, projector matte, and camera/temporal selection. Do not assume this is just a mask error without an A/B probe.

Reference analysis already performed by project in docs/screenstudio-study.md: Screen Studio official 10.3667s example had two distinct ~1.62× camera pushes, deliberate holds, and releases. Its actual motion is not a license to reproduce copyrighted footage. Our editorial win is action → revealed state → readable hold, not shaders everywhere.

## 2. Priority P0 — eliminate opening modal occlusion

Read scripts/modal_depth_capture.py, scripts/multi_plane_depth.py, scripts/session_replay.py, scripts/cinematic_stage.py, and tests/phase2/test_multiplane_depth.py. The existing verified_modal_background() hides a genuine dialog for the H0 background plate; Brimble-specific dark-terminal suppression is opt-in. The current final foreground screenshot is collected separately, and its compositing origin must be proven.

Diagnostics FIRST on a repeatable pinned capture:
1. Render a per-frame diagnostic at frames 40, 44, 46, 48, 50, 54, 60 with four sources side by side: unmodified Chromium screenshot, clean H0 plate, masked H60 source and final composited output. Include DOM bounding rects, active z-index, computed visibility, modal animation progress and whether the dark terminal shell was hidden.
2. Check if the gray wedge exists in the unmodified source at the same source time. If yes, it is source/UI overlap; do not pretend to repair it through a post-production matte. Prefer a narrowly documented, opt-in presentation-only hiding of a **DOM-verified decorative terminal shell** during the modal shot, restoring styles in a finally block. Never remove actual interactive content or infer a dark rectangle from color.
3. If raw modal pixels are clean but composite is broken, correct the H60 alpha/matte and projection. Derive both foreground alpha and rounded-border coverage from the same verified modal border geometry. Warp the alpha and real pixels with the same H60 homography, premultiplied-alpha compositing and matching sampling/border behavior; avoid leaving an opaque rectangular residual. Retain 1-plane fallback on missing evidence.
4. If the modal is temporarily in a genuine transition or obscured by the live page, **delay the lift** until its visible pixels pass a geometry/occlusion check; preserve the truthful underlying source rather than manufacturing modal contents or freezing arbitrary unrelated frames.
5. Ensure all source-side temporary style overrides restore even on capture failure; redact diagnostic traces/screenshots and keep them private.

Acceptance:
- In the 0.65–1.10s region, no black/gray terminal or rectangular matte crosses visible modal content in the full-size exported film.
- Genuine text and modal regions come from captured Chromium; no reconstruction, text overlay, synthetic success or screenshot inpainting.
- H0/H60 projection, pointer hotspot on click, existing one-frame seam and action-cut frame 125 unchanged unless a frame-specific regression proves necessity.
- Deterministic pinned-input pixel QA plus a negative case for no verified modal, nested popup and failure cleanup.
- Actual encoded 60fps film, not only a screenshot or green unit test, independently reviewed.

## 3. Priority P1 — make the payoff crop contextual and readable

Read scripts/result_payoff.py and the result branch in scripts/session_replay.py. The current endFocus weights .65 result / .35 modal, and fixed zoom factor 1.34 can crop the modal header. Replace the hardcoded geometric heuristic with a bounded **shot layout solver** (not an ML model):

- Inputs: verified result box, dialog box, viewport dimensions, stage bounds, current pose, safe margin, source DPR.
- Find the maximum scale that keeps the **result region, identifying row/header/context, and a 24–48px projected safe margin** in frame. If these constraints conflict, prioritize complete result and Codex context over raw zoom magnitude; back off.
- Project and check all four corners after H0/H60 tilt, not only axis-aligned focus. Never shift the source text or widen its DOM just to fake a one-line URL. Natural source line wrapping is allowed; make the complete command readable.
- Replace the fixed 42-frame reading period with an explicit length/category-aware hold bound (first prototype 0.9–1.5s for a code command), then visually test against the owner's objection to the earlier frozen 1.6s ending. A moving camera is not a substitute for readable holding.
- Preserve direct full-resolution DPR2 source reprojection for the dolly; no second lossy zoom, no ungrounded callout, and no invented click.
- A/B the current and candidate outputs at 1920×1080, 1280×720 and 390×844. Include complete beginning/middle/end motion playback, not isolated frames.

Acceptance: full original command and its app identity visible, no unintended viewport clipping, readable frame at native resolution and normal-size mobile video, authentic final state, Foley time map still exact.

## 4. Priority P1 — upgrade URL engine from authentic recording to art-directed footage

The active URL pilot is a credible *capture substrate* but currently not the flagship film system. Do not turn it back into screenshot montage, and do not claim its 1080p60 label implies source 1080p60 fidelity.

A. **Measure source raster options before committing to a recorder rewrite.** Benchmark the same controlled public fixture under three capture candidates:
   - current 1280×720 DPR1 Playwright record_video;
   - 1280×720 CSS viewport at DPR2 with controlled record_video_size and measured **actual encoded detail**, not theoretical DPR;
   - existing Linux headful Chromium/Xvfb + FFmpeg screen capture at a genuine 1920×1080 or 2560×1440 physical raster if the existing VM can sustain it.
   Compare source text edge fidelity, actual measured frames/s, dropped/repeated frames, load, render time and safety. Pick the least complex source-true capture that visibly beats current upscale. Do not market interpolated/resampled 60fps as original 60fps.

B. **Remove the in-page circular faux pointer from the saleable cinematic preset.** Capture browser pointer coordinates and click times on the same monotonic clock as the video; draw one small, normal premium arrow in post, using hotspot-preserving CSS→source→camera projection. Add a clicked-state frame and retain the natural recorded motion; do not generate 140ms depth ease. Keep the marker as fallback only until the new pointer track is proven.

C. **Introduce a small bounded editorial timeline, not autonomous multi-agent vision choreography.** Event timeline contains observed pointer approach, actual click, verified change, user-visible target geometry, scroll, state hold and cut. A rule director selects:
   establishing frame (brief) → real approach → genuine click → observed change → camera reframe (AFTER change) → readable hold → quiet release. For marketing-only sources, clearly label public-site showcase and use paced source scrolling with no invented feature outcome. The single existing Gemini element-ID direction call can choose what to film but may not invent evidence or arbitrary selectors. Geometry and temporal constraints are deterministic.

D. **One honest renderer boundary.** Feed the continuous browser stream and its clock-aligned event/target sidecars through shared stage/camera/pointer/editorial primitives **where valid**, without claiming HAR-backed deterministic replay. The verified replay/3D H0/H60 mode remains a higher-assurance optional source type; do not splice private capture data or incorrectly declare that continuous source has verified DOM replay. Store explicit source-mode and quality/provenance labels.

E. **Build three distinct polished public workflows**, not three presets of the same fixture: a source-visible modal flow, a source-visible form/input state with NO submission, and a bounded scroll/showcase. Use real public controls. SEAL can support the safe paste-text example; Igor public showcase and Paldey preview are coverage cases, not claims of private app interaction. Avoid depending only on brittle third-party pages; add local non-private fixtures.

Acceptance:
- At least three source-true 16:9 films with recognizably different real interaction geometries, beginning/action/result pacing and no montage transitions.
- Each has source SHA, observed action receipt, actual source cadence, original resolution, encoded stream report, media decode, contact sheet and owner-viewable preview.
- Side-by-side native/full playback shows a real quality increase over current URL-engine output. If source recorder cannot meet legibility, do not misrepresent a 1080p upscale as premium.
- Reuse existing operational safety and app. No full rewrite of Phase 1/2, Studio API, or credential model.

## 5. Priority P2 — visual QA and reliability that catch defects before owner review

Build a lightweight rule-based visual critic (local OpenCV + saved verified geometry; no per-frame paid vision required):

- Rectangle intrusion: detect abrupt large, flat-edged opaque overlays intersecting the verified modal's content region. Pinned regression must flag existing frame 48 and not flag a legal dialog border/shadow.
- Projection continuity: assert no unexpected H0/H60 cursor hotspot jumps on non-cut frames. Preserve preferred trace; numerical smoothness is a diagnostic, not aesthetic approval.
- Crop: project protected DOM rect corners and fail when a required header/result passes outside safe areas for settled reading frames.
- Legibility: flag source that is upscaled beyond measured raster fidelity or result visible for fewer than the configured reading frames. Use the local receipt and geometric checks, not OCR on private UI.
- Narrative: event order cannot start post-click zoom before click or classify a marketing showcase as a demonstrated private product outcome.
- Full media gate: ffprobe H.264/16:9/frame count/48kHz when Foley exists, FFmpeg -xerror full decode, muted audio stays silent, progressive MP4 playback, Range support, desktop/mobile browser errors and overflow, consistent source lineage.
- Review artifacts: versioned contact sheet of 6–12 event-selected full-resolution frames; A/B before/after; exact timecode defects; protected only if capture is private.
- Subjective creative review is mandatory: no automatic numerical "premium grade" or launch signoff.

## 6. Launch decision and product honesty

**Today:** the protected URL pilot and flagship proof are online, but a broadly self-serve premium Sauce launch is not quality-approved. The Studio currently offers private pilot access; public URL filming intentionally excludes authenticated apps, purchases, risky submissions, and private workflows. Preserve those bounds.

Launch as **invitation-only public-site beta** after P0 and a credible P1 vertical slice. Product promise can be "Sauce turns a genuine public product interaction into a polished, reusable demo clip" for supported public sites; do NOT promise arbitrary authenticated SaaS workflows, full product launch films, or live 60fps native capture without proof.

Before opening beyond pilot:
1. Visually approved flagship Brimble film with corrected modal and result crop.
2. Three externally reviewable distinct URL-output films, with at least one interactive workflow, not only scrolling. Original and new side-by-side available.
3. Browser journey on desktop and 390×844 mobile: enter URL → inspect → actual bounded capture → progress with real stages → playable MP4 → download → review. Test failed URL, restricted host, unsupported auth, provider unavailable and restart.
4. Security and capacity: keep private pilot codes, same-origin cookie, server-only AI key, SSRF/DNS/redirect controls, response size/duration bounds, cleanup and job quotas. Add measured cost/job, concurrency, disk retention and abuse checks before unrestricted opening. No public auth-state/HAR uploads. Review OWASP guidance before adding a user-upload feature.
5. Landing page shows the **actual updated 1080p film**, not stale baseline or fake storyboard. Sample and URL pipeline outputs must not be mislabeled as equally verified. Show capability and limitations with precise wording.
6. Capture 5 external human reviews (at least 2 motion/video designers), asking: "Would you use this footage in your workflow?", "What exact frame looks cheap?", "Would you pay to avoid re-recording?" Revenue and repeat usage, not green CI, decide whether to widen scope.
7. Document p50/p95 render time, failure rate, full job costs and visual acceptance on a small nonprivate pilot sample before charging generally. No speculative throughput promises.

Suggested execution sequence: **P0 modal intrusion** → **P1 payoff context/hold** → **URL capture resolution A/B** → **URL source-clock/pointer/editorial reuse** → **three multi-domain QA films** → **private beta release review**. Work sequentially on main with each scoped verified commit and handoff update. Parallelize read-only research/tests if useful, but avoid competing edits on the same files.

## 7. Builder delivery contract

For EACH milestone provide: (a) exact main SHA before/after and a clean/preserved worktree account, (b) observed defect and source proof, (c) smallest code and tests changed, (d) commands/test counts and file hashes, (e) exact public or protected preview URL, (f) at least 3 actual inspected decoded frames and mobile/desktop playback, (g) defects still open, (h) updated docs/SAUCE_HANDOFF.md. No generic "complete" without this evidence.

Use only current main and the existing persistent worker; if main advances, reconcile without force push/reset. No paid services, broad public release, purchases or private session exposure without owner's explicit authorization.

## 8. Research and primary technical references

These inform a pragmatic implementation, not a claim Sauce has cloned their engines:

- Official Screen Studio automatic zoom: https://screen.studio/guide/auto-zoom — click-focused zoom vs manual framing
- Official Screen Studio animation controls: https://screen.studio/guide/animations — focus/stability and per-motion blur differ; evidence supports restraint, not permanent cursor following
- Sauce's measured, licensed-internal reference analysis: docs/screenstudio-study.md
- Playwright Trace Viewer: https://playwright.dev/docs/trace-viewer — action-aligned snapshots and recording strip useful for diagnosis
- Playwright Page API: https://playwright.dev/docs/api/class-page — real screenshot/DOM capture and deterministic animation options
- Chrome DevTools DOMSnapshot: https://chromedevtools.github.io/devtools-protocol/tot/DOMSnapshot/ — bounding/layout evidence, not full semantic understanding
- OpenCV geometric warps: https://docs.opencv.org/4.12.0/da/d54/group__imgproc__transform.html — warpPerspective, border and interpolation discipline
- FFmpeg formats: https://ffmpeg.org/ffmpeg-formats.html — faststart and stream delivery
- Playwright authentication: https://playwright.dev/docs/auth — sensitive browser storage state must stay private
- OWASP file upload: https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html — when/if per-user source uploads are introduced

**Principle:** a better film comes from the right real action, a readable result and restrained camera. A shader stack cannot compensate for source occlusion, low-density capture, absent narrative or an unverified product action.
