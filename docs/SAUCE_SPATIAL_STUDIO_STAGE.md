# Source-true spatial studio stage for Sauce

**Status:** reusable opt-in Phase 2 engine capability (2026-11-20). Research-quality demonstrations; **NOT approved premium films**. The renderer retains the genuine Chromium source video, the verified capture manifest, the existing floating UI matte, original recorded pointer and 48kHz Foley mixer. The stage is 2.5D perspective compositing, not physically simulated global illumination.

## Model-driven workflow (no human per-site compositor)

For each real source movie and event trace, generate a hash-bound model contract:

    python3 scripts/film_director_capabilities.py \
      --source /private/source.mp4 \
      --manifest /private/capture.json \
      --brief "Cinematic film of this real interaction and its verified payoff" \
      --out /private/director-contract.json

The contract contains the exact current executable JSON Schema, genuine source and manifest hashes, native FPS, timestamps, safe verified event rectangles, and available visual primitives. It does not call an LLM, upload media, or include raw evidence text. Send it, the actual footage and separately rights-cleared references to the selected model. The model directs the film and outputs a Sauce film-plan-v1 JSON.

Validate the returned JSON against the **actual executable renderer** before rendering:

    python3 scripts/render_event_video.py \
      --video /private/source.mp4 \
      --manifest /private/capture.json \
      --film-plan /private/model-film.json \
      --validate-only

    python3 scripts/render_event_video.py \
      --video /private/source.mp4 \
      --manifest /private/capture.json \
      --film-plan /private/model-film.json \
      --output /private/film.mp4

When a model explicitly asks for the physical stage but accidentally selects the obsolete window presentation *without window configuration*, the only permitted deterministic compatibility correction is available through:

    python3 scripts/studio_plan_bounded_repair.py \
      --plan /private/original-model.json \
      --out /private/normalized-model.json \
      --receipt /private/normalization-receipt.json

This repair does **not** alter camera, sound, timing, colors, source hashes or verified product states. The corrected JSON must still pass the strict validator. Do not silently fix bad creative choices or suppress a rejection.

## Executable studioStage JSON controls

The new optional top-level field **studioStage** owns physical camera motion, material, light, reflection and the final payoff. Set presentation to fullscreen, and do not combine it with legacy window, glassLoupe or frozen isolation composition. The otherwise-required ordinary 2D camera can be omitted if studioStage owns the motion.

Supported nested fields:

- **camera:** 2–24 keys, each with at, scale (0.55–1.55), optional startAt, yaw (±16 degrees), pitch (±12), and either a normalized screen-space center [x,y] or a source-evidence focus of wide, event:N:target, event:N:result, event:N:component. Source-result focus cannot start before its verified pixel appearance or conservative event confirmation. A 60fps-equivalent perspective quad velocity limit rejects overly abrupt motion.
- **material:** optional RGB background color [0–255] and bounded grain. This colors the environment, never the UI texture.
- **depthPx:** 0–24, for the projected real-screen physical edge. **reflection:** 0–0.18, a subdued exterior reflection made only from the actual projected source pixels.
- **lighting:** real eventIndex, intensity, transitionSeconds, trigger of verified or appearance. The verified trigger begins at the actual DOM-confirmed result. Appearance analyzes sustained chroma changes in **the recorded result rectangle**, beginning no earlier than the real release, and falls back to the confirmation clock if the pixels don't prove early onset. The accent light is sampled from actual visible source pixels, not guessed from brand colors.
- **payoff:** an event:N:result or event:N:component anchor, minimum visible fraction, and mode overview or detail. Overview additionally requires a sufficient fraction of the entire product screen to remain visible at the last frame. Detail mode allows a deliberately cropped, still-verified source component, but not a missing payoff.
- **action visibility:** the real action target must stay visible when it happens. If a valid recorded pointer track exists and is requested, its actual tip is projected from source coordinates through the camera and must remain visible at the action. A model that zooms into the wrong UI region fails before rendering.
- **audio:** the new optional eventFoley mode uses the preexisting 48kHz sample-accurate Foley mixer. It reads real eventIndex and bounded clickGain, motionGain and masterGain, accents the genuine press and source-evidenced result, and never invents new user actions or unsolicited music. Existing clean/file modes retain their semantics.

A model can choose not to use studioStage; the no-stage renderer and previous motion paths retain the same executable behavior. All numeric bounds and allowed fields live in schemas/sauce-film-plan-v1.schema.json and are revalidated by scripts/film_plan.py plus scripts/spatial_studio_stage.py.

## Verified source cross-tests

- **tweakcn**, live Default to Neo Brutalism: 1920×1080, native 25fps and a verified theme-change click. Source saturation in the dashboard ROI starts at about 2.32 seconds and is clearly different by 2.40 seconds, while later DOM confirmation occurs at 3.0784 seconds. The new source appearance gate independently detected **2.40 seconds** from actual decoded frames. The click target and recorded pointer remain projected and visible. 164-frame 6.56-second H.264/AAC MP4 fully decoded.
- **Resend** authentic pricing slider: same reusable stage engine, native **60fps**, 1920×1080 output, 279 frames over 4.65 seconds. The source manifest has no general pointer samples; cursor is therefore none, never fabricated. Reactive lighting uses conservative verified result at 2.30 seconds. A too-tight final crop failed the new overview context gate. A revised wide final composition preserves the actual pricing page, and the H.264/AAC render fully decoded.

Both cases use the same code with different source evidence and declarative plan values, and both use **two real-event-aligned synthesized audio cues**, no licensed external samples. This establishes reuse on two different product sites, not good taste or autonomous premium creative direction.

**Old reference regression:** The preexisting liquid-glass technique replayed under the new code and produced the **identical** SHA-256 3df5b2391ef933a92b8198541ec9981649f115035d9e38dbd45991588653b10f. Its 1920×1080 60fps 279-frame 4.65-second source-true reference is not independently established as a $50K creative gold example.

**Actual Gemini trial:** The source-and-schema packet was sent once to Gemini 3 Flash with the real tweakcn MP4. The model selected studioStage and returned a JSON plan. First-pass mode mismatch (legacy window + stage) failed. One mechanical normalization restored schema compatibility and produced a real MP4. **Frame review revealed it focused the wrong dashboard region and hid the actual click.** The new source-target visibility validator therefore correctly **rejects** that plan with target visibility 0.000. One model feedback repair returned truncated JSON, was discarded and was NOT reported as a success. All original model plans and receipts are private research evidence.

## Honest capability boundaries

The stage is screen-space perspective and environmental lighting, not independent 3D UI layers or physically traced materials. Source capture frame cadence is preserved, so tweakcn is not falsely described as native 60fps. Long-page text can still be too small; neither tests nor an attractive backdrop establish premium visual quality. The generated source packet is a reusable *input* for a model-equipped director, not a guarantee that model inference has been wired into every deployed request path. The existing live production service was not edited or deployed during this research run. Film approval still requires actual MP4 frame review, desktop/mobile checks, a verified premium reference and explicit owner signoff.
