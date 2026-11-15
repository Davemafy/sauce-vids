# Sauce v08: auto-zoom follows actual interaction

**Current landscape default:**
https://devmcp.davemafy.xyz/sauce-film-05/

**Standalone new 16:9 cut:**
https://devmcp.davemafy.xyz/sauce-landscape-action/

**1080p / 60fps master:**
https://devmcp.davemafy.xyz/sauce-landscape-action/new-1080p60.mp4?c=8

**Previous spring version:**
https://devmcp.davemafy.xyz/sauce-landscape-spring/

Date: 2026-11-15. This change is exclusively in the **16:9 landscape**
pipeline. There were no Shorts or portrait edits.

## Research: what "auto" must mean

Official product documentation:

- Screen Studio's auto-zoom targets recorded click positions. It does not
  acquire a zoom target in a segment with no click:
  https://screen.studio/guide/auto-zoom
- Tella's Auto mode follows recorded cursor positions; Manual mode remains
  on a fixed focus point. Adjacent clicks may be merged:
  https://www.tella.com/agent/auto-zoom-screen-recording
  https://www.tella.com/edit-with-ai/zoom-in-on-a-video
- Tella's Gentle style can begin a little *before the click*, but the
  cursor has already established the related action. Clips still need
  context, breathing room and time to read the result:
  https://www.tella.com/blog/how-to-add-auto-zoom-to-screen-recordings
- Cap generates editable automatic zooms from recorded click/cursor data:
  https://github.com/CapSoftware/Cap/blob/main/apps/web/content/docs/recording/studio-mode.mdx

Sauce v07 implemented a well-behaved physical *interpolator* attached to
an incorrect manual timeline. Its first camera keyframe began at **1.25s**.
The pointer did not intentionally start moving until **3.797s**; this
caused a meaningless two-and-a-half-second camera lead.

Spring physics cannot fix an editorially incorrect target timeline.

## New behavior

The action planner is `scripts/action_zoom_planner.py` and is integrated
into `scripts/render_brimble_landscape_hidpi.py`.

It accepts recorded pointer samples, actual click coordinates and DOM
bounds, plus the timestamps when each resulting UI state becomes real.
It derives and precomputes a deterministic 60fps critically damped camera
track.

The verified Brimble example proceeds as follows:

| Evidence time | Camera decision |
| --- | --- |
| 0–3.797s | Wide composition, exactly stationary |
| 3.797s | Intentional pointer motion detected toward the first click |
| ~3.9–4.90s | Move with pointer progress toward the real button |
| 4.90s | The original capture script triggers the Connect click |
| 5.011s | Real DOM dialog becomes visible; begin centering its region |
| 7.723s | Real copied-command state becomes visible; gently widen focus to its full height |
| 10.161s | Real Copy confirmation is recorded; hold the readable result |

The camera does **not** chase every small pointer fluctuation. It uses
the clicked element's box, an editorially biased contextual center,
a dead-zone while tracking inside the modal, and minimum padding to keep
the full product dialog readable.

Maximum zoom was reduced from **1.80× to 1.66×**, still sampling the
3200×1800 real Chromium screenshots at less than their source pixel
resolution (peak output/source sampling factor **0.9047×**).

The recorded cursor continues to be critically damped, drawn separately,
and verified against the real click locations. No screenshot interface
is recreated from an LLM.

### Legacy timestamp honesty

The legacy 2026-11-14 Brimble sidecar recorded state-visibility times
and mouse positions but not explicit mouse-down events. Its first click
time is therefore recovered from the original recording automation's
`until(4.9); pg.mouse.down()` schedule, not claimed to be an
independent mouse-down observation.

The current `scripts/capture_brimble_agent05.py` is updated so
**future captures explicitly log mouse-down timestamps, labels, source
coordinates and DOM bounding boxes**. The action planner will prefer
those records automatically; the 4.90s fallback only applies to this
archived recording.

## Objective acceptance

- Export: H.264 1920×1080 at 60fps, 774 video frames; 13s container.
- 3 original high-DPI state PNGs checked by SHA256.
- Full video decode verified, including the 720p preview.
- 29/29 checked adjacent frames in the active camera move contain
  visible image changes.
- First-frame auto zoom gate checked: no movement before recorded
  intentional pointer motion.
- The source dialog remains in frame in verified result holds, with
  actual final modal bounds inside the composed viewport.
- Filtered cursor deviation at the three interaction deadlines:
  0.085, 0.030, 0.002 CSS pixels.
- 65 local unit tests, including 9 focused action-zoom tests.
- Player QA on desktop and Android-size viewports: new 16:9 cut loads,
  previous spring cut and raw capture work, no horizontal overflow
  or browser JS errors.

## Reproduce on Vultr

```bash
python3 -m unittest tests.test_action_zoom_planner
python3 scripts/render_brimble_landscape_hidpi.py \
  --output studio/.tmp/landscape-hidpi/sauce-landscape-action-1080p60.mp4
python3 scripts/verify_brimble_landscape_spring.py
```

The renderer still uses three real high-resolution browser screenshots
for this one workflow. It cross-dissolves the verified app states; it
does not reproduce native browser transition animation frame by frame.
Avoid adding a synthetic spring animation to an app's own modal as if
it were original footage. Generalized session-state replay is separate
from this camera-policy fix.

Source videos, copyrighted site content, fonts and playback exports
remain off GitHub on the existing Vultr worker. Only code and
documentation are committed.
