# Sauce Vids quality floor — v0.5

Sauce is the production medium, not the creative agent. An agent may ask
for a weak shot, but Sauce must either repair the rendering constraint or
**reject it with a useful reason**. Do not equate "an MP4 exists" with
premium quality.

## Diagnosed from the real v0.4 film (2026-11-12)

The uploaded film `1000415093.mp4` was 1920×1080/30fps,
19.667s, but had approximately 757 kbps of *video* data, with small UI.
The pipeline recorded at 1440×900/25fps, then rendered the source through
1280×720, cropped/zoomed, upscaled to 1920×1080, then downscaled into
the floating-browser aperture. Playwright's 25fps source was converted to
30fps. That can compound softness and judder; the source's own animations
may also contribute. The old page cursor was a handmade injected SVG, and
the fake browser toolbar was a single 54px band.

Low bitrate by itself does **not** prove a defect (simple screen content
compresses efficiently). Never use a bitrate threshold as the only
visual-quality classifier. Inspect real source and output frames.

## Mandatory defaults

1. **Capture:** Browser viewport 1440×810 CSS pixels, DPR 1.5,
   native recording 1920×1080, **30 real fps**, source VP9. Chromium
   must run with `--disable-dev-shm-usage` in the constrained worker.
   A live ffprobe check verifies the saved recording; an empty WebM is
   a hard failure. Reduced-motion preference is intentional for stable
   marketing demonstrations and must be recorded as a setting.
2. **No baked-in fake cursor:** The handmade SVG injection is disabled.
   OS-style pointer rendering must be a separate compositing track
   with a tested icon/asset, proper hotspot, smooth trajectory and
   idle-hide behavior. If no approved cursor asset is available, use
   no cursor rather than a bogus one.
3. **Native pixels:** Studio prefers the raw recorded WebM over the
   old FFmpeg-edited `final.mp4`, avoiding gratuitous re-encodes.
   A source must be at least as large as its actual display aperture;
   invalid sources are rejected.
4. **Window chrome:** A two-level tab+address bar treatment is provided.
   It must be visually compared to real browser chrome before public
   release. A browser is a frame for real content, never a fabricated
   representation of the product itself.
5. **Motion:** No forced zoom oscillations, no frame-rate conversions
   by accident. Full dynamic camera/keyframes remain a future engine
   capability with explicit easing and stable holds; current Studio
   may only render the supported static window.
6. **Readability:** A single-window presentation must remain large
   enough to show its real contents. If source UI is dense, Hermes can
   request a close-up using *real pixels*, or a full-screen shot.
   Current Studio doesn't yet implement zoomed close-up scenes; it
   must not pretend they work.

## Agent-independent production contract

Agent controls creative intent: product feature, shot order, content focus,
brand character, palette/music selection from licensed assets.

Sauce controls hard invariants: capture timing and frame rate, file
validation, color/fidelity, cursor correctness, window crop, canvas padding,
legal asset provenance, timing bounds, no text clipping, and deterministic
rendering. If the request violates the constraints, return a concrete
validation error and a safe alternative. Never silently downgrade.

## Acceptance suite for v0.5

- Capture produces a readable 1920×1080, 30fps video with nonzero duration,
  from real approved-origin browser interactions.
- An empty/corrupt file fails capture regardless of page action receipt.
- Studio sources the original WebM and refuses upscaling; do not reuse a
  pre-zoomed 720p export as input.
- Browser chrome survives visual inspection at full size and mobile
  downsample. This is **not yet verified** on the shared worker.
- OS-style cursor asset + hotspot + movement test **pending**.
- A 20-second multi-scene, fully choreographed example with source
  readability, frame-level temporal testing and Hermes-led revision
  **pending**.

## Runtime note

The current VM worker is shared with other development processes, has
a 1GiB cgroup and a 128-PID ceiling. A Remotion preview on this worker
stalled at process creation. Sauce kills its own renderer process group
on timeout, leaving unrelated projects untouched. Do not raise global
limits or terminate other projects without explicit approval.

## References

- Playwright browser recording options: https://playwright.dev/python/docs/api/class-browser
- Screen Studio separate cursor rendering: https://screen.studio/create/screen-recorder-with-audio
- Screen Studio animation and cursor controls: https://preview.screen.studio/guide/animations
