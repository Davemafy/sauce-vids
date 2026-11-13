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
