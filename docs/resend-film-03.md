# Sauce Film 03 — real pricing, magnified

Watch: https://devmcp.davemafy.xyz/sauce-film-03/

Full-resolution film: https://devmcp.davemafy.xyz/sauce-film-03/film-1080p60.mp4

Date: 2026-11-14. One independently produced **16-second** narrated
product film, recorded from the actual
[Resend pricing page](https://resend.com/pricing). Independent demonstration;
not affiliated with Resend.

## Source and factual checks

- Live Chromium session captured continuously with `ffmpeg x11grab` at
  **1440×900, 60fps** (960 frames).
- The actual X11 pointer is captured, including click timings.
- Native interactive pricing slider was clicked twice in the *same source
  recording*; the application confirmed **0.125** at 50,000 emails
  (**Pro $20/mo**) and **0.25** at 100,000 emails (**Pro $35/mo**) at the
  time of capture. These are observations, not a general guarantee of pricing.
- User-visible application controls, text, prices and pointer are real
  screen-recording pixels throughout the finished film. No recreated website.
- The full event receipt and raw source are on the Vultr worker in ignored
  `studio/.tmp/film-03/` and are not committed to GitHub.

## Direction and production

This was built after inspecting the user's two Screen Studio reference clips.
It adopts **desktop wallpaper + independent browser frame + circular
magnification lens**, with the real source frame sampled inside the lens,
followed by a clean wide return. It also includes actual spoken explanation
and a small amount of correctly sequenced phrase captions. It does *not*
claim to reproduce Screen Studio internals.

- Film content: "Three thousand emails start free. Fifty thousand emails?
  Twenty dollars a month. A hundred thousand? Thirty-five dollars.
  One slider. The price changes right where you need it."
- Voice: generated locally with Kokoro `af_heart` (offline).
- Audio bed: local licensed Mixkit track; voice normalized in final export.
- Desktop photographic backdrop: Victor G, Unsplash
  https://unsplash.com/photos/stone-formations-during-foggy-daytime-DHAluftDzos
  (Unsplash License).
- Browser artwork: `Shotcandy` MIT component included with the project and
  license, not a freehand imitation of native browser controls.
- Film renderer: `scripts/render_resend_film.py`; capture:
  `scripts/capture_resend_film.py`; audio:
  `scripts/film03_voice.py`.

The production deliberately uses a preauthored one-story timeline, not a
general autonomous software-demo director. There is no webcam presenter;
one would require genuine authorized footage. Neither the original user's
reference video nor its artwork were redistributed.

## Acceptance evidence

- Master: **1920×1080 H.264 60fps, 960 frames, AAC audio, 16.0 seconds**.
- Master audio: measured approximately **-17.2 integrated LUFS**
  and **-1.4 dBTP**.
- Lower-bandwidth version: **1280×720 30fps**, about **805KB**.
- FFmpeg full decode completed without error for the master and mobile copy.
- Independent local transcript of final mixed audio recovers all narrated
  pricing facts and the concluding sentence.
- Live HTTPS route supports both full file and range requests.
- Mobile browser: Chromium viewport 390×844 @ DPR2 played video, switched
  between edited/raw footage, had no horizontal overflow or JS errors.
- Film frames at the actual price changes were inspected visually.

## Reproduce

A working Ubuntu recording system needs a Chromium executable, Xvfb, python-xlib,
Playwright, FFmpeg, and the locally installed Kokoro model/voice files.
Set up Python environments with NumPy, OpenCV, Pillow and CairoSVG for the
renderer; voice generation needs kokoro-onnx. Paths to local model,
music and image assets are validated in scripts before rendering.

```bash
# On the configured Vultr machine:
python scripts/capture_resend_film.py
python scripts/film03_voice.py
python scripts/render_resend_film.py
```

The actual film is a useful, discrete end-to-end quality specimen. It is not
evidence that Sauce can yet reproduce human webcam recording, serve a
multi-scene 30-second launch campaign, or automate editorial judgement across
arbitrary applications.
