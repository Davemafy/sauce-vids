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
