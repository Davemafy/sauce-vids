# Sauce JSON Film Plan v1 — source-true programmable cinema

**Status:** engine path tested on actual previously captured browser footage; **not** a premium-film creative approval, arbitrary-URL director, or production deployment.

## Architecture

`Verified browser media + event sidecar → director-authored JSON → existing OpenCV compositor → FFmpeg MP4`.

The director (person, deterministic policy, future model) selects **what to show**. The renderer supplies camera/cursor/audio choreography using genuine source pixels and existing event geometry. No Python selector, vendor hostname or visual effect is hardcoded to the example source.

The original `scripts/evidence_edl_renderer.py` remains the multi-event 60fps EDL engine. The new `--film-plan` option in `scripts/render_event_video.py` gives the normal URL-compositor path a **site-independent single-source camera and audio plan**, including one-event footage at other original capture rates. This is a first interoperable JSON surface, not a replacement for every EDL capability.

## Boundary with the existing JSON replay command

The previously integrated `sauce-live-edit-v1` (`scripts/live_edit_plan.py` and `backend/live_render.py --edit-plan`) controls replay trims, one verified slider's measured fit, cursor scale and the existing URL narrator. It is the **capture/replay editing stage** and is preserved without changing its grammar.

The new `sauce-film-plan-v1` is the **general compositor stage**: it pins the recorded media AND its event manifest and applies arbitrary approved keyframes targeting any measured event index that has target/result geometry, not only a single slider. It accepts a pre-generated local audio stem. The two versioned contracts are separate production stages, not interchangeable schema names. A future compiled orchestration should hand off from capture/replay to source-true shot planning; v1 is an opt-in CLI and has not been wired into the live URL queue.

## Declarative contract

Machine-readable schema: [`schemas/sauce-film-plan-v1.schema.json`](../schemas/sauce-film-plan-v1.schema.json).

Example (from a private, real browser source; no video or credentials are in Git):
[`examples/sauce-film-plan-slider.json`](../examples/sauce-film-plan-slider.json).

- `schema`: exactly `sauce-film-plan-v1`
- `sourceSha256`: exact hash of the media file passed to `--video`
- `manifestSha256`: exact hash of the source-timed sidecar passed to `--manifest`; pins recorded evidence to the plan
- `durationSeconds`: bounded by the actual source duration
- `presentation`: `fullscreen` or the existing browser `window` stage
- `cursor`: `recorded` (from real monotonic timestamped pointer samples) or `none`
- `camera`: 2–32 strictly ordered keyframes, `at` arrival time, optional `startAt` start of camera movement, `zoom` (1–2.5), `easing` (`quintic` or `linear`), `anchor`
- Anchors: `wide` or `event:N:target`, `event:N:result`, `event:N:group`. `group` frames the union of **verified** target and observed outcome regions. Anchors are document/source pixel coordinates, not prose, CSS selectors, or invented rectangles.
- `audio`: `{"mode":"clean"}` or `{"mode":"file","file":"narration.wav"}`. Audio is a **previously generated and authorized local file**, never text fabricated by the renderer. For current automated URL pricing narration, use the existing Kokoro producer upstream.

Key safety requirements are enforced in Python, beyond what static JSON Schema can express:

1. Reject a source-video or capture-manifest hash mismatch, unrecognized keys, nonfinite values, invalid geometry, absent event evidence, missing original cursor trace, or a path escaping the local audio workspace.
2. **Do not even begin panning toward a result before the event was observed.** For an `event:N:result` or `group` keyframe, its `startAt` must be at or after the verified event timestamp. Result keyframes hold the prior camera until that time.
3. Reject result/group keyframes that crop the verified actual region. No fake UI pixels are introduced.
4. Restrict camera velocity and zoom acceleration to bounded, 60fps-equivalent limits; the current initial geometry limit is a conservative engineering diagnostic, not an independent creative-quality guarantee.
5. Preserve the exact frame clock of the input video, and explicitly distinguish a 60fps presentation from a native 60fps source capture.

## Rendering a JSON plan

From an authorized Sauce workstation or existing isolated Vultr workspace:

```bash
python scripts/render_event_video.py \
  --video /private/verified-source.mp4 \
  --manifest /private/capture-events.json \
  --film-plan /private/sauce-film-plan.json \
  --validate-only

python scripts/render_event_video.py \
  --video /private/verified-source.mp4 \
  --manifest /private/capture-events.json \
  --film-plan /private/sauce-film-plan.json \
  --seconds 3 \
  --output /private/opening-study.mp4

python scripts/render_event_video.py \
  --video /private/verified-source.mp4 \
  --manifest /private/capture-events.json \
  --film-plan /private/sauce-film-plan.json \
  --output /private/review.mp4
```

The optional duration must be inside the authorized source and plan. The same genuine captured source can be rendered repeatedly with revised JSON, **without recapture or editing the renderer**. Output receipts include source hash, plan hash, frame count, actual FPS and explicit `creativeApproval:false`.

## What v1 does NOT claim

It does not generate polished creative decisions on its own, perform unsafe browser actions, synthesize motion between distinct real UI states, replace the existing advanced scene/3D renderer, produce arbitrary layered typography, provide an interactive animation editor or promise any given JSON is cinematic. Advanced compositing must be added as **versioned reusable engine primitives** (masks, depth planes, transforms, accessible title/caption layers, reversible time warps, audio tracks), with independent source-truth proofs and tests—not through per-website Python hacks.

## Honest evidence on original product sample

An original 25fps Chromium recording of the public Resend pricing calculator had already been transformed to a continuous 1920×1080/60fps **presentation-source** MP4 for the revised test. The JSON renderer reused that presentation media and its source-verified `slider_change` event, not a fresh capture or a native 60fps browser session. It produced a full **414-frame, 6.9s** 1080p/60 H.264 preview (initial variant 180 frames/3s), and a separate 6.9s 1080p/60 H.264+48kHz AAC render using audio extracted from the existing verified local Kokoro narration. FFmpeg full decode passed.

Actual frame review at 0.3/1.8/3.65/4.65/5.4/6.5s still exposes small pricing cards, dark UI and weak surrounding composition. The material remains **rejected for sale**. This test establishes **JSON→existing engine→real output**, not studio quality or a customer approval. Raw source, manifests and review videos stay private. No inference calls, new servers, production deploy or external publishing.
