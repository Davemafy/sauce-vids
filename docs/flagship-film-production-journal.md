# Sauce flagship film — production journal

Project: **Brimble · Connect your agent**. Workspace `/opt/sauce-vids`; Git branch `main`. Private capture is never published. Primary source URL: `https://www.brimble.io/`; the shot uses only the verified `Connect your agent → Codex → Copied. Paste it into your terminal` interaction.

## Creative direction — "The interface is the scene"

A real web product is the protagonist. A restrained charcoal gallery environment, sharply displayed actual UI, subtle physical screen border, single unobtrusive cinematic pointer, no wallpaper glows. Establish context, show one specific action, linger on the genuine copied-command result, and finish on Sauce's authorship. No fake browser chrome, counterfeit UI, model-invented code diff, or moving optics for their own sake.

Reference study: Screen Studio's documentation explains separate cursor data and independent output rendering and provides controlled smooth/rapid cursor motion and differentiated screen/cursor blur. Technique adopted: **separate the single native website cursor from the composited film pointer**, make the click position authoritative. Source: https://screen.studio/create/product-demo-videos and https://screen.studio/guide/animations. Raycast's September 2026 AI launch film uses a long product-led introduction, readable UI shots, shot changes motivated by feature beats rather than indiscriminate motion. Technique adopted: **let the user understand the interface before committing to a camera change**, scaled to the short runtime. Reference: https://launchscene.app/v/raycast-ai-automations?play=1&s=55.

## Iteration 0 — Rejected starting film

Render: `studio/.tmp/three-layer-qa/master-1080p60.mp4` (2.933 s, 176 frames). Starting Git commit `f2a1ad7`. Technical validity: H.264 1920×1080/60fps, AAC 48 kHz; shader uniforms sample-synchronized.

| Category | Score (1–10) | Actual evidence |
|---|---:|---|
| Storytelling | 3 | 00:00–00:02.93: product → modal → copied command compressed beyond reading time |
| Visual direction | 3 | Purple, heavily illuminated empty stage; effects unrelated to Brimble identity |
| Composition | 4 | 00:00 browser window too small for text; source website competes with stage |
| Motion | 3 | 00:01–00:02 modal scale and separate callout fight with the cinematic pointer |
| Readability | 3 | 00:01–00:02 strong blur obscures surrounding action context |
| Sound | 5 | Seven Foley cues in under three seconds; verified output sample clock, subjective loudness requires an actual listening pass |
| Overall production | 3 | Artifact is an engine proof, not a shippable SaaS launch film |

Hard blocker verified at original `studio/.tmp/curated-traces/brimble-connect/states/001-approach.png`: large black photographic bee overlaps native "Connect your agent" button. DOM inspection traced it to an animated `<img src="/assets/bee-cutout-DXbVAaRy.webp">`, inside `pointer-events-none` decorative positioning. This was **source-site presentation, not Sauce's SVG pointer**. The independent Sauce callout renderer also drew an extra oval arc, decorative top line, and a physical connector below its badge. Both systems were interfering with a clean cursor story.

Corrections:
1. Recapture using a strictly allowlisted, presentation-only hide rule for the decorative bee image. The DOM still gets real hover/pointer/click events.
2. Remove the duplicated Sauce pill and connector from the flagship compositor; keep Brimble's real, single-silhouette button.
3. Use fixed-timestep `120/18/1` cursor spring and assert the true recorded click landing within three CSS px.
4. Replace the purple scene with a charcoal physical studio matte and 1644-pixel-wide actual site, no refraction, caustics, artificial modal blur or extra cursor rings.
5. Put moderate, bounded modal zoom and perspective only in comparators that justify them. Source and source clock stay identical across A/B/C.

## Capture V2

Private `studio/.tmp/flagship/capture-v2/` has six SHA-backed 2560×1440 screenshots and matching verified workflow/HAR. Recording is about 5.97 seconds between first and last capture evidence. New `001-approach.png` and `002-click.png` inspected at native resolution: Brimble icons, edges and the button are intact; the bee has disappeared. The overlay selector is explicitly recorded in the private session manifest. Previous capture remains untouched for forensic comparison.

## Iterations

_Automatically appended only after a complete render has been inspected; weak or blocked releases stay classified unfinished._

### A — Clean V1 (reviewed, not release-ready)

File `studio/.tmp/flagship/clean-v1/master-1080p60.mp4`. Real 380-frame, 6.333-second export at 1920×1080/60fps, 48kHz AAC; four source-clock Foley cues. Same private capture V2; no fake product states. Six frame samples at 0–5 s and the actual modal at native resolution were inspected. The clean charcoal stage and narrow screen border replace the old purple aura and artificial floor. The 1644px-wide window makes the page sharper than the old 1480px rendition. The primary cursor is the only generated pointer; the bee image was hidden **before SHA-verified capture**; callout duplication/ring/leader line are disabled.

| Story | Art direction | Composition | Motion | Readability | Sound* | Overall |
|---:|---:|---:|---:|---:|---:|---:|
| 4.5 | 5.5 | 6.0 | 5.0 | 6.5 | 5.5 | **5.5** |

00:00–00:01: too much unmotivated whitespace; 00:01–00:03: modal is visible, but there's no obvious first impression or editorial arc; 00:03–00:06.33: static ending, copied command lives inside a small dialog with no final resolution. No longer visually defective; not a flagship advertisement. Highest-impact correction: title → clearly filmed action → authentic response → authored Sauce endpoint, and progressive detail framing after copied state.

### B — Cinematic V1 (reviewed, not release-ready)

Source `studio/.tmp/flagship/cinematic-v1/master-1080p60.mp4`; editorial edit `studio/.tmp/flagship/cinematic-edit-v1/master-1080p60.mp4` (554 frames, 9.233333 s; 78-frame opening, 380-frame verified product, 96-frame closing). Reuses source capture V2 and 48kHz sample clock, and uses mild perspective/zoom without fabricated spotlights. Frame samples reviewed at 00:00.65 (intro), 00:01.60 (establish), 00:02.80 (dialog), 00:04.55 (Codex response), 00:06.70 (result), 00:08.35 (Sauce close). A full-native-resolution still at 00:04.30 confirmed the actual copied command and button text remain legible, without the earlier black insect or duplicate oval.

| Story | Art direction | Composition | Motion | Readability | Sound* | Overall |
|---:|---:|---:|---:|---:|---:|---:|
| 7.0 | 6.5 | 7.0 | 6.0 | 7.0 | 6.0 | **6.5** |

0:00.0–0:01.30: editorial intro explains the interaction but remains typographic rather than product-led. 0:01.30–0:02.60: establishes real screenshot without hero camera motion. 0:02.60–0:04.50: modal opens at the recorded timestamp, remains sharp and in context. 0:04.50–0:07.63: overlong unchanging second half; copied text has no dedicated detail reveal. 0:07.63–0:09.23: Sauce end card clear, but its original tagline was too generic and was revised. Main correction in V2: reveal the copied-command result with a source-clock-triggered detail camera ease-out cubic and restrained section labels outside the captured UI.

### C — Experimental V1 (reviewed, rejected)

File `studio/.tmp/flagship/experimental-v1/master-1080p60.mp4` (380 frames at 60fps, WebGL2 optics). Four synchronized frames were compared directly at 0.60, 1.65, 3.10 and 5.30 s with A and B. Cinematic lighting retains adequate clarity, but the existing WebGL post-process grain/vignette adds an unnecessary perceived layer and inflates the file from ~2.1MB to ~14MB, without a meaningful improvement in depth or storytelling. No gimmick is worth this tradeoff. It is not the preferred direction.

| Story | Art direction | Composition | Motion | Readability | Sound* | Overall |
|---:|---:|---:|---:|---:|---:|---:|
| 4.5 | 5.8 | 6.0 | 6.0 | 6.0 | 5.7 | **5.8** |

*Sound scores provisional: the audio streams, cue counts and decoded waveform/timestamps were inspected, but subjective full-playback listening has not been independently verified by a human listener. No creative score of nine is claimed.*

### Production decision

**B is the strongest of A/B/C but fails the acceptance gate.** Keep B as a candidate, reject C's optics. V2 adds stronger grounded story beats and a dedicated recorded-outcome detail framing. Do not publish any version as the final Sauce flagship unless it passes all seven categories, including actual audible review.

### B — Cinematic V2 / selected working candidate (not final)

Raw verified workflow `studio/.tmp/flagship/cinematic-v2/master-1080p60.mp4`; edited 9.233333-second candidate `studio/.tmp/flagship/B-edit/master-1080p60.mp4`; public review player `https://devmcp.davemafy.xyz/sauce-motion-phase2/flagship-review/B/`. The same original footage appears in the full-length A/B/C edits. All comparison masters share exactly 554 frames at 60fps, including the identical 78-frame opening, identical 380-frame source timeline and 96-frame ending. No UI/application functionality was invented.

**Actual encoded film review, cold:** at 0:00–1:30, typography makes the task clear, but it is still a simple title card; at 1:30–2:39, the product appears with a credible matte and single cursor; 2:39 first click lands on genuine Brimble button; a real modal opens and stays legible without forced blur; 4:20 the verified Codex click happens; subsequent copied command stays visible while a 400ms ease-out cubic begins a distinct, modest detail-camera progression; 7:63 the closing edit reveals Sauce. The finale ends at 9:23. There is **no duplicated Sauce callout, second oval stroke or leader line** in these decoded review frames. A six-phase pixel contact sheet from the actual B source master covers cursor approach, acceleration, contact, modal and settlement: `studio/.tmp/flagship/audit/cursor-six-phases.jpg`.

**A further actual encoded-film defect was found and corrected**: the first edit faded the opening almost to black at 1.28s, then jumped to a bright screen at 1.30s. It also inserted a black flash at 7.63s before the end card. The corrected cut now maintains the title's measured brightness (~24.6/255) through 1.28s, cuts directly into the product at 1.30s, and cuts from product to a lit Sauce card at 7.63s (~27.5/255), not zero. No extra crossfade ghost images were introduced.

Sound: the first complete edit had *mean* −47.3 dBFS and a peak −16.5 dBFS, leaving most of a nine-second film effectively empty. The revised edit incorporates a deterministic, original 48kHz three-tone ambient bed with gentle fade boundaries, without introducing licensed samples or unearned UI actions. Measured final decoded mix: **mean −28.4 dBFS, peak −14.1 dBFS**; actual 48kHz PCM receipt contains exactly 443,200 samples, equal to 554 film frames × 800 samples. Six cue events in the final source B pass, preserved at the source-to-output clock mapping. Audible human evaluation remains outstanding; signal levels alone cannot certify musical taste.

#### Independent release scorecard — V2

| Category | Score | Observed reason |
|---|---:|---|
| Storytelling | **7.5** | Real sequence is intelligible (intro → select Codex → copied command → Sauce); however the experience ends with copied setup text, not an actual connected, working agent |
| Visual direction | **7.2** | Artifact-free neutral studio and restrained title cards; still conventional and not distinctive enough to serve as Sauce's signature visual identity |
| Composition | **7.5** | Larger 1644px capture, stable bordered window, preserved context. Brimble's original ample white space remains under-directed in establishing shots |
| Motion | **7.2** | Click-locked spring pointer, action-led modal easing, explicit final detail shot. The shot grammar remains short of outstanding motion direction |
| Readability | **8.0** | Native MP4 dialog/command text clear at 1080p; preview requires a desktop-size viewer for the smallest terminal text |
| Sound | **7.0 provisional** | Foley and original pad sample-aligned, improved measured level. Full human listening and mix taste check outstanding |
| Overall production quality | **7.4 — FAIL** | Material improvement over baseline, no glaring duplicate pointer, but not an independently publishable 9/10 flagship film |

No score is inflated for tests passing. The absence of a true outcome scene and conventional 2D shot composition are the largest creative deficits. The 9/10 gate is **not met**. A stronger authorized Brimble journey (agent handoff, a real terminal result or deployment outcome) and an actual listening/viewing signoff would be needed before calling this a flagship advertisement. This candidate must not replace the public product homepage or be labelled "final".

### Production and test receipts

- **Single pointer:** screenshot metadata explicitly records presentation-only hiding of `img[src*="bee-cutout-"]`. Rechecked six SHA-backed capture states. Brimble pointer/hover/click behavior preserved; exactly one Sauce `CinematicCursor` overlay is drawn. Flagship disables `KineticCalloutRenderer` (second oval, arc and leader line) and disables click-ring graphics.
- **Contact accuracy:** recorded first pointerdown at source video frame 65 has 1.1788 CSS-pixel residual; second at frame 174 has 1.6721 CSS-pixel residual; both under the 3px threshold. The pointer track uses 120 stiffness/18 damping/mass1 at fixed dt=1/60; optional badge is a separately precomputed spring and does not alter contact.
- **Lighting and blur:** flagship matte has no artificial purple glow, no shader-caustic overlays, no forced spotlight blur, no source UI text resampling beyond DPR2→1644px Lanczos. Experimental WebGL postprocess was rejected for the chosen treatment. Native source type remains actual website pixels.
- **Frame/audio timeline:** H.264 1920×1080, exactly 554 frames at 60/1; one AAC stream at 48000Hz, duration metadata 9.233000s versus video 9.233333s (AAC packet rounding ~0.33ms). Offline WAV length exactly 554×800 samples. Full MP4 FFmpeg decode passed with zero errors.
- **Existing tests:** 165 Python `unittest` checks, one skipped; 13 Phase 2/3 pytest passed, two skipped; 21 StudioMotion TypeScript passed; 12 app/web tests passed; both web and Remotion TS typechecks passed; seven Playwright browser E2E tests passed. No user-facing Studio/landing changes.
- **Public candidate:** `https://devmcp.davemafy.xyz/sauce-motion-phase2/flagship-review/B/`; A and C under sibling paths. Full MP4 reports `HTTP 200` and partial-media `HTTP 206`; contact sheets under the same `flagship-review/` directory.
- **Selected candidate:** B V2. Rejected A for flat direction and C for noise, exaggerated optical cost and distracting processing. Prior films are retained privately.

### Current status

**UNFINISHED BY DESIGN.** The existing work can be publicly examined as a *candidate* but does not meet the stipulated 9/10 overall and every-category-8/10 threshold. Requirements not fully closed: independently heard full-sound review, richer verified product outcome footage, and a further high-level creative direction pass. Preserve the candidate and source/correction history; do not silently promote it to an accepted flagship on a later restart.

---

## Iteration V3 — Brimble's real homepage becomes the opening

Capture `studio/.tmp/flagship/hero-v1/verified-hero.png` and `manifest.json` came from public Chromium at DPR2, 2560×1440, scrollY=120. SHA-256: `51b9b2346c85d73b2d3b58d99d5a336ca367808e3a6c6a4ff1936dee487a2b19`. The separate interaction trace keeps its source-only presentation suppression of the *mouse-following decorative bee*. The bee is preserved in the real homepage shot, where it is genuine Brimble visual identity, not a duplicate pointer.

Film `studio/.tmp/flagship/B-v3/master-1080p60.mp4` contains 608 frames at 60fps (10.133s): 132-frame genuine homepage hero and very gentle camera pullback, 380-frame real Codex setup workflow, 96-frame Sauce ending. Cold review frames: 00:00.15 actual bee photograph; 00:00.85 readable Brimble H1; 00:02.20 verified Connect Agent shot; 00:03.75 modal; 00:05.60 copied response; 00:08.85 Sauce closing. No synthetic website state or fake scrolling.

Scores: storytelling **7.7**, visual direction **7.4**, composition **7.6**, motion **7.2**, readability **8.0**, sound **7.0 provisional**, overall **7.6/10 — FAIL**. At 00:05.8–00:08.1 the copied-command result holds with almost no editorial change. Correct by preserving the real successful click, cutting later idle, and creating a separate high-DPI result insert.

## Iteration V4 — photographed outcome, not a simulated connection

Film `studio/.tmp/flagship/B-v4/master-1080p60.mp4`: 579 frames / 9.65s. The new `flagship_story_v4.py` independently verifies the SHA-backed result screenshot (`capture-v2/states/005-wait.png`) and the capture's original `expect_text` assertion before constructing a 90-frame **editorial photographic close-up** of the actual copied command. Timeline: 132-frame hero → 261-frame actual cursor workflow → 90-frame verified result still with a 2.6% camera push → 96-frame Sauce ending. No invented terminal execution, authentication or deployed agent.

Visual cold review: 00:03.40 modal open; 00:04.80 recorded choice; 00:06.50 verified copied response; 00:07.30 large crisp source-verified two-line command; 00:08.30 Sauce. The cut into the detail at 00:06.55 is editorially intelligible and source context remains recognizable. Scores: storytelling **8.1**, art **7.6**, composition **8.0**, motion **7.4**, readability **8.5**, sound **7.0 provisional**, overall **7.8/10 — FAIL**. The film finally has a distinct result scene, but cursor glides could be more natural. Continue only with a subtle 180-degree shutter on the pointer, not text.
## Iteration V5 — selected review candidate, NOT a finished flagship

**Private master:** `studio/.tmp/flagship/B-v5/master-1080p60.mp4`, SHA-256 `1c8a382a669bd860603ac551abc268b48f648948d7d762d18a71588f5adba703`. **Public candidate player:** https://devmcp.davemafy.xyz/sauce-motion-phase2/flagship-review/V5/ . The canonical recorded action source was rerendered as `cinematic-v3/master-1080p60.mp4`. Fast cursor glides receive a bounded, centered, 5-tap premultiplied-alpha 180° shutter with a maximum exposure distance of **2.4 physical pixels**. There is no frame-blended double cursor. This filter is disabled exactly at button contacts; the real website UI receives no indiscriminate motion blur.

**Actual decoded film at 60fps, 1920×1080; 579 frames, 9.65s:**

- **00:00.00–00:02.20:** photographed real Brimble homepage with the genuine bee and H1, one subtle 3D-style camera pullback, real app visible from frame zero
- **00:02.20–00:03.30:** real agent-connect section, accurate spring cursor arriving at actual Connect Agent click
- **00:03.30–00:05.10:** real modal opens, original Brimble controls stay in context; no synthetic callout, duplicate oval or leader line
- **00:05.10–00:06.55:** genuine Codex choice and actual source-verified copied-command feedback
- **00:06.55–00:08.05:** deliberate 1.5-second editorial insert showing the SHA-verified copied command at higher native-pixel detail, no claim of completed authentication
- **00:08.05–00:09.65:** Sauce end mark; visually simple and still conventional

### Independent creative scorecard — V5 (failing release gate)

| Category | Score | Observations tied to decoded film |
|---|---:|---|
| Storytelling | **8.1** | Actual product establishes at 00:00; two-click sequence and physical result at 00:06.55 are intelligible. Still no real connected agent outcome |
| Visual direction | **7.6** | Distinct Brimble bee image and disciplined matte; Sauce end mark at 00:08.05 remains generic rather than ownable |
| Composition | **8.1** | Product stays dominant; the 1644px wide browser and 00:07.30 modal detail are readable. Outcome cut is deliberately abrupt but accurate |
| Motion | **7.7** | 120/18/1 deterministic spring, intentional detail cut and restrained zoom, shutter only on fast cursor movement. Less editorial expressiveness than exceptional launch films |
| Readability | **8.5** | Native capture has crisp headings and 00:07.30 copied command; smallest 720p preview details remain difficult on mobile |
| Sound | **7.0 provisional** | Original low-level three-voice bed and six genuine Foley cues; encoded mean **−28.4 dBFS**, peak **−15.4 dBFS**. Listening taste has **not** been independently certified |
| Overall production quality | **7.9 — FAIL** | A credible and materially better product demo, not yet a publishable 9/10 Sauce flagship |

The V5 film is the strongest comparative direction. A is too static, C's reflection/chromatic shader layer is distracting and inflates files; B provides restrained framing, V5 adds the real hero, outcome and cursor-only shutter. No category scores were increased for technical test counts. No version is presented as a completed flagship advertisement.
### V5 source-integrity and engineering receipts

`studio/.tmp/flagship/audit/B-v5-verification.json` was generated by `scripts/verify_flagship_release.py`, not manually invented. It asserts full MP4 decoding, exact stereo WAV samples, H.264 1080p60, true audio alignment, a replayed actual source session, SHA-verified real Brimble homepage and result state, bounded output-frame click errors and absence of unexpectedly black frames at edit cuts.

- Video H.264 exactly **579 frames**, 1920×1080 **60/1fps**, 9.65s; audio AAC **48,000Hz**. Underlying PCM **579×800 = 463,200 stereo sample frames**. No accumulating audio/video drift. The independently decoded master passed `ffmpeg -xerror`.
- Verified two actual pointerdown contacts: source frame 65 CSS error **1.1788px**, conservative projected 1080p output error **1.8471px**; frame 174 CSS error **1.6721px**, projected output error **2.6201px**. Both under the **3px hard gate**.
- Image obstruction regression: in the actual 2560×1440 source screenshot around Connect Agent, percentage of dark bee-contaminated pixels is **0.00042**, versus 0.1069 in the old blocked capture. Presentation-only narrow suppression of `img[src*="bee-cutout-"]` is recorded in the private `sauce.session.v1` trace. The legitimate bee is **preserved** in the independent real homepage shot. No source icon, actual click control, source event or hover target was deleted.
- The double-stroked synthetic pill, leader line and clicking ripple are disabled **in the flagship compositor**, not erased in final pixels. The original code is preserved for unrelated presets. Only Sauce's `CinematicCursor` is composited into interaction frames, and its exact-contact shutter is a no-op. Static website typography is never motion-blurred.
- Verified *real encoded output*, not just generated screenshots: 5 frames around each hard cut were decoded and luminance-checked for black flashes; none failed. The six-phase original film source audit is `studio/.tmp/flagship/audit/cursor-six-phases.jpg`; selected film audit `studio/.tmp/flagship/audit/V5-verified-sequence.jpg`; matched A/B/C/V5 source-event comparison `studio/.tmp/flagship/audit/ABCV5-source-frame-aligned.jpg`.
- Public player and master media return HTTP **200**; byte-range 1024-byte request returns **206**. Playwright loaded, played and measured progress at both 1440×900 desktop and 390×844 mobile with no horizontal overflow. The public files contain **no private capture HAR** or session event dump.
- Existing Stage/TypeScript/Python/app/browser regression records remain to be rerun and summarized with the final Git commit (initial 166 Python checks passed, one skipped; follow-up shutter tests passed). The production rendering is deliberately separate from the Studio application and landing UI.

### Outside craft research; specific lessons

Screen Studio's [animation guide](https://screen.studio/guide/animations) documents cursor-only motion treatment separately from whole-screen movement blur: selected film keeps that separation, with explicit click-frame sharpness. A [November 2026 frame-by-frame analysis of nine software launches](https://demosmith.ai/blog/saas-product-launch-video-examples) emphasizes showing an actual product early and using distinct narrative beats. We adopted authentic Brimble source pixels at frame zero and an outcome-specific close-up, without copying any outside video or style assets.

### Release gate: **UNFINISHED**

Our 9/10 overall / ≥8-every-category gate remains unmet. Main blockers are **no actually connected working-agent outcome** (only verified copied setup command), **Sauce's own brand treatment still generic**, less expressive cinematography than a top-tier launch and no independent full audible human approval. Preserve the current V5 candidate and all previous film files. Next improvement should record a richer *authorized and provable* real agent outcome or develop a substantially stronger branded film concept; nothing may fabricate agent connection. Re-critique the whole encoded film with a human listener, and only relabel final if all seven measured scores pass.

### Final regression receipts for this turn

- Python: `python -m unittest discover -s tests -q` → **168 tests, 166 passed, 2 skipped**. Includes source image obstruction, single-pointer policy, 180° cursor shutter/no-ghost contact, spring determinism and real capture evidence checks.
- Phase 2 and Phase 3 integration: `SAUCE_BROWSER_TEST=1 python -m pytest tests/phase2 tests/phase3 -q` → **13 passed, 2 skipped**.
- TypeScript StudioMotion → **21/21 passed**; web app Vitest → **12/12 passed**; web and Remotion Studio `tsc --noEmit` → **passed**.
- Web Playwright browser E2E → **7/7 passed**. Tested desktop/mobile Studio, real preview, deny-cross-origin render submission, and existing landing. Untracked Playwright screenshot byproducts preserved privately under `studio/.tmp/flagship/audit/web-e2e/` and removed from working tree.
- Public **V5 review** at `https://devmcp.davemafy.xyz/sauce-motion-phase2/flagship-review/V5/`: HTML5 video played with actual currentTime progression at both 1440×900 desktop and 390×844 mobile (zero horizontal overflow); `/V5/master-1080p60.mp4` returns HTTP 200, byte range returns HTTP **206**, no private HAR or source traces exposed.
- `python -m compileall -q scripts`, `git diff --check`, exact 48-kHz sample count, decoded full encoded MP4, source SHA checks, 3-pixel projected click gate, and black-flash check all passed. This is **engineering completion of a review candidate**, **not artistic acceptance**.
