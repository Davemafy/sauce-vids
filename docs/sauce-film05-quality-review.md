# Sauce Film 05 — a real Brimble agent setup

Watch: https://devmcp.davemafy.xyz/sauce-film-05/

## Outcome

A complete **13-second** narrated software demonstration, edited in native
landscape and vertical formats. It was created from a real, uninterrupted
public browser capture at https://www.brimble.io/.

The entire demonstrated workflow is:

1. Open Brimble's **Connect your agent** dialogue.
2. Choose **Codex**.
3. Observe the site's real setup command and the **Copied** acknowledgement.
4. Explain that account sign-in is required to approve access.

**No actual Brimble account authorization, authenticated cloud operation,
or deployment was performed.** The film never claims those actions succeeded.

## Why this was selected

Film 04's oversized round magnifier, scenic desktop wallpaper and stretched
pricing slider demonstration obscured the product, ran longer than its
content warranted and fell short of the Screen Studio reference videos.

The user supplied two short Screen Studio references, including a 5.55-second
Google Sheets currency-formatting tutorial and a 4.65-second pricing-control
lens demonstration. Neither copyrighted reference was republished here.

Film 05 replaces those conventions with a more disciplined composition:
real product artwork at the opening, one genuine interaction sequence,
an anticipatory camera push, holds for reading, no simulated deployment
success, and a native aspect-ratio-specific vertical edit.

## Source and provenance

Capture script: `scripts/capture_brimble_agent05.py`

- Browser: graphical Chromium on a dedicated Xvfb desktop
- Raw continuous video: 1600×900, 60fps, 15.5 seconds
- FFmpeg x11grab: mouse cursor disabled in video; separate pointer telemetry
- Sidecar: 125 timestamped real pointer positions and three observed events
  (dialog appeared, setup command appeared, copy confirmed)
- Browser content, product UI and copy acknowledgement come from the
  actual live site; the camera and caption layers are post-production

The capture file and sidecar are retained on the Vultr worker under the
ignored `studio/.tmp/film-05/` directory. None are simulated.

## Art direction

The film uses a warm, nearly neutral canvas grounded in Brimble's actual
page, a lightly framed UI, and restrained 2D optical camera movement.

- The 16:9 edit opens on the site's bee artwork, expands it enough to show
  details and the site's real headline, then moves through the connector.
- The camera focuses on the actual modal instead of following the mouse
  continually.
- The vertical 9:16 version is separately composed. Its portrait window
  covers the actual central content and gives the options/command a larger
  mobile viewing area.
- Cursor movement is rendered as a separate layer based on the original
  source pointer track; it does not have an added 70px X11 title-bar offset.
- Original offline Kokoro narration: `scripts/film05_voice.py`
- Visual editing scripts:
  `scripts/render_brimble_film05_final.py` and
  `scripts/render_brimble_portrait05.py`
- Subtitle presentation: sentence/phrase captions, not falsely represented
  as precise word-level forced alignment.
- Typeface: DM Sans from Google Fonts (SIL Open Font License); used locally,
  not committed to the repository
- A low-volume licensed Mixkit background track is used, not a recreated
  copyrighted melody

## Delivery and verification

| Version | Master | Preview |
| --- | --- | --- |
| Widescreen | 1920×1080 H.264 60fps / 774 video frames | 1280×720 30fps |
| Vertical Short | 1080×1920 H.264 60fps / 774 video frames | 540×960 30fps |

Both masters have approximately 13-second containers (12.9 seconds of
video content, with AAC end padding).

- 16:9 master: ~2.83 MB
- 9:16 master: ~2.58 MB
- Landscape low-data preview: ~1.23 MB
- Portrait low-data preview: ~0.89 MB
- Integrated loudness approximately **-16.4 LUFS**, true peak approximately
  **-1.5 dBTP** for landscape master
- FFmpeg full decoding: passed for all four public video exports
- Public HTTP delivery and MP4 seeking: verified
- Browser tests: Android-sized 390×844 and desktop 1280×720
- Both formats play, toolbar switches versions, no horizontal overflow or
  page JavaScript errors
- Production source compiles; preexisting project unit suite passes 49 tests

## Reproducibility

On the configured Vultr worker, with graphical Chromium, Xvfb, FFmpeg,
Playwright, python-xlib, OpenCV, CairoSVG, Pillow, local Kokoro ONNX and
the model voices installed:

```bash
export SAUCE_CHROME_BIN=/path/to/chromium
export SAUCE_DISPLAY=:98
python3 scripts/capture_brimble_agent05.py
python3 scripts/film05_voice.py
python3 scripts/render_brimble_film05_final.py
python3 scripts/render_brimble_portrait05.py
```

An existing Xvfb on :98 will block a new session; choose a free display.
Download the OFL-licensed DM Sans variable font into the ignored
`studio/.tmp/film-05/fonts/DMSans.ttf` directory for rendering.
A licensed background audio file is needed for reproducible sound design.

## Quality assessment and next limit

This is a finished original example with improved composition and real source
integrity, **not evidence that the engine can autonomously deliver the same
quality for arbitrary websites or authenticated app journeys**. The next
critical evidence would be an authorized full product workflow that ends
in a real deployment or another complete high-value action, with reviewed
creative choices and narration-to-visual alignment.

A missing webcam-presenter track was not fabricated. No claims of being
made by Screen Studio or endorsed by Brimble are made.
