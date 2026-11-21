# Sauce — actual MP4 cursor geometry repair and creative comparison correction (2026-11-22)

**Scope:** GitHub `main`, existing persistent Vultr DevMCP worker, existing source-true Recode public browser recording. No branches, remote sign-ins, new servers, model inference calls, public product releases or additional UI overlays.

## User-reported failures, verified in real encoded videos

1. **All six model films look similar.** Confirmed. The six-model trial was a deliberately constrained **camera-only ablation** on exactly the same 4.9-second real recording, identical visible `index.html` edit, immutable real source pixels, action clock, audio mode and pointing samples. At most the JSON camera keyframes differed, with modest zoom (GLM5.2 1.00→1.077×; Qwen/Gemini/GLM5.3 ~1.25× max). A model could not author different product stories or alternative actions. It was misleading to treat this as evidence of six varied creative directions or a commercial-quality film contest. At t4.65, full encoded Qwen-vs-Gemini average absolute RGB difference downsampled to 480×270 was **1.243/255/channel** and GLM5.3-vs-Gemini was **0.960/255/channel** (same source, nearly identical framing). Source remains legitimately weak: a browser-local public HTML preview and abrupt `fill`, not a rich cloud-product workflow. **Creative result: all six still REJECTED.**
2. **Mouse cursor is crooked.** Confirmed. `scripts/recorded_pointer.py` drew a hand-authored seven-point polygon `[[0,0],[4,32],[11,25],[18,43],[25,39],[17,22],[29,22]]`. Actual encoded frame crops clearly displayed a thin, angular, kinked arrow over the code editor. The distorted geometry was a shared compositor issue, **not a model mistake**.

## Scoped real compositor fix

`scripts/recorded_pointer.py` now draws the existing **MIT-licensed Tabler pointer-outline SVG** already bundled in `assets/cursors/tabler/pointer-outline.svg`, rasterized with our existing fourfold supersampling and cached at display size. It uses the exact original SVG apex from `online_cursor_assets.hotspot("outline")`, BGR/alpha blended with `cinematic_presentation_v13._blend`. The pointer is white with a dark rim, standard orientation and recognizable shaft. The recorded x/y sample times, camera-projected positions and click hotspot remain unchanged; no imaginary pointer motion, clicks, UI or screenshots were introduced. Only the cursor's actual MP4 pixels change. This fixes all renderer paths calling `draw_pointer` including source-true fullscreen and 3D stage pointer rendering, while leaving existing user-selectable glass loupe cursor modes alone. Supersampled sprite size is ~34×38 pixels at the 1080p film's existing `scale=.73`.

New regression checks in `tests/phase2/test_recorded_pointer.py` compare the entire painted frame pixel-for-pixel to the pre-existing Tabler alpha sprite aligned to the measured hotspot; check white body visibility; and prove the original source-to-camera projection is preserved. This prevents a future return to distorted procedural cursor geometry or a shifted synthetic click point.

## Encoded before/after proof

The same Qwen 3.8 Flash Next camera plan was rerendered with the modified compositor. **Old** MP4 SHA256 `82d62aaa58c91c79f7e9ee3432d097b8faf0b4bd15dfe0986df9547789338ce1`; **new** SHA256 `4e6f8bbc173267b95392e97bec05990209c3427f22958f8175439f906c75a766`. Same real Recode source SHA256 `1b7b3b58948601e81e7dc415167c9ca5e1a06d501eb518d764803aecc35aef77`, manifest SHA256 `1768f688da06e9b6d0916d1c6f4759f3c10750162b90cd9bacc74f4713d714a8`, camera key SHA256 `fcb93e213e6669b89080577a92989613d06d73dc60a19164414c5d017c0fb22a`; unmodified 294-frame 1920×1080/60fps video, 4.9s. Actual decoded source frame at **t0.50** pixel-equal before/after, when no real cursor has yet appeared. At **t1.10**, changed-pixel connected component focuses on old/new cursor near **(1269,809)**; at **t1.25**, pointer near **(859,385)**; at **t1.35**, near **(806,344)**. Only shape/alpha was corrected: source product UI and camera plan did not change. The enlarged actual decoded MP4 before/after grid at these timestamps was opened and inspected (not mocked source screenshots).

All six original model plans were rerendered under `.tmp-model-shootout-reasoning-off-20261122/cursor-fixed-films/`, **retaining the originals for honest comparison**. New SHA256:
- DeepSeek V4.1 Flash: `0b173f88dbc9c20276df78efb451bb53ba5a29019c3afbe551083bf5843e749b`
- GLM 5.2: `1362088fc2775e7730679d30e7b4593b6688253d46a2df2873a77c3cf74ce403`
- Qwen 3.8 Flash Next: `4e6f8bbc173267b95392e97bec05990209c3427f22958f8175439f906c75a766`
- Gemini Flash-Lite: `9d4d05186478278ec7eb00fa02b758d0f2b0e932cf4436f3393dd2fd7562157c`
- GLM 5.3: `a527596739d1e12fab506b6412b933eb3c3d846492208d0fd3a360e37e07b4d9`
- MiniMax M3.1 Flash: `c93dcacf4a8a613f90a040309c68cb41d15e370838208ce46ab106ad60f4fee2`

All six **individually passed FFprobe 1920×1080 H.264 CFR60 / 294 frames and FFmpeg full decode**. Contact sheet from genuine corrected film frames at 0.35, 2.75 and 4.65s opened at phone-size (~366px wide). Signed review has **original broken Qwen + six corrected variants** and a close-up image of actual before-and-after video pixel crops. Signed URL, owner-only, expires 2026-11-28 23:33:10 UTC:

[Watch genuine fixed-cursor film comparison](https://devmcp.davemafy.xyz/sauce-expiring-review/tweakcn-20261120/sauce-fixed-cursor-c1e37c3a3b3d7bc5d860/index.html?md5=Ys8JWw1QTqHeMOXllnJaew&expires=1795908790)

Signed HTML/image/MP4 verified HTTP200; video HTTP206 byte-range seek verified; remote Qwen MP4 SHA256 matched local file. Browser on desktop **1280×720** and phone **390×844** played and sought **7 films per viewport, 14/14 passed**, with zero page script errors or horizontal overflow; phone video displays ~362×204px. All private photos and media remain off GitHub; no HAR, credentials or user data hosted.

## Still visually poor; action for next model evaluation

- The original pointer track has only **12 real samples from t0.9788 to t1.3452**. It stays stationary over the code pane after that. The renderer **must not synthesize a pointer path**, but capture design should produce genuine full action-duration cursor tracking or safely retire pointer after verified interactions. This source is not ideal for selling cursor craft.
- No readable typing animation, substantive action sequence, or cinematic reveal exists to compose. Too much unnecessary site footer, code labels unreadable at 390px, and a weak static opening. **No model output passed premium acceptance**; only the cursor shape is fixed.
- Do not run more model shootouts on one immutable 4.9-second clip expecting major differences. Next meaningful test needs **at least two separately verified and genuinely worthwhile product actions**, allows each model to choose and compose different source-true shots and beats (EDL/story, not just camera coordinates), and assesses real encoded diversity/phone legibility against Screen Studio references before announcing creative winners.

**Tests on latest current main:** focused Python suite **33 passed, 3 skipped, 8 subtests passed**, broad Python unittest **278 run, 2 skipped, no failures**. GitHub main stays the sole branch; changes limited to `scripts/recorded_pointer.py`, `tests/phase2/test_recorded_pointer.py`, this report and appended `docs/SAUCE_HANDOFF.md`.
