# Sauce — autonomous source-true shot coverage (2026-11-21)

Status: owner-only, source-verified research; ZERO human-approved premium films.
GitHub main only, existing persistent Vultr worker, no new compositor.

## Reusable production-independent behavior

- scripts/autonomous_shot_coverage.py consumes an immutable real Chromium MP4 and a verified event/pointer sidecar. Original SHA256 hashes, native event indices/timings, measured result/target rectangles, and actual mouse-approach samples determine camera timing. No per-website coordinates, LLM prompts or manual editing.
- Source-measured result area selects small-card or large-panel framing. Six small-card camera candidates or four large-panel candidates are generated automatically. Original Sauce spatial projection checks opening context, original cursor-tip/target onscreen, real result area/readability and camera-cut safety. Original renderer validate-only and source_director_preflight independently reject illegal candidates.
- When source lacks a genuine approach before an action, no fake cursor zoom is generated; source-wide context is restored where feasible. Cut/result frames cannot precede observed real outcomes.
- Up to two distinct passing candidate types are rendered. Each encoded MP4 undergoes existing source-relative QA. REJECT films stay private and are not auto-selected. Every status says creativeApproved=false and noAutoPublication=true.
- scripts/auto_public_ui_film.py now supports optional --director-mode coverage using the existing allowlisted, source-verified public URL capture. Its existing Gemini default, private output policy and sandbox restrictions are unchanged. This mode needs no model key or external creative agent at runtime.

## Verified Resend input and 3-film comparison

Reused an existing source-true editorial trim of a REAL independent Chromium Resend pricing capture: 10.2166667s, 613 native source frames, 2880x1800 DPR2 60fps, three original price outcomes ($35/$160/$350 per month) and 325 genuine pointer samples.

Edited source SHA256: 6973a247624d514aa75b8d10c45a01a022942f2597f251c65aeb7d91a95ff586
Event manifest SHA256: efd1843cd6668b089f1fd41dfbd3db0263432a6da82e453daaf66d3d776e9168

A: unchanged earlier source-event control film SHA256 49e6b668c64f1d2a7f5fefec0e255d6f43f679fa653db65c9404209885d8154a. Objective REJECT: STATIC_OPENING_2S.
B: new autonomous restrained camera coverage SHA256 420085cbe724f167d75084e4dd4c10bd25cbdb96f2f2c1013d48e7a2608171bb. Objective HUMAN_REVIEW_REQUIRED, zero objective findings, NOT creatively approved.
C: contrasting fast source-event cut SHA256 90ba404d0f324380e85eb3d3bb14316cf525f2bb96a8fc53926051fca7035b15. Objective REJECT: REPEATED_OR_STATIC_FRAMES.

All source-true, genuine MP4 H264 1920x1080 60fps / 613 frames + AAC stereo 48000Hz. Existing Foley clock preserved. Full FFmpeg decoder check, real desktop 1280x720 and mobile 390x844 Chromium play+seek succeeded for B/C. Signed HTTP200, unsigned HTTP403, 72-hour private review:
A: https://devmcp.davemafy.xyz/sauce-expiring-review/tweakcn-20261120/sauce-resend-coverage-A-control-20261121.mp4?md5=uMFiZFhmQEIndoXFcSZ_OA&expires=1795560677
B: https://devmcp.davemafy.xyz/sauce-expiring-review/tweakcn-20261120/sauce-resend-coverage-B-smooth-20261121.mp4?md5=GGt31DYLPTU5K29iJDa-Og&expires=1795560677
C: https://devmcp.davemafy.xyz/sauce-expiring-review/tweakcn-20261120/sauce-resend-coverage-C-punchy-rejected-20261121.mp4?md5=PkKoYIOQLGmGAnnmqtIFdA&expires=1795560677

## Independent real-site holdout: Tweakcn

Reused the existing source-authentic 16s 2880x1800 DPR2/60fps capture of https://tweakcn.com/editor/theme (SHA256 c9d4811286c354d5bcc1fe4a703e8059f409138b1bdc7d90ac58626f20585c35). Genuine Marketing, Dashboard, Application tab switches, original cursor and real displayed preview changes. The small-card framing was correctly rejected for a clipped large result panel. Geometry automatically selected context-preserving panel coverage; four plans passed original strict renderer. The two rendered results (panel_soft, panel_punch) BOTH failed existing encoded QA: LOW_VISUAL_DETAIL. Original page is dark and dense. The owner-only wrapper returned coverage_failed_source_retained, without asserting success. Not general unknown-SaaS proof.

## Actually viewed visual difference and remaining failure

Opened actual A/B/C and Tweakcn original/rendered contact frames and privately held 10.37s Screen Studio UI motion-study reference. B has stronger authentic pricing focus, meaningful cursor actions, and passes bounded negative checks; nevertheless it still resembles a dark browser crop, with secondary text too small on mobile. C's faster cuts did not cure boring source holds. Tweakcn's dense UI yields weaker result clarity.

No independently source-verified component clean plates are included in these particular captures; independently animated spatial layers were therefore NOT fabricated. Next actual creative milestone is a verified new capture with component/clean-plate provenance and a genuinely strong separate foreground reveal, then multi-shot integration and reference review. No $50k premium approval, new VM, new branch, production deployment, credentials/public source artifacts, paid purchase, or public release.
