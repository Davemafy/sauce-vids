# Sauce URL-to-video pilot

Primary experience: https://devmcp.davemafy.xyz/sauce-app/studio

A submitted public URL follows the existing Sauce engine:
inspection in Playwright -> one multimodal Gemini direction call ->
browser-evidence-bound safe workflow -> continuous Chromium video recording ->
H.264 postproduction -> private playable MP4 -> user review.

The default Studio page is now URL-first. Bounded sample recordings
remain available under /studio/samples.

## Services and credentials

- sauce-url2video.service (systemd): Python backend in /opt/sauce-vids
- localhost HTTP endpoint: 127.0.0.1:8767 (existing bearer authentication)
- Unix socket: /var/lib/sauce-url2video/sauce.sock (mode 0600,
  owned by devmcp; the parent directory is mode 0700)
- Frontend: Next.js /sauce-app/studio, rendered by sauce-studio.service
- Frontend bridge: apps/web/app/api/studio/url/[...parts]/route.ts
- The frontend bridge connects only through the permission-limited
  Unix socket; it never receives the backend bearer or Gemini API key.
- /etc/sauce-url2video.env is a root-owned backend secret.
- /etc/sauce-studio-url.env has only a separately scoped pilot access
  code and cookie signing secret (both root-owned, never committed).
- The pilot code is exchanged for a 6-hour signed, HttpOnly,
  SameSite=Strict HTTPS cookie scoped to URL-job API paths.

The public URL-to-video endpoints do not accept arbitrary untrusted
rendering without successful pilot authorization. POST requests enforce
same-origin. The private API still requires host-level access.
No raw HAR, captures, secrets or jobs directory are published.

## Operation

Configure a Gemini vision-capable model in the backend:
SAUCE_DIRECTOR_MODEL=gemini-3.1-flash-lite (verified 2026-11-16).
The prior 3.5 Flash Lite sometimes returned HTTP 503 for the
vision request. A failed provider call produces a safe terminal error,
not fake direction.

- GET /sauce-app/api/studio/url/auth: check pilot session
- POST /sauce-app/api/studio/url/auth: redeem pilot code
- POST /sauce-app/api/studio/url/jobs: start bounded URL job
- GET /sauce-app/api/studio/url/jobs/<id>: poll stages and actual
  compositor REPLAY frame counts
- GET /sauce-app/api/studio/url/jobs/<id>/media: private preview
- POST /sauce-app/api/studio/url/jobs/<id>/feedback: save rating/notes

The URL loading screen shows real stages: inspecting, directing,
capturing, rendering, and final review. It displays observed frame
counts only in the renderer stage, never an invented total-job
percentage. Job IDs are recoverable after a tab reload within the
authenticated pilot session. Interrupted status polling does not
cancel the backend job.

The final outcome is needs_review or failed for accessible public pages.
A marketing-only site may produce a labelled *public website preview*,
never a fabricated authenticated product walkthrough. Paldey was captured
as such a public preview without inventing scholarship applications. Prior user feedback is included
as untrusted context in the NEXT direction call; approved videos
are not automatically regenerated.

## Limitations

- Public HTTP(S), global DNS, standard ports only. Browser
  requests are GET/HEAD-only; network redirects are checked.
- The director can select observed, reversible public controls by evidence ID.
  Safe interactions are filmed live, with a small benign text fixture only
  after an explicit public paste-text control. No purchases, authenticated
  flows, submissions, or arbitrary fabricated product outcomes.
- One Gemini direction call per job, no silent retries. The provider
  may fail or become unavailable. The backend returns an honest
  error and no fabricated video.
- Serial render worker, bounded queue, trace-derived short film duration,
  CPU-heavy 1080p60 compositor and 720p preview.
- The real film still needs human visual signoff even after
  technical encoding tests pass. Neither shaders nor a successful
  frame count guarantee compelling product storytelling.


## Sauce-native Product Explorer and reliable visual exports (16 November 2026)

`backend/product_explorer.py` extracts a bounded inventory of *observed* first-party
controls and headings, computed style tokens, actual DOM-path selectors and a
Chromium screenshot. It rejects mutating controls, cross-origin links and private
network destinations. Browser actions are checked against a fresh session.

`backend/url_engine.py` sends the screenshot and inventory to a single Gemini
vision call. Gemini returns **element IDs, not selectors or URLs**. IDs are
validated against observed inventory. If the model is unavailable, Sauce
produces a deterministic public showcase rather than inventing functionality.
A browser-side interaction that is unstable downgrades to a conservative public
preview. Private account workflows are never simulated.

`backend/state_film.py` was the previous still-frame montage renderer and is
**retired from the URL production path**. It remains only for diagnostics or
historical receipts. Its exports felt like slideshows because a handful of
screenshots were held and crossfaded; it is no longer an acceptable default.

`backend/live_capture.py` records the actual moving Chromium viewport to WebM
while the browser physically scrolls, moves its pointer, opens public examples,
and observes real state changes. `backend/live_render.py` SHA-checks that
continuous stream and transcodes to H.264 720p30 preview plus 1080p60 master.
The recorded source was captured at Chromium's native video cadence; 60fps
master output resamples frames but does not invent higher-frequency animation.
The receipt says `continuous_motion: true`, `source_verified: true`, and
`replay_verified: false`: source evidence is verified but a second independent
DOM replay is not claimed.

The Studio result screen identifies public showcases versus observed public
interactions and provides a protected MP4 download and a review link.
The job API marks unfinished jobs `failed` on worker restart so the browser
cannot display an endless stale rendering state.

Real integration checks produced playable files from:
- seal-verify.vercel.app (one evidence-bound click of Paste text instead)
- igor-taste.vercel.app (public product showcase)
- paldey.com (public-site showcase; not authenticated matching)
- 21.dev (public-site showcase)
- example.com (simple public document)

Additional public HTTPS Playwright verification: entering example.com through
Sauce Studio on a 390x844 viewport, returning a completed job and a protected
MP4 with HTTP 200, visible video and download controls, no page errors and no
horizontal overflow. Measured completion in that test: 12.9 seconds; this is
not a guaranteed future time or quality result.

Supported scope: websites that render public content to automated Chromium.
Captchas, bot blocks, private products and services requiring authenticated
sessions remain explicitly unsupported for automated filming. The generated
visual preview still requires human quality review.


## Continuous-motion replacement acceptance (17 November 2026)

An actual production job at `seal-verify.vercel.app` now records the real
"Paste text instead" transition followed by safe non-submitted demo typing.
The measured public preview lasts approximately 7.97 seconds, with source
recording preserved and SHA-256 verified. The video was fully decoded by
FFmpeg and verified at 1280x720 30fps; its 1080p master was verified at 60fps.

Independent public domains `igor-taste.vercel.app` and `paldey.com` also
produced complete continuous screen recordings. Those are labelled public-site
showcases because their private app functions were not demonstrated.

Do not equate successful encoding with editorial signoff. Continuous motion
fixes the slideshow failure mode, but persuasive automated product storytelling,
meaningful multi-action flows, and cinematic pacing still need improvement.

### Playwright video runtime dependency

The production service must have Playwright's bundled FFmpeg in the user-owned
browser cache, in addition to system FFmpeg used for encoding:

    runuser -u devmcp -- env HOME=/var/lib/sauce-url2video \
      /opt/sauce-vids/.venv/bin/python -m playwright install ffmpeg

The container uses a private Unix socket and runs the browser as the restricted
non-root devmcp service account. A missing Playwright recorder is a capture
failure, not a reason to silently fall back to screenshot montages.
