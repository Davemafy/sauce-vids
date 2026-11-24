# Sauce — fresh URL-only native-60 capture and licensed sound (2026-11-24)

**Mission:** The user explicitly demanded a real customer experience: *paste one public URL, Sauce alone discovers, captures, directs, renders and critiques*. No reused footage, model-generated UI, handcrafted action ID or hand-edited camera plan. This work is on existing persistent Vultr 8 vCPU/16 GiB worker, latest GitHub **main only**, isolated API worker; no production service restart or additional infrastructure.

## Real problem and verified source capture

The legacy customer product pipeline used Playwright's `record_video_dir` recorder, yielding **25 unique-source-frame timestamps/second** and then exporting resampled H264 at 60fps. An encoded stream marked 60fps was not real native60 capture.

Found **already installed** full headed Chromium `/opt/continuity-remote/chromium/chrome`, Xvfb and system FFmpeg with x11grab. Implemented strictly **opt-in** `SAUCE_CAPTURE_MODE=x11grab60` in `backend/native60_capture.py` and `backend/live_capture.py`. Each job starts a dynamically allocated, private 1920×1200 Xvfb display, headed Chromium with actual 1920×1080 CSS viewport at DPR2, independently calibrates original Playwright screenshot pixels against the visible X11 display, then captures **only the page** at 1920×1080/60 (no Chrome address bar). The X11 display's extra 120px accounts for browser toolbar. Capture source H264 MP4 is written to a private `continuous-source.mp4`; legacy `continuous-source.webm` is left unchanged. Per-source hash and exact source filename in the receipt are verified by renderer, QA and saved-checkpoint/revision loader. Xvfb and FFmpeg processes are stopped on completion/error. A mismatch in geometry, actual source dimensions, source codec, FPS, source file sha, or proven source format fails closed.

Native60 calibration sample before integrating: Playwright native page vs actual X11 crop gave viewport Y=87px and mean full-frame RGB error **0.7908/255**, correctly identifying/removing Chrome's native top bar. The first 300-frame 5s actual 60/1 video had **98/100 changing consecutive frame pairs during active scrolling** (mean diff >.2 on 320×180 grayscale), and zero during a genuinely static tail. This proves the recorder can retain actual browser scene changes at original 60Hz, not merely rename a Playwright 25fps file.

## Real fresh customer URL-only execution

Submitted exactly `POST /v1/jobs {"url":"https://mantine.dev/core/modal/"}` to an isolated current-main Sauce customer API with opt-in native60. Sauce itself inspected the live URL, used bounded candidate exploration to reject unsafe/login and tiny public outcomes, selected the genuine `Open modal` control `a25` and verified an independently captured public DOM result before recording. No manual action ID, plan, or reused source. Gemini was unavailable in the isolated run; **`ai_calls=0`**, and this is the deterministic source-grounded fallback, NOT a Gemini-authored story.

Intermediate **native-60-only** job `7791b6833cca1b53e4ed15fb` produced fresh 432? actual source 433 frames ~7.22s and a new 1920×1080/60 master. Encoded QA `REJECT` only because no audio. That separate original source was not reused for the final customer film.

Final fresh **native-60 + pinned CC0 music** job `81b5dde97ffbc22581c3aa51` completed source inspection → observed verified action → recording → camera → render entirely automatically. The private evidence is `../.sauce-stagehand-private/customer-fresh-mantine-native60-music-20261124/jobs/81b5dde97ffbc22581c3aa51/`. A new native60 original source `private/motion/continuous-source.mp4`, SHA256 **`ac6ba65d2b974f74d86627288154b64831a222a9eba88c6c5f4d9fdd201bedc2`**, H264 1920×1080 60/1, **432 actual captured frames/7.2s**, Chromium CSS 1920×1080 DPR2, viewport top Y=87, independent screenshot average difference **0.465/255**. Frame-by-frame 320×180 decoded source inspection: in second 1–2 (active browser motion) **60/60 consecutive frame pairs change**; static post-result section predictably remains unchanged. This is 60Hz sampling of actual Chromium output; *not a guarantee of 60 changing pixels in an idle UI*.

Final MP4 `export/master-1080p60.mp4`, SHA256 **`42de097bac8f8bc6242320b3f262e5470b9b66846ed0ce5eb4e6e9d25b21a64f`**, **282 frames** at 1920×1080/60, H264 + **stereo AAC 48kHz**, format **4.716s** (video track 4.700s, AAC padding), full FFmpeg decode **PASS**; preview 1280×720/30 with stereo AAC48k. Source click and real visible modal are preserved. Actual encoded contact sheet and side-by-side full-image source-vs-film comparisons at t1.4/1.8/2.4s examined: the modal is genuine, becomes readable at full camera push; no copied UI, no fake success. The show remains too simple to sell as a premium film.

**Final encoded-quality gate:** `HUMAN_REVIEW_REQUIRED` with **zero** automatic findings, explicitly **`creative_approved:false` / `release_eligible:false`**. It is a source-proven *customer film candidate*, not an owner-approved premium reference. Source audio RMS after licensed mix ~-26 to -29dB in opening, peak -12.1dB; not empty/synthetic silence.

## Genuine license-pinned soundtrack (opt-in)

Found worker's earlier private, not-Git-tracked FMA CC0 catalog and downloaded/verified a fresh official [Free Music Archive page](https://freemusicarchive.org/music/play-house/songs-1/tent-1/) for **Tent by Play House**. Page visibly states CC0 1.0 Universal and links to Creative Commons Zero 1.0. Private original FMA evidence `.sauce-music-private/licensed-confirmed-20261124/tent-fma-cc0-20261124.html`, SHA256 `808200ab85e98bd049a37c9b2db4b7c7080db7e0afa10654c76fda25943ae1dd`. Original private MP3 `.sauce-music-private/tracks/tent.mp3`, SHA256 `2e0307a01ad005980c2e7671c50830bf6a9fefe3bb780365485d5738eb859d9f`; catalog hash, strict FMA CC0 license HTML and operator evidence SHA verified at runtime.

`backend/licensed_music_bed.py` requires **all** of `SAUCE_CC0_TRACK_ID`, `SAUCE_CC0_CATALOG_PATH`, `SAUCE_CC0_PROOF_PATH`, `SAUCE_CC0_PROOF_SHA256`. If track ID isn't set, no music is added. If configured evidence/track fails hash or CC0 license, job **fails closed**. For audio=auto and no source-verified narrated pricing, a restrained source-licensed track is muxed into the actual 60fps master with a quiet linear gain/fades and 48kHz AAC stereo. Stream-copy preserves exact H264 picture packets; dedicated test verifies identical original video stream hash after mux. Browser source remains untouched. No generic click samples or artificially silent soundtrack. Audio=clean and price-verified voice workflows retain their prior semantics.

## Code, safety, tests

- `backend/native60_capture.py` — exact viewport pixel registration, safe process lifecycle, native x11grab60 + source proof.
- `backend/live_capture.py` — opted-in headful Chromium/Xvfb original source capture without changing the default 25fps helper.
- `backend/live_render.py` — strictly validated dual source format, genuine source60 receipt, licensed AAC in actual master **and preview**, truthful output/receipt provenance; no audio if unconfigured.
- `backend/job_store.py` / `backend/sauce_api.py` — hash-bound job recovery and private revision correctly reuse the **exact** source filename; remain backwards compatible with original .webm jobs.
- `backend/licensed_music_bed.py` — CC0 music provenance and bounded mixer.
- `tests/test_native60_customer_audio.py` — 7 tests: viewport alignment/no toolbar, mismatched/forged source metadata, safe source filenames and mode, CC0 independent license proof, tampered music, original bitstream preservation, 48k AAC.
- Full prepublication QA: **546 Phase 2 passed, 10 skipped, 21 subtests; 369 legacy unittest run, 2 skipped, zero failures**, `git diff --check` clean. A clean checkout after main publication is still required.

## Honest remaining defects and deployment boundary

1. **No owner-approved premium film.** The original Mantine source is a documentation page with a fairly small modal; even an improved 2.1× camera and licensed house track do not create a strong product story or cinematic taste.
2. **Latest-main runtime still isolated.** Existing live production `sauce-url2video.service` uses older Nov 17 code, was NOT restarted or upgraded. To use native60+CC0, service must be explicitly deployed with env flags after owner-approved operations; otherwise existing customers still see legacy behavior.
3. Native60 uses a headed Chromium/Xvfb capture on the 8 vCPU/16GiB worker and consumes more CPU than 25fps Playwright. It has proved one good public interactive page, **not all URLs**, browser/GPU variants or multi-job capacity. Failure is explicit; no silent source-fps mislabeling.
4. The customer renderer still uses the older neutral Shotcandy window, not the user's preferred cobalt-cloud large floating acrylic window. Full stage/hook integration needs additional source-safe QA.
5. Music is a **CC0 test selection**, not owner creative approval. The single track is operator-configured, not intelligently matched to product type or mood; don't call this a proprietary music director.
6. Still no generalized anonymous multi-step product-value discovery, provider reliability or verified human appeal. Tests and zero automated QA findings do not constitute premium quality.

**Next realistic milestone:** native60 + pinned sound running on approved Studio service with concurrency/backpressure, then a truly unseen *action-rich* URL producing two or more meaningful verified UI outcomes and a human-reviewed premium 1080p60 film. Do not rebuild the renderer or promote failed reference studies.
