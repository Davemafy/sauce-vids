# Sauce semantic effects engine — integration contract

Current status: **one production-compositor opt-in family** (`semantic-layer-separation`) and **one experimental source-pixel handoff library**, plus a **separate opt-in glass loupe** in the event-video renderer. This is not a general shader engine or a visual-quality approval. See [SAUCE_SIGNATURE_EFFECTS_RESEARCH.md](SAUCE_SIGNATURE_EFFECTS_RESEARCH.md) for the external references and OpenSheets laboratory proof.

## Single rendering contract

```
verified browser captures + event log + stable geometry
  -> semantic identity/occlusion + protected content regions
  -> effect director (typed source-bound cues, compatibility, timing)
  -> per-output-frame effect samples
  -> existing Python/OpenCV cinematic stage and 48k Foley
  -> H.264 landscape film + source-provenance receipt + encoded QA
```

**Implemented seam:** `scripts/semantic_effect_timeline.py` provides a bounded timeline and mask/pass contract. `session_replay.py` now samples it for the already-existing opt-in `--preset 3d-launch --modal-lift` path. It preserves the original 300ms quintic easing and the existing H0/H60 source-pixel compositor. It is intentionally **not** another preview-only CSS layer or a replacement renderer.

Every effect operates on integer output frames from the canonical FramePlan. Real screenshots, verified geometry and the genuine clean background plate must be present before the compositor can sample an effect. If those fail, the current single-plane path remains the fallback. The drawn pointer stays a single projected compositor asset above the planes. Source pixels inside opaque foreground coverage must not be distorted or fabricated. The effect interface declares the composition order; the existing `CinematicStage` owns the actual draw order.

## Candidate families and their gating evidence

| Research idea | Sauce effect family | Input and trigger | Engine state |
| --- | --- | --- | --- |
| Semantic layer separation / exploded UI | `semantic-layer-separation` | Genuine dialog plus clean H0 plate; preserve DOM ancestry and correct pointer projection | **Opt-in wired** for one verified dialog. Broader hierarchy unproved |
| State metamorphosis / fluid reveal | `state-metamorphosis` | Two *actually captured* states, source-verified stable ID and geometry, observed change | Not implemented; do not tween invented text/content |
| Persistent spatial transitions / continuity tunnel | `spatial-continuity` | Recorded common-element identity and before/after rectangles, source pixel textures | R&D; source-preserving projection primitives exist |
| Kinetic typography / type masks | `kinetic-type` | Explicit owner/editorial copy OR source-authored text, opt-in and safe areas | Not implemented; no generated replacement product labels |
| Optical lens / refraction / x-ray | `optical-field` | Source-backed secondary representation or bounded interaction mask, text exclusion | Separate opt-in `--glass-loupe` on real Resend slider evidence; no common EffectPlan implementation yet |
| Procedural displacement | `transition-displacement` | Verified A/B textures, stable masks and exact unmodified settled state | Not implemented |
| Velocity deformation | `velocity-deformation` | Measured projected region motion, nontext-only deformation during transit | Not implemented |
| Grain, glints, rack focus | existing stage/optics finishing | Stage-only or masked inactive background; never damage UI glyphs | Existing opt-in experiments; not headline effects |

No new family should be added to `IMPLEMENTED_FAMILIES` until both its source-evidence validator and pixel compositor are implemented, with frame-level test coverage and a reviewed encoded A/B on **two distinct real websites**.

### Source-bound cue format (next interface)

A future versioned `EffectPlan` should carry `family`, `regionId`, `sourceCaptureHash`, `triggerOutputFrame`, `startOutputFrame`, `durationFrames`, `sourceRects`, `evidenceIds`, `protectedRegions`, `mask`, `pointerOwner` and bounded `parameters`. Its output is per-frame geometry and mask ownership, not AI-generated pixels. The TypeScript director can author the plan, but Python must independently validate all source evidence and geometry before drawing. A missing semantic identity or non-monotonic source clock must fail closed to the original readable film.

### Composition and compatibility

1. Source background (real browser pixels), then restrained background focus, then genuine moving foreground, then optional exterior edge light, then one projected cursor and evidence-linked callouts.
2. A semantic region has one owner at a time. Two effects that require different masks, modify legible text, or claim the pointer concurrently are incompatible; select the simpler effect or fall back.
3. Preserve 16:9 safe margins and a legible result hold. Never use a full-frame fluid shader on text-heavy software. Mask optical effects outside glyphs, or finish the optical transition *before* the readable hold.
4. Use deterministic seeds and the existing canonical frame cache where needed. A shared clock removes scheduler jitter; it does **not** make independently replayed Chromium pages pixel deterministic.
5. Roll out effects as **opt-in**; no default or paid product claim until the exact MP4 is viewed at normal speed on both landscape desktop and 390px phone, compared with the pre-effect output and approved by a person.

## Next release gate

The owner rejected the gray backing and floating UI treatments. A newer one-plane editorial shot gives a better action/result reading baseline; it is still unapproved. The modal lift remains an optional technical reference rather than the default aesthetic. Next build a *persistent common-element handoff* between two authentic Brimble states, with explicit background mask and text-preserving crop, then compare against real OpenSheets formatting. Render original / modal-lift / handoff shots from the same source and time map, keeping a stable first-click frame and full command context. If the effect reduces readability, reject it even when all tests are green.
