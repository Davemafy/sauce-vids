# Sauce URL-to-video pilot

Primary experience: https://devmcp.davemafy.xyz/sauce-app/studio

A submitted public URL follows the existing Sauce engine:
inspection in Playwright -> one multimodal Gemini direction call ->
validated read-only workflow -> verified browser capture ->
Sauce compositor/FFmpeg -> private playable MP4 -> user review.

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

The final outcome is needs_review, needs_access or failed. If the
public website only advertises an authenticated product workflow,
the AI must choose needs_access. Paldey was verified to stop without
inventing scholarship applications. Prior user feedback is included
as untrusted context in the NEXT direction call; approved videos
are not automatically regenerated.

## Limitations

- Public HTTP(S), global DNS, standard ports only. Browser
  requests are GET/HEAD-only; network redirects are checked.
- Director can choose sections from observed headings but cannot
  yet perform meaningful click-based tasks. Current autonomous
  capture is constrained to scroll/hover with observed visual-region assertions; it must not claim
  authenticated behavior, form submissions, or real app actions
  that were not observed.
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

`backend/state_film.py` validates the SHA-256 hashes of every captured browser
screenshot and produces an 8-second 720p30 H.264 preview and 1080p60 master
with gentle real-image camera movement, without reconstructing site UI. This is
**not** a semantically verified DOM replay: the release manifest says
`replay_verified: false`. Existing Sauce replay verification remains enabled in
the original renderer and is not bypassed or misreported.

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
