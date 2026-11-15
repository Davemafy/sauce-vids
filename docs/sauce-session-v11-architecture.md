# Sauce v11 — action-led cinematic replay

**Current proof:** https://devmcp.davemafy.xyz/sauce-engine-v11/

**1080p/60fps master:**
https://devmcp.davemafy.xyz/sauce-engine-v11/master-1080p60.mp4?v=11

**Previous 3-second v10 comparison:**
https://devmcp.davemafy.xyz/sauce-engine-v10/

**Film 05 (landscape flagship) remains unchanged:**
https://devmcp.davemafy.xyz/sauce-film-05/

Date: November 15, 2026. This is a **16:9 landscape engineering proof**, not a final launch advertisement. No Shorts pipeline changes.

## Why v10 still looked mechanical

The v10 renderer had a fixed-frame clock and a spring interpolator, but its
Playwright `click()` steps teleported the pointer to a button. The captured
cursor trace contained too few intermediate coordinates for believable
acceleration and deceleration.

Similarly, v10's camera targeted click rectangles without distinguishing the
click from the actual dialog appearance. Although Brimble has a real native
CSS modal animation, an incorrect camera timeline could hide its visual impact.

The fix was **not** to insert a generic Framer Motion modal into someone else's
site or draw a fake cursor. The correct pipeline is capture a real approach,
follow genuine interaction events, and preserve the app's own animation.

## 1. Human-paced cursor capture

`scripts/session_capture.py` supports the new `approach` workflow action.

- Stage the relevant screen section before frame zero.
- Move a real Playwright pointer through a curved Bezier path.
- Use quintic timing, which accelerates then decelerates rather than
  traveling linearly at constant speed.
- Send intermediate pointer events while the actual browser is running.
- Record the resulting event timestamps and computed CSS cursor states.
- Keep clicks at real target positions, instead of inventing displaced clicks.

The released Brimble session contained **56 browser events**, including two
physical pointer approaches lasting approximately **0.73s** and **0.69s**.
There were six verified 2× screenshot states.

The renderer independently smooths the recorded path with the critically
damped mass-spring solver in `scripts/spring_motion.py` and replays pointer
positions one output frame at a time. Recorded mouse-down coordinates remain
authoritative. Resulting click-position deviations in the verified v11 session
were **0.014px** and **0.0095px** at the two click deadlines.

The Linux OS cursor glyph and its hotspot remain the basis of the composited
pointer. When Brimble reports `cursor:none` inside its dialog, Sauce respects
that state; the site's own interactive cursor/animation may therefore remain
visible. This is deliberately not misrepresented as a macOS cursor.

## 2. Event-driven, deterministic camera

`scripts/cinematic_tracks.py` converts the true cursor path and UI events
into a complete 60fps spring camera track.

For the release session:

- Recorded first visible pointer movement: 1576.0ms capture clock.
- The first camera zoom begins at output frame **8**, after pointer movement
  becomes meaningful.
- First actual pointer-down click: 2232.9ms.
- Actual `dialog-visible` browser event: 2362.7ms.
- First camera focus follows the Connect button; once the modal exists and
  is visible, the focus transfers toward its real bounding box.
- The Codex approach tightens attention within the dialog; after the second
  click, the camera leaves the resulting command readable.
- Maximum zoom is **1.398×**. Critically damped movement keeps the camera
  position and velocity continuous while protecting dialog framing.

There is no random panning, no unexplained zoom before the cursor moves, and
no frame-based camera reset when the modal opens.

## 3. Native modal animation and restrained depth

The rendering system uses Chromium's real DOM, loaded assets and original
CSS/Web Animations, controlled by a fixed output clock. It does not
reconstruct Brimble's modal or insert artificial scale/opacity keyframes.

An earlier virtual-clock issue kept CSS animations at a negative current
time. The v10 animation driver fixes that by seeking the real site's
finite animations each frame. In the v11 output, the modal is visibly
translucent during its first entrance frames before settling.

`scripts/cinematic_composite.py` optionally applies a subtle
**editorial background-focus blur** outside the verified dialog bounds. The
dialog itself is protected at pixel resolution and is never redrawn.
This pass runs after the source is projected to the 1600×900 video window,
which avoids unnecessarily blurring full-resolution 2560×1440 input.

There is no default gradient, glass UI, new title bar, invented browser
interface or synthetic modal overlay.

## 4. Verification on the actual encoded export

Release input: `studio/.tmp/brimble-cinematic-v11-release` (private on the
Vultr worker; HAR and screenshots are **not** in the public repository).

Acceptance script: `scripts/verify_cinematic_session.py`.

- Final video: **1920×1080 H.264**, **60fps**, exactly **252 frames**, 4.2s.
- 720p/30fps lower-data playback copy also fully decodes.
- 6 original screenshot hashes verified.
- 3 semantic assertions succeeded (dialog visible, copied-command visible,
  result still present).
- 3 cropped UI pixel-region checks measured MAE **0.0** against the
  captured session using the same Chromium/resources.
- 26/26 adjacent sampled frames in the active camera movement changed.
- Full video decode passed FFmpeg's error checks.
- The final player passed desktop 1280×720 and phone 390×844 testing:
  16:9 presentation, playback, previous-version switching, no JavaScript
  errors, no horizontal overflow.
- **92 local unit tests** passed.

Pixel-region matching is limited to the verified regions. It is **not** a
claim of pixel-for-pixel identical full-browser replay under all conditions.

## Reproduce on the existing Vultr worker

```bash
python3 scripts/session_capture.py \
  --url https://www.brimble.io/ \
  --workflow tests/fixtures/brimble-cinematic-workflow.json \
  --out studio/.tmp/brimble-cinematic-v11-release \
  --width 1280 --height 720 --dpr 2 --har

../.sauce-render-env/bin/python scripts/session_replay.py \
  --session studio/.tmp/brimble-cinematic-v11-release \
  --workflow tests/fixtures/brimble-cinematic-workflow.json \
  --output studio/.tmp/brimble-cinematic-v11-release/sauce-v11-1080p60.mp4 \
  --fps 60 --seconds 4.2 --har --backdrop-focus

../.sauce-render-env/bin/python scripts/verify_cinematic_session.py
python3 -m unittest discover -s tests -q
```

The renderer currently supports the verified 1280×720 CSS source in this
proof path. Full arbitrary-website state recovery, complex authenticated
sessions, accurate synchronization across independent network fetches,
voice-driven shot selection, and market-leading cinematic quality on
multiple products are still separate milestones.

**Security:** HAR files may contain credentials, request payloads or other
private data. Keep raw captures on the worker; do not publish unreviewed HAR,
input values, videos, fonts or third-party website snapshots to GitHub.
