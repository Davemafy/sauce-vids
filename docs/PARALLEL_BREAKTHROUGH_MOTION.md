# Parallel breakthrough — Motion & Optics

2026-11-19. Isolated main checkout at /srv/devmcp-workspaces/009d4bc7ec42499d54e8c37fec2d9886/sauce-motion-optics. Base main 06453d127fada315459595549fb2939e1ba4a2de. No pushes, deployments, new VM, or edits to other workspaces.

## Source evidence

Private original real public Linear marketing-preview: /var/lib/sauce-steward/qa-logs/market-film-20261118/capture/linear-workflow-dpr2-source-60.mp4, 2640x1440/60 fps, 1110 frames. Source SHA256 7a539dd06e90257f237db0ad602301ca3fd8cc2db96ac802613904d010a8a454, checked by the renderer against the actual event manifest. Manifest: capture/linear-workflow-dpr2-events.json (19 events). Observed Agent Insights at trace t=12.8198, with genuine counters 3,389 / 1,128 / 729, measured DOM card positions x=563.0, 1265.656, 1968.328, y=263, height 80. No private sources or events committed.

## Reusable change

New opt-in --protect-summary-group in scripts/evidence_edl_renderer.py. For a shot with a unique summary:N or overview:N camera anchor, calculate the union of all verified summaryRects and bound source-camera scale to preserve 6% safe area. Recenter the group, without changing actual source pixels, event timestamps, or cursor choreography. Fail closed on invalid/out-of-viewport geometry. Default and non-summary shots remain unchanged. No effects layered onto UI.

## Actual 4-second A/B

Private artifacts: motion-proof/before.mp4 (SHA256 38302d923d933aed825613e6f56b87c6f3d799846e527ab449e18be4141a4cd9) and motion-proof/after.mp4 (SHA256 5f0818ce4c01ebd694be301cccb9962b1339973d34b374e9689083ea08128462). Both 1920x1080/60 H.264, 240 frames, FFmpeg full decode successful and source hash verified; identical original frames [780,1020) and --premium-cursor --floating-stage --stage-scale .86. The only difference is --protect-summary-group. Evidence contact sheet motion-proof/comparison.jpg shows 0.5, 1.3, 2.5, 3.7 seconds, before left and after right. Actual study source edit is untracked motion-study-edl.json; its two remaining shot entries are not rendered, because --max-frames 240 truncates to the real stable post-outcome excerpt. No click occurs in the excerpt and no full-film choreography is claimed.

Reproduce: from the isolated checkout, with P=/var/lib/sauce-steward/qa-logs/market-film-20261118/capture, run PYTHONPATH=scripts [venv-python] scripts/evidence_edl_renderer.py --video "$P/linear-workflow-dpr2-source-60.mp4" --manifest "$P/linear-workflow-dpr2-events.json" --edl motion-study-edl.json --out motion-proof/after.mp4 --max-frames 240 --premium-cursor --floating-stage --stage-scale .86 --protect-summary-group. venv-python is /srv/devmcp-workspaces/5c407ce984e7defcf77da3f1f9cb7f67/.sauce-render-env/bin/python.

Tests: targeted geometry and default-is-unchanged tests 3 passing; related continuity tests 13 passing combined. Encoded before/after consumed ~22.58/23.34 seconds respectively.

## Cold aesthetic review

PASS: all 3 genuine counters remain visible versus the unprotected crop that cuts off second/third. No invented UI, additional pointer, or fake interaction. FAIL: protected stage has oversized matte and small typography; weak camera motion after clamp; no click/action proof inside excerpt. Not competitive with reference Screen Studio's measured ~1.62x push/hold/release grammar (docs/screenstudio-study.md). This is a safety opt-in, not film acceptance, human signoff, or 10/10. A future directed sequence should show the three-card overview then cut/push into a genuine single outcome while preserving the group context. No publish/deploy is authorized.
