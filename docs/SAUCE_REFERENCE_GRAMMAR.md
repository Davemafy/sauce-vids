# Sauce Reference Grammar → Gemini Director → source-true film plan

**Status:** one reference converted from actual public MP4 samples; a local, privacy-reduced packet builder and regression tests exist. **No Gemini API call, paid inference, live Studio integration, production deployment or creative acceptance.**

**QUALITY CORRECTION (2026-11-19):** This initial Arcade recipe was only a 15-frame editorial impression, NOT 1:1 reference-quality data. The source has now been examined across all 2016 decoded frames; 10 strong cut boundaries are visually confirmed, but element tracks and independent motion reconstruction have NOT been completed. The reference MUST NOT be sent to Gemini production. See [SAUCE_REFERENCE_FIDELITY.md](SAUCE_REFERENCE_FIDELITY.md) for the new fail-closed contract. The packet builder requires the explicit research-only mode until an independently compared and approved reconstruction exists.

## Two JSON contracts, with a strict boundary

1. **Reference grammar** (`references/arcade-stack-by-ramp.reference.json`, `sauce-reference-grammar-v1`) is learned **offline** from a benchmark film. It describes shot purposes, measured/sampled observations, compositional principles, intentional timing and restrictions. It has **no authority over product pixels or source events**. Store source URL, SHA256 and what was and wasn't actually measured; do **not** commit the MP4 or still frames. The sampled Arc​ade source has public provenance but no implied license to redistribute its media.
2. **Director packet** (`sauce-director-packet-v1`) combines a small *style-only* subset of the recipe, an approved customer brief, **actual event** timestamps, measured DOM result/component geometry, source and sidecar SHA256, and allowable event anchors. `scripts/reference_director_packet.py` prepares it locally; it does **not** contact an API.
3. **Executable film plan** (`schemas/sauce-film-plan-v1.schema.json`) is an entirely NEW output the model proposes for Sauce's already-existing `scripts/render_event_video.py --film-plan`. Camera, timeline and isolated UI are anchored to this actual product's event ID, not the reference's. No copied reference UI, typography, claims, brand or absolute timestamps.

The public Stack by Ramp reference (SHA256 `7d22a17f97d3183cae73df90321f7be7943006d9bf7f4ecd7c2a79f15215bbbf`) was sampled at 15 timestamps from 0.6 to 65.5 seconds and reviewed in a contact sheet. The reference recipe records a recognizable progression: product orientation → task intent → concrete choice/approval → visible work → completion state → wider context. This is an **observed editorial pattern**, NOT a claim that exact cuts, easing curves or manual/automatic production processes were measured. Do not transfer an unverified action from that film to a new customer.

## Production design (not yet activated)

```text
References MP4s --offline review/extract--> curated reference recipes (JSON, analysis-only)
                                                                |
Customer URL + brief --> safe Chromium capture --> real events + frame hashes
                                                                |
                   select 1–3 matching reference recipes by event/outcome shape
                                                                |
                   local source-reduced Gemini request packet
                                                                |
           Gemini structured response: new sauce-film-plan-v1 JSON
                                                                |
     full local schema/semantic/geometry/time validator, reject nonexistent actions
                                                                |
      existing Sauce JSON compositor + FFmpeg --> actual 16:9 film
                                                                |
       frame-level visual QA (readability, cropped UI, story, source, sound)
           | reject + constrained JSON revision (bounded retry, same media)
           +-- approve only if independently reviewed
```

Use a small shortlist of proven *shot families*, not all 60 references on every request. The source event story selects a family: an actually recorded single slider change cannot support a six-step bank approval story. For a simple source, compress the reference grammar to **action → evidence → clear result hold**. For a multi-step source, the corresponding longer pattern may apply.

### Local packet generation (no cloud or inference)

```bash
python scripts/reference_director_packet.py --research-only \
  --reference references/arcade-stack-by-ramp.reference.json \
  --source /private/real-browser-source.webm \
  --manifest /private/events.json \
  --brief "Show an actual user changing the value and seeing the price update" \
  --seconds 10 --width 1920 --height 1080 \
  --out /private/gemini-director-packet.json
```

This packet is research-only and marked productionGeminiEligible:false; do not send it to Gemini as a verified example. The packet excludes the reference film's screenshots, text, source URL and branding, and it uses an anonymous style fingerprint and excludes the capture's raw event text, private URLs, source pixels, credentials and numeric product claims. It includes only allowlisted measured rectangles and source timestamps. **An actual external-model request still needs customer authorization for sharing their brief and sanitized capture facts.** Prefer a server-side key, no client-side model credentials. No private app session or raw capture gets sent by default.

### Gemini contract

Google documents both **video understanding** (useful for *offline* reference analysis) and **structured JSON output** (useful for *online* direction). For production, use a Gemini-compatible reduced schema for the proposed plan, but enforce the complete Sauce schema and runtime truth checks **after** receiving it; JSON well-formedness does not prove feasibility, source authenticity or cinematic quality.

**System rule for model:** "The reference is only a style example. You may choose shot order, bounded pacing, camera scale, focal point and supported layers. Only use anchors/times from `actualCapture.verifiedEvents`. Never invent a click, approval, value, result, field, screenshot, UI element or licensed media. Do not show a result before its observed timestamp. If the requested story cannot be produced from the evidence, return a declared insufficiency rather than fabricating one."

Do **not** make Gemini's output executable browser commands. Sauce's deterministic capture policy decides what interactions are authorized. For every returned camera/event/layer anchor, validate actual source geometry, hashes, event time, component visibility and safe margins before rendering. On visual failure, revise only the affected shot(s) against the decoded output, not by adding unexplained effects.

## What must be proved before flipping the live Gemini flag

- At least three independently reviewed reference recipes from useful *different* visual families, with evidence of actual observation (not AI-invented cut times).
- Two new authorized product recordings, different from the reference product, whose approved films reuse the recipes and execute end-to-end without manual code changes.
- Blind human publishability comparison with actual competitor footage; visible action/result at 390px, one correct cursor and no clipped component or invented behavior.
- Measure inference spend, retry count, video render seconds and review minutes per **approved** film. Start with a few recipes and a hard rate/cost cap.
- Keep existing `sauce-film-plan-v1` and main-only repo policy; this is a director atop the current engine, not a rebuild or a full launch-film generator.

**Key caution:** Good JSON descriptions of excellent references are not enough alone. What makes a film premium includes spatial placement, duration, optical motion and result legibility. Those must be measurable in reference source, represented by engine primitives **and** checked on the actual rendered MP4. A 100% valid Gemini JSON plan can still make a bad film.
