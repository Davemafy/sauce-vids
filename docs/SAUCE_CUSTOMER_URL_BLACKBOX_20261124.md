# Sauce — customer URL black-box audit and verified interaction gate (2026-11-24)

**Scope:** user requested Sauce be operated as a real customer would, not from reused session recordings or hand-edited JSON. This audit submits only a public URL to the existing owner-authorized URL-to-video API. Existing production code, private workspaces and all original videos preserved. Changes are on GitHub `main` only, no new VM or public Studio deployment.

## 1. Actual customer experience (no manual interactions or footage)

**Existing live loopback API**, `POST /v1/jobs {"url":"https://dub.co/"}`, ID `1ac0d6931dacb89a773df27b`: real browser inspection completed with 35 controls/16 headings. The server **failed at direction**: Gemini returned HTTP **503**, job failed with `StoryPlanningError`, no recording or video. Diagnosis: running `sauce-url2video.service` executes the **November 17** story pipeline in `/opt/sauce-vids`, not the latest GitHub main. A healthy /health endpoint therefore does not prove the customer pipeline works. DO NOT claim production was upgraded.

**Unmodified current-main isolated customer API**, same Dub URL, job `133c5ba7e1bb3eced8909edb`: failed model availability was recorded as `provider-unavailable-fallback`; automatic source capture produced real 1920×1080 Chrome source but only **25fps**, output H264 at 60fps is resampled rather than native60. No product interaction was recorded. Source SHA256 `43beefe83301f10161cf42f8d4145a03acd2636afe35ab8ff1241a0c2672c7fb`. Film `export/master-1080p60.mp4` SHA256 `cbbcf09a3c553bb2016e7e42819214b4a0b5dfc317d7aefe40f05700377378ef`. Encoded QA **REJECT**: `STATIC_OPENING_2S`, `REPEATED_OR_STATIC_FRAMES` (0.739), `NO_AUDIO_STREAM`. This is a PUBLIC WEBSITE PREVIEW, not an actual product demo.

**Another fresh customer URL**, `https://www.radix-ui.com/primitives/docs/components/tabs`, isolated job `2450eddffa2b3f7dae6b4b10`: Sauce found the real inactive `Password` tab but its independently measured result panel was outside the captured viewport. Existing verifier threw generic `ValueError`, then fallback silently changed to public showcase. Resulting real source 25fps and 60fps output with no actual tab action, QA **REJECT**: repeated/static frames 0.719 and no audio. No screenshot or app state invented.

## 2. Corrective customer product contract

- `POST /v1/jobs` **defaults to `intent:"product_demo"`**. A new customer URL must contain a safe, real, independently verified public product interaction with a visible payoff before motion recording. A mere accessible homepage or model fallback to marketing headings does not count. The API safely returns `needs_product_demo_url` with actionable next-step text, **without** spending time on another empty 60fps master.
- An explicit `intent:"website_preview"` preserves the honest pre-existing public-site showcase path; it must never claim to demonstrate private software.
- `backend.url_engine.execute(..., intent=...)` retains environment-policy compatibility for older internal scripted callers by using `intent=None`, while the customer API provides the explicit default.
- `backend/source_action_preflight.py`: when a real result container extends past the recording viewport, preserve the actual before/stable/after image hashes and independent pixel change measurement; mark `result_not_fully_visible`, `result_area_fraction=0`, no fabricated `result_rect`. This cannot be admitted as a premium/product outcome. Never convert this into “visually approved.”
- `tests/test_customer_film_intent.py` covers strict fail-before-capture, explicit website preview and invalid-intent rejection. Existing cinematic source gate remains fail-closed.

## 3. Fresh customer proof of the correction

An isolated server running this modified checkout, with no Gemini key, on the existing Vultr worker (NOT the production service), accepted single-URL POSTs:
- Dub, job `ed325282ac36897286d16d67` → `needs_product_demo_url`, no capture/MP4.
- Radix Tabs, job `af598dce6c36172614195de9` → `needs_product_demo_url`, no capture/MP4.
- Independent real Radix browser probe after the verifier change: `result_not_fully_visible`, measured visual change **0.02111**, visible result area **0**, before/steady/after SHA256 evidence all retained; no human approval.
- Existing original customer jobs and private rejected films remain untouched for comparison.

**Tests:** whole Phase 2 `pytest tests/phase2 -q`: **539 passed, 10 skipped, 21 subtests passed**. Legacy `unittest discover -s tests -q`: **340 run, 2 skipped, zero failures**, including the 3 new intent regressions and source-visibility tests. `git diff --check` passed.

## 4. Customer-facing encoded-quality disclosure

The initial strict customer gate prevents obviously unsupported public URLs from wasting capture/render resources. Separately, a genuinely rendered film can still be **visually rejected**. Its status endpoint therefore now derives safe fields from the actual saved `release.json`, not marketing copy or code-green state: `encoded_quality_verdict`, finding codes, actual browser source frame rate, encoded frame rate, whether a public product action was recorded, `film_kind`, `creative_approved:false` and `release_eligible:false`. There are distinct quality states for `REJECT`, `HUMAN_REVIEW_REQUIRED`, and `NOT_EVALUATED`. Unauthorized callers still cannot fetch job details or private footage. Existing bounded private revision is retained.

Verified by running the updated `customer_quality_summary` **against the original exact encoded Dub and Radix customer release receipts** (not fixtures). Dub: actual browser **25/1 fps**, encoded output **60fps**, `encoded-qa-rejected`, no real product action, no release eligibility, `STATIC_OPENING_2S`, `REPEATED_OR_STATIC_FRAMES`, `NO_AUDIO_STREAM`. Radix: same source/output fps and rejected quality, no action, `REPEATED_OR_STATIC_FRAMES`, `NO_AUDIO_STREAM`. `tests/test_customer_quality_receipt.py` adds six regressions.

**Updated regression:** 539 Phase2 passed, 10 skipped, 21 subtests; 346 legacy unittest run, 2 skipped, zero failures. This is status *truthfulness*, not a fix to the underlying native source fps, storytelling or audio.

## 5. Critical remaining defects

A URL that cannot expose a useful anonymous interactive action cannot automatically yield a saleable product demo, regardless of glass, background or camera effects. The live old server is still deployed and must not be confused with the clean main tests. The fallback website-preview recording is 25fps, silently resampled to 60fps, and produced overly static, silent output. We have NOT fixed native60 general public capture, the present story-discovery quality, model reliability, or product-value direction. **No customer-ready accepted film. Zero owner-approved premium films.**

**Next honest step:** test the exact production-deployment change under explicit rollout controls and upgrade native60/verified-action capture through a genuinely action-rich public URL; do not promote research-only B-roll or claim arbitrary-URL autonomy.
