# CMOkit public-URL film — actual encoded quality failure, 2026-11-18

**Creative status: FAIL. Do not present this as a premium UI product demonstration.**
This document describes evidence from an already-produced private, user-initiated Sauce Studio URL job for `https://cmokit.co/`. No new Gemini request, paid service, submission or customer action was performed.

## The real 30-second artifact

Retrieved its private on-worker capture/scene/encoded receipts, probed the actual H.264 MP4, fully decoded it with FFmpeg, opened a 12-frame contact sheet spanning the entire video, and inspected the public site live in Chromium at seven scroll positions. The Studio screenshot supplied by the owner shows the resulting review/download card, **not proof of premium film quality**.

- Exact pipeline was `backend/story_arc_pipeline.py` → `scripts/story_arc_capture.py` → `backend/story_arc_render.py` in a **dirty, uncommitted production checkout**. These modules are **not on current GitHub main**; the main checkout has separate motion and event-video tooling. They must be reconciled deliberately, never overwritten by resetting production.
- Actual master: **30 seconds, 1800 frames, 1920×1080 H.264/60fps**. Source: Chromium **1280×720 VP9/WebM about 25fps**, resized and temporally resampled. The final fps does not mean 60 distinct genuine source fps. Full FFmpeg decode passed.
- Four AI-directed scenes: hero/landing pitch, 'How it works' navigation, 'Brief your CMO' instruction heading, 'Pricing' navigation. Two clicks were real, but both were same-document **navbar anchor links**, not product operations. There were **zero verified H60 elevated states**. The compositor drew 414 kinetic-callout frames over ordinary page content.
- Scene two's camera target rectangle was **82×21.59px at y≈21px**, the navbar link. Scene four was **44×21.59px at y≈21px**, another navbar link. The scene-three text target was only **230.66×22.39px**. Following these narrow targets while the page scrolls creates badly cropped website typography and shots without meaningful payoff.
- At ~0–7.5s the film shows largely the same small hero with generic callout. Around 9.5s it pushes awkwardly into the 'How it works' part of the page and cuts typography; through ~15–22s it holds on static instructional cards with a weak view of the example terminal. The last section shows pricing. There is no observable execution of the product's claimed 56-agent CMO workflow.
- The source website actually contains stronger original editorial sections: cost comparison, 'Every floor of a growth team', 'Your next customer asks ChatGPT', and 'You type one line. A launch happens'. The auto director largely ignores these regions. The two owner's screenshots show **different sections** of the site; they are not pixel-equivalent before/after frames.

## Tested source-evidence admission guard

`backend/url_film_quality.py` is a conservative, **currently non-wired** quality admission function. It distinguishes verified controls from same-document link clicks, identifies undersized focus rectangles, flags a long non-action opening, and reports source-resolution/frame-rate provenance. It does not score film craft or create new pixels. Dedicated tests: six passing. Applied to this *actual* stored CMOkit inspection and capture metadata:

- `eligible_product_demo=false`
- `navigation_only=true`
- `actual_product_action_candidates=0`
- `bad_camera_targets=3`
- `opener_seconds=7.51562`
- `source_is_native_master=false`, `source_is_native_fps=false`

This is a **diagnostic regression**, not a fix to the live customer path. Never claim the production app uses it until that integration has been committed/deployed and observed.

## Next strictly scoped live-render corrections

1. **Reconcile the running StoryArc modules into versioned main safely.** They are still untracked in a dirty production checkout. Preserve and back up all existing source/private artifacts before any integration. No reset or surprise deploy.
2. **Before any AI direction request**, classify the inspected URL. A site exposing only anchor navigation supports an honest *public website showcase*, not a verified functional product demonstration. No 'interactive app demo' or unsupported value claims.
3. **After a real same-document navigation**, wait for scrolling to settle and target the actual destination section's visible headline/result region, not the clicked 44–82px navigation link. Validate the source-derived rectangle in screen coordinates and reject clipping. Keep one real cursor.
4. First storyboard the opening **three seconds** with native source frames and deliberate selected shots. Avoid the seven-second inert hero, user-written generic callouts, tight text crops, neutral gray fallback, and repetitive wide cuts. Compare with real premium reference shot geometry.
5. Only after human review of that low-cost opening should any longer 16:9 master be rendered. The goal is source-true cinema, not prettier static screenshots or another green test run.

No additional 30-second render was executed during this audit. No unfinished film was publicly published.
