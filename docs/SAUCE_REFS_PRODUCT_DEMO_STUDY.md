# Refs.video product-demo editorial study — applied to Sauce, 2026-11-18

**Scope:** Publicly viewable written film analyses at refs.video, not downloaded copyrighted reference videos, gated Pro plates or recreated reference branding. The reference page's own [source policy](https://refs.video/source-policy) keeps original media with its maker and transfers techniques, not footage or scripts. All numbers below are **Refs' reported measurements**, not independently measured from a local copy. No paid Refs access or inference was used.

## Three inspected real references

1. **REF-3721 — Loom, 21.8-second inbox-to-shareable-recording demo.**
   https://refs.video/v/2071890767996649939 . Refs publishes eight shot boundaries at 0, 5.50, 8.75, 13.10, 14.70, 17.48, 18.32 and 21.05 seconds, a 60 fps source, roughly 2.76 s median shot, and a 4-frame whip into the proof-transfer sequence. The most useful lesson: establish context → identify action → capture actual effect → hold a readable outcome. Its shot 1 is largely camera-static while interface elements move; the deliberate later reframe is tied to a changed state. These timings are reference-specific, not a Sauce template. The entry includes a physical desk insert and brand card; Sauce must not invent them for another app.
2. **REF-0542 — Framer, from design canvas to published site.**
   https://refs.video/v/yt-8AHPXm9Y6mI . The publicly visible 38-second reference description stresses a real completed page, editor proof and final Publish payoff. The full film/blueprints are gated, so no inaccessible plate or exact shot motion is claimed. Takeaway: product proof matters more than generic intro art.
3. **REF-3058 — Raycast Quick AI Feature Launch Walkthrough.**
   https://refs.video/v/1651942594509955074 . Public description reports a long real workflow followed by proof and a readable end. Full film gated. Takeaway: tolerate long static or minimally moving UI shots where real actions/results provide visual interest; do not force camera moves or animated text every second.

Cross-check: REF-3003 One's agent inbox, https://refs.video/v/2107549434280284460 — 31.5 seconds / 9 shots reported, includes stable shots >6 s; it is a mixed launch film, not a general Sauce UI demo template.

## The actual reusable grammar

- **Still establishing view:** for 3D Launch, saliency/gaze clues can protect real source timing but do not alone direct the cinematic camera. Previously this metadata could generate premature ambient zoom/pan without a recorded product action. Cursor and real source UI can move; camera waits for an actual trace hero or verified result. Experimental Hyper-Cut retains its existing ambient saliency behavior.
- **Verified action owns focus:** modal and source-verified feature events still activate the existing perspective rig. The physical 180/24/1 spring, 1200px perspective, source-true H0/H60 compositor, cursor and Foley are untouched. Feature-commit results now own up to 2600ms of the camera beat instead of the generic 1800ms click cap. No fake action or frozen interface is introduced.
- **Reading time follows outcome type:** source DOM kind selects a bounded hold without accessing sensitive text: verified pre/code **108 frames (1.8s)**; output **84 frames (1.4s)**; other verified results **66 frames (1.1s)**. All have 8-frame anticipation, 36-frame real H0/H60 first reframe and 12-frame ending. Only when the existing opt-in result-aware payoff has real evidence; malformed duration fails closed.
- **One continuous source-true detail:** for a code/pre result *only when its verified geometry fits*, hold the whole dialog 12 frames after the first dolly, then move the **same unaltered DPR2 source pixels** in a 24-frame bounded second dolly toward the actual code box, up to 2.9×. A final 108-frame code hold lets the two-line command read. No duplicate card, retyped text, fake copy success, or unrecorded product action. If the detail cannot fit, keep the original context shot.
- **Cuts serve picture:** never sync a visual cut blindly to music BPM or copy Loom's 8-shot timing. Prefer a source-recorded action boundary; the next shot must explain the real result.
- **Provenance first:** never use the reference logos, screenshots or original media as templates, and never replace real product states with typographic fakes.

## What this changes and what it does not

**Integrated:** scripts/studio-motion/src/cameraRig.ts (gaze guard, source-event ownership), scripts/result_payoff.py (result-kind duration and validated two-step native detail shot), compiled JS and targeted tests. No new preset, endpoint, AI model, scraper, subscription or UI rebuild.

**Not solved:** capture sharpness, small initial Brimble subject, gray backing slab, product-agnostic result capture, UI redesign, multi-product full-length direction or human visual approval. Short demos remain technical proofs.

**Next acceptance:** Compare encoded frames at first impression, action, modal and final result against the earlier same-source video; verify full FFmpeg decode, metadata, source receipt and Playwright at 390px/1280px. Repeat on **another actual product** (OpenSheets/Resend) with verified changes. Green tests do not establish art direction.


## Verified actual encoded output (2026-11-18)

**Published opt-in proof:** https://devmcp.davemafy.xyz/sauce-motion-phase2/refs-editorial-study-20261118/ ; exact [1080p/60 master](https://devmcp.davemafy.xyz/sauce-motion-phase2/refs-editorial-study-20261118/master-1080p60.mp4). SHA-256 f7863d6058cee63e3436600d8e845aa64acc9139e5d0557ea53f1f73d9250834; H.264 1920×1080/60 fps, 397 frames / 6.616667 s, AAC 48 kHz stereo. Full FFmpeg error-on-error decode passed. Actual private six-state Brimble capture, 3 semantic / 3 region checks, 152 genuine multi-plane frames, 0 fallbacks, four procedural Foley cues; private browser artifacts stayed on VM. Source session/workflow, raw shots, command data and HAR were not published.

The resulting payoff reports 60 moving frames over two real camera pushes (36 + 24), 12 contextual-hold frames, 108 sharp code-reading frames, 12 fade frames and native source target end scale 2.9×. The **actual encoded frame 310** was opened at full-derived and 390px display width: real Codex heading, two-line command and Copy control are visible; the text is substantially larger than the one-dolly comparison. The opening is still visually undersized and the gray backing slab remains prominent, so the film is **not human-approved as premium**.

Browser playback on the real HTTPS player passed at 390×844 and 1280×720: duration about 6.63s reported by Chromium, readyState 4, successful seek to 5.15s, no video/JS errors or horizontal overflow. Page/master/preview/poster all returned HTTP 200, with the expected content types. Existing three Sauce services remain active; no production renderer default or server config was changed.

Tests (current isolated main checkout): npm test 33/33; Python pytest tests/phase2 -q 82 passed / 10 skipped (browser gated); unittest discover -s tests -q 205 passed / 1 skipped; focused result-payoff 5 passed / 1 browser-skipped. Do not equate these green results with aesthetic approval. The required second-product proof (OpenSheets or Resend) **has not been run** for this new editorial family.
