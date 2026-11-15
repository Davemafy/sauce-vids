# Sauce Studio — Phase 3 release

**Live Studio:** https://devmcp.davemafy.xyz/sauce-app/studio

**Landing page with genuine 3D Launch AFTER film:**
https://devmcp.davemafy.xyz/sauce-app

Production architecture: Next.js 15 / React 19 (Vultr loopback port 3197,
systemd managed) → bounded Node render queue → existing Playwright, Python,
OpenCV and FFmpeg Sauce Motion Engine. The UI sends only recording ID,
preset ID and a Foley boolean; it never submits shell commands, arbitrary
URLs, user-selected paths or capture contents.

## Improvements shipped

### Browser source polish

The capture script installs `MOCKUP_SCROLLBAR_STYLE` before capture actions
and applies it to the current page. Replay adds the identical CSS during
film production:

```css
::-webkit-scrollbar, *::-webkit-scrollbar {
  display: none !important;
  width: 0 !important;
  height: 0 !important;
}
```

`scrollbar-width:none` covers engines that support the property. The actual
scroll position and wheel events remain functional. New source screenshots
are captured with the same clean mockup treatment.

### Kinetic callout

The verified label (e.g. "Connect Agent") gets a restrained dark-glass
backdrop with 16px blurred real-frame pixels, an ivory-blue 1px luminous
rim in the spotlight palette, subtle top-edge specular reflection and a
180ms cubic slide/fade from 14px below. It remains attached to the
**projected actual UI anchor**, using the existing frame-driven spring and
leader line. The label has no audio-dependent animation.

### One-click Studio

`apps/web/app/studio/` provides an accessible, responsive dark workspace
with recording selection, Clean Studio / 3D Launch / Hyper-Cut flavors,
Foley on/off, rendering state, video preview and a master download.

The initial bounded catalog includes:
- `brimble`: a recorded, verified real product interaction.
- `sauce`: a seven-state local browser fixture, freshly recaptured with
  five real source pixel-region checks (session data remains private).

The background job route only accepts:
`{recording:"brimble"|"sauce",preset:"clean-studio"|"3d-launch"|"hyper-cut",foley:boolean}`.
There are 12 possible immutable output keys. Work is serialized, cached
by key and limited to the two verified workflows. The worker supports
Range requests for streamed MP4 playback, and makes only completed
video assets available. It does **not** expose HAR, screenshots, secrets
or original session files.

This is **not yet arbitrary per-user recording upload**. A future public
upload workflow needs authentication, quotas, storage lifecycle rules,
malware screening and tenant isolation.

### Landing film

The landing page's AFTER player uses the real Phase 2 3D Launch
H.264/AAC film rather than a fabricated image:
`https://devmcp.davemafy.xyz/sauce-motion-phase2/master-1080p60.mp4`.
Autoplay starts muted due to browser policy; pressing video controls
enables the actual Foley soundtrack.

## Public verification

The HTTP API was exercised against the live reverse-proxied Next app:

- Brimble / 3D Launch / Foley on: returned 202 → rendering → ready,
  valid 1080p60 master with AAC stereo at 48kHz.
- Brimble / 3D Launch / Foley off: returned ready, and the decoded
  48kHz AAC PCM peak is **exactly 0.0**.
- Sauce / Clean Studio / Foley off: returned ready after a valid recapture,
  **7 hashed states, 5 semantic checks, 5 pixel-region checks**,
  and exactly silent 48kHz AAC.
- Cross-site render POST: HTTP 403. Completed video accepts Range
  requests (HTTP 206 Partial Content).
- Playwright public desktop + mobile verified no horizontal overflow,
  preset selection, sound toggle, finished render display and the
  actual landing film.
- Python local: 5 Phase 3 tests; 10 Phase 2 tests; 156 legacy unittest
  checks. Next web TypeScript compilation and production build passed;
  9 Vitest unit tests; 7 Playwright end-to-end tests.

## Local development and service configuration

```bash
cd apps/web
npm install
npm run build
npm run test
npm run test:e2e
```

Use Node.js 22 or newer with this toolchain. Local worker variables:

```env
SAUCE_STUDIO_ENABLED=1
SAUCE_WORKSPACE_ROOT=/absolute/path/to/sauce-v05-release
SAUCE_PYTHON_BIN=/absolute/path/to/.sauce-render-env/bin/python
NEXT_PUBLIC_SAUCE_BASE_PATH=/sauce-app
```

Run `next start` from `apps/web` with those environment variables and
proxy `/sauce-app` and `/sauce-app/` to its loopback port without stripping
the URL prefix. The Vultr instance runs `sauce-studio.service`, a
systemd-managed Node 22 worker, bound only to 127.0.0.1:3197.

No secrets, private screenshots, HAR archives or generated videos are
committed to git. Only the public Phase 2 demo MP4 URL and the
code/configuration belong in the repository.
