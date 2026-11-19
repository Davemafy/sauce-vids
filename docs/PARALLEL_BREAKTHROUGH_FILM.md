# Parallel breakthrough film — isolated opening study (2026-11-19)

**Status:** COMPLETE AS A PRIVATE 4-second technique candidate; **NOT APPROVED** as a winning/premium opening. No pushes, deployments, new VM, inference or edits to dirty production trees.

## Checkout and evidence
- Fresh isolated Vultr DevMCP workspace: `/srv/devmcp-workspaces/5309590a4567ffee840cf87975647c5e/sauce-film`, main `45ee5a82c4f0d9bb3f8972a01d2b7e39e0b9cc4c` at clone time.
- Authenticated *public Linear marketing preview*, not private Linear workspace: `/var/lib/sauce-steward/qa-logs/market-film-20261118/capture/linear-workflow-dpr2-source-60.mp4`; source SHA256 `7a539dd06e90257f237db0ad602301ca3fd8cc2db96ac802613904d010a8a454`; 2640x1440/60fps.
- Recorded real DOM/event sidecar: `.../capture/linear-workflow-dpr2-events.json`; SHA256 `3619c8891f9a1ba35783a39f07ab55d584dd05b14c5b242f241be32af3c2e3eb`. Genuine Agent Insights result at trace t=12.82 plus 0.28s lead; 3,389 / 1,128 / 729 and graph.
- Independent Screen Studio local video inspected at sampled 0.3, 1.3, 2.2, 6.4sec: `/srv/devmcp-workspaces/5c407ce984e7defcf77da3f1f9cb7f67/sauce-v05-release/studio/.tmp/sauce-reference-research/screenstudio-product-1.mp4`, SHA256 `b305d36e8c764e6affe92b0001bea81d33b52c7d73f557bdd3bedcbcf0cba3df`. Source 1280×720/60, 10.367 sec; frames show an establishing wide application view, controlled enlargement to a clear subject, return to whole app, and a second focus. Independent SIFT reference measurements in `docs/screenstudio-study.md`: ~1.62x pushes with clear holds and releases, not continuous chase.
- Public Refs/Loom REF-3721 used from `docs/SAUCE_REFS_MARKET_FILM_20261118.md`: 21.8sec/8 shots and 5.5sec uninterrupted opening. **No claim of independently opening gated reference video**. This local study used the available documented timings rather than importing reference pixels.

## Editorial and render
The original 15-second Linear film's future-state teaser is rejected for this opening. Isolated chronological source frames **780–1019 inclusive** = **13.000–16.983sec**; source result already proven before frame 780. Opens with actual outcome on the first frame, not a fake click, synthetic UI change or private app. No gratuitous text overlay. Recorded single premium pointer; static-readable hold. Restrained camera 1.00x at f0 → 1.07x by f55 (0.917s), held through f239. DOM-grounded source remains unchanged.

The existing deterministic `scripts/evidence_edl_renderer.py` has a **narrow isolated opt-in** `openingStudy:true` acceptance path for 1–2 shots and 3–5 seconds. The full-film default still enforces ≥3 shots and ≥7 sec. Also guards its two-shot nonchronological metadata check. No other core-renderer modifications.

Two previews **total**:
1. **Rejected** 4.0sec initial zoom 1.32→1.55 around measured overview; left 3,389 counter was clipped. Contact `studio/.tmp/parallel-film/contact.jpg`; initial MP4 SHA256 `a9ce34607ca78247866e37a6dd3150c249f05e5f9066e14d0660ff56d3e6a7be`.
2. **Retained** 4.0sec, source-true wide camera 1.00→1.07: `studio/.tmp/parallel-film/opening-v2-1080p60.mp4` SHA256 `8757965569dd5bd0807560b963d38e36a0756c7dd8a437e53b3ec85bd22b2d7e`. Editorial JSON `studio/.tmp/parallel-film/opening-edl-v2.json` SHA256 `f85b77b7409e7993feee4935b0b99813c31c394a6caf11ffd222bad262ca6d54`. Frames and contact: `studio/.tmp/parallel-film/frames/v2-*.jpg`, `studio/.tmp/parallel-film/contact-v2-review.jpg`, and reduced inspectable `contact-v2-small.jpg`; reference contact `reference-review.jpg`.
- Reviewed encoded frames at 0.05 / 0.90 / 2.00 / 3.90sec. All three real counters visible through hold, genuine chart left and table right. First version failed that review. The V2 pointer is very subtle and UI still dense.
- FFprobe V2: **H.264 1920x1080, 60fps, exactly 240 frames/4.000s, silent video**; FFmpeg `-v error -xerror` full decode **PASS**. No Foley/narration invented; video-only export intentionally labeled silent.
- Test: `/srv/devmcp-workspaces/5c407ce984e7defcf77da3f1f9cb7f67/.sauce-render-env/bin/python -m pytest tests/phase2/test_evidence_edl_renderer.py -q` → **6 passed**. Two render receipts are adjacent to MP4s. No desktop/phone player playback claimed.

## COLD VERDICT
**6/10 as a truthful standalone product insight insert, only 4/10 as a standout competitive opener.** It earns trust by showing a legitimate result immediately, and corrects the original crop. But it does not have Screen Studio's distinct subject-directed push/release or Refs/Loom's action→payoff choreography. The still-dark/dense interface and nearly static camera create weak first-second visual energy; there is no fresh action in these four seconds. **Do not market as a 10/10 breakthrough.** Better future candidate would require a new verified capture with the source action and result separated by <1 second, no unstable transition interval; this existing recording has a 1.27-second click→result delay and white transition frames that cannot ethically be masked as live interaction.

**Coordinator integration:** Cherry-pick/edit only the opt-in short-EDL validation if useful; no remote branch or push. Private media stays on Vultr.
