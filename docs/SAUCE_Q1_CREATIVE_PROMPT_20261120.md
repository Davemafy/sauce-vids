# Q1: short creative Gemini prompt + real footage + existing Sauce JSON (2026-11-20)

**Status: one experimental creative task; output RENDERED for review, but REJECTED for quality.**

## Exact first creative prompt

> My client needs a cinematic UI shot of HeroUI's real theme-color change. Give this four-second 16:9 recording the taste, confidence and visual impact of a $50,000 motion-design production.
>
> I've attached our actual product footage, a premium motion reference, and an existing executable Sauce JSON. The JSON shows the format, not the creative ceiling. Study the work, choose your own composition, motion and pacing, then give me a NEW JSON in exactly that format. Take creative ownership.
>
> The UI must remain genuine: hue 208→50 becomes visible at 1.88965s. Never fabricate a UI state or click. Return only the complete renderable JSON.

The real four-second HeroUI browser MP4, the genuine Arcade 46-frame Stack by Ramp panel-motion clip (frames 1392–1437, privately downscaled to 960×540), the 1200-byte verified manifest, and an existing complete isolated-UI Sauce JSON were supplied. The prior JSON was explicitly disclosed as a geometry-verified, quality-rejected format example, NOT a gold creative example. The two VIDEO clips were sent as multimodal inputs; this was not a text-only interpretation.

**Target video SHA256:** ac0c57a8b92f61414296dddc46c03a83013b803f66bf6c70febe3af1becf1c5c. Original browser capture was native ~25fps and resampled to 1920×1080/30fps for the four-second shot. All source states are genuine.

## Inference receipts

The existing root-protected Vultr Gemini key was used (never printed or uploaded). Model endpoint attempts:
- gemini-3.1-pro-preview: HTTP 429; no film plan.
- gemini-2.5-pro: HTTP 404; no film plan.
- gemini-pro-latest: HTTP 429; no film plan.
- gemini-3.8-flash: timeout at 155.12s; no plan (billing after timeout unknown).
- gemini-3-flash-preview first request: 3,320 reported total tokens; creative JSON, invalid source hash.
- gemini-3-flash-preview short source-timing feedback #1: 2,798 tokens; JSON still showed future UI state before it existed.
- gemini-3-flash-preview follow-up: HTTP 503; no plan.
- Identical follow-up retry: 2,753 tokens; JSON still had a 10ms future-state timing conflict and out-of-range rounded radius.

**Eight network requests, three successful JSON completions, 8,871 reported total tokens** across successful replies. Actual provider billing was NOT independently checked. All three raw Gemini JSON files are preserved unchanged and failed genuine Sauce validation. No production change or external submission.

**Creative selection:** Without the old keyframe-heavy instruction scaffold, Gemini independently requested a floating, isolated-ui dashboard layer, a second source-derived color-control layer, and a restrained camera push. This is an observed behavior, NOT a controlled proof of better models or better prompting.

## Honest rendered preview

A separately labeled mechanical preview copy normalized the model's last JSON, with only:
- composition start and first layer start: 1.89s -> 1.90s, because sourceAt is 1.90s
- accent indicator radiusPx: invalid 100 -> supported maximum 28
- accent indicator entry y: 0.920 -> 0.915 (about five pixels upwards, necessary for safe margins)

This preview therefore does **NOT** prove the original model JSON was directly executable, and it must NOT be promoted as approved reference data. All pixels in its UI layers come from actual captured source frames. Verified output: H.264, 1920×1080, 30fps, 120 frames, 4.000s; decoded fully by FFmpeg. **MP4 SHA256: 8f63cd62c38007276e0f65c4e9bc9517ff1d43eaac8eee45397314aa3afbb947.** Existing isolation/receipt tests: 20 passed.

Frame review included 0.15, 0.90, 1.70, 1.92, 2.16, 2.60, 3.22 and 3.82s at source scale, including a 1920×1080 2.60s frame and a contact-sheet comparison against real Arcade shot frames 0/23/45. Film verdict: **REJECT**.

Specific defects: the crop cuts off the real upper dashboard metric cards, a real but irrelevant multicolor indicator is detached below golden charts, the enormous pale stage is visually unmotivated, the isolated reveal fades through a washed-out transitional state, and the action->outcome handoff lacks the reference's decisive pointer/control grammar. Authenticity and a valid MP4 do not make the output commercially acceptable.

Private isolated worker directory: /srv/devmcp-workspaces/2a3b4d0ecb17c0c0f22736be61468a31/sauce-q1-pro-creative/.tmp-q1/
Relevant files: brief.txt, proposed.film-plan.json, repaired.film-plan.json, repaired2.film-plan.json, preview-normalized.film-plan.json, gemini-q1-preview.mp4, q1-review-contact.jpg, reference-versus-q1.jpg, provider-receipt.json, repair-receipt.json, repair2-receipt.json and validator logs.

**Interpretation:** short-client-brief multimodal prompting elicited meaningful composition choice, but first-pass schema/source safety, crop judgment, focus and visual payoff still failed. One isolated qualitative trial cannot establish direction quality. Keep the original prompt and full evidence for inspection, without seeding rejected plans as successful examples.
