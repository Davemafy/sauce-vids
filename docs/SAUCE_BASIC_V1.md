# Sauce Basic — deterministic website-tour contract

## Cross-site QA and real capture wall-budget

The private allowlisted preflight tested ten public websites with at
most two pages per site. Nine initially produced bounded manifests,
and Sentry's safe root-to-/welcome redirect was fixed and retested
separately. This is NOT a ten-film visual acceptance matrix.

Ghost's actual 53.833s native-1080p 25fps homepage video exposed six
incomplete visible images at one viewport. It is NOT quality approved.
A real Ghost rerender with bounded image decode still reported incomplete_visible_images and lazy_discovery_step_limit. Remains low confidence and NOT approved.

Resend's 131.850s native-1080p 25fps source exceeded its 38.728s
plan because one wheel interval blocked for 41,957ms. Marked
low confidence and REJECTED for pacing/economics. Source-true
does not mean commercially acceptable. Added a wall-time budget
that refuses runaway browser captures between wheel calls:
min(180s, max(24s, plan_seconds*1.65+12s)).
This check does not interrupt an individual stalled browser call.
Real 60fps unique source, visual approval on three different sites,
worker network isolation, data retention and cost-based pricing
remain required before an arbitrary-URL launch.

## CURRENT: Native Sauce Basic private-pilot proof — 2026-11-19

The current implementation reuses the EXISTING Playwright continuous
Chromium recording infrastructure, rather than screenshotting every output
frame. It uses the established, SHA256-pinned sauce-film-plan-v1 JSON
compositor contract for future upgrades. No separate effects engine.

- Run: python3 scripts/basic_tour_native.py --experimental --url
  https://www.brimble.io/ --allow-host www.brimble.io --scope homepage
  --max-pages 1 --max-minutes 3 --out /private/output
- Default deterministic website coverage is homepage plus nav destinations,
  with an optional all-reachable scope and explicit bounds. No LLM, fake
  clicks, form submits, login or unrestricted links.
- Native source capture is at a genuine 1920x1080 CSS viewport, DPR2.
  Browser recording helper emits VP9 WebM at 25fps, and FFmpeg creates an
  H.264 CFR60 master by RESAMPLING existing source frames. This is NOT
  native-60fps footage nor native 5K; never imply otherwise.
- Per-page real wheel events, actual DOM text-aware cursor parking, bounded
  image/skeleton/known-chat/consent checks, honest low-confidence flags,
  independent verified media receipts, and MP4 chapter metadata.
- Each scene emits a genuine film-plan JSON with its source media and
  capture-manifest SHA256. The plan is validated by Sauce's existing
  film_plan.load_film_plan; cursor mode none means no SECOND cursor is
  composited on top of the existing recorded source pointer.
- A public user URL endpoint is intentionally BLOCKED. The CLI accepts
  only explicitly allowlisted test hosts. DNS-rebinding and private-IP
  defense need hard network egress isolation before launch.

Verified owner-review-only THREE-PAGE Brimble master:
https://devmcp.davemafy.xyz/sauce-motion-phase2/basic-native-20261119/master-1080p60.mp4
SHA256 6d75f34c4b7ac660235d0fec451ca2e81595db160b831faf847beb6b8b67064b
Visual review contact sheet:
https://devmcp.davemafy.xyz/sauce-motion-phase2/basic-native-20261119/contact-sheet.jpg

The master is 172.850s, 1920x1080 H264, 60fps CFR presentation from
25fps browser source, 10,371 frames, 3 MP4 chapters at 0, 82.517 and
109.000 seconds. Real public-source Brimble homepage, Agent and Sandboxes
pages; no fake product interactions. The video hash matched the static
host copy, HTTP 200 and byte-range 206. Full FFmpeg decoding passed.
Chromium video playback and seeking passed at desktop 1280x720 and
mobile 390x844. Visual contact samples and playback screenshots inspected.

Dry-run versus actual encoded length:
- Homepage 57.091s -> 82.517s (drift, not creative acceptance).
- Agent 24.474s -> 26.483s.
- Sandboxes 45.093s -> 63.850s, marked low confidence for >20% drift.

This is a deliberate 3-page cap. Other Brimble navigation pages, such
as Pricing and Blog, were not included. No claim of exhaustive coverage.

Quality caveats: real filmed sections have flat but recognizable framing.
Some source text is tiny in mobile portrait preview; timing still drifts
on browser-heavy pages; source frames are only 25fps; known chat widget
suppression and consent visibility checks are not universal; scroll-linked
fades, lazy sections, and text/cursor overlaps on all arbitrary pages
remain subject to manual review. This is a technical multi-page acceptance,
NOT three independent approved product films and NOT revenue proof.
No Studio, advanced motion or production API code was changed.

The current Basic suite includes 33 passing focused pure and Chromium
tests, including false skeleton/image detection, hover nav, cursor
occlusion, opacity settling, chapter metadata, native source geometry,
and actual H264 video QA. Ship gates remain: visually approve real films
from three different products, ten-site adversarial matrix, verified
ownership/rights and abuse policy, hardened network isolation, durable
job queue, retention, customer feedback and cost-based export tiers.

---


Status: first implementation slice, NOT a released video, production URL endpoint, or quality-approved film. Preserve existing Phase 2 and Studio systems.

## Product promise and decisions

- Default: homepage plus same-origin header/nav/dropdown pages. Public URL in, plan out. No AI inference or user-authored per-site script.
- Optional full tour: safely reachable same-origin pages within explicit page, depth, height and wall-clock limits. A coverage manifest lists skipped, blocked, capped or failed pages. Optional short cut is generated from verified segments and never replaces full coverage.
- Discovery precedes recording. The customer sees observed page count, expected duration range, excluded scope and eventually a benchmarked cost. Never display invented price estimates.
- Same-page hash links are validated as actual DOM IDs and become in-page chapter anchors, not duplicate pages; missing IDs get unresolved_anchor. External links, GET links with possibly destructive paths and query-driven route expansion are skipped.
- Independent page segments use clean hard cuts, a neutral cursor reset, consistent capture viewport and source-true titles. Do NOT fake navigation clicks between segments. MP4 chapter metadata should mark each page and real anchor; no added branding or fake UI.
- Default film 1920x1080 H.264 at 60fps, captured from a 1280x720 CSS viewport with DPR at least 2; silent by default. 4K/5K only after real compute/memory/quality benchmarks. The proposed private-retention policy is seven days, NOT deployed storage lifecycle.

## Contract and shared dry-run planner

The code is in scripts/basic_tour_planner.py and has schema sauce.basic.tour.v1. Contract fields include root_url, scope (homepage/navigation/all), max_pages (default 12, cap 50), max_depth (default 2), max_minutes (default 10), profile (relaxed/balanced/quick), width 1280, height 720, fps 60, audio silent, transitions hard_cut, chapters metadata and retention_days 7.

The *same* wheel_steps and hold_seconds values used in preflight must drive the eventual recorder: no separate animation easing. Per scroll distance D (CSS pixels), use the quintic smootherstep E(u)=6u^5−15u^4+10u^3. Total duration T must be at least the greater of 1.875 D / V and sqrt(5.774 D / A). Balanced V=800 CSS px/s and A=1200 CSS px/s squared; Relaxed scales by 0.68 and Quick by 1.2. Wheel deltas are emitted at 30Hz and must be sent through actual Playwright mouse.wheel with an accurate recording clock. Section holds use clamp(0.65+0.032×min(words,120),0.6,4.0) seconds with profile multipliers 1.35, 1.0 or 0.8. These are provisional film-editing parameters, not owner-approved pacing.

Preflight reports a bounded estimate range and source fingerprint. The recorder must recheck source/geometry immediately before filming; a changed page invalidates the estimate until replanned. An infeasible short-cut duration must reject or remove whole verified sections, NEVER compress motion/text into an unreadable blur. Show the customer the range before consuming paid compute.

## Browser behavior for the next implementation slice

- Trigger lazy content by real wheel events; wait for meaningful images to decode, skeletons to disappear, and visible layout/content to stabilize. No universal networkidle wait.
- For scroll-jacked/pinned sections, verify visually settled states after scrolling and hold before continuing. Detect occluded content under sticky navigation.
- When idle, move the single real cursor to a neutral non-text area; compare planned cursor position against DOM text rectangles. Never leave it over a heading.
- Apply presentation-only CSS to known optional chat widgets without deleting their real DOM. For cookie banners, do not auto-accept tracking; only choose reject-nonessential where allowed, otherwise report the obstruction.
- No automatic form submissions, arbitrary tab/button clicks, sign-ins, purchases, downloads or destructive requests in Basic. Preserve genuine source interactions only.
- If some pages fail, return remaining verified segments and a manifest with precise skip reasons. Never fabricate missing scenes.
- Audio silent by default. Optional licensed music and Foley are separate user choices.

## Public-service security boundary

The experimental scanner in scripts/basic_tour_discovery.py reuses capture_safety URL and request checks, same-origin filtering, robots.txt handling, an identified user-agent, bounds and a crawl interval. It is ONLY a local feasibility probe. The current cached DNS check plus browser route guard do NOT solve DNS rebinding or every redirect-to-private-IP attack. Before accepting arbitrary customer URLs, isolate browsers in network-restricted containers, block private/link-local/metadata egress at the network layer, validate redirects, disable downloads, impose per-tenant CPU/RAM/time/network caps and rate limits, and define legitimate-use, ownership, consent, privacy and deletion policies. Respect robots.txt unless an explicit verified-owner policy later permits exceptions.

## Measurable acceptance gates

1. Coverage: each selected URL recorded or explicitly listed with a reason in final manifest.
2. Film: actual 1920×1080 constant 60fps output, frame count matching the committed timeline, complete FFmpeg decode. Chapter cut points align with real encoded frames.
3. Load: no obvious unrendered skeletons, blank hero regions or blocked content in sampled frames; cross-check with DOM loading indicators and pixel analysis.
4. Motion: scroll peak velocity and acceleration within 2% of declared profile bounds, no discontinuity at section holds, source-backed cursor locations and no resting cursor overlapping DOM-readable text.
5. Legibility: output-resolution human review, supported by selective OCR; OCR is not a stand-alone pass.
6. Cost: measure actual worker memory, CPU, wall time, media size and cost per delivered minute. No speculative 5K promises.
7. Breadth: at least ten unseen public sites including pinned hero, SPA and hash navigation, infinite scroll, sticky UI, lazy imagery, consent wall, chat widget, bot-blocking and cross-origin links. Automated tests never replace watching the actual movie.

## Verified prototype evidence — November 18, 2026

- scripts/basic_tour_planner.py implements deterministic planning, safe-ish route filtering, nav/anchor grouping, bounded wheel/hold plans, coverage reporting and source fingerprints. It is NOT a browser-to-video adapter.
- scripts/basic_tour_discovery.py experimentally scans public DOM with Playwright, obeys robots where reachable and emits a preflight manifest; not production-network safe without stronger egress controls.
- An offline browser fixture and pure unit tests passed. A live Brimble preflight (www.brimble.io) observed homepage, /agent and /sandboxes at max_pages=3, with 10,159, 4,190 and 7,798 CSS-pixel page heights. Dry-run estimate: 226.685 seconds, range 192.7–308.0 seconds. It skipped 22 external links and 22 page-limit routes. The manifest remains private; no Basic MP4 was rendered or public endpoint deployed.

Next: source-verified page recordings and a segment assembler, plus hardened network isolation and actual playback QA. Do not call this a launched Sauce Basic feature.

## Verified estimate and offline film experiment — 2026-11-18

Old live Brimble preflight: homepage 10,159 CSS pixels, 35.28s of scrolling plus 73.63s of holds (32 stops); Agent 4,190 pixels, 14.44s scrolling plus 31.32s holds (17 stops); Sandboxes 7,798 pixels, 23.70s scrolling plus 47.61s holds (20 stops). Total 226.685s, of which 152.56s or 67% were holds. The original manifest recorded 22 external-link skips and 22 page-cap skips; these are link entries, NOT unique page counts.

Cause of slow estimate: the planner inserted both viewport-grid holds and section-top holds, which duplicated pauses around nested DOM sections. Revised shared planner uses one stop per viewport band with density-based holds. New real Brimble preflight estimate, same three routes: homepage 66.7s (26.1s scroll + 40.6s holds), Agent 31.2s (9.9 + 21.2), Sandboxes 61.7s (20.0 + 41.7); total 160.247s, range 136.2 to 218.3s. This is still a PREVIEW, not a validated live-site recording.

The experimental OFFLINE fixture recording uses tests/fixtures/basic-tour-offline.html, not a Brimble or customer site. The proof in scripts/basic_tour_segment_experiment.py dispatches the same real Chromium wheel deltas from the planner and encodes captured source pixels into a film. Planned 12,246.635ms versus encoded 12,250ms (+0.0275% because of whole-frame rounding); actual 735 H.264 1920x1080 frames at 60fps; FFprobe and complete FFmpeg decode pass. All 146 scheduled Playwright wheel events were dispatched, and final measured scrollY=1629 exactly matched max scroll 1629. The host spent 66.854 seconds to render 12.25 seconds, or ~5.46x realtime. This is a useful wall-time benchmark but insufficient to price 4K/5K.

12 frames were visually inspected from 0.3 to 12.0 seconds: source text is readable at native resolution; lingering holds are still conspicuous, navigation text is tiny at phone preview scale, and the custom Sauce cursor is NOT implemented in the experimental film. This is technically verified but NOT a visually approved customer video.

Timing agreement between the plan and encoded clip is partly BY CONSTRUCTION: the recorder intentionally uses the planner's exact frame count. More meaningful independent checks are event dispatch, actual final scroll offset, FFmpeg full decode and wall time. No claim that the preflight will predict real-world changed websites, lazy media, scroll-jacked animations or bot blocks within ten percent.

The experimental crawler is now restricted to an explicit allowed test host using --allow-host plus --experimental. It still needs actual network-level SSRF/redirect/DNS isolation before public inputs. Live-site recording, lazy-content/readiness and skeleton gates, cookie and overlay policy, scroll-jacked visual settling, cursor text exclusion, chaptered multi-page assembly, R2 retention and ten-site visual acceptance are NOT implemented.

## First real public-site homepage film — 2026-11-19, QA ONLY

The actual Brimble marketing homepage (https://www.brimble.io/) was recorded
through a strictly allowlisted experimental Playwright/Chromium capture using
the deterministic planner's real mouse.wheel trajectory. This uses existing
Vultr DevMCP compute; it does NOT deploy a public URL-to-video endpoint,
run paid AI, or authenticate to Brimble.

Verified:
- Preflight page height: 10,159 CSS pixels. Source re-read at recording:
  10,159 CSS pixels; 720 CSS pixel viewport; intended total scroll 9,439.
- Planner: 66,688.888ms and 794 wheel events. Real browser received 794/794.
  Final browser scroll position 9,439/9,439 CSS px, exact bottom reached.
- Actual MP4: 66.700s, 4,002 1920x1080 H.264/yuv420p frames, exactly
  60/1 nominal and average frame rate, no separate audio. Complete FFmpeg
  decode verified. The encoded duration differs from the planned duration by
  +0.0167%, one-frame rounding; the duration match alone is not independent
  validation since the script uses the planner's frame count.
- Measured worker capture and encode wall clock: **835.379 seconds**
  (approximately **12.5x the movie length**). This is NOT viable proof of
  cheap/fast 5K generation. Native source capture dominates CPU usage.
- Public owner-review-only QA link (source is a public marketing page):
  https://devmcp.davemafy.xyz/sauce-motion-phase2/basic-qa-20261119/brimble-homepage-1080p60.mp4
  SHA256 3b94775a927e148d48a4a3f1b35a28f71bdbe915ba65e5e1d58ae3206098aa7d
  Static host copy matched source SHA256; HTTP 200 with MP4 content-type
  and byte-range 206. No HAR, private session log or credential was published.
- Contact sheet manually inspected at 16 times across 0.3–66.2s:
  https://devmcp.davemafy.xyz/sauce-motion-phase2/basic-qa-20261119/contact-sheet.jpg
  Full-size frames checked at 0.3, 12.0, 42.0 and 47.0s.
- Existing previous Brimble 3-page estimate after removing redundant holds:
  160.247s total (homepage 66.69s, Agent 31.17s, Sandboxes 61.69s).
  The cap was THREE visited pages, not all Brimble main-nav pages:
  Pricing, Blog, several product routes remain unvisited. Original 44
  skipped LINK ENTRIES included 22 external and 22 page-limit entries,
  the latter representing approximately 11 unique URLs duplicated across
  navigations. No full multi-page film exists yet.

Human film QA (REJECTED as a paid-customer Basic master):
- At 0.3s the large source bee dominates and the hero headline starts near
  the lower boundary; opening composition does not introduce the offer well.
- At 12.0s, scroll-driven copy is partly faded during a transition. The
  browser action is genuine, but the planned hold is not settled on a
  legible state; this fails the scroll-jacked/pinned animation quality gate.
- At 42s and 47s source sections and native page screenshots overlap the
  viewport as the page scrolls. Text hierarchy is weak at mobile playback
  size; evaluate whether a later pause can settle these actual sections.
- A fragment of decorative bee imagery remains at the top edge in later
  frames. Investigate the true source animation rather than masking it
  blindly or fabricating UI.
- There is **no composited Sauce cursor**. Existing proven cursor semantics
  have NOT been integrated into this experimental scroll recorder.
- 16 viewport holds still account for about 40.6s of the 66.7s film.
  Pacing is predictable but contains dead time. Preserve legibility while
  finding fewer/more meaningful stops.
- Overlay/cookie-bubble cleanup is not implemented; sampled frames do not
  establish a comprehensive no-overlay guarantee.
- The recorded output is a flat, source-true website tour, not a directed
  SaaS-product workflow or an accepted premium film.

Other implementation improvements in this local isolated main checkout:
- Experimental crawler requires explicit --allow-host in addition to
  --experimental. Production DNS-rebinding/redirect/network egress isolation
  remains a hard launch blocker.
- Post-crawl skip summaries are recalculated after appending page-cap skips,
  including distinct capped-route counts; do not misreport link entries as
  unique pages.
- Header/nav hover-only menus are inspected without clicking; click-only
  menus are explicitly outside current automatic discovery.
- Twenty focused tests pass, including Chromium fixtures for lazy content,
  pinned hero requiring wheel events, bounded infinite scrolling, a visible
  unaccepted cookie wall, and hover-activated navigation.

Next work should prioritize speed of real source capture, settled-state
scroll pauses, intentional native cursor placement, loading and overlay
policies, single-page visual approval, then multi-page chapter assembly.
Do not expose an arbitrary-URL customer API, claim 5K economy, or treat
this technical success as human creative sign-off.

## Real cursor, overlays and loading QA follow-up — 2026-11-19

The prior 66.7-second Brimble homepage film was visually rejected: faded
scroll-linked copy, a poor opening, small text at mobile playback scale and
no custom Sauce cursor. The latest work explicitly targets those defects
instead of adding new visual effects.

- New scripts/basic_tour_quality.py measures real visible DOM text
  rectangles and rejects an idle cursor hotspot if the arrow's body
  intersects text. It also inspects visible skeletons, broken/incomplete
  images, known chat widgets and consent overlays. These checks are
  bounded observations, not OCR or exhaustive pixel-level readiness.
- scripts/basic_tour_live_segment_experiment.py now installs Sauce's
  existing known support-widget presentation CSS, collects initial and
  per-hold quality flags, and records measured cursor-safe placements.
  It never silently accepts a cookie banner. The modified long-form
  capture script has NOT been rerun end-to-end since this change.
- scripts/basic_tour_cursor_finish.py uses Sauce's ORIGINAL
  assets/cursors/reference-v15/black-rounded.svg artwork, not an invented
  cursor silhouette, and renders the arrow only in the video compositor.
  A real Brimble browser scan sampled 16 hold positions and 473 DOM text
  rectangles; chosen CSS rest spot (18,432) was collision-free at those
  sampled holds. This does NOT prove absence of text overlap at every
  intermediate scrolling frame or across future site versions.
- The initial cursor candidate passed nominal 60fps checks but was
  visually REJECTED: the FFmpeg command mistakenly mapped the original
  input stream, not the filtered output. Corrected to explicitly map
  the overlay filter output. Added decoded-frame pixel-change checks
  that fail if the output cursor is missing. Verified 463 and 468 changed
  cursor-region pixels at two timestamps, plus opened native crops.
- Public, owner-review-only corrected film:
  https://devmcp.davemafy.xyz/sauce-motion-phase2/basic-qa-20261119/brimble-homepage-cursor-rest-1080p60.mp4
  SHA256 e73aefdd90a1a47f89c037a782f922288b01afa639e8751f15d9a2c1ac4165a7
  H.264 1920x1080 60fps, 4,002 frames and 66.7 seconds. Full FFmpeg decode,
  matching copy SHA, HTTP 200 and HTTP range 206 verified.
- Twenty-four focused unit/Chromium tests passed, including cursor/text
  collision, suppression of known chat widget CSS without changing consent,
  visible skeleton detection, and broken image warning.
- This is NOT a commercially ready Basic film. Scroll-linked fades,
  per-frame loading guarantees, hidden/safe cookie policy, readable
  mobile composition, page-to-page chapters, public-worker network
  isolation, and runtime/cost hardening remain unapproved or incomplete.
  The visible stationary cursor is a parking proof, not realistic action
  animation. No 5K rendering economics claim is supported.

## First-glance review and Short Cut, November 19 2026

The user rejected the 172.85s three-page Brimble tour on first glance, despite full technical video verification. Comprehensive coverage and watchable opening are separate goals.

New opt-in scripts/basic_tour_shortcut.py uses source-hash-verified existing Sauce film-plan-v1 scene recordings to derive a separate short-cut JSON EDL and MP4. It does not capture a page again and does not replace Advanced rendering. The EDL selects original browser-footage clips, optional bounded source-pixel reframing and clean cuts, keeping the full verified tour unchanged. The optional strongest_hero hook uses objective visual contrast of real decoded first frames rather than a model or invented product state; it requires creative review before becoming a default. Durations are never fixed by speeding up unreadable text. Entire optional shots are omitted when a duration budget is infeasible.

Two experimental candidates were rejected: a 17.47s static slideshow, and a 20.90s cut still opening on a static bee hero. A third 20.90s / seven-shot candidate opens on the real Sandboxes code UI, includes source browser scroll, then shows Homepage, Agent and verified feature imagery before finishing on Brimble's real CTA. Live QA: https://devmcp.davemafy.xyz/sauce-motion-phase2/basic-hook-review-20261119/brimble-short-cut-1080p30.mp4
SHA256 c914857cbb2150301261df4d2661aea9238b3d307adff0c8fd02a76de698fae3. True 1920x1080 H264, 30fps output derived from 25fps Chromium source, 627 frames, 20.900s. Full decode, source hash verification, static host SHA and HTTP byte range passed. Visual frame review showed stronger initial framing but excessive static holds remain. This is NOT approved for release. The Sandboxes source timing error is retained as a low-confidence flag in the EDL receipt.

New tests cover source tampering, bounded shot selection, authentic highest-contrast hook choice and encoded output. All 40 focused tests passed. Public URL ingestion remains disabled until security isolation, page loading, overlays, ten-site hard cases, source FPS, cost and quality approvals.
