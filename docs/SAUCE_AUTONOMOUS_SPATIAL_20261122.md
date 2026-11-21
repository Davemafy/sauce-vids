# Sauce — Autonomous verified DOM spatial direction (2026-11-22)

Status: owner-only reusable R&D; no human-approved premium film or production rollout.

## What changed
New scripts/autonomous_spatial_film.py is a deterministic spatial film director over the EXISTING source-true paired-browser DOM compositor. It does not rebuild the renderer or generate replacement UI. When it finds a genuine independently validated same-Chromium-clock clean plate containing 2–3 real opaque DOM elements, it chooses native-frame lift/peak/return times, independent screen-space positions, camera recession, spatial material and 48kHz event-locked Foley from the original source event timestamps and measured DOM rectangles. Three compositional variants are independently checked by the existing source contract, SHA256 checks, decoded source/plate pixel validator, actual homography/overlap tests, original renderer and encoded QA. Without authentic evidence it declines spatial editing. No Gemini API call, manual shot JSON or fabricated cursor samples.

Existing owner-only scripts/auto_public_ui_film.py --director-mode coverage now automatically selects spatial only when actualCapture.verifiedLiveDomPlaneGroup is independently verified, otherwise keeps the previous source-only coverage mode; its default Gemini behavior stays unchanged. Added --from-paired-capture DIRECTORY to accept an existing owner-authorized native source.mp4, capture.json and matching plate.mp4 from the SAME private folder, so real source hashes and relative clean-plate frames survive. Exact public URL and explicit allowed host must match, competing capture flags and model mode are rejected, no overwrite or auto-publication. This is an executable capture-to-film director once paired footage exists, not general arbitrary-URL live paired capture.

## Original real source, unchanged
Public Tweakcn editor, https://tweakcn.com/editor/theme, an actual Default to Neo Brutalism click with observed source result. Original Chromium source and same-clock hidden-element plate: native 2560x1440, 60fps, 210 frames/3.5 seconds, two opaque real cards, their native rectangles [801,372,847,512] and [1681,372,847,512].
Original source SHA256 eb78cc91bbf1c6cf8094c54e59292bb16ddf50ba98b4909e4651c5a7df7fd805
Original plate SHA256 c56458600b0bf8b9579f2cc29ad70941d443e9434bc16007723d382c6ad07e3a
Original manifest SHA256 673ef62388adeb36412173cb095a40894a4df5544ade7a1eb7c09c69d542658c

## Three genuine autonomous edits
No manual camera plan, no model call. Each is native 1920x1080 H264 60fps/210 frames with AAC48kHz stereo, full strict FFmpeg decode. Source+plate hash/geometry provenance and renderer validation passed. Encoded QA: HUMAN_REVIEW_REQUIRED, no objective findings. Actual contact/full-payoff frames inspected against earlier human-directed Tweakcn spatial film and privately held Screen Studio UI reference. Improved first camera context and reduced excessively empty black stage behind the two independent original cards; still a modest 3.5s technique proof with small secondary UI and weak narrative. Creative REJECT; no claim of $50k film quality.

Composed SHA256 701264ae5524800da01c3b3a39e27c794ce0eecea3b0afa48eb6f7b3d5ee0494
Dimensional SHA256 6850adfc888bc3a227ebe58f5eed652d08091da2a3dc387aabc14806525cf1db
Subtle SHA256 c5c221f421792f7eeb09ee8694d4c0721eb681cb37acf0c60be3229f6dd242c4

Private 72-hour signed links (signed HTTP200, unsigned HTTP403):
Composed: https://devmcp.davemafy.xyz/sauce-expiring-review/tweakcn-20261120/sauce-tweakcn-autospatial-composed-20261122.mp4?md5=a19-CZJzbqcEt7_4NnQyiw&expires=1795563196
Dimensional: https://devmcp.davemafy.xyz/sauce-expiring-review/tweakcn-20261120/sauce-tweakcn-autospatial-dimensional-20261122.mp4?md5=Ay-kp1nz3I4Ocg47gFDsew&expires=1795563196
Subtle: https://devmcp.davemafy.xyz/sauce-expiring-review/tweakcn-20261120/sauce-tweakcn-autospatial-subtle-20261122.mp4?md5=gUiIoOkt6apFH3geAOjfIA&expires=1795563196

Actual Chromium signed playback and seek-to-2.25s succeeded in desktop 1280x720 and mobile 390x844 for composed/dimensional with no JS/video errors. Real existing-capture owner CLI produced film_requires_human_review, providerAttemptCount=0, and SHA256-backed film receipts; original capture remained private/untouched.

Single-command owner-only usage after a real authorized capture:
    python scripts/auto_public_ui_film.py --url https://tweakcn.com/editor/theme --allowed-host tweakcn.com --director-mode coverage --from-paired-capture /PRIVATE/existing-folder --out /PRIVATE/new-review

## Limits and next work
The default anonymous public URL capture does not automatically generate genuine frame-synchronized DOM-hidden clean plates; this route does not yet solve general self-service capture. On unsupported/transparent sites it falls back to source-true whole-browser footage, not fabricated elements. To reach commercial film quality, improve safe automatic DOM plate acquisition, shot-level storytelling, closeup readability and compositional judgment against real premium references.

No production deployment, new VM, branch, paid purchase, committed source videos/screenshots, key exposure, public release or approved films. Three customer-quality-approved independent films required; count remains ZERO.
