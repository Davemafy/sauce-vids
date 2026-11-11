# Sauce Vids

**A product-video production toolkit for Hermes Agent.**

Hermes directs the story and selects interactions. Sauce Vids supplies real continuous Chromium recording, structured event receipts, and an FFmpeg renderer that can use operator-supplied licensed image assets. It does **not** fabricate product screens.

## What works

- `sauce_capture`: Launch a real browser and record a public HTTPS site with safe recorded interactions (scroll, hover, link navigation), preserving the actual URL and event trace.
- `sauce_render`: Encode the capture to MP4, optionally composing it with a background image from a configured licensed-asset directory.
- `sauce_inspect`: Return actual video metadata and the recorded event trace for Hermes to review.
- `sauce-director` skill: Guides Hermes through selecting, capturing, verifying and revising a product demo.

## Installation

Requires Python 3.11+, FFmpeg/ffprobe and Playwright Chromium. A running Hermes Agent is required to invoke the plugin through the agent.

```bash
git clone https://github.com/Davemafy/sauce-vids.git
cd sauce-vids
python3 -m pip install "playwright>=1.55,<2"
python3 -m playwright install chromium
# Install FFmpeg from your OS package manager
export SAUCE_ALLOWED_HOSTS="www.brimble.io,brimble.io"
hermes plugins validate . --install-deps
hermes plugins install . --no-enable
hermes plugins enable sauce-vids
```

Set `SAUCE_ALLOWED_HOSTS` to the specific domains whose content you're authorized to record. To enable a licensed background, set `SAUCE_ASSET_DIR` to a local directory containing an operator-supplied PNG/JPG. Captures and renders go into `~/.sauce-vids/` by default.

## Example

Ask Hermes to:

> Use Sauce Vids to record the public Brimble Agent page and an authorized link navigation. Inspect the event receipt and render a video. Do not present marketing illustrations as an authenticated agent execution.

## Provenance and limits

The Brimble sample film produced during development was **manually directed** using Playwright and Remotion; it is not proof that Hermes independently directed the film. The plugin itself is a separate, minimal recording-and-rendering API. This MVP was validated against Hermes's plugin validator but has **not** been proven in a live Hermes-directed run.

The plugin can make external HTTPS requests to explicitly allowed sites; launches headless Chromium; executes FFmpeg; writes recordings and JSON receipts to `~/.sauce-vids/` or `SAUCE_RUN_DIR`; and reads images from `SAUCE_ASSET_DIR` when supplied. It stores no credentials and sends no telemetry. Processing arbitrary customer sites requires stronger sandbox, DNS-rebinding and egress controls; this release is intended for trusted operators and authorized public sites.

Earlier visual experimentation used [Third Space Interactive's screen-demo](https://github.com/Third-Space-interactive/screen-demo) (MIT). This repository does not vendor that code or include third-party fonts, music, stock assets, or Brimble trademarks.
