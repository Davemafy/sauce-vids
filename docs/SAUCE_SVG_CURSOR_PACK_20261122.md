# Sauce Phase 2 — genuine SVG cursor-pack replacement (2026-11-22)

**Scope:** Existing source-true film compositor, GitHub `main` only, persistent Vultr worker. User rejected the prior "fixed" pointer because it was a Tabler UI icon instead of a real cursor theme.

## Reality check and sources

A screen-recording cursor is not an arbitrary icon. It needs an actual cursor silhouette, correct click hotspot, controlled native size, high-DPI antialiasing and stable source-true pointer motion. The previously introduced `Tabler pointer-outline` is intended as a UI icon. Its silhouette looked like a tilted, split-tailed symbol in the encoded Recode MP4. Merely passing cursor shape tests did not make it visually acceptable.

Compared the following **actual cursor-theme SVGs** on a close crop of the genuine encoded Recode video at the same hotspot, *without* picking from a marketing image:

- [Bibata Modern Classic / Ice](https://github.com/rtgiskard/bibata_cursor), genuine SVG cursor theme, **GPL-3.0**. Its round chunky silhouette is appealing but the asset has copyleft obligations to consider; the upstream SVG and metadata were inspected privately, not committed or reused in owner videos.
- [Phinger Light / Dark](https://github.com/phisch/phinger-cursors), genuine SVG theme, **CC BY-SA 4.0**. Browser-scale outline is delicate and licensing requires attribution/share-alike on adaptations. No Phinger assets copied into Sauce.
- [Colorosse Mint Cursors](https://www.colorosse.com/assets/2d/ui/mint-cursors), **CC0-1.0**, original `cursor-arrow.svg`, `cursor-hand.svg`, `cursor-text.svg` supplied as actual 32×32 SVGs with native per-role hotspots. The original pack was fetched from its own CDN archive, verified and inspected at real screen scale. We selected the clean geometric Mint arrow with **render-only high-contrast white rim**, using original black interior, original geometry, original `hotspot 0,0` declaration and no invented cursor movement. Its outline is easier to read against the real dark Recode editor than the original pack's muted gray stroke.

**Source provenance:** `assets/cursors/mint-studio/{arrow,hand,text}.svg` are verbatim from Colorosse's CC0 archive; `PROVENANCE.md` documents original source, role SVGs and their license. Runtime changes only the `#66757f` SVG rim to `#f5f7fb`, never rewrites the source assets.

## Actual implementation

- `scripts/recorded_pointer.py`: `_mint_svg_sprite(role,size)` uses CairoSVG supersampled 4×, Lanczos downsample, cache and exact original role hotspot metadata: arrow (0,0), hand (10,2), text (16,16). One genuine source-timed pointer only. Normal 1920×1080 fullscreen film scale `0.73` produces a ~40px SVG tile, with a narrower conventional arrow shape; not a giant icon. `draw_pointer(..., theme="mint-studio")` and `project_pointer(..., theme="mint-studio")` retain the source coordinates and action clock. A consciously opt-in `tabler-legacy` mode is preserved strictly for reproducibility/comparison, not a silent fallback to old shapes.
- `scripts/render_event_video.py`: operator-owned `--cursor-pack {mint-studio,tabler-legacy}` (default **mint-studio**); this explicit parameter travels through fullscreen, perspective-stage and DOM-plane pointer paths and is recorded in camera diagnostics. Film-plan JSON still owns cursor **presence**, never invented mouse movements or CSS selectors. This avoids inventing site state to manufacture a cursor theme change. Pack hand/text assets are available for future **verified** cursor-role metadata, not automatically activated by a guessed DOM state.
- `tests/phase2/test_recorded_pointer.py`: compare actual full-frame painted cursor pixels against *independently rasterized* original Mint CC0 SVG with only white-rim color transform, test exact native arrow/hand/text hotspots, malformed sizes/roles, unchanged camera-projected source points, and explicit legacy sprite equivalence. The legacy opt-in rerender is **byte-identical** to the original rejected Qwen cursor MP4, so this change is reversible.

## Visual and file verification

**Same genuine Recode source:** 1920×1080, 60fps, 294 frames / 4.900s, actual source SHA256 `1b7b3b58948601e81e7dc415167c9ca5e1a06d501eb518d764803aecc35aef77`. Same Qwen camera JSON, same original 12 source pointer samples and same verified edit/result clock. **No changes to browser pixels, capture pipeline, product story, stage chrome or inferred interaction results.**

| Render | SHA256 |
|---|---|
| Old Tabler UI-icon version | `4e6f8bbc173267b95392e97bec05990209c3427f22958f8175439f906c75a766` |
| New genuine Mint SVG theme | **`5510dffedf4f916944ba148b5182c548061afea43ca8ecbe8efa636ca12821c2`** |
| Explicit `--cursor-pack tabler-legacy` re-render | `4e6f8bbc173267b95392e97bec05990209c3427f22958f8175439f906c75a766` — **byte-for-byte exact** |

The actual Mint SVG MP4 was rendered and **FFprobe confirmed H.264 1920×1080, 60fps, 294 frames, 4.9s**; full FFmpeg error-checked decode passed. Opened a multi-timestamp actual decoded MP4 comparison: before pointer at t0.35s the full frame difference was **0.0**. When recorded cursor visible at t1.10, 1.25, 1.35, 3.65, changed connected components were ~28×38 pixels around the recorded cursor; all rest of the product pixels and camera were preserved. The new arrow stays at recorded tip coordinates and is visually clean, with no mouse path invented after the recording stops.

**Owner-only signed review, expires 2026-11-29 20:39:33 UTC:**

[Watch Mint SVG vs rejected Tabler videos and real encoded frame crops](https://devmcp.davemafy.xyz/sauce-expiring-review/tweakcn-20261120/sauce-mint-svg-cursor-39d46d664881bf074d66/index.html?md5=FnXdgLrqW2wOLywDnS5B2g&expires=1795984773)

Signed page, image, video HTTP 200 and video byte-range seek HTTP 206 independently checked. Remote new MP4 SHA256 matched the rendered local file. Chromium playback/seek at desktop **1280×720** and phone **390×844**, **4/4 videos passed** (two versions per viewport), no script errors and no horizontal overflow; phone player ~362×204.

## Important remaining visual failures

**No owner premium-film signoff.** The new pointer looks like a conventional OS arrow rather than UI clip art, but the user has not approved this styling. The Recode video is still a simplistic 4.9s, one-action HTML editor fill; no readable live typing, insufficient source detail on mobile, and original pointer trace has only 12 positions (t0.98–1.35) and then parks over source text. Do not invent cursor paths, artificially animate typing or count a cursor asset swap as a cinematic breakthrough. The next source-true multi-action capture and editorial pass remains necessary.

**Tests:** focused Phase 2 and asset tests **48 passed, 3 skipped, 8 subtests passed**; full Python unittest discover **278 run, 2 skipped, zero failures**. Two encoded videos independently checked; no model API calls, new infrastructure, purchase or public product launch. Keep creative acceptance pending owner review of the rendered film, not test status.
