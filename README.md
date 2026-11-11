# Sauce Vids

**Turn real product interactions into product videos — with Hermes as the director.**

Sauce Vids gives [Hermes Agent](https://github.com/NousResearch/hermes-agent) the tools to capture actual software in a browser, turn the footage into a shareable MP4, and inspect the result. Designed for founders, developers, and product teams who need demos that show what their software really does.

Instead of generating replacement interfaces, Sauce Vids works with **the live product and licensed visual assets**.

## The workflow

1. **Direct:** Hermes uses the included `sauce-director` skill to plan a focused product walkthrough.
2. **Capture:** Playwright records continuous Chromium video and timestamps a structured action receipt.
3. **Render:** FFmpeg exports the recording as an MP4, optionally composed with an existing image asset.
4. **Inspect:** Hermes reads video properties and the captured interaction log to inform the next edit.

| Tool | Purpose |
| --- | --- |
| `sauce_capture` | Record approved HTTPS pages, hover states, scrolling, and real link navigation |
| `sauce_render` | Produce a video file; optionally use a pre-existing licensed background |
| `sauce_inspect` | Return recording provenance, event traces, and rendered-video metadata |

The package also includes the **`sauce-director` skill**, which describes the capture–render–inspect iteration for Hermes.

## Judge quickstart — no hosted account required

Sauce Vids runs on the same machine as Hermes. **No API key, paid cloud service, or login is required for the public-site test.** Linux with Python 3.11+, Chrome/Chromium via Playwright, and FFmpeg is recommended.

1. Clone and install using the commands below, then verify with `hermes plugins validate .`.
2. In the same shell where you launch Hermes, set `SAUCE_ALLOWED_HOSTS=www.brimble.io,brimble.io`. Install and enable the plugin.
3. Paste this into Hermes:

> Use Sauce Vids to record a short, real-browser walkthrough of https://www.brimble.io/agent. Use project `brimble` and start with a 2-second wait, then scroll down 500 pixels. Call `sauce_capture`, pass its returned run_id to `sauce_render`, then call `sauce_inspect`. Report the saved MP4 path and its actual metadata. Only describe interactions that were captured.

4. Open the MP4 path returned by `sauce_render` (normally `~/.sauce-vids/<run_id>/final.mp4`). The original WebM and action receipt are beside it.

**Troubleshooting:** If Playwright cannot launch Chromium, run `python3 -m playwright install chromium` (on Linux, additional OS browser dependencies may be needed). If rendering fails, confirm `ffmpeg -version` and `ffprobe -version`. If recording is refused, verify `SAUCE_ALLOWED_HOSTS` is set in Hermes's process environment.

## Install

Requires Python 3.11+, [Playwright](https://playwright.dev/python/), Chromium, and FFmpeg/ffprobe.

```bash
git clone https://github.com/Davemafy/sauce-vids.git
cd sauce-vids
python3 -m pip install "playwright>=1.55,<2"
python3 -m playwright install chromium
# Install ffmpeg and ffprobe with your system package manager
export SAUCE_ALLOWED_HOSTS="www.brimble.io,brimble.io"
hermes plugins validate .
hermes plugins install . --no-enable
hermes plugins enable sauce-vids
```

Set `SAUCE_ALLOWED_HOSTS` to the exact domains you are authorized to record. Recording outputs and receipts are kept in `~/.sauce-vids/` (configurable with `SAUCE_RUN_DIR`).

For brand imagery or a professionally designed visual background, supply a licensed PNG/JPG in a directory configured through `SAUCE_ASSET_DIR` and provide its filename to `sauce_render`. Sauce Vids does not bundle third-party stock assets.

## Example direction

> Record the public Brimble Agent page, capture one link navigation, render the genuine browser footage as an MP4, and inspect the video and interaction receipt.

A `sauce_capture` call returns a run ID. Pass that run ID to `sauce_render`, then `sauce_inspect` to retrieve the video metadata and evidence from the same recording.

## Verification

- **15/15 checks passed** using Hermes's official plugin admission validator, including capability registration and security scanning.
- **3/3 unit tests passed** for registration, input restrictions, and tool error responses.
- The plugin is listed for review in [the Hermes plugin catalog PR](https://github.com/NousResearch/hermes-agent/pull/154015).

```bash
python3 -m unittest discover -s tests -v
```

## Operating model

The plugin runs Chromium and FFmpeg locally, saves the footage on the host, and only records sites explicitly listed in `SAUCE_ALLOWED_HOSTS`. It is designed for authorized public websites and trusted operators. For hosted multi-tenant use, run capture workers inside a network-restricted sandbox.

**Open source:** MIT. Built for Hermes. Earlier visual research referenced the MIT-licensed [screen-demo](https://github.com/Third-Space-interactive/screen-demo) project; that code is not bundled here.
