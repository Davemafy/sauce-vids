# Sauce Cloud Glass v2 — owner reference correction (2026-11-24)

**Repository:** `Davemafy/sauce-vids` / `main` only. **Workplace:** recovered existing persistent Vultr DevMCP worker. No new infrastructure or separate Git branch. Owner supplied two direct images: an actual Brimble shot from Sauce and a Y2K glossy sky-filled acrylic reference. The mismatch was explicitly called out: Sauce had rendered a 26px border around a near-full-card browser over a cobalt halftone wallpaper, while the reference depicts an entire swollen cloud-filled glass body with white ambient surround, broad curved softbox light and a cut-in lower-right tail.

## Corrective implementation

Rather than cosmetically thickening the old border or destroying a previously verified stage default, added an **opt-in `studioStage.stagePreset: "cloud_glass_v1"`** to the actual source-true video compositor. Legacy `cloud_shadow_v1` and `classic` remain valid and pixel/geometry-identical.

- New `scripts/cloud_glass_object_stage.py`: genuine rounded organic glass body nearly spanning the 16:9 output; lower-right recessed swirl and broad lower tail, white gallery surround, soft elevation/contact shadows.
- The source-true browser is inset in a separate foreground aperture: at 1920×1080 with 2880×1800 original source, `window_geometry()=(211,140,1490,939)`; visual real browser height **799px (74% of output)**. The body fills ~87.2% of the output while exposed actual blue acrylic outside the crisp browser occupies ~**37.9%** of the total output area. Old shell exposed a mere 26px trim.
- Original user-supplied licensed cobalt sky artwork, retained as `assets/stages/cloud_shadow_v2_1536x864.jpg`, is gently de-screened/softened **only in the acrylic body**. Pale upper cloud glass and deeper cobalt lower volume, bounded curved-surface refraction, white meniscus and concentric specular ridge, strong horizontal upper softbox reflection, left/right studio reflections, and dim curved floor reflection are composited into the physical stage plate.
- No giant reference cursor, fake retro windows, phone illustration, fake popup, fabricated state or screen blur. The genuine page is projected from the original source video onto the aperture and finally composed over all glass. Source DOM event/manifest hashes, source timing, pointer track, camera trajectory and playback were unchanged.
- `scripts/spatial_studio_stage.py` now validates and projects the new approved opt-in stage, including the real camera's physical dolly and overview visibility bounds. `scripts/cloud_shadow_stage.py` chooses the appropriate immutable stage/material and aperture, preserving its original path for the legacy preset.
- `tests/phase2/test_cloud_glass_object_stage.py`: 4 regressions checking actual cloud-object surface visibility, white surround and organic notch, legacy geometry preservation, original source-pixel RGB equality in opaque foreground, landscape bounds and accurate verified DOM region visibility.

## Actual media proof — owner only, not a mockup

The same independently verified Brimble 6.5s DPR2, native60 Chromium capture (`../.sauce-stagehand-private/brimble-fast-native6s-20261123/source-native-dpr2-60.mp4`), original verified source manifest and original camera JSON were used without altering original evidence. Film plan for **only this private experiment** changed `stagePreset` to `cloud_glass_v1`.

- Exact new real MP4: `../.sauce-stagehand-private/glass-object-study-20261124/brimble-glass-object-6p5s.mp4`, **SHA256 `86f023f5f5e6efbde46c13db7ef03ab6981f13339a8ff22e9fd65611906f9e18`**, **6.500s**, H.264 1920×1080/60, **390 output frames**, AAC 48kHz, size 3,195,194 bytes; strict FFmpeg full decode PASS.
- Actual private study film plan: `../.sauce-stagehand-private/glass-object-study-20261124/film-plan.json`. The original recorded click and resulting Brimble dialog remain real/source-true. Camera/source-validity checks passed.
- Rendered and directly inspected: actual object-only plate, original webpage wide at 0.3s, result closeup at 3.5s, release at 5.9s, and the **10-frame encoded contact sheet**. Stage now visibly occupies the space rather than wallpaper framing a 26px border.
- Encoded supervisor QA **`HUMAN_REVIEW_REQUIRED` with zero automatic findings**. This is neither 1:1 photographic accuracy nor premium-film owner approval; original Brimble value-story remains limited to an agent connection dialog.
- Owner-only signed expiring film served through existing secure route; signed GET 206, unsigned GET 403. Desktop Chromium 1280×720 and mobile 390×844 successfully decoded and sought to 3.4s (video 1920×1080, 6.5s, zero JS or media errors). Original camera/cloud film remains available unchanged.
- Regression verification before publish: **517 Phase2 tests passed, 10 skipped, 21 subtests passed**; legacy unittest **302 run, 2 skipped**, zero failures. `git diff --check` clean.

## Remaining visual truth

This is a much better material/composition match, **not** an exact original-photo reconstruction: the real reference contains photographic cloud texture, physically photographed glow, its own stylized popup/phone artwork and a differently proportioned object. Sauce uses an existing safe cloud material plus raster-optical simulation, and still prioritizes the real product's readability. Under a deep post-result camera dolly, the stage object intentionally moves partly out of frame. At the wide overview, browser text is smaller than in the old 87.5%-height default; the close-up remains necessary for the actual result. Keep the old preset available and leave this new opt-in variant private until the owner reviews and explicitly approves a default switch.

**Zero owner-approved premium Sauce films; no production Studio redeploy or public client launch.**
