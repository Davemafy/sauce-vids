# Sauce standards — visual direction and engineering acceptance

**Product claim:** *A screen recording is not a demo.* Sauce should create a film that makes the real software easier and more compelling to understand. This document is an acceptance contract for any future agent or new ChatGPT conversation, not a list of default decoration effects.

## Priority order

1. **Truth:** every product state, click, modal, copy confirmation and result comes from a genuine captured/authorized interaction. No fictional UI, fake success, or unsupported feature claims.
2. **Readability:** the viewer must understand the product in the first seconds, see the real action, and have enough time to read the result. Never sacrifice legibility for effects.
3. **Direction:** make deliberate choices about framing, holds, transitions, cursor, and timing. If effects do not communicate action, remove them.
4. **Craft:** considered typography, native source colors, margins, corner radii, soft light, coherent spatial placement, meaningful sound.
5. **Technical quality:** verified deterministic output, source fidelity, frame and audio correctness, reproducible tests, playable delivery.

## Creative decisions that MUST survive a new conversation

- **Landscape first:** the flagship Sauce product film and studio demos are 16:9 by default. Do not auto-convert the task to Shorts, portrait or 9:16. Portrait is a separate intentionally composed cut when requested.
- **Reference-driven, not template-driven:** study a real premium demo frame by frame before rebuilding technique. Use `docs/screenstudio-study.md` and the user's actual references; do not falsely claim affiliation or reuse copyrighted footage.
- **Do not design over the product:** preserve the real source interface, source aspect ratio and recognizable interaction. No generic app-card mockups standing in for a recording. Do not obscure the product with oversized pills, desktop wallpaper, bezels or big labels.
- **Motion grammar:** visible pointer approach → actual click/contact feedback → observed UI change → purposeful camera push/pan → readable hold → release. Do not zoom into a location before the cursor or interaction establishes the viewer's focus. Continuous cursor chasing is not cinema either.
- **Cursor:** one cursor only, always visible during relevant actions, ordinary premium pointer semantics, rounded geometry and precise hotspot. User explicitly rejected giant cursors and wrong pointer angle. Previous small v16 pointer (~32 × 39px at 1080p, film scale 0.56) is a *size baseline*, not a final claim of perfect shape; judge against each composition and references.
- **Composition:** window fits within the stage with real margins and rounded outer edges; no accidental edge-to-edge landscape embed. Soft occlusion shadows and ambient light are permitted when they enhance depth. No excessive neon glow or gradient blobs as automatic decoration.
- **Typography:** choose intentional premium type, hierarchy and whitespace. No uppercase eyebrow/section metadata, redundant "real interface" claims, banner headlines repeating the product UI, oversized captions, or generic AI-marketing copy. Captions must breathe, fit safe areas and correspond to actual narration.
- **Callouts:** rare and high-intent, grounded in trace metadata, attached to the actual projected target. Default cooldown 2500ms; maximum lifetime 1800ms. Use an anchor dot/leader when useful, never crowd real UI.
- **Sound:** event-locked Foley and ducking at the output clock, low enough not to mask narration. Respect mute; never add unwanted music, invented copy confirmations or unauthorized samples.
- **No generic "AI slop":** redesign choices must be argued by the specific site, motion reference and desired audience action, not by stock gradients/glassmorphism/glowing cursors or overproduced effects.

## Required quality gates (all must pass)

### 1 — Source and editorial
- Can we identify the source URL/capture, real sequence and exact outcome? Never conflate a public preview with authenticated app use.
- Does the opening immediately reveal the product and story? Do shots deliver a beginning, useful action and visible result?
- Does every zoom, callout, tilt, sound or transition improve comprehension? Remove effects with no explanatory function.
- Is there an actual comparison against relevant reference frames? Record differences that remain.

### 2 — Visual film review, not only automated tests
- Render a review contact sheet **and** full-resolution frames at: first impression, pointer approach, click, modal/result, final hold. Open the images; don't just report filenames.
- Check full-size UI legibility and how long the viewer can read text. Look for clipped content, crushed blacks, flat roads/backgrounds, misaligned drop shadows, floating elements, wrong fonts, accidental jagged edges.
- Check correct pointer proportions, tip alignment, click feedback, camera sequencing and absence of unintended early zoom.
- Review player screenshots and actual playback at desktop 1280×720 and phone 390×844. If distributing for mobile as portrait, render a native 9:16 cut; CSS cannot make a landscape MP4 full-screen portrait.
- For each flaw, fix and rerender; don't cover it with more overlays. A working renderer or green CI is not a visual signoff.

### 3 — Video/audio/export
- Verify browser source at DPR ≥2 when using the cinematic pipeline; don't upscale poor source resolution and call it 1080p fidelity.
- Inspect real file streams with `ffprobe`, full-decode using FFmpeg. Prefer 1920×1080/60fps master, correct 16:9 framing, Lanczos downscaled preview where applicable.
- Verify event action windows and monotonic time map; after time-warp, Foley must align to **output samples at 48kHz**, within one 60fps frame of the visual event. Confirm mute and peak ceiling.
- With pinned input, prove repeatability via source/capture hashes and decoded-frame comparison; distinguish that from general live-web determinism.
- Check responsive controls, tap targets, video playback, no overflow, safe crop and browser errors.

### 4 — Safety and delivery
- No HAR, screenshot archives, credentials or private session traces in public output.
- No speculative promises or unverified "production ready" claims. Label a 3-second technique proof as a technique proof, not a launch film.
- No branch overhead unless requested; work against current `main`, preserving unrelated changes.
- Commit scoped source/tests/docs. Include a concrete proof link, tests run, what was visually inspected and what remains unacceptable.

**Decision rule:** *If a viewer would scroll away at first glance, the film is not done even if all tests pass.* If a technique fails reference comparison, revise the technique rather than accumulating CSS layers.
