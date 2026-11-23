# Stagehand + existing Gemini: live public product discovery and film proof (2026-11-23)

**Repository:** Davemafy/sauce-vids, main only. **Environment:** recovered existing persistent Vultr worker. **Owner key correction:** the Gemini key already exists in the root-protected `/etc/sauce-url2video.env`; the running `sauce-url2video.service` has it in its process environment. The previous missing-key claim reflected only the isolated development-shell environment, not production configuration. The existing key was read only in memory for the owner-authorized experiment; its value was never printed, stored in output receipts, or committed. The service's configured model `gemini-3.1-flash-lite` was reused.

## Genuine browser-agent study

Stagehand Python 4.4.0 runs in the isolated `../.sauce-stagehand-venv` and calls Gemini `observe` against the actual public page. First negative round: cssgradient.io returned navigational labels, animista.net and neumorphism.io returned no usable local workflow. None were forced through Sauce as fake product interactions.

Root issues identified and repaired:
- SDK `observe(timeout=35)` means 35 **milliseconds**, not seconds; explicit 35,000ms budget now used.
- Strict first-party domain policy accidentally blocked legitimate apex/www redirects. Scout now allows only the URL's apex and its www counterpart; any other host remains refused. Capture's own post-click origin guard now makes the same narrowly bounded exception, never http downgrade, foreign origin or arbitrary subdomain.
- Model was being asked to rank navigation links and selected `Browse` rather than real product actions. Scout now considers only separately observed, allowlisted local buttons/tabs/sliders. Any unmatched/ambiguous selector or generic site navigation remains rejected. The model cannot invent selector/action/state.

Second live model round with same configured key:
- `https://brimble.io/`: Gemini identified **Connect your agent**, matched only existing Sauce inspected control ID `a1`, independent real Playwright `probe_public_action` verdict `visible_outcome_candidate`; actual DOM change true, changed-above-baseline 0.8051 and genuine result rectangle 400×360 (0.15625 viewport fraction).
- `https://www.heroui.com/`: Gemini identified **Switch the preview to dark mode**, matched inspected control ID `a11`, independent real probe `visible_outcome_candidate`; actual DOM change true, changed-above-baseline 0.35679.
- `https://seal-verify.vercel.app/`: no local action chosen by model. No action faked.

## Actual exported diagnostic films, not premium approvals

Each model-selected ID was replayed via Sauce's existing independently inspected source plan, after the verified proof, with the real `backend.live_capture` then `backend.live_render` binaries, keeping raw source truth. This was a manual private continuation from the saved real Gemini observation receipt, **not** a claim that production Studio automatically invokes the model or that a fully autonomous end-to-end job was completed.

- **Brimble:** initial genuine capture **failed** to record the button because the legacy `urlsplit(page.url).netloc != urlsplit(input).netloc` rejected the site's legitimate `brimble.io → www.brimble.io` canonical redirect, even though the live DOM probe passed. Fixed this root cause with safe exact apex/www equivalence. Fresh HIGH quality Chromium capture had genuine `a1` click, real public dialog and timestamped `click` / `state_change` event: 1920×1080, DPR2, source SHA256 `fc7b03e6220f283761f80f9f9d93362a948f7b555ccf71ec57adf9339a796237`. Final actual MP4 SHA256 `6fa6c42faf337ec0e1e1cd79b71bfd54a660aca5d044a6b1f911775c71a65f17`, 6.250s H.264 1920×1080 CFR60, complete FFmpeg strict decode PASS. Diagnostic private path `../.sauce-stagehand-private/film-brimble-live-20261123/export/master-1080p60.mp4`.
- **HeroUI:** fresh HIGH quality genuine `a11` click, original source SHA256 `f6d63fefdfb7ffd94693fc43f66918701fe362071390fb5296604b19640f321a`, source 1920×1080 DPR2. Final actual MP4 SHA256 `52b3c3e7ad5e8ff24602566c480d32f791971153ad50cadea031c39c8b29534f`, 8.733s H.264 1920×1080 CFR60, full FFmpeg strict decode PASS. Diagnostic private path `../.sauce-stagehand-private/film-heroui-live-20261123/export/master-1080p60.mp4`.

**Creative verdict: REJECT BOTH.** Opened fresh encoded 6-frame Brimble and 9-frame HeroUI contact sheets, not just green manifests. Both use the **legacy floating-browser** compositor, not the fixed blue-cloud Phase 2 studio grammar. Brimble has too much whitespace and a small dialog; HeroUI is mostly broad website scrolling with a tiny dark preview. These are not convincing value demonstrations, and the browser source records at 25fps, so nominal 60fps exports **duplicate/resample original frames**; they do not satisfy native60 motion. HeroUI had no source-specific editorial event despite the legitimate real action. The main constraint is now semantic film direction, native source continuity and legible result framing, not credential availability.

## Safe next step

Keep Stagehand optional and source-verified. Before any customer release, direct two real source-verified actions into the existing Phase 2 60fps event/camera compositor with actual camera grammar: contextual overview → genuine cursor → meaningful action → readable detail / payoff → short hold → release. Inspect encoded full-resolution frames and 390px phone viewing; explicitly reject tiny UI, weak story, repeated frames or missing source-true evidence. Do not represent this diagnostic as a premium approved film. No new infrastructure, branches, credential publication, model subscription, or Studio deployment.
