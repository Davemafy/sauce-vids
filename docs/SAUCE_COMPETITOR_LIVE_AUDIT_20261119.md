# Sauce competitor browser and film audit — 2026-11-19

**Scope:** Fresh, owner-directed competitive research on actual public vendor pages and publicly published media, with the existing Vultr DevMCP worker and one dedicated AgentMail inbox. No purchases, paid inference, production job/deploy, private customer credentials, outreach or circumvention of authentication. Findings distinguish firsthand tests, vendor claims and creative interpretation.

## Comparable URL → demo flow: DemoVisor

- Site: https://demovisor.com/
- Entered exactly `https://resend.com/pricing` into the free `Preview my demo free` form from Chromium. No account required. Preview resolved successfully.
- Returned title/description: `Pricing · Resend` / `Start for free and scale up to millions of emails with flexible plans.`
- The proposed video story had three sections: `Product overview`, `Sign up → first value`, `Resend`, with prospective navigation such as Pricing → Resend/Contact us and Sign up. No proposed pricing-slider control, before/after price or $20→$35 reveal.
- This tests **planning only**. It does not prove what DemoVisor's finished Resend video would render. The preview includes an ~11-second illustrative "taste", not a generated final Resend product film.
- Competitive advantage Sauce can attempt to demonstrate: verified small-control → large or important product outcome, rather than general homepage navigation.

## Legitimate free-trial access

- DemoBot: https://app.getdemobot.com/login offered an email verification flow. A verification email was delivered to a dedicated AgentMail benchmark inbox. An attempted authenticated browser step was blocked by tool safety controls. **No account dashboard, usable free credits, new video or editor journey was verified.** No bypass attempts.
- DemoVisor: URL preview verified without signup. No full account creation or finished Resend generation performed.
- Arcade free video endpoint: `https://try.arcade.software/` returned HTTP 403 Cloudflare **Error 1000 DNS points to prohibited IP** in real Chromium on Vultr (2026-11-19 14:55 UTC). This is a site configuration/error response for that request, not proof every visitor is blocked or a statement about Arcade's main domain.
- Clueso: no authenticated trial attempted in this exercise.

## Actual public competitor films downloaded and frame-reviewed privately

Do not commit raw video bytes or extracted frames to Sauce; use the publicly accessible vendor URLs below.

### DemoVisor — OpenSwarm walkthrough
- Public player: https://demovisor.com/share/26e3c4d6ce03dcb007cc4e09b019e7045dcc6f1e60b7ac55
- Direct media from the public video element: `https://demovisor.com/share/26e3c4d6ce03dcb007cc4e09b019e7045dcc6f1e60b7ac55/explainer.mp4`
- SHA256: `d3b2adecb403caf649423fe9d30a50feb1a6d28ce3fdc6ca1626356a4a91b85b`. H264 1920×1080 30fps, AAC 44.1 kHz, 62.000 seconds, 4,756,443 bytes.
- Inspected real decoded frames at ~0.5, 3, 7, 12, 18, 25, 35, 45, 56 seconds. Intro typography and logo → browser-looking homepage → product promise/feature cards → app-style examples/marketplace → CTA.
- Strength: cohesive narrative arc, recognizable brand, lightweight purposeful typography and packaging.
- Weakness: sampled shots spend substantial time on broad page or static marketing graphics, with small interface detail. These sampled frames alone do not prove that the action/narration represents live executed app workflows; do not label it fake.

### Clueso — Clueso Agents launch film
- Public player: https://www.clueso.io/showcase/clueso-agents-autonomous-product-videos
- Direct media: `https://publicassets.in.prod.clueso.io/showcase/4184415f0353c0a4eda1bdf580d9d74c/video.mp4`
- SHA256: `ea9c7d5cf00664f61b4a3576eb42630b66b1614dc5e9492cebc05b2d56018c5a`. H264 1920×1080 30fps, AAC 44.1kHz, 30.023 seconds, 9,745,035 bytes.
- Reviewed ~0.4, 2.5, 5, 8.5, 12, 15, 18, 22, 27 seconds.
- Clearly labeled **Launch Film** on source page, with its own storyboard/prompt; not evidence of a purely URL-generated browser walkthrough.
- Strong cinematic grammar: coherent brand 3D mark, kinetic typography, orbital lines/process graph, controlled lighting and temporal hierarchy; actual app UI is not the subject. A benchmark for advanced motion grammar, not Sauce's one-URL source-true output promise.

### Arcade — Stack by Ramp
- Public examples: https://www.arcade.software/ai-video-examples
- First visible public MP4: `https://cdn.arcade.software/mp4s/K1Mzh18aG5dgLR54rxAN_JRh26WeXAOyQSmeqJD8f.mp4`
- SHA256: `7d22a17f97d3183cae73df90321f7be7943006d9bf7f4ecd7c2a79f15215bbbf`. H264 1920×1080 30fps, AAC 48kHz, 67.2 seconds, 17,679,340 bytes.
- Reviewed ~0.6, 4, 8, 15, 22, 30, 39, 50, 61 seconds.
- Strong for Sauce's target: intentional dominant UI element each beat (prompt field, choice state, an approval card, results, dashboard). Clean light backgrounds, zoom choices supporting task comprehension, coherent restrained yellow accents, strong legibility compared with Sauce's previous dark, wide Resend drafts.
- Not evidence of unrestricted automatic URL generation; the film is labeled `Made by Arcade`, and its production/manual intervention is not observable from the public MP4. Avoid extrapolating cost or fully autonomous success.

## Decision for Sauce Phase 2

1. **Do not compete on URL input, MCP availability, AI narration, or 1080p export as differentiators.** Vendor pages already advertise these.
2. Benchmark against actual **Arcade scene clarity** (large functional interface and clear result), **Clueso motion grammar** (intentional controlled layers), and **DemoVisor packaging** (video + guide + deck), while preserving Sauce's original source pixels.
3. Create one authorized single-workflow 5–10 second film with before/action/visible payoff, then have an independent product owner judge publishability **blind**, without knowing which system produced it.
4. Measure per approved film: capture/retry costs, human minutes to plan or revise, real source truth, text legibility at phone width, and whether a buyer would use it.
5. Do not claim a customer-ready premium engine from these competitor samples or from Sauce's passing unit tests.

**Local private evidence (existing Vultr workspace):** `/srv/devmcp-workspaces/b024c71d369a18d883fa7cc6baffe428/benchmark/`. Public extracted videos and contact sheets must not be checked into GitHub or deployed. No Suite/CI claims from this research-only exercise.
