# Sauce — Three controlled directing edits on one verified Resend workflow

**Date:** 2026-11-24
**Status:** Research experiment, **creative REJECT ×3**, no launch or owner sign-off.
**Repo:** `Davemafy/sauce-vids`, `main` only. Existing 8-vCPU/16GiB Vultr DevMCP worker. No new source capture, invented UI, model-generated gestures, deployment, paid API use, new branch or infrastructure.

## Why this experiment

Owner called for ending the iterative cloud/bezel loop and evaluating actual film direction instead. Three film edits from the *same* existing verified Resend pricing workflow test whether continuous direction, editorial cuts, or a physically tracked glass-window camera communicates the real product's value best. Don't mistake having 3 playable films for having 3 premium demonstrations.

**Verified original source**: `sauce-singlecall-20261121/.tmp-singlecall/source-trim-v4/original-pixels-action-reel.mp4`, SHA256 `6973a247624d514aa75b8d10c45a01a022942f2597f251c65aeb7d91a95ff586`. Original unmodified 2880×1800 Chromium DPR2, **613 native frames / 10.216667s at 60fps**, cursorless; 325 original source pointer samples. Matching independently verified event manifest `rebased-verified-events.json`, SHA256 `efd1843cd6668b089f1fd41dfbd3db0263432a6da82e453daaf66d3d776e9168`, has three genuine slider outcomes: **$35/mo, $160/mo and $350/mo** after progressing from a visible $20/mo starting state. Real verified result times **1.989s, 4.815s, 7.809s**. No change to source pixels, action timing, price text, cursor stream, event evidence or source audio cue indices.

All three treatments use the same cloud background and large floating browser `cloud_window_fullglass_v1` with the original 48kHz Foley timeline. The exact three independently rendered `source-verified-event-foley.wav` tracks have identical SHA256 `0409a4d9694863988322d5218c56521f82783580d794044918c377b810d483a0`. Only original-source-anchored camera plan and associated lens motion vary.

| Variant | Editing grammar | Camera evidence | Encoded QA | Actual film SHA256 |
|---|---|---|---|---|
| **A — Living Interface** | Quiet continuous drift and verified price-result focus, no hard cuts | 5 keys, 0 cuts, max **13.0849px/60fps frame**, final context **0.6414** | **REJECT**: STATIC_OPENING_2S, REPEATED_OR_STATIC_FRAMES (0.891) | `1d32bbadc9d73592e1cbd0481b434a8e31285b248544c42d1115a25c45aac4f8` |
| **B — Cloud Editorial** | Three native-source-frame cuts **after** the real results, brief returns to slider before next input, stronger price close-ups | 7 keys, cuts at source frames **123/292/472**, max continuous motion **24.7488px/frame**, final context **0.5119** | **REJECT**: STATIC_OPENING_2S, REPEATED_OR_STATIC_FRAMES (0.772) | `2a28d3da1ec6be9ca51e942ce7e86a2919060c8d383926175e615edbc5796533` |
| **C — Optical Film** | Physical window dolly, source-recorded pointer spring and no editorial cuts | 8 keys, 0 cuts, max motion **41.691px/frame** (below engine's 45px limit), final context **1.0** | **REJECT**: STATIC_OPENING_2S | `0ef5718c6b709e3b1cc71aeac605f8e6c91ecfaeafe91fe9dbcf644113a4ae2a` |

All three outputs: **1920×1080/60fps, 613 frames, 10.216667 seconds, H264 + AAC stereo 48kHz**. Each strict FFmpeg full decode PASSED. Inspected the actual **ten-frame encoded contact sheets** and decoded full-resolution frames at **2.55s, 5.42s, and 8.55s**. Codec and Playwright checks are not creative acceptance. The existing quality supervisor flagged the above failures. Optical C has the most acceptable motion rhythm *of the three*, but the header clips uncomfortably on its zoom; B emphasizes the verified dollar values most clearly but partially clips the “Pricing” heading and is too cut-heavy; A preserves context but barely moves. No sufficiently strong option to select for production.

**Access:** three encoded masters under private worker folders `.sauce-stagehand-private/three-edit-experiment-v2-20261124/{living,optical}` and `.sauce-stagehand-private/three-edit-experiment-v3-20261124/editorial`. Three separate owner-signed expiring HTTPS review links were delivered in the chat, each verified signed Range GET **206**, unsigned **403**, 72h expiry; playback and seeking to t8.5s passed using real Chromium at **1280×720** and **390×844** for every variant, with no player errors or JavaScript exceptions. No signed links, private media, original browser recording or screenshot content committed to public Git.

## Implementation retained (R&D only)

- `scripts/compare_three_verified_edits.py`: strictly compares one SHA-bound original source and manifest; requires genuine recorded pointer and 3 measured non-destructive observed UI events; creates three deterministic source-time-safe camera plans. No frame synthesis, source retime or source-aligned-cut fakery. Denies inconsistent hashes, unsafe events, missing evidence, insufficient reading intervals and overwriting earlier experiments.
- `tests/test_three_real_edits.py`: source/manifest/timeline/audio parity, real-result-causal focus/cut alignment, forged evidence refusal, insufficient hold refusal.
- Output directory and rejected plans are private; **do not include these as approved few-shot Gemini references**, per the project's reference provenance gate. No model API calls were needed or admitted.

## Substantive creative lesson

**A weak recording cannot be rescued by beautiful camera movements.** Original price outcomes are genuine, but the first payoff doesn't appear until 1.99s; too much of a 10.22s film is source-idle; the dark pricing grid is dense on mobile; the current glass reflection can compete with source contrast. A has no compelling early hook, B cuts away useful pricing context, and C makes real prices feel more physical but clips the heading. The outcome supports future **action-led shorter source capture** with a readable slider-and-price payoff in the first two seconds, then one deliberate detail shot and a stable legible hold. Before promoting any reference, test a new actual native-DPR2/60 public interaction clip and compare with the inspected Screen Studio references. **Do not add synthetic movement just to lower a static-frame metric.**

No winner approved. No release-candidate replaced. No production redeployment. No sale claimed.
