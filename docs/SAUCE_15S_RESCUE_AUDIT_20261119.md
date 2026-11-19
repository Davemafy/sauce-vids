# Sauce Phase 2 — genuine 900-frame cinematic film and visual acceptance audit

**Date:** 2026-11-19. **Status:** final 15-second candidate exported and reviewed; **creative signoff and universal URL→film acceptance remain OPEN**.

## Published video and original browser proof

[**Watch the 15-second Resend study**](https://devmcp.davemafy.xyz/sauce-motion-phase2/resend-15s-20261119/) · [Exact playable 1080p60 H.264/AAC MP4](https://devmcp.davemafy.xyz/sauce-motion-phase2/resend-15s-20261119/master-1080p60.mp4) · [Prior film vs revised video in two real players](https://devmcp.davemafy.xyz/sauce-motion-phase2/resend-15s-20261119/) · [Earlier/later source-frame comparison](https://devmcp.davemafy.xyz/sauce-motion-phase2/resend-15s-20261119/comparison.jpg).

**Master SHA-256:** `181d28043154ec805e4b0aadd96c5b2bdd3b7662decd6c4c9c056988cdc0d5ca`. Original public source URL: `https://resend.com/pricing` (no account, sign-in or personalized data). Physically recorded in isolated Chromium/X11 via pre-existing Vultr worker: **2880×1800 native DPR2**, 60fps H.264, **960 continuous decoded source frames**. Original source SHA-256: `3d28c84e02406eb39822610e627613188fdc9482d8bc074fe316a58184123d58`. New master uses **exactly source frames 51–950 inclusive**, no repeated/constructed source states, yielding **900 output frames at exactly 1920×1080/60fps, 15.000s**. AAC 48kHz stereo. Original cursorless source, browser event metadata, source stills, browser profiles and private PCM are never published.

Three genuine recorded Playwright/X11 mouse-drags against the **visible real native pricing slider**, with actual browser value + DOM price + independently decoded-source pixel checks:

| Action / real observed result | DOM observed outcome | Original source price ROI changed pixels |
| --- | --- | --- |
| Pro 50K → 100K emails/month | $20/month → **$35/month** | **2.925%** |
| Scale 100K → 200K | $90/month → **$160/month** | **13.181%** |
| Scale 200K → 500K | $160/month → **$350/month** | **14.356%** |

Price boxes were independently projected into output film and checked at output frames **222 / 450 / 630**: **100% of each verified source result rectangle remained visible**. No change was inferred solely from model-generated copy. The browser slider **snaps** at tiers, rather than animating through 60 distinct values per second; source validation reports exactly 3 real native tier transitions and correctly does not claim that all 60fps source frames are unique. Independent source timing reconciliation: physically observed slider-right-edge versus recorded cursor yielded an estimated **+5-frame clock offset**, median residual 23.495 physical pixels after track-width/bias removal; this is not a fully instrumented sub-frame capture timecode.

## Observed reference footage, not reference re-creation

Privately inspected **actual** locally retained Screen Studio 10.3667-second product demonstration (622 frames/1280×720/60fps), prior 197-frame Brimble authentic ripple clip and prior 16-second Resend oversized-loupe film. Full reference footage has **not** been republished. A preexisting feature-matched Screen Studio motion study measured approximately **1.62×** meaningful pushes over **0.48–1.32s** and **5.88–6.84s**, with roughly 1.8–3.0s / 8.64–9.84s releases. These are observed screen feature displacements, **not** Screen Studio's official proprietary camera settings.

The applied film grammar is **real product context → cursor approach → actual slider drag → verified price text → deliberate close-reading hold → another live value → end on full genuine product**. Existing tested professional Brimble reference-v15 rounded cursor, floating source matte and `click_water_ripple.apply_click_water_ripple` were reused. Camera is driven by the captured slider/price rectangles rather than guessed magic coordinates, with bounded quintic smoothstep and optional 3-sample source-preserving camera-only shutter. Measured actual output camera scale from **0.965×** wide to **1.84×** focused; zoom parameter maximum delta 0.01932 per 1/60s frame. Across source landmarks, projected maximum displacement approximately **12.2–13.1 output pixels/frame** and second-difference below **0.67px/frame²** (excluding naturally snapped application content). The film never overlays UI from different source states.

## Actual iteration and rejected choices

- **First real 15s render** already passed codec/tests, but in its actual contact frames its pointer appeared mid-opening and the first push left partial giant “Pricing” heading text clipped. **Rejected for final delivery.** The input was recaptured with a real timestamped stationary first-pointer sample. Camera shot keys were retimed relative to the first observed approach and tightened. Source A and source B live as separately hashed immutable worker artifacts.
- **Second genuine capture / final output** has zero unrecorded cursor frames and zero projected offscreen pointer frames for its full 900-frame plan. The first slider closeup avoids the cropped title. Multiple price reading holds are clear at full-resolution native output and at the 390-pixel mobile-player scale.
- Prior 16-second Resend film used a giant circular lens covering real prices; the revised study discarded that visually destructive approach instead of layering another shader. It includes a **real, silent before-film** player next to the new rendered film, not just a pair of static thumbnails.
- **Remaining creative caveat:** Resend's page is a simple pricing calculator, not a dramatic, multi-step application flow. Repeated pricing-tier changes, some clipped neighboring cards at zoomed edges and a very dark natural product palette still lack the feeling of a top studio's diverse UI motion. A subtler ripple is honest but not visually distinctive enough to claim Apple/Screen Studio parity. Adding a large lens would be a regression. No independent human rater/owner-approved score was obtained.

## Verified objective quality gates

- H.264 master 1920×1080, 60fps, **900 frames/15.000s**, one AAC 48kHz stereo track; strict **full-video and audio FFmpeg `-xerror` decode passed**. Preview Lanczos-downsampled to 1280×720, 60fps, AAC 48kHz also decoded.
- **All 900 encoded video frames** sampled for near-white flash every third frame: zero flash violations (near-white >3.5% criterion), maximum near-white fraction 0.0012413. Of 300 decimated comparison samples, 79 exceeded a small frame-difference threshold; screen-state uniqueness and camera motion are not conflated.
- Real recorded 3 source clicks/following price observations and 3 procedural Foley results. **Output cue frames** click **124 / 355 / 535**; result **198 / 426 / 606**. The 720,000-sample 48kHz original stereo PCM was independently correlated with separately decoded AAC at all six cues: **0-sample lag across all six**; decoded audio peak ≈0.0739. This proves output cue lock, not absolute X11 source clock precision beyond the approximate +5-frame calibration.
- HTTP **200** for HTTPS watch page, 1080p MP4, 720p preview and old 16s visual comparison; master checksum matched local source after public copy.
- Real Playwright Chromium site and native video played, sought to **3.55 / 7.83 / 10.82 / 14.60 seconds** and advanced at **1280×720 and 390×844**; decoder `readyState=4`, no JavaScript exceptions, no request failures after lazy-loading auxiliary players, no horizontal overflow. Old 16s film separately played and sought to 9.1s, no media error.
- `../.sauce-render-env/bin/python -m pytest tests/phase2 tests/phase3 -q` → **148 passed, 11 skipped**; Python legacy `unittest discover -s tests -q` → **205 passed, 1 skipped**. TypeScript StudioMotion `npm ci && npm test` → **34 passed**. No paid inference or new infrastructure. Current `main` integration verified after rebasing the isolated clean checkout over concurrent upstream cursor/glass-loupe changes.

## Second visually different real application regression

On original public Linear preview: DPR2 2640×1440/60fps capture SHA256 `7a539dd06e90257f237db0ad602301ca3fd8cc2db96ac802613904d010a8a454` was processed with the SAME `source_continuity_scan.py`, finding actual bad ranges **[0,0], [185,257], [484,533], [733,778]** (170/1110 source frames). The SAME scanner on the new Resend real capture correctly found **zero** unstable ranges, full 960-frame stable source. Existing `source_true_director.py` generated source-verified Linear 790-frame storyboard with **zero offscreen cursor frames**, and `evidence_edl_renderer.py` produced an independently fully decoded **180-frame, 1080p/60fps** real Linear smoke excerpt SHA256 `a17da80c1794379eaf8fb9021e5990078614fd1f92b0a412992b2954ea8c879f`. Its actual encoded 8-frame contact was opened and critically examined; it **remains dense and is not a premium film**. Prior complete genuine Linear film preserved: https://devmcp.davemafy.xyz/sauce-motion-phase2/quality-source-director-20261118/ .

**Transfer boundary / concurrent URL workflow:** Cross-app continuity detection, source hash checking, cursor/stage effect machinery and real-event EDL rendering were tested. The **new 15s pricing-slider director** specifically applies to authorized, DOM-verified range/price workflows, with the action schedule supplied by a JSON fixture; it did **not** pass through the deployed URL job service. Meanwhile current GitHub `main` independently contains a separate **short-form URL job prototype**, integrated by other contributors at commits `f314b20` and `3908337`: an isolated `POST /v1/jobs` request against public Resend pricing produced job `c01817e5007497a9ffdfe822` at `needs_review`, a **5.45s / 327-frame H.264 1080p60** verified glass shot from a **25fps** capture (master SHA `4b739b8e269f001540e41b2cda3c71f2f213940c5bad44564493d378e23c4b2a`), and a separate Bootstrap panel test. That demonstrates **bounded automatic URL capture/routing exists and was tested in an isolated API**, not that the 15-second native 60fps quality criterion passed through it. The live production service still operates a locally modified `/opt/sauce-vids` tree with an unreconciled `duration_seconds` API argument, so **no full, production, arbitrary URL→15s premium film pass has been verified**. Do not overwrite the dirty production tree or deploy either candidate. No paid inference calls were used for the local range demos.

## Creative scorecard — provisional, not independent/owner approval

| Dimension | Self-score /10 | Evidence and shortcoming |
| --- | --- | --- |
| Capture/source truth | 9.0 | Native DPR2 verified, no remounts, discrete actual slider tiers |
| Story | 6.6 | Three true pricing deltas, but one feature with limited emotional payoff |
| Cursor | 8.0 | One proven small asset, exact recorded path, zero missing/offscreen |
| Camera | 7.4 | Measured smooth zoom and deliberate holds, less punch than reference |
| Scrolling | N/A | Real slider workflow contains no page scroll; no scrolling quality claim |
| Transitions | 7.8 | Continuous one-take; no editorial remount cut, but repetitive |
| Legibility | 7.5 | All prices completely in frame; detailed other UI small on mobile |
| Optical finishing | 6.6 | Reserved water refraction and matte, no fake lens or sparkle |
| Pacing | 6.8 | Clear three-beat structure, some long dark unchanged states |
| Publishability | 6.7 | Good private study, lacks credible premium/art-direction approval |
| **Overall** | **6.9 provisional** | **Quality gate not passed** |

**The top three remaining problems:** (1) Story selection—the source product's three tier changes are too repetitive for an exceptional 15-second flagship; use a stronger real multi-step interface with distinct payoffs. (2) Frame-by-frame camera art direction: though smooth, the current closeups occasionally cut through inactive neighbor cards, rather than owning the entire composition. (3) Automatic workflow: the current capture fixture is curated by an engineer, and the deployed URL→video StoryArc isn't verified to discover, capture, direct, review and repair an arbitrary product unaided. None are solved by yet another generic glow/ripple.

**Stop-loss conclusion:** This is an objectively better source-true 900-frame demo than the earlier tiny/disconnected Linear cut and giant-obscuring Resend lens. It **does not earn 10/10**. Do not promote the public test film to a saleable flagship or report “paste URL→premium film” passed until an independent human visually approves an end-to-end automated second product film with varied real interactions. The reference comparison was internal (Screen Studio footage locally; no redistribution). No independent reviewer was available in this execution; scores are provisional.

## Reproduce with permitted worker

```sh
cd sauce-cinematic-1119
# A physically isolated Chromium/X11 session. Do not overwrite prior captures.
PYTHONPATH=scripts ../.sauce-render-env/bin/python scripts/capture_verified_slider_dpr2.py \
  --fixture tests/fixtures/resend-pricing-dpr2-15s.json --out PRIVATE_CAPTURE_DIR
../.sauce-render-env/bin/python scripts/verify_native_slider_source.py \
  --video PRIVATE_CAPTURE_DIR/source-real-dpr2-60.mp4 \
  --manifest PRIVATE_CAPTURE_DIR/source-events.json \
  --out PRIVATE_CAPTURE_DIR/source-validation.json
PYTHONPATH=scripts ../.sauce-render-env/bin/python scripts/verified_slider_cinema.py \
  --source PRIVATE_CAPTURE_DIR/source-real-dpr2-60.mp4 \
  --manifest PRIVATE_CAPTURE_DIR/source-events.json \
  --validation PRIVATE_CAPTURE_DIR/source-validation.json \
  --out PRIVATE_FILM/master-1080p60-silent.mp4
```

No raw capture, private source sidecar, Xvfb session, saved browser profile, original Screen Studio reference movie or key is committed or publicly served.
