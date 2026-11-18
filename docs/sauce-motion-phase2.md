# Sauce Motion Engine — Phase 2 production integration

**Public Brimble render (3D Launch):** https://devmcp.davemafy.xyz/sauce-motion-phase2/
**Fresh independently regenerated proof:** https://devmcp.davemafy.xyz/sauce-motion-phase2-verified/

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

The independently regenerated proof was decoded end to end. A direct
48kHz waveform-to-AAC correlation measured **0 samples of alignment
offset**, compared with a permitted maximum of 800 samples (one 60fps
frame). The new pytest regression additionally muxes procedural Foley
into a synthetic 60fps H.264 film and verifies decoded AAC timing.

**Testing**: `SAUCE_BROWSER_TEST=1 ../.sauce-render-env/bin/python -m
pytest tests/phase2/test_sauce_motion_phase2.py -q` (10 passing on
worker). Python legacy suite: 156 tests passing, 11 skipped. TypeScript
planner: 18/18 passing.

The published film and release receipt contain **no raw HAR, screenshots
or event logs**. The present preview is a 3.3-second technical rendering
test, not a complete edited/narrated commercial.

## Phase 3 boundary

The Next.js preset picker, secure per-user render-job API, signed source
uploads, queued render jobs and long-form creative acceptance are Phase 3.
Do not imply those exist because the CLI supports presets.

## 2026-11-16 continuation: true depth and beat-locked 3D Launch

The original 197-frame Phase 2 proof remains an independent regression baseline. The new 3D Launch implementation introduces an independent H60 dialog plane (z=+60px) above the original H0 browser window (z=0), both projected with the original 1200px perspective and Y-then-X rotations. The background is a Chromium screenshot with a geometry-verified live dialog temporarily hidden; the renderer restores the original DOM style in a finally block. Without a verified modal-free plate, the original 6px-blur, 1px-rim single-plane spotlight is used instead. The active foreground owner survives nested child actions, with a shared nominal 2400ms lifetime or earlier recorded close.

The 3D Launch source-true beat scheduler generates actual hard cuts at observed hero actions, avoiding motion-blurring a cut frame. Camera transitions preserve the 180 / 24 / 1 physical spring constants between editorial cuts. Every Foley event maps to an integer output-video frame (800 audio samples per frame at 60fps and 48kHz), with sample alignment reverified against decoded AAC.

Verified real Brimble output: https://devmcp.davemafy.xyz/sauce-motion-phase2/z60-beats/ ; master SHA-256 35ef68e22c842eb28cb90ccda92a3961af770ed6352c716c609693648fa2a48c. 1920x1080 H.264/60fps, 197 frames, 3.283333s and AAC stereo 48kHz. The 125th output frame is an executed action-aligned cut, producing 125- and 72-frame shots. There were 120 elevated-modal frames, zero failed modal-free background attempts, 6 verified source hashes, 3 semantic checks and 3 pixel-region checks. Decoded AAC clicks had 0 sample offset before and after the cut. TypeScript 25/25; Python unittest 160/160; Phase 2 pytest with browser 17/17. Opened the new QA montage and full-res cut frame; validated public desktop and mobile playback. The limited 3.3s proof is technically passed, not a premium editorial film or arbitrary-source signoff. See docs/SAUCE_HANDOFF.md for retained gaps.

### Event-video glass loupe

\`scripts/render_event_video.py --glass-loupe --video CAPTURE --manifest MANIFEST --output OUTPUT\`
adds an event-driven loupe to the browser recording path. It is opt-in.
The sidecar must declare \`cursorless: true\` and contain one or more
\`slider_change\` events with press time \`start\`, verified result time \`t\`,
release time \`end\`, a nonempty \`evidence\` string, \`targetRect\` and
\`resultRect\`, and ordered \`pointer_samples\` with \`t\`, \`x\` and \`y\`.
All times use seconds on the capture clock. Rectangles and pointer positions
use decoded source-pixel coordinates. Capture adapters should record actual
before/after UI change and provide bounds of the changed visible result.

The rim bends and splits color near the edge of the lens. The center samples
the original frame directly. The lens starts at the recorded interaction, tracks
the pointer and widens its framing when a result is verified. The frame renderer
preserves the regular composition when evidence is absent or invalid.


## 2026-11-18 — opt-in quality hardening of the source-verified EDL renderer

This is **not** a restart of Phase 2 or a default Studio effect. Commit `465e1882f60dff9200e835637c4565a7d198924c` adds `scripts/editorial_quality_gate.py` and `scripts/camera_shutter.py`, with source-verified `overview:<state_index>` group framing. The existing `scripts/evidence_edl_renderer.py` accepts optional `--quality-gate`, `--bounded-repair`, and `--camera-shutter`. It rejects obviously misleading openings, camera anchors aimed at not-yet-observed results and clipped verified summary groups; source-true bounded repair can only remove an editorial teaser, not invent scenes or future events. Still requires an existing verified EDL and real X11/DOM source capture. No automatic arbitrary-URL scene direction is claimed.

[Verified 13.97s Linear output](https://devmcp.davemafy.xyz/sauce-motion-phase2/quality-action-first-20261118/) and [quality audit with comparison and remaining defects](SAUCE_QUALITY_AUDIT_20261118.md). Original Brimble Phase 2 proofs, water ripple, 3D H0/H60 compositor, TypeScript motion planner and Studio were left intact.
