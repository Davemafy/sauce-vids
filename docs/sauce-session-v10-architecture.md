# Sauce session engine v10 — deterministic browser capture and replay

**Engineering proof player:** https://devmcp.davemafy.xyz/sauce-engine-v10/

**1080p / 60fps offscreen master:**
https://devmcp.davemafy.xyz/sauce-engine-v10/master-1080p60.mp4

**Existing flagship remains unchanged:**
https://devmcp.davemafy.xyz/sauce-film-05/

Date: 2026-11-15. Only the 16:9 pipeline was developed; no Shorts work.

## What the requested four-stage architecture actually became

### 1. Browser event capture with visual provenance

`scripts/session_capture.py` attaches a listener before document execution
and stores timestamped pointer moves, pointerdown/up, click, mouseover, focus,
input length, and scroll events. Each event includes the relevant DOM selector,
CSS bounding rectangle, computed cursor type and scroll offsets.

Actions are run against an authorized browser session; selectors and
verification expectations are passed in a separate operator workflow.

Alongside the structured events, capture saves lossless device-pixel Chromium
screenshots of **observed UI states** and SHA256 hashes. These are *not* H.264
screen recordings. The manifest schema `sauce.session.v1` is validated by
`scripts/session_contract.py`.

Sensitive field contents, URL query strings and passwords are not serialized
into the event trace. A separate workflow file may still contain real input
values and must be kept private. HAR archives can contain private network
data and must never be published or committed without review.

### 2. Offscreen, fixed-frame Chromium replay

`scripts/session_replay.py` launches a fresh Chromium session, optionally
serves the captured HAR with unknown requests blocked, and replays the
authorized actions on the real webpage.

A Playwright clock controls JavaScript timers; every frame is captured
at deviceScaleFactor=2 and assembled offline at frame-index / fps.
The full-resolution PNG frames are streamed through the compositor into
FFmpeg. They are not cut from a real-time screen video.

A critical incompatibility was found on Brimble: when virtual time was
moved forward, CSS animations could hold a **negative currentTime**, leaving
the real dialog in the DOM but visually transparent. v10 now controls
finite CSS/Web Animation instances using their **original keyframes**, seeking
their currentTime on Sauce's output clock. This is neither synthetic HTML nor
a fake modal animation. It may still fail on sites using custom compositor,
canvas/WebGL, live video, workers or uncontrolled network state.

Browser hydration is checked before pausing time. After each action, a
semantic visible-element or text check verifies the expected result.

**Pixel-region acceptance:** the renderer additionally compares
captured and replayed pixels for the recorded target region, rejecting
large deviations even if a hidden element exists in the DOM.

### 3. Spring camera / cursor

`scripts/spring_motion.py` remains the spring solver. The v10 proof
compositor uses critical damping to frame the actually clicked region. The
camera does not initiate a zoom without click telemetry. The style remains
restrained; no arbitrary bounce, shifting gradients or unrelated shots.

Recorded cursor movement is filtered independently of browser content.
Mouse-down timestamps are used to time a *subtle, optional* grayscale
click indicator (off by default).

### 4. Native cursor and truthful window composition

`scripts/system_cursors.py` retrieves real X11 cursor glyphs from the
installed system theme, including hotspot coordinates:

- default arrow
- pointer / hand
- text I-beam

The script switches the asset based on recorded CSS cursor state.
`cursor:none` hides the overlay rather than forcing an arrow.

The renderer uses a neutral canvas with a clipped, rounded browser frame
and restrained shadow. It does **not** add an invented macOS tab bar or
traffic-light buttons to a capture that never had them.

## Evidence

### Deterministic local fixture

An independently hosted local interactive UI
(`tests/fixtures/session-demo.html`) was captured once, with seven
verified states and twenty recorded browser events.

It was rendered twice from the same session at 1920×1080/60fps,
162 frames per render. Nine tested frame indices, including frame zero
and the last frame, were **pixel-identical across both renders**.

The fixture exercises hover states, pointer vs I-beam, a modal,
text input, and a verified created-item state.

### Real public Brimble flow

`tests/fixtures/brimble-public-workflow.json` replays:

1. Open the real visible Connect your agent button;
2. Hover Codex within the real modal;
3. Select Codex and observe the copied-command confirmation;
4. Hold the verified state.

The captured session included five source-state screenshots,
20 browser events and an approximately 6.2 MB local HAR.
The replay produced **180 frames at 1920×1080/60fps**, all verified
for decoding.

The four semantic checks passed. The four target screenshot-region
comparisons each measured an MAE of **0.0** in this particular
run with the same Chromium and archived resources. That is
strict evidence of pixel matching for those targeted regions,
**not** proof that the entire frame or all websites reproduce exactly.

The proof is silent, approximately 3 seconds, and intentionally
separate from the main 13-second Sauce film. No user logged in and
no deployment occurred.

## Reproduce on the configured Vultr machine

The local Python render environment requires Playwright, OpenCV, NumPy,
Pillow, FFmpeg, Xvfb, libX11 and libXfixes.

```bash
# Controlled local UI
python3 scripts/session_capture.py \
  --url file://$(pwd)/tests/fixtures/session-demo.html \
  --workflow tests/fixtures/session-workflow.json \
  --out studio/.tmp/session-demo-v1 --width 1280 --height 720 --dpr 2

../.sauce-render-env/bin/python scripts/session_replay.py \
  --session studio/.tmp/session-demo-v1 \
  --workflow tests/fixtures/session-workflow.json \
  --output studio/.tmp/session-demo-v1/offscreen.mp4 \
  --fps 60 --seconds 2.7 --expect-text Created

# Public Brimble, with HAR recorded locally
python3 scripts/session_capture.py --url https://www.brimble.io/ \
  --workflow tests/fixtures/brimble-public-workflow.json \
  --out studio/.tmp/brimble-session-v10 \
  --width 1280 --height 720 --dpr 2 --har

../.sauce-render-env/bin/python scripts/session_replay.py \
  --session studio/.tmp/brimble-session-v10 \
  --workflow tests/fixtures/brimble-public-workflow.json \
  --output studio/.tmp/brimble-session-v10/replay.mp4 \
  --fps 60 --seconds 3 --har
```

CI runs dependency-free session-contract tests and the existing project
unit suite. Machine/browser integration was run and inspected on Vultr.

## Limitations / release gate

- Not a generalized browser-state recorder yet. DOM events, screenshots,
  HAR and virtual time are useful ingredients, not an automatic guarantee
  of deterministic app behavior.
- A connection, database write or deployment must be independently
  verified against real state, not inferred from a button click.
- 16:9 web output is the product focus. The three-second proof is
  infrastructure evidence, not a finished launch film.
- Typed values are omitted from traces. Authorized replay must supply
  them separately; secret-bearing workflows must not be committed.
- HAR archives may contain cookies, tokens, payloads, and personally
  identifying information. Never publish raw session bundles without
  sanitizing and reviewing them.
- The offscreen compositor currently accepts 1280×720 CSS sources and
  produces 1920×1080 video. It needs general responsive layout support.
- The camera does not yet implement an artistic shot planner, audio-driven
  camera revision, captions or presenter choreography. The v09 film is
  still the better marketing-oriented visual.
- No promise of parity with Screen Studio or fully autonomous,
  market-grade filmmaking has been established.

Playwright official documentation consulted:

- https://playwright.dev/python/docs/clock
- https://playwright.dev/python/docs/api/class-page
- https://www.remotion.dev/docs/renderer/render-frames
