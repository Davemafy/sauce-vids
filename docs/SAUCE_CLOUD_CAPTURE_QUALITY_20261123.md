# Sauce — scrollbar-free high-fidelity large cloud window (2026-11-23)

**Current stage update (2026-11-23):** The former 480×270 cloud-art limitation documented below is resolved by the exact 1536×864 third user reference. This file remains historical evidence for the capture/scrollbar/87.5%-window fixes. See [SAUCE_CLOUD_SHADOW_HIFI_20261123.md](SAUCE_CLOUD_SHADOW_HIFI_20261123.md) for current stage asset, film hashes and remaining editorial defects.

**Status:** isolated owner-only 1080p/60fps encoded film verified. This is a meaningful source-capture and framing repair, not a premium film or public self-service deployment.

## Cold review of the owner's actual uploaded movie

The owner's `1000424582.mp4` was inspected at actual 1920x1080, 60fps H264 ~2.95Mbps. At ~3.8s the CSS generator heading was cut on the left by an over-focused overview camera; the original webpage scrollbar was visible along the rounded card's right edge. The floating source card was only 1313x821px (76% output height). The cloud plate was only a 480x270 JPEG before enlargement to 1080p, and the recorded browser site was a 2880x1800 DPR2 source shrunk down inside a small physical card. H264 bitrate is NOT alone an explanation for softness.

## Fix implemented on existing machinery, main only

- **Scrollbar:** existing `session_capture.MOCKUP_SCROLLBAR_STYLE` and `install_presentation_cleanup` reused in `public_interaction_scout.py`, `record_scouted_interactions.py`, and `source_truth_tab_capture.py`. The style is installed at document initialization and after hydration before the true first recording frame. It hides visible root/nested Chromium scrollbar chrome, **not** document content; wheel, nested scrollTop and real browser actions work. Real Playwright 960x540 browser test verified scrolling still works on original and nested overflow after style injection. Old captured media remains untouched; do not fabricate an in-place correction of baked original scrollbar pixels.
- **Window:** rigid `cloud_shadow_v1` card changed from 76% to **87.5%** of available 1080p height, while staying inside 16:9 landscape with genuine 60px+ margins. For a 2880x1800 source the card increases from 1313x821 to **1512x945 pixels**, about **32% greater readable software area**. Real border radius, shadow, cloud plate and fixed outer shell remain.
- **No accidental crop:** new cloud `overview` camera validation rejects keyframes whose physically measured original-page visible fraction falls below **0.935**; the bounded Gemini JSON feedback supplies the exact physical source-content crop error. The general deterministic original-source director now starts on the full webpage, uses restrained camera scale for full-page results, and classifies a genuinely verified compact/modal result as **detail**. No source URL-specific coordinates or events.
- **Actual source sharpness:** when a DPR2 2880x1800 source is projected into the ~1512px card, pre-downsample with `cv2.INTER_AREA` before perspective warping with `cv2.INTER_CUBIC`. This removes one un-antialiased 2:1 shrink. The source recorder now uses x264 `ultrafast -crf 14` (versus 17 in the scout recorder, 18 in tab capture), retaining native-60fps realtime capture; final compositor and existing timeline recut use `libx264 -preset medium -crf 15` versus higher-CRF fast presets. These changes reduce generational compression without claiming fixed text readability on a phone.

## New live, genuine source evidence

Re-ran the **same two independently scouted anonymous UI Colors controls** on the real public website through a fresh Chromium 1440x900 CSS / DPR2 / native60 browser on the existing 8vCPU/16GB Vultr worker, with the CSS cleanup before the frame recorder. Both interactions were confirmed by actual DOM+pixel changes:

- Action 0 `Switch to dark mode` result pixel fraction `0.75317`; action 1 `Contrast matrix` fraction `0.68237`.
- 720 original frames, 92 real source-pointer samples, **no visible main-page scrollbar** in independently inspected native source frame. Full source MP4 SHA256 `d764c4152b60097cf90cee3ef3f3cabe185c3947d54a9cfe7723312ece90535c`, new validated native event manifest SHA256 `ef14cc3778fd3f2f6646412765a4724f0ebc89975403b72758570a36d940c349`.
- New 12s cloud-stage source-true master, native1080p/60fps H264 AAC48k, full FFmpeg decode.
- Existing verified native-frame edit reused without altering genuine source time; 6.333333s = 380 original native frames, two real click/result windows, 48kHz aligned audio. Final MP4 SHA256 **`7f2fd7729e89b291058705fc3cc57d85a53668de97f14aad6deca4782f3bdab6`**, bitrate ~3.26Mbps (higher than old 2.95Mbps; not a reason to declare premium). Strict FFmpeg full video/audio decode passed. 46 actual original-to-output mapped frame pairs: max gray MAE **0.2009/255**, median **0.0987/255**.
- Owner-only expiring signed preview, verified HTTP200 and unsigned403: [6.33s bigger+clean movie](https://devmcp.davemafy.xyz/sauce-expiring-review/tweakcn-20261120/sauce-uicolors-large-clean-cursor-main-6s-20261123.mp4?md5=x2TtoWN_KmurptYMFbh0Dg&expires=1795676412); [original continuous 12s large+clean movie](https://devmcp.davemafy.xyz/sauce-expiring-review/tweakcn-20261120/sauce-uicolors-large-clean-cursor-main-12s-20261123.mp4?md5=oPY2yL4kbygcUlazbYb14A&expires=1795676412). ~72h from generation.
- Actual Chromium video play, positive playback-time progression and seek-to-4.4s passed, **both 1280x720 desktop and 390x844 mobile**, HTTP200, no JS/media errors. Contact sheet + full-size original and revised frame inspected; actual full page title now visible before modal, card visibly larger, no visible scrollbar. This is *film evidence*, not just mockup CSS.

## Explicit remaining quality rejections

- **The cloud backdrop is still the previous optimized 480x270 JPEG.** The user's original uploaded ~1229x1536 image exists in the conversation but has NOT been promoted to an equivalent original-resolution asset inside GitHub. The backdrop remains intrinsically softer than the DPR2 product footage; do not claim true full-resolution stage art. Preserve rights review before public use.
- Source page has large dense UI and small contrast-matrix labels. On a 390px mobile landscape player even 1080p output cannot make the entire 1440CSS-wide source readable. Needs more intentional product-specific detail shots/stronger real story and possibly a separately directed 9:16 cut if requested.
- The new encoded 12s film's general frame-quality QA is still **REJECT** for repeated/static frames (0.714); the 6.33s recut is **REJECT** for static opening, repeated/static frames (0.79), and one cut candidate corresponding to an intentional source-verified edit. The generic QA has no source-beat cut-map awareness. **Premium human approvals ZERO.** The stage/capture fixes are real; they do not solve story direction.
- No paid inference, client sign-in, customer contact, public API deployment, new VM or new branches.

## Verification

Dedicated new tests `tests/phase2/test_cloud_capture_polish.py` cover scroll-cleanup reuse in all three public capture paths, live Chromium scrolling through root and nested overflows, stage margins/window size, and encoder contracts. Updated cloud-window and Gemini preflight regression tests. Whole Phase2 + concurrent `tests/test_model_shootout.py` suite: **495 passed, 10 skipped, 29 subtests passed** on pre-commit candidate. Independent full source decodes + desktop/mobile browser playback verified. Source files, personal reference and new movie remain outside Git.

