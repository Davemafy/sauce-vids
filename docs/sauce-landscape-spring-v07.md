# Spring camera and cursor — Sauce landscape v07

**Production:** https://devmcp.davemafy.xyz/sauce-film-05/

**Independent spring-master URL:**
https://devmcp.davemafy.xyz/sauce-landscape-spring/new-1080p60.mp4?s=7

**Comparison:** The player offers Spring camera, Previous camera (the
preserved v06), and silent, continuous source recording. This work affects
the **16:9 flagship only**. The portrait/Shorts pipeline was not edited.

## Problem and implementation

v06 used quintic interpolation between fixed keyframes for the camera, plus
linear interpolation between recorded cursor positions. The goal was not to
add gratuitous overshoot but to preserve velocity during camera retargets,
while remaining aligned with recorded actions.

`scripts/spring_motion.py` implements the mass-spring-damper equation:

`x'' + damping × x' + stiffness × (x − target) = 0`

It updates the exact ODE solution over each fixed timestep rather than
using explicit Euler. Critical, under- and over-damped cases are supported.
The renderer uses **critical damping** on all the actual camera/cursor axes
to avoid bouncing off the content or overshooting a real click.

### Camera

`scripts/render_brimble_landscape_hidpi.py` now precomputes the full
774-frame camera motion track at a fixed 1/60s timestep. This makes all
frames random-access reproducible and removes seek-time dependencies.

Camera target changes are event-led, not a running interpolation from
one keyframe to the next:

| Target starts | Zoom target | Center in source CSS pixels |
| --- | ---: | --- |
| 0.00s | 1.08× | (800, 450) |
| 1.25s | 1.34× | (670, 450) |
| 4.25s | 1.73× | (800, 450) |
| 7.38s | 1.80× | (800, 450) |

Scale stiffness=100, damping=20 (critical); pan stiffness=144,
damping=24 (critical). The physical target may change instantaneously,
but camera velocity and position are continuous.

The camera transform is built in OpenCV from the focus center, viewport
dimensions and zoom. This is **not** the naive CSS expression
`scale(...) translate(...)`, whose transform order and origin can cause
incorrect framing.

The high-DPI source remains 3200×1800. Maximum output/source sampling
scale is 0.981×, so the strongest zoom never magnifies already-compressed
pixels.

### Pointer

The separately captured **125 timestamped cursor samples** are still
the source of truth. Samples are interpolated only to form continuous
time-indexed *targets*; the output position is evolved by a spring:

- Cursor stiffness=784, damping=56 (critical).
- The spring state is computed sequentially once at 60fps and cached.
- The recorded click times and targets are not modified.
- Quality gating refuses output if the filtered cursor is more than 3
  CSS pixels away from a verified click.
- The cursor is rendered in its own layer over real website screenshots.

On the verified source sequence, cursor deviations at three click
deadlines are 0.085, 0.030 and 0.002 CSS pixels, respectively.
These measurements are for this specific captured sequence; they do
not guarantee correct clicks for every future application.

The cursor trajectory is **spring-filtered**, not randomly jittered,
manually bouncy or arbitrarily offset. Spring physics by itself does
not magically make a scripted gesture indistinguishable from a person.

## Automated checks

`tests/test_spring_motion.py` covers:
- Critical/under/over damping and exact timestep subdivision;
- camera monotonicity, no target overshoot and no frame-position jump;
- deterministic motion lookup;
- recorded cursor-path convergence;
- input validation.

Existing and new tests: **56 passing**.

`scripts/verify_brimble_landscape_spring.py` checks the *actual film*
and its original recordings:

- source SHA256 hashes and three real high-DPI UI states;
- 1920×1080 H.264, 60fps and 774 encoded video frames;
- full FFmpeg decode without errors;
- 38/38 adjacent frames in the active camera move contain image motion;
  settled holding frames are deliberately excluded;
- strict recorded-click location tolerance;
- the verified command dialog fits the visible browser viewport in
  sampled late frames;
- peak image zoom remains downsampled from source.

The source state dissolves remain editorial transitions between actual,
verified Chromium screenshots; they are *not* an exact recreation of the
original website animation. No authenticated login or deployment was
performed, and none is shown.

## Repeat

On the existing Vultr VM with the same recorded source assets:

```bash
python3 -m unittest tests.test_spring_motion
python3 scripts/render_brimble_landscape_hidpi.py \
  --output studio/.tmp/landscape-hidpi/sauce-landscape-spring-1080p60.mp4
python3 scripts/verify_brimble_landscape_spring.py
```

Only code, tests and this document belong in the public repository. Video
masters, source captures, third-party screenshots and fonts remain on the
private worker and are served from the existing video test endpoint.

## Still unsolved

Spring motion fixes velocity continuity, settling behavior and cursor
smoothness in the verified three-state sequence. It does not solve
general-purpose dynamic UI replay, automatic shot selection, voice-to-action
editing, presenter footage or proof of market-leading video quality.

Those are separate product-quality milestones. The priority remains
landscape, not Shorts.
