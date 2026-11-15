# Landscape Film 05 — cursor and caption composition (v09)

**Watch:** https://devmcp.davemafy.xyz/sauce-film-05/

**1080p/60fps master:** https://devmcp.davemafy.xyz/sauce-film-05/new-1080p60.mp4?c=9

**Previous action-led landscape edit:**
https://devmcp.davemafy.xyz/sauce-landscape-action/

## Source of this correction

The supplied 13-second 1280×720 video `1000417593.mp4` was the v08
landscape output. Reviewing frames at 0.5, 2.0, 3.6, 4.1, 4.5, 4.9,
5.15, 5.6, 7.25, 8.0, 9.0 and 11.5 seconds showed two clear presentation
failures:

- The arrow had a chunky 43×51-pixel handmade shape with a thick
  black border, visually oversized relative to the genuine website.
- Captions began at y=1009 while the product browser frame ended at
  y=1008 in the 1080-pixel master: essentially **one pixel apart**.
  They were squeezed against the bottom of the entire canvas.

The exact cause is visible in the old `render_brimble_landscape_hidpi.py`
compositor; it was not a failure of spring physics or frame rate.

## Applied corrections

- **Cursor:** replaces the oversized white polygon with a restrained
  27×37px, supersampled black-on-white OS-style arrow. Cursor hotspot
  remains the top-left tip. It remains at a fixed output-pixel size
  independent of camera zoom, and its *path* remains derived from the real
  recorded pointer telemetry and critically damped filter.
- **Product stage:** rebalances the browser from 1744×981 at (88,27)
  to 1600×900 at (160,25). It preserves a full 16:9 browser window
  and leaves space for typography without covering the product.
- **Caption layout:** 40px regular DM Sans centered by actual text
  bounds in a dedicated bottom text region y=991–1054. Browser ends at
  y=925, leaving **66px between the browser and caption region**.
  The glyphs are optically positioned inside the 63px region.
- No uppercase eyebrow, redundant explanatory tagline, circular
  magnifier or synthetic Brimble UI was added.
- Existing event-led camera trajectory, real click locations and
  verified three-state 3200×1800 Chromium capture were preserved.

These constants now live in `scripts/landscape_layout.py`, with four
composition tests in `tests/test_landscape_composition.py`.

## Verified on the actual export

The v09 master is 1920×1080, H.264 60fps, 774 video frames, and
approximately 13.0 seconds including audio padding.

`scripts/verify_brimble_landscape_spring.py` now checks:
- all three source-state SHA256 values;
- 774 video frames with complete FFmpeg decoding;
- camera only moving after the recorded pointer begins its approach;
- three real click coordinates within 0.1 CSS pixel at their deadlines;
- the full command dialog inside the view;
- caption gap >=55px, fixed cursor dimensions <=30×40;
- decoded v09 video frames at five timestamps have **zero dark
  typography pixels** in the quiet y=947–991 gutter at central x=400–1520,
  and a visible caption in its designated area.

The 720p30 low-data preview also fully decodes. Chrome playback checks
at 1280×720 desktop and 390×844 mobile passed, including selection
between v09, previous v08 and silent source capture, no page errors
and no horizontal overflow.

## Reproducibility

```bash
python3 scripts/render_brimble_landscape_hidpi.py \
  --output studio/.tmp/landscape-hidpi/sauce-landscape-presentation-v09-1080p60.mp4
python3 scripts/verify_brimble_landscape_spring.py \
  --video studio/.tmp/landscape-hidpi/sauce-landscape-presentation-v09-1080p60.mp4
python3 -m unittest discover -s tests -q
```

All third-party Brimble screenshots, captured source, typeface file,
audio and MP4 exports remain on the private Vultr worker; the GitHub
commit includes only source, tests and documentation.

## Remaining limitations

The new arrow is **OS-style**, not an extracted proprietary macOS or
Windows system pointer. This recording does not yet capture computed
CSS cursor state for each hovered element, so arrow-to-hand transitions
remain unimplemented. Do not claim native cursor-state fidelity yet.

Likewise, better caption spacing and cursor proportions do not solve
the separate creative questions: shot selection, narration, exact
modal motion, or market-level visual acceptance. This is a targeted,
verifiable landscape composition repair, not an assertion that Sauce
is ready to launch.
