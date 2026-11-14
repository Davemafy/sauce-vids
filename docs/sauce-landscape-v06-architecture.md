# Landscape v06 — source-fidelity architecture correction

**Primary 16:9 film:** https://devmcp.davemafy.xyz/sauce-film-05/

**1080p / 60fps direct MP4:** https://devmcp.davemafy.xyz/sauce-film-05/new-1080p60.mp4

**Reference comparison:** The same player lets the viewer choose the previous
landscape edit or original screen capture.

Date: 14 November 2026. This is an engineering improvement to the Brimble
film, *not* a claim of Screen Studio parity or a general-purpose DOM replay
engine. The real source is Brimble's public website. No sign-in, authorization
or deployment was performed.

## Diagnosis against the actual old source

The previous capture/render system used:

- Xvfb desktop + Playwright Chromium, with FFmpeg `x11grab` recording
  the 1600×900 screen in realtime at a declared 60fps.
- H.264 video encoded at CRF 15, `yuv420p`.
- A separate cursor event path recorded by Playwright mouse actions.
- OpenCV `warpAffine` on decoded *already-compressed* source pixels
  inside a larger browser canvas.
- A camera zoom peak of 2.63×.

The old camera's effective output magnification was approximately
`(1736 / 1600) × 2.63 = 2.85×`. It cannot invent the text-detail that
was lost in the earlier H.264 capture. A 60fps tag also cannot guarantee
individual frame freshness, correct click timing or smooth motion.

**Do not describe the old system as deterministic browser frame replay.**
It was a fixed-rate, offline postprocessor of a realtime screen recording.

## v06: Verified high-resolution state capture

`scripts/capture_brimble_hidpi.py` loads the actual public Brimble website
into Chromium at a 1600×900 CSS viewport with device-scale factor 2.

It saves three uncompressed 3200×1800 device-pixel PNG screenshots:

1. The actual scrolled agent section, with the Connect button visible.
2. The real `Connect your agent` dialog, verified to contain Codex.
3. The real Codex command copied state. The visible confirmation and
   clipboard text are both checked.

Each file's SHA256, dimensions, bounding rectangle and evidence are
recorded in an ignored local manifest. Neither the screenshot files nor
third-party app artwork are checked into GitHub.

This uses Playwright's `scale=device` high-DPI screenshot path. It does
*not* counterfeit website pixels or instruct an LLM to redraw the app.

## v06: Deterministic offline 16:9 frame compositor

`scripts/render_brimble_landscape_hidpi.py` runs a 60fps output clock
with `frame_index / 60` timestamps. It uses an event-bounded storyboard:

- 0–5.011s: actual scrolled agent section.
- 5.011–5.241s: transition into the verified agent picker.
- 5.241–7.723s: picker stays visible.
- 7.723–7.993s: transition into the actual copied command state.
- After 7.993s: copied command and sign-in guidance remain visible.

The cross-dissolves are **editorial transitions between genuine browser
states**. They are not presented as exact recordings of Brimble's internal
modal animation.

The recorded real mouse path remains a separate cursor layer. Camera
movement is independently time-stepped with quintic easing; the strongest
zoom was cut from 2.63× to **1.80×**, so the final output samples the
high-DPI source at no more than:

`1744 / 3200 × 1.80 = 0.981×`

In other words, even at maximum zoom the renderer is slightly
*downsampling* real UI pixels instead of amplifying compressed pixels.
The verified 400×476 CSS-pixel command modal remains entirely in frame.

The film keeps the previously generated, original 5-line narration and
low-level background bed, with captions outside the main product frame.
No decorative uppercase eyebrow, gradient, giant circular magnifier,
fake login or generated product UI is introduced.

## Acceptance checks

`scripts/verify_brimble_landscape_hidpi.py` checks:

- All three high-DPI source files are intact and SHA256-matched.
- Source screenshots are genuinely 3200×1800.
- A real copied-command confirmation and expected clipboard value exist.
- Final master is H.264, 1920×1080 and exactly 774 video frames at 60fps.
- The command dialog projected box remains on-screen; measured relative
  rectangle at maximum zoom is x=479.6–1264.4, y=23.5–957.5 inside
  the 1744×981 composited browser window.
- 57/57 checked consecutive frames in the camera push differ
  beyond the chosen threshold. This detects frozen camera frames in
  that section, **not** every possible kind of playback judder.
- The complete export fully decodes with FFmpeg's error checks.

The 12.9-second motion track is contained in a 13-second MP4 due to audio
container padding. Public master: ~4.1 MB. A smaller 720p/30fps preview is
also supplied for web/mobile playback.

Browser QA checks the deployed page at desktop 1280×720 and phone 390×844:
video loads, comparison selection works, no JavaScript errors or horizontal
overflow, and the flagship opens in landscape on both devices.

## Repeat on the configured Vultr worker

A working Python environment needs Playwright, OpenCV, NumPy, Pillow,
CairoSVG, and the installed Chromium. FFmpeg and ffprobe must be available.
The source site is external, so its current DOM, styles and pricing can
change independently of Sauce.

```bash
python3 scripts/capture_brimble_hidpi.py
python3 scripts/render_brimble_landscape_hidpi.py
python3 scripts/verify_brimble_landscape_hidpi.py
```

Only code, not user media, reference clips, site screenshots, models,
licensed third-party fonts or videos, is committed to main.

## What the architecture still needs

The new workflow is a **three-state hybrid**, not an autonomous film
editor and not a fully reproducible browser session. It cannot yet
reconstruct a moving/animated UI between arbitrary events, reproduce
network-dependent behavior or synthesize all screenshots of a user-owned
app without authorization.

For a general production engine, the next substantive work is an
instrumented session package with an exact action timeline, DOM/layout
snapshots, resource and font state, recorded relevant network responses,
consistent animation clock, deterministic screenshot/frame replay,
audio markers and semantic focus boundaries. Browser virtual time may
help only once all relevant state is controllable.

A stronger server is useful for capture concurrency and offline encoding,
but GPU flags alone do not guarantee accurate frames, and even perfect
rendering does not select the most compelling product story.

**Roadmap priority:** landscape only. No portrait/Shorts changes until
the flagship's visual and narrative acceptance criteria are met.
