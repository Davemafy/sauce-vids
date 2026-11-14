# Sauce camera proof — official Linear interactive preview

Date: 2026-11-14
Status: 14-second technical proof, NOT a production-ready generalized SaaS director.

## Public deliverable

- Viewer: https://devmcp.davemafy.xyz/sauce-autozoom/
- 1080p/60 master: https://devmcp.davemafy.xyz/sauce-autozoom/linear-auto-1080p60.mp4
- 720p/60 and 720p/30 versions and same-footage locked-camera comparison are available in the viewer.
- Source: https://linear.app/ — public interactive marketing preview; no account sign-in and no real Linear customer project. No fabricated UI.
- Browser frame: Shotcandy browser-dark.svg, MIT, https://github.com/btahir/shotcandy commit 15fa803. Source and license are vendored at studio/assets/vendor/shotcandy.

## Inputs / code paths

Recorder: scripts/record_linear_event_camera.py
Camera planner: scripts/autozoom_event_planner.py
Renderer: scripts/render_linear_autozoom.py
Regression tests: tests/test_autozoom_event_planner.py
Reference study: docs/saas-motion-reference-study.md

Raw source and sidecar live under studio/.tmp/sauce-autozoom-v1 on the Vultr VM, deliberately untracked (video exports may be several megabytes). The player HTML is also there as player.html.

The sidecar was recorded in the same X11 capture session as the video, with timestamped pointer coordinates, button-down, click, actual DOM target rectangle, observed state change and resulting content rectangle. A sidecar generated later from imagined clicks would NOT qualify.

## Truthful event evidence

- 14.0s original live browser recording, 840 frames at 60fps, 1320x720.
- Real Linux desktop cursor, 161 timestamped pointer samples.
- The 'Reviews' button was clicked at 3.6868s.
- DOM state-change at 4.0463s confirmed the review list and diff tab were visible.
- Semantic interaction completed at 10.6501s.

The planner produced one shot from the action event and resulting content region:
- Start focus push 3.3668s
- Fully settled 5.2463s
- Fixed camera while code is read
- Begin release 10.8301s
- Finish release 12.8801s
- Focus zoom 1.36x

These timestamps are OUTPUTS derived from recorded events and conservative durations. They are not hard-coded per-shot coordinates or per-scene timelines in the renderer.

## Implemented improvements

- No synthetic interface and no homemade browser toolbar; actual Shotcandy SVG controls, URL adapted truthfully to linear.app, MIT notice retained.
- 60fps real cursor and interaction capture; no 720p fake source upscale.
- Camera pans and scales within a stable frame. Its focus is the changed code panel, not every cursor location.
- C2 quintic easing with fractional-pixel OpenCV transform.
- Fails closed: absent verified state change means no zoom at all.
- Stable hold until interaction completion; raw vs locked vs auto accessible at identical timestamps.
- Quiet sound, no click noises; decoded audio peaks measured below -15 dBFS.

## Verification (2026-11-14)

- Full HD 1920x1080 60fps: 840/840 frames, complete FFmpeg decode pass.
- Phone 1280x720 60fps: 840/840 frames, Constrained Baseline Level 4.0, complete decode pass.
- Phone 1280x720 30fps: 420/420 frames, Constrained Baseline Level 3.1, complete decode pass.
- Seven event planner regression tests passed.
- Playback tested through a mobile-sized Chromium context; all player formats switched and advanced without decoder errors.
- Camera path measured max translation acceleration 0.3228 output pixels/frame squared.
- Public HTTPS outputs verified with HTTP 200 and range requests returning HTTP 206. DevMCP OAuth remained protected.

## Boundaries / what is NOT solved

- The pilot targets one accessible official marketing preview. It does NOT prove arbitrary SaaS recording or polished shot selection across different apps.
- This first planner only accepts click-to-observed-state-change with a visible resulting DOM rectangle. General scroll, drag, keyboard, form and modal event segmentation remain future work.
- The preview is not a working customer Linear workspace. No real issue was approved, committed or mutated.
- A reviewer must still judge emotional timing, editorial taste, typography readability and whether the move feels natural. Passing unit tests and 60fps playback is not creative acceptance.
- Actual third-party Screen Studio reference MP4s are retained only in ignored local research, never redistributed with Sauce.
