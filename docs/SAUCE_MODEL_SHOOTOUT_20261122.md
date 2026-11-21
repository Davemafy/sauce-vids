# Sauce model shootout — 20 candidates, six rendered films (2026-11-22)

**Branch:** GitHub `main` only. **Environment:** existing persistent 8-vCPU/16GB Vultr DevMCP worker; actual Recode public demo captured and independently verified earlier. **Commercial film acceptance:** **0 / 6**. This is owner-authorized inference R&D, NOT an unattended production URL feature or a provider endorsement.

## What was tested

User asked to try all available model alternatives: Vultr Serverless Inference through the already owner-configured protected Refit environment, plus the existing configured Sauce Gemini API. The live Vultr `GET /v1/models` returned 33 models; 17 plausibly text/generation-compatible IDs were tested via chat completions. Other catalog models target image, audio, embeddings, re-ranking and moderation and were not treated as candidates for a text film plan. Three Gemini configurations were probed too: **20 distinct candidate IDs**.

**Claude wasn't tested:** no configured Anthropic Claude API access for this runner. **Inkling 2 Mini wasn't tested:** absent from the Vultr catalog; 16GB shared Sauce VM is not a proven suitable local execution target. Neither model can be given an invented score.

**Fair inputs:** a natural founder request with the same bounded observed Recode public pages / HTML editor / visible local preview, followed independently by the **same** native 4.9s Recode source-video event geometry, truthful before/after and exact Sauce `sauce-film-plan-v1` camera contract. No candidate chose a new fake result or clicked a remote website. The film-director stage used **text-only identical evidence** for each model, not video-multimodal advantage for Gemini; the original real browser video was rendered later from source-pinned plans.

- Original captured Recode source `1920×1080`, CFR `60fps`, **294 actual source frames / 4.900s**, SHA256 `1b7b3b58948601e81e7dc415167c9ca5e1a06d501eb518d764803aecc35aef77`.
- Authoritative action/result manifest SHA256 `1768f688da06e9b6d0916d1c6f4759f3c10750162b90cd9bacc74f4713d714a8`.
- Recorded browser edit starts at **2.2775s**; first visible changed heading from genuine encoded source appears at **frame 152 / 2.533333s**. `Hello, Recode` becomes `Instant Browser Preview` in a sandboxed, browser-local iframe. No authenticated code run, save, cloud deployment or email occurred. No private user project, HAR or credentials were given to a model.
- Model JSON validation is mechanical and independent: exact source/video SHA, manifest SHA, 4.9s duration, camera-anchor allowlist, verified result onset, original Sauce motion-velocity and source-rectangle clipping gates. Source/event/iframe content must NEVER be regenerated or retimed to rescue a model.
- Each model was given **at most one identical corrective prompt** containing its rejected plan plus deterministic validator error. A correction passes only if the original renderer independently validates it. No manual timing fix was included in a model's credited result.

**Input caveat:** The original story-stage observed packet used an illustrative HTML wrapper around the genuine `<h1>Hello, Recode</h1>` phrase. This wrapper was NOT a verbatim source-file dump. All story candidates saw the same packet, but it limits absolute source-provenance evaluation. The retained script now supplies only the exact verified heading excerpt for future runs. The camera test used only verified source and manifest data throughout.

## Provider trial receipts

Three distinct experimental stages were recorded to avoid misreading an API failure as a creative failure:

| Configuration | Story calls | Usable story replies | Camera calls | First-pass valid camera plans | Correction calls | Valid corrections |
|---|---:|---:|---:|---:|---:|---:|
| Default provider reasoning | 20 | 6 | 12 | 0 | 0 | 0 |
| Vultr reasoning disabled; Gemini standard | 17 Vultr (Gemini story separately in first row) | 7 Vultr | 20 | 1 | 7 | 3 |
| Selected Vultr models, reasoning effort minimal and 256-token budget | 4 | 4 | 4 | 1 | 3 | 1 |

These are **request counts**, not unique model counts per row; the 12 default-reasoning camera requests were NOT the full 20. First low-budget aborts were also retained privately. This experiment made multiple paid API calls; no account-level transaction ledger or USD bill was retrieved. Only returned token-usage receipts can be audited, and the usage totals omit some truncated responses that did not provide usable content. There is no claim that failed calls cost $0.

The most important practical insight: **Vultr's reasoning controls mattered.** At default effort, several models repeatedly consumed their `max_tokens` allowance without a final answer. With `reasoning.enabled=false`, DeepSeek, Qwen, GLM 5.2 and MiMo returned usable replies quickly. GLM 5.3, GLM 5.3 Flash, MiniMax M3.1 Flash and Muse Glimmer needed the separate `reasoning_effort=minimal` and `reasoning.max_tokens=256` profile. Treat the tuned setting as a separate inference configuration, not an apples-to-apples claim against another model's default.

Six catalog IDs returned HTTP 400 for the normal chat request: `auk`, `auk-flash`, `clef`, `clef-flash`, `d3`, `minimax-h3`. These errors do not establish poor model intelligence; the specific endpoint/payload is unsupported or unsuitable. Gemini 3.1 Pro Preview repeatedly returned **429** and Gemini 3.7 Flash intermittently **503** or truncated before a valid plan, so neither produced an approved competing film.

### Model-by-model admission

| Model | Founder understanding | Camera-plan admission | Render |
|---|---|---|---|
| **DeepSeek V4.1 Flash** | Strong honest local-preview scope, no fake deployment | Valid after 1 correction, Vultr reasoning off | Yes |
| **GLM 5.2** | Honest browser-local editor pitch | **Valid first try**, Vultr reasoning off | Yes |
| **Qwen 3.8 Flash Next** | Critically noted the public demo is too thin for a premium launch film | Valid after 1 correction, Vultr reasoning off | Yes |
| **Gemini 3.1 Flash-Lite** | Correctly found the editor/preview action, but some wording overstated “real runtime” | Valid after 1 correction | Yes |
| **GLM 5.3** | Accurate, evidence-aware story, explicitly rejected fake Run/Deploy | Valid after 1 correction, 256-token reasoning cap | Yes |
| **MiniMax M3.1 Flash** | Honest browser-local preview limitations | **Valid first try**, 256-token reasoning cap | Yes |
| Qwen 3.8 27B, MiMo V2.6 Flash/Pro, Raon 1 Mini | Found real editor; Raon additionally suggested an unverified Run action | Still rejected after one allowed camera correction | No |
| GLM 5.3 Flash, Muse Glimmer 30B | Good bounded-reasoning stories | Still rejected after correction | No |
| Other catalog or unavailable models | No comparable valid experiment | No valid plan | No |

## Six actual encoded films

All six share the precise same genuine 4.9-second recorded pixels, pointer track, verified action/result onset and original bounds. No fake overlays, synthetic interface or narration. Each was validated with the original Sauce renderer, actually encoded to **H.264 1920×1080 at 60fps, 294 frames**, individually FFmpeg full-decode verified. Different output hashes prove the camera treatments were genuinely different, not reused files.

| Model | Film SHA256 | Resulting direction / inspected defect |
|---|---|---|
| DeepSeek V4.1 Flash | `fa3faab07a7e03d009ac6d48cdf6a9f1e16609dcb244b5ed88dfb58929156f18` | Moves from editor toward preview, but result becomes prominent too late |
| GLM 5.2 | `b2b641c68b193332c33fc4e2105cb5cbdf6b49b946a17ad32c5c6159e8d0f904` | Technically safe; barely visible 1.0×→1.077× whole-page drift, weak artistic direction |
| Qwen 3.8 Flash Next | `82d62aaa58c91c79f7e9ee3432d097b8faf0b4bd15dfe0986df9547789338ce1` | Clearer editor→preview emphasis, though mobile labels are still tiny |
| Gemini 3.1 Flash-Lite | `7367650f566da0d17e50e0fe65001df5e58cf63039fb7134c26f8cafa72611fb` | Similar editor→preview move; no decisive visual advantage over Qwen |
| GLM 5.3 (tuned) | `8306d6a3a972640ed929917e3364ee3e2c227d833017fe0bf6b3b6e8416a7985` | Purposeful staged cause→result, still small |
| MiniMax M3.1 Flash (tuned) | `4e228d5cb9a51760e71891ee174bcb828342c540f90fbaca16d270b5888efdd9` | Valid first time, measured slow result push; lacks a strong opening |

**Owner-only signed review:** [Play all six model films](https://devmcp.davemafy.xyz/sauce-expiring-review/tweakcn-20261120/sauce-sixmodel-recode-4c965e029d3038c1f31d/index.html?md5=ijRJIgH538tk5YCE1WI9AA&expires=1795907856). Link expires **2026-11-28 23:17:36 UTC**. The private review page contains no raw capture, user data, API keys or unpublished application code. Six model clips were opened from actual encoded frames and inspected on **366px phone-size contact sheets** at real before/action/result timestamps. All six videos were additionally played and sought through the signed website in Chromium at **1280×720 desktop and 390×844 mobile**: **12 / 12 video playback checks passed**, zero JS page errors and zero horizontal overflow. Phone player is ~362×204px. These successful playback checks do not imply the tiny source text became readable.

Compared with the source-true Screen Studio reference in `docs/screenstudio-study.md` (measured ~1.62× motivated push/release and distinct meaningful actions), all six films remain **creatively rejected**. They begin too static, show excessive website chrome/footer context, contain an instantaneous browser textarea `fill` rather than believable visible typing, lack an interesting second action or substantial payoff, and keep essential source details unreadable on phones. Moving the camera over an undifferentiated public demo is not a substitute for a better real feature.

## Engineering result and next choice

**Validated:** 20 models probed, configurable Vultr inference works without loading the 16GB CPU worker with model weights, genuine source-pinned JSON compiling, nontrivial different camera renders, faithful recording, source/frame SHA checks, 1080p/60 encoded output, desktop/mobile playback, private signed review and auditable per-call receipts. The benchmark runner is opt-in `scripts/experiment_model_shootout.py` with no production URL queue integrations; provider keys are read from the already protected host environment, **never written into the repository or model responses**.

**Not validated:** any model independently directing a premium launch film; Claude superiority; Inkling viability on this hardware; arbitrary-URL autonomous customer-ready output; provider-account charges from credits; actual Recode backend execution; price/quality dominance with statistical confidence from one source. Green tests and a 4.9-second successful video are not premium acceptance.

**Working selection for the next real source:** **Qwen 3.8 Flash Next or DeepSeek** for honest research at Vultr credit-backed pricing; **Qwen Flash Next / GLM 5.3 / Gemini Flash-Lite** as competing camera directors. MiniMax M3.1 Flash deserves a second-source reliability test because its first camera plan passed and remained grounded. Use 1–2 owner-authorized high-payoff public product actions with real visible state changes, native text framing, no fake server claims, and the same *actual encoded film feedback loop*. Do not preselect an overall winner until at least another product type is tested.
