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

## JSON-driven source-true separated UI layers (experimental)

The optional `composition` object gives the existing renderer a **neutral stage containing independent real UI crop layers** after a verified browser result. A layer is sampled as a still from the original hash-pinned source video, using its separate manifest's `event:N:target` or `event:N:result` bounding box, with bounded surrounding source padding. No generative fill, fake DOM, retyped product text, or synthesized state. The original browser recording and one recorded cursor are retained before the isolated-stage cut; after the cut the cursor is intentionally suppressed because a frozen crop must not pretend to be live interactive footage.

Sample: [`examples/sauce-isolated-ui-price.json`](../examples/sauce-isolated-ui-price.json) (Resend, private authorized source not included in Git). The module is `scripts/ui_isolation_layers.py` and the existing `scripts/render_event_video.py` composes the output without a new web/video framework.

```json
"composition": {
  "mode": "isolated-ui",
  "startAt": 3.84,
  "background": [237, 236, 233],
  "layers": [
    {
      "id": "slider", "anchor": "event:0:target",
      "sourceAt": 3.60, "startAt": 3.84, "endAt": 6.90,
      "position": [0.50, 0.24], "widthFraction": 0.65,
      "paddingPx": 40, "enterSeconds": 0.52, "zIndex": 0
    },
    {
      "id": "price", "anchor": "event:0:result",
      "sourceAt": 3.60, "startAt": 4.12, "endAt": 6.90,
      "position": [0.50, 0.64], "widthFraction": 0.45,
      "paddingPx": 80, "enterSeconds": 0.62, "zIndex": 1
    }
  ]
}
```

This is an excerpt and needs the top-level source/media/manifest hashes, camera plan, pointer and audio settings shown in the example.

**Boundaries:** this first primitive handles source-true **frozen element cutouts**, not video-tracked moving elements. JSON controls placement, independent entry timing, layering, easing, width, matte shape and shadow. All visual product pixels are copied from the original recorded frame. The snapshot time cannot be later than the layer's entrance or earlier than the actual observed result. Only evidence-backed event rectangles can be cropped. `position` is normalized to the 16:9 stage, not a DOM locator or generated art. The engine refuses overflow and unsafe missing proofs.

**Critical visual defect found in actual decoded MP4:** the remembered Resend `resultRect` represents the changed price area, not the full Pro card. Enlarging that rectangle yields a **partial/cropped card**; slider cutout captures some adjacent lettering. It is NOT a visually accepted Arcade-style shot. The proper general solution is to store **complete source DOM element bounds, screenshot/matte and a same-state clean background plate** in the capture manifest; JSON then references those independently compositable, provenance-pinned assets. Cropping around arbitrary tiny text boxes is not an adequate long-term extraction method. Don't turn a clean technical effect into a low-quality default.

Private first proof `studio/.tmp/layer-proof/isolated-ui.mp4`: 6.9s 414 frames 1920×1080/60 H264, full FFmpeg decode passed, total 19.34s rendering, no audio. The input is the **60fps resampled presentation**, whose actual browser source was ~25fps; this does not establish native 60fps capture. Contact sheet reviewed at ~0.4/1.8/3.1/3.85/4.15/4.5/5.2/6.3 seconds; the cutout/clip defects remain and the film is rejected for sale.

## Verified full-component anchors for UI isolation (2026-11-19)

The editor now supports event:N:component as a camera or UI-isolation anchor, but only when the original captured event contains the complete, verified componentRect. event:N:result remains the changed-price/text rectangle and is never silently enlarged. The source and event manifest are SHA256-pinned. A missing, clipped or future component fails validation.

The public slider capture now scrolls slightly before interaction only when a compact bordered pricing component can fit entirely in the viewport without losing the real slider. After the genuine change, capture records the exact decorated DOM ancestor as componentRect. No website-specific selector or synthetic pixels are involved. The isolated UI crop remains a frozen browser frame rather than a re-created dynamic component.

In an isolated genuine Resend probe at 1920x1080 CSS/DPR2, one recorded slider drag changed $20/mo to $35/mo. Preframing moved scrollY to 97 and measured the complete Pro card at x=655,y=368.797,width=299,height=658.313. The recorded source was 1920x1080 VP9 at 25fps (not native 60fps). A 7.52s H264 study of the whole card plus duplicate price close-up and a second 6.24s H264 minimal study both decoded fully. Creative review rejected both: the first duplicates the price and opens too wide, while the second has a weak opening and abrupt empty stage. See living handoff for full hashes and proof paths. No commercial approval or production deployment.

## What v1 does NOT claim

It supports static UI isolation as a bounded experimental primitive, but still does not generate polished creative decisions on its own, perform unsafe browser actions, synthesize motion between distinct real UI states, replace the existing advanced scene/3D renderer, produce arbitrary layered typography, provide an interactive animation editor or promise any given JSON is cinematic. Advanced compositing must be added as **versioned reusable engine primitives** (masks, depth planes, transforms, accessible title/caption layers, reversible time warps, audio tracks), with independent source-truth proofs and tests—not through per-website Python hacks.

## Honest evidence on original product sample

An original 25fps Chromium recording of the public Resend pricing calculator had already been transformed to a continuous 1920×1080/60fps **presentation-source** MP4 for the revised test. The JSON renderer reused that presentation media and its source-verified `slider_change` event, not a fresh capture or a native 60fps browser session. It produced a full **414-frame, 6.9s** 1080p/60 H.264 preview (initial variant 180 frames/3s), and a separate 6.9s 1080p/60 H.264+48kHz AAC render using audio extracted from the existing verified local Kokoro narration. FFmpeg full decode passed.

Actual frame review at 0.3/1.8/3.65/4.65/5.4/6.5s still exposes small pricing cards, dark UI and weak surrounding composition. The material remains **rejected for sale**. This test establishes **JSON→existing engine→real output**, not studio quality or a customer approval. Raw source, manifests and review videos stay private. No inference calls, new servers, production deploy or external publishing.

## Floating browser and recorded glass loupe

For a window presentation, optional `window.scale` sets the size of the floating window. An optional local JPEG or PNG backdrop requires its SHA-256 in `window.backdropSha256`. Store the image next to the plan and use an asset you have permission to render.

The optional `glassLoupe` object enables the existing source-sampled loupe. It requires a verified slider result and its recorded pointer samples. The controls set entry, expansion and exit timing in seconds, lens radii relative to the stage height, and center and payoff placement as fractions of the stage. The lens still derives its interaction cues and sampled pixels from the capture. It draws one cursor projected through the same optical mapping. Omit these objects for the existing film-plan behavior.

`examples/sauce-film-plan-glass-loupe.json` uses the retained Resend capture and local backdrop. Put the JSON and the matching `backdrop.jpg` together, then pass that JSON to `--film-plan` with the verified source and manifest. The reference comparison video is a review input only. No reference pixels are needed for the export.

The optional `glassLoupe.cursor_style` selects `rounded` (the default) or
`outlined`. Both use the same recorded hotspot and lens projection. The
[liquid-glass example](../examples/sauce-film-plan-glass-loupe-liquid.json)
uses the outlined style and the timing of the standalone 4.65-second reference.

Use `glassLoupe.cursor_style: "clean"` for a straight-shaft arrow with a
thin white outline and fixed screen-space size. Its hotspot follows the
same recorded path through the lens. The [clean cursor example](../examples/sauce-film-plan-glass-loupe-clean-cursor.json)
uses the exact-reference plan as its starting point and changes only the
cursor style.
