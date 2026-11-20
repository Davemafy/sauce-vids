# Sauce — Gemini Glass Loupe extension A/B on tweakcn (2026-11-20)

**Status: two completed, verified and visually REJECTED A/B films; one bounded B2 repair also REJECTED. No approved premium reference or production rollout.** This report records the real research experiment, not a production success claim.

## Scope and isolation

- Target: public `https://tweakcn.com/editor/theme` (no login or paid actions).
- Workspace on existing persistent Vultr DevMCP: `/srv/devmcp-workspaces/009d4bc7ec42499d54e8c37fec2d9886/sauce-tweakcn-gemini-20261120/`, a **fresh isolated main-only clone** from `a88415728a01f6c5c54d162c1dacbf9250f5812c`.
- No change or reset of dirty production `/opt/sauce-vids`; no new VM, push, deploy, public exposure of private video, or private credentials written to artifacts.
- Model API key remained in existing root-protected `/etc/sauce-url2video.env`, invoked only via owner-authenticated host administration. Never logged.
- Temporary experiment artifacts are private under `.tmp-tweakcn/`. No customer-ready share link exists.

## Real scout and genuine source

Gemini `gemini-3-flash-preview` received an editor screenshot with its genuine preset dropdown and chose **Neo Brutalism**, predicting a stark contrast from the monochrome Default state. Its first response was truncated (`MAX_TOKENS`), its one bounded repeat returned complete choice JSON. The site was captured using a REAL Playwright Chromium session; no interface pixels, theme outcome, or API results were synthesized. The first take was preserved under `.tmp-tweakcn/attempt1/` after a native color menu obstructed the result. The recapture used actual Escape input to dismiss the obstruction. No source pixels were retouched.

Verified before/after on the public site: CSS `--primary` changed from `hsl(223.8136 0.0000% 9.0527%)` to `hsl(0 100% 60%)`; `--border` went to `hsl(0 0% 0%)`; `--radius` from `0.625rem` to `0px`. In the visible preview comparison, **16.47%** of sampled luminance pixels had an absolute change above 25/255. The source is not an authenticated customer workflow: it proves a public theme-editor transformation only.

- Hash-verified 1920×1080 H.264 source, **25fps (not native 60fps)**, 164 frames / 6.56 seconds: SHA-256 `00949cfb3cbe688daae3069fb76f11f2bab9479f92c66d3679df649f584e15ba`.
- JSON manifest: SHA-256 `ffc3380a8cc359c3d71a9a43fb80f914a125f2920c08936d8bc9c9b8688c4b95`. Real `kind:"theme_change"`, pointer approach/press/release, genuine element and outcome bounds; model planning conservatively treats the changed state as verified at **3.0784s**. The Playwright video recorder-to-application monotonic-clock offset is approximate and explicitly documented in `capture.json`; it is **not** sample-exact event sync proof.
- Source video frames independently inspected at ~0.5, 2.2, 2.8, 3.5, 4.8 and 6.0s. No fake color state. The transformation is visible after the genuine selection.
- `source.mp4`, `capture.json`, `before.png`, `after.png`, source contact grid and source receipt remain private.

## Reference admitted for the A/B

Prior real Sauce liquid-glass source-true reference `1000421253.mp4` was reconstructed from its original capture and `examples/sauce-film-plan-glass-loupe-liquid.json`. This is **a byte-identical technique reference, not independently approved $50K creative gold**. In this experiment the source and manifest hashes were validated on current main, and the full 279-frame/4.65s/1920×1080/60fps reference was re-rendered **again after** the opt-in click-style extension; the new MP4 SHA-256 matches the original reference **byte-for-byte**:

`3df5b2391ef933a92b8198541ec9981649f115035d9e38dbd45991588653b10f`

The exact reference video and JSON were provided only to condition B (and to later independent critique and B2 repair). A and B shared the same live source footage, before/after images, engine contract, model, instruction objective, and actual rendering capability. The shared contract necessarily exposed the glass-loupe schema to both, so A was **not** a fully unprimed creative baseline.

## Genuine Gemini A/B result

Two distinct `gemini-3-flash-preview` calls, **one initial plan each**, temperature 0.8. A received source MP4, before/after images, evidence, and engine contract. B received all of that **plus the exact 4.65s reference MP4 and matching executable JSON**. Both original outputs were syntactically valid and passed Sauce's exact source/manifest, source-clock, anchor and window/backdrop validation **without repair**. Both chose glass-loupe presentation and window stage.

| Film | Plan SHA-256 | Encoded MP4 SHA-256 | Visual result |
|---|---|---|---|
| A (no reference) | `995de3d11779003c1c55c9171d006e7e0cb80fd5e138c7d5e2a961bc49ce48cd` | `7cb3390bf4e6c39bb497429a1e67ab69079508a850612d411514dfa55a925e11` | **REJECT**: extreme menu zoom, oversized refraction hides genuine UI, dense tiny content, irrelevant scenic backing |
| B (Glass reference + JSON) | `12545bef4f6b7157a9029b3df2d6e7d7e6566961b90062445ad9c9583bc48414` | `737cdea0bf13b4d88cc83fff59ab7b171c892ed79c14b8d1d72868cbbb229ca6` | **REJECT**: steadier center lens but still huge, clipping critical cards, uninspired static opening and compromised ending |
| B2 (one critic-informed repair, **not part of the controlled A/B**) | `fafa3f3292019eee063ce0de508bc1cc80081eae8ad132207a85ee6180696604` | `ec621e3290215c5ed2e83e3e413cace762229c8adfeea5de6a017df7c80b74b7` | **REJECT**: neutral backing and smaller lens improve restraint, but opening UI remains tiny/static and final crop still weak |

All three real H.264 videos contain **164 frames at 1920×1080/25fps, 6.56 seconds, no audio** (source cadence is not 60fps). `ffmpeg -v error -xerror -i FILM -f null -` completed on all three. Chromium play/seek at **1280×720** and **390×844** passed for A/B/B2 with no video errors or page errors. That proves browser playback, **not** phone-scale legibility. Contact sheets show the observed defects at 0.25, 1.1, 1.8, 2.35, 2.9, 3.5, 4.3, 5.15 and 6.2 seconds; full-resolution stills from A/B were inspected at 2.9, 4.3, 5.2 seconds. The lens visually distorts the real source pixels rather than inventing a new UI, but its enormous size and source geometry obscure what changed.

One separately instructed Gemini critic viewed A/B actual MP4s, the reference MP4 and contacts and rated A 4/10 and B 6/10, rejecting both. These **are model self-scores, not human/independent studio approval**. Its preference for B does not prove a significant few-shot effect: n=1, same model family, and baseline included the glass schema. It identified lens occlusion and clipped cards. A bounded B2 revision exposed a scale-control argument but still failed human-facing first-glance judgment after real rendering. No blueprints/reference pair were promoted to gold examples.

## Experimental compositor change — **local only, not GitHub production**

On isolated `main` checkout, local commit `f6b0ea3c360795f43a48e0255b29b1b6d9095200`:
- `scripts/glass_loupe.py`: permits a verified **theme_change click** without relabeling it a slider drag, respecting early release vs later DOM-confirmed result, recorded pointer and bounds.
- Adds optional `glassLoupe.magnification_scale` in [0.55,1.0], default 1.0; validated bounded optical-strength control. No feature deployment or remote-code push.
- New `tests/phase2/test_glass_loupe_theme_click.py` protects admitted outcome, negatives, magnification bounds and backward compatibility.
- **12 targeted tests passed** on this private checkout. The original reference replay remained **exactly byte-identical** under the modified local engine. New code was intentionally NOT promoted to GitHub `main` while its film remains aesthetically rejected.

## Provider usage and interpretation

Six network model requests: scout attempt #1 incomplete, scout attempt #2 complete, A, B, independent critic, B2. Provider-reported token totals by call: **2,279 + 2,259 + 7,720 + 8,260 + 4,727 + 7,073 = 32,318**. Actual billing/price not independently verified. Most Gemini outputs validated first try; **zero films creatively approved**.

This test supports *technical feasibility* of a verified reference-video+JSON-conditioned film plan and a reusable event-type-compatible optical effect. It **does not establish** learned premium direction, improved commercial output, or scalable URL→$50K film. Technical passing and one critic's 6/10 cannot supersede our encoded-frame rejection.

**Next experimental bottleneck:** the meaningful theme payoff needs much larger, source-derived cards, a truly action-first 1–2s opener, less intrusive optics and higher native source cadence. The old liquid-glass match is a technique sample, not a gold visual standard. Use a high-quality **externally benchmarked** UI-first film and a fully faithful motion reconstruction before claiming transfer generalization. Preserve these rejected films as research evidence only.

## Private reproducibility pointers

`.tmp-tweakcn/`: `source.mp4`, `capture.json`, `source_receipt.json`, `reference.mp4`, `reference-plan.json`, `reference-regression-replay.mp4`, `A.json`, `B.json`, `B2.json`, `film-A.mp4`, `film-B.mp4`, `film-B2.mp4`, `contact-A.jpg`, `contact-B.jpg`, `contact-B2.jpg`, `critic.json`, `playback_qa.json`, per-call receipts and render logs. No public review URL was authorized and no private capture was committed to this public repository.
