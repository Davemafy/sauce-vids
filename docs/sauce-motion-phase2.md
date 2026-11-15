# Sauce Motion Engine — Phase 2 production integration

**Public Brimble render (3D Launch):** https://devmcp.davemafy.xyz/sauce-motion-phase2/

**1080p/60fps master:** https://devmcp.davemafy.xyz/sauce-motion-phase2/master-1080p60.mp4

Phase 2 connects the versioned FramePlan + FoleyPlan produced by the
Phase 1 TypeScript director to the actual Python/Chromium/OpenCV/FFmpeg
film pipeline. The existing no-preset behavior is still supported.

## CLI

From the existing Vultr workspace:

```bash
cd sauce-v05-release
../.sauce-render-env/bin/python scripts/produce_cinematic_demo.py \
  --session studio/.tmp/brimble-reference-v16-ink \
  --workflow tests/fixtures/brimble-cinematic-workflow.json \
  --out studio/.tmp/sauce-motion-phase2-3d-launch \
  --seconds 4.2 --preset 3d-launch \
  --no-webgl-optics \
  --presentation-hide-selector 'img[src*="bee-cutout"]'
```

Optional flags: `--foley-assets /local/folder` (WAV or OGG files named
`click_crisp`, `whoosh_soft`, or `pop_glass`),
`--music-track /local/licensed-track.wav` (ducked during cues),
`--mute-audio`, `--foley-volume 0.0..1.0`.

## Capture privacy and schema

`session_capture.py` now emits redacted `copy`, `paste`, and `submit`
entries with actual browser `performance.now()` timestamps, CSS selector
where safe, and target `getBoundingClientRect()` bounds. Submit prefers the
real submitter button. **Clipboard contents, selected text, form values and
secret input lengths are never read or serialized**. Confidential inputs
have no identifying selector in the trace.

## Camera and active element

`studio_motion_bridge.py` validates `sauce-motion-plan-v1` plus the
FramePlan's exact per-frame source clock, camera values, and FoleyPlan timing.
`session_replay.py` consumes FramePlan scale, focus center, rotateX/Y and
1200px perspective. It no longer substitutes the older camera track for
explicit presets.

`spatial_parallax.py` exposes a strict projected target quadrilateral
using the **same 3×3 window homography** as the website, vector cursor and
kinetic callout. `cinematic_stage.py` uses the projected quad to preserve
the original active region pixels while applying up to 6px Gaussian blur
and dimming to inactive browser pixels. A 1px antialiased luminous rim
and 7px-elevated diffused shadow separate the element from its context.
All operations occur in the MP4 compositing pass, not page CSS.

## Audio contract

`scripts/foley_mixer.py` generates 48kHz stereo PCM as a temporary WAV
and uses the unchanged outputSample offsets from `foleyPlan`. It supports
local, licensed WAV/OGG cues and deterministic NumPy/SciPy synthesis
(including a NumPy-only contingency) with seeded noise, envelopes,
music duck intervals, gain control, mute and soft-knee peak limiting.

The final FFmpeg mux embeds **one 48kHz AAC stereo track**, preserving
the 60fps H.264 video stream. The temporary WAV is outside the public
release directory and automatically cleaned up.

## Actual Brimble verification

Source 4.2 seconds; 3D Launch output 197 frames at 60fps (3.2833 seconds).
- 1920×1080 H.264 master, AAC stereo at 48000 Hz.
- 1280×720 preview with Lanczos downscale and 48000 Hz AAC.
- 2× capture DPR, 6 hashed source states validated.
- 3 semantic checks and 3 pixel-region checks passed.
- 125 frames activate the new focused-region spotlight.
- 7 Foley cues: 2 click transients, 1 modal pop, 4 camera whooshes.
- All three Foley sound types use procedural fallback, no asset files.
- 48kHz PCM length 157,600 samples before AAC encoder padding;
  decoded AAC click peaks inspected near their planned output positions.
- Sound limiter output peak 0.2108, below 0dBFS.
- Browser capture privacy test, WAV/OGG fallback tests, mute, ducking,
  projection and encoded-stream tests pass via pytest.

**Testing**: `SAUCE_BROWSER_TEST=1 ../.sauce-render-env/bin/python -m
pytest tests/phase2/test_sauce_motion_phase2.py -q` (9 passing on
worker). Python legacy suite: 156 tests passing, 11 skipped. TypeScript
planner: 18/18 passing.

The published film and release receipt contain **no raw HAR, screenshots
or event logs**. The present preview is a 3.3-second technical rendering
test, not a complete edited/narrated commercial.

## Phase 3 boundary

The Next.js preset picker, secure per-user render-job API, signed source
uploads, queued render jobs and long-form creative acceptance are Phase 3.
Do not imply those exist because the CLI supports presets.
