# Original Sauce cursor styles

These three **original Source-True Sauce SVG treatments** are selectable render-time appearances, not copies of proprietary cursor assets or branding.

| ID | Treatment | Source | Click hotspot |
|---|---|---|---|
| `studio-rounded` | Bold, rounded white desktop arrow with dark contrast outline | `studio-rounded.svg` | SVG (4,4) |
| `gloss-carbon` | Dimensional graphite/carbon face, polished metallic rim | `gloss-carbon.svg` | SVG (4,4) |
| `aero-prism` | Iridescent teal-violet-coral glasslike finish | `aero-prism.svg` | SVG (4,4) |

All share 48 × 56 SVG coordinates, preserve a single pointer tip, and use actual source-timed cursor trajectories. The designs are independently authored for Sauce, influenced by broad stylistic categories in software demo media. **They are not official or extracted assets from Screen Studio, Tight Studio, Figma, or their partners.**

The existing `mint-studio` remains the **production default** until owner visual signoff; its original Colorosse cursor SVG and CC0 license are independently preserved under `assets/cursors/mint-studio/`. `tabler-legacy` is retained for reproducing previously rejected videos only.

To select a cursor for a genuine Sauce film:

```json
{
  "schema": "sauce-film-plan-v1",
  "cursor": "recorded",
  "cursorPack": "gloss-carbon"
}
```

This is a **partial snippet**, not a complete executable plan. A complete plan additionally requires the actual source/manifest SHA256, duration, presentation, verified camera keys and audio mode. To render without a plan-specified cursor, use `scripts/render_event_video.py --cursor-pack aero-prism ...`. A CLI value differing from the film-plan `cursorPack` is rejected rather than silently overriding the film.

The pointer is never recreated if source footage already contains one; source `cursorless` and recorded sample validation still apply. No synthetic pointer, fake clicks, UI, action timestamps or source replacements.
