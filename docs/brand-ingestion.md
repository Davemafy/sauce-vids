# Source-grounded brand-token ingestion

Sauce reads **presentation styles** from the authorized Chromium page at
capture start, after hydration and before the first frame. The immutable
`session.json.brand_tokens` snapshot is the input to later renders. It does
not derive a fake palette from a hostname, refetch page CSS every frame, or
recolor real product footage.

## Accepted sources and priority

1. Computed `:root`/body custom properties such as `--brand-primary`,
   `--primary`, `--color-primary`, `--brand-accent`, `--accent`,
   `--background` and their supported equivalents.
2. Public `<meta name="theme-color">` when no suitable primary variable exists.
3. Visible semantic button and accent-element computed styles, including
   accent-class `stroke` or `color` when there is no explicit token.
   Floating third-party chat/support widgets are excluded.
4. When reliable chromatic colors are absent, the original neutral dark
   stage is preserved; neither page URL nor a hash invents a brand color.

Chromium resolves RGB/HSL/OKLCH/OKLab and display-P3 CSS to bounded sRGB
`#rrggbb` output. Color origins (`css:`, `meta:`, `computed:`, `derived:`,
`fallback:`) are recorded. If only one brand color is observed, its hue
is reused for both dim lights instead of inventing an unrelated accent.

Body and first heading `fontFamily`, `fontWeight`, and `fontSize` are
recorded in bounded strings and numbers. Sauce preserves the genuine
captured typography; the shader does not paint new text or replace fonts.
Only allowlisted style values enter `session.json`. Raw CSS, selectors from
the page, images, form values, and private content are not serialized.

## Render mapping

`CinematicStage` takes validated `brand_primary` and `brand_accent`.
The `_stage_base` LRU cache keys on the backdrop style **and both colors**,
preventing cross-customer palette leakage. `procedural_backdrops.py`
maps those hues into restrained stage-only fluted, chromatic or matte
blooms, normalizing brightness and retaining the dark `#090a0f` floor.
The audio-driven ambient bloom is similarly color-keyed. The original
rounded H60 outer rim receives at most 6% of the captured accent, and
experimental spectral dispersion uses bounded primary/accent weights.
H0 and H60 content pixels are never intentionally recolored.

Old sessions without `brand_tokens`, and captured sessions with
`confidence: fallback`, preserve the previous neutral palette exactly.
The optional brand snapshot is schema-validated in `verify_package` before
replay. The private raster-cache identity includes captured tokens when
present. Stage style and extracted colors never affect FramePlan or 48kHz
FoleyPlan timing.

## Reproducibility and limits

Given the same capture, palette and renderer, stage material generation is
deterministic. General **independent live Chromium replay** is still not
fully deterministic; the experimental canonical-frame-cache limitation
described in `docs/SAUCE_HANDOFF.md` remains. Cross-origin iframes, shadow
DOM and canvas/WebGL-only themes may not expose useful public CSS tokens;
Sauce falls back rather than guessing.

Tests use two independent, local HTML site origins (Cobalt/Copper fixtures),
modern CSS syntaxes, neutral/malformed fallbacks, a real file:// capture
and H0/H60 pixel-isolation checks. The Brimble brand-aware proof is based on
a **separate derivative of the existing verified Brimble HAR**, not a new
independent user-recording session. The original session and old releases
remain unchanged.
