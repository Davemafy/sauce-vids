# Sauce — new chat bootstrap and Phase 2 continuation

**Reviewed:** 2026-11-16. **Current user-selected focus:** Phase 2 *visual-quality hardening and continued production-engine improvement*. This is a recovery guide, not a new competing specification.

> **One governing rule:** The latest GitHub `main` + actual exported video are the source of truth. ChatGPT memory and previous assistant replies are only pointers, never substitutes for reading files or viewing the real MP4.

## Fast start in a new conversation

1. **Stay in the same ChatGPT Project** that contains Sauce/Vultr context. In its menu choose **Project settings → Instructions**, paste the short instructions below. If the current chat is outside the Project, move it into the Project when the UI permits. Add this file or its GitHub link as a Project source if useful.
2. **Begin a new chat in that Project** with the ready-to-paste message below. Use connected GitHub and recover the existing persistent Vultr DevMCP workspace. A new chat has no safe permanent workspace handle: recover a fresh handle; never paste tokens into the prompt.
3. **Read these versioned references from current GitHub `main`**, in order:
   - [`AGENTS.md`](../AGENTS.md) — how to work in Sauce.
   - [`docs/SAUCE_STANDARDS.md`](SAUCE_STANDARDS.md) — what a good film *must* look and behave like.
   - [`docs/SAUCE_HANDOFF.md`](SAUCE_HANDOFF.md) — current scope, verified links, open gaps.
   - [`docs/sauce-motion-phase2.md`](sauce-motion-phase2.md) — already implemented Phase 2 technical baseline.
   - [`docs/screenstudio-study.md`](screenstudio-study.md) and [`skills/sauce-quality/SKILL.md`](../skills/sauce-quality/SKILL.md) — motion reference and review method.
4. The new agent must **compare GitHub `main` to the worker's local HEAD and uncommitted files**, inspect actual source and exported frames, then report **confirmed reality / uncertain claims / next specific edit**. No hard reset, new branch, infrastructure rebuild or unrelated prototype.
5. After each substantive milestone, update `docs/SAUCE_HANDOFF.md` with: current commit, implementation change, commands/tests and results, exact live proof URL, frame timestamps inspected, remaining visual defects and what is still unapproved.

### ChatGPT Project instructions — paste once

```text
This Project is for Sauce, "A screen recording is not a demo".
For any Sauce engineering/design task, recover current GitHub main at
https://github.com/Davemafy/sauce-vids and read AGENTS.md,
docs/SAUCE_STANDARDS.md and docs/SAUCE_HANDOFF.md before editing.
For new-chat continuity read docs/SAUCE_NEW_CHAT.md.
Use the existing Vultr DevMCP workspace; verify current HEAD against
main, preserve uncommitted files, and work on main only.
Our active focus is Phase 2 visual quality hardening, not restarting
the completed technical proof. Keep genuine product events, landscape
16:9 as the flagship, readable UI, action-following camera, proportionate
always-visible cursor, deliberate typography and event-synced Foley.
No generic AI slop, fake interfaces, pointless overlays or Shorts by default.
Inspect actual MP4 frames against real references; passing tests is not
creative approval. Report exact URLs, evidence and unresolved defects.
Update docs/SAUCE_HANDOFF.md after verified milestones. Never claim
that a tool ran or a film is premium without evidence.
```

### New-chat first message — paste for Phase 2

```text
Resume Sauce Phase 2 quality hardening, not a new implementation.
Repo: https://github.com/Davemafy/sauce-vids (main only).
Use the connected GitHub and persistent Vultr DevMCP worker.
Read AGENTS.md, docs/SAUCE_NEW_CHAT.md, docs/SAUCE_STANDARDS.md,
docs/SAUCE_HANDOFF.md, and docs/sauce-motion-phase2.md from CURRENT main.
Recover the worker, compare its HEAD and dirty files to remote main,
then inspect the actual Phase 2 1080p master and frame evidence.
Do not replace or restart the existing verified renderer, preset engine,
Foley system or bounded Studio UI. Identify remaining differences from
the premium Screen Studio/reference quality bar and execute the next
scoped improvement with full frame-level QA. Preserve existing work.
When done, update docs/SAUCE_HANDOFF.md with evidence.
First tell me: what is already proven, what looks weak, and what exact
Phase 2 change should happen next?
```

## What Phase 2 means here

**Completed as a limited technical baseline:** Phase 1 TypeScript `FramePlan` + `FoleyPlan` and presets; a real `--preset 3d-launch` Python output with projected 3D camera, spotlight + luminous active-region rim, genuine redacted copy/paste/submit events, and deterministic 48kHz Foley including procedural fallback. `docs/sauce-motion-phase2.md` records the acceptance tests and a short 3.3-second proof. A bounded Phase 3 Studio selector (Brimble/Sauce fixtures, three presets and Foley toggle) was subsequently documented in `docs/sauce-studio-phase3.md`.

**Still unproven:** automatic premium-quality films across arbitrary websites, longer convincing narrative arcs, general authenticated upload support, and final human-level visual acceptance. Thus the **current active Phase 2 goal is visual/editorial quality**, not repeating the baseline implementation. The first action is to watch the actual rendered output and compare concrete frames against approved references, then improve the lowest-quality scene.

**Approved constraints that must not drift:**

- Landscape **1920×1080/60fps** primary output; DPR ≥2 verified source and Lanczos preview; do not produce 9:16 by default.
- Actual browser/DOM evidence and real product UI. No invented clicks, modal results or fake success.
- Cursor **one**, visible in key actions, correct hotspot and proportions (prior ~32×39px at 1080p is a *size baseline*, not final shape approval).
- Narrative motion: pointer approach → genuine press → observed change → camera move → enough reading time. No pre-action zoom or endless cursor chasing.
- Intentional fonts, whitespace and captions; no generic uppercase eyebrows, redundant headlines, random gradients or massive glass pills.
- Foley aligned to the output sample clock at **48kHz**; mute actually works. Use licensed samples or the built-in deterministic procedural synth. No unsolicited music.
- Verify the source hashes, semantic and pixel assertions, FFmpeg streams/full decode, contact sheet/full-resolution frames, desktop/mobile playback and privacy.
- **A technically green render is not a premium film.** Do not announce completion when a viewer would scroll away on first glance.

## Phase 2 references and recovery checks

Known public baseline URLs (check again; HTTP availability is not visual QA):
- Phase 2: https://devmcp.davemafy.xyz/sauce-motion-phase2/
- Independently rerendered: https://devmcp.davemafy.xyz/sauce-motion-phase2-verified/
- Limited Studio: https://devmcp.davemafy.xyz/sauce-app/studio
- Actual code: `scripts/produce_cinematic_demo.py`, `scripts/session_replay.py`, `scripts/cinematic_stage.py`, `scripts/foley_mixer.py`, `scripts/studio-motion/src/`.

Targeted checks (from the repo root, using a configured Vultr worker):

```bash
git status --short
git rev-parse HEAD
git ls-remote origin refs/heads/main
(cd scripts/studio-motion && npm ci && npm test)
../.sauce-render-env/bin/python -m pytest tests/phase2/test_sauce_motion_phase2.py -q
python3 -m unittest discover -s tests -q
# Inspect actual MP4 with ffprobe; decode with ffmpeg -v error -xerror.
# View contact sheet and frame images; test desktop 1280x720 and mobile 390x844.
```

Do not assume every command above is valid in an arbitrary ephemeral shell; locate the actual persistent worker first. Never download private HAR, credentials or session screenshots to public hosting to make a preview.

## Why this is more reliable than relying on chat memory

A ChatGPT Project can retain project instructions, uploaded sources, and refer to earlier project chats. But a fresh conversation does **not** automatically execute repository instructions, nor does it necessarily reconstruct each design decision from thousands of old messages. The explicit starter message forces the new agent to **fetch and verify the durable repo contract**.

If you rely on ChatGPT Work, review the current Project memory setting first: OpenAI's help notes that **Work is not available with project-only memory**. Project instructions are the essential layer; default vs project-only memory should be chosen based on the features you actually need.

Documentation sources (checked 2026-11-16):
- OpenAI ChatGPT Projects: https://help.openai.com/en/articles/10169521-projects-in-chatgpt
- Agent instructions convention: https://agents.md/
- OpenAI agent-instruction guidance: https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra

**Maintenance:** This file is a startup interface, not a new status database. Keep the current technical state in `docs/SAUCE_HANDOFF.md` and update that file after every verified milestone.
