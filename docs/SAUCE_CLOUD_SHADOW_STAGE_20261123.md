# Sauce — Cloud Shadow floating-window stage (2026-11-23)

**Status:** Real owner-only 1080p/60 render verified. Cloud backdrop / fixed rounded floating window implemented as a renderer stage preset. This is **not** visual acceptance of the entire film or a public product deployment.

## Owner instruction and actual reference

Owner supplied a blue halftone cumulus cloud image (1229 × 1536 portrait) and asked to use its cloud look with a fixed shadow and floating browser with rounded corners. The real source image was visually inspected beside the supplied 6.3333s UI Colors MP4. The previous editor used a nearly edge-to-edge dark studio plate and a mostly rectangular source screen.

The bounded stage preview asset `assets/stages/cloud_shadow_v1.jpg` is a downscaled **user-provided image crop**, not generated clouds and not an unrelated stock image: original pixels (0,205) through (1229,896), 480 × 270, JPEG, SHA256 `d760a91a6e2d8b138e483d1dbb1c047b2a3071a12bdf244d3b36842d2ff1d282`. Compositor softens halftone JPEG compression and reapplies subtle deterministic 4px screenprint texture. Retain source/image provenance; user wants this aesthetic. **Commercial media rights are not independently evidenced**: owner should verify the original image's redistribution rights before public commercial deployment. The private asset does not alter or synthesize original *software UI* content.

## Rigid / flexible implementation

- `studioStage.stagePreset = "cloud_shadow_v1"` is a renderer-recognized, strictly enumerated stage. No model-defined arbitrary background gradients, sticker layers, fonts, magic window shadow coordinates or radius.
- `scripts/cloud_shadow_stage.py` sets a constant 16:9 cloud stage. The physical card uses the original capture aspect ratio, centered with hard 12% top/bottom safety area, an approximately 20px radius at 1080p, a thin subtle border, a two-scale soft contact/elevation shadow, and no fake Chrome tab/address bar.
- The source video is still the **real decoded browser footage**. Camera interpolation from the existing real source-bound `studioStage.camera` moves *inside* the rounded physical viewport. The outer card and cloud plate do not change dimensions, position, silhouette, or shadow with the camera.
- `scripts/spatial_studio_stage.py`: the actual compositor, action/pointer visibility gates, source-rect projection, focus, and reading-context checks now use the inner physical window when the cloud preset is active, rather than pretending the whole MP4 is source pixels. Existing `classic` stages remain pixel-for-pixel default-compatible for old plans.
- The owner-only source-true action director and autonomous coverage planner now select the cloud preset for newly generated ordinary product films. The unattended Gemini JSON director mechanically locks `cloud_shadow_v1` at normalization, independently of any model-selected colors; the original proposal and normalization receipt remain separately visible. Already verified independent real DOM-plane foreground modes remain on their existing compositor path until proper spatial-to-cloud integration; unsupported cloud+domPlane combinations reject rather than silently masking source content. No public Studio redeployment.

## Actual rendered film — SHA-locked proof

Source: **original verified UI Colors Chromium capture**, same two real actions (light → dark theme, original contrast matrix) and recorded cursor. Capture source SHA256 `dc1c48559b7bc842eba3ad405c44724dbf06bdc9e2d748da7495cfb0384a1dbd`, event/cursor manifest SHA256 `90dddc0468c41e87fcf1b1f5bd58dbf11f9f7499b7c65ddcb26d066c143bde87`.

- Real new 12-second cloud-stage master, H264 1920×1080 60fps 720 frames, AAC48kHz.
- The **existing native source-beat JSON editor** cut the exact same verified original footage to 380 original source frames (6.333333 seconds) and remapped both genuine press→result windows and event-locked audio. No new scripted UI or fake cursor.
- Final cloud-stage cut SHA256 **`1af6b14ea2f862329ec3dde8d93c9570976f24ab1b0448968534e5837770f531`**, 1920×1080 H264/60fps 380 frames + AAC48kHz. Strict FFmpeg decode passed; 46 original-to-new projected-frame pairs max downscaled grayscale error **0.2518/255**, median 0.1438 (H264 recompression). First/second clicks: decoded 48kHz cue correlation **0.999/0.9998**, exact **0-sample** offset.
- [**Cloud Shadow 6.33s video**](https://devmcp.davemafy.xyz/sauce-expiring-review/tweakcn-20261120/sauce-uicolors-cloud-shadow-rounded-6s-20261123.mp4?md5=4CXAaTyC0qwqQ6uYdXvwKg&expires=1795674115)
- [Original continuous 12-second cloud-stage master](https://devmcp.davemafy.xyz/sauce-expiring-review/tweakcn-20261120/sauce-uicolors-cloud-shadow-rounded-12s-20261123.mp4?md5=2fDS97TBCeKdAUeARfeNzQ&expires=1795674115)

Both owner-only private signed 72-hour URLs HTTP200; unsigned requests HTTP403. Actual browser-video play and seek-to-4.5s passed at desktop1280×720 and mobile390×844, zero playback/JS errors. Contact sheet and full-size 1080p source-result render inspected; the cloud plate and rounded physical window remain visible at both real product states and through the source-verified time cuts.

## Remaining defects, no inflated creative approvals

The stage now has the requested literal blue cloud visual language and visible physical depth. **The source film remains a creative REJECT**: dense dark contrast matrix, visually static opening, weak original workflow storytelling, and small text in a landscape video viewed on a phone. The general encoded QA (which does not yet consume the source-beat edit map) flags STATIC_OPENING_2S, REPEATED_OR_STATIC_FRAMES and ABRUPT_CUT_CANDIDATE. This is not a new quality-approved customer film. Use actual customer/product storytelling with strong source actions, not more backdrop decoration, to address this gap.

No generated video or raw customer browser capture committed to Git; no new VM, paid media, public deployment or branches. Main-only tests and implementation are recorded in the living handoff.

