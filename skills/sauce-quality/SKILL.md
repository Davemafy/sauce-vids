---
name: sauce-quality
description: Apply Sauce's source-true cinematic production standards, verify actual MP4 output, and maintain durable project continuity across chats.
---

# Sauce Quality & Continuity

For a new conversation, start with `docs/SAUCE_NEW_CHAT.md`. Load the repo files directly; prior chat memory is not evidence of the current implementation.

Before any Sauce code, design or render task:

1. Read root `AGENTS.md`, `docs/SAUCE_STANDARDS.md` and `docs/SAUCE_HANDOFF.md` in full.
2. Inspect current GitHub `main`, the exact production code and the latest relevant MP4/receipt. Local Vultr worktrees can be behind remote; preserve uncommitted work.
3. Preserve **genuine source footage, visible and proportionate cursor, event-following camera, readable UI, landscape-first framing, deliberate type and non-generic overlays**. Do not mistake a functionally correct output for a visually acceptable product film.
4. Review multiple actual full-resolution frames, a contact sheet, desktop and mobile players, and an appropriate live product-demo reference. Fix visible defects before declaring quality.
5. Verify trace provenance, source pixel fidelity, metadata assertions, `ffprobe` and full decode, 60fps master/preview resampling, Foley output-clock alignment when present, CI and source privacy.
6. State exact deliverable URLs, changes and remaining visual gaps. Update `docs/SAUCE_HANDOFF.md` after meaningful milestones.

Current architecture: TypeScript `scripts/studio-motion/` for camera/time/foley plans; Python/Chromium/OpenCV/FFmpeg production renderer; Next.js `apps/web/app/studio/` limited catalog UI. **Reinspect the source on each new session** rather than trusting this sentence forever.

Hard prohibition: don't add Shorts, fake interface elements, misleading authenticated results, random gradients/glass UI, uppercase eyebrow filler, oversized pointers, or motion that begins before the recorded action simply because they look cinematic.

A skill reference is not a magic memory: the agent must actually load and obey the repository docs.
