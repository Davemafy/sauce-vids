# Sauce independent film-critic rejection — Linear 13.17s, 2026-11-19

**Status: REJECTED for premium product-demo positioning.** This is a creative rejection, not a denial of verified engineering or source provenance. Do not promote this film to a flagship, customer example, launch approval or market parity evidence. **Creative rating against the user's Linear/Apple/Screen Studio target: approximately 3/10, editorial judgment, not an instrumented metric.** The older provisional 6.5/10 estimate put too much weight on technical gains.

## Exact rendered artifact and basis

Reviewed the actual MP4 at `/var/www/sauce-motion-phase2/quality-source-director-20261118/master-1080p60.mp4`, public [review page](https://devmcp.davemafy.xyz/sauce-motion-phase2/quality-source-director-20261118/), SHA-256 `9b661e9b0eb0c9cde8b21da95e0d979b4f7e6e8d8ef71e50ccda4ae09fa8e475`, H.264 1920×1080, 60fps, 790 frames/13.166667s. Samples viewed from the actual encoded movie at **0, 1, 2.5, 3.8, 5.8, 7.8, 10.2 and 12.5 seconds**. Not a reconstruction or a proposed storyboard.

Compared separately against the **actual privately retained Screen Studio product-1 reference** at `studio/.tmp/sauce-reference-research/screenstudio-product-1.mp4`, inspected at 0, 1, 2.3, 4, 6.6 and 9.5s. Refs.video's published Loom shot breakdown and the existing `docs/screenstudio-study.md` are conceptual references only, not proof the Sauce film looks like them. Reference footage was not redistributed.

A diagnostic on full decoded samples downsampled to 320×180 grayscale: Sauce first-second frames had mean pixel difference **0.25/255** and **0.0%** of pixels changed by at least 15 levels; the Screen Studio reference's first-second frames had mean difference **68.74/255** and **60.8%** above that threshold. This measures **relative frame activity only, not subjective quality**; static establishing shots can work when the subject itself is compelling. Here the subject is also small/dense, so the inert opening is costly. Sauce's initial grayscale mean ~25.9, with 96.2% below level 40, versus reference ~122.6 and 21.2% respectively; difference in product color palette by itself is not a defect, but low visual separation exacerbates this shot's readability failure.

## Editorial assessment — reasons to reject rather than polish

1. **0–1s opening: fails the hook test.** The film opens on a dark, cramped issue workspace with no dominant object, visible transformation, or instantly comprehensible promise. First-second encoded pixels barely change. A general viewer does not know what to look at or why it matters. Merely starting with the same issue page is not an establishing *shot* if it provides no hierarchy.
2. **~2.5–3.8s Reviews/code diff: strongest action, still improperly staged.** Real color-coded diff is interesting, but the viewer's eye is not clearly carried from a visible input to an obvious outcome. The frame contains dense supporting text and chrome; a camera move alone cannot clarify what changed.
3. **~5.8–7.8s task board: context switch without visual causality.** A different view appears, but the change feels like a tour of screens. Rows of tasks occupy the frame without one obvious hero, reveal or progressing outcome. Cutting to a new page is not automatically an editorial beat.
4. **~10.2–12.5s Agent Insights: the first strong graphic arrives too late.** The actual chart and counters are the strongest visual objects in the available footage, but viewers must wait through a dense issue, diff, and task board before encountering them. The final composition still spreads attention across chart, counters, and table rather than presenting a clear result.
5. **Cursor/motion: technically verified, weak on-screen authority.** Real-source hotspot preservation and zero missing/offscreen frames are good engineering but do not mean the viewer can follow the pointer at phone-feed scale. Camera changes are procedural, not a persuasive demonstration of the product's mechanism.
6. **Aesthetic coherence: lacks a visual protagonist.** The film presents multiple real features instead of a single story. Spatial continuity complications arise because the public preview remounts different UI states in the raw source; this is a source limitation that shaders cannot magically repair. No evidence of a complete customer workflow or independent art-director signoff.

Sound was **not independently auditioned** in this review; no claim is made that the score or Foley sounds good or bad. An AAC track or sample alignment cannot establish the sound's creative effectiveness.

## No more false passes: two separate gates

**Technical gate:** may pass on source provenance, native capture, cursor geometry, no privacy leakage, 1080p60 output, audio sync and regression tests. Never report technical pass as a film pass.

**Film gate:** reject the work unless all are independently evidenced:
- **First frame:** clear dominant visual subject, appropriate scale/contrast and no accidental clutter.
- **First 3 seconds:** a viewer can identify the product's specific value or an unfolding meaningful action; no dead opener. Judge the actual **rendered frames**, not timeline JSON.
- **Single coherent promise:** every shot advances one demonstrable authentic product outcome. A sequence of menu destinations is not a story.
- **Camera is subordinate to meaning:** visible pointer approach, real user action, observed change, camera change follows effect, enough hold to read; no pre-action zoom, source-state ghosting or empty sweeps.
- **Feed-size acceptance:** critical content survives viewing as a ~390px-wide landscape video; if it doesn't, recompose or choose another interaction.
- **Reference comparison:** open both actual source films at corresponding narrative beats; name the specific gap in focal size, pacing, hierarchy, cursor, transitions and payoff. Do not claim 95% match from a checklist.
- **Critical review before expense:** inspect a 3–5-frame storyboard and the first 3 seconds before committing to a full multi-scene render; after **two failed visual iterations**, stop and reconsider source/workflow rather than polishing more effects.
- **Explicit owner acceptance:** human approval is distinct from critic acceptance, and both are distinct from passing CI.

## Corrective creative brief

Do **not** try another micro-polish of this exact Linear preview merely to raise a numeric grade. It has several real UI states, but they are separated by source remount gaps and the link between them is weak. Select a stronger **continuous** real workflow with an intrinsically visual transformation: e.g., dragging, editing or publishing a design in an authorized product, or a genuine UI action whose before/after is obvious on screen. Keep the true interface intact and obey rights/access. Obtain a DPR2 native source and a **three-shot picture-led board**: (1) real hero state/promise, (2) visible action, (3) satisfying verified changed result. Prefer 5–8 seconds of excellent material over 13 seconds of dull screens.

The next milestone is **an independently criticized first 3 seconds that earns a visual GO**, not another feature, extra test suite, bigger 4K render, paid inference call or self-declared cinematic completion. Preserve all historical source assets and rejected outputs for evidence; make no destructive changes to production.
