# Sauce reference fidelity — do not feed approximations to Gemini

Status, 2026-11-19: Arcade Stack by Ramp has a full decoded-frame ledger and 10 visually reviewed hard discontinuities. **It has NOT been reconstructed with 1:1 visual/motion fidelity. It is not production-ready Gemini reference data.**

## Two distinct fidelity targets

**Recreating the reference:** With legal, independently obtainable source assets and reusable Sauce primitives, reproduce a selected reference shot to output-equivalent framing, geometry, layer order, scale, motion, easing, timing, pointer, color, shadows, transitions and sound. Compare original versus output at every frame and corresponding audio timeline. The original proprietary edit project cannot be uniquely reconstructed from an MP4; the requirement is observable output equivalence, not recovery of hidden source keyframes.

**Transferring to another customer product:** The customer's authentic UI must differ, so literal pixel equality to Ramp is impossible and would violate source-truth. The standard is equally strict motion/composition correspondence on that new real UI, plus source fidelity and independent publishability approval. Never transfer Ramp logos, source media or invented product actions.

Descriptions like "big approval card", "slow zoom", and "hold result" are editorial impressions, not verified 1:1 data. The older Arcade recipe is reclassified analysis_only, explicitly NOT a gold motion example.

## Actual source measurements and their limits

The original public 67.2-second H264/30fps 1920x1080 reference was reopened and checksummed. Reference MP4 SHA256: 7d22a17f97d3183cae73df90321f7be7943006d9bf7f4ecd7c2a79f15215bbbf. The new scripts/reference_frame_ledger.py decodes every one of 2016 full-resolution frames, hashes its exact decoded BGR pixel data and records per-frame objective BGR means and pixel-change fractions, without resizing. The output is references/arcade-stack-by-ramp.frame-ledger.json (derived numeric data only). It does not contain reference screenshots or media.

The full-resolution change heuristic nominated exactly 10 large discontinuities; adjacent original frame pairs were visually checked for frames 66, 624, 792, 1015, 1104, 1261, 1392, 1438, 1579 and 1833. A cut at incoming frame 66 is at frame-clock time 66/30 = 2.2 seconds. Review is recorded in references/arcade-stack-by-ramp.cut-review.json. This list is NOT exhaustive: fades, soft transitions, small-region changes, object movements and actual keyframe curves remain unmeasured. No shot-level reconstruction, pointer tracking, object masks or full layer order has been recovered.

The frame SHA256 ledger certifies frame identity only; it cannot tell Gemini the desired camera path. Distinguish pixel evidence, heuristic discontinuities, manual visual review, inferred layer behavior and independently reproduced motion.

## Admission gate for a true 1:1 reference

1. Source media and timing: exact SHA256, full decoded frame ledger, original frame rate, provenance and lawful use.
2. Shot segmentation: verified start/end frames, soft transitions, temporal overlaps and fade durations.
3. Object tracks: bounding geometry and masks for every relevant UI element across each frame; camera translation/zoom/rotation, easing, shadow, occlusion, cursor hotspot and click semantics, tracked with measured confidence. Unobserved features must remain unknown.
4. Renderer execution: every declared transformation must be supported by tested, reusable JSON-driven Sauce primitives. Do not put imaginary parameters in a reference recipe.
5. Independent reproduction: render with Sauce and authorized UI assets, not by using original reference frames as the output. Compare all corresponding frames at native resolution, audio timing, legibility, transition boundaries and object trajectories. Maintain failed A/B reviews as evidence and revise until approved.
6. Independent creative signoff and rights/source-truth review. Technical tests alone cannot mark the source or candidate premium.
7. Only after those steps can a reduced recipe be used to direct Gemini on a different product with separately verified capture evidence. A production plan must pass deterministic geometry/time validation and full MP4 visual review.

One genuinely matched reference is worth more than dozens of vague stylistic JSON descriptions. Do not feed the old Arcade recipe to Gemini in production.

## Enforced status in code

The existing scripts/reference_director_packet.py now rejects the Arcade recipe by default, including attempts to falsely label it verified_1to1. Its sole permitted operation is explicit --research-only, which produces a packet with productionGeminiEligible:false. No Gemini API call or deployment has been performed. A future production release requires an independently verified render-match receipt; that certification path is NOT implemented by changing a JSON string.

Tests: tests/phase2/test_reference_frame_ledger.py and tests/phase2/test_reference_director_packet.py. No third-party media bytes or screenshots are committed.

## Next exact recreation to prioritize

Choose a short shot inside the real Arcade film: the approval or verified-result reveal. Recover its exact incoming/outgoing frame bounds, UI rectangle and matte tracks, camera curve, foreground/background geometry and pointer motion at all frames. Implement any missing reusable Sauce compositor primitive, recreate against authorized independently captured UI, compare output at native resolution frame-by-frame, and iterate. Only that output-verified shot earns a place in the high-quality reference dataset. The entire 67.2-second reference is not claimed reconstructed.
