# Native 5K render on GitHub Actions

This workflow benchmarks actual browser-rasterized 5120×2880 product footage, not
an upscaled 1080p file. It captures the public [Brimble Agent page](https://www.brimble.io/agent),
follows a 12-second controlled scroll path, applies a plain neutral background
(no Sauce branding), and exports two clips.

- **5K master:** H.264 5120×2880 at 24 fps, intended for editing and capable desktop playback.
- **Android preview:** H.264 Constrained Baseline, Level 3.1, 1280×720 at 24 fps,
  with silent AAC audio to maximize compatibility on phone browsers.
- **Poster:** JPG frame suitable for a web-video poster.
- **benchmark.json:** capture, render/verification, and total timings, frame counts,
  dimensions, and codec information.

Both MP4s are decoded to completion with FFmpeg in the render workflow before
being uploaded; their dimensions and frame counts are verified with FFprobe.

## Running it

Open [Sauce 5K — hosted render benchmark](https://github.com/Davemafy/sauce-vids/actions/workflows/render-5k.yml)
in GitHub Actions, choose **Run workflow** on **main**, or change
\`scripts/render_github_5k.py\` or the workflow itself on main. The resulting
artifact is \`sauce-brimble-native-5k\` and is retained for 14 days.

This intentionally uses a GitHub-hosted \`ubuntu-24.04\` worker and no
privileged/self-hosted runner on Vultr. It requires no API keys or accounts
for the public source website. GitHub Actions artifacts are downloads, not
streaming-video URLs; users should play the 720p MP4 locally on Android.

To reproduce the comparison on an existing Vultr development workspace:

\`\`\`bash
python3 -m pip install 'playwright>=1.55,<2' 'pillow>=11,<13'
python3 -m playwright install chromium
python3 scripts/render_github_5k.py --out out/5k-benchmark-vultr --duration 12
\`\`\`

Compare the \`timing.total_seconds\` fields in the two benchmark receipts.
Do not compare with earlier Sauce previews using different codecs, sources,
frame dimensions, or capture logic. This measures pipeline runtime; it does
not validate the aesthetics or storytelling of the resulting film.


## First measured run (November 13, 2026 UTC)

Same \`scripts/render_github_5k.py\` script, identical 12-second input,
288-frame output, H.264 master and Android-compatible preview:

| Metric | GitHub-hosted Ubuntu 24.04 | Native Vultr VM |
| --- | ---: | ---: |
| Capture | 114.16 s | 133.64 s |
| Encode and full decode verification | 38.12 s | 30.32 s |
| Script total | **152.36 s** | **164.09 s** |
| Maximum process RSS | ~1.73 GB | ~1.72 GB |
| Outcome | 5K + 720p produced | 5K + 720p produced |

GitHub was ~7.1% faster *inside the render script* in this single test,
but its full hosted job took about **207 seconds**, including dependency
installation, setup, and artifact upload. The Vultr runtime was measured on
a prepared machine. Neither result is a reliable long-term performance
guarantee; repeated runs would be needed for statistical confidence.

[Successful Actions run](https://github.com/Davemafy/sauce-vids/actions/runs/43527441608)
contains an 8 MB artifact zip, including the verified 5K master, 720p phone
version, poster, and machine-readable receipt. It expires after 14 days.

We have verified code correctness and the ability to render 5K in GitHub
Actions, **not** the creative quality of this short scrolling-page test.
