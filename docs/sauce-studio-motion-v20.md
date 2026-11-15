# Sauce v20 — StudioMotion: temporal warp, projected floor, semantic callouts

**Silent landscape proof:** https://devmcp.davemafy.xyz/sauce-studio-v20/

This release contains no audio generation, analysis, soundtracks or audio muxing.
The new motion options are opt-in; existing Sauce export behavior stays intact.

## Architecture (real MP4, not decorative web CSS)

Source: `scripts/studio-motion/src/`

| Module | Responsibility |
|---|---|
| `timeWarp.ts` | Source-time to output-time monotonic map, action protection, deadzone classification |
| `StudioStage.ts` | Strongly typed window/perspective/reflection contract and 3D anchor projection |
| `KineticCallouts.ts` | Evidence-only CTA extraction, cooldown/lifetime enforcement |
| `bridge.ts` | Typed JSON planner interface for the existing Python exporter |

Runtime adapters:

- `scripts/studio_motion_bridge.py`: Node planner over stdin, provenance checks and bounded safe selector fallback.
- `scripts/session_replay.py`: Chromium clock advances using the source timestamp for each **output frame**; camera, pointer, modal transitions and original verified UI all advance against the same source clock.
- `scripts/studio_motion_blur.py`: 5-tap directional Gaussian shutter triggered by accelerated, *moving* content or confirmed fast scroll, not by static UI.
- `scripts/cinematic_stage.py`: original projected 3D window + optional floor (roughness-equivalent 4.5px Gaussian, 0.25 reflection strength, near-floor fade), contact shadow and shifting broad cast shadow.
- `scripts/studio_motion_callouts.py`: projected anchor coordinates via the same 3D homography as the cursor, 16px local backdrop blur, specular pill and dot/leader; mass 0.8 / stiffness 220 / damping 20.
- `scripts/session_capture.py`: adds bounded, redacted `eventType`, `tag`, `role`, `ariaLabel`, and `innerText` metadata on high-intent events.

No React root wrapper was created: the actual Sauce export is Python/OpenCV/Chromium, and the 3D studio floor is in the encoded MP4 itself. TypeScript owns the deterministic typed planning layer.

## Temporal semantics

- Click, pointerdown, submit, modal-open, initial text-field focus generate **400ms pre-roll / 300ms post-roll** windows at exactly 1.0× source speed.
- Adjacent protected windows are merged and are never accelerated.
- Idle gaps strictly longer than 800ms qualify for a maximum 4× speedup. Explicit loading spans and continuous observed scrolling also qualify, with 1.0× guards preserved.
- Cubic Hermite `3t² - 2t³` eases speed from 1× to the configured peak and down. Numerical integration and monotonic inverse lookup yield a fixed output-frame→source-ms mapping.
- Browser events, cursor tracking, animations, zoom/framing, semantic checks and evidence comparisons are referenced to the **source clock**; exported video remains constant 60fps.

## Visual behavior

- A real 3D homography transforms the window up to ±2.5°, including existing cursor hotspots; 3D-to-2D callout anchors use that exact transform each output frame.
- The floor is placed **below the projected window bottom**, reflecting real browser pixels with blur and geometric falloff. Reflection intensity is clamped to 0…0.5, with default 0.25.
- Contact and broad floor shadows shift with tilt. Floor rendering is optional and does not repaint the website.
- Callouts are **not** generated for arbitrary clicks. Only high-intent CTA, submit, or legitimate modal transitions with safe, short recorded text and real element bounds qualify.
- A minimum **2500ms cooldown in output time**, and **1800ms maximum display time**, are both enforced. Output-time cooldown remains strict even after the trace is sped up.
- Existing 0.56-scale rounded vector cursor remains on top and never vanishes when the callout is shown.

## Config

```bash
cd scripts/studio-motion
npm ci
npm test                       # TypeScript strict compile + Node tests
cd ../..

../.sauce-render-env/bin/python scripts/produce_cinematic_demo.py \
  --session studio/.tmp/brimble-reference-v16-ink \
  --workflow tests/fixtures/brimble-cinematic-workflow.json \
  --out studio/.tmp/sauce-studio-motion-v20-canonical-b \
  --seconds 4.2 \
  --enable-time-warp --max-warp-speed 4 \
  --enable-studio-floor --floor-reflection-intensity 0.25 \
  --enable-callouts --callout-cooldown-ms 2500 \
  --deterministic-frame-cache studio/.tmp/sauce-studio-motion-v20-source-cache \
  --no-webgl-optics \
  --presentation-hide-selector 'img[src*="bee-cutout"]'
```

Use `--deterministic-frame-cache` only when bitwise export reproduction
is required. It is a **private** PNG source-frame archive cryptographically
bound to the source trace, action history, source frame times and DPR.
The exporter checks the source hashes on every reused frame; mismatched
archives abort. It still replays the authorized browser actions and checks
semantic results. The cache and HAR must **never be web-published**.
Without a canonical cache, remote web content/Chromium rasterization may
differ slightly across otherwise identical executions.

To disable all three features, omit the flags above. No audio options are
required or used. An audio track is **rejected** while these new features
are enabled.

## Verified real-input acceptance

- Trace: six independently hashed states and 56 actual user events from a
  recorded Brimble session. Two high-intent clicks and a real dialog.
- Source: **4200ms**; mapped output: **3004.92326ms**;
  exported **181 frames**, 1920×1080 / 60fps.
- Peak accelerated speed: **4.0×**; protected action windows **2**;
  dead zones **1**.
- One safe callout: **Connect Agent** (recorded CTA text, not generated
  hallucination), no second pill within the cooldown.
- Floor reflection **0.25**, tilt maximum **1.0126°**.
- 3/3 semantic action checks and 3/3 pixel-region validations passed.
- Master and 720p30 Lanczos preview decode; **neither contains audio streams**.
- TypeScript strict compilation: zero errors; seven Node test cases pass.
- Python suite: 155 tests pass (10 skipped when optional native
  dependencies absent); runtime pixel/cursor/stage tests pass with native libs.
- Two complete exports with the same private canonical raster cache:
  **181/181 decoded frames byte-identical**, exactly zero pixel difference.
  Their SHA-256 digest over decoded-frame hashes matches.
- Without cached source frames, two otherwise equivalent live Chromium
  runs had an average **0.20/255** per-channel difference. Do not claim
  unrestricted bitwise reproducibility of arbitrary live webpages.

The real proof does **not** demonstrate 4× scroll motion on Brimble: its
trace contains an idle deadzone, not a long scroll run. Explicit loading
and continuous-scroll classification have independent TypeScript tests.

**Visual acceptance limitation:** This proves integration, timing, and
pixel determinism in a controlled sample, not automatic superiority over
custom studio/agency films. A blinded comparison of full product films
would be required for that claim.
