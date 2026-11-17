# Sauce real Chromium + FFmpeg render-load gate

**Verified 2026-11-17 · Source: GitHub main · private pilot only**

This is a controlled, real end-to-end **capture → render** stress test, not an API mock and not permission to open the self-serve product. The test fixture is a real public **Sauce-owned** website: \`https://devmcp.davemafy.xyz/sauce-app/studio/samples\`. No outside site interactions, external customer jobs, AI direction calls, API billing, checkout, or private capture data. The VM had 8 vCPUs, ~16 GiB RAM, and ~237 GiB free disk before the tests.

## Actual test method

1. Independently inspected Sauce's sample page using the real \`backend.product_explorer.inspect\` Chromium browser. Observed actual DOM headings \`h0\` ("Make a recording worth watching.") and \`h3\` ("Finish"), saved private source inspection receipt. Used only an honest **showcase** plan for these observed headings. No simulated clicks or claims of protected functionality.
2. Launched isolated processes running the exact current-main \`python -m backend.live_capture\` (Playwright video recording) and \`python -m backend.live_render\` (FFmpeg/libx264 encoding). Each job created a genuine continuous-source WebM, SHA-256 capture ledger, 1920×1080/60fps H.264 master, 1280×720/30fps preview, source-verified release receipt, poster, and player. This is the live public URL pipeline, **not** the separate Phase 2 deterministic cinematic compositor.
3. Three bounded waves: one, two and four parallel complete jobs. Each ran under the unprivileged \`devmcp\` account at \`nice -n 10\` with paid inference removed from its environment. A health guard refuses to start if production customer jobs are queued, and monitors system RAM/free disk against a 4 GiB memory / 8 GiB disk safety floor. 0.5 s whole-VM CPU and available-memory samples were recorded. Capture capped at 125 s and render at 270 s per job; the test stops if an actual failure occurs.
4. Independently reran the actual **production checkout** after a targeted runtime fix, with the Playwright browser-cache environment variable deliberately unset. No service restart or rebase of dirty production checkout.
5. Verified each exported master with \`ffprobe\`, then executed **full FFmpeg -xerror decode** of all eight finished films. Opened a four-frame actual-encoded contact sheet from 0.3, 1.2, 2.3 and 3.6 seconds of the production-checkout export. No frames were invented.

Source-runner: \`ops/stress_sauce_render_pipeline.py\`. Logs, source videos, exports and aggregate JSON receipts are **private** under \`/var/lib/sauce-steward/qa-logs/render-stress-20261117/\`. Do not publish them automatically.

## Real concurrency results

| Simultaneous real capture+render jobs | Finished | Full wave wall time | Peak total VM CPU usage | Minimum VM MemAvailable | Exported finished video duration |
|---|---:|---:|---:|---:|---:|
| 1 | 1/1 | **9.765 s** | **87.0%** | **13,071.9 MiB** | 4.38 s |
| 2 | 2/2 | **12.018 s** | **97.7%** | **12,358.1 MiB** | 9.33 s total |
| 4 | 4/4 | **17.799 s** | **99.8%** | **11,055.2 MiB** | 21.39 s total |

Per-job recording wall time was ~5.5–6.5 s, while encoding took 4.26 s (one job), 5.78–6.01 s (two), and 10.80–11.27 s (four). CPU saturation **clearly begins by four concurrent workflows**, and transient whole-machine CPU usage was already 97.7% with two. RAM remained safely available for this tiny 4–6-second fixture; these data do not justify more concurrency for 30–60-second customer clips.

**Correct interpretation:** All seven *staging parallel* capture/render jobs succeeded. This DOES NOT mean the customer-facing job executor can run four simultaneously: \`backend/sauce_api.py\` deliberately uses \`ThreadPoolExecutor(max_workers=1)\` and accepts at most two queued+active jobs in the pilot. No live paid queue or production concurrency policy was changed.

## Critical real-production issue discovered and fixed

**Failure encountered:** The first baseline real capture failed while creating its Chromium page video: Playwright requested \`/home/devmcp/.cache/ms-playwright/ffmpeg-1013/ffmpeg-linux\`, which did not exist for the worker account. Existing \`/opt/devmcp-browsers/ffmpeg-1013/ffmpeg-linux\` was already executable, but \`PLAYWRIGHT_BROWSERS_PATH\` was not configured in the running Sauce service's environment. Previous GET-only / fake-worker tests could not detect this. The failed fixture and log are retained privately.

**Source fix** committed to main: \`backend/live_capture.py\` adds \`ensure_video_helper()\`: when no explicit Playwright browser cache is set, and a real \`ffmpeg-*/ffmpeg-linux\` exists under the Vultr shared browser directory, it selects that directory. Explicit operator paths are preserved; other installations without the helper are unchanged. No binaries installed or downloaded and no paid calls. Unit tests \`tests/test_live_capture_env.py\` cover discovery, explicit override, and missing helper.

**Surgical deployment:** The original \`/opt/sauce-vids/backend/live_capture.py\` was **untracked in the pre-existing dirty production checkout**. Diff verification showed the GitHub source was byte-identical apart from this small helper. The existing file was backed up at \`/var/lib/sauce-steward/deploy-backups/real-pipeline-20261117/live_capture.py.bak\`, and only that exact file was updated; the rest of production's dirty files and systemd services were preserved. No restart needed since captures run in a fresh subprocess. A real **production-checkout** Chromium capture and render then succeeded with \`PLAYWRIGHT_BROWSERS_PATH\` explicitly absent. Its final master was 1920×1080/60fps H.264, **257 frames / 4.283 seconds**, fully decodable with FFmpeg, and source-provenance receipt showed \`continuous_motion=true\` and \`source_verified=true\`.

## Media, quality and scope checks

- **8/8 actual MP4 masters** (seven staging parallel outputs + one post-fix production-checkout output) passed complete FFmpeg decode and stream validation; master dimensions **1920×1080, 60fps**, durations from 4.28–5.52 seconds and frame counts 257–331.
- Actual capture receipt SHA-256 matched each original source WebM and each output release receipt referred back to that source.
- Contact-sheet inspection confirmed real Source page with legitimate sample video panels, no fabricated UI. However, the footage is a relatively static, dense, wide Sauce Studio view. It does **not** exhibit premium editorial focus or a persuasive product-action narrative. It was selected as a reproducible owned-site *performance fixture*, not as an approved film.
- The current live recorder captures at **1280×720 DPR1**, then upscales to 1080p/60fps, so a 60fps encoded master **does not prove 60 unique real browser-rendered frames per second** or satisfy the premium DPR≥2 standard. The pointer remains a small circular in-page marker. These are known product quality gaps.
- Approximate temporary wave artifact sizes: 1-job **4.3 MB**, 2-job **9.3 MB**, 4-job **19.8 MB**. Real customer footage size/encoder settings may be much larger. The worker remained alive, all three services active throughout.

Targeted tests after the helper change: \`14 passed, 15 subtests passed\` for \`tests/test_live_capture_env.py\`, \`tests/test_sauce_api_load.py\`, \`tests/test_sauce_pilot_stress.py\`, and \`tests/test_url2video_api.py\`.

## What this does NOT prove and next release gates

- No sustained soak over hours, no 8/16/30-job real render wave, no multi-user queue latency percentile, no streaming 100–500 MB files, no packet loss/slow 4G measured, no spontaneous host reboot or mid-render recovery live, no actual AI provider rate-limit or paid inference cost profiling.
- The 4-job wave already achieved 99.8% VM-wide CPU. **Do not increase production worker concurrency** based on this test. First add bounded FFmpeg thread allocation and CPU/memory/disk per-job quotas, then test **real 30–60-second** captures on the owned fixture and prove low-background overhead under simultaneous website users.
- Before unrestricted release: real HTTP byte-range/206/416 streaming instead of full-buffered media; proper account/tenant isolation, quotas and cost caps; safe in-progress interruption policy; slow-network Android playback; genuine buyer-reviewed visual results. Full creative Phase 2 Brimble visual defects remain separate.
- This was an execution performance gate, not a creative quality gate and not any commercial validation.

**Release decision: keep the private pilot; the discovered missing recorder helper is fixed and verified. Keep one production render worker for now.**
