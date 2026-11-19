# CMOkit 900-frame source-true optical film — private 15-second review

2026-11-18. **Rendered and verified; creative quality remains NOT APPROVED.** This is an honest, source-derived public landing-page showcase of https://cmokit.co/. It does **not** show or prove private CMO-agent operation.

## Watch and retrieve

- **Private, Basic-auth protected review:** https://devmcp.davemafy.xyz/sauce-private-review/cmokit-900-20261118/watch.html
- **Protected H.264/AAC master:** https://devmcp.davemafy.xyz/sauce-private-review/cmokit-900-20261118/master-1080p60.mp4
- **Protected output manifest:** https://devmcp.davemafy.xyz/sauce-private-review/cmokit-900-20261118/manifest.json
- **Protected click sync receipt:** https://devmcp.davemafy.xyz/sauce-private-review/cmokit-900-20261118/dry-run-verification.json
- **Protected redacted event ledger:** https://devmcp.davemafy.xyz/sauce-private-review/cmokit-900-20261118/events.json

These endpoints reuse the **existing Continuity Cloud HTTP Basic auth**; no usernames/passwords are in version control. Unauthenticated HTTPS GETs for the player and master returned **401**. Nginx config validated and reloaded; no other service, source project or production URL-to-video job was changed. This is a restricted owner review artifact, not a public Sauce release.

## Actual source evidence, with honesty about native fps

- Existing isolated Capture Engineer source root:
  `/srv/devmcp-workspaces/12e31c5c22751de1011b5f2f3022cceb/sauce-capture-current/artifacts/private-anchor/live-capture`.
- Real Playwright Chromium continuous captured source: `continuous-source.webm`, VP9 **1280×720/25fps**, 15.760 seconds including 0.781 seconds lead-in. Source SHA256 **`b4a58bb2e921c37cb55097a0431dd64a894ab87532e3bf6397f0233c21b2fb42`**. Signed-in or paid CMOkit workflows were not accessed.
- `scripts/story_arc_900_contract.py` verifies the original capture receipt hash, retimes the recorded 15.04215-second StoryArc to **15.000 seconds**, resamples source video using FFmpeg to **900 LOSSLESS PNG files** `frame_000000.png` through `frame_000899.png`, and emits `events.json` with source click coordinates and synchronized time indices. Input remains **native 25fps**, not 60 unique source moments. This limitation is carried into every receipt.
- Source frame sequence in the isolated coordinator checkout:
  `/srv/devmcp-workspaces/5c407ce984e7defcf77da3f1f9cb7f67/sauce-final-900-main/studio/.tmp/cmokit-final-900/frames/` (~156 MiB). Private source frames never copied to the website.
- Frame pad/trim contract `reconcile_frame_count`: if frames are short by ≤12 at the **end**, duplicates only the exact last original source PNG; if over by ≤12, moves originals to an `overflow-original-frames` quarantine (never deletes them); any interior gap or greater mismatch is a hard failure. **Actual capture required zero padding and zero trimming.** 900 file count, sequential naming, PNG format, IHDR 1280×720, and selected SHA256s verified.

## Capture → compositor event identity

Source `session.json` contains two real, captured navbar anchor clicks with measured CSS coordinates and browser timestamps. Both source time mapping and the compositor's ripple index use **the identical output integer frame**.

| Event | Source CSS position | Output frame | Output frame time | Quantization difference |
|---|---|---:|---:|---:|
| "How it works" | (868, 32) | **385** | 6416.667 ms | **-0.980 ms** |
| "Pricing" | (953, 32) | **674** | 11233.333 ms | **-0.350 ms** |

Thus **inter-lane event → first visible ripple frame offset is exactly 0 frames** for both clicks. Continuous timestamps must be quantized onto a 60Hz raster; the maximum physical quantization discrepancy is **0.980 ms**, not literally zero sub-millisecond time. Both click transients originate at the verified frame's **48kHz PCM sample index** (308000 and 539200), exactly **800 samples per 60fps frame**. No fabricated click positions or result states.

## Optical composition actually implemented

`scripts/story_arc_optical_master.py` consumes those exact PNGs and events:

1. Source-preserving **shallow curved-glass barrel** refraction via OpenCV remap in the outer ~42px of the browser plane only, with bounded chromatic edge dispersion. Product typography in the center is not distorted.
2. Existing deterministic `scripts/click_water_ripple.py` `cv2.remap` on the active click frames, centered at the measured source (x,y), with two real water waves, no fake drawn rings.
3. `scripts/story_arc_dom_text_mask.py` captures 347 authentic DOM text and button/control geometries, interpolated against the 119 captured source scroll positions. Protected text/control pixels are **copied back exactly from the unchanged source** after optical effects; frame-by-frame assertion verifies no masked pixels altered. During full render, ~141 million text-mask pixel checks passed. Source-aware modal protection remains fail-closed; the public source has no actual modal to claim.
4. Source-true bounded camera moves only **after** the clicked website has scrolled to the real explanatory/pricing section. Second-pass v2 reaches 1.25× framing while retaining the real navigation cursor inside the frame, and keeping verified section headings and pricing panel fully inside horizontal bounds. No interaction is invented.
5. Genuine app pixels are projected into a rounded, softly shadowed floating 16:9 dark-neutral stage. Exactly one existing Sauce reference ink SVG cursor is painted from interpolated **real recorded pointer samples**, after lens/refraction layers.
6. Two original low-gain, event-aligned synthesized Foley clicks, no licensed music or paid TTS.

Two private 15s outputs preserved. Final chosen output is **v2**, because the encoded how-it-works and pricing regions are more legible and the pointer stays in-frame across the optical push. It still has an overly static first ~6 seconds and source-native fade/scroll transitions, so do not label the cinematic quality 10/10.

## Machine and playback verification

- **Final**: `studio/.tmp/cmokit-final-900/final-v2/master-1080p60.mp4` in the isolated worktree. SHA256 **`36ff7f461fb0970b4d50a5a52acfdce1e490e3528357ba892777e7215df00c9d`**.
- H.264 yuv420p video **1920×1080, 60/1 FPS, exactly 900 frames, 15.000000s** and AAC stereo **48000Hz**. Entire master decoded with `ffmpeg -v error -xerror` successfully.
- `scripts/story_arc_900_dryrun.py` produced `final-v2/dry-run-verification.json`: zero event-to-ripple **frame offset** at both exact indices; first-frame changed source pixels outside text **987** and **1119**, and **0** protected text pixels altered. Source hash, frame sequence, output length, audio clock and first click-wave visibility tested.
- Created and **opened** the real final v1 and v2 15s contact sheets at 0s, 1s, 2.8s, 4.8s, 6.2s, exact 6.417s click, 6.65s source fade, 8.1s genuine "How" section, 9.8s focused result, exact 11.233s click, 11.48s source fade, 12.7s, 13.4s, 14s, 14.95s pricing hold. Enlarged both click close-ups; camera does not crop heading edges or duplicate cursor.
- Actual HTML5 video playback via Chromium at **1280×720 desktop and 390×844 phone**: `readyState=4`, no JS/media errors, no horizontal overflow, video played from seek 8.5s to ~9.7s with correct 15s duration.
- Synthetic negative tests enforce that altered event indices, missing interior PNG frames, >12-frame pad/trim, source-text deformation, fake navigation evidence and lost cursor/misaligned click center are rejected. The dedicated source/optics suite passed **9/9**; combined Phase 2 and source quality suites on pre-current-main passed **148/10 skipped**. Run current suite again after versioned integration.

## Reproduce privately (no paid inference)

```bash
cd /srv/devmcp-workspaces/5c407ce984e7defcf77da3f1f9cb7f67/sauce-final-900-main
export PYTHONPATH=scripts
CAPTURE=/srv/devmcp-workspaces/12e31c5c22751de1011b5f2f3022cceb/sauce-capture-current/artifacts/private-anchor/live-capture
ROOT=studio/.tmp/cmokit-final-900
/opt/sauce-vids/.venv/bin/python scripts/story_arc_900_contract.py --capture "$CAPTURE" --out "$ROOT" # use fresh empty out; --verify-existing for guarded reuse
/opt/sauce-vids/.venv/bin/python scripts/story_arc_dom_text_mask.py --url https://cmokit.co/ --out "$ROOT/text-regions.json"
/opt/sauce-vids/.venv/bin/python scripts/story_arc_optical_master.py --raw "$ROOT" --out "$ROOT/final-v2"
/opt/sauce-vids/.venv/bin/python scripts/story_arc_900_dryrun.py --raw "$ROOT" --master "$ROOT/final-v2/master-1080p60.mp4" --out "$ROOT/final-v2/dry-run-verification.json"
/opt/sauce-vids/.venv/bin/python -m pytest tests/phase2/test_story_arc_900_pipeline.py -q
```

**Remaining quality gap:** These render and validation programs are now versioned as opt-in capability, but the running `/opt/sauce-vids` URL service was not switched to them and the final preview is not premium/owner-approved. Source native capture sharpness and 60Hz, an action-first first three seconds, source-site fade avoidance, and body text readability at 390px remain unresolved. Never confuse exact frame synchronization with award-winning visual direction.
