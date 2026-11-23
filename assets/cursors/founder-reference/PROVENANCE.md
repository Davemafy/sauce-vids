# Founder reference pointer set

This set is based on frame-by-frame inspection of three **owner-supplied** cursor reference videos on 2026-11-23. The raw reference footage is not committed.

- Clip 1 (4.933s, 1280×720/30): compact filled black arrow, low visual noise.
- Clip 2 (5.550s, 1920×1080/60): black arrow and an explicitly white hand pointer with a robust black rim over an actionable Google Sheets menu.
- Clip 3 (4.650s, 1920×1080/60): black arrow with a bright white rim. The big circle is a separate glass-loupe camera effect; the small white circle under the pointer is the site's genuine slider handle, NOT a generic cursor click indicator.

Original Sauce black arrow vector is a new design informed by the **visual qualities** of these refs, not a pixel trace/copy. The hand and text-pointer shapes are **adaptations of Colorosse Mint Cursors (CC0-1.0)** and have their own exact documented hotspots. Original source: https://www.colorosse.com/assets/2d/ui/mint-cursors. Original CC0 permission: https://creativecommons.org/publicdomain/zero/1.0/.

Recorded pointer positions, CSS cursor semantics, and actual click events must control appearance and effects. A hand must never be inferred merely because a site has a nearby button. The white slider thumb is original browser UI and should not be re-created as a synthetic click dot. Creative SVG styles under `assets/cursors/sauce-styles` are separate opt-in treatments, not a default replacement for normal pointer semantics.
