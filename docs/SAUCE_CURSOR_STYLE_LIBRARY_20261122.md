# Sauce Phase 2 — selectable cinematic cursor styles (2026-11-22)

**User requirement:** “Why not use all?” regarding the recognizable rounded / glossy / playful pointers seen in founder demos. Previous one-size-fits-all replacement of a malformed cursor with a Tabler UI icon, then a neutral Mint CC0 arrow, never established the user's preferred visual style.

**Decision:** Support multiple true vector **appearance presets per film**, without layering multiple cursors onto the same shot, borrowing proprietary cursor artwork, altering source pixels or fabricating movement. Keep `mint-studio` as the default until explicit owner preference. No website UI redesign or production model switch.

## Assets and semantics

Three original 48×56 SVG arrows stored as actual editable vector source in `assets/cursors/sauce-styles/`:
- **`studio-rounded`:** high-contrast, rounded white pointer with restrained dark keyline and shadow. Familiar studio recorder category, not Screen Studio artwork.
- **`gloss-carbon`:** polished graphite/chrome with dimensional reflected face; a glossy category, not Tight Studio artwork.
- **`aero-prism`:** restrained iridescent teal/violet/coral pointer; playful category, not a Figma-provided asset.

The previously verified commercial-reusable **Colorosse Mint CC0** original remains `mint-studio` with its separate upstream provenance. The rejected Tabler UI-icon version remains **explicit-only** `tabler-legacy` for reproduction. Original Sauce artwork is independent; no vendor affiliation, trademark or claim of exact reproduction.

Every original SVG has native viewBox 48×56, title with `hotspot 4,4` and a single arrow shape. The compositor uses CairoSVG at 4× output resolution and Lanczos downsample to genuine 1080p cursor sizes (~40×47px tile; ~30×41px painted foreground), preserving a **single recorded click tip and source-timed trajectory**. Pixel source coordinates, verified manifest, product action timing and camera movement do not change. No extra fly-in, glow halo obscuring product UI or fake click feedback.

## Engine integration

- `scripts/recorded_pointer.py`: expands `CURSOR_PACKS` to `mint-studio`, `studio-rounded`, `gloss-carbon`, `aero-prism`, `tabler-legacy`; cached `_sauce_style_sprite` loads exact vector assets, validates their original dimensions and hotspot, and scales correct click origin; every draw/project path can select style. No live download at render time.
- `scripts/render_event_video.py`: `--cursor-pack` accepts all styles, default remains **Mint**. User-selected style propagates through the actual MP4 compositor's fullscreen, staged and 3D pointer paths; no client-side CSS trick. When `--film-plan` is present, an optional `cursorPack` field is authoritative; mismatched CLI override fails closed.
- `scripts/film_plan.py`: adds optional `cursorPack` on existing `sauce-film-plan-v1`, resolves only the verified allowlist, rejects unknown names and styling a cursor that does not exist; optional `FilmPlan.cursor_pack` persists it. Source and manifest SHA256, verified camera anchors, motion-speed gates and recorded-cursor requirements remain intact.
- `tests/phase2/test_recorded_pointer.py` and `tests/phase2/test_json_film_plan.py`: validate exact independent supersampled raster against the SVG, original click hotspot, genuinely different authored assets, exact source projection, default and alternate selections, fail closed on invalid styles and absent pointer. Regression tests for unchanged Mint and explicitly selected Tabler continue passing.

## Actual encoded video proof

All four MP4s use the **same genuinely captured Recode 4.900s 1920×1080/60fps, 294-frame source**, with a verified local HTML editor→iframe heading change and identical Qwen film camera JSON. Source SHA256: `1b7b3b58948601e81e7dc415167c9ca5e1a06d501eb518d764803aecc35aef77`. The only changed pixels are source-anchored cursor styling. At actual encoded t0.35 before the recorded pointer, all style frames are **pixel-identical**; at t1.25, distinct cursor-shape changes are contained in 30×41 to 32×43px connected-component clusters near the identical recorded hotspot (x≈859,y≈387). At full-size 1920×1080 and on the 366px phone-size playback, cursors remain proportionate, not giant effect stickers. The same one weak original product action and poor phone text readability remain.

| Selected cursor | Encoded H.264 1080p/60fps file SHA256 |
|---|---|
| Mint CC0 original | `5510dffedf4f916944ba148b5182c548061afea43ca8ecbe8efa636ca12821c2` |
| Studio Rounded original | `6d9f6716555cf8cf357c963c93df6912fc1357bf1de8e32f06578c58f06652d6` |
| Gloss Carbon original | `1927e82297e3b1748d4048ed65b46741645e534eb92070dfb0b2ceb32b741163` |
| Aero Prism original | `a8278c8163a3281b66e7c0af5610d5e155d78fe9bd7ef8c4843c27b875410a95` |

All **4/4** individually verified via FFprobe **H.264, 1920×1080, 60fps, 294 frames, 4.900s**, full FFmpeg `-xerror` decode PASS. The enlarged actual encoded-film frame comparison was **opened and inspected**, with no replacement or staged screenshots. The user can change the cursor style for the same authentic video using the private review page's accessible four-option selector.

**Owner-only review** (expires **2026-11-29 20:54:07 UTC**): [Choose the four real cursor MP4s](https://devmcp.davemafy.xyz/sauce-expiring-review/tweakcn-20261120/sauce-multi-cursor-library-b0f885ae5b17c8a15164/index.html?md5=CZroIhF0Grp5jaTWaxa6ag&expires=1795985647).

The signed page returned HTTP 200; MP4 supports HTTP 206 byte-range seeking. Real Chromium desktop 1280×720 and phone 390×844 tests clicked **all four styles**; 8/8 variants loaded, played and sought without page errors, with one selected button at a time, correct natural 1920×1080 stream, correct viewport sizing and no horizontal overflow. Private capture, HAR, credentials, provider logs and user-specific material stayed off public hosting and GitHub.

## Tests and actual creative acceptance

Focused `pytest`: **51 passed, 3 skipped, 8 subtests passed**; broader `unittest`: **278 tests run, 2 skipped, zero failures** on the inherited main tree plus local candidate. The existing unused/public filming systems were not rebuilt, and no model API inference was needed.

**Creative status: NOT APPROVED.** All cursors are options, not automatically “premium” or the exact founder reference the user had in mind. In the underlying Recode film the source pointer still stops moving after ~1.35s, then parks on source code; product result remains weak and unreadable at phone size. The style library solves **choice**, not missing genuine product action, motion choreography or story. Next step after owner style review is better source-true multi-action capture and verified film-direction, not further cosmetic swaps.
