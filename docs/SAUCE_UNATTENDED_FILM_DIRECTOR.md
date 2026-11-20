# Sauce unattended Gemini film director — bounded, source-true production capability

**Date:** 2026-11-20. **Implementation:** scripts/auto_direct_studio_film.py. **Scope:** a real capture MP4 + verified manifest -> Gemini-generated source-locked film JSON -> deterministic mechanical normalization -> strict Sauce validator -> render + existing decoded-film quality supervisor. This is an **independently runnable worker entry point**; it is not yet wired into the deployed public URL-to-video backend and no quality approval is implied.

## Run a genuinely model-directed film without a human coder

The existing Sauce browser capture supplies the **genuine private source movie** and its matching sidecar JSON. The helper in scripts/film_director_capabilities.py creates a model contract from the actual source: hash, frame rate, verified events and rectangles, current schema, and **which cursor representations actually exist**. The prompt never copies a research-only reference as an approved gold sample.

Run the fully unattended executable on the existing worker with its already configured protected server environment, not with a key on the command line:

    python3 scripts/auto_direct_studio_film.py \
      --source /private/session/source.mp4 \
      --manifest /private/session/capture.json \
      --brief "Make a cinematic product film from the real click and verified result" \
      --model gemini-3-flash-preview \
      --out /private/session/unattended-film

The engine requires an empty private output directory, a real local MP4 (max 24 MiB, 30 seconds), honest source capture metadata, a verified action and result, and a configured Gemini credential. It makes **at most two generation calls** (one initial, one feedback-guided retry). Provider failures, invalid source hashes, nonexistent or offscreen clicks, impossible camera movements, clipped result geometry, and unverified early lighting **fail closed**. There is no secretly fabricated fallback product story or hidden human camera rewrite.

All initial model output remains on disk. The only allowed deterministic repairs are:

1. If the model explicitly selected studioStage but confused it with the legacy window presentation *without any configured window*, use fullscreen because the stage already draws the physical screen.
2. If the model requested a recorded cursor for studioStage but the genuine capture has **no usable global pointer track**, downgrade cursor to none; **never invent pointer samples**. A separate legacy glass-loupe track is not removed, since it may use verified event-local samples.

The runner then executes the **same** scripts/render_event_video.py --validate-only that real rendering uses. Failed first-pass JSON and mechanical repair receipts remain available for regression. It does not loosen the camera/action/viewport gates to get a green result.

After encoding, the runner invokes the **pre-existing** scripts/quality_preview_supervisor.py on the actual MP4, with correct source+manifest hash proofs. Objective rejects become outcome=objective_reject; a film free of those known objective defects becomes outcome=needs_review, **never premium-approved**. The actual JPEG review/motion critic still matters: neither a model's creativity nor technical validity is sufficient. No background scheduling, constant paid inference, or unmapped URL exploration is built into this CLI.

Private output includes source-packet.json, each raw model text, parsed first-pass plan, normalized plan, mechanical-repair receipt, validator log, full render log, encoded-visual-qa.json, the final MP4 if possible, and unattended-receipt.json. All are source SHA-locked and must not be published as unapproved marketing media.

### What happened in real non-mocked model tests

**tweakcn source, 25fps:** one real Gemini 3 Flash unattended run used **2 generation calls** (provider-reported totals 4,910 + 12,035 = 16,945 tokens; charges not verified). The first response requested a studio and confused stage/window; mechanical normalization safely handled that, but the strict action gate rejected the camera: **0% of the genuine click target visible**. The agent automatically sent the exact validator failure as feedback. The **second Gemini film plan** passed the strict source-truth camera gate without any human editing of shot coordinates, and the runner encoded a real **1920×1080, 25fps, 164-frame, 6.56s H264/AAC 48kHz stereo MP4**, SHA256 **7f7cc115b6f1381630becded45aba6a6fa3c393e16adde9d3ab7701613d7f434**. After source-verified audio and output checks, the status was **needs_review**, not creative-approved. Actual contact-sheet inspection: pale stage, overly slow first second, limited atmosphere, only a modest payoff. **Creative review: REJECT as premium** even though the existing objective supervisor did not find a hard-coded video defect. The model was not trained on previous rejected cuts and did not require a per-site custom compositor.

**Resend pricing slider source, native 60fps:** separate real Gemini 3 Flash unattended run also used **2 calls** (reported 4,528 + 5,665 = 10,193 tokens, charges unverified). Its first output confused the 3D studio with legacy window configuration, and second output requested a global recorded pointer that did not actually exist. The first run **failed closed** without publishing an MP4. That directly motivated the reusable source-pointer contract and safe recorded→none correction (not site-specific logic). Replaying the **original saved second Gemini JSON** through the now-updated same orchestration (zero further model calls or manual creative JSON edits) passed the validator, encoded a real **1920×1080, 60fps, 279-frame, 4.65s H264/AAC 48kHz stereo MP4**, SHA256 **28ceff09497d7bbccb15d55120316fee73f5f1055e6f641dd74c94370ec6b601**. The **existing encoded supervisor automatically REJECTED** the model-directed film: **LOW_VISUAL_DETAIL** (fraction 1.0 of sampled frames). Frame contact review confirms the too-dark UI, tiny pricing values and overcropped intervening scene. This was a deterministic replay of the recorded model plan, **not** a second freshly requested Resend model run.

**Reusability distinction:** these two provider-sourced plans were executed by the **same generic director and renderer path** using their real sources/manifest. One completed fully unattended. The other initially failed safely, and the saved response subsequently rendered via the general source-provenance correction. Both remain **creative rejects**, and two sites are not proof of arbitrary-site quality. Running this independent CLI does not mean the installed sauce-url2video.service already invokes it; the deployed production service remains unchanged.

### Tests and safety

- Newly added unattended runner tests check a real source-locked generated response, a bounded validator-failure retry, invalid source hashes not reaching render, no credential → no model call/fake output, disallowed model IDs, original model output retention, mechanical compatibility edits, source-aware cursor availability and keeping independent glass-local track untouched.
- Complete Phase2 suite on this new isolated checkout: **363 passed, 10 skipped, 21 subtests passed**.
- Previous feature's **original Glass Loupe clip** reproduced byte-for-byte with SHA256 3df5b2391ef933a92b8198541ec9981649f115035d9e38dbd45991588653b10f. The original Resend and tweakcn cross-site source videos were rendered with the new stage, 48kHz event Foley and validated provenance in docs/SAUCE_SPATIAL_STUDIO_STAGE.md.
- Model provider keys are used only from the existing root-protected environment, never stored in the repo, plan, logs or public video. No new VM, branches, production secrets, public job changes or production service restarts.

### Next acceptance gap

This automation removes **a human coder** from the motion-design execution loop **after a genuine capture exists**. It does not yet remove the need for editorial taste. The current encoded supervisor catches technical defects, missing footage or visual poverty, not every uninspired but valid sequence (as the tweakcn test demonstrates). Improving that requires reference-verified film criticism on the **encoded result**, specific bounded revision recommendations, and actual creative review from users. Wiring this opt-in entry point into the deployed URL-to-video backend requires a separate source-capture/manifest adapter and production capacity/security evaluation, because its current capture receipts use a different schema. Do not infer that existing public jobs automatically have the new capability or that this study met the $50K quality bar.
