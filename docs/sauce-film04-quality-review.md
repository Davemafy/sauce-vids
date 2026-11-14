# Sauce Film 04 — a quality-driven revision of the Resend recording

**Watch the new film alongside Film 03:** https://devmcp.davemafy.xyz/sauce-film-04/

**1080p/60fps direct MP4:** https://devmcp.davemafy.xyz/sauce-film-04/new-1080p60.mp4

Created: 2026-11-14. This is an independent editing exercise, not endorsed by
Resend or Screen Studio.

## Actual source and benchmark

Two short user-provided reference videos were studied frame by frame:

- `1000417059.mp4`, **5.55 seconds**: a complete spreadsheet currency-format
  interaction, with speaker video, captions, menu context, and a clean
  return to an overview.
- `1000417060.mp4`, **4.65 seconds**: Resend's actual pricing interface
  filmed in a floating browser over a scenic desktop. A circular magnifier
  quickly grows, follows the actual pricing interaction, holds both the
  selected volume and updated price in view, then releases.

Neither reference file is checked into Sauce or placed on public hosting.

Additional independently checked product information:

- [Screen Studio 4](https://screen.studio/4): visual camera benchmark.
- [Cap Studio](https://cap.so/docs/recording/studio-mode): separate cursor
  metadata, smoother motion and different layouts.
- [Tella](https://www.tella.com/): camera/layout switching, speech editing,
  auto zoom and sharing.

## Why Film 03 failed

1. The 16-second film overstayed its real pricing action.
2. Its circular magnifier had almost fixed size instead of an intentional
   grow/hold/release progression.
3. It buried the $20 and $35 values near the bottom of the output.
4. The source's X11-rendered mouse was approximately 70 screen pixels
   below the corresponding Playwright click position. That was **not**
   fixed by adding more zoom.
5. Narration could reach a changed price before that price visibly updated.
6. Dark, cramped scenery competed with a small product screen.

Film 04 solves these defects with a cleaner capture channel and a shorter,
retimed editorial cut. It does not claim parity with Screen Studio across
all its features.

## Truthful production input

- Actual live page: https://resend.com/pricing
- Actual 16-second X11/Chromium capture: **1440×900, 60fps**.
- Native pointer movement is recorded separately from the screen's pixels.
  No native pointer is burned into this new raw capture.
- **193 timestamped real pointer samples** in the capture sidecar.
- Two actual clicks/observed application states:
  - 50,000 transactional emails → Pro **$20/month**
  - 100,000 transactional emails → Pro **$35/month**
- The user interface pixels, slider, card contents and price changes
  remain original screen recordings; no synthetic HTML product UI.

Prices reflect the live page at the moment of recording, not a guarantee
of current pricing.

## Camera and editorial finish

- The raw 16-second screen action becomes a **10.4-second picture edit**.
- Monotone cubic source-time interpolation preserves the order of real
  interactions while smoothing speed changes at editorial boundaries.
- The magnifier grows from zero to roughly **632px radius** (1920×1080),
  holds while the values update, and withdraws to reveal the application.
- Real DOM position/action data guides the edit. Product pixels inside
  the loupe are sampled from the same source frame as the underlying UI.
- Cursor SVG and compositing are independent from the source pixels,
  at the recorded click coordinates; no opaque fake cursor baked
  into the screen and no 70px vertical displacement.
- A bright Unsplash scene is used as the desktop wallpaper, separately
  licensed from the software. Source image:
  https://unsplash.com/photos/lake-in-the-middle-of-mountains-during-daytime-jzNRMhs_Thg
  (Unsplash License; photo by its credited photographer).
- The desktop browser frame is based on an existing MIT Shotcandy SVG,
  with its license retained in the project.
- Local Kokoro narration, 8 timed caption segments and a low licensed
  soundtrack bed. **Phrase-aligned captions**, not an unverified claim
  of perfect word-level caption synthesis.

The revised script reads:

> Three thousand emails start free. Fifty thousand? Twenty dollars a
> month. A hundred thousand? Thirty-five dollars. One slider. Clear pricing.

In the final composition, $20 is visible before the spoken "twenty dollars"
and $35 is visible before "thirty-five dollars." These timing decisions
were specifically revised after inspecting initial full-render frame strips.

## Verification

| Output or check | Result |
| --- | --- |
| Master picture | 1920×1080, 60fps, **624 frames** |
| Container duration | 10.5s including final AAC padding |
| Mobile picture | 1280×720, 30fps, **312 frames** |
| Master file size | ~1.9 MB |
| Integrated audio loudness | ~**-16.7 LUFS** |
| True peak | ~**-1.5 dBTP** |
| Full FFmpeg decode | Passed |
| Mixed-audio transcription | Recovered all scripted pricing facts and conclusion |
| Mobile playback | Chromium 390×844 (DPR 2); video plays, switches new/old/raw, no JS errors or horizontal overflow |
| Public HTTPS | HTML and MP4 delivered with successful HTTP responses |

The raw footage, third-party image, voice model, music and exported
MP4 files remain local ignored artifacts on the Vultr machine. The code
and original written production notes are checked in to the main branch.

## Reproduction on the configured Vultr machine

Requires Linux, Xvfb, FFmpeg, a Chromium binary, Playwright, python-xlib,
NumPy/OpenCV, CairoSVG, Pillow, a locally installed Kokoro ONNX model, its
voices file, and a properly licensed soundtrack.

```bash
export SAUCE_CHROME_BIN=/path/to/installed/chrome
# Browser capture records the real slider and native pointer telemetry:
python scripts/capture_resend_film04.py
# Original offline voiceover:
python scripts/film04_voice.py
# Reformat, composite, verify and export:
python scripts/render_sauce_film04.py
```

Source-specific capture uses a real public app; it is not a reusable
authenticated-site autonomous agent. No camera-presenter footage was
invented because no authorized presenter track was supplied.

## Remaining product work

The output is a much better single film, **not yet an arbitrary-site
video generation product**. The next generalization problem is a reusable
semantic camera director that groups real interactions and composes
speakable shots without human-authored scene timings. Human-level
creative judgement, branding, and multiple layout variants still need
explicit acceptance tests against market-grade references.
