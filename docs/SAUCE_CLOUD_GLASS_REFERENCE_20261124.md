# Sauce Cloud Glass material — 2026-11-24

The owner's uploaded 1536×976 retro sky-glass reference is used as a visual material study, not copied as a composited product screen. No fake popups, cursors, chrome or flip-phone art were imported. The existing verified 1536×864 cobalt stage asset remains authoritative.

## Implemented compositor effect

- `scripts/cloud_shadow_stage.py`: cached, expanded 26px acrylic shell around the unchanged 1512×945 source-true viewport at 1920×1080. Outer radii ~70px; fixed stage stays 16:9.
- Real clouds from the existing stage image are embedded in translucent blue acrylic with bounded edge refraction, lightly softened cloud material, brighter upper/left bevel, milky top-left illumination, horizontal specular streak, broad lower reflection, and distinct contact/elevation shadows.
- All glass effects happen **behind** the original browser mask. No source content blur or fake UI overlay. The existing spring camera carries the physical glass together with the object.
- Tests: updated `tests/phase2/test_cloud_shadow_stage.py` for the thicker shell/shadow, plus `tests/phase2/test_cloud_glass_reference.py` for material geometry, source pixel purity and 640/1280/1920 landscape sizes.

## Real encoded verification

Previously verified 6.5s Brimble native60 DPR2 source, its exact real-event manifest, and source-verified camera plan remained unchanged. New encoded film at private worker path `../.sauce-stagehand-private/glass-shell-preview-20261124/brimble-glass-shell-real-6p5s.mp4`, SHA256 `40c03ff50ca80a674478c227a94549a813d807125ad8ac958fbad54c8f461f47`, 390 output frames, H.264 1920×1080/60fps plus AAC stereo 48kHz; strict full decode passed.

Compared to the original encoded film at t=0.3s and t=1.2s, the genuine UI interior mean absolute RGB deltas were 0.110 and 0.242 of 255 (ordinary codec variation), while the exterior glass band's differences were 80.899 and 80.975 of 255. The actual 0–6.5s contact sheet and the wide frame were viewed. QA returned `HUMAN_REVIEW_REQUIRED` with no automatic findings; this is **not** owner premium approval.

The existing private review location serves the new video by expiring signed access; signed HTTP 206 range works, unsigned 403. Browser playback and seek to 3.2s passed at 1280×720 desktop and 390×844 mobile with no JS/media errors.

## Remaining distinction

The original reference is an entire cloud-filled object with retro graphic overlays and a notched corner. Sauce instead needs a readable original product viewport inside that material. This is a faithful glass-material treatment, **not** a pixel-by-pixel copy of the entire uploaded photograph. During immersive close-ups the object may fill the frame, making its exterior material temporarily invisible. Original film's weak single-dialog story has not changed. Zero owner-approved premium films; no running Studio deployment.
