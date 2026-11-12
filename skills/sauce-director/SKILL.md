---
name: sauce-director
description: Direct truthful browser-based product demos with Sauce Vids.
---

# Sauce Director v0.2

Hermes chooses the story and edits. Sauce Vids gives it real observations, browser capture, an editable EDL and film inspection.

1. Check the user's URL and ensure they authorize recording the public site. Ask about preferred aspect ratio/duration only when needed.
2. Call sauce_scout first; use observed page sections, screenshot files, and verified selectors to choose what to demonstrate.
3. Call sauce_capture with safe observed actions. Only click actual anchor links or role=tab controls. Never enter credentials, submit forms, purchase, delete, or simulate nonexistent results. Use expected_visible_heading for SPAs.
4. Review capture timestamps and (if image playback is available) look at the real recording. Call sauce_plan with a simple chronological edit decision list based on what actually appeared. Keep zoom between 1.0x and 1.45x to maintain readability.
5. Call sauce_render with use_edit_plan=true. It composes cuts/zooms and can add user-provided licensed music and background assets from SAUCE_ASSET_DIR. Do not invent decorative UI, logos, or artwork.
6. Call sauce_review and inspect the extracted video frames with available vision tools. Check title/feature visibility, blank sections, dead time and obvious visual flaws. If quality is poor, revise the plan and render again.
7. Call sauce_inspect for exact output duration, provenance and media metadata. Return the MP4 file path, edit-plan path, and available review evidence.

A public website or marketing simulator is not an authenticated agent execution. Do not claim that a feature was performed unless the capture log and frames support it. Do not pretend that metadata inspection constitutes aesthetic review.
