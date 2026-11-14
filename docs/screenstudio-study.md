# Sauce film engineering study 01 — Screen Studio camera grammar

Date: 2026-11-14
Status: **real rendered reproduction and independently verified source, not a shipped autonomous video director**

## Reference inspected, not redistributed

Official Screen Studio product demo on [screen.studio/4](https://screen.studio/4).
The exact 10.3667-second H.264 file was inspected privately under
`studio/.tmp/sauce-reference-research/screenstudio-product-1.mp4`.
FFprobe: 1280×720, 60fps, 622 frames. It is **not** included in Sauce's repo
or publicly redistributed.

A SIFT/RANSAC camera-motion estimate from the actual reference frames
(`scripts/study_camera_motion.py`) found:

| Motion | Time in reference | Relative scale across reliable sample pairs |
| --- | --- | --- |
| First push | ~0.48–1.32s | 1.621× |
| First release | ~1.80–3.00s | 0.503× |
| Second push | ~5.88–6.84s | 1.625× |
| Second release | ~8.64–9.84s | 0.502× |

The reference shows two tight close-ups separated by stable readable holds.
Camera motion begins and ends decisively; it does not continuously chase the
pointer. The product being filmed is not replaced with fictional UI.

**Measurement caveat:** The scale estimates come from tracked visible feature
matches. A scene cut or application animation can affect them, and they are
not proprietary Screen Studio implementation parameters. The reported
durations are approximate, not instrumented internal camera-keyframe times.

## Our real-source recreation

[Watch the comparison](https://devmcp.davemafy.xyz/sauce-autozoom/study01/)

Source is **Linear's public interactive marketing preview**, not an
authenticated Linear customer workspace. The recording was produced on the
Vultr machine using a real Chromium window, real X11 pointer, one uninterrupted
`ffmpeg x11grab` capture, and Playwright DOM observations on the capture clock.
No regenerated UI or fake click sequence was inserted into the footage.

- One 12.0-second **1320×720 / 60fps** browser recording; 720 source frames.
- 13 timestamped events and **212 pointer samples**.
- Two genuine click → observed DOM-change pairs:
  - Reviews clicked at 2.2380s, code diff visible at 2.5871s;
    observed region x559.891,y97,w750.609,h616.
  - Faster app launch clicked at 6.3612s, task body visible at 6.6551s;
    observed region x296.391,y97,w661.766,h614.
- Profile `screenstudio` reconstructed from the reference timing, with
  bounded 1.62× zoom and quintic ease-in/ease-out. Camera targets are
  taken **only** from the verified result rectangles.
- First camera: 1.898–2.8271s push, holds until 4.8301s,
  releases by 5.8301s.
- Second camera: 6.0212–6.8951s push, holds until 9.5601s,
  releases by 10.5601s.
- Fullscreen presentation retains original application pixels without
  browser chrome or a fabricated desktop.
- Final: **1920×1080 H.264 / 60fps, 12.0 seconds, 720 frames**, AAC
  licensed background music; **full FFmpeg decode passed**.
- Identical 1080p/60fps locked-camera baseline uses the same real recording.
  Both have 720p/30fps mobile versions.

These motion timings are derived from captured interactions and actual DOM
changes; no hand-authored motion timestamps appear in the renderer. Manual
action scheduling in the controlled capture script is intentional for this
technique study, not a claim of fully automatic product discovery.

## Reproduce on a configured Linux capture machine

Use Python 3.11+ with playwright, python-xlib, numpy, Pillow,
opencv-python-headless and cairosvg, and a compatible browser binary.

```bash
# Run an isolated X11 server once, only if :91 is not already running.
Xvfb :91 -screen 0 1440x900x24 -nolisten tcp -ac &
export SAUCE_CHROME_BIN=/path/to/compatible/chrome
python3 scripts/record_linear_dual_focus.py

# In the installed video-renderer virtual environment:
python3 scripts/render_event_video.py \
  --video studio/.tmp/screenstudio-recreation/linear-dual-interaction-real-60.mp4 \
  --manifest studio/.tmp/screenstudio-recreation/linear-two-interactions.json \
  --camera-profile screenstudio --presentation fullscreen \
  --music /path/to/licensed-music.mp3 \
  --output studio/.tmp/screenstudio-recreation/auto-1080p60.mp4

python3 scripts/study_camera_motion.py \
  /path/to/reference.mp4 --out /path/to/analysis.json
```

`--static` renders the baseline. Leaving out `--music` produces silent film.
`--camera-profile standard --presentation window` preserves the previous
conservative renderer defaults.

## What this establishes—and what it doesn't

This is a working, repeatable technique recreation: real screenshot input,
real cursor, evidence-derived focus, and two independently directed camera
passes with identical-source A/B control. It does not yet prove general
unattended capture, appropriate shot selection across different SaaS products,
word-level narration synchronization, or premium 30-second launch-film
editing. Do not present this study as Screen Studio's output or an official
Linear integration.
