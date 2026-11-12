# Sauce Vids v0.4 — Production Studio

Status: implementation specification. This document is not a claim that the compositor has been built.

## Product boundary

**Hermes owns judgment:** product understanding, story selection, browse plans, composition and music choices, pacing, review and revision.

**Sauce owns execution:** capture real product behavior, expose safe observations and measured interaction coordinates, assemble deterministic scenes according to a plan, render video and inspect measurable technical failures.

No second creative LLM, standalone editing dashboard, synthetic product UI, or style chosen by Sauce without Hermes input. Keep existing `sauce_auto` only as a low-level baseline/smoke-test and don't mistake it for Hermes-directed filmmaking.

## Visual bar

User-provided reference images (2026-11-12): Dia floating browser over ambient background, Screen Studio camera/wallpaper/timeline controls, framed Figma canvas with selected wallpaper, Dia multi-pane browser composition.

Extract capabilities, not copyrighted look-and-feel or trademarked browser interfaces:

- Authentic screen content remains primary and readable on a phone.
- Float one or two browser/product windows on an intentionally selected image/video/color field.
- Carefully tuned padding, shadows, corner treatment and optional real browser chrome; no fake app screens.
- Animated camera trajectories (time + scale + position + easing); small, purposeful moves and bounded crop.
- Cursor trajectories and click/typing indicators tied to real recorded events.
- Music volume, fades, scene transitions and optional licensed SFX; narration only if asked.
- No mandatory watermark, logo, generic glass layer, randomized gradient or sensational text overlay.

## Existing baseline

`sauce_scout`, `sauce_capture`, `sauce_plan`, `sauce_render`, `sauce_review`, `sauce_inspect` already exist. `sauce_auto` creates an algorithmic first cut, **not a creative agent**. Live Brimble public marketing-page capture, 1080p media render, licensed audio and frame extraction have been verified on the isolated Vultr worker; this does **not** establish authenticated product footage or a Hermes-run autonomous agent session.

Avoid breaking these paths. Keep `main` as sole development branch; do not update the challenge catalog SHA until the improved engine is verified.

## Implementation slices

### 1. Reusable Remotion compositor

Use Remotion and adapt appropriate MIT-licensed components from `Third-Space-interactive/screen-demo` (preserve attribution/license). Keep Playwright as source-footage recorder and FFmpeg/ffprobe as media preparation/verification tools.

First renderable scene `FloatingBrowser`:
- Canvas 1920×1080, 30 fps, with output aspect ratio explicit.
- Background: asset filename, solid color, or explicitly chosen video; no unsolicited visual treatment.
- Stage: one recorded video, draggable-by-data window placement, radius/shadow, safe viewport margin, optional chrome.
- Camera: frame-based interpolation of scale/pan; target specified by Hermes; hold -> move -> hold, with ease.
- Audio: licensed soundtrack filename, start/trim, volume and fades.

Second scene `MultiWindow`: two independent recordings/window layers with reveal timing and controlled transitions, not simulated panes within a recording.

Reuse existing real recording WebM and edit-plan.json. Preserve a provenance record linking each footage layer to its source run.

### 2. Versioned edit-project contract

Create a schema and example `project.json`, validated before any render. Suggested conceptual structure:

```json
{
  "schema_version": "1",
  "canvas": {"width": 1920, "height": 1080, "fps": 30, "duration_frames": 600},
  "background": {"kind": "asset", "asset_id": "approved-wallpaper"},
  "scenes": [
    {
      "id": "hero",
      "start_frame": 0,
      "duration_frames": 180,
      "layout": "floating-browser",
      "windows": [{"recording_id": "brimble-run", "in_frame": 0, "x": 0.14, "y": 0.12, "w": 0.72}],
      "camera": [{"frame": 0, "scale": 1}, {"frame": 90, "scale": 1.12, "focus_x": 0.5, "focus_y": 0.45}],
      "audio_cues": []
    }
  ],
  "audio": {"licensed_asset_id": "digital-clouds", "gain": 0.20}
}
```

This is illustrative until implemented. Actual schema must define units, bounds, timeline alignment, media IDs and easing. `asset_id` resolves **only** to operator-approved files; never accept arbitrary remote media URLs or untrusted filesystem paths from an agent.

### 3. Tool surface for Hermes

Keep discovery/capture tools. Add only production primitives:
- `sauce_compose`: validate and save Hermes-authored scene project; return warnings and project ID.
- `sauce_preview`: render selected frames or a short low-res sequence for Hermes's actual visual inspection.
- `sauce_render_project`: deterministic final render (MP4, optional 4K) and source/edit receipts.

Retain `sauce_review` for objective checks. Hermes—not a custom hidden decision loop in Sauce—reads the preview images and revises project JSON. Agent runs should be logged with the tool calls and final render ID.

### 4. Honest end-to-end agent acceptance

Single Hermes request on a real authorized site:
"Create a polished 20-second demo of this product from real interactions."

Proof package must contain:
- Hermes tool-call trace with no manual shot selection.
- Real scout observations, selected browser actions and recording(s).
- Versioned scene project with chosen wallpaper/music licenses.
- Preview frames, Hermes critique, at least one meaningful revision.
- Final 1920×1080 MP4 with audio if licensed asset was selected.
- Inspection receipt (duration, dimensions, black-frame segments, crop/readability review).
- Original recordings and source provenance.

For Brimble, public marketing illustrations must **never** be described as real authenticated agent actions. Test authenticated UI only with permission and temporary test credentials outside chat.

## Visual acceptance gates

1. Side-by-side with the four user-provided screenshots: coherent selected background, floating window depth, clear visual hierarchy; no template-looking filler.
2. At least three intentional scenes; identifiable beginning, demonstration and end rather than an unbroken scroll.
3. Headings and important UI remain readable at mobile playback size; no text off-canvas; action focus inside crop.
4. Camera stays settled long enough to understand the product; no gratuitous zoom oscillation.
5. Track source-license evidence; never bundle assets with uncertain redistribution rights.
6. Real output passes technical inspection and visual inspection **by looking at frames**, not just metadata.
7. Prototype verified on existing Vultr worker without touching Refit. Render with concurrency 1 initially; measure memory/CPU and only change worker limits if justified.

## Implementation order and stop conditions

A. Single polished floating-browser scene from existing Brimble capture and a licensed selected wallpaper. Stop until a real MP4 and inspection frames match the visual bar.

B. Multi-window composition, timeline camera/cursor, transitions, audio. Stop until at least two substantially different shots are convincing.

C. Expose versioned project tools to Hermes; require a real Hermes-directed capture-preview-revise-final run. Stop if orchestration was actually manual.

D. Verify on three product classes: public marketing site (honest claims), functional SaaS UI (authorized), mobile viewport. Then design distribution/hosting based on adoption.

Do **not** launch a general SaaS editor or a startup around creative decision making at this stage.

## Dependencies/licensing

- Screen-demo source: https://github.com/Third-Space-interactive/screen-demo (MIT; retain copyright notices).
- Remotion official docs: https://www.remotion.dev/docs and https://www.remotion.dev/pricing. Check free-license eligibility before commercial multi-user automation.
- Assets must have per-file license provenance. Mixkit music used in internal Brimble prototype, but do not assume all Mixkit/Figma/Envato media are freely redistributable.
