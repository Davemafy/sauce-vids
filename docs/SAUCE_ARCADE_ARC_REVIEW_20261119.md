# Arcade Stack by Ramp — editorial arc and first 1:1 motion target

**Review:** 2026-11-19. **Source:** original publicly shared Arcade Stack by Ramp MP4, reopened on existing persistent Vultr DevMCP. **Status:** reference analysis only; **NO** 1:1 recreation, production Gemini approval, customer footage or publishable Sauce film.

## Source identity and scope

- Original public reference: https://cdn.arcade.software/mp4s/K1Mzh18aG5dgLR54rxAN_JRh26WeXAOyQSmeqJD8f.mp4
- SHA256: `7d22a17f97d3183cae73df90321f7be7943006d9bf7f4ecd7c2a79f15215bbbf`.
- Encoded video: H.264 1920×1080, 30fps, 2016 decoded frames / 67.2s. AAC stereo audio 48kHz exists, **but audio content/beat sync was not independently assessed in this pass**.
- Actual MP4 reopened, with sampled source frames at 0.4, 2.3, 6.0, 10.5, 13.0, 16.8, 20.83, 22.5, 24.5, 26.5, 30.3, 33.95, 36.8, 39.0, 42.1, 46.5, 47.96, 50.85, 52.75, 55.3, 57.5, 61.3, 64.5, 66.9s, plus dense inspection of 45.6–52.5s.
- Reference frame ledger and adjacent-frame cut review already on main; not rewritten by this editorial pass. Reference film pixels and private contact sheets are **not** checked into Git.

## Observable story arc

| Approximate span | Observed screen content | Story function |
| --- | --- | --- |
| 0–2.200s | Large branded Stack introduction | Establish product identity |
| 2.200–13s | Accounting workspace, task prompt, assistant begins work | Orient the viewer; show user goal |
| 13–20.800s | Confirmation of prepaid-insurance file and choice of expense-identification method | Clarify the task, show system seeking input |
| 20.800–26.400s | Task plan with approval | Establish user authorization |
| 26.400–42.033s | Plan approved, real-looking spreadsheet and accounting work in UI | Show work rather than just claim it |
| 42.033–50.800s | Journal-entry detail, posting CTA, processing and posted result | High-salience consequential action |
| 50.800–61.100s | Finished task checklist, completion action, return to dashboard and bigger product context | Verified-looking payoff and broad consequence |
| 61.100–67.200s | Brand statement and Ramp logo outro | Close |

These are *editorial phases*, not an exhaustive list of hard cuts. Ten previously measured high-change discontinuities have exact incoming frames **66, 624, 792, 1015, 1104, 1261, 1392, 1438, 1579, 1833**, corresponding to 2.200, 20.800, 26.400, 33.833, 36.800, 42.033, 46.400, 47.933, 52.633 and 61.100 seconds. Dense viewing also confirms a meaningful visual state replacement at **frame 1524 (50.800s)** that the high-change threshold did *not* classify; don't pretend the ten-candidate set is complete.

## Selected first technique — 46.400–52.633s (187 frames)

The strong transferable sequence is: **consequential button → processing → journal posted → completed task → contextual dashboard**. It is not appropriate to force this multi-state storyline onto the one-event Resend price slider.

Measured **visible near-white panel extents** were obtained from decoded original BGR frames with threshold `all channels >=243` and the largest connected bright component per frame. These are **approximate raster panel bounds from a documented threshold**, not DOM coordinates, exact masks, shadow bounds or inferred proprietary keyframes:

| Source frames | Observed stage | First bright-panel bbox (x,y,w,h) | Last stable bbox | Focal behavior |
| --- | --- | --- | --- | --- |
| 1392–1437 (46.400–47.900s) | Large isolated Post to Quickbooks / Posting control | (200,300,1520,480) | (185,295,1550,489) | Card stays centered around (960,540); width +1.97% |
| 1438–1523 (47.933–50.767s) | Journal entry pending/posted | (462,387,996,376) | (441,365,1038,396) | Card remains horizontally centered; width +4.22%, center drifts vertically as content settles |
| 1524–1578 (50.800–52.600s) | Finished updating prepaid insurance schedule / Mark as complete | (200,355,1520,370) | (181,351,1558,433) | Card mostly centered; width +2.50%; last height includes a transition/change and is **not** a clean scale estimate |
| 1579 onward (52.633s+) | Larger dashboard re-introduction | At frame 1579: (234,149,1454,819) | — | Pull back to product context |

Actual source background pixel at bottom-left in these central card shots: BGR approximately **(219,223,225)**. The bright paper white element has gentle boundaries; deliberate high contrast on the significant action uses a yellow-green accent. Do not copy the reference brand color onto unrelated customer UI.

A durable effect of this choreography: an original UI component can occupy roughly 79% of the 1920-pixel canvas width in the first posting-card beat; the single event and status are readable. Sauce's old Resend price-text crops were too small and incompletely extracted. The value is **complete source-true component capture + appropriately scaled stage + event-timed result**, not a random larger zoom.

### Why the original works

- **One subject per beat.** Wide application background disappears at consequential steps; the viewer can read a single approval/posting/result component.
- **A motivated progression.** Each cut corresponds to a new stage of the *same* accounting task, not disconnected product screens.
- **Micro-motion while holding.** The bright panel footprints grow by ~2–4% over their segments, creating energy without obscuring the label; precise interpolation/easing still requires tracked measurement.
- **Earned payoff.** The posted journal and final checklist appear before the wider dashboard; the final wider screen gives the task context.

### Important limitations and criticisms for Sauce

- **The payoff arrives late** in the 67-second branded launch format. A Sauce 7–12s automatically generated **UI shot** should not copy this full 67s structure. Remove unnecessary brand-only openers/outros and preserve a faster action→result arc.
- **The transition around frame 1524 is real and was missed** by the earlier simplistic cut detector. Need human/video A/B review beyond only high-difference candidates.
- It is a professionally composed marketing presentation, **not evidence of an authenticated browser recording**. Do not assume the reference underlying UI states/interaction event logs can be legally or technically recovered.
- A flat MP4 doesn't uniquely expose original animation timelines, masks, depth, cursor hotspot or source-layer hierarchy. Threshold panel bboxes are not 1:1 keyframes and must not be promoted to Gemini training labels.
- EDL formats currently vary: `scripts/evidence_edl_renderer.py` expects multiple proven state changes in its standard mode, while `sauce-film-plan-v1` handles the single real-event Resend flow. Avoid merging or rewriting functioning renderers just to force training examples into one name.

## Next source-true 1:1 reconstruction gate

1. Pick **only one** 1.5–3s UI micro-shot from the 46.400–52.633 segment (prefer the 46.400–47.933 isolated posting CTA first). Determine exact component edge/matte, perspective, source-scale and pointer tracks for **every frame**, with a measured trajectory and explicit uncertainty.
2. Capture a genuinely authorized separate UI with the same meaningful event. Stage and animate its **real pixels** with an existing Sauce JSON compositor; add only a necessary reusable primitive, not a new pipeline.
3. Render an actual matched-duration MP4. Align source and output by frame index. Compare element-relative geometry, scale/center drift, visibility, transition, pointer choreography and mobile legibility across **all** output frames. Never claim literal product pixel equality across different apps.
4. Reject until a side-by-side is genuinely approved. Bundle `capture evidence + executable JSON + render MP4 + frame-level review + unresolved defects` before allowing any production Gemini few-shot use.
5. Do not describe the currently existing Arcade JSON as 1:1. The `--research-only` production gate remains in force.

**Bottom line:** The transferable advantage is the film's *task-led visual hierarchy*, not a magic effects preset. First exact-motion target: the isolated consequential-action card at frames 1392–1437; the full story/payoff sequence is a later multi-state acceptance test.
