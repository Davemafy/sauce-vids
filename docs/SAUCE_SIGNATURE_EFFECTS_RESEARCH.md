# Sauce signature UI-effects research — 2026-11-18

Status: **research + one source-true encoded laboratory proof**. No production preset, commercial visual acceptance, customer deployment, or claim of automatic generalization.

## Thesis

Sauce should not compete by stacking generic post-processing filters on a screen recording. It should convert **verified UI states and spatial hierarchy into an editable, deterministic cinematic scene**, then apply occasional optical effects only to regions where they improve the story. Its durable advantage would be **source-true semantic motion**: genuine interface pixels retain identity while the viewer's attention moves through a clear action, observed state change and readable result. Film quality must be judged from the actual encoded video at normal speed, including 390px-wide playback.

The current renderer already implements a true H0 background/H60 foreground dialog plane, spring camera, source-derived action/DOM geometry, deterministic backgrounds, occasional rim lighting, result payoff and 48 kHz Foley. Do **not** rebuild any of these. What remains weak in actual Brimble and OpenSheets encoded images is small visual subjects against an oversized neutral/gray plate and underpowered result visibility.

## Verified visual references and the transferable techniques

| Reference / viewable URL | Technique worth extracting | What not to copy |
| --- | --- | --- |
| [Figma: 3D transforms launch film behind the scenes (12 Nov 2026)](https://www.figma.com/blog/how-3d-transforms-and-figmas-agent-brought-a-launch-video-to-life/) | Shared perspective, depth-separated editable frames, spatial typography, composition before surface shaders, reusable arranged components. | Figma's manually art-directed scenes do not prove that all SaaS DOMs can be automatically exploded. |
| [Figma Slides official product film](https://www.youtube.com/watch?v=p-B--SGq_ZQ) and [Cutmap's 28-beat analysis](https://cutmap.co/v/figma-presenting-figma-slides) | Actual interface is the hero; purposeful close-ups, hard scene cuts, action/result narrative and reading holds outperform constant optical effects. | Reusing their commercial assets or claims. |
| [Codrops persistent WebGPU page transitions](https://tympanus.net/codrops/2026/06/30/building-persistent-page-transitions-with-webgpu-and-vanilla-javascript/) | DOM-bound persistent image planes detach, move through a stable scene then reattach. Capture-to-capture common-element transforms (FLIP) are a plausible Sauce route. | It is interactive page tech, not proof of a deterministic offline film compositor. |
| [Codrops Atelier UI](https://tympanus.net/codrops/2026/10/21/atelier-ui-webgl-dom/) | Shared DOM/graphics timing and pixel transitions; relevant to coordinating source frames, mask movement, cursor and optics. | Blanket distortions over text-heavy video frames. |
| [Ordinary Folk: Webflow A New Era of No-Code](https://vimeo.com/664409837) and [case study](https://www.ordinaryfolk.co/project/webflow-a-new-era-of-no-code) | Precise visual rhythm and motif continuity between 2D and 3D compositions. | Its abstract/custom 3D design is not source-verifiable UI footage; use as direction benchmark only. |

## Ranked candidate *effect families* for Sauce

Scores are qualitative engineering priorities, **not** measured market potential.

| Candidate | Trigger and pixels | Differentiation | Generality | Readability risk | Decision |
| --- | --- | --- | --- | --- | --- |
| **1. Semantic result lift** | Observed before/after resultRect, verified source pixels; result crop detaches and grows with context preserved | High | High for bounded, visible regions | Medium (source resolution, pointer duplication) | **Promote to gated engineering experiment** |
| **2. Common-element match / spatial handoff** | Same element ID and recorded before/after source rectangles; match anchor transform across states | Very high | Medium | Medium (identity ambiguity, occlusion) | **Second engineering prototype** |
| **3. Layered hierarchy reveal** | Confirmed modal/tooltip/menu ancestry and real clean H0 plate, native H60 active content | High | Medium-high | Low-medium if restrained | Extend existing H0/H60; do not rebuild |
| **4. Contextual rack focus** | Only post-interaction and behind verified result, use depth masks / bokeh on non-text contextual layers | Medium | High | High if text is blurred prematurely | Optional supporting finish |
| **5. Kinetic type as a scene edge** | Product-authored name/section title or clearly labeled editorial captions; not regenerated UI labels | Medium-high | Medium | High for misrepresentation | Opt-in, subordinate to real UI |
| **6. Local optical displacement or refraction** | Bounded shader away from text while detaching/attaching a plane; final frame exact source pixels | High in short bursts | Medium | Very high if masks leak over text | R&D only |
| **7. Animated edge specularity** | Derived from actual rounded projected element mask and scene light | Low as standalone | High | Low if restrained | Existing experiment was too subtle; no P0 |
| **8. Generic bloom/chromatic/glass backgrounds** | Whole-frame filters unrelated to interaction | Low | High | Medium | **Reject as selling point** |

## Technical contract (for every new effect)

1. **Provenance:** accept only frame-indexed, hashed browser captures and recorded click/result geometry. Track private-element exclusions. Static plates must be captured from the browser, never inpaint imaginary application states.
2. **Identity:** a promoted piece must have a persistent source rectangle and stable element identity. Reject when the visible region is animated, partially occluded, intersects an untracked live pointer, changes during extraction, or its source is below a legibility threshold.
3. **Motion:** all transforms run on the existing 60 fps output clock. Establish original app and cursor before action. If detaching a plane, keep at most one visible pointer representation: pass through as part of the original only if spatially owned; otherwise composite the verified cursor once with the same camera geometry.
4. **Readability:** crop must include required context (e.g. title, column label, changed values), fit within 16:9 safe bounds, and settle before an adequately long reading hold. Exclude text from irreversible distortion and depth-of-field. Inspect final 390px-wide frame and full-res text.
5. **Pixel truth:** never OCR/retype values into invented UI; final foreground is real source pixel data. Post-processing can move/color/light the video, but any source opacity stabilization or presentation-only modification is disclosed in the receipt.
6. **Failure:** when geometry, identity, privacy, or pixel evidence is insufficient, use the current verified whole-frame action-first shot; do not fake a sophisticated transition.
7. **Costs:** start with CPU/OpenCV/FFmpeg and the existing render worker; a new WebGPU service, paid inference, extra VM, or wholesale shader framework requires separate demonstrated benefit.

## Actual encoded A/B: OpenSheets semantic result lift

- Source: existing real continuous Chromium/X11 OpenSheets MIT sample recording at `sauce-v05-release/studio/.tmp/film-paradigm/opensheets-real-ui-x11-60fps.mp4`, 1600×900 at 60 fps, SHA256 `69800f09767840b54334d09f6006ad4c53c3edd519a9ea27a4460aae540c8eca`. Source sample expenses were created for this demo, **not customer data**. The recorded real formatting click is at t=4.9487s, real result at 4.9755s, verified first formatted frame 308. Result rectangle = CSS x1200, y223, w193, h109, five authentic USD-formatted cells.
- Previous main-linked OpenSheets match cut enlarges the full table by about 1.39× but the values remain small at phone width. Reviewed existing encoded source contacts and actual browser players.
- Isolated current-main study script: `sauce-high-effort-main/studio/.tmp/effects-lab/study.py` (ignored local scratch, not a deployed renderer). Wide authentic source sequence through frame 307, then a source crop anchored to the verified result, animated into a foreground reading plane in 27 output frames with a 90-frame hold. The foreground pixels come from source frame 330, observed to be **cursor-free within the lifted crop**; the first discarded study sampled frame 535 and duplicated a cursor cross. This correction was based on visual inspection of real source frames 308/330/350/400/480/535/600/680, not an invented or cleaned pointer.
- Final **review only** encoded master: 1920×1080 H.264 at 60 fps, 267 frames/4.45 s, **silent**, SHA256 `3a10c4813f331ff37a35f8c18e3002698c29540ca4cf7bdd30cbe1dbd8fc8d39`; full FFmpeg `-v error -xerror` decode passed, frame montage, native output frame and 390px downscale opened. Published only safe MP4, poster and minimal player to an isolated static review directory: [view prototype](https://devmcp.davemafy.xyz/sauce-motion-phase2/semantic-result-lift-study-20261118/), [master](https://devmcp.davemafy.xyz/sauce-motion-phase2/semantic-result-lift-study-20261118/master-1080p60.mp4). HTTP 200 for page/video/poster; Playwright on actual public HTTPS at desktop 1280×720 and mobile 390×844 gave `readyState=4`, `duration=4.45`, `error=null`, no JS page errors or horizontal overflow.
- **Honest visual critique:** genuine values now substantially larger and readable at the downscaled phone screenshot; the reveal is still an enlarged rectangle against a dimmed but flat spreadsheet, the low-DPR source softens glyphs, there is no Foley, the source-to-detached-plane jump is not yet clean enough, and it has not been compared through owner viewing in real motion. It is a compositing feasibility proof, **not a quality-approved film, benchmark pass, live URL capture default, or a sellable effects preset**.
- Local production worktrees and older published proofs untouched. This study uses an isolated current-main checkout and existing machine; zero inference, new hardware, paid actions or customer jobs.

## Next acceptance gate

Develop one **event-anchored, common-element continuity** shot on two *different* real workflows: the Brimble nested modal/Codex result and the OpenSheets amount formatting. Validate visual semantic identity and cursor ownership, no gray backing dominance, crisp phone-size result, and strict frame-aligned deterministic plan. Compare the same real source as side-by-side original / lifted / common-element shots at full 1080p and 390px downscale and normal video speed. Promote nothing to default until the strongest shot passes the project creative quality review.