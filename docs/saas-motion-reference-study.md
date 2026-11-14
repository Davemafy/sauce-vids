# Sauce: SaaS film reference study and camera quality gate

Date: 2026-11-14
Status: researched; not an acceptance pass or completed implementation.

## Actual videos inspected on Vultr

The following source clips were played by sampling frames through FFmpeg and reviewing filmstrips. They are retained ONLY in ignored local research workspace, NOT republished:

| Reference | Source | Clip inspected | Observation |
|---|---|---|---|
| Screen Studio product demo | https://screen.studio/create/product-demo-videos | `screenstudio-product-1.mp4` 10.37 sec at 60fps | Zoom into a single consequential action, hold while it is read, zoom back out. |
| Screen Studio product editor | same URL | `screenstudio-product-3.mp4` 16.87 sec at 60fps | Explicit zoom regions on timeline, not constant camera wandering. |
| A real Screen Studio-made coding demo | same URL | `screenstudio-madedemo-1.mp4` 23.15 sec at 60fps | A long stable close-up over editing activity; release to overview late in the clip. |
| Screen Studio 4 home-page hero | https://screen.studio/4 | `screenstudio-hero.mp4` 5.55 sec, approximately 60fps | Zoom begins in advance of format selection; remains focused while menus open; exits cleanly. |

Actual files and contact sheets are at `studio/.tmp/sauce-reference-research/` in the VM. **No copying these third-party clips into Sauce's public assets.**

Additional references whose analysis was read (not directly video-downloaded):
- Linear for Agents 2025 (32 sec) https://launchscene.app/v/linear-for-agents?play=1 : product immediately, deliberate actions, clean staging, edits when useful
- Linear Agent 2026 (54 sec) https://launchscene.app/v/linear-agent?play=1 : 3D editorial presentation with prolonged static holds, one feature, focus racking. This is not default automation behavior.
- Screen Studio official guides:
  - https://screen.studio/guide/auto-zoom
  - https://screen.studio/guide/adding-editing-zooms
  - https://screen.studio/guide/animations
  - https://screen.studio/guide/cursor

## Where our previous 34.5-second Kiva film fails

**Reject it as the visual standard**, despite verified 60fps playback:
1. SaaS choice failed taste selection. Kiva demo has high visual density, tiny content, crowded controls; accessibility does not justify using it as a premium hero film.
2. Browser frame was a handcrafted approximation instead of an established frame component.
3. Hard-coded timestamp cues tracked script decisions, NOT actions; camera behavior could be physically smooth and still be editorially wrong.
4. Product interactions take too long and are buried under controls; a task dialog becomes a shot just because it opens.
5. Hover/click coordinates were burned into the capture, with no separate pointer track, so we cannot suppress cursor changes, size or smooth it independently.
6. Too many camera moves. Watching the zoom should not become the task.
7. A photographic background does not improve product typography, UI hierarchy or feature choice.

## Frame selection (reuse, not reinvent)

Chosen for next evaluation:
- `btahir/shotcandy` commit `15fa803`, **MIT**. Existing `brand/frames/macos-dark.svg` and `brand/frames/browser-dark.svg` plus documented video framing. Source: https://github.com/btahir/shotcandy ; https://shotcandy.app/macos-window-frame/
- This is a reusable *frame design*, not an endorsement of wholesale application integration. Reuse with MIT notice and validate real input pixels, aspect ratio and border behavior.
- BrowserFrame https://browserframe.com/ is another visual reference for Chrome, Safari, Firefox and macOS-style frames, but its public site is primarily a screenshot wrapper. Do not assume its video output can be integrated.
- If capturing a native Mac app, use a macOS window frame; if a web SaaS with recognizable URL, use browser frame. Avoid a bar that falsely claims an app was opened in a browser.
- Prefer a restrained plain environment when content is weak. **Background must not become the visual subject.**

## Camera architecture to implement (replaces the hard-coded shot list)

Capture sidecar (60fps source; same monotonic clock):
`{timestamp, cursorXY, pointerShape, action, mouseButton, targetRect, role, textEditing, scroll, scrollContainer, viewport, focusChange}`.
Instrument Playwright actions and DOM targets. Also log pointer shape/position where possible. Reconstructed sidecars are NOT equivalent to capturing original events.

Auto shot planner:
- Trigger: meaningful click, committed input, menu opening, modal opening, state change or pointer dwell at a specific action. Suppress toolbars/irrelevant navigation.
- Cluster nearby actions in time/space. Once zoomed, **stay zoomed** while the interaction continues and pan minimally within the framed area. Do not zoom out/in between two related clicks.
- Begin camera anticipation before the triggering action using recorded events from the completed capture.
- Zoom to the bounding box plus context, not blindly to the pointer center. Prevent clipping menus, dropdowns, selections, text labels, cursor and important app chrome.
- Dead zone: cursor can move within the focused area without moving the camera. Reframe only if action leaves it.
- Hold: stop moving entirely when content needs to be read. Transition only on a new meaningful focus or break in the story.
- Return to overview when a multi-step action is complete or a wider relationship is revealed. Never because a timer expired.
- If the event analysis lacks sufficient confidence: **no zoom**. A clean locked shot wins over an invented push-in.
- Separate motion channels: screen translation, zoom depth, cursor position, click signal, and optional pointer hide. Use continuous / deterministic interpolation and fractional positioning.

Suggested initial engineering tuning **for experiments only, not alleged Screen Studio parameter values**:
- Target zoom 1.25–1.55x typical, >1.6x only when text needs it.
- Anticipation 0.3–0.6 sec; settle 0.5–0.9 sec.
- Hold through entire action plus at least 0.5 sec of readable state.
- Dead zone occupying about a quarter of the *zoomed view*; avoid following every minor cursor motion.
- Optical motion blur only while actual camera velocity > threshold; never blur text during a static hold.
- Stable app window and wallpaper (if used), zoom the UI layer **inside** it. No heavy vignette by default.

## Visual quality gate

A 12–15 second single-action test, before any 30-second marketing film:
1. Use a high-quality SaaS with permission/legitimate demo access; no fake UI and no choosing ugly apps merely because they are easy to automate.
2. Show overview → natural cursor approach → anticipatory zoom → action → readable hold → release.
3. Maintain feature legibility at Android 390x844 physical phone viewing.
4. No unexpected zoom, no zoom chasing the cursor, no repeated zoom-out/zoom-in for related actions.
5. No browser-frame reconstruction; use a vetted existing library with its license.
6. Record a pointer/click/DOM event sidecar and generate the camera timeline *from the sidecar*.
7. Render output at stable 60fps and verify frame pacing and decoding, but **do not treat FPS/4K/5K as a proxy for taste**.
8. Human compare side by side against Screen Studio clips; reject if the motion still draws attention to itself.
9. Output only after passing. If the only accessible SaaS demo looks poor or requires fake interactions, change subject rather than lowering the bar.

**Milestone:** build one truthful, event-driven auto-zoom on a genuinely good SaaS interface, not a new full film.
