# Sauce — repository instructions for every coding agent

Product: **Sauce** — "A screen recording is not a demo."

For a **new chat or recovered worker**, use `docs/SAUCE_NEW_CHAT.md` as the short bootstrap. The ongoing engineering rules below remain authoritative.

**Required before making any change:**
1. Read `docs/SAUCE_STANDARDS.md` (creative and engineering acceptance contract).
2. Read `docs/SAUCE_HANDOFF.md` (status, limits, live proofs, next handoff).
3. Read the exact source and nearest tests for the change. Never assume past assistant claims describe today's `main`.
4. Compare working-tree status with `origin/main`; preserve unrelated local changes and private artifacts. **Main only**; do not create branches by default.
5. Identify the actual output pipeline. Changing the web player does NOT change pixels in the MP4. Never substitute preview CSS for composition work.

## Commercial engineering objective (owner decision, 2026-11-17)

**Optimize for a credible first paying customer within seven days of a quality-approved launch, while remaining viable for six months with no revenue.** This is a target, not a forecast or a reason to expose unapproved films.

Use this decision order for scope and tradeoffs:
1. **Make the output worth paying for.** Fix known film-level defects before new dashboards, agent frameworks, or generalized infrastructure. Review the *encoded* landscape film against references; preserve real source pixels, readable action/results, purposeful camera and cursor motion. Three distinct source-true demos must earn quality approval before public launch.
2. **Make one paid pilot possible with minimal manual work.** After visual approval, prioritize bounded, reliable capture → return → preview/download → explicit review, a clear offer, and a simple legitimate way to accept one payment. Do not build a full billing platform or open self-service access speculatively. Obtain owner consent for real purchases, communication and paid infrastructure.
3. **Protect runway.** Keep single-worker production until longer real-film capacity, limits and storage are measured. Prefer small, reversible, dependency-light changes and existing Vultr capacity. A 4 GiB Sauce-only host is plausible for one short render, **not** verified for all current shared-VPS services. No deletion, migration or new VM without authorization. Experimental inference is authorized under the 2026-11-20 owner decision below; log all usage.
4. **Measure actual customer value separately from technical success.** Verified source clips, human-approved films, qualified buyer conversations, genuine payment and repeat purchases are distinct counts. Green CI, a 60fps encoded stream, localhost load tests and internal test jobs never count as revenue or creative acceptance.

**Immediate creative P0:** inspect and fix the Brimble modal occlusion and clipped result payoff in the real MP4; compare against reference and re-render. Then address native source sharpness, cursor semantics and compelling editorial holds for URL-produced films. Avoid speculative feature expansion until the saleable film gate is satisfied.

## Non-negotiables

- Real product footage, real recorded events and verified DOM outcomes. Do not fabricate screenshots, authenticated actions, UI or pointer data.
- Landscape 16:9 is the flagship. Portrait edits are separate deliverables only when explicitly requested.
- The film must be legible, deliberately directed and reference-reviewed. Passing unit tests does not establish premium visual quality.
- Avoid formulaic AI design: uppercase eyebrow titles, redundant headlines, random gradients, needless badges, giant cursors, fake clicks, mechanical constant-speed pointer paths and pre-action zooms.
- Keep the pointer visible and appropriately sized to the interface, with verified tip/hotspot alignment. Camera follows actual narrative action; hold long enough to read.
- Preserve source continuity, audio synchronization, privacy, accessible UI and responsive playback.
- Do not claim "shipped" unless the exact deployed URL and video have actually been opened and verified.
- Never commit credentials, HAR, private capture sessions, source screenshots, unlicensed assets, or generated videos that are meant to remain private.
- Paid model inference for Sauce experiments is authorized under the owner decision below. Purchases, sign-ins, external submissions, and new infrastructure still need separate authorization.
- **Reference provenance gate:** A rejected, approximate or `research_only` creative study is diagnostic evidence, **never an approved few-shot reference**. Do not select it for Gemini production or treat an old failure prompt as a quality target. Require the separately verified 1:1 render-match and source-truth admission gates. Preserve failed studies for regression analysis; never ingest whole research directories or unlabelled logs into the active director. 


## Experimental inference — explicit owner authorization (2026-11-20)

The owner has explicitly lifted the prior **no paid inference** restriction for Sauce research and experimentation. Agents may use existing configured inference credentials, stronger creative-director models, and repeated model experiments **without seeking approval for each call or treating the old inference restriction as a blocker**. There is no owner-imposed model-tier or fixed experimental token budget in this authorization. This supersedes the older inference restriction for Sauce R&D only.

Use inference to create genuinely excellent, source-true cinematic footage, not to inflate test counts. Prefer the owner's creative direction: a concise, ambitious **client-style brief + real target product footage + excellent prior reference films with their verified executable JSON + the engine contract**. Give the model creative freedom, then render, critique the actual MP4 against the references, and revise. Keep mechanical source-time and event-validity constraints enforced by the engine, not buried in huge creative prompts. Do not treat invalid or research-only reference JSON as successful training examples.

Keep an auditable log of provider, model, request counts, tokens, available pricing/charges, exact artifacts and visual outcomes. No silent unbounded automatic retry loop, exposed secrets, invented interactions, or unapproved publication. This authorization does **not** grant permission for unrelated purchases, new VMs, destructive changes, sign-ins, external submissions or public deployment.

## Acceptance and handoff

Before reporting completion: run relevant builds/tests, check actual encoded streams, inspect full-resolution frames **and** desktop/mobile playback, compare with selected real references, and record what is still visually weak. Update `docs/SAUCE_HANDOFF.md` after milestones with repo commit, actual proof URL, tests and remaining gaps. Cite exact links and frame evidence, not invented grades.

Architecture at this writing: TypeScript `scripts/studio-motion/` plans frame/Foley timelines; verified Chromium + Python/OpenCV compositor + FFmpeg produces final media; Next.js `apps/web/` hosts bounded Studio UI. Read the current code and phase docs for the precise implementation.

Agent-specific entry points: `CLAUDE.md` (Claude Code) and `skills/sauce-quality/SKILL.md` (explicit skill). All point back to this file and the two living documents.
