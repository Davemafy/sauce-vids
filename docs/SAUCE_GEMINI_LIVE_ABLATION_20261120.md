# Sauce — real Gemini three-condition reference experiment

**Executed 2026-11-20. Research-only; all videos and generated plans kept private.**

**Result:** Gemini-3.1-flash-lite returned syntactically valid JSON in 6/6 first calls but 0/6 passed Sauce film-plan validation. After precisely one failure-specific Gemini repair call per response, 6/6 passed the actual validator and were rendered. All six four-second MP4s fully decoded; **0/6 passed visual review**. Conditioning on the partial measured Arcade reference did not demonstrate improved film quality. No model-quality superiority claim is established.

## Credential recovery and model calls

Existing Google Gemini API access was confirmed on the persistent Vultr host in the root-protected /etc/sauce-url2video.env file. The running sauce-url2video.service already used GEMINI_API_KEY and SAUCE_DIRECTOR_MODEL=gemini-3.1-flash-lite. No new credentials, VM, cloud services or deployment were created. The key was accessed only within a private server process, not copied into prompt files, code, GitHub or model output.

The live evaluation made six initial generateContent calls and six single repair calls using JSON response MIME, temperature 0.1 and no initial sampling retries. API receipts reported **22,713 total tokens** over 12 requests. The actual billing amount was not checked. The previous statement that Gemini was unavailable on Vultr was wrong.

## Controlled evidence and reference conditions

Both independent products used genuine hash-pinned public browser sources (original 25fps Chromium VP9, trimmed and resampled to 30fps, not native 30/60fps), source-bound event sidecars and the same four-second film-plan JSON schema:

- **Resend pricing:** real $20 -> $35/month Pro slider action; verified result at 2.383206s relative to the trimmed source. Complete real Pro card 299 x 658 CSS/source pixels; timed mouse drag.
- **HeroUI Theme Builder:** real hue 208 -> 50 native keyboard interaction; verified result at 1.889646s. Actual chart group 1118 x 316 pixels, with 5.31% meaningful changed pixels between inspected before/after screenshot evidence.
- **Arcade reference:** measured 46-frame posting-card shot at original frames 1392-1437 from the SHA256-pinned Stack by Ramp MP4. First panel raster rectangle (200,300,1520,480); last (185,295,1550,489). This is **NOT certified 1:1**; full source-layer motion and project state remain unknown.

Each source was passed to Gemini under three prompt conditions, otherwise the same constraints and source evidence: **A no reference**; **B a prose style description**; **C the research-only Arcade input measurements paired with independently reconstructed isolated-UI JSON parameters**, explicitly warning about shape/interaction mismatch. All prompts required only real event anchors and forbidden future result anticipation. These conditions test natural reference selection, not forced pixel-reconstruction.

## First-pass validation and bounded feedback

| Source | Condition | First-pass JSON | First-pass film-plan validation | After one failure-specific repair |
| --- | --- | --- | --- | --- |
| Resend | A — no reference | valid | FAIL: zoom targets an unobserved future result | PASS |
| Resend | B — style prose | valid | FAIL: zoom targets an unobserved future result | PASS |
| Resend | C — measured Arcade | valid | FAIL: zoom targets an unobserved future result | PASS |
| HeroUI | A — no reference | valid | FAIL: zoom targets an unobserved future result | PASS |
| HeroUI | B — style prose | valid | FAIL: camera acceleration/motion too abrupt | PASS |
| HeroUI | C — measured Arcade | valid | FAIL: zoom targets an unobserved future result | PASS |

The gate is the real scripts/render_event_video.py --film-plan ... --validate-only against the captured source MP4 and evidence manifest. No artificial post-hoc scoring. One bounded second request provided each original rejected JSON plus the exact validator error and correction fence. All six corrected plans passed without a second repair attempt. First-pass failures remain preserved as evidence.

**Critically, none of the 12 plans selected Sauce's isolated-ui composition primitive.** Even the measured-reference condition produced conventional camera keyframes rather than the reference's centered card and measured 46-frame scale trajectory.

## Encoded film review

All six corrected outputs are genuine 1920x1080, 30fps, 120-frame H.264 four-second films, independently FFmpeg-decoded. SHA256:

| Product | Condition | SHA256 |
| --- | --- | --- |
| Resend | A | ef61df31d82378220aaad9fa11537edbc7a210b6f07c0188570ae79520467b17 |
| Resend | B | 40abfa7ff3107b7afa33ecf3d7b4c32bf5cc0d31407b9e890d98402a38d03720 |
| Resend | C | 7953e4037ccab84abb309f6e13d6cc8f89ad2580f23aad5232624667aa6f8a3f |
| HeroUI | A | 4ae3c480882de47dce9ea009c8298afae5ad80034361d47276b99330e5b85309 |
| HeroUI | B | a503e681d991f545cef7aaf55defb4cd10cca25412ffcd3a00888f983e7b9525 |
| HeroUI | C | db1934ee55df3c8f5cc3ba0a8ea34dbde8a31e15d248c9ddf30b7b5ac8d716db |

Full film sample grids were opened and critically reviewed at t=0.7, 1.6, 2.6, 3.73s across all six products/arms. Actual projection geometry was computed from the camera matrices at 3.75s:

- Resend full 299px Pro card displays approximately **69.8 / 65.6 / 66.8px width on a 390px device** (A/B/C). A clips the complete card. All fail legibility and action/result hierarchy.
- HeroUI two-chart group displays approximately **249.8 / 245.3 / 249.8px width, only ~70px high, at 390px device width** (A/B/C). Chart content is too small; the output reads as tiny dashboard footage rather than a directed visual payoff.
- All variants have weak visual hierarchy, restrained but unremarkable zooms, and no cinematic isolated payoff stage. The measured-reference arm did not visibly win.

**Creative approvals: 0/6. First-pass executable: 0/6. Post-feedback executable: 6/6.** Independent blinded human graders were not commissioned, so this is a documented, internal qualitative review, not a statistical win/loss claim.

## Interpretation and next gate

The earlier deterministic compositor study could reproduce Arcade's observed panel rectangle growth across all 46 frames with at most 1px geometry coordinate drift when manually given measured parameters. This live Gemini study demonstrates the separate creative-selection bottleneck: Gemini did not autonomously select the executable isolation technique, even with reference example data. Accurate numbers alone are not sufficient for autonomous good direction.

This does not prove Gemini fundamentally cannot do it: the reference was research-only rather than fully matched, the prompt was intentionally permissive (to test choice), there were only two target sites and a single provider sample per condition, and neither target duplicates Arcade's real posting task.

**Production rules:** retain the research-only gate for unverified references; pass Gemini plans through deterministic validation and at most bounded specific feedback; never call a green validator a good film; require real UI legibility at phone size and coherent action/result before creative approval; do not simply accumulate more approximate reference JSON. The next substantive experiment should match interaction/payoff type and source geometry before attempting prompt comparisons, use multiple samples and blinded human review when possible.

**Private artifacts:** existing isolated Vultr workspace contains 12 generated model plans/receipts, validation traces, six output films, contact sheets and original source media. None was deployed or copied to this public repository. Full numeric proprietary reference tracks also remain private. No secrets were printed or committed.
