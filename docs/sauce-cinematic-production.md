# Sauce cinematic production preset

**Live v17 verified output:** https://devmcp.davemafy.xyz/sauce-engine-v17/

**Previous v16:** https://devmcp.davemafy.xyz/sauce-engine-v16/

This release unifies Sauce's existing high-quality session renderer with
repeatable capture, export and player generation. It doesn't introduce a
new cursor silhouette or overwrite the longer landscape flagship.

## Command: one input, one publishable package

Reusing a verified, private session:

```bash
../.sauce-render-env/bin/python scripts/produce_cinematic_demo.py \
 --session studio/.tmp/brimble-reference-v16-ink \
 --workflow tests/fixtures/brimble-cinematic-workflow.json \
 --out studio/.tmp/sauce-premium-release-v17 \
 --seconds 4.2 --title "Connect your agent" \
 --cursor-style ink --cursor-scale .56 \
 --presentation-hide-selector 'img[src*="bee-cutout"]'
```

Or capture a new, authorized website:

```bash
../.sauce-render-env/bin/python scripts/produce_cinematic_demo.py \
 --url https://example.com/ \
 --workflow tests/fixtures/your-authorized-workflow.json \
 --out studio/.tmp/your-publishable-film \
 --dpr 2
```

A new capture is restricted to DPR 2 or 3. Raw HAR archives, screenshots,
event timelines and interaction workflows are stored in a **separate private
capture directory** and must not be exposed as web assets.

The publishable directory contains only:

- `master-1080p60.mp4`
- `preview.mp4`
- `poster.jpg`
- `index.html`
- `release.json`

## Film presentation contract

`scripts/cinematic_spec.py` centralizes:
- DPR 2 or 3, 1280×720 CSS source (2× capture = 2560×1440 pixels).
- 1920×1080 H.264 at 60fps for the master.
- 1280×720 at 30fps for the preview, encoded with FFmpeg's
  `fps=30,scale=1280:720:flags=lanczos`.
- Rounded black `#111113` cursor, 2.2 white outline,
  0,12,24,0.35 shadow and **0.56 film scale** (roughly 32×39px),
  preserving the user's v16 size correction.
- Browser/native cursor suppressed. One compositor SVG pointer follows
  the verified JSON trace through `Spring2D`; pointerdown causes 0.88×
  press contraction and fading SVG click ripple.
- Dark stage with 120px-blurred color fields; CSS-equivalent layered shadows
  and inner highlight. Source website pixels and its own modal remain real.
- `cinematic_presentation_v13.py` reads shadow and glow values from
  this shared contract.

`docs/sauce-premium-player-template.html` is a reusable, dark 16:9
video-player page. Its blurred ambient light and exact layered CSS
window shadow are present independently of the corresponding shadow and
glow baked into the MP4. The player fits the full video and export link
inside the standard **1280×720 desktop viewport** and works on a
**390×844 mobile viewport**, without horizontal overflow.

## Live acceptance (November 15, 2026)

One-command production on the Vultr worker generated and verified:

- 252 master frames, 1920×1080, 60fps.
- 1280×720/30fps Lanczos preview, both videos fully decoded.
- Six original source state hashes checked.
- Three semantic state checks and three pixel-region comparisons passed.
- Two recorded clicks retained, and the same cursor path and 0.56
  cursor scale as v16.
- Desktop and mobile video playback passed, with zero page errors.
- Download control is visible without scrolling at 1280×720.
- **128 local unit tests** pass, including eight original production
  contract checks and one output-directory isolation check.

Limitations: this currently works with the verified 1280×720 CSS capture
format, duration up to 10 seconds, and websites whose state can be restored
through the controlled Chromium replay and optional HAR. It is a short
silent engine proof, **not** a finished, narrated launch video. Raw captures
must always be reviewed for secrets before any separate publication.
