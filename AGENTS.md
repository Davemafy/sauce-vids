# Sauce — repository instructions for every coding agent

Product: **Sauce** — "A screen recording is not a demo."

**Required before making any change:**
1. Read `docs/SAUCE_STANDARDS.md` (creative and engineering acceptance contract).
2. Read `docs/SAUCE_HANDOFF.md` (status, limits, live proofs, next handoff).
3. Read the exact source and nearest tests for the change. Never assume past assistant claims describe today's `main`.
4. Compare working-tree status with `origin/main`; preserve unrelated local changes and private artifacts. **Main only**; do not create branches by default.
5. Identify the actual output pipeline. Changing the web player does NOT change pixels in the MP4. Never substitute preview CSS for composition work.

## Non-negotiables

- Real product footage, real recorded events and verified DOM outcomes. Do not fabricate screenshots, authenticated actions, UI or pointer data.
- Landscape 16:9 is the flagship. Portrait edits are separate deliverables only when explicitly requested.
- The film must be legible, deliberately directed and reference-reviewed. Passing unit tests does not establish premium visual quality.
- Avoid formulaic AI design: uppercase eyebrow titles, redundant headlines, random gradients, needless badges, giant cursors, fake clicks, mechanical constant-speed pointer paths and pre-action zooms.
- Keep the pointer visible and appropriately sized to the interface, with verified tip/hotspot alignment. Camera follows actual narrative action; hold long enough to read.
- Preserve source continuity, audio synchronization, privacy, accessible UI and responsive playback.
- Do not claim "shipped" unless the exact deployed URL and video have actually been opened and verified.
- Never commit credentials, HAR, private capture sessions, source screenshots, unlicensed assets, or generated videos that are meant to remain private.
- No paid inference, purchases, sign-ins, or submission without authorization.

## Acceptance and handoff

Before reporting completion: run relevant builds/tests, check actual encoded streams, inspect full-resolution frames **and** desktop/mobile playback, compare with selected real references, and record what is still visually weak. Update `docs/SAUCE_HANDOFF.md` after milestones with repo commit, actual proof URL, tests and remaining gaps. Cite exact links and frame evidence, not invented grades.

Architecture at this writing: TypeScript `scripts/studio-motion/` plans frame/Foley timelines; verified Chromium + Python/OpenCV compositor + FFmpeg produces final media; Next.js `apps/web/` hosts bounded Studio UI. Read the current code and phase docs for the precise implementation.

Agent-specific entry points: `CLAUDE.md` (Claude Code) and `skills/sauce-quality/SKILL.md` (explicit skill). All point back to this file and the two living documents.
