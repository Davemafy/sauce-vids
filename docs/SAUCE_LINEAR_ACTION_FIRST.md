# Linear public-preview film — action-first camera review

**2026-11-17 · Candidate, not creative approval · Main only**

This is a real second-site editorial experiment against the Sauce creative standard. It does not demonstrate an authenticated Linear workspace or any paid customer outcome.

## Verified source and two genuine interactions

The recorded source is the official public interactive preview at \`https://linear.app/\`, captured in the existing persistent Sauce workspace. Original footage: continuous **1320×720, 60fps, 12.000s** X11grab recording with an actual browser and mouse pointer, SHA256 \`0e6a864365f91e7931565454c1b0ad9f98d9a78b77c0f49ac7b849321f58be69\`. Private timestamped evidence: \`studio/.tmp/screenstudio-recreation/linear-two-interactions.json\` under the existing release workspace.

- **2.238s:** real click on “Reviews”; **2.5871s:** real DOM “Diff”/review result visible, with a measured result rectangle x≈559.9, y97, w750.6, h616.
- **6.3612s:** real click on “Faster app launch”; **6.6551s:** real task detail and body visible, with a measured rectangle x≈296.4, y97, w661.8, h614.
- Real \`interaction_complete\` events at 4.7501s and 9.4801s were used to reserve reading time.

**This footage is the public interactive preview on Linear’s marketing site, not evidence of a signed-in Linear customer experience.** No fake text, screenshots, clicks or DOM outcomes were generated in the film.

## Opt-in editor change, no production regression

Added \`action-first\` to \`scripts/autozoom_event_planner.py\` and \`scripts/render_event_video.py\`. For a click with recorded source-side UI change, source-derived visible result rectangle, nonempty evidence description **and** observed interaction completion, camera initiation is constrained to **after the result**. Original \`standard\` and reference-study \`screenstudio\` profiles remain unchanged. Without qualifying evidence, there is no action-first close-up. No user/customer API changes or redeploy.

Two exact opt-in camera shots in the encoded candidate:

| Event | Click | Actual result | Camera starts | Settles at 1.62× | Reading hold until | Returns wide |
|---|---:|---:|---:|---:|---:|---:|
| Code review | 2.238 | 2.5871 | 2.6471 | 3.3671 | 4.8301 | 5.6301 |
| Task detail | 6.3612 | 6.6551 | 6.7151 | 7.4351 | 9.5601 | 10.3601 |

Compared to the older \`screenstudio\` study: the older camera was already at **1.1636×** at the first click (2.24s) and **1.1959×** at the second click (6.37s). Action-first is **exactly 1.0×** through both clicks and observed result moments, reaching the same stable **1.62×** close-ups after a 0.72s quintic move.

## Actual master and independent verification

**Public review, not an announced release:** https://devmcp.davemafy.xyz/sauce-motion-phase2/linear-action-first-review-20261117/

**Exact encoded master:** https://devmcp.davemafy.xyz/sauce-motion-phase2/linear-action-first-review-20261117/master-1080p60.mp4

New master SHA256 \`9414f4507332017ea2d86ca1f6c73e189c3ee5ba86bfaa3fd73b2a5fad734e86\` (public match against private output). **1920×1080 H.264 / 60fps, 720 frames / 12.000s**, full FFmpeg \`-xerror\` decode passed. No audio was added; source action timing remains unaltered and no fake Foley is introduced.

Private full-resolution frames, source-true camera plan, original-vs-candidate A/B contacts and render logs retained in \`/var/lib/sauce-steward/qa-logs/new-buyer-quality-20261117/linear-action-first/\` plus sibling A/B images. Public directory contains **only** index page, master, 720p preview and poster; no raw HAR, timestamped source trace, or private captures.

**Actual frame inspection:**
- Opened encoded old/new compare at 2.4/2.8/3.55, 6.5/7.0/8.2 seconds. New film correctly leaves the first real click and second real click at wide framing and follows only the confirmed resulting UI. The original already pushed ahead of those two interactions.
- Inspected the decoded close-up frames at **3.8s and 8.2s**: real code diff and task detail remain visible, with the same natural source UI. **Still fairly text-dense** in the silent 12-second film. UI sharpness is limited by the real 1320×720 source being enlarged to an encoded 1080p frame.
- Reference comparison: the original Screen Studio study measured two ~1.62× closeups and readable holds. Action-first follows the owner's stronger **click → visible result → push → hold → release** grammar without a distracting pre-action zoom. It has not been independently owner-approved as premium film craft.

**Browser QA on the live public HTTPS page:** actual Chromium HTML video loaded to readyState **4**, playback progressed beyond **0.8s** with no media error, and no horizontal overflow at **1280×720 desktop** or **390×844 mobile**. All four static assets served HTTP 200. Other three Sauce systemd services stayed active.

**Code QA:** \`14 passed\` focused event-planner tests, and \`34 passed\` in the combined camera, native-capture and existing recorder regression selection. The main checkout was synced fast-forward and kept clean. Real render ran isolated in a transient systemd scope with no paid inference.

## Customer-value verdict and next step

This gives Sauce a **distinct second-site source-true review candidate**, not its second approved commercial-quality demo. The old Linear source is an interactive marketing preview, and this player does not show account ownership, actual customer workflows, or a personalized narrative. Its 720p source upscales, dense silent UI, and close-up reading rhythm remain subjective review points. The repaired Brimble film remains a separate first-site review candidate.

**Next highest-value action:** Test the same evidence-gated action-first camera grammar on a *new native-resolution real product-action capture*, rather than creating more static marketing tours or building a pricing/billing system. Hold the paid pilot gate until three distinct films pass real visual review. Then put a small honest early-access offer before qualified buyers. No inference spending, outreach, checkout or VM migration was done in this pass.
