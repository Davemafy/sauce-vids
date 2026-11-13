# Sauce Studio v0.4 — production module

**Hermes directs. Sauce Vids renders the production, with real captured footage.**

The versioned `StudioProject` JSON controls a floating-browser composition. Remotion creates a precisely framed browser, toolbar, shadow and art-directed background. FFmpeg composites an actual Sauce recording into a rounded video aperture and mixes an operator-approved licensed soundtrack.

## Verified output

The first Brimble floating-browser film was rendered successfully on the persistent isolated Vultr worker: 1920×1080 H.264/AAC, approximately 19.67 seconds. The original public marketing-page footage and Mixkit soundtrack remain separate source assets; the repository does **not** redistribute either.

The sample project is `examples/brimble-first-scene.json`. Populate:
- `public/footage/brimble-autonomous.mp4` — actual authorized browser recording
- `public/audio/digital-clouds-mixkit.mp3` — separately obtained licensed audio

The reference soundtrack was **Digital Clouds**, Alejandro Magaña (A. M.), catalog: https://mixkit.co/free-stock-music/electronic/ . Music license: https://mixkit.co/license/#musicFree . Review usage rights per file; do not redistribute stock audio independently.

### Installation

```bash
cd studio
npm ci
python3 -m pip install Pillow
# ffmpeg, ffprobe, and Chromium system dependencies must also be present
python3 render_project.py --project examples/brimble-first-scene.json \
  --out out/brimble-studio.mp4 \
  --browser-executable /path/to/chrome-headless-shell

python3 render_project.py --project examples/brimble-first-scene.json \
  --out out/preview.png --preview-at 6 \
  --browser-executable /path/to/chrome-headless-shell
```

For Hermes plugin operation, install `studio/node_modules` once and set `SAUCE_REMOTION_BROWSER` to an installed compatible Chromium binary. `SAUCE_ASSET_DIR` names a directory of **licensed, operator-provided** images and audio.

## Tools

- `sauce_compose({run_id,project,music_asset?,background_asset?})`: validates Hermes-authored v1 project, replaces untrusted footage paths with the actual verified Sauce recording and stores a reproducible `studio-project.json`.
- `sauce_preview({run_id,time_s?})`: renders a real frame, ready for Hermes image inspection and revisions.
- `sauce_render_project({run_id})`: renders 1080p MP4 from that exact project, returns final file and receipt.

No second creative agent, generated UI, fictional product interactions or hardcoded visual decisions. The existing `sauce_auto` tool is only a baseline for first-cut smoke tests.

## Explicit limitations

The 1 GiB Vultr worker could not sustain a full 360-frame Remotion browser render even with concurrency one. This supported v0.4 backend instead renders the Remotion **stage as a still** and overlays the real screen video efficiently with FFmpeg. Only one **static** floating-browser scene is accepted: moving-window camera keyframes, multi-window layers, transitions, reactive typography and timeline editing are not implemented yet. Unsupported creative instructions are rejected rather than silently ignored.

The Brimble public website recording demonstrates marketing-page content, **not** real authenticated agent activity.

Source reference: `Third-Space-interactive/screen-demo` (MIT), https://github.com/Third-Space-interactive/screen-demo . We inspected its components; this Studio implementation is authored separately. Remotion licenses apply independently: https://www.remotion.dev/license .


## v0.5 quality baseline (implementation in progress)

New Sauce capture runs produce a **native 1920×1080 / 30fps** original WebM from
a 1440×810 viewport at device scale 1.5. The renderer uses the original
source rather than a prior 720p-cropped re-encode and rejects footage smaller
than the output window aperture. The minimum single-browser width is 1400px.

The separate tab and navigation/address bars are a more faithful browser
composition, but the updated chrome has passed TypeScript checks **only**.
An end-to-end preview on the shared VM has not yet passed; the Remotion
renderer hit its process/concurrency limit. A timed-out process is cleaned
up with its Chromium children. A visually verified browser screenshot is a
release gate, not something to claim from compilation.

The old hand-drawn pointer injection is disabled. A genuine OS-style cursor
needs approved assets, correct hotspots and a separately recorded motion
track; that feature is not implemented yet. No cursor is preferable to a
misleading approximation.

Read [../docs/quality-floor-v05.md](../docs/quality-floor-v05.md).

## Sauce identity baseline (Vultr, November 13, 2026)

The sauce stage preset uses the same red/cream palette and Lobster and
Instrument Sans typography as the Sauce landing page. It is a simple
product-film frame, not a substitute for excellent footage or direction.

An example project lives at studio/examples/sauce-brimble-brand-pass.json.
Bring your own authorized browser recording named
studio/public/footage/brand-brimble-fixed.webm (1920x1080, native 30 fps).
Then run the Studio renderer with that project JSON.

This run corrected a real Playwright padding defect caused by recording a
1440x810 CSS viewport in a 1920x1080 video canvas. The fix records matching
1920x1080 browser and video frames at 30fps.

The public Brimble marketing page was captured, not an authenticated app.
This sample verifies recording, composite and visual identity consistency,
but is not approved as a final marketing film: cursor, timing, typography
at mobile viewing size, camera choreography and audio remain quality gates.
