# Sauce Stagehand → Phase 2: action-first pacing correction, 2026-11-23

**Decision:** The owner said the Brimble film *"Seems slow from Gemini."* The observed problem was editorial: an original 10-second real-source film spent >50% of its timeline in nearly static source frames, even after useful camera improvements. Gemini selects the product control; it does **not** generate individual MP4 frames, animate the cursor or dictate the old 10-second render. Earlier confirmed Stagehand/Gemini observe completed in about 1.5s inference on a public page; native60 browser recording and FFmpeg composition are separate latency concerns.

## What changed on main

No rebuild, new browser framework, altered production Studio defaults or synthetic source UI:

- **Shorter native source capture**: experimental `scripts/capture_stagehand_verified_native.py` defaults to **6.5s**, permits a bounded **6–16s** public one-action shot, still verifies real same-origin click and actual changed DOM/pixels. The X11 recording is still native 60fps at 2880×1800 DPR2.
- **Causal shorter source edit**: `scripts/source_event_director.py` admits a six-second minimum only when exactly **one** independently verified action exists. Multi-action baseline remains 8–25s. `scripts/plan_stagehand_phase2.py` now reaches the real source-confirmed result in ~0.92s, then gives a >=0.7s static source-true readable hold and a 1.5s physical window release. The outcome camera still **cannot start before the true recorded result**. No guessed source timestamps, fake interactions or new decoration.
- **Experimental opt-in wrapper**: `scripts/stagehand_phase2_pipeline.py` defaults to 6.5s. The wrapper itself was not newly proven one-command end-to-end in this change; the native recorder, source adapter, plan validator, renderer and QA were executed on the actual original Brimble footage. Existing opt-in and private-only deployment boundaries remain.
- **New regressions**: short native source planning maintains click/result order, ≥0.7s legibility gap between closeup peak and wide release, full source hash and multi-action minimum-duration guards.

## Evidence: two original native60 takes, not artificially sped footage

| Metric | Before | After |
|---|---:|---:|
| Source-run length | 10.0s | **6.5s** |
| Original native60 source frames | 600 | **390** |
| Encoded target | 1920×1080, 60fps | **1920×1080, 60fps** |
| Source manifest | Original actual DOM click/result | Original actual DOM click/result |
| Encoded QA | **REJECT**; `REPEATED_OR_STATIC_FRAMES` 0.556 | **HUMAN_REVIEW_REQUIRED**; **no automated findings** |
| Creative approval | No | **Still no** |

**After original source:** private `../.sauce-stagehand-private/brimble-fast-native6s-20261123/source-native-dpr2-60.mp4` SHA256 `859392c3594a71069806fc1b51fbb8cb487b04d581d6e57de4d3f33a304d5453`. Real Brimble `a1` from existing actual Stagehand observation; real DOM dialog 800×720 at DPR2; genuine 65 pointer samples; independent source pixel change fraction **0.39563**. Renderer native original source plan SHA256 **`63abfa5d8a1339bb8cd2f1ea51f730f761254642dfc0c4f3ff9483dc12acb020`**. Strict camera validation: 390 frames, max motion **40.0809 px per 60fps frame**, below existing 45 bound, genuine result visible fraction 1.0 and final context visible fraction 1.0. This is a significantly faster push than old 23px/60fps; still needs eyes-on evaluation.

**Encoded film:** private `../.sauce-stagehand-private/brimble-fast-native6s-20261123/brimble-fast-native6.5s-1080p60.mp4`, SHA256 **`5e5ef53e4bf7cd45be9916403841a9f1854e760eb58cb2966b36dd0b4097e787`**; 6.500s / 390 frames H.264 1920×1080/60fps, AAC 48kHz, **strict FFmpeg full decode PASS**. Inspected 6.5s final encoded contact sheet (0–6s). The dialog dominates the mid-section more legibly; cobalt Cloud Shadow and product source remain true, but the film still only shows a **Connect your agent** selection, not Brimble's deeper payoff. No false claim of cinematic film acceptance.

**Signed owner-only film review:** [Brimble, tighter 6.5s](https://devmcp.davemafy.xyz/sauce-expiring-review/tweakcn-20261120/brimble-agent-paced-6p5s-20261123.mp4?md5=Y6vpRByYMC_jY7KBMUJKAg&expires=1795698563). Existing protected review route, ~72h expiry. Signed HTTP206 range, unsigned HTTP403; actual browser 1280×720 desktop and 390×844 mobile video decoded and seeked t3.5s (source dimensions 1920×1080, zero playback/JS errors). No public Studio deployment, new VM, or overwrite of the old 10s footage.

## Remaining creative distinction

This experiment establishes that **a shorter real-source capture and a more decisive source-confirmed physical dolly** can remove the technical repeated-frame failure. It does not demonstrate general autonomous story selection, production readiness, or reference-quality product value communication. Film must remain owner review until a more meaningful verified multi-state workflow and cinematic shot grammar are approved. Shortcuts that falsify temporal source truth or animate a fake screen are forbidden.

Use the next session to make stronger *source-permitted* action choices, preserve readability on 390px, and measure full film quality beyond codec/QA. Do not confuse Gemini request latency with frame generation and render time.
