# Sauce — autonomous public URL → genuine recorded interaction → video (2026-11-21)

**Status:** New-source end-to-end technical proof from a public URL, executed on the existing persistent Vultr worker. **CREATIVE REJECT / not premium-approved, not deployed into a public customer ingestion pipeline.** This does not replace previously completed Sauce systems.

## Actual output and source

Starting from **only** `https://uicolors.app/generate/` and an explicit `uicolors.app` private test-host allowlist, a new isolated Sauce job autonomously:

1. Opened the real public website in guarded Chromium, discovered the genuine interactive controls, and tested up to eight safe display-only candidates in independent browser contexts. No account, form submission, export, purchase, or cross-origin navigation.
2. Measured true before/after browser screenshots plus DOM state and idle baseline; selected **Switch to dark mode** (appearance) and **Contrast matrix** (inspection) as separate, verified high-payoff roles. Pixel results during discovery were ~83% and ~57–65% on different sampled sessions. A separate tweakcn probe admitted **zero** actions because its observed tab changes were too small (around 0.58% and 2.48%); no fictional showcase substituted.
3. Recorded fresh Chromium on dedicated Xvfb with original CSS 1440×900, DPR2, native 2880×1800 at 60fps / 720 frames / 12.0 seconds using FFmpeg X11 grab and real mouse input. Measured **92 real source-clock pointer samples**, two real down/up clicks and observed browser state changes. No imaginary input, no altered website markup, no generated screenshots or user-credential activity. Original source SHA256: `dc1c48559b7bc842eba3ad405c44724dbf06bdc9e2d748da7495cfb0384a1dbd`; original browser-capture receipt SHA256 `234505b9eb59a75743f3051aa8219385a5bb7208393f93f94ed4658fbf443490`. Recorded canonical public landing URL `https://uicolors.app/generate/3aa65f`.
4. Independently accepted both using the existing SHA-pinned source receipt adapter, plus a new distinction between an authentic button click and a slider drag. Real event 0: press `2.189694` sec, release `2.310422` sec, confirmed result `3.181067` sec, genuine full-viewport color theme change. Event 1: press `6.230606` sec, release `6.334683` sec, confirmed result `7.444369` sec, new original contrast table `[977,396,1370.2031,1371.9844]` native source pixels. Original before/after source-pixel changed fractions: **0.75757** and **0.67908**. Fresh independent manifest SHA256 `90dddc0468c41e87fcf1b1f5bd58dbf11f9f7499b7c65ddcb26d066c143bde87`.
5. Generated the first film plan through a **strictly labeled deterministic source-event director** (NOT Gemini output). It uses only real original event times/bounds, source hashes, recorded pointer track, existing StudioStage/C2 motion primitives, and source-aligned 48kHz procedural Foley cues. Film plan SHA256 `c9bba74af78feb18842feff34e9616656f8f77dfcf4f4d165e7b1fbc9205d277`. Original strict renderer source validation and actual multi-event editorial preflight passed, covering both results and both Foley indices.
6. Rendered authentic H.264 **1920×1080/60fps, 720 frames, 12.0 seconds**, with **48kHz stereo AAC** and four original-event-locked cues. Both video and audio fully decoded. Exact MP4 SHA256 `0cfb86c4e0101747bb637355436982de5ded7f8aa22f248f32ab638c42684bcb`, private worker at `.tmp-urlscout/full-autonomous-url-v6/private-demo-1080p60.mp4`. Complete one-command output receipt at `.tmp-urlscout/full-autonomous-url-v6/run-receipt.json`. Total local URL→encoded-film time **100.88s** (one trial, not a measured distribution or production SLA).
7. Actual desktop1280×720 and portrait mobile390×844 Chromium playback/seek passed with no JavaScript/player errors. Actual source frames and film contact inspected near 0, .65, 1.6, 2.3, 3.3, 4.9, 5.8, 6.4, 7.7, 9.1, 10.4, 11.6 seconds. Private signed 72-hour review MP4 (verified HTTP200 signed and HTTP403 unsigned):
   https://devmcp.davemafy.xyz/sauce-expiring-review/tweakcn-20261120/sauce-uicolors-autodiscovered-12s-1080p60.mp4?md5=Ks0QFFQ-mxZCr88LAmTgGg&expires=1795536228

## Client's Refit-style creative JSON — the director's *intent* not proof

A separate uploaded example supplied the complete `sauce-creative-brief-v1` concept for an 80-second Refit film on X, including a hook, workspace, live run, comparison, trace, verified export, outro and voiceover. This is a **strong CLIENT STORY ASSIGNMENT**, not a valid executable `sauce-film-plan-v1`, not evidence of a new live run and not a way to derive nonexistent timestamps.

`scripts/client_creative_brief.py` strictly loads up to 28KB of UTF-8 `sauce-creative-brief-v1` client intent, validates the requested original source hostname, landscape, scene/action shape, and explicitly labels all narration, route suggestions, numbers and claimed outcomes as **unverifiedClientStoryIntent**. The existing `scripts/auto_direct_studio_film.py` appends it to its source-hash-bound packet only as a creative target and warns Gemini that the recorded source/video/event manifest *always* overrides user proposals. The preexisting `scripts/auto_public_ui_film.py` now accepts `--creative-brief-json` and passes this through to its existing model director. Typical private CLI:

```bash
python scripts/auto_public_ui_film.py --url https://YOUR-ALLOWED-PUBLIC-SITE   --allowed-host YOUR-ALLOWED-PUBLIC-SITE --out /private/new-job   --creative-brief-json /private/client-story.json
```

**Critical caveat:** This makes the *director input* richer; it does NOT give Gemini browsing tools or allow 80-second newly recorded multi-route workflows by itself. Current source-bound Gemini runner accepts <=30-second actual source, and the existing one-URL public action discovery CLI only allows narrowly verified reversible preview tabs. Refit's real refund-agent workflow can be long-running and make tool/inference calls; it requires an explicitly authorized separate recorder and verified run evidence, not an unchecked model-generated click list. This study has no successful provider call because the configured Gemini key returned HTTP429. Current 12-second UI Colors film is **deterministic fallback**, not Gemini-produced.

## Reusable code (main-only)

- `scripts/public_interaction_scout.py`: opt-in, bounded safe public browser probes with allowlist, real screenshot+DOM evidence, baseline idle-drift rejection, fail-closed actions, two independent semantic roles selected from actual visual payoff; no LLM needed for safe discovery. Does not claim generalized product understanding.
- `scripts/record_scouted_interactions.py`: native DPR2/60fps original Chromium/X11 recording of already-admitted genuine controls, new DOM-measured table/dialog/grid result bounds (not fake slider coordinates), true pointerdown/up, post-action screen-state and changed-pixel evidence, immutable original receipt.
- `scripts/verified_capture_receipt_adapter.py`: now preserves source-true click release semantics `start < end < t` vs legacy slider-change clock, refuses missing/forged releases; original Resend capture compatibility preserved.
- `scripts/source_event_director.py`: deterministic, versioned source-bound film plan fallback when provider is unavailable, clearly labeled `deterministic_no_model`; bounded 16:9 camera, verified source anchor frames and source-event Foley, no fabricated content.
- `scripts/public_url_to_film_experiment.py`: private **single CLI command** orchestrating discovery→two action admission→native recording→adapter→director→strict renderer→encoded supervisor with separate receipts and no auto-publish. Example:

```bash
python scripts/public_url_to_film_experiment.py \
  --url https://uicolors.app/generate/ \
  --allow-host uicolors.app \
  --out <new-private-output-folder> \
  --display :154 --seconds 12
```

- `scripts/quality_preview_supervisor.py`: source-SHA verified real theme changes/verified UI-state transitions can no longer be incorrectly counted as artificial editorial hard cuts, if actual source+render differences align within sampled times and preserve amplitude. In the v6 original source, mean frame deltas **166.779** at 2.3s and **77.759** at 6.6s; film corresponding **145.319**, **68.924**, with matching native source event evidence. Genuine *unmatched* cinematic cuts still fail.
- `scripts/auto_direct_studio_film.py`: provider HTTP400/401/403/404/413/**429** now yields safe numbered status and stops further retries, without persisting private response bodies or secrets. Live Gemini 3 Flash request with no reference returned **HTTP429**, after prior three similarly blocked calls with the Raycast study; zero valid new model JSON, do NOT imply any model-assisted film on this site.

## Human visual and creative verdict

**Technical proof succeeded. Film is still a creative REJECT.** Corrected source-relative encoded QA flags **REPEATED_OR_STATIC_FRAMES (68.1% of 10fps sampled adjacent frame differences below threshold)**. It does *not* reject the two genuine abrupt browser state changes as misleading edits. The film demonstrates real app theme switching and opening an authentic contrast grid, but has long motionless holds and relatively straightforward camera movement; the source app is small in the opening, and it does not match the polish/direction of independently researched Raycast and Jitter UI-motion reference films. The lens is a source-true film treatment, not independently layered art direction. The overall user promise of premium arbitrary-URL films remains unproven; quality-approved film count **0**.

This live trial is restricted to opt-in testing on the explicitly allowlisted public product. The guard is an application-level network request check and **not** production network isolation against all untrusted URL/egress routes or anti-rebinding attacks. Needs a hardened network sandbox, site permission/rights and scalable orchestration before any arbitrary external user URLs. No public self-serve capability, deploy/restart, paid infrastructure purchase, account login, protected session, secrets, private original screenshot, reference footage, or raw MP4 was committed to GitHub.

## Tests and preservation

- Entire Phase 2 suite on persistent Vultr worker: **413 passed, 10 skipped, 21 subtests passed** after the new synthetic source action/receipt and 429 fail-fast tests.
- Browser scout negative cases: unsafe submit/purchase/external actions blocked, two distinct results required, real changed pixels and independent DOM evidence required, no forged source cursor releases, source times and hashes exact, unmatched source cut rejected, synchronized real UI state change not mislabeled as editor cut.
- All compilation and `git diff --check` pass.
- Legacy Glass Loupe rendered with the updated source-code tree and was **byte-identical** to the existing reference, SHA256 `3df5b2391ef933a92b8198541ec9981649f115035d9e38dbd45991588653b10f`. Existing work untouched.
- No model-created premium shots or fake confidence claims. This is one **newly captured URL** proof plus one **rejected-by-scout** site; not an established multi-site commercial success rate.

**Next P0:** strengthen source footage/choreography such that a viewer experiences continuously readable movement and an editorial arc, not a static switch-and-hold. Test other real public products/geometry, actual safe access control under hardened egress and uptime, and demand three separate *owner-approved* original product films before paid public release.
