# Sauce Scripted Renderer v2 — verified handoff (2026-11-16)

**Status:** implementation and technical gates verified. Premium multi-action film quality remains an editorial acceptance decision, not implied by green tests. Repo Davemafy/sauce-vids, main only. Original Phase 2 3d-launch and its proofs are untouched.

## Public evidence

- Player: https://devmcp.davemafy.xyz/sauce-motion-phase2/scripted-v2/
- Master: https://devmcp.davemafy.xyz/sauce-motion-phase2/scripted-v2/master-1080p60.mp4
- Contact sheet at 0.4-second intervals: https://devmcp.davemafy.xyz/sauce-motion-phase2/scripted-v2/contact-every-0.4s.jpg
- 100% callout: https://devmcp.davemafy.xyz/sauce-motion-phase2/scripted-v2/callout-at-native-100pct.png
- 100% opening/final: first-frame-100pct.png / final-frame-100pct.png at that folder.
- Checksums: frame-sha256.json and release.json at the same URL prefix.
- Verified master SHA-256: 99e05ec4f60305fb5880eab736af889bbf6d5d5237b7d6766e733f3bcba3f25e

## Cause, fix and actual verification

1. **Callout arc:** scripts/studio_motion_callouts.py contained an explicit PIL ImageDraw.arc 180–342 degrees and top decorative line. Removed both and preserved one rounded outline. The new scripted callout has no arc. Opened the actual 100% pixel crop and verified no stray curved line.
2. **Camera consistency:** scripts/scripted_v2_render.py now uses a fixed 1480×832 browser window, a quintic 6t^5−15t^4+10t^3 eased camera in CSS coordinates, no tilt/rotation and an explicit static hold after every move. Target rectangle determines camera focal point. Source viewport edges are clamped. During QA, identified and fixed a separate incorrectly constructed rounded mask that had caused black top bars and white corner protrusions.
3. **Opening:** immediately start at a 1.55× camera framing of the observed Connect control, with an identical first 1.3 seconds. Opened native frame and verified legibility.
4. **Stray panel:** actual trace verifies a 560×376 terminal at CSS x=640,y=172. For this Brimble storyboard, the compositor presentation-masks the terminal and restores all original Radix dialog pixels, including its expanded copied-command state. This is concealment of a recorded panel, not evidence that the underlying application state changed.
5. **Ending:** final camera is 1.34× and shows the *complete* real dialog. Last 1.5 seconds remain unchanged. Initial CRF16 H.264 produced 17 unique decoded images in the 90-frame hold despite identical raster inputs; fixed by lossless x264 QP0 with B-frames disabled. New final MP4 passes **90/90 decoded frames with exactly one unique hash** and the source has 90/90 identical raw-frame hashes. This is a High 4:4:4 Predictive H.264 profile with yuv420p pixel format; published player intentionally serves a broadly compatible High-profile 720p preview, while the 1080p lossless master is downloadable.
6. **Audio:** optional local licensed music and/or voice are supported, with a deterministic 48kHz frame clock, voice-triggered music ducking (approximately −13 dB) and two-pass EBU R128 normalization to −16 LUFS. The public sample used an original low synthetic bed and measured −16.0 LUFS; no real voiceover was supplied. Synthetic voice ducking tests passed. Explicit --silent or no audio input produces silent AAC.
7. **Longer scripted films:** demos/brimble-scripted-v2.json contains eight editorial steps referencing six SHA-verified DPR2 2560×1440 snapshots and two genuinely recorded clicks. Each shot defines action, target, zoom, movement time, static hold, optional caption/callout, panel concealment and optional redaction rectangles. scripts/scripted_v2_schema.py rejects unverified/nonmonotonic state references, invalid geometry, fabricated click steps and private captions. These are **scripted editing beats over existing captured actions**, not invented product actions.

## Deterministic acquisition, privacy and exports

The render is a deterministic source-backed offline re-edit, not one Chromium replay per output frame. Each screenshot is SHA-verified; output frames are written at 60fps through a raw BGR24 FFmpeg pipe independent of machine processing speed. Browser acquisition for future sessions lives in scripts/scripted_v2_capture.py: wait for network idle, document.fonts.ready, visible images decoded and finite Web Animations finished, then acquire a HiDPI screenshot. The blur_selectors hook resolves actual live DOM rectangles and destructively obscures these source regions. Missing selectors cause explicit failure. Archived screenshots cannot safely guess selector positions. No private raw states or HAR files are included in public exports.

The 1440p option renders 2560×1440 directly from the verified DPR2 website pixels inside a scaled stage, not by upscaling a finished 1080p video.

### Reproduce on the persistent Vultr worker

~~~bash
python scripts/render_scripted_v2.py \
  --script demos/brimble-scripted-v2.json \
  --out studio/.tmp/my-scripted-demo --original-bed
~~~

Alternatives: --resolution 1440p, --silent, --voice /path/to/approved.wav, --music /path/to/licensed.mp3. Output and private session directories must differ. The example references the private worker fixture; do not commit source screenshot states.

## Completed verification

| Acceptance | Measured |
| --- | --- |
| Main film | 27.25s; 1635 frames; 1920×1080; 60fps; H.264/AAC 48kHz; complete FFmpeg decode |
| Sound | Integrated −16.0 LUFS with original optional music |
| 100% callout | Opened pixel grab; no arc/top-line artifact |
| Camera | Fixed-stage geometry, no tilt, quintic eased moves and static holds; 69-sample contact sheet at 0.4s |
| First second | Tight 1.55× Connect framing, legible full-resolution button text |
| Stray terminal | Presentation-only concealment, live source modal pixels restored and source-backed tests |
| End payoff | Full modal + code, 90 identical raw and 90 identical decoded video frames |
| Same script twice | All 1635 SHA256 raw-frame hashes identical; entire MP4 SHA256 identical |
| Optional 1440p / silence | Separate 2.5s 2560×1440/60fps H.264/AAC silent smoke export; 90 decoded hold frames identical |
| Public desktop/mobile | Playwright 1280×720 and 390×844, seek 26.7s, HTTP 200, no video errors, no horizontal overflow |
| Tests | 25/25 TypeScript; 160/160 Python unittest; 25/25 Python pytest with browser checks |

## Not claimed / future work

The 27s sample demonstrates the new editorial engine but deliberately has only two real user clicks: it does not establish premium storytelling for a 20–40s product film featuring several distinct actions. A real narrator was not provided or used; voice-over mixing was exercised with synthetic speech and requires an end-to-end author-supplied voice track QA. The 1440p renderer was validated with a 2.5s smoke render, not a full 27s 1440p film. Cross-app modal bounds, live state repeatability, arbitrary privacy detection and mobile hardware decoding of the lossless High 4:4:4 master remain unverified. The High-profile 720p preview mitigates that playback compatibility issue.
