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

## v0.5 — source-quality baseline

Sauce now records approved public websites as **1920×1080 / 30 fps VP9**
from a matching 1920×1080 browser viewport at 1× device scale, with the browser's
reduced-motion preference enabled to prioritize stable demonstrations. A real
`ffprobe` check confirms that footage contains the required video stream,
dimensions, frame rate and duration before Sauce reports capture success.
A zero-byte or corrupted recording is a failure, not a successful demo.

The former hand-drawn pointer injection is disabled: it was neither an
authentic macOS nor Windows cursor. The compositor now prioritizes the native
source WebM, avoiding the old 720p intermediate zoom/render pipeline.
The Studio renderer rejects sources smaller than their intended display
aperture rather than stretching low-resolution UI.

The browser header has been rebuilt with separate tab and navigation/address
rows. A faithful OS-style cursor **rendered from tracked pointer events** is
still a pending quality gate; an absent cursor is preferable to a fake one.
Capture of CSS animations is intentionally reduced for stability, but real
dynamic product interactions must eventually have an explicit opt-in
motion-preservation mode. The new header still needs visual verification
on an unconstrained renderer and is not considered launch-ready.

## v0.4 — production studio (Hermes directs)

Sauce now includes a real Remotion-based **floating-browser stage** and a memory-bounded FFmpeg compositor. Hermes supplies a versioned scene project, including browser framing, backdrop and licensed audio. Sauce validates actual footage/provenance and renders precisely what was requested without another creative-planning model.

The production loop is `sauce_compose` → `sauce_preview` → Hermes visually critiques the actual frame → `sauce_render_project`. These tools are separate from the old `sauce_auto` first-cut smoke-test heuristic.

A 19.67-second Brimble public-site film, 1920×1080 H.264/AAC, was rendered on the isolated Vultr worker. The browser mockup/window is a composition layer; the content inside is the real captured marketing site, **not** an authenticated Brimble deployment. Only one static floating-window scene is supported in this slice. Dynamic camera paths, independent multi-window layers and full Hermes conversational orchestration have **not** been proven.

The design-system and execution reference is documented in [studio/README.md](studio/README.md). Install Node.js dependencies with `cd studio && npm ci`, ensure FFmpeg and Chromium are available, and set `SAUCE_REMOTION_BROWSER` to the browser binary. Approved licensed assets still come only from `SAUCE_ASSET_DIR`; no third-party audio is bundled.

## v0.3 — one URL, first-cut MP4

sauce_auto is the one-call entry point. Input: an approved public HTTPS URL,
optional project slug and 8–30 second target. It scouts actual page headings,
chooses safe on-page interactions, records them, builds an editable cut list
from genuine event timestamps, renders a 1080p MP4 with subtle camera pushes
and extracts review frames.

To smoke-test the pipeline without Hermes:

    export SAUCE_ALLOWED_HOSTS=www.brimble.io,brimble.io
    python3 scripts/auto_demo.py --url https://www.brimble.io/agent --project brimble --duration 20

Outputs include the real MP4, capture receipt, edit-plan.json, review.json and
objective quality indicators. Artistic approval still requires inspecting real
frames. Licensed soundtrack/background files are optional operator-provided
assets in SAUCE_ASSET_DIR; no third-party assets are redistributed.

## v0.2 — real discovery, editing and review

Hermes has six tools: sauce_scout, sauce_capture, sauce_plan, sauce_render, sauce_review and sauce_inspect.

1. Scout a public approved HTTPS product site. Hermes receives actual headings, verified link and tab selectors, and screenshot files.
2. Capture the selected interactions. The click_tab action is restricted to role=tab controls; expected_visible_heading waits for real rendered content.
3. Ask Hermes to write a scene-by-scene edit plan with sauce_plan, using timestamps from the actual recording. Save cuts, 1.0–1.45x zoom and focal position to edit-plan.json.
4. Call sauce_render with use_edit_plan=true. The final film is produced with H.264/FFmpeg. Optional music_asset and background_asset are existing licensed files supplied in SAUCE_ASSET_DIR, not automatically sourced or bundled.
5. Call sauce_review to extract film frames and detect sustained black sections. Hermes should inspect the actual frames and revise the plan if needed.

Example editing calls:

    sauce_plan({"run_id":"brimble-example123","shots":[
      {"start_s":0,"end_s":3,"zoom":1.0,"label":"Hero"},
      {"start_s":4,"end_s":8,"zoom":1.2,"focus_x":0.6,"focus_y":0.5,"label":"Feature"}
    ]})
    sauce_render({"run_id":"brimble-example123","use_edit_plan":true})
    sauce_review({"run_id":"brimble-example123"})

The tool suite records and edits genuine browser footage; it does not autonomously guarantee professional cinematography without Hermes choosing and reviewing the shots.

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

## Waiting for SPA content after a link click

For React and other client-rendered websites, navigating to the correct URL does not always mean the screen has finished rendering. Supply `expected_visible_heading` on a `click_link` action to wait for the exact, visible heading before advancing to the next shot:

```json
{
  "url": "https://example.com",
  "project": "example",
  "actions": [
    {
      "type": "click_link",
      "selector": "a[href='/dashboard']",
      "expected_visible_heading": "Dashboard",
      "seconds": 1
    }
  ]
}
```

The heading check is optional. When provided, Sauce Vids waits up to 15 seconds for the heading to become visible, then records `heading_verified: true` with the completed action in the capture receipt. If the heading never appears, capture returns an error rather than treating the loading screen as a successful shot. Use a heading observed on the actual destination page, not a guess. Recording continues during the wait; the receipt's timing can guide a later edit to remove loading frames.

## Verification

- **15/15 checks passed** using Hermes's official plugin admission validator, including capability registration and security scanning.
- **22/22 unit tests passed** for registration, input restrictions, and tool error responses.
- The plugin is listed for review in [the Hermes plugin catalog PR](https://github.com/NousResearch/hermes-agent/pull/154015).

```bash
python3 -m unittest discover -s tests -v
```

## Operating model

The plugin runs Chromium and FFmpeg locally, saves the footage on the host, and only records sites explicitly listed in `SAUCE_ALLOWED_HOSTS`. It is designed for authorized public websites and trusted operators. For hosted multi-tenant use, run capture workers inside a network-restricted sandbox.

**Open source:** MIT. Built for Hermes. Earlier visual research referenced the MIT-licensed [screen-demo](https://github.com/Third-Space-interactive/screen-demo) project; that code is not bundled here.
