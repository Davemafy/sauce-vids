# Film 05: correcting the mobile first impression

Reference: User-provided Android screenshot of a landscape demo appearing as a
small horizontal strip between large black areas on a portrait display.

## Actual failure

The 1920×1080 landscape MP4 was being viewed inside a tall Android browser.
The intrinsic video aspect ratio made it occupy a narrow horizontal band.
Although a previous comparison page selected a portrait preview on smaller
screens, direct playback of the landscape MP4 could not be rescued by CSS.
The original portrait film also wasted its first seconds on an establishing
shot, and the first full-bleed revision clipped titles at tall-phone ratios.

## Correction

- New share endpoint: https://devmcp.davemafy.xyz/sauce-film-05/short/
- Default mobile entry at /sauce-film-05/ now redirects there; use
  /sauce-film-05/?compare=1 to keep the comparison view on mobile.
- Immersive, no-scroll portrait viewer; warm neutral page background, no
  browser-generated black letterboxing inside the page.
- Real 1600×900 Brimble capture reused. New short starts at 5.60s of the
  continuous source, already displaying the actual agent picker.
- Scripted **8.4-second** portrait cut (MP4 container ~8.5 seconds).
- True 1080×1920/60fps master and a 540×960/30fps low-data preview.
- Safe-area text for 390×844 Android viewports: opening headings move inward,
  captions wrap to the central visible 80% instead of clipping.
- Play muted automatically when allowed; explicit tap unmutes and restarts
  narration at the beginning. When autoplay is blocked, tap to play.
- The video retains the genuine choice of Codex and copied command. It
  explicitly says the user must sign in before approving access. No account
  authorization or deployment was simulated.

## Verification

- Both exports pass a full FFmpeg decode.
- The source-verified live page, modal and copied state are real recording
  pixels; the title/caption/camera are editorial layers.
- 390×844 DPR2 Chromium: page redirected to /short/, video ready and playing,
  object-fit cover, no scroll, unmute/restart control worked, no JS errors.
- Screenshot inspection caught clipped headings from object-fit cover. A
  subsequent real-aspect crop comparison confirmed corrected first and final
  frames fit the safe region.

The change repairs a severe distribution and first-impression error. It is
**not** evidence of Screen Studio-level overall filmmaking quality, nor
a replacement for production-grade storytelling and authenticated workflow
captures.

## Reproduce

Use the stored real capture in `studio/.tmp/film-05/capture.mp4` and
recorded pointer positions in `capture-events.json`, with the already
configured local Kokoro and rendering dependencies:

```bash
python scripts/film05_short_voice.py
python scripts/render_brimble_short05.py
```

Do not share the landscape MP4 as the phone-first link. Share the
`/short/` webpage or the native portrait MP4.
