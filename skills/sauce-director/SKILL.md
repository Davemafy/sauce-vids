---
name: sauce-director
description: Create authentic SaaS demo videos from real browser interactions.
---

# Sauce Director — autonomous first cut

The one-call path is sauce_auto({url, project, duration_seconds}).
It performs scout → section selection → capture → timestamped edit plan →
camera push → FFmpeg render → objective QA and returns an actual 1080p MP4.

For improved editorial quality, Hermes should inspect the actual scout
screenshots and extracted review frames. Inspect edit-plan.json and capture
receipts; never infer authenticated outcomes from marketing screenshots.
Identify bad framing, tiny UI, blank segments, weak pacing and false claims.
Use sauce_plan to refine clips using OBSERVED timestamps, rerender with
sauce_render(use_edit_plan=true), then run sauce_review again.

Only use licensed assets supplied by the operator. Do not create decorative
overlays, watermarks, gradients or fake product UI.

Focus actions only scroll to observed headings. Tabs must be real role=tab
controls, and links must be approved same-host anchors. Never enter credentials,
submit destructive forms, purchase, delete or make claims not grounded in
recordings. Objective QA does not substitute for visual aesthetic inspection.


## Studio production mode

The final film's look belongs to Hermes, not `sauce_auto`. After a real
`sauce_capture` + `sauce_render`, Hermes should choose a versioned
`StudioProject` based on observed footage and user-provided visual references.
Use `studio/examples/brimble-first-scene.json` for the schema shape; do not
impose its look on other products. Current valid Studio projects have one
static floating-browser scene only (1920×1080, 30fps); the backend rejects
moving-window camera keyframes and multi-window scenes.

1. Choose a real browser title and the **same** domain found in the capture
   receipt, with a composition background and safe margins. Never invent app UI.
2. Call `sauce_compose({run_id,project,music_asset?,background_asset?})`.
   Requested music/background files must exist in the configured licensed-assets
   folder; Sauce stages source footage from the verified run.
3. Call `sauce_preview({run_id,time_s})` at multiple points; visually inspect
   the actual PNG files with an available image/view tool. Identify text too
   small for mobile, clipped UI, bad whitespace, distracting crop or weak depth.
4. Revise and call `sauce_compose` and `sauce_preview` again if needed.
5. Call `sauce_render_project({run_id})` for the actual 1080p film. Verify
   the MP4/receipt and return paths. Do not call it professional-looking
   unless the film was actually reviewed.
6. Do not claim authenticated product interaction when the only evidence is
   the public marketing site.

Full Remotion frame-by-frame video exceeded the Vultr worker's 1 GiB memory
limit. This slice composes the stage with Remotion and composites genuine
footage/audio with FFmpeg, one operation at a time.


## Non-negotiable visual integrity (v0.5)

Treat fidelity as an engine invariant, not a creative preference. Do not pass
old 25fps/1440x900 footage through the 720p editor and label it 1080p.
The capture tool now verifies real 30fps native footage before declaring
success. Studio may reject a source if rendering would enlarge its pixels.
Never invent a pointer, browser UI, product outcome or accessibility claim.
If a product's own UI is too dense to remain legible in a floating frame,
tell Hermes to request a tighter *real-footage* crop/fullscreen shot; do not
fabricate or repaint the application. Current static Studio does not yet
support those advanced shots and must not silently pretend otherwise.
