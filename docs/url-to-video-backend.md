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
